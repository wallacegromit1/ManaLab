from __future__ import annotations

import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, Mapping

import yaml

from .phase3_policies import POLICY_REGISTRY, validate_policy_freeze
from .metrics import PHASE3_METRIC_REGISTRY
from .statistics import validate_seed_partition


REQUIRED_STAGES = [
    "01_validate", "02_enumerate", "03_screen", "04_medium",
    "05_select_finalists", "06_fresh_validation", "07_robustness",
    "08_frontier", "09_report",
]
REQUIRED_PROFILES = {
    "balanced", "tempo_sensitive", "color_consistency",
    "interaction_sensitive", "double_spell_sensitive",
    "affinity_value_engine",
}
BAD_PLACEHOLDERS = {None, "", "TODO", "TBD", "PLACEHOLDER", "UNSPECIFIED"}

RUN_E_SHA256 = "82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71"
EXPECTED_C0 = {
    "Ancient Den": 3, "Seat of the Synod": 4, "Vault of Whispers": 4,
    "Great Furnace": 4, "Razortide Bridge": 1, "Goldmire Bridge": 1,
    "Mistvault Bridge": 2, "Drossforge Bridge": 0, "Rustvale Bridge": 0,
    "Silverbluff Bridge": 0,
}

def scientific_config_view(config: Mapping[str, Any]) -> dict[str, Any]:
    """Return only decision-relevant scientific configuration.

    Authorization/control metadata is intentionally excluded so toggling an
    external authorization state cannot alter scientific hashes or results.
    """
    excluded = {"phase_control", "_config_path", "_config_hash"}
    return {key: value for key, value in config.items() if key not in excluded}

def scientific_config_hash(config: Mapping[str, Any]) -> str:
    return canonical_hash(scientific_config_view(config))


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def load_phase3_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).resolve()
    value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Phase 3 config must be a mapping")
    value["_config_path"] = str(config_path)
    value["_config_hash"] = sha256_file(config_path)
    return value


def _walk_for_placeholders(value: Any, path: str = "config") -> list[str]:
    failures: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).startswith("_"):
                continue
            failures.extend(_walk_for_placeholders(child, f"{path}.{key}"))
    elif isinstance(value, list):
        if not value:
            failures.append(f"{path} is empty")
        for index, child in enumerate(value):
            failures.extend(_walk_for_placeholders(child, f"{path}[{index}]"))
    else:
        try:
            bad = value in BAD_PLACEHOLDERS
        except TypeError:
            bad = False
        if bad:
            failures.append(f"{path} is a placeholder")
    return failures


