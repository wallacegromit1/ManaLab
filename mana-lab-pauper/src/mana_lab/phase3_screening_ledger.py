"""Run I reversible, multiplicity-aware screening evidence ledger.

This module is safe to exercise on candidate-neutral fixtures. It does not
authorize performance screening or finalist selection of legal mana bases.
A caller must pre-register every relevant candidate/profile/component claim:
the module cannot infer that its supplied family covers the full experiment.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Iterable, Mapping

from .metrics import MetricEvidence, uncertainty_aware_dominance
from .phase3_config import canonical_hash
from .statistics import TrialObservation, adaptive_paired_difference


Claim = tuple[str, str, str, str]  # comparator, candidate, profile, metric


@dataclass(frozen=True)
class ScreeningEntry:
    comparator: str
    candidate: str
    profile: str
    family_id: str
    partition: str
    look: int
    trials: int
    status: str
    relation: str
    components: tuple[tuple[str, float, float, float], ...]
    evidence_hash: str


class ReversibleScreeningLedger:
    """Append-only evidence with a derived (never irreversibly pruned) view.

    A pair-level result is NOT an overall candidate elimination. Global
    elimination requires the same comparator to prove dominance across all
    registered profiles, and all boundary/C0 candidates remain protected.
    """

    def __init__(
        self,
        *,
        candidate_bridge_counts: Mapping[str, int],
        protected_candidates: Iterable[str],
        registered_claims: Iterable[Claim],
        family_id: str,
        minimum_trials: int,
        maximum_looks: int,
        family_alpha: float = 0.05,
    ) -> None:
        self.candidates = dict(candidate_bridge_counts)
        self.protected = frozenset(protected_candidates)
        self.claims = tuple(registered_claims)
        self.family_id = family_id
        self.minimum_trials = minimum_trials
        self.maximum_looks = maximum_looks
        self.family_alpha = family_alpha
        self.history: list[ScreeningEntry] = []
        if not family_id or not self.candidates or not self.claims:
            raise ValueError("registered family and candidate universe required")
        if len(self.claims) != len(set(self.claims)):
            raise ValueError("registered family contains duplicate claims")
        if minimum_trials < 2 or maximum_looks < 1 or not isfinite(family_alpha) or not 0 < family_alpha < 1:
            raise ValueError("invalid screening precision plan")
        if not self.protected.issubset(self.candidates):
            raise ValueError("protected candidates missing from registered universe")
        for comparator, candidate, profile, metric in self.claims:
            if (not comparator or not candidate or not profile or not metric
                    or comparator == candidate
                    or comparator not in self.candidates
                    or candidate not in self.candidates):
                raise ValueError("invalid registered claim")

    def _current_pair(
        self, comparator: str, candidate: str, profile: str,
    ) -> ScreeningEntry | None:
        rows = [
            row for row in self.history
            if (row.comparator, row.candidate, row.profile) == (comparator, candidate, profile)
        ]
        return rows[-1] if rows else None

    def record(
        self,
        *,
        comparator: str,
        candidate: str,
        profile: str,
        components: Mapping[str, tuple[Iterable[TrialObservation], Iterable[TrialObservation]]],
        dimensions: Mapping[str, tuple[str, float, float]],
        look: int,
        partition: str = "selection",
    ) -> ScreeningEntry:
        if partition != "selection":
            raise ValueError("selection ledger cannot consume validation or unlabelled trials")
        declared = {
            m for left, right, p, m in self.claims
            if (left, right, p) == (comparator, candidate, profile)
        }
        if not declared or set(components) != declared or set(dimensions) != declared:
            raise ValueError("components must match the pre-registered comparison family")
        earlier = self._current_pair(comparator, candidate, profile)
        if look < 1 or look > self.maximum_looks or look != (1 if earlier is None else earlier.look + 1):
            raise ValueError("adaptive look is unregistered or out of order")
        evidence: dict[str, MetricEvidence] = {}
        snapshot = {}
        trial_counts = set()
        pairing_keys = None
        for name in sorted(declared):
            left, right = (tuple(side) for side in components[name])
            if not left or len(left) != len(right):
                raise ValueError("missing or unequal paired observations")
            if any(
                not isinstance(item, TrialObservation)
                or item.candidate != expected
                for side, expected in ((left, comparator), (right, candidate))
                for item in side
            ):
                raise ValueError("paired candidate identity mismatch")
            keys = tuple(item.pairing_key for item in left)
            if pairing_keys is None:
                pairing_keys = keys
            elif keys != pairing_keys:
                raise ValueError("component populations must have aligned trial identities")
            direction, no_worse, material = dimensions[name]
            if direction not in {"higher", "lower"} or any(
                not isfinite(value) or value < 0 for value in (no_worse, material)
            ):
                raise ValueError("invalid registered dimension")
            estimate = adaptive_paired_difference(
                left, right, family_alpha=self.family_alpha,
                maximum_looks=self.maximum_looks, family_size=len(self.claims),
            )
            trial_counts.add(estimate.trials)
            evidence[name] = MetricEvidence(
                direction, False, estimate.mean_difference,
                estimate.confidence_low, estimate.confidence_high,
                no_worse, material,
            )
            snapshot[name] = {
                "left": [asdict(item) for item in left],
                "right": [asdict(item) for item in right],
                "direction": direction,
                "no_worse": no_worse,
                "materiality": material,
            }
        if len(trial_counts) != 1:
            raise ValueError("component trial counts disagree")
        trials = trial_counts.pop()
        if earlier is not None and trials <= earlier.trials:
            raise ValueError("adaptive evidence must grow at each registered look")
        relation = uncertainty_aware_dominance(evidence).status
        if candidate in self.protected or self.candidates[candidate] == 3 or candidate == "C0":
            status = "RETAIN_PROTECTED"
        elif trials < self.minimum_trials:
            status = "RETAIN_INSUFFICIENT_EVIDENCE"
        elif relation == "dominates":
            status = "PAIR_ELIMINATION_SUPPORTED"
        else:
            status = "RETAIN_UNRESOLVED_OR_NONDOMINATED"
        row = ScreeningEntry(
            comparator, candidate, profile, self.family_id, partition, look,
            trials, status, relation,
            tuple((name, ev.difference, ev.confidence_low, ev.confidence_high)
                  for name, ev in sorted(evidence.items())),
            canonical_hash({
                "family_id": self.family_id, "family_claims": self.claims,
                "profile": profile, "look": look, "partition": partition,
                "raw_paired_components": snapshot,
            }),
        )
        self.history.append(row)
        return row

    def candidate_disposition(self, candidate: str) -> str:
        """Require one comparator to establish every registered profile.

        This is only a decision relative to the explicitly supplied registered
        family, NOT proof that the experimental family is exhaustive.
        """
        if candidate not in self.candidates:
            raise ValueError("unknown candidate")
        if candidate in self.protected or self.candidates[candidate] == 3 or candidate == "C0":
            return "RETAIN_PROTECTED"
        profiles = {profile for _, other, profile, _ in self.claims if other == candidate}
        if not profiles:
            return "RETAIN_NO_REGISTERED_EVIDENCE"
        comparators = {left for left, other, _, _ in self.claims if other == candidate}
        for comparator in comparators:
            if all(
                (row := self._current_pair(comparator, candidate, profile)) is not None
                and row.status == "PAIR_ELIMINATION_SUPPORTED"
                for profile in profiles
            ):
                return "ELIMINATION_SUPPORTED_WITHIN_REGISTERED_FAMILY"
        return "RETAIN_PROFILE_CONFLICT_OR_UNRESOLVED"

    def audit_rows(self) -> tuple[dict, ...]:
        return tuple(asdict(item) for item in self.history)

    def audit_hash(self) -> str:
        return canonical_hash({
            "family_id": self.family_id, "registered_claims": self.claims,
            "protected": sorted(self.protected),
            "candidate_universe_hash": canonical_hash(self.candidates),
            "minimum_trials": self.minimum_trials,
            "maximum_looks": self.maximum_looks,
            "family_alpha": self.family_alpha,
            "entries": self.audit_rows(),
        })
