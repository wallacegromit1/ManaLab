# Run F Phase 3 Frozen-Configuration Review

This is a pre-execution snapshot, not an authorization and not a replacement Phase 3 config. Values shown as gaps must be frozen before any real candidate performance run; they must not be chosen after observing candidate results.

| Parameter | Value found in Run E | Source | Frozen before results? | Audit status |
|---|---|---|---|---|
| Deck | Strixpatch Affinity v1.3; 60 cards | deck YAML | Yes | PASS |
| Frozen nonlands | 41; no nonland variable | deck YAML/tests | Yes | PASS |
| Land count | Exactly 19 | deck YAML | Yes | PASS |
| C0 | 3 Den / 4 Seat / 4 Vault / 4 Furnace / 1 Razortide / 1 Goldmire / 2 Mistvault | deck YAML | Yes | PASS |
| Candidate pool | 4 mono artifact lands at 1–4; 6 Bridges at 0–4 | deck YAML | Yes | PASS |
| Candidate-space size | 296,706 | independent Run F checks | Yes | PASS |
| C0 protection | `protect_current_base: true` | experiment YAML | Declarative | PARTIAL: no screening pipeline enforces it |
| Boundary-class protection | All 56 three-Bridge candidates named in prose | experiment YAML | Declarative | PARTIAL: no executable rule |
| Phase mode | `RUN_C_REMEDIATION_VALIDATE_ONLY` | experiment YAML | Yes | FAIL for Phase 3 |
| Optimization permission | false | experiment YAML | Yes | FAIL for Phase 3 |
| Play/draw production handling | Scenarios list all-play/all-draw/mixed; smoke override uses mixed only | experiment YAML | Ambiguous | BLOCKING GAP |
| Play/draw weighting | Deck says 0.5/0.5; no Phase 3 aggregation rule | deck/experiment YAML | No | BLOCKING GAP |
| Mulligan policies | baseline functional London; alternate land-count London | deck/experiment/code | Yes | PASS |
| Sequencing policies | baseline hand-demand; alternate tempo | deck/experiment/code | Names frozen | PARTIAL: authoritative precedence conflicts with code |
| Opponent reserve policies | baseline reserve-one-reply; alternate tap-out | deck YAML | Name only | FAIL: tap-out behavior not executable |
| Scry policies | baseline and land-stability alternate | deck/code | Yes | PASS |
| Information policies | baseline 100/190/80; conservative 35/60/20 | code/Run E spec | Yes | PARTIAL: not in Phase 3 config |
| Planner depth | default 8 | simulator code | Hard-coded | PARTIAL: insufficient coverage |
| Planner sensitivity | depths 7/8/9 on 16 states | Run E output | Yes | PARTIAL: corpus inadequate |
| Replan/action bound | default 12 | simulator code | Hard-coded | PARTIAL: absent from config |
| Primary raw metrics | 18 named metrics | experiment YAML/registry | Yes | PARTIAL: no production aggregation |
| Secondary raw metrics | 11 named metrics | experiment YAML/registry | Yes | PARTIAL: three are validation-only |
| Critical sequences | 11 prose predicates | experiment YAML | Names only | FAIL: no evaluators |
| Balanced profile | Name only | deck YAML | No | BLOCKING GAP |
| Tempo-sensitive profile | Name only | deck YAML | No | BLOCKING GAP |
| Color-consistency profile | Name only | deck YAML | No | BLOCKING GAP |
| Interaction-sensitive profile | Name only | deck YAML | No | BLOCKING GAP |
| Double-spell-sensitive profile | Name only | deck YAML | No | BLOCKING GAP |
| Affinity/value-engine profile | Name only | deck YAML | No | BLOCKING GAP |
| Leave-one-component-out variants | Dictionary helper only | metrics.py | No executable plan | BLOCKING GAP |
| De-correlated variants | Keeps first component per family | metrics.py | No substantive definition | BLOCKING GAP |
| Screening enabled | false | experiment YAML | Yes | FAIL for Phase 3 |
| Screening trials | 0 | experiment YAML | Yes | BLOCKING GAP |
| Screening elimination rule | `NONE_IN_RUN_A` | experiment YAML | Yes | BLOCKING GAP |
| Near-boundary survival rule | Unspecified | — | No | BLOCKING GAP |
| False-elimination budget | Unspecified | — | No | BLOCKING GAP |
| Medium trials | 0 | experiment YAML | Yes | BLOCKING GAP |
| Medium-stage promotion rule | Unspecified | — | No | BLOCKING GAP |
| Finalist target/rule | 0 / unspecified | experiment YAML | No | BLOCKING GAP |
| Selection seed | 2026091701 | experiment YAML | Yes | PASS as label only |
| Validation seed | 2026091702 | experiment YAML | Yes | PASS as label only |
| Replicate seeds | 2026091703–2026091706 | experiment YAML | Yes | PASS as labels only |
| Seed stage enforcement | No Phase 3 orchestrator | — | No | BLOCKING GAP |
| Validation trials | 0 | experiment YAML | Yes | BLOCKING GAP |
| Adaptive finalist rule | Unspecified | — | No | BLOCKING GAP |
| Confirmatory seed/stage | Unspecified beyond generic replicate list | — | No | BLOCKING GAP |
| Multiple-comparison containment | Fresh-validation prose only | docs | No executable procedure | BLOCKING GAP |
| Paired-difference estimator | Strict keyed estimator | statistics.py | Yes | PASS primitive |
| Confidence level | 0.95 | experiment YAML | Yes | PASS primitive |
| Practical-significance rule | Unspecified | — | No | BLOCKING GAP |
| Pareto dimensions | Unspecified | — | No | BLOCKING GAP |
| Pareto direction/tolerance | Higher-only helper; no tolerance | metrics.py | No | FAIL |
| Pareto uncertainty rule | Unspecified | — | No | BLOCKING GAP |
| Regret reporting | Higher-only subtraction helper | metrics.py | No | PARTIAL/FAIL |
| Robustness variants | Names/prose only | experiment/deck YAML | No complete matrix | BLOCKING GAP |
| Unsupported-mechanic containment | No frozen plan | Run E limitations | No | BLOCKING GAP |
| Candidate table output | Boolean true | experiment YAML | Name only | PARTIAL |
| Pareto output | false | experiment YAML | Yes | FAIL for Phase 3 |
| Robustness matrix output | false | experiment YAML | Yes | FAIL for Phase 3 |
| Raw event output | gzip JSONL in smoke | simulator.py | Yes for smoke | PARTIAL |
| Phase 3 report/output schema | Unspecified | — | No | BLOCKING GAP |
| One-command reproduction | Validation commands only | README/reproduction file | No Phase 3 command | BLOCKING GAP |

Conclusion: the frozen input model is largely recoverable; the Phase 3 experiment is not frozen.
