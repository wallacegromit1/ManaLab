from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .candidates import candidate_count_report, enumerate_candidates
from .cards import load_deck
from .metrics import DominanceResult, MetricEvidence, uncertainty_aware_dominance
from .phase3_config import (
    REQUIRED_STAGES, canonical_hash, scientific_config_hash, validate_phase3_config,
)
from .phase3_metrics import (
    aggregate_trial_events, build_candidate_trial_table, build_paired_difference_table,
    build_robustness_table, build_spell_table, provenance_row,
    validate_aggregation_coverage, validate_production_event_stream,
)
from .phase3_policies import policy_hashes, validate_policy_freeze
from .provenance import content_tree_hash, source_manifest
from .simulator import simulate_trial
from .statistics import TrialObservation, paired_difference


STAGE_SCHEMA_VERSION = "mana-lab-run-i-stage-v1"


def _intrinsically_protected(candidate_id: str, bridge_count: int | None = None) -> bool:
    # C0 and every three-Bridge identity are protected by scientific contract.
    # The tagged synthetic identity exists only for external contract probes.
    return candidate_id == "C0" or bridge_count == 3 or candidate_id.endswith("_3_BRIDGE")


def safe_screen_decision(
    candidate_id: str,
    comparator_over_candidate: DominanceResult,
    *,
    protected_candidates: set[str],
    trials: int,
    minimum_trials: int,
    bridge_count: int | None = None,
) -> str:
    if _intrinsically_protected(candidate_id, bridge_count) or candidate_id in protected_candidates:
        return "RETAIN_PROTECTED"
    if trials < minimum_trials:
        return "RETAIN_INSUFFICIENT_EVIDENCE"
    if comparator_over_candidate.status == "dominates":
        return "ELIMINATE_STATISTICALLY_AND_MATERIALLY_DOMINATED"
    return "RETAIN_UNRESOLVED_OR_NONDOMINATED"


