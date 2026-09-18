from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .mulligan import ALTERNATE_MULLIGAN, BASELINE_MULLIGAN
from .policies import (
    ALTERNATE_ACTION_POLICY,
    ALTERNATE_LAND_POLICY,
    ALTERNATE_RESERVE_POLICY,
    ALTERNATE_SCRY_POLICY,
    BASELINE_ACTION_POLICY,
    BASELINE_INFORMATION_POLICY,
    BASELINE_LAND_POLICY,
    BASELINE_RESERVE_POLICY,
    BASELINE_SCRY_POLICY,
    CONSERVATIVE_INFORMATION_POLICY,
)


def _canonical_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# These records are the machine-readable policy contract.  A behavior change
# requires a version/contract update and therefore a new frozen hash.
_POLICY_CONTENT: dict[str, dict[str, Any]] = {
    BASELINE_LAND_POLICY: {
        "kind": "sequencing", "version": "run-g-1",
        "precedence": ["hard_deadline", "reserve", "land_preservation", "due_execution", "artifact_state", "future_joint", "future_color", "untapped", "spell_execution", "information"],
    },
    ALTERNATE_LAND_POLICY: {
        "kind": "sequencing", "version": "run-g-1",
        "precedence": ["hard_deadline", "reserve", "untapped", "land_preservation", "due_execution", "spell_execution", "artifact_state", "future_joint", "future_color", "information"],
    },
    BASELINE_MULLIGAN: {
        "kind": "mulligan", "version": "run-g-1",
        "rule": "London; at 7/6/5 keep 2-4 lands with visible two usable mana by T2; auto-keep four; exhaustive deterministic bottoming",
    },
    ALTERNATE_MULLIGAN: {
        "kind": "mulligan", "version": "run-g-1",
        "rule": "London; at 7/6/5 keep 2-5 lands; auto-keep four; same exhaustive deterministic bottoming",
    },
    BASELINE_SCRY_POLICY: {
        "kind": "scry", "version": "run-g-1",
        "rule": "revealed-pair only; visible land/color need, due spell, horizon value; no hidden-card inspection",
    },
    ALTERNATE_SCRY_POLICY: {
        "kind": "scry", "version": "run-g-1",
        "rule": "revealed-pair only; land stability, draw/development, horizon value; no hidden-card inspection",
    },
    BASELINE_RESERVE_POLICY: {
        "kind": "reserve", "version": "run-g-1",
        "rule": "reserve one currently demanded payable opponent-turn reply unless a hard proactive deadline would be missed",
    },
    ALTERNATE_RESERVE_POLICY: {
        "kind": "reserve", "version": "run-g-1",
        "rule": "tap-out development; reserve status is measured but contributes zero policy score",
    },
    BASELINE_INFORMATION_POLICY: {
        "kind": "information", "version": "run-g-1",
        "draw_1": 100, "draw_2": 190, "scry_2": 80,
    },
    CONSERVATIVE_INFORMATION_POLICY: {
        "kind": "information", "version": "run-g-1",
        "draw_1": 35, "draw_2": 60, "scry_2": 20,
    },
}


POLICY_REGISTRY: dict[str, dict[str, Any]] = {
    name: {"id": name, **content, "content_hash": _canonical_hash({"id": name, **content})}
    for name, content in _POLICY_CONTENT.items()
}


def policy_hashes() -> dict[str, str]:
    return {name: entry["content_hash"] for name, entry in sorted(POLICY_REGISTRY.items())}


def validate_policy_freeze(frozen: Mapping[str, Any]) -> None:
    requested = frozen.get("identities")
    if not isinstance(requested, Mapping) or not requested:
        raise ValueError("policy freeze must define identities")
    for role, item in requested.items():
        if not isinstance(item, Mapping):
            raise ValueError(f"policy role {role} must be a mapping")
        name = item.get("id")
        if name not in POLICY_REGISTRY:
            raise ValueError(f"unknown policy id for {role}: {name}")
        expected = POLICY_REGISTRY[str(name)]["content_hash"]
        if item.get("content_hash") != expected:
            raise ValueError(f"policy hash drift for {role}/{name}")

    required_roles = {
        "sequencing_baseline", "sequencing_alternate", "mulligan_baseline",
        "mulligan_alternate", "scry_baseline", "scry_alternate",
        "reserve_baseline", "reserve_alternate", "information_baseline",
        "information_alternate",
    }
    missing = required_roles - set(requested)
    if missing:
        raise ValueError(f"policy freeze missing roles: {sorted(missing)}")
