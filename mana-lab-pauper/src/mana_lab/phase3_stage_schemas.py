"""Run I typed, fail-closed Phase-3 stage envelope contracts.

These schemas describe the current machinery-validation stages. They do NOT
claim that the still-unimplemented live candidate stages are ready to optimize.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, TypedDict


class RawEventPayload(TypedDict):
    file: str
    content_hash: str
    trial_stream_count: int
    format: str


class CandidatePayload(TypedDict):
    candidate_count: int
    candidate_payload: str
    candidate_payload_hash: str
    canonical_candidate_set_sha256: str
    protected_candidate_ids: list[str]
    c0_occurrences: int
    three_bridge_count: int


class StageEnvelope(TypedDict):
    stage: str
    status: str
    mode: str
    stage_schema_version: str
    scientific_config_hash: str
    code_tree_hash: str
    policy_identity_hash: str
    seed_identity_hash: str
    prerequisite_hash: str | None
    control_metadata: dict[str, Any]
    ranking_produced: bool
    recommendation_produced: bool
    payload: dict[str, Any]
    artifact_content_hash: str


SHA256 = re.compile(r"^[a-f0-9]{64}$")


STAGE_REQUIRED: dict[str, dict[str, type]] = {
    "01_validate": {
        "scientific_config_validated": bool,
        "policy_hashes": dict,
        "control_is_not_part_of_scientific_hash": bool,
    },
    "02_enumerate": {
        "candidate_count": int,
        "candidate_payload": str,
        "candidate_payload_hash": str,
        "canonical_candidate_set_sha256": str,
        "protected_candidate_ids": list,
        "c0_occurrences": int,
        "three_bridge_count": int,
    },
    "03_screen": {
        "candidate_payload_hash": str,
        "all_candidate_identities_carried": int,
        "protected_candidate_ids": list,
        "candidate_neutral_pairing": dict,
        "raw_event_payload": dict,
        "trace_derived_tables": dict,
        "screening_ledger_probe": dict,
        "real_candidate_performance_screened": bool,
    },
    "04_medium": {
        "protected_candidate_ids": list,
        "candidate_payload_hash": str,
        "all_candidate_identities_carried": int,
        "selection_seed": int,
        "paired_keys_verified": list,
        "real_candidate_performance_screened": bool,
    },
    "05_select_finalists": {
        "protected_candidate_ids": list,
        "candidate_payload_hash": str,
        "all_candidate_identities_carried": int,
        "selection_disabled_in_remediation": bool,
        "real_candidate_performance_screened": bool,
    },
    "06_fresh_validation": {
        "protected_candidate_ids": list,
        "candidate_payload_hash": str,
        "all_candidate_identities_carried": int,
        "validation_seed": int,
        "fresh_partition_verified": bool,
        "real_candidate_performance_screened": bool,
    },
    "07_robustness": {
        "protected_candidate_ids": list,
        "candidate_payload_hash": str,
        "all_candidate_identities_carried": int,
        "executed_policy_tuples": list,
        "raw_event_payload": dict,
        "trace_derived_robustness_rows": list,
        "real_candidate_performance_screened": bool,
    },
    "08_frontier": {
        "protected_candidate_ids": list,
        "candidate_payload_hash": str,
        "all_candidate_identities_carried": int,
        "frontier_algorithm_available_but_not_executed_on_real_candidates": bool,
        "real_candidate_performance_screened": bool,
    },
    "09_report": {
        "protected_candidate_ids": list,
        "candidate_payload_hash": str,
        "all_candidate_identities_carried": int,
        "output_schema_fields": list,
        "attestation": str,
        "real_candidate_performance_screened": bool,
    },
}


def validate_stage_envelope(stage: str, value: Mapping[str, Any]) -> None:
    if stage not in STAGE_REQUIRED:
        raise ValueError(f"unsupported stage schema: {stage}")
    if value.get("stage") != stage:
        raise ValueError("stage identity mismatch")
    if value.get("status") != "PASS":
        raise ValueError("stage status is not PASS")
    if value.get("mode") != "RUN_I_PRODUCTION_MACHINERY_VALIDATION":
        raise ValueError("stage mode mismatch")
    if value.get("stage_schema_version") != "mana-lab-run-i-stage-v1":
        raise ValueError("stage schema version mismatch")
    for field in (
        "scientific_config_hash", "code_tree_hash",
        "policy_identity_hash", "seed_identity_hash",
        "artifact_content_hash",
    ):
        if not isinstance(value.get(field), str) or not SHA256.fullmatch(value[field]):
            raise ValueError(f"invalid stage hash: {field}")
    previous = value.get("prerequisite_hash")
    if previous is not None and (
        not isinstance(previous, str) or not SHA256.fullmatch(previous)
    ):
        raise ValueError("invalid prerequisite hash")
    for flag in ("ranking_produced", "recommendation_produced"):
        if value.get(flag) is not False:
            raise ValueError(f"remediation unexpectedly produced {flag}")
    control = value.get("control_metadata")
    if not isinstance(control, dict) or not isinstance(
        control.get("optimization_execution_allowed"), bool
    ) or not isinstance(control.get("authorization_status"), str):
        raise ValueError("malformed control metadata")
    payload = value.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("missing typed stage payload")
    for field, expected in STAGE_REQUIRED[stage].items():
        if field not in payload or type(payload[field]) is not expected:
            raise ValueError(f"{stage} payload missing/invalid {field}")
    if stage != "01_validate":
        if stage == "02_enumerate":
            if (
                payload["candidate_count"] != 296706
                or payload["c0_occurrences"] != 1
                or payload["three_bridge_count"] != 56
                or len(set(payload["protected_candidate_ids"])) != 57
            ):
                raise ValueError("candidate/protection schema invariant failed")
        else:
            if (
                payload["all_candidate_identities_carried"] != 296706
                or len(set(payload["protected_candidate_ids"])) != 57
            ):
                raise ValueError(f"{stage} lost candidate/protection identities")
    if stage in {"03_screen", "07_robustness"}:
        record = payload["raw_event_payload"]
        for field, kind in (
            ("file", str), ("content_hash", str),
            ("trial_stream_count", int), ("format", str),
        ):
            if type(record.get(field)) is not kind:
                raise ValueError(f"invalid raw event contract: {field}")
        if not SHA256.fullmatch(record["content_hash"]) or record["trial_stream_count"] <= 0:
            raise ValueError("invalid raw event hash/count")
    if stage == "03_screen":
        ledger = payload["screening_ledger_probe"]
        if (
            ledger.get("family_id") != "run_i_candidate_neutral_machinery"
            or ledger.get("registered_claim_count") != 1
            or ledger.get("history_rows") != 1
            or ledger.get("status") != "RETAIN_INSUFFICIENT_EVIDENCE"
            or ledger.get("real_candidate_evidence") is not False
            or not isinstance(ledger.get("audit_hash"), str)
            or not SHA256.fullmatch(ledger["audit_hash"])
        ):
            raise ValueError("invalid candidate-neutral screening ledger proof")
    if stage == "09_report" and not payload["attestation"].startswith("NO REAL CANDIDATE PERFORMANCE RANKING"):
        raise ValueError("missing no-optimization attestation")
