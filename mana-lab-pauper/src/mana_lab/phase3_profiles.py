from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import fmean
from typing import Any, Iterable, Mapping, Sequence

from .phase3_metrics import evaluate_critical_sequences, validate_event_stream
from .statistics import PairedEstimate, TrialObservation, paired_difference


@dataclass(frozen=True)
class ProfileComponentValue:
    metric: str
    value: float
    direction: str
    no_worse_tolerance: float
    materiality_tolerance: float
    population_id: str = ""
    aggregation: str = ""
    turns: tuple[int, ...] = ()
    scenarios: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProfileComponentComparison:
    metric: str
    population_id: str
    direction: str
    paired: PairedEstimate
    relation: str


def component_population_id(component: Mapping[str, Any]) -> str:
    return "|".join([
        str(component["metric"]),
        "turns=" + ",".join(str(turn) for turn in component["turns"]),
        "scenarios=" + ",".join(str(s) for s in component["scenarios"]),
        "aggregation=" + str(component["aggregation"]),
    ])


def _turn_weights(component: Mapping[str, Any]) -> dict[int, float]:
    turns = [int(turn) for turn in component["turns"]]
    text = str(component["aggregation"])
    parsed = {
        int(turn): float(weight)
        for turn, weight in re.findall(r"T(\d+)\s*=\s*([0-9]*\.?[0-9]+)", text)
    }
    if parsed:
        missing = set(turns) - set(parsed)
        if missing:
            # Explicitly mentioned weighted contracts may not silently omit a
            # configured turn.
            raise ValueError(f"aggregation weights omit turns: {sorted(missing)}")
        total = sum(parsed[turn] for turn in turns)
        if total <= 0:
            raise ValueError("turn weights must have positive total")
        return {turn: parsed[turn] / total for turn in turns}
    weight = 1.0 / len(turns)
    return {turn: weight for turn in turns}


def evaluate_profile(
    profile: Mapping[str, Any],
    metric_values: Mapping[str, float | None],
) -> tuple[ProfileComponentValue, ...]:
    """Build a transparent ordered vector from validated aggregate values.

    Population/window identity is part of each vector element. Consequently a
    changed aggregation or turn/scenario window is a different scientific
    quantity even if a caller supplies the same numeric scalar.
    """
    values: list[ProfileComponentValue] = []
    for component in profile["metric_vector"]:
        name = str(component["metric"])
        value = metric_values.get(name)
        missing = component["missing_data"]
        if value is None:
            if missing == "error":
                raise ValueError(f"profile metric missing: {name}")
            if missing == "exclude_component":
                continue
            raise ValueError(f"unsupported missing-data behavior for {name}: {missing}")
        if component["normalization"] != "none":
            raise ValueError("profiles permit only explicit raw-scale vectors")
        values.append(ProfileComponentValue(
            metric=name,
            value=float(value),
            direction=str(component["direction"]),
            no_worse_tolerance=float(component["no_worse_tolerance"]),
            materiality_tolerance=float(component["materiality_tolerance"]),
            population_id=component_population_id(component),
            aggregation=str(component["aggregation"]),
            turns=tuple(int(turn) for turn in component["turns"]),
            scenarios=tuple(str(scenario) for scenario in component["scenarios"]),
        ))
    if not values:
        raise ValueError("profile produced an empty vector")
    return tuple(values)


def compare_profile_vectors(
    left: tuple[ProfileComponentValue, ...],
    right: tuple[ProfileComponentValue, ...],
) -> str:
    """Exact-vector comparison; stochastic Phase 3 uses paired evidence below."""
    if [(item.metric, item.population_id) for item in left] != [
        (item.metric, item.population_id) for item in right
    ]:
        raise ValueError("profile vectors are not population-aligned")
    better = False
    worse = False
    for a, b in zip(left, right):
        signed = a.value - b.value if a.direction == "higher" else b.value - a.value
        if signed > a.materiality_tolerance:
            better = True
        elif signed < -a.materiality_tolerance:
            worse = True
    if better and not worse:
        return "better"
    if worse and not better:
        return "worse"
    if better and worse:
        return "conflict"
    return "practically_tied"


def _weighted_turn_mean(values: Mapping[int, Sequence[float]], component: Mapping[str, Any]) -> float:
    weights = _turn_weights(component)
    observed: dict[int, float] = {}
    for turn in weights:
        items = list(values.get(turn, ()))
        if not items:
            raise ValueError(f"profile population missing turn {turn}")
        observed[turn] = fmean(items)
    return sum(weights[turn] * observed[turn] for turn in weights)


