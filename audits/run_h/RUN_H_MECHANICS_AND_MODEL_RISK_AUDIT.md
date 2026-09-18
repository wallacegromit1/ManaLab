# Run H mechanics and model risk

**FAIL — F-06/F-07.** All 28 CSV rows reviewed; row-level implementation/test references and assessments are in evidence/mechanic_row_review.csv. All referenced test files exist and shipped tests pass. Test existence is not equated with production reachability or containment.

Ordinary artifact lands, tapped entry, Boulder filtering/scry, live affinity, UB payment, Metalcraft, Hawk, Bargain losses/triggers, Cryogen triggers, Spellbomb optional black draw, London mulligan and play/draw have production paths and focused passing regressions. No new failure of those primitives is asserted here. Their Phase 3 measurement joins remain separately incomplete.

## Containment challenges

- Familiar conditional draw: test_familiar.py tests only suppression of automatic draw. The CSV promises a zero-versus-available counterfactual absent from that test; no production robustness scenario executes it. Extra cards can change subsequent land drops, affinity and spell choices even when draw is not an objective term.
- Blood activation: effects.activate_blood and a payment/discard/sacrifice test exist, but generate_legal_actions does not expose it. It requires no opponent target. Raw-only/excluded does not contain future mana/draw/artifact effects.
- Blood Fountain recursion: NOT MATERIAL based on turn-4/profile exclusion is not an executable bound. Its colored/generic resource cost and returned cards require a precise horizon/opportunity argument and tested scenario.
- Munitions and Cryogen stun: tested primitives and target fixtures are useful, but no production option/sensitivity executor implements the declaration. Separate resource feasibility from target usefulness and indirect sacrifice/trigger effects.
- Opponent targets: refusing speculative probabilities is sound; missing target-value modeling alone need not invalidate raw mana availability. However a raw-only scenario label without implementation is not evidence of containment.
- Removal/Bridge indestructibility: goldfish is an explicit model boundary, not proof that resilience cannot affect candidate preference. A frozen removal sensitivity or justified restricted claim is still required by the authorization standard. Run H measured no ranking change.

The registry validator rejects an injected ranking-relevant NOT IMPLEMENTED row, a useful positive control. It trusts relevance/status declarations and therefore cannot independently establish their truth.

## Planner evidence

| Class | States at depth 9 | Max actions at depth 9 | Stable 7–10 |
| --- | --- | --- | --- |
| boulder_multiple_spells | 13 | 2 | True |
| affinity_changes_mid_sequence | 25 | 2 | True |
| hawk_return_replay_competing_lines | 26 | 3 | True |
| interaction_hold_vs_development | 10 | 2 | True |
| representative_double_spell | 127 | 4 | True |
| bargain_resource_and_trigger_composition | 29 | 2 | True |

Depth 10 was also tested. Stability is reproduced, but no supplied path reaches 7 actions. Reported shipped terminal_state_counts are counts of returned recorded states/prefixes, not a separate terminal-node census; root_choices stores full sequence option keys. External helper records true first action separately.

Each class also received an independent tapped-source plus visible-Bridge-in-hand variant at 7/8/9 and two hidden library substitutions (supplemental_checks.json). Hidden-order invariance holds in these probes. Existing D-03 reveal/continuation regressions pass. No exhaustive post-reveal state-space claim is made.

Baseline versus tap-out, baseline versus tempo, mulligan, and scry are decision-sensitive in external synthetic fixtures. Information valuations differ (100 versus 35 for a one-card information node), but both information policies choose the same lines throughout the shipped corpus. A state demonstrating intentional information-policy decision divergence was not established; adequacy is unproven, not reported as PASS. Need stress tests that actually fail when depth/pruning or information boundaries are wrong, and a production caller that consumes frozen limits.
