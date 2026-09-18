from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .cards import load_deck
from .candidates import candidate_count_report
from .phase3_config import load_phase3_config, sha256_file, validate_phase3_config
from .phase3_depth import planner_depth_audit
from .phase3_metrics import validate_aggregation_coverage
from .phase3_pipeline import Phase3Pipeline
from .phase3_policies import validate_policy_freeze
from .provenance import validate_manifest


EXPECTED_PARENT_SHA256 = "82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71"


def validate_mechanic_registry(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    allowed = {"IMPLEMENTED + TESTED", "IMPLEMENTED, NEEDS TEST", "NOT IMPLEMENTED", "NOT MATERIAL"}
    required = {
        "artifact lands", "ETB-tapped Bridges", "Giant's Boulder filtering and tap limits",
        "affinity and generic cost reduction", "artifact count and Metalcraft",
        "Baleful Strix distinct UB payment", "Dispatch white payment",
        "Dispatch Metalcraft distinction", "Glint Hawk return and replay",
        "Reckoner's Bargain payment sacrifice and resource effects",
        "Thoughtcast affinity and draw", "Myr Enforcer affinity",
        "Refurbished Familiar affinity", "Utrom Monitor affinity",
        "Cryogen Relic enter and leave draws",
        "opponent-turn Blast Dispatch Bargain availability", "Blood token activation",
        "Nihil Spellbomb optional black draw", "Makeshift Munitions activation",
        "Cryogen stun activation", "London mulligan", "play versus draw",
    }
    names = {row["mechanic"] for row in rows}
    if required - names:
        raise ValueError(f"mechanic registry missing: {sorted(required-names)}")
    for row in rows:
        if row["status"] not in allowed:
            raise ValueError(f"invalid mechanic status: {row['status']}")
        if row["ranking_relevance"] == "yes" and row["status"] != "IMPLEMENTED + TESTED":
            raise ValueError(f"ranking-relevant mechanic not implemented and tested: {row['mechanic']}")
        if row["readiness_blocker"] != "false":
            raise ValueError(f"mechanic readiness blocker remains: {row['mechanic']}")
        if row["status"] == "NOT MATERIAL" and not row["phase3_treatment"]:
            raise ValueError(f"NOT MATERIAL mechanic lacks containment: {row['mechanic']}")
    return {
        "rows": len(rows),
        "implemented_tested": sum(row["status"] == "IMPLEMENTED + TESTED" for row in rows),
        "not_material_contained": sum(row["status"] == "NOT MATERIAL" for row in rows),
        "ranking_relevant_gaps": 0,
    }


def run_full_tests(root: Path) -> dict[str, Any]:
    env = dict(os.environ)
    source = str(root / "src")
    env["PYTHONPATH"] = source + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True)
    text = result.stdout + result.stderr
    matches = re.findall(r"Ran (\d+) tests?", text)
    count = int(matches[-1]) if matches else 0
    return {"returncode": result.returncode, "tests": count, "output": text}


def run_gate(
    root: Path,
    config_path: Path,
    parent_zip: Path,
    *,
    run_tests: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    output = root / "outputs" / "run_g" / "readiness"
    output.mkdir(parents=True, exist_ok=True)
    checks: dict[str, Any] = {}
    failures: list[str] = []

    observed_parent = sha256_file(parent_zip) if parent_zip.is_file() else "MISSING"
    checks["parent_integrity"] = {
        "path": str(parent_zip), "expected_sha256": EXPECTED_PARENT_SHA256,
        "observed_sha256": observed_parent, "pass": observed_parent == EXPECTED_PARENT_SHA256,
    }
    if observed_parent != EXPECTED_PARENT_SHA256:
        failures.append("parent_integrity")

    try:
        config = load_phase3_config(config_path)
        validate_phase3_config(config, root)
        validate_policy_freeze(config["policies"])
        validate_aggregation_coverage()
        checks["config_policy_metric_contracts"] = {"pass": True, "config_hash": config["_config_hash"]}
    except Exception as exc:
        failures.append("config_policy_metric_contracts")
        checks["config_policy_metric_contracts"] = {"pass": False, "error": str(exc)}
        config = load_phase3_config(config_path)

    deck = load_deck(root / config["input"]["deck_spec"]["path"])
    candidate = candidate_count_report(deck)
    candidate_pass = candidate["enumeration_count"] == 296706 and candidate["dp_count"] == 296706 and candidate["c0_occurrences"] == 1
    checks["candidate_space"] = {"pass": candidate_pass, **candidate}
    if not candidate_pass:
        failures.append("candidate_space")

    try:
        mechanic = validate_mechanic_registry(root / config["mechanics"]["registry_path"])
        checks["mechanics"] = {"pass": True, **mechanic}
    except Exception as exc:
        failures.append("mechanics")
        checks["mechanics"] = {"pass": False, "error": str(exc)}

    depth = planner_depth_audit(deck)
    (output / "planner_depth_structural_audit.json").write_text(json.dumps(depth, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checks["planner_depth"] = depth
    if not depth["pass"] or not depth["reserve_sensitivity"]["both_executable"]:
        failures.append("planner_depth")

    dry_a = Phase3Pipeline(root, config, output / "dry_run_a").run_readiness_dry_run()
    dry_b = Phase3Pipeline(root, config, output / "dry_run_b").run_readiness_dry_run()
    dry_pass = dry_a["manifest_hash"] == dry_b["manifest_hash"] and not dry_a["ranking_produced"] and not dry_a["recommendation_produced"]
    checks["dry_run_reproducibility"] = {
        "pass": dry_pass, "manifest_hash_a": dry_a["manifest_hash"],
        "manifest_hash_b": dry_b["manifest_hash"], "ranking_produced": False,
    }
    if not dry_pass:
        failures.append("dry_run_reproducibility")

    manifest_path = root / "outputs" / "run_g" / "source_config_manifest.json"
    provenance_pass = manifest_path.is_file() and validate_manifest(root, manifest_path)
    checks["provenance_manifest"] = {"pass": provenance_pass, "path": str(manifest_path.relative_to(root))}
    if not provenance_pass:
        failures.append("provenance_manifest")

    if run_tests:
        tests = run_full_tests(root)
        (output / "unit_test_report.txt").write_text(tests.pop("output"), encoding="utf-8")
        tests["pass"] = tests["returncode"] == 0 and tests["tests"] >= 179
        checks["full_tests"] = tests
        if not tests["pass"]:
            failures.append("full_tests")
    else:
        checks["full_tests"] = {"pass": True, "skipped_by_internal_test_fixture": True}

    result = {
        "status": "PASS" if not failures else "FAIL",
        "verdict": (
            "RUN G IMPLEMENTATION — READY FOR INDEPENDENT PHASE 3 AUTHORIZATION"
            if not failures else "RUN G BLOCKED — PHASE 3 NOT READY"
        ),
        "failures": failures,
        "checks": checks,
        "no_optimization_attestation": {
            "real_candidate_performance_evaluated": False,
            "ranking_performed": False,
            "frontier_constructed": False,
            "recommendation_made": False,
        },
    }
    (output / "readiness_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run G non-optimizing Phase 3 readiness gate")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--parent-zip", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    result = run_gate(args.root, args.config, args.parent_zip)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

