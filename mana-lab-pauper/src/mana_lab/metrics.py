from __future__ import annotations

import csv
import gzip
from collections import Counter, defaultdict
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping


EVENT_FIELDS = [
    "candidate",
    "scenario",
    "replicate",
    "trial",
    "pairing_id",
    "on_play",
    "raw_opening_lands",
    "raw_W",
    "raw_U",
    "raw_B",
    "raw_R",
    "raw_joint_UB",
    "mulligans",
    "kept_hand_size",
    "usable_mana_t1",
    "usable_mana_t2",
    "usable_mana_t3",
    "usable_mana_t4",
    "W_t2",
    "U_t2",
    "B_t2",
    "R_t2",
    "UB_t2",
    "artifacts_t3",
    "metalcraft_t3",
    "opponent_options_t3",
    "boulder_deployed",
    "policy_decisions",
    "spells_cast",
]


class GzipEventWriter:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = gzip.open(self.path, "wt", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(self._handle, fieldnames=EVENT_FIELDS, extrasaction="ignore")
        self._writer.writeheader()

    def write(self, row: dict[str, Any]) -> None:
        self._writer.writerow(row)

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "GzipEventWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class SmokeAggregator:
    def __init__(self) -> None:
        self.count = 0
        self.sums: Counter[str] = Counter()
        self.opening_lands: Counter[int] = Counter()
        self.mulligans: Counter[int] = Counter()

    def add(self, row: dict[str, Any]) -> None:
        self.count += 1
        self.opening_lands[int(row["raw_opening_lands"])] += 1
        self.mulligans[int(row["mulligans"])] += 1
        for field in EVENT_FIELDS:
            value = row.get(field)
            if isinstance(value, bool):
                self.sums[field] += int(value)
            elif isinstance(value, (int, float)) and field not in {"trial", "raw_opening_lands", "mulligans", "kept_hand_size"}:
                self.sums[field] += value

    def summary(self) -> dict[str, Any]:
        if not self.count:
            return {"trials": 0}
        return {
            "trials": self.count,
            "raw_opening_land_distribution": {str(key): value / self.count for key, value in sorted(self.opening_lands.items())},
            "mulligan_distribution": {str(key): value / self.count for key, value in sorted(self.mulligans.items())},
            "rates_and_means": {key: value / self.count for key, value in sorted(self.sums.items())},
        }


OVERLAP_FAMILIES = {
    "spell_miss_etb_unavailable": ["spell_miss", "ETB_block", "unavailable_mana"],
    "color_and_castability": ["color_access", "castability"],
    "boulder_and_castability": ["Boulder_rescue", "castability"],
    "artifact_affinity_metalcraft": ["artifact_count", "affinity_reduction", "Metalcraft"],
    "metalcraft_full_effect": ["Metalcraft", "full_effect_interaction"],
    "mulligan_early_castability": ["mulligan_quality", "early_castability"],
}


# Objective components are intentionally mappings, not weights or a winner
# function.  Phase 3 may build named views from these raw events while keeping
# correlated families explicit and supporting leave-one-component-out checks.
OBJECTIVE_COMPONENT_REGISTRY = {
    "on_time_castability": {"events": ["spell_window", "spell_cast"], "correlated_family": "color_and_castability"},
    "stranded_spell": {"events": ["spell_window"], "correlated_family": "spell_miss_etb_unavailable"},
    "etb_blockage": {"events": ["etb_tempo"], "correlated_family": "spell_miss_etb_unavailable"},
    "usable_mana": {"events": ["state_snapshot"], "correlated_family": "spell_miss_etb_unavailable"},
    "boulder_rescue": {"events": ["boulder_filter", "spell_window", "payment"], "correlated_family": "boulder_and_castability"},
    "artifact_thresholds": {"events": ["state_snapshot", "bargain_cast", "glint_hawk_return"], "correlated_family": "artifact_affinity_metalcraft"},
    "interaction_availability": {"events": ["opponent_window"], "correlated_family": "interaction_availability_timing"},
    "mulligan_quality": {"events": ["opening_hand"], "correlated_family": "mulligan_early_castability"},
    "multi_action": {"events": ["multi_action_window", "policy_action_sequence"], "correlated_family": "multi_action_castability"},
}


RAW_EVENT_CONTRACT = {
    "opening_hand": {"denominator": "trial", "timing": "after London keep and bottom"},
    "state_snapshot": {"denominator": "trial-window", "timing": "named decision window"},
    "spell_window": {"denominator": "card-copy/profile/turn while in hand", "timing": "named decision window"},
    "etb_tempo": {"denominator": "land play", "timing": "immediately after land entry"},
    "multi_action_window": {"denominator": "own-main start", "timing": "before policy spending"},
    "boulder_filter": {"denominator": "Boulder activation", "timing": "during payment"},
    "bargain_cast": {"denominator": "Bargain cast", "timing": "after payment and sacrifice, before draw"},
    "glint_hawk_return": {"denominator": "Hawk trigger resolution", "timing": "after return"},
    "opponent_window": {"denominator": "interaction card/window", "timing": "end own turn"},
}


def _metric(
    source: list[str], numerator: str, denominator: str, timing: str,
    grain: str, opportunity_id: str, missing: str, snapshot_role: str,
    direction: str, family: str, *, status: str = "phase3",
) -> dict[str, Any]:
    return {
        "event_source": source,
        "numerator": numerator,
        "denominator": denominator,
        "timing": timing,
        "aggregation_grain": grain,
        "opportunity_id": opportunity_id,
        "deduplication": "exactly one row per opportunity_id and event_role; reject duplicates",
        "missing_data": missing,
        "snapshot_role": snapshot_role,
        "direction": direction,
        "correlated_family": family,
        "status": status,
    }


# Authoritative Run E Phase-3 registry.  Fixture-only options remain explicit
# but are not advertised as production aggregates.
PHASE3_METRIC_REGISTRY = {
    "opening_land_distribution": _metric(["opening_hand"], "count by opening_land_count", "all trials", "pre-mulligan seven", "trial", "trial_id", "error", "pre-spend", "descriptive", "mulligan_early_castability"),
    "mulligan_count_and_kept_hand_size": _metric(["opening_hand"], "mulligans and keep_size", "all trials", "after London bottom", "trial", "trial_id", "error", "pre-spend", "lower/contextual", "mulligan_early_castability"),
    "usable_untapped_mana_by_turn": _metric(["state_snapshot"], "usable_untapped_mana", "primary_pre_spend snapshot", "start_own_main", "trial-turn", "trial_id+turn+event_role", "error", "pre-spend", "higher", "spell_miss_etb_unavailable"),
    "W_U_B_R_access_by_turn": _metric(["state_snapshot"], "color in direct_colors or available_filtered_colors", "primary_pre_spend snapshot", "start_own_main", "trial-turn-color", "trial_id+turn+color", "error", "pre-spend", "higher", "color_and_castability"),
    "joint_UB_access_by_turn": _metric(["state_snapshot"], "joint_UB true", "primary_pre_spend snapshot", "start_own_main", "trial-turn", "trial_id+turn", "error", "pre-spend", "higher", "color_and_castability"),
    "spell_level_on_time_castability": _metric(["spell_window", "spell_cast", "spell_resolution"], "castable or functional resolution for card_instance", "one primary_pre_spend opportunity per card/profile/turn", "start_own_main; execution linked by related_opportunity_ids", "card-instance-profile-turn", "spell_window.opportunity_id", "opportunity absent means card not in hand and is excluded", "pre-spend opportunity", "higher", "color_and_castability"),
    "opponent_turn_interaction_availability": _metric(["opponent_window"], "payable and resource_preserved", "interaction card present at modeled opponent window", "end own turn", "trial-turn-card", "trial_id+turn+card", "in_hand false is explicit non-opportunity", "post-spend remainder", "higher", "interaction_availability_timing"),
    "full_effect_metalcraft_interaction_availability": _metric(["opponent_window", "state_snapshot"], "payable and metalcraft", "interaction card present", "end own turn", "trial-turn-card", "trial_id+turn+card", "in_hand false is explicit non-opportunity", "post-spend remainder", "higher", "artifact_affinity_metalcraft"),
    "double_spell_success": _metric(["multi_action_window", "policy_action_sequence", "spell_resolution"], "at least two functional resolutions", "own-main start", "own main", "trial-turn", "trial_id+turn+start_own_main", "error", "pre-spend feasibility and realized execution", "higher", "multi_action_castability"),
    "spell_plus_held_interaction_success": _metric(["multi_action_window", "spell_resolution", "opponent_window"], "functional spell and payable reply", "own-main start", "own main through opponent window", "trial-turn", "trial_id+turn", "error", "mixed pre/post explicitly joined", "higher", "interaction_availability_timing"),
    "artifact_count_by_window": _metric(["state_snapshot"], "artifact_count", "named primary snapshot", "start or end named window", "trial-turn-window", "trial_id+turn+event_role", "error", "declared by event_role", "descriptive", "artifact_affinity_metalcraft"),
    "metalcraft_rate_by_window": _metric(["state_snapshot"], "metalcraft true", "named primary snapshot", "start or end named window", "trial-turn-window", "trial_id+turn+event_role", "error", "declared by event_role", "higher", "artifact_affinity_metalcraft"),
    "affinity_reduction_by_spell_and_turn": _metric(["spell_cast"], "affinity_reduction", "affinity spell cast", "payment", "cast", "trial_id+spell uid+event_id", "no cast is no execution opportunity", "post-payment", "higher/contextual", "artifact_affinity_metalcraft"),
    "boulder_deploy_activation_rescue_dependency": _metric(["boulder_deployed", "boulder_filter", "boulder_usage"], "separate used/rescue/dependency booleans", "deployment or payment event", "resolution/payment", "event", "trial_id+event_id", "explicit false required when used but native payment exists", "payment", "descriptive", "boulder_and_castability"),
    "cryogen_enter_leave_draw_events": _metric(["draw", "information_node"], "draw count by reason", "Cryogen enter/leave trigger", "trigger resolution", "trigger", "trial_id+event_id", "zero only when trigger event explicitly absent", "information resolution", "descriptive", "card_draw_execution"),
    "glint_hawk_functional_execution_and_return_cost": _metric(["spell_cast", "spell_resolution", "glint_hawk_return", "hawk_land_replay"], "functional resolution and resource-loss fields", "Hawk raw cast", "resolution/replay", "Hawk instance", "trial_id+card uid", "error if cast lacks resolution", "execution outcome", "higher/contextual", "hawk_resource"),
    "bargain_functional_execution_and_sacrifice_resource_loss": _metric(["bargain_cast", "spell_resolution"], "functional and explicit land/color/untapped/artifact deltas", "Bargain raw cast", "after sacrifice before draws", "Bargain instance", "trial_id+card uid", "error if cast lacks outcome", "pre-draw cost state", "contextual", "bargain_resource"),
    "critical_sequence_success": _metric(["spell_resolution", "glint_hawk_return", "opponent_window"], "named sequence predicate", "trial", "through configured turn", "trial-sequence", "trial_id+sequence id", "false only after complete trace", "mixed declared sequence", "higher", "critical_sequence"),
    "stranded_spell_reason": _metric(["spell_window"], "failure_reason count when castable false", "primary_pre_spend due opportunity", "start_own_main", "card-instance-profile-turn", "spell_window.opportunity_id", "exclude absent cards", "pre-spend", "lower", "spell_miss_etb_unavailable"),
    "realized_etb_tapped_block": _metric(["etb_tempo"], "blocked_action true", "land play", "immediately after entry", "land play", "trial_id+land uid+event_id", "error", "post-entry", "lower", "spell_miss_etb_unavailable"),
    "unused_mana": _metric(["state_snapshot"], "usable_untapped_mana", "primary_post_spend snapshot", "end_own_turn_opponent_window", "trial-turn", "trial_id+turn+event_role", "error", "post-spend remainder", "lower/contextual", "spell_miss_etb_unavailable"),
    "unavailable_tapped_mana": _metric(["state_snapshot"], "unavailable_tapped_mana", "named primary snapshot", "named window", "trial-turn-window", "trial_id+turn+event_role", "error", "declared by event_role", "lower/contextual", "spell_miss_etb_unavailable"),
    "nihil_optional_black_draw_option": _metric(["nihil_draw_opportunity", "nihil_draw_paid", "nihil_draw_declined"], "payable and paid separately", "Nihil grave trigger", "trigger resolution before parent spell", "trigger", "nihil opportunity_id", "error if trigger lacks paid/declined outcome", "option resolution", "descriptive", "card_draw_execution"),
    "scry_decision_outcome": _metric(["scry_reveal", "scry_resolve"], "kept/bottomed identities", "scry event", "resolution", "scry", "trial_id+event_id", "error if reveal lacks resolution in executed trace", "information resolution", "descriptive", "card_draw_execution"),
    "land_return_events": _metric(["glint_hawk_return", "hawk_land_replay"], "return and replay resource loss", "land returned", "Hawk resolution/replay", "returned land instance", "trial_id+uid+return event", "replay may be absent and is explicit", "execution outcome", "lower/contextual", "hawk_resource"),
    "land_sacrifice_events": _metric(["bargain_cast"], "battlefield_land_loss/colors_lost/untapped_source_loss", "Bargain cast", "additional-cost payment", "cast", "trial_id+event_id", "zero fields required for nonland sacrifice", "pre-draw cost state", "lower", "bargain_resource"),
    "blood_token_activation_option": _metric(["blood_activation"], "fixture execution only", "targeted fixture", "fixture", "fixture", "fixture id", "not produced by normal planner", "validation-only", "descriptive", "validation_option", status="validation_only"),
    "munitions_activation_option": _metric(["munitions_activation"], "fixture execution only", "targeted fixture", "fixture", "fixture", "fixture id", "not produced by normal planner", "validation-only", "descriptive", "validation_option", status="validation_only"),
    "cryogen_stun_activation_option": _metric(["cryogen_stun_activation"], "fixture execution only", "targeted tapped-creature fixture", "fixture", "fixture", "fixture id", "not produced by normal planner", "validation-only", "descriptive", "validation_option", status="validation_only"),
}


RUN_E_EVENT_CONTRACT = {
    **RAW_EVENT_CONTRACT,
    "spell_resolution": {"denominator": "raw spell cast", "timing": "mandatory resolution outcome"},
    "information_node": {"denominator": "unrevealed draw/scry effect", "timing": "planning boundary"},
    "nihil_draw_opportunity": {"denominator": "Nihil grave trigger", "timing": "trigger resolution"},
}


def validate_metric_registry(configured_metrics: Iterable[str]) -> None:
    missing = set(configured_metrics) - set(PHASE3_METRIC_REGISTRY)
    if missing:
        raise ValueError(f"metrics missing registry definitions: {sorted(missing)}")
    required = {
        "event_source", "numerator", "denominator", "timing", "aggregation_grain",
        "opportunity_id", "deduplication", "missing_data", "snapshot_role",
        "direction", "correlated_family", "status",
    }
    for name in configured_metrics:
        absent = required - set(PHASE3_METRIC_REGISTRY[name])
        if absent:
            raise ValueError(f"metric {name} missing fields: {sorted(absent)}")


def objective_components(*, leave_out: str | None = None, decorrelated: bool = False) -> dict[str, dict[str, Any]]:
    components = {name: dict(value) for name, value in OBJECTIVE_COMPONENT_REGISTRY.items() if name != leave_out}
    if not decorrelated:
        return components
    seen: set[str] = set()
    result: dict[str, dict[str, Any]] = {}
    for name, value in components.items():
        family = str(value["correlated_family"])
        if family in seen:
            continue
        seen.add(family)
        result[name] = value
    return result


@dataclass(frozen=True)
class MetricEvidence:
    direction: str
    exact: bool
    difference: float
    confidence_low: float | None = None
    confidence_high: float | None = None
    no_worse_tolerance: float = 0.0
    materiality_tolerance: float = 0.0


@dataclass(frozen=True)
class DominanceResult:
    status: str
    no_worse_dimensions: tuple[str, ...]
    materially_better_dimensions: tuple[str, ...]
    unresolved_dimensions: tuple[str, ...]
    materially_worse_dimensions: tuple[str, ...]


def uncertainty_aware_dominance(evidence: Mapping[str, MetricEvidence]) -> DominanceResult:
    """Classify left versus right without treating noisy means as dominance.

    Differences are always left-minus-right.  For a lower-is-better metric the
    sign is reversed before applying practical and statistical thresholds.
    Stochastic dimensions require paired confidence bounds.
    """
    if not evidence:
        raise ValueError("dominance comparison requires at least one dimension")
    no_worse: list[str] = []
    better: list[str] = []
    unresolved: list[str] = []
    worse: list[str] = []
    equivalent: list[str] = []
    for name, item in evidence.items():
        if item.direction not in {"higher", "lower"}:
            raise ValueError(f"metric {name} has invalid direction {item.direction}")
        numeric = [item.difference, item.no_worse_tolerance, item.materiality_tolerance]
        if any(not isfinite(float(value)) for value in numeric):
            raise ValueError(f"metric {name} contains a non-finite estimate/tolerance")
        if item.no_worse_tolerance < 0 or item.materiality_tolerance < 0:
            raise ValueError(f"metric {name} tolerances must be non-negative")
        sign = 1.0 if item.direction == "higher" else -1.0
        estimate = sign * item.difference
        if item.exact:
            low = high = estimate
        else:
            if item.confidence_low is None or item.confidence_high is None:
                unresolved.append(name)
                continue
            if not isfinite(float(item.confidence_low)) or not isfinite(float(item.confidence_high)):
                raise ValueError(f"metric {name} confidence interval must be finite")
            if item.confidence_low > item.confidence_high:
                raise ValueError(f"metric {name} confidence interval is reversed")
            if sign > 0:
                low, high = float(item.confidence_low), float(item.confidence_high)
            else:
                low, high = -float(item.confidence_high), -float(item.confidence_low)
        if high < -item.no_worse_tolerance:
            worse.append(name)
        elif low >= -item.no_worse_tolerance:
            no_worse.append(name)
            if low > item.materiality_tolerance:
                better.append(name)
            elif low >= -item.materiality_tolerance and high <= item.materiality_tolerance:
                equivalent.append(name)
            else:
                # One-sided no-worse evidence is not two-sided equivalence.
                unresolved.append(name)
        else:
            unresolved.append(name)

    if worse:
        status = "dominated_or_incomparable"
    elif unresolved:
        status = "unresolved"
    elif better:
        status = "dominates"
    elif len(equivalent) == len(evidence):
        status = "practically_equivalent"
    else:
        status = "unresolved"
    return DominanceResult(status, tuple(no_worse), tuple(better), tuple(unresolved), tuple(worse))


def pareto_dominates(left: dict[str, float], right: dict[str, float], metrics: Iterable[str]) -> bool:
    """Compatibility predicate for exact fixtures; Phase 3 uses evidence rows.

    Known stochastic registry metrics deliberately remain unresolved when only
    point estimates are supplied.  Unknown fixture dimensions are treated as
    exact higher-is-better values for the legacy deterministic tests.
    """
    evidence: dict[str, MetricEvidence] = {}
    for name in metrics:
        definition = PHASE3_METRIC_REGISTRY.get(name)
        if definition:
            raw_direction = str(definition["direction"])
            direction = "lower" if raw_direction.startswith("lower") else "higher"
            exact = False
        else:
            direction = "higher"
            exact = True
        evidence[name] = MetricEvidence(direction=direction, exact=exact, difference=left[name] - right[name])
    return uncertainty_aware_dominance(evidence).status == "dominates"


def profile_regret(values: dict[str, float], best_by_profile: dict[str, float]) -> dict[str, float]:
    return {profile: best_by_profile[profile] - value for profile, value in values.items()}
