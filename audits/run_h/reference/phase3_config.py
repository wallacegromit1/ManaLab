from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from .phase3_policies import validate_policy_freeze
from .statistics import validate_seed_partition


REQUIRED_STAGES = [
    "01_validate", "02_enumerate", "03_screen", "04_medium",
    "05_select_finalists", "06_fresh_validation", "07_robustness",
    "08_frontier", "09_report",
]
REQUIRED_PROFILES = {
    "balanced", "tempo_sensitive", "color_consistency",
    "interaction_sensitive", "double_spell_sensitive",
}
BAD_PLACEHOLDERS = {None, "", "TODO", "TBD", "PLACEHOLDER", "UNSPECIFIED"}


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


def validate_phase3_config(config: Mapping[str, Any], root: str | Path) -> None:
    root = Path(root).resolve()
    failures = _walk_for_placeholders(config)
    if failures:
        raise ValueError("; ".join(failures))

    if config.get("schema_version") != "mana-lab-phase3-run-g-v1":
        raise ValueError("unexpected Phase 3 schema_version")
    control = config["phase_control"]
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
    if not config["candidate_space"]["protect_c0_every_serious_stage"]:
        raise ValueError("C0 protection must be enabled")

    random = config["randomness"]
    if not validate_seed_partition(
        random["selection_seed"], random["validation_seed"], random["replicate_seeds"]
    ):
        raise ValueError("selection/validation/replicate seed partitions overlap")
    if random["selection_seed"] == random["validation_seed"]:
        raise ValueError("fresh validation seed equals selection seed")

    counts = config["trial_plan"]
    for field in ("screening_trials_per_candidate", "medium_trials_per_candidate", "validation_trials_per_candidate"):
        if not isinstance(counts[field], int) or counts[field] <= 0:
            raise ValueError(f"{field} must be a positive frozen integer")

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
        for field in ("comparison", "tie_behavior", "overlap_rationale", "decorrelated_variant", "leave_one_out"):
            if field not in profile:
                raise ValueError(f"profile {name} missing {field}")

    validate_policy_freeze(config["policies"])

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

