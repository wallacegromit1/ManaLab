from __future__ import annotations

import hashlib
from dataclasses import dataclass
from math import comb, sqrt
from statistics import fmean, stdev
from typing import Any, Iterable, Mapping


def hypergeometric_pmf(population: int, successes: int, draws: int, observed: int) -> float:
    if observed < 0 or observed > successes or draws - observed > population - successes:
        return 0.0
    return comb(successes, observed) * comb(population - successes, draws - observed) / comb(population, draws)


def at_least_one(population: int, successes: int, draws: int) -> float:
    return 1.0 - hypergeometric_pmf(population, successes, draws, 0)


def joint_presence_two_sets(population: int, size_a: int, size_b: int, overlap: int, draws: int) -> float:
    union = size_a + size_b - overlap
    no_a = comb(population - size_a, draws) / comb(population, draws)
    no_b = comb(population - size_b, draws) / comb(population, draws)
    neither = comb(population - union, draws) / comb(population, draws)
    return 1.0 - no_a - no_b + neither


def binomial_standard_error(probability: float, trials: int) -> float:
    return sqrt(probability * (1.0 - probability) / trials)


def tolerance_95(probability: float, trials: int, floor: float = 0.002) -> float:
    return max(floor, 1.96 * binomial_standard_error(probability, trials))


@dataclass(frozen=True)
class PairedEstimate:
    trials: int
    mean_difference: float
    standard_error: float
    confidence_low: float
    confidence_high: float
    pairing_mode: str = "keyed"

    @property
    def mean(self) -> float:
        return self.mean_difference

    @property
    def ci_low(self) -> float:
        return self.confidence_low

    @property
    def ci_high(self) -> float:
        return self.confidence_high


@dataclass(frozen=True)
class TrialObservation:
    scenario: str
    replicate: int | str
    trial: int
    on_play: bool
    value: float
    candidate: str | None = None

    @property
    def pairing_key(self) -> tuple[str, int | str, int, bool]:
        return self.scenario, self.replicate, self.trial, self.on_play


def _coerce_observation(value: TrialObservation | Mapping[str, Any]) -> TrialObservation:
    if isinstance(value, TrialObservation):
        return value
    required = {"scenario", "replicate", "trial", "on_play", "value"}
    missing = required - set(value)
    if missing:
        raise ValueError(f"paired observation missing keys: {sorted(missing)}")
    return TrialObservation(
        scenario=str(value["scenario"]),
        replicate=value["replicate"],
        trial=int(value["trial"]),
        on_play=bool(value["on_play"]),
        value=float(value["value"]),
        candidate=None if value.get("candidate") is None else str(value["candidate"]),
    )


def paired_difference(
    left: Iterable[float | TrialObservation | Mapping[str, Any]],
    right: Iterable[float | TrialObservation | Mapping[str, Any]],
    confidence_z: float = 1.96,
) -> PairedEstimate:
    left_values = list(left)
    right_values = list(right)
    if len(left_values) != len(right_values):
        raise ValueError("paired samples must have equal trial counts")
    if not left_values:
        raise ValueError("paired samples cannot be empty")
    keyed = isinstance(left_values[0], (TrialObservation, Mapping)) or isinstance(right_values[0], (TrialObservation, Mapping))
    if keyed:
        if not all(isinstance(value, (TrialObservation, Mapping)) for value in left_values + right_values):
            raise ValueError("cannot mix keyed and unkeyed paired observations")
        left_observations = [_coerce_observation(value) for value in left_values]  # type: ignore[arg-type]
        right_observations = [_coerce_observation(value) for value in right_values]  # type: ignore[arg-type]
        left_keys = [item.pairing_key for item in left_observations]
        right_keys = [item.pairing_key for item in right_observations]
        if len(left_keys) != len(set(left_keys)) or len(right_keys) != len(set(right_keys)):
            raise ValueError("paired observations contain duplicate trial identities")
        if left_keys != right_keys:
            raise ValueError("paired observation identities are not exactly aligned")
        differences = [a.value - b.value for a, b in zip(left_observations, right_observations)]
        pairing_mode = "keyed"
    else:
        # Compatibility for Run A/C deterministic fixtures only.  Phase-3
        # analysis must pass TrialObservation records and is tested separately.
        differences = [float(a) - float(b) for a, b in zip(left_values, right_values)]  # type: ignore[arg-type]
        pairing_mode = "legacy_positional_fixture"
    estimate = fmean(differences)
    standard_error = 0.0 if len(differences) == 1 else stdev(differences) / sqrt(len(differences))
    return PairedEstimate(
        len(differences), estimate, standard_error,
        estimate - confidence_z * standard_error, estimate + confidence_z * standard_error,
        pairing_mode,
    )


def replicate_identifier(seed: int, scenario: str, trial: int) -> str:
    return f"seed={int(seed)}|scenario={scenario}|trial={int(trial)}"


def validate_seed_partition(selection_seed: int, validation_seed: int, replicate_seeds: Iterable[int]) -> bool:
    values = [int(selection_seed), int(validation_seed), *(int(seed) for seed in replicate_seeds)]
    return len(values) == len(set(values))


def replicate_seed(base_seed: int, replicate_id: int, purpose: str) -> int:
    """Deterministic purpose-separated seed without Python's salted hash."""
    digest = hashlib.sha256(f"{purpose}|{replicate_id}".encode()).digest()
    return base_seed + int.from_bytes(digest[:8], "big")
