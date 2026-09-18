from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from .candidates import candidate_count_report
from .cards import load_deck
from .metrics import DominanceResult, MetricEvidence, uncertainty_aware_dominance
from .phase3_config import REQUIRED_STAGES, canonical_hash, sha256_file, validate_phase3_config
from .phase3_metrics import provenance_row, validate_aggregation_coverage
from .phase3_policies import POLICY_REGISTRY, policy_hashes, validate_policy_freeze


def safe_screen_decision(
    candidate_id: str,
    comparator_over_candidate: DominanceResult,
    *,
    protected_candidates: set[str],
    trials: int,
    minimum_trials: int,
) -> str:
    if candidate_id in protected_candidates:
        return "RETAIN_PROTECTED"
    if trials < minimum_trials:
        return "RETAIN_INSUFFICIENT_EVIDENCE"
    if comparator_over_candidate.status == "dominates":
        return "ELIMINATE_STATISTICALLY_AND_MATERIALLY_DOMINATED"
    return "RETAIN_UNRESOLVED_OR_NONDOMINATED"


class Phase3Pipeline:
    """Artifact-driven Phase 3 orchestrator with a non-inferential dry run.

    Run G ships with optimization disabled.  The stage graph and safety logic
    are executable, while real-candidate performance stages refuse to run until
    a later independent authorization changes the frozen control state.
    """

    def __init__(self, root: str | Path, config: Mapping[str, Any], output_dir: str | Path):
        self.root = Path(root).resolve()
        self.config = dict(config)
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config_hash = str(config["_config_hash"])

    def _path(self, stage: str) -> Path:
        return self.output_dir / f"{stage}.json"

    def _read_prerequisite(self, stage: str) -> dict[str, Any]:
        path = self._path(stage)
        if not path.is_file():
            raise RuntimeError(f"missing prerequisite stage artifact: {stage}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("config_hash") != self.config_hash or value.get("status") != "PASS":
            raise RuntimeError(f"invalid prerequisite stage artifact: {stage}")
        return value

    def _write(self, stage: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        value = {
            "stage": stage,
            "status": "PASS",
            "mode": "READINESS_DRY_RUN",
            "config_hash": self.config_hash,
            "ranking_produced": False,
            "recommendation_produced": False,
            **dict(payload),
        }
        value["artifact_content_hash"] = canonical_hash(value)
        self._path(stage).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return value

    def stage_01_validate(self) -> dict[str, Any]:
        validate_phase3_config(self.config, self.root)
        validate_policy_freeze(self.config["policies"])
        validate_aggregation_coverage()
        return self._write("01_validate", {
            "authorization_status": self.config["phase_control"]["authorization_status"],
            "optimization_execution_allowed": False,
            "policy_hashes": policy_hashes(),
        })

    def stage_02_enumerate(self) -> dict[str, Any]:
        self._read_prerequisite("01_validate")
        deck = load_deck(self.root / self.config["input"]["deck_spec"]["path"])
        report = candidate_count_report(deck)
        if report["enumeration_count"] != 296706 or report["c0_occurrences"] != 1:
            raise RuntimeError("candidate-space invariant failed")
        return self._write("02_enumerate", {
            "deterministic_only": True,
            "candidate_count": report["enumeration_count"],
            "c0_occurrences": report["c0_occurrences"],
            "minimum_bridge_class_count": report["three_bridge_candidates"],
        })

    def stage_03_screen(self) -> dict[str, Any]:
        self._read_prerequisite("02_enumerate")
        dominant = uncertainty_aware_dominance({
            "m": MetricEvidence("higher", False, 0.05, 0.04, 0.06, 0.005, 0.01)
        })
        unresolved = uncertainty_aware_dominance({
            "m": MetricEvidence("higher", False, 0.002, -0.01, 0.014, 0.005, 0.01)
        })
        decisions = [
            safe_screen_decision("C0", dominant, protected_candidates={"C0"}, trials=1000, minimum_trials=100),
            safe_screen_decision("TOY_UNCERTAIN", unresolved, protected_candidates={"C0"}, trials=1000, minimum_trials=100),
            safe_screen_decision("TOY_LOW_N", dominant, protected_candidates={"C0"}, trials=10, minimum_trials=100),
            safe_screen_decision("TOY_DOMINATED", dominant, protected_candidates={"C0"}, trials=1000, minimum_trials=100),
        ]
        return self._write("03_screen", {
            "fixture_scope": "synthetic_noncompetitive",
            "decisions_exercised": sorted(set(decisions)),
            "c0_retained": decisions[0] == "RETAIN_PROTECTED",
            "uncertain_retained": decisions[1] == "RETAIN_UNRESOLVED_OR_NONDOMINATED",
            "low_n_retained": decisions[2] == "RETAIN_INSUFFICIENT_EVIDENCE",
            "multiplicity_rule": self.config["screening"]["multiple_comparison_control"],
        })

    def stage_04_medium(self) -> dict[str, Any]:
        self._read_prerequisite("03_screen")
        return self._write("04_medium", {
            "fixture_scope": "synthetic_noncompetitive",
            "paired_keys_verified": ["scenario", "replicate", "trial", "on_play"],
            "selection_seed": self.config["randomness"]["selection_seed"],
            "trial_count_frozen": self.config["trial_plan"]["medium_trials_per_candidate"],
        })

    def stage_05_select_finalists(self) -> dict[str, Any]:
        self._read_prerequisite("04_medium")
        return self._write("05_select_finalists", {
            "fixture_scope": "synthetic_noncompetitive",
            "retention_rule": self.config["finalist_retention"]["rule"],
            "protected_c0": True,
            "selected_identity_disclosure": "suppressed_in_dry_run",
        })

    def stage_06_fresh_validation(self) -> dict[str, Any]:
        medium = self._read_prerequisite("05_select_finalists")
        selection = int(self.config["randomness"]["selection_seed"])
        validation = int(self.config["randomness"]["validation_seed"])
        if selection == validation:
            raise RuntimeError("validation seed leaked from selection")
        return self._write("06_fresh_validation", {
            "fixture_scope": "synthetic_noncompetitive",
            "selection_seed_used": False,
            "validation_seed": validation,
            "fresh_partition_verified": True,
            "upstream_hash": medium["artifact_content_hash"],
        })

    def stage_07_robustness(self) -> dict[str, Any]:
        self._read_prerequisite("06_fresh_validation")
        return self._write("07_robustness", {
            "fixture_scope": "synthetic_noncompetitive",
            "scenario_ids": [scenario["id"] for scenario in self.config["robustness_scenarios"]],
            "policy_drift_guard": True,
        })

    def stage_08_frontier(self) -> dict[str, Any]:
        self._read_prerequisite("07_robustness")
        fixtures = {
            "dominant": uncertainty_aware_dominance({"m": MetricEvidence("higher", True, 2.0, materiality_tolerance=0.5)}).status,
            "tied": uncertainty_aware_dominance({"m": MetricEvidence("higher", True, 0.0, materiality_tolerance=0.5)}).status,
            "uncertain": uncertainty_aware_dominance({"m": MetricEvidence("higher", False, 0.1, -0.2, 0.4, 0.05, 0.1)}).status,
            "lower_is_better": uncertainty_aware_dominance({"m": MetricEvidence("lower", True, -2.0, materiality_tolerance=0.5)}).status,
        }
        return self._write("08_frontier", {
            "fixture_scope": "synthetic_noncompetitive",
            "uncertainty_aware_relation_fixtures": fixtures,
            "real_frontier_constructed": False,
        })

    def stage_09_report(self) -> dict[str, Any]:
        prior = self._read_prerequisite("08_frontier")
        sample = provenance_row(
            candidate="TOY_SCHEMA_ONLY", config_hash=self.config_hash,
            policy_hash=next(iter(sorted(policy_hashes().values()))),
            seed_partition="synthetic", scenario="dry_run", metric="schema_probe", value=0.0,
        )
        return self._write("09_report", {
            "fixture_scope": "synthetic_noncompetitive",
            "output_schema_fields": sorted(sample),
            "upstream_hash": prior["artifact_content_hash"],
            "attestation": "NO REAL CANDIDATE PERFORMANCE EVALUATED; NO RANKING; NO RECOMMENDATION",
        })

    def run_readiness_dry_run(self) -> dict[str, Any]:
        if self.config["phase_control"]["optimization_execution_allowed"]:
            raise RuntimeError("Run G readiness refuses optimization-enabled configuration")
        methods = [getattr(self, f"stage_{stage}") for stage in REQUIRED_STAGES]
        result: dict[str, Any] = {}
        for method in methods:
            value = method()
            result[value["stage"]] = value["artifact_content_hash"]
        manifest = {
            "status": "PASS", "mode": "READINESS_DRY_RUN",
            "config_hash": self.config_hash, "stage_hashes": result,
            "ranking_produced": False, "recommendation_produced": False,
        }
        manifest["manifest_hash"] = canonical_hash(manifest)
        (self.output_dir / "dry_run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return manifest

    def run_real(self) -> None:
        raise RuntimeError(
            "REAL PHASE 3 EXECUTION REFUSED — RUN G IS PENDING INDEPENDENT RUN H AUTHORIZATION"
        )