def validate_phase3_config(
    config: Mapping[str, Any],
    root: str | Path,
    *,
    validate_control: bool = True,
) -> None:
    root = Path(root).resolve()
    failures = _walk_for_placeholders(config)
    if failures:
        raise ValueError("; ".join(failures))

    if config.get("schema_version") != "mana-lab-phase3-run-g-v1":
        raise ValueError("unexpected Phase 3 schema_version")
    parent = config["input"]["parent_archive"]
    if parent.get("sha256") != RUN_E_SHA256:
        raise ValueError("parent archive hash does not match frozen Run E authority")
    control = config["phase_control"]
    required_control = {
        "authorization_status", "optimization_execution_allowed",
        "real_candidate_performance_allowed_in_readiness", "readiness_mode",
    }
    if required_control - set(control):
        raise ValueError("phase-control metadata is incomplete")
    if validate_control:
        if control["authorization_status"] != "PENDING_INDEPENDENT_RUN_H":
            raise ValueError("Run G config must remain pending independent authorization")
        if control["optimization_execution_allowed"] is not False:
            raise ValueError("Run G must not authorize optimization execution")
    if list(config["pipeline"]["stages"]) != REQUIRED_STAGES:
        raise ValueError("pipeline stages are missing or out of order")

    deck = config["input"]["deck_spec"]
    deck_path = root / deck["path"]
    if not deck_path.is_file() or sha256_file(deck_path) != deck["sha256"]:
        raise ValueError("deck specification path/hash mismatch")
    if config["candidate_space"]["expected_count"] != 296706:
        raise ValueError("candidate count freeze must be 296706")
    if dict(config["candidate_space"].get("c0", {})) != EXPECTED_C0:
        raise ValueError("C0 does not match the frozen benchmark")
    if sum(int(v) for v in EXPECTED_C0.values()) != 19:
        raise ValueError("frozen C0 land count is invalid")
    if not config["candidate_space"]["protect_c0_every_serious_stage"]:
        raise ValueError("C0 protection must be enabled")
    if not config["candidate_space"].get("protect_minimum_bridge_class"):
        raise ValueError("three-Bridge boundary protection must be enabled")
    if config["candidate_space"].get("expected_minimum_bridge_class_count") != 56:
        raise ValueError("three-Bridge boundary count must be frozen at 56")

    random = config["randomness"]
    if not validate_seed_partition(
        random["selection_seed"], random["validation_seed"], random["replicate_seeds"]
    ):
        raise ValueError("selection/validation/replicate seed partitions overlap")
    if random["selection_seed"] == random["validation_seed"]:
        raise ValueError("fresh validation seed equals selection seed")
    all_seeds = [
        random["selection_seed"], random["validation_seed"], *random["replicate_seeds"]
    ]
    if any(not isinstance(seed, int) or seed <= 0 for seed in all_seeds):
        raise ValueError("all declared seeds must be positive integers")
    if len(set(all_seeds)) != len(all_seeds):
        raise ValueError("seed declarations must be globally unique")
    if len(random["replicate_seeds"]) != int(config["trial_plan"]["replicate_count"]):
        raise ValueError("replicate seed count does not match replicate_count")
    if random.get("pairing_keys") != ["scenario", "replicate", "trial", "on_play"]:
        raise ValueError("paired comparison keys differ from the frozen contract")
    expected_derivation = (
        "SHA-256(purpose|scenario|replicate|trial|mulligan_attempt); "
        "candidate identity and iteration order excluded"
    )
    if random.get("seed_derivation") != expected_derivation:
        raise ValueError("seed derivation declaration differs from frozen contract")
    if not isinstance(random.get("validation_isolation"), str) or not random["validation_isolation"].strip():
        raise ValueError("validation isolation declaration is missing")

    counts = config["trial_plan"]
    for field in (
        "screening_trials_per_candidate", "medium_trials_per_candidate",
        "validation_trials_per_candidate", "validation_adaptive_batch",
        "validation_adaptive_cap", "replicate_count",
    ):
        if not isinstance(counts[field], int) or counts[field] <= 0:
            raise ValueError(f"{field} must be a positive frozen integer")
    if counts["validation_adaptive_batch"] > counts["validation_adaptive_cap"]:
        raise ValueError("adaptive validation batch exceeds cap")
    if counts["validation_adaptive_cap"] < counts["validation_trials_per_candidate"]:
        raise ValueError("adaptive validation cap is below initial validation trials")

    scenarios = config["scenarios"]
    for field in ("planner_search_depth", "planner_max_actions_per_main"):
        if not isinstance(scenarios[field], int) or scenarios[field] <= 0:
            raise ValueError(f"{field} must be a positive integer")
    if not scenarios.get("depth_sensitivity") or any(
        not isinstance(value, int) or value <= 0 for value in scenarios["depth_sensitivity"]
    ):
        raise ValueError("depth_sensitivity must contain positive integer depths")
    mixes = scenarios.get("primary_play_draw")
    if not isinstance(mixes, list) or not mixes:
        raise ValueError("primary play/draw mix is missing")
    total_weight = 0.0
    ids = set()
    for item in mixes:
        weight = float(item.get("weight", -1))
        if not isfinite(weight) or weight < 0:
            raise ValueError("play/draw weights must be finite and non-negative")
        ids.add(str(item.get("id")))
        total_weight += weight
    if ids != {"on_play", "on_draw"} or abs(total_weight - 1.0) > 1e-12:
        raise ValueError("primary play/draw mix must be on_play/on_draw and sum to one")

    profiles = config["decision_profiles"]
    missing_profiles = REQUIRED_PROFILES - set(profiles)
    if missing_profiles:
        raise ValueError(f"required profiles missing: {sorted(missing_profiles)}")
    for name, profile in profiles.items():
        components = profile.get("metric_vector")
        if not isinstance(components, list) or not components:
            raise ValueError(f"profile {name} has no metric vector")
        for component in components:
            required = {
                "metric", "direction", "aggregation", "turns", "scenarios",
                "normalization", "no_worse_tolerance", "materiality_tolerance",
                "missing_data", "uncertainty",
            }
            absent = required - set(component)
            if absent:
                raise ValueError(f"profile {name} component incomplete: {sorted(absent)}")
            if component["direction"] not in {"higher", "lower"}:
                raise ValueError(f"profile {name} has invalid direction")
            if component["metric"] not in PHASE3_METRIC_REGISTRY:
                raise ValueError(f"profile {name} references unknown metric {component['metric']}")
            for tolerance in ("no_worse_tolerance", "materiality_tolerance"):
                value = float(component[tolerance])
                if not isfinite(value) or value < 0:
                    raise ValueError(f"profile {name} has invalid {tolerance}")
            if not component["turns"] or any(not isinstance(turn, int) or turn <= 0 for turn in component["turns"]):
                raise ValueError(f"profile {name} has invalid turn window")
            if not component["scenarios"]:
                raise ValueError(f"profile {name} has empty scenario population")
            if not isinstance(component["aggregation"], str) or not component["aggregation"].strip():
                raise ValueError(f"profile {name} has invalid aggregation")
        for field in ("comparison", "tie_behavior", "overlap_rationale", "decorrelated_variant", "leave_one_out"):
            if field not in profile:
                raise ValueError(f"profile {name} missing {field}")

    validate_policy_freeze(config["policies"])

    role_kind = {
        "mulligan": "mulligan", "sequencing": "sequencing", "reserve": "reserve",
        "scry": "scry", "information": "information",
    }
    for scenario in config.get("robustness_scenarios", []):
        if not isinstance(scenario.get("id"), str) or not scenario["id"]:
            raise ValueError("robustness scenario has invalid id")
        for axis, kind in role_kind.items():
            policy_id = scenario.get(axis)
            entry = POLICY_REGISTRY.get(str(policy_id))
            if entry is None or entry.get("kind") != kind:
                raise ValueError(f"robustness scenario {scenario['id']} has invalid {axis} policy")
        if scenario.get("play_draw") not in {"weighted_50_50", "all_play", "all_draw"}:
            raise ValueError(f"robustness scenario {scenario['id']} has invalid play/draw policy")

    mechanic_path = root / config["mechanics"]["registry_path"]
    if not mechanic_path.is_file() or sha256_file(mechanic_path) != config["mechanics"]["registry_sha256"]:
        raise ValueError("mechanic registry path/hash mismatch")

    output_names = set(config["outputs"])
    required_outputs = {
        "candidate_metrics", "spell_metrics", "turn_metrics", "paired_differences",
        "screening_decisions", "validation_results", "robustness_matrix",
        "pareto_frontier", "stage_manifests", "final_report",
    }
    if required_outputs - output_names:
        raise ValueError(f"output definitions missing: {sorted(required_outputs - output_names)}")