def _trial_component_value(component: Mapping[str, Any], events: Iterable[Mapping[str, Any]]) -> float:
    rows = validate_event_stream(events)
    turns = set(int(turn) for turn in component["turns"])
    metric = str(component["metric"])
    declared_scenarios = set(str(value) for value in component["scenarios"])
    actual_scenario = str(rows[0]["scenario"])
    scenario_allowed = (
        actual_scenario in declared_scenarios
        or ("weighted_primary" in declared_scenarios and actual_scenario == "baseline_primary")
    )
    if not scenario_allowed:
        raise ValueError(
            f"profile component {metric} excludes scenario {actual_scenario}"
        )

    snapshots = [
        row for row in rows
        if row.get("event") == "state_snapshot"
        and row.get("event_role") == "primary_pre_spend_opportunity"
        and int(row.get("turn", 0)) in turns
    ]
    spell_windows = [
        row for row in rows
        if row.get("event") == "spell_window"
        and row.get("event_role") == "primary_pre_spend_opportunity"
        and int(row.get("turn", 0)) in turns
    ]

    if metric == "usable_untapped_mana_by_turn":
        by_turn: dict[int, list[float]] = {}
        for row in snapshots:
            by_turn.setdefault(int(row["turn"]), []).append(float(row["usable_untapped_mana"]))
        return _weighted_turn_mean(by_turn, component)

    if metric == "joint_UB_access_by_turn":
        by_turn: dict[int, list[float]] = {}
        for row in snapshots:
            by_turn.setdefault(int(row["turn"]), []).append(float(bool(row["joint_UB"])))
        return _weighted_turn_mean(by_turn, component)

    if metric == "realized_etb_tapped_block":
        opportunities = [
            row for row in rows
            if row.get("event") == "etb_tempo" and int(row.get("turn", 0)) in turns
        ]
        if not opportunities:
            return 0.0
        return fmean(float(bool(row.get("blocked_action"))) for row in opportunities)

    if metric == "spell_level_on_time_castability":
        text = str(component["aggregation"]).lower()
        subset = spell_windows
        if "colored spells" in text:
            subset = [
                row for row in subset
                if bool(row.get("colored_cost")) or row.get("card") in {"Baleful Strix", "Glint Hawk"}
            ]
        if "thoughtcast/myr enforcer/refurbished familiar/utrom monitor" in text:
            affinity = {"Thoughtcast", "Myr Enforcer", "Refurbished Familiar", "Utrom Monitor"}
            subset = [row for row in subset if row.get("card") in affinity]
        if not subset:
            raise ValueError("spell castability profile population is empty")
        weights = [float(row.get("weight", 1.0)) for row in subset]
        denominator = sum(weights)
        if denominator <= 0:
            raise ValueError("spell castability population has zero weight")
        return sum(weight * float(bool(row.get("castable"))) for row, weight in zip(subset, weights)) / denominator

    if metric in {"opponent_turn_interaction_availability", "full_effect_metalcraft_interaction_availability"}:
        opportunities = [
            row for row in rows
            if row.get("event") == "opponent_window"
            and row.get("interaction_in_hand")
            and int(row.get("turn", 0)) in turns
        ]
        if not opportunities:
            raise ValueError("interaction profile population is empty")
        if metric == "opponent_turn_interaction_availability":
            return fmean(float(bool(row.get("payable"))) for row in opportunities)
        return fmean(
            float(bool(row.get("payable")) and bool(row.get("metalcraft", row.get("full_effect", False))))
            for row in opportunities
        )

    if metric in {"double_spell_success", "spell_plus_held_interaction_success"}:
        field = "double_spell_feasible" if metric == "double_spell_success" else "spell_plus_interaction_feasible"
        windows = [
            row for row in rows
            if row.get("event") == "multi_action_window"
            and row.get("timing") == "start_own_main"
            and int(row.get("turn", 0)) in turns
        ]
        if not windows:
            raise ValueError("multi-action profile population is empty")
        by_turn: dict[int, list[float]] = {}
        for row in windows:
            by_turn.setdefault(int(row["turn"]), []).append(float(bool(row.get(field))))
        return _weighted_turn_mean(by_turn, component)

    if metric == "critical_sequence_success":
        predicates = evaluate_critical_sequences(rows)
        selected = [
            value for name, value in predicates.items()
            if any(int(token[1:]) in turns for token in re.findall(r"T\d+", name))
            or name.startswith("OPP_")
        ]
        if not selected:
            raise ValueError("critical-sequence population is empty")
        return fmean(float(value) for value in selected)

    raise ValueError(f"no executable profile aggregator for metric {metric}")


