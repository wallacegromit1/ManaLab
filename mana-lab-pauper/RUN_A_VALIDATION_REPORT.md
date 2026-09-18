# Mana Lab — Pauper v1 Run A validation report

## Result

**PASS — implementation is ready for Phase 2 Chat QA.**

**No final optimization was run. No candidate was ranked, selected, or recommended.**

## Implemented

- Physical-card and zone state with ordered library, hand, battlefield, graveyard, exile, stack, turn/phase, tapped state, and visible-information boundaries.
- Explicit colored/generic payment, net-zero Boulder filtering, affinity, artifact/Metalcraft state, actual draws and scry-2 library mutation.
- Cryogen enter/leave triggers, Bargain cost/trigger order, Hawk returns, Blood token, Nihil optional B draw, opponent-window resources, same-turn sequencing, London mulligans, and play/draw.
- Identical named baseline/alternate policies with deterministic tie breaks and audit logs.
- Full legal candidate enumeration plus independent DP coefficient count.

## Validation

- Unit tests passed: **70** reported cases, zero failures.
- No-lookahead suite passed with zero failures.
- Enumeration and DP both returned **296,706** candidates.
- Minimum Bridges: **3**; three-Bridge class: **56**.
- Candidate histogram, C0 facts, hypergeometric distribution, source-presence fixtures, and T2 Myr Enforcer impossibility fixture matched.
- Smoke exact-vs-simulation agreement: **PASS** under the predeclared four-standard-error/0.5-point floor rule.

## Ambiguities and deviations

- The action-policy specification defines a lexicographic objective but not one unique exhaustive search implementation. Run A implements executable shared legal-action scoring and exposes deterministic traces; Phase 2 should review realism before optimization.
- The smoke run stores one compact event-level sufficient-statistics row per trial plus full sampled policy traces. This preserves every reported smoke aggregate without writing every low-level engine event for all 480,000 trials.
- No trial-count deviation: 20,000 per configured scenario/candidate.
- Target-dependent late Boulder, Cryogen-stun, and Munitions value remains option-only, as required by the frozen model.

## Stop

Run A is complete. Full mana-base optimization remains prohibited until Phase 2 Chat QA is completed and a later execution run is explicitly authorized.
