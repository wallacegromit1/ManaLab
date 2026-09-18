from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProfileComponentValue:
    metric: str
    value: float
    direction: str
    no_worse_tolerance: float
    materiality_tolerance: float


def evaluate_profile(
    profile: Mapping[str, Any],
    metric_values: Mapping[str, float | None],
) -> tuple[ProfileComponentValue, ...]:
    """Build a transparent lexicographic vector from already-aggregated metrics.

    Phase 3 profiles deliberately do not normalize or combine unlike metrics
    into a master score.  Aggregation across events/turns/scenarios occurs
    upstream exactly as named in the frozen component contract.
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
            raise ValueError("Run G profiles permit only explicit raw-scale vectors")
        values.append(ProfileComponentValue(
            metric=name,
            value=float(value),
            direction=str(component["direction"]),
            no_worse_tolerance=float(component["no_worse_tolerance"]),
            materiality_tolerance=float(component["materiality_tolerance"]),
        ))
    if not values:
        raise ValueError("profile produced an empty vector")
    return tuple(values)


def compare_profile_vectors(
    left: tuple[ProfileComponentValue, ...],
    right: tuple[ProfileComponentValue, ...],
) -> str:
    """Return better/worse/practically_tied under the frozen lexicographic rule."""
    if [item.metric for item in left] != [item.metric for item in right]:
        raise ValueError("profile vectors are not aligned")
    for a, b in zip(left, right):
        signed = a.value - b.value if a.direction == "higher" else b.value - a.value
        if signed > a.materiality_tolerance:
            return "better"
        if signed < -a.materiality_tolerance:
            return "worse"
    return "practically_tied"


def leave_one_component_out(profile: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    variants: dict[str, dict[str, Any]] = {}
    for component in profile["metric_vector"]:
        omitted = component["metric"]
        variant = dict(profile)
        variant["metric_vector"] = [dict(item) for item in profile["metric_vector"] if item["metric"] != omitted]
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