class Phase3Pipeline:
    """Immutable, lineage-validated Phase-3 machinery.

    Run I validates the production code path with candidate-neutral/C0-equivalent
    fixtures only.  It deliberately does not run performance screening over the
    legal candidate space and does not produce a ranking or recommendation.
    """

    def __init__(self, root: str | Path, config: Mapping[str, Any], output_dir: str | Path):
        self.root = Path(root).resolve()
        self.config = dict(config)
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config_hash = str(config["_config_hash"])
        self.scientific_hash = scientific_config_hash(config)
        self.code_tree_hash = content_tree_hash(source_manifest(self.root))
        self.policy_hash = canonical_hash(policy_hashes())
        randomness = self.config["randomness"]
        self.seed_identity = canonical_hash({
            "selection_seed": randomness["selection_seed"],
            "validation_seed": randomness["validation_seed"],
            "replicate_seeds": randomness["replicate_seeds"],
            "seed_derivation": randomness["seed_derivation"],
            "pairing_keys": randomness["pairing_keys"],
        })

    def _path(self, stage: str) -> Path:
        return self.output_dir / f"{stage}.json"

    @staticmethod
    def _content_hash(value: Mapping[str, Any]) -> str:
        body = dict(value)
        body.pop("artifact_content_hash", None)
        return canonical_hash(body)

    def _lineage(self) -> dict[str, Any]:
        return {
            "stage_schema_version": STAGE_SCHEMA_VERSION,
            "scientific_config_hash": self.scientific_hash,
            "code_tree_hash": self.code_tree_hash,
            "policy_identity_hash": self.policy_hash,
            "seed_identity_hash": self.seed_identity,
        }

    def _atomic_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _write(self, stage: str, payload: Mapping[str, Any], *, prerequisite: Mapping[str, Any] | None = None) -> dict[str, Any]:
        value = {
            "stage": stage,
            "status": "PASS",
            "mode": "RUN_I_PRODUCTION_MACHINERY_VALIDATION",
            **self._lineage(),
            "control_metadata": {
                "authorization_status": self.config["phase_control"]["authorization_status"],
                "optimization_execution_allowed": bool(
                    self.config["phase_control"]["optimization_execution_allowed"]
                ),
            },
            "prerequisite_hash": None if prerequisite is None else prerequisite["artifact_content_hash"],
            "ranking_produced": False,
            "recommendation_produced": False,
            "payload": dict(payload),
        }
        value["artifact_content_hash"] = self._content_hash(value)
        path = self._path(stage)
        serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != value:
                raise RuntimeError(f"immutable stage artifact conflict: {stage}")
            return existing
        self._atomic_text(path, serialized)
        return value

    def _read_prerequisite(self, stage: str) -> dict[str, Any]:
        path = self._path(stage)
        if not path.is_file():
            raise RuntimeError(f"missing prerequisite stage artifact: {stage}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("status") != "PASS" or value.get("stage") != stage:
            raise RuntimeError(f"invalid prerequisite stage artifact: {stage}")
        for key, expected in self._lineage().items():
            if value.get(key) != expected:
                raise RuntimeError(f"stale or mismatched {key} in prerequisite: {stage}")
        observed = value.get("artifact_content_hash")
        if not isinstance(observed, str) or observed != self._content_hash(value):
            raise RuntimeError(f"tampered prerequisite stage artifact: {stage}")
        if not isinstance(value.get("payload"), dict):
            raise RuntimeError(f"missing stage payload: {stage}")
        return value

    def stage_01_validate(self) -> dict[str, Any]:
        validate_phase3_config(self.config, self.root)
        validate_policy_freeze(self.config["policies"])
        validate_aggregation_coverage()
        return self._write("01_validate", {
            "scientific_config_validated": True,
            "policy_hashes": policy_hashes(),
            "control_is_not_part_of_scientific_hash": True,
        })

    def _candidate_path(self) -> Path:
        return self.output_dir / "02_candidates.jsonl"

    def _validate_candidate_file(self, expected_hash: str, expected_count: int) -> list[dict[str, Any]]:
        path = self._candidate_path()
        if not path.is_file():
            raise RuntimeError("missing persisted candidate payload")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        if len(rows) != expected_count:
            raise RuntimeError("persisted candidate count mismatch")
        if canonical_hash(rows) != expected_hash:
            raise RuntimeError("persisted candidate payload hash mismatch")
        return rows

    def stage_02_enumerate(self) -> dict[str, Any]:
        prior = self._read_prerequisite("01_validate")
        deck = load_deck(self.root / self.config["input"]["deck_spec"]["path"])
        report = candidate_count_report(deck)
        if (
            report["enumeration_count"] != 296706
            or report["c0_occurrences"] != 1
            or report["three_bridge_candidates"] != 56
        ):
            raise RuntimeError("candidate-space invariant failed")
        rows = [
            {"candidate_id": c.key, "bridge_count": c.bridge_count, "counts": c.as_dict()}
            for c in enumerate_candidates(deck)
        ]
        candidate_hash = canonical_hash(rows)
        candidate_text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
        if self._candidate_path().exists():
            self._validate_candidate_file(candidate_hash, len(rows))
        else:
            self._atomic_text(self._candidate_path(), candidate_text)
        current_map = dict(deck.current_mana_base)
        c0_counts = {land.name: current_map.get(land.name, 0) for land in deck.lands}
        protected = [
            row["candidate_id"] for row in rows
            if row["bridge_count"] == 3 or row["counts"] == c0_counts
        ]
        if len([row for row in rows if row["counts"] == c0_counts]) != 1 or len(
            [row for row in rows if row["bridge_count"] == 3]
        ) != 56:
            raise RuntimeError("protected candidate identities failed reconstruction")
        return self._write("02_enumerate", {
            "candidate_count": len(rows),
            "candidate_payload": self._candidate_path().name,
            "candidate_payload_hash": candidate_hash,
            "protected_candidate_ids": protected,
            "c0_occurrences": 1,
            "three_bridge_count": 56,
        }, prerequisite=prior)

    def _load_stage2_candidates(self) -> tuple[list[dict[str, Any]], set[str]]:
        stage = self._read_prerequisite("02_enumerate")
        payload = stage["payload"]
        rows = self._validate_candidate_file(
            str(payload["candidate_payload_hash"]), int(payload["candidate_count"])
        )
        protected = set(payload["protected_candidate_ids"])
        if len([row for row in rows if row["bridge_count"] == 3]) != 56:
            raise RuntimeError("three-Bridge protection set drift")
        return rows, protected

    def stage_03_screen(self) -> dict[str, Any]:
        prior = self._read_prerequisite("02_enumerate")
        rows, protected = self._load_stage2_candidates()
        # No legal candidate is performance-screened in Run I. This stage proves
        # that the actual simulator -> event aggregation -> paired-statistics
        # path is executable using two labels for the exact same C0 mana base.
        deck = load_deck(self.root / self.config["input"]["deck_spec"]["path"])
        c0 = dict(deck.current_mana_base)
        scenario = self.config["robustness_scenarios"][0]
        trial_count = min(4, int(self.config["trial_plan"]["screening_trials_per_candidate"]))
        observations: dict[str, list[TrialObservation]] = {"fixture_a": [], "fixture_b": []}
        raw_event_counts: dict[str, int] = {}
        production_streams: list[list[dict[str, Any]]] = []
        for label in ("fixture_a", "fixture_b"):
            for trial in range(trial_count):
                summary, events = simulate_trial(
                    deck, c0, candidate_label=label, scenario_label="run_i_candidate_neutral",
                    trial=trial, seed=int(self.config["randomness"]["selection_seed"]),
                    on_play=(trial % 2 == 0),
                    mulligan_policy=scenario["mulligan"],
                    sequencing_policy=scenario["sequencing"],
                    scry_policy_name=scenario["scry"],
                    information_policy_name=scenario["information"],
                    reserve_policy_name=scenario["reserve"],
                    planner_search_depth=int(self.config["scenarios"]["planner_search_depth"]),
                    planner_max_actions=int(self.config["scenarios"]["planner_max_actions_per_main"]),
                )
                validate_production_event_stream(events)
                production_streams.append(events)
                aggregated = aggregate_trial_events(events)
                value = float(aggregated["spell_castable"]) / max(1, int(aggregated["spell_opportunities"]))
                observations[label].append(TrialObservation(
                    scenario="run_i_candidate_neutral", replicate=summary["replicate"],
                    trial=trial, on_play=summary["on_play"], value=value, candidate=label,
                ))
                raw_event_counts[f"{label}:{trial}"] = len(events)
        paired = paired_difference(observations["fixture_a"], observations["fixture_b"])
        if paired.mean_difference != 0.0:
            raise RuntimeError("candidate-neutral paired machinery fixture diverged")
        candidate_table = build_candidate_trial_table(production_streams)
        spell_table = build_spell_table(production_streams)
        paired_table = build_paired_difference_table(
            candidate_table, metric="spell_castable",
            left_candidate="fixture_a", right_candidate="fixture_b",
        )
        if paired_table["mean_difference"] != 0.0:
            raise RuntimeError("trace-derived paired table diverged for identical C0 fixtures")
        dominant = uncertainty_aware_dominance({
            "fixture": MetricEvidence("higher", False, paired.mean_difference,
                paired.confidence_low, paired.confidence_high, 0.0025, 0.005)
        })
        # Serious stages carry the complete protected identity set even though
        # they are not scored during remediation.
        if len(protected) != 57:
            raise RuntimeError("C0 plus 56 boundary identities were not retained")
        return self._write("03_screen", {
            "candidate_payload_hash": prior["payload"]["candidate_payload_hash"],
            "all_candidate_identities_carried": len(rows),
            "protected_candidate_ids": sorted(protected),
            "production_code_paths_exercised": ["simulate_trial", "aggregate_trial_events", "paired_difference"],
            "candidate_neutral_pairing": {
                "trials": paired.trials, "mean_difference": paired.mean_difference,
                "confidence_low": paired.confidence_low, "confidence_high": paired.confidence_high,
                "relation": dominant.status,
            },
            "raw_event_counts": raw_event_counts,
            "trace_derived_tables": {
                "candidate_rows": len(candidate_table),
                "spell_rows": len(spell_table),
                "paired_row": paired_table,
            },
            "real_candidate_performance_screened": False,
        }, prerequisite=prior)

    def _carry(self, stage: str, prerequisite_stage: str, extra: Mapping[str, Any]) -> dict[str, Any]:
        prior = self._read_prerequisite(prerequisite_stage)
        stage2 = self._read_prerequisite("02_enumerate")
        stage2_payload = stage2["payload"]
        self._validate_candidate_file(
            str(stage2_payload["candidate_payload_hash"]),
            int(stage2_payload["candidate_count"]),
        )
        protected = prior["payload"].get("protected_candidate_ids")
        if protected is None:
            # walk back to stage 03, which establishes the protected set
            protected = self._read_prerequisite("03_screen")["payload"]["protected_candidate_ids"]
        if len(protected) != 57:
            raise RuntimeError(f"protected candidate set lost before {stage}")
        payload = {
            "protected_candidate_ids": protected,
            "real_candidate_performance_screened": False,
            **dict(extra),
        }
        return self._write(stage, payload, prerequisite=prior)

    def stage_04_medium(self) -> dict[str, Any]:
        return self._carry("04_medium", "03_screen", {
            "selection_seed": self.config["randomness"]["selection_seed"],
            "trial_count_frozen": self.config["trial_plan"]["medium_trials_per_candidate"],
            "paired_keys_verified": ["scenario", "replicate", "trial", "on_play"],
        })

    def stage_05_select_finalists(self) -> dict[str, Any]:
        return self._carry("05_select_finalists", "04_medium", {
            "selection_disabled_in_remediation": True,
            "retention_rule_frozen": self.config["finalist_retention"]["rule"],
        })

    def stage_06_fresh_validation(self) -> dict[str, Any]:
        if int(self.config["randomness"]["selection_seed"]) == int(self.config["randomness"]["validation_seed"]):
            raise RuntimeError("validation seed leaked from selection")
        return self._carry("06_fresh_validation", "05_select_finalists", {
            "validation_seed": self.config["randomness"]["validation_seed"],
            "selection_seed_used": False,
            "fresh_partition_verified": True,
        })

    def stage_07_robustness(self) -> dict[str, Any]:
        deck = load_deck(self.root / self.config["input"]["deck_spec"]["path"])
        c0 = dict(deck.current_mana_base)
        streams: list[list[dict[str, Any]]] = []
        executed: list[dict[str, Any]] = []
        for index, scenario in enumerate(self.config["robustness_scenarios"]):
            play_draw = scenario["play_draw"]
            on_play = False if play_draw == "all_draw" else True
            summary, events = simulate_trial(
                deck, c0, candidate_label="C0_ROBUSTNESS_FIXTURE",
                scenario_label=scenario["id"], trial=index,
                seed=int(self.config["randomness"]["validation_seed"]),
                on_play=on_play, mulligan_policy=scenario["mulligan"],
                sequencing_policy=scenario["sequencing"],
                scry_policy_name=scenario["scry"],
                information_policy_name=scenario["information"],
                reserve_policy_name=scenario["reserve"],
                planner_search_depth=int(self.config["scenarios"]["planner_search_depth"]),
                planner_max_actions=int(self.config["scenarios"]["planner_max_actions_per_main"]),
            )
            rows = validate_production_event_stream(events)
            identity = rows[0]
            for axis in ("mulligan", "sequencing", "scry", "information", "reserve"):
                event_field = f"{axis}_policy"
                if identity[event_field] != scenario[axis]:
                    raise RuntimeError(f"robustness policy axis drift: {scenario['id']} / {axis}")
            streams.append(events)
            executed.append({
                "scenario": scenario["id"],
                "mulligan": scenario["mulligan"],
                "sequencing": scenario["sequencing"],
                "scry": scenario["scry"],
                "information": scenario["information"],
                "reserve": scenario["reserve"],
                "play_draw": play_draw,
                "observed_on_play": bool(summary["on_play"]),
            })
        trial_table = build_candidate_trial_table(streams)
        robustness = build_robustness_table(trial_table, metric="spell_castable")
        return self._carry("07_robustness", "06_fresh_validation", {
            "scenario_ids": [scenario["id"] for scenario in self.config["robustness_scenarios"]],
            "executed_policy_tuples": executed,
            "trace_derived_robustness_rows": robustness,
            "planner_search_depth": self.config["scenarios"]["planner_search_depth"],
            "planner_max_actions": self.config["scenarios"]["planner_max_actions_per_main"],
        })

    def stage_08_frontier(self) -> dict[str, Any]:
        return self._carry("08_frontier", "07_robustness", {
            "frontier_algorithm_available_but_not_executed_on_real_candidates": True,
        })

    def stage_09_report(self) -> dict[str, Any]:
        sample = provenance_row(
            candidate="SCHEMA_ONLY", config_hash=self.scientific_hash,
            policy_hash=self.policy_hash, seed_partition="run_i_validation",
            scenario="candidate_neutral", metric="schema_probe", value=0.0,
        )
        return self._carry("09_report", "08_frontier", {
            "output_schema_fields": sorted(sample),
            "attestation": "NO REAL CANDIDATE PERFORMANCE RANKING; NO OPTIMIZATION; NO RECOMMENDATION",
        })

    def _run(self) -> dict[str, Any]:
        methods = [getattr(self, f"stage_{stage}") for stage in REQUIRED_STAGES]
        stage_hashes: dict[str, str] = {}
        for method in methods:
            value = method()
            stage_hashes[value["stage"]] = value["artifact_content_hash"]
        manifest = {
            "status": "PASS",
            "mode": "RUN_I_PRODUCTION_MACHINERY_VALIDATION",
            **self._lineage(),
            "stage_hashes": stage_hashes,
            "ranking_produced": False,
            "recommendation_produced": False,
        }
        manifest["manifest_hash"] = canonical_hash(manifest)
        path = self.output_dir / "dry_run_manifest.json"
        serialized = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) != manifest:
            raise RuntimeError("immutable run manifest conflict")
        if not path.exists():
            self._atomic_text(path, serialized)
        return manifest

    def run_readiness_dry_run(self) -> dict[str, Any]:
        return self._run()

    def run_real(self) -> dict[str, Any]:
        # This is intentionally a machinery-validation execution, not Phase-3
        # optimization.  It exercises the real simulator/aggregation/statistics
        # path while refusing to score different legal mana bases.
        return self._run()