def aggregate_profile_events(
    profile: Mapping[str, Any],
    trials: Iterable[Iterable[Mapping[str, Any]]],
) -> tuple[ProfileComponentValue, ...]:
    """Execute one profile from raw schema-shaped trial traces."""
    trial_rows = [list(events) for events in trials]
    if not trial_rows:
        raise ValueError("profile aggregation requires trials")
    metric_values: dict[str, float] = {}
    for component in profile["metric_vector"]:
        values = [_trial_component_value(component, events) for events in trial_rows]
        metric_values[str(component["metric"])] = fmean(values)
    return evaluate_profile(profile, metric_values)


def compare_profile_trials(
    profile: Mapping[str, Any],
    left_trials: Iterable[Iterable[Mapping[str, Any]]],
    right_trials: Iterable[Iterable[Mapping[str, Any]]],
    *,
    confidence_z: float = 1.96,
) -> tuple[ProfileComponentComparison, ...]:
    """Compute paired per-component differences from aligned raw trials."""
    left = [list(rows) for rows in left_trials]
    right = [list(rows) for rows in right_trials]
    if len(left) != len(right) or not left:
        raise ValueError("profile paired trials must be nonempty and equally sized")
    output: list[ProfileComponentComparison] = []
    for component in profile["metric_vector"]:
        left_obs: list[TrialObservation] = []
        right_obs: list[TrialObservation] = []
        for lrows, rrows in zip(left, right):
            lvalid = validate_event_stream(lrows)
            rvalid = validate_event_stream(rrows)
            lkey = (
                str(lvalid[0]["scenario"]), lvalid[0]["replicate"],
                int(lvalid[0].get("trial_id", lvalid[0].get("trial"))),
                bool(lvalid[0]["on_play"]),
            )
            rkey = (
                str(rvalid[0]["scenario"]), rvalid[0]["replicate"],
                int(rvalid[0].get("trial_id", rvalid[0].get("trial"))),
                bool(rvalid[0]["on_play"]),
            )
            if lkey != rkey:
                raise ValueError("profile trial identities are not paired")
            left_obs.append(TrialObservation(*lkey, _trial_component_value(component, lvalid), candidate="left"))
            right_obs.append(TrialObservation(*rkey, _trial_component_value(component, rvalid), candidate="right"))
        estimate = paired_difference(left_obs, right_obs, confidence_z)
        sign = 1.0 if component["direction"] == "higher" else -1.0
        low = estimate.confidence_low * sign
        high = estimate.confidence_high * sign
        if sign < 0:
            low, high = min(low, high), max(low, high)
        no_worse = float(component["no_worse_tolerance"])
        material = float(component["materiality_tolerance"])
        if high < -no_worse:
            relation = "worse"
        elif low > material:
            relation = "better"
        elif low >= -material and high <= material:
            relation = "practically_tied"
        else:
            relation = "unresolved"
        output.append(ProfileComponentComparison(
            metric=str(component["metric"]),
            population_id=component_population_id(component),
            direction=str(component["direction"]),
            paired=estimate,
            relation=relation,
        ))
    return tuple(output)


def compare_profile_comparisons(comparisons: Sequence[ProfileComponentComparison]) -> str:
    relations = {item.relation for item in comparisons}
    if "worse" in relations and "better" in relations:
        return "conflict"
    if "worse" in relations:
        return "worse"
    if "unresolved" in relations:
        return "unresolved"
    if "better" in relations:
        return "better"
    return "practically_tied"


def leave_one_component_out(profile: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    variants: dict[str, dict[str, Any]] = {}
    for component in profile["metric_vector"]:
        omitted = component["metric"]
        variant = dict(profile)
        variant["metric_vector"] = [
            dict(item) for item in profile["metric_vector"] if item["metric"] != omitted
        ]
        if variant["metric_vector"]:
            variants[f"without__{omitted}"] = variant
    return variants


def decorrelated_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    declared = profile["decorrelated_variant"]
    keep = list(declared["metrics"])
    by_name = {item["metric"]: dict(item) for item in profile["metric_vector"]}
    missing = set(keep) - set(by_name)
    if missing:
        raise ValueError(f"de-correlated variant references missing metrics: {sorted(missing)}")
    result = dict(profile)
    result["metric_vector"] = [by_name[name] for name in keep]
    result["decorrelation_reason"] = declared["rationale"]
    return result
