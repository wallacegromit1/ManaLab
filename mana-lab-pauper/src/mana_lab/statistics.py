from __future__ import annotations

import hashlib
from dataclasses import dataclass
from math import comb, erf, isfinite, sqrt
from statistics import NormalDist, fmean, stdev
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
    observation = TrialObservation(
        scenario=str(value["scenario"]),
        replicate=value["replicate"],
        trial=int(value["trial"]),
        on_play=bool(value["on_play"]),
        value=float(value["value"]),
        candidate=None if value.get("candidate") is None else str(value["candidate"]),
    )
    if not isfinite(observation.value):
        raise ValueError("paired observation value must be finite")
    return observation


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
    if any(not isfinite(value) for value in differences):
        raise ValueError("paired differences must be finite")
    if not isfinite(float(confidence_z)) or confidence_z < 0:
        raise ValueError("confidence_z must be finite and non-negative")
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


@dataclass(frozen=True)
class MultiplicityDecision:
    comparison_id: str
    p_value: float
    holm_rank: int
    adjusted_alpha: float
    rejected: bool


def normal_two_sided_p_value(estimate: PairedEstimate) -> float:
    """Normal-approximation two-sided p-value for an aligned paired estimate."""
    if estimate.trials <= 0 or not all(isfinite(v) for v in (
        estimate.mean_difference, estimate.standard_error,
        estimate.confidence_low, estimate.confidence_high,
    )):
        raise ValueError("invalid paired estimate")
    if estimate.standard_error == 0:
        return 0.0 if estimate.mean_difference != 0 else 1.0
    z = abs(estimate.mean_difference / estimate.standard_error)
    return max(0.0, min(1.0, 2.0 * (1.0 - NormalDist().cdf(z))))


def holm_family(
    estimates: Mapping[str, PairedEstimate],
    *,
    family_alpha: float,
) -> tuple[MultiplicityDecision, ...]:
    """Holm step-down family-wise error control over one declared family."""
    if not estimates:
        raise ValueError("Holm family cannot be empty")
    if not isfinite(family_alpha) or not 0 < family_alpha < 1:
        raise ValueError("family_alpha must be between zero and one")
    ranked = sorted(
        ((name, normal_two_sided_p_value(estimate)) for name, estimate in estimates.items()),
        key=lambda item: (item[1], item[0]),
    )
    m = len(ranked)
    stopped = False
    output: list[MultiplicityDecision] = []
    for index, (name, p_value) in enumerate(ranked, start=1):
        alpha = family_alpha / (m - index + 1)
        rejected = (not stopped) and p_value <= alpha
        if not rejected:
            stopped = True
        output.append(MultiplicityDecision(name, p_value, index, alpha, rejected))
    return tuple(output)


def sequential_confidence_z(
    *,
    family_alpha: float,
    maximum_looks: int,
    family_size: int = 1,
) -> float:
    """Conservative always-valid planning bound via Bonferroni over looks/family.

    Holm is applied within each realized comparison family; this alpha spending
    protects optional continuation across at most maximum_looks looks.
    """
    if maximum_looks <= 0 or family_size <= 0:
        raise ValueError("look and family counts must be positive")
    if not isfinite(family_alpha) or not 0 < family_alpha < 1:
        raise ValueError("family_alpha must be between zero and one")
    per_test_two_sided = family_alpha / (maximum_looks * family_size)
    return NormalDist().inv_cdf(1.0 - per_test_two_sided / 2.0)


def adaptive_paired_difference(
    left: Iterable[TrialObservation | Mapping[str, Any]],
    right: Iterable[TrialObservation | Mapping[str, Any]],
    *,
    family_alpha: float,
    maximum_looks: int,
    family_size: int = 1,
) -> PairedEstimate:
    """Paired interval protected for repeated adaptive inspection."""
    z = sequential_confidence_z(
        family_alpha=family_alpha,
        maximum_looks=maximum_looks,
        family_size=family_size,
    )
    return paired_difference(left, right, confidence_z=z)


def stratified_paired_difference(
    left: Iterable[TrialObservation | Mapping[str, Any]],
    right: Iterable[TrialObservation | Mapping[str, Any]],
    *,
    on_play_weights: Mapping[bool, float],
    confidence_z: float = 1.96,
) -> PairedEstimate:
    """Paired estimate with an explicitly registered play/draw population.

    Each stratum contributes its declared population weight, regardless of
    its trial count. Pairing remains key-exact and each positive-weight stratum
    needs at least two independent trial pairs to estimate sampling variance.
    Normal intervals remain asymptotic and require separate model audit.
    """
    left_rows = [_coerce_observation(value) for value in left]
    right_rows = [_coerce_observation(value) for value in right]
    paired_difference(left_rows, right_rows, confidence_z=confidence_z)
    if not on_play_weights or any(type(key) is not bool for key in on_play_weights):
        raise ValueError("play/draw weights require boolean population keys")
    weights = {key: float(value) for key, value in on_play_weights.items()}
    if any(not isfinite(value) or value <= 0 for value in weights.values()):
        raise ValueError("play/draw weights must be finite and positive")
    if abs(sum(weights.values()) - 1.0) > 1e-10:
        raise ValueError("play/draw weights must sum to one")
    if not isfinite(confidence_z) or confidence_z < 0:
        raise ValueError("confidence_z must be finite and nonnegative")
    strata: dict[bool, list[float]] = {}
    for a, b in zip(left_rows, right_rows):
        if a.on_play not in weights:
            raise ValueError("trial play/draw stratum excluded by declared population")
        strata.setdefault(a.on_play, []).append(a.value - b.value)
    if set(strata) != set(weights):
        raise ValueError("declared play/draw population stratum is missing")
    if any(len(values) < 2 for values in strata.values()):
        raise ValueError("paired stratum needs at least two observations")
    mean = sum(weights[key] * fmean(values) for key, values in strata.items())
    standard_error = sqrt(sum(
        weights[key] ** 2 * stdev(values) ** 2 / len(values)
        for key, values in strata.items()
    ))
    return PairedEstimate(
        len(left_rows), mean, standard_error,
        mean - confidence_z * standard_error,
        mean + confidence_z * standard_error,
        "keyed_stratified_play_draw",
    )
