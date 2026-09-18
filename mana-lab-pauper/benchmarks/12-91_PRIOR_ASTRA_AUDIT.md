# Strixpatch Affinity v1.3 — Final adversarial mana-base audit

## Executive ruling: REJECT

Reject the prior claim that C1 is a high-confidence mathematical optimum or a demonstrated material improvement. **Retain C0 for registration.** This is a conservative decision under unresolved model risk, not a claim that C0 is globally optimal.

Confidence: **High** that the submitted evidence does not establish the claimed optimum; **Low–Medium** in the exact land-choice recommendation. A fully validated replacement optimization is required before certifying a global optimum. The independent implementation below completes a substantial adversarial test, but its simplified game policy does not justify replacing one unsupported certainty with another.

```text
3 Ancient Den
4 Seat of the Synod
4 Vault of Whispers
4 Great Furnace
1 Razortide Bridge
1 Goldmire Bridge
2 Mistvault Bridge
```

19 lands, 15 untapped / 4 tapped; direct W5/U7/B7/R4. All 41 nonlands and all four Giant’s Boulders remain fixed.

## Material findings

1. The packet lacks the original simulator, objective equation, executable sequencing policy and precise London keep/bottom rules. Its million-trial claims are reported results, not independently reproducible experiments.
2. Approximately 90.1% of the C0–C1 composite gap is attributable to the apparent explicit tap penalty recovered from the doubled-penalty sensitivity. Removing it reduces the gap from 0.874799 to 0.086988. Removing the double-spell contribution as well leaves 0.075612, exactly matching the weighted spell-table difference. The added terms might encode real costs, but the packet does not establish their incremental value beyond castability failures.
3. Independent spell-execution probes reverse the ranking under defensible alternatives. Different white-Bridge configurations or C0 win different profiles. C1 therefore fails the required robustness standard.
4. Four white sources have a real later-access cost. Boulder reduces that cost, but needs deployment mana and cannot provide two missing colors with one activation.
5. The independent model itself has limits: it scores cast opportunities, not wins; ignores scry, targets and combat; does not model actual opponent turns; and leaves some artifact payoffs unscored. Its rankings are stress-test evidence, not a certified replacement optimum.

## Forensic workbook QA

All ten workbook sheets were inspected. Packet SHA-256 hashes pass. Land counts, candidate identities, direct source arithmetic, reported comparison deltas and finalist ordering reconcile. Formula expressions in Configuration are simple count/delta formulas; simulation outputs are stored values. No comparison-delta discrepancies were found. No workbook edits were made.

The replicate seeds conflict: Sources!B18 / the handoff describe 20260918–20260920, whereas Sensitivity!F36:F47 lists four seeds 20261917–20261920. The numerical replicate gaps can be recomputed from the stored scores, but their provenance cannot be certified. The stored four-run mean gap is about 0.869 and SE about 0.0052; a normal ±1.96 SE interval from four replicates is not a robust uncertainty guarantee. A t interval with three degrees of freedom would be wider.

The workbook’s T1 W values are *selected-land policy outputs*, not the probability of having an Ancient Den available. On the play, drawing at least one Den in seven is 31.54% for C0 and 39.95% for C1/C2. This distinction explains why the workbook’s 16.12%/21.27% values are lower without proving a numerical bug.

## Deterministic checks

The enumeration is the coefficient of x^19 in (x+x²+x³+x⁴)^4(1+x+x²+x³+x⁴)^6: **296,706**. At most 16 mono lands are legal, hence at least three Bridges. There are 56 legal three-Bridge compositions. Enumerating the space is not proof that every configuration received sufficient simulation.

| Quantity, raw opening seven | C0 | C1 | C2 |
| --- | --- | --- | --- |
| No land | 5.8212% | 5.8212% | 5.8212% |
| No untapped land | 11.7501% | 9.9223% | 9.9223% |
| Expected tapped lands | 0.466667 | 0.350000 | 0.350000 |
| Only land is tapped, unconditional | 4.6570% | 3.4927% | 3.4927% |
| Both tapped, conditional on exactly two lands | 3.5088% | 1.7544% | 1.7544% |

## Independent implementation and execution

The preserved C++ source models a shuffled locked 60, visible-hand land selection, land taps, payment backtracking, Boulder deployment/filter use, affinity, artifact count, artifact bounce/sacrifice, and draw effects described by the packet. Cards drawn later are not exposed to land decisions. Land choice maximizes current hand castability plus a small color-diversity value; the alternate policy adds a 0.65 preference for a Bridge. Action priorities are explicit in source and shared across candidates.

The objective is the sum of frozen spell weights times weighted failure probability conditional on having seen that spell. A spell counts as successful if already cast or legally payable at a visited decision state. This is an *at-least-one-copy opportunity* objective: it does not demand every drawn copy or all separately available spells simultaneously. Weights sum to 28.7. It includes no explicit tapland, unavailable-mana, delay or double-spell surcharge. Delays can still cause missed weighted opportunities.

Raw-seven trials alternate play/draw. London policy A keeps 2–4 lands; policy B additionally requires an untapped land. Both stop at five cards, bottom excess lands above three first, otherwise a non-Boulder nonland, with deterministic ties. These are reproducible fixed policies, not an assertion of optimal Affinity mulligans. They omit many competent one-land keeps and spell-synergy decisions.

Completed experiments:

- 250,000 paired mana-only trials for each of six candidates under Bridge-first and untapped-first policies, plus two London policies.
- 250,000 paired spell-execution trials per original finalist for raw-seven, alternate land sequencing, no additional card draws, no Boulder fixing, and two London policies.
- Full 296,706-configuration screen at 32 trials each, followed by 281 shortlisted configurations at 4,096 trials. The shortlist forces all 56 three-Bridge compositions and reported higher-Bridge frontier candidates. Screening uses full own-turn fixing credit and is deliberately coarse.
- Fresh validation of 12 candidates at 250,000 trials each under raw-seven and London A. Screening seed sequence is 917260300+n; fresh validation uses 927260300+n. The same shuffled physical card indices are used across candidates. Selection and validation seeds differ.

The expanded search is a staged screen, not an exhaustive high-precision proof. Poor 32-trial estimates can exclude good configurations; no uniform confidence bounds certify every eliminated candidate. The 12-candidate validation addresses surviving contenders only.

Payment/setup tests pass: one UB Bridge alone cannot pay UB; one Boulder cannot turn WW into UB; two Boulders can; filtering does not ramp; deployment spends mana; one Boulder cannot filter twice without a reset; tapped Bridges immediately count for affinity; Hawk can bounce an artifact land; nonartifacts cannot be chosen as Hawk’s artifact return. Tests establish these behaviors, not every Magic rule.

Interaction credit 0–100% interpolates native and filter-enabled opportunity failures on the same path. It is a *scalar stress test*, not literal opponent-turn simulation. The no-fixing scenario reruns sequencing with filtering disabled. Native-counterfactual histories can differ from fully rerun no-fixing histories.

Scry 2 is not executed, Spellbomb’s optional draw is omitted, Dispatch is scored as castable without demanding its exile mode, Blast’s metalcraft damage is unscored, and Enforcer has zero objective weight despite being sequenced. Opponent pressure, removal, indestructibility and sideboarding are outside scope. These omissions prevent a full practical optimum claim.

## Candidate identities

| ID | Counts in land-code notation | Untapped / Bridges |
| --- | --- | --- |
| C0 | W3 U4 B4 R4 WU1 WB1 UB2 | 15 / 4 |
| C1 | W4 U4 B4 R4 UB3 | 16 / 3 |
| C2 | W4 U4 B4 R4 WU1 UB2 | 16 / 3 |
| C3 | W4 U4 B4 R4 WB1 UB2 | 16 / 3 |
| C4 | W4 U4 B4 R4 UB2 BR1 | 16 / 3 |
| C5 | W4 U4 B4 R4 UB2 UR1 | 16 / 3 |
| C6 | W4 U4 B4 R4 WB2 UB1 | 16 / 3 |
| C7 | W4 U4 B4 R4 WU1 WB1 UB1 | 16 / 3 |
| C8 | W4 U4 B4 R4 WB3 | 16 / 3 |
| C9 | W4 U4 B4 R4 WU1 WB2 | 16 / 3 |
| C10 | W4 U4 B4 R4 WU2 UB1 | 16 / 3 |
| C11 | W4 U4 B4 R4 WB1 UB1 UR1 | 16 / 3 |

## Robustness matrix

Scores below belong to the independent opportunity model and are not numerically interchangeable with Sol’s composite score. Lower is better. Regret is the score above the best candidate tested in that row. Full candidate scores and paired uncertainty are in robustness.csv.

| Test | Winner | C0 | C1 | C2 | C0 regret | C1 regret | C2 regret |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fresh raw seven | C6 | 12.85217 | 12.83608 | 12.83147 | 0.04360 | 0.02751 | 0.02291 |
| Fresh London A | C0 | 10.46730 | 10.46988 | 10.49626 | 0.00000 | 0.00258 | 0.02896 |
| No Boulder fixing | C0 | 16.14946 | 16.21950 | 16.23450 | 0.00000 | 0.07004 | 0.08504 |
| No extra draws | C3 | 12.66706 | 12.67298 | 12.67699 | 0.01734 | 0.02326 | 0.02726 |
| Bridge-preference policy | C3 | 12.76748 | 12.79075 | 12.77840 | 0.00498 | 0.02825 | 0.01590 |
| London B | C0 | 10.44072 | 10.45517 | 10.48768 | 0.00000 | 0.01445 | 0.04695 |
| Fresh opponent_credit_0 | C8 | 13.66401 | 13.65695 | 13.64736 | 0.07154 | 0.06448 | 0.05489 |
| Fresh opponent_credit_0.25 | C8 | 13.29499 | 13.28383 | 13.27650 | 0.05625 | 0.04509 | 0.03776 |
| Fresh opponent_credit_0.5 | C6 | 12.92597 | 12.91070 | 12.90565 | 0.04545 | 0.03018 | 0.02512 |
| Fresh opponent_credit_0.75 | C3 | 12.55695 | 12.53758 | 12.53479 | 0.03869 | 0.01932 | 0.01652 |
| Fresh opponent_credit_1 | C3 | 12.18793 | 12.16445 | 12.16393 | 0.03574 | 0.01226 | 0.01173 |
| Fresh Dispatch | C8 | 13.47559 | 13.45729 | 13.41148 | 0.16183 | 0.14353 | 0.09773 |
| Fresh Hawk | C8 | 13.36763 | 13.37110 | 13.31948 | 0.15741 | 0.16089 | 0.10926 |
| Fresh Blast | C11 | 14.04123 | 14.02302 | 14.01876 | 0.04688 | 0.02866 | 0.02440 |
| Fresh Strix | C3 | 13.86780 | 13.85766 | 13.87309 | 0.01677 | 0.00663 | 0.02206 |
| Fresh Black | C6 | 14.03322 | 14.01506 | 14.07209 | 0.04603 | 0.02787 | 0.08490 |
| Fresh Blue | C1 | 15.68731 | 15.65106 | 15.67039 | 0.03625 | 0.00000 | 0.01933 |
| Fresh all_play | C6 | 13.63309 | 13.62903 | 13.62692 | 0.03362 | 0.02956 | 0.02745 |
| Fresh all_draw | C6 | 12.13818 | 12.11054 | 12.10381 | 0.05256 | 0.02492 | 0.01820 |

The independent model has no additive tap, delay, unavailable-mana or double-spell term to remove. Original-workbook leave-one-out tests are reconstructed algebraically where a matching sensitivity exists; delay-only and unavailable-mana-only deletions are unavailable. “Low Boulder” is covered for interaction by the scalar grid, while the workbook’s halved-rescue scenario is workbook-verified only. Tempo-heavy and color-heavy original profiles remain workbook-only. These are explicit coverage limits, not silently completed tests.

## C0 versus C1, and the close C1 versus C2 decision

Fresh raw seven: C0 minus C1 = **+0.01609 ± 0.01461**; C2 minus C1 = **-0.00460 ± 0.00510**, paired approximate 95% Monte Carlo intervals. Positive favors C1. These intervals cover sampling noise within the implementation, not model error or multiple-comparison selection.

Fresh London A: C0 minus C1 = **-0.00258 ± 0.01631**; C2 minus C1 = **+0.02638 ± 0.00569**, paired approximate 95% Monte Carlo intervals. Positive favors C1. These intervals cover sampling noise within the implementation, not model error or multiple-comparison selection.

The original C1–C2 balanced gap is 0.071629, falling to 0.027906 without the apparent explicit tap term. Increasing Dispatch weight by 50% reverses it in the workbook. This is already evidence against describing C1 as uniquely robust. The independent profiles further show that the blue/black/white tradeoff depends on deployment and spell timing.

C1 preserves B7 and U7; C2 preserves U7 but changes B7 to B6 and W4 to W5. Their red sources and total untapped/tapped counts are identical. This is a white-versus-black tradeoff, not a tempo upgrade. C3 instead retains B7 and adds W5 at the cost of U7 to U6. No universal winner follows from source arithmetic alone.

For C0 versus C1, the extra untapped Den is a genuine early-tempo benefit. Its magnitude in game outcomes is not demonstrated. For C1 versus C2, the correct classification is **small and assumption-sensitive, practically unresolved**. Do not interpret hundredths of this score as match-win percentage points.

## White access and Boulder

Exact direct white-source *draw* probabilities, on the play without extra draws, scry or mulligans. These are not probabilities that a source was played and is untapped:

| Turn / cards seen | C0 and C2, five white sources | C1, four white sources |
| --- | --- | --- |
| T1 / 7 | 47.46% | 39.95% |
| T2 / 8 | 52.41% | 44.48% |
| T3 / 9 | 56.99% | 48.75% |
| T4 / 10 | 61.21% | 52.77% |

C2’s fifth source is tapped, so its extra T1 drawn-white probability does not increase T1 usable white. C1 and C2 both have four Dens. On the draw, use one additional card; all exact 7–11-card quantities are in checks.json.

At T3 on the play, the unconditional probability of seeing at least one of seven white spells but no direct white source is 31.67% with W5 versus 37.35% with W4. Adding the condition “no Boulder seen” leaves 15.78% versus 18.89%. Drawing Boulder is not synonymous with successfully deploying and using it.

Mana-only T3 probe, Bridge-first, after paying Boulder setup where possible (250,000 paired trials, 50/50 play/draw):

| Metric | C0 | C1 | C2 |
| --- | --- | --- | --- |
| Usable direct W | 52.61% | 42.82% | 52.16% |
| Usable W with Boulder | 75.26% | 70.15% | 74.96% |
| Usable UB with Boulder | 59.71% | 57.83% | 56.22% |
| White-spell state rescued by Boulder | 16.03% | 19.03% | 16.03% |
| White-spell state still lacking W | 19.19% | 22.79% | 19.35% |

C2 improves T3 Boulder-adjusted W over C1 by 4.8068 percentage points in that policy, while C1 improves UB by 1.6160 points. Under untapped-first, the differences shrink to 1.3876 and 0.4168 points respectively. Neither policy is optimal; together they demonstrate policy sensitivity.

The workbook’s Dispatch +0.5664 points / Hawk −2.1655 points is directionally plausible: Dispatch gives T1 weight while Hawk starts at T2; interaction receives reduced fixing credit; Hawk needs a returnable artifact. The divergence is not proof of a bug. It also cannot be certified without the original mechanics. In particular, casting Dispatch is not equivalent to having metalcraft exile available.

## Spell-demand audit

All Demand & Assumptions rows were inspected. Printed costs and mechanics are frozen packet assertions, not externally verified Oracle text. The 41-card total and copies reconcile.

- Strix: UB at T2–3 is coherent; it needs two distinct mana and one Boulder cannot repair two absent colors. Its weight 3.6 is subjective.
- Fountain: early B development is coherent, but weight 0.5 can underprice creating two artifacts and downstream affinity.
- Cryogen Relic: 1U, T2–3, and entry/exit draw are implemented as disclosed. Weight 3.2 and timing remain assumptions.
- Dispatch: T1 0.15 / T2 0.45 / T3 0.30 / T4 0.10 is decision-sensitive; tapping and exiling need distinct treatment in a full model.
- Blast: high early weight 4.8 is plausible as interaction but not data-calibrated. Red-heavy stress changes relative values.
- Boulder: cost 1 and one-mana filtering are implemented. Zero direct objective weight is reasonable only if its downstream benefits are captured. Omitting scry leaves an important benefit outside the model.
- Hawk: T2–3 favors repeatable artifact value over an unsupported naked T1 cast. Return costs must be sequenced; low white count hurts later access.
- Munitions: later 1R is coherent; activation costs and engine impact are unscored.
- Enforcer: zero color demand is correct, but zero objective weight omits a central artifact-development payoff.
- Spellbomb: colorless cast is coherent; optional B draw is omitted, understating some black demand.
- Bargain: 1B and an eligible sacrifice are required; opponent-turn scalar is not a substitute for a real reserve-mana policy.
- Familiar: affinity and B floor are implemented. Discard value and pressure are unscored.
- Thoughtcast: affinity and U floor are implemented with two draws. T2/T3 weighting is subjective and very influential.
- Monitor: affinity/U requirement follows the packet; broader card text is not independently verified.

None of these subjective weights was silently presented as an empirical metagame estimate. White-, blue-, black-, Blast- and Strix-heavy tests expose their decision sensitivity.

## Reproduction status

| Claim | Classification | Scope |
| --- | --- | --- |
| 296,706 configurations; minimum Bridges; source counts; hypergeometric quantities | INDEPENDENTLY_REPRODUCED | Exact arithmetic and enumeration |
| Stored score deltas, finalist ordering, sensitivity winners | VERIFIED_FROM_WORKBOOK | Arithmetic verified; original experiments not rerun |
| T1 W and T2/T3 UB reported values | LOGICALLY_CONSISTENT_BUT_NOT_REPRODUCIBLE | Policy unspecified; independent probes answer a separately defined question |
| Unavailable mana; T2/T3 realized delays | UNSUPPORTED_FROM_HANDOFF | Stored values exist; event definitions and implementation absent |
| Original Boulder rescue and spell castability | LOGICALLY_CONSISTENT_BUT_NOT_REPRODUCIBLE | Separate independent implementation tested; not original replication |
| Original raw-seven and London failure costs | VERIFIED_FROM_WORKBOOK | Numbers confirmed; policies and original objective unverified |
| Original C0-minus-C1 replicate gap | VERIFIED_FROM_WORKBOOK | Stored replicate arithmetic only; conflicting seed record |
| Unique/global optimum and material game improvement | UNSUPPORTED_FROM_HANDOFF | Not established by enumeration or surrogate-score significance |
| New independent scenario results | INDEPENDENTLY_REPRODUCED | Executable disclosed probes, with stated exclusions |

## Final action and residual uncertainty

**Register C0 and do not switch to C1 solely on the prior report.** The evidence does not support a robust improvement sufficient to override the existing base. This is one recommendation, not a list of equal choices.

A future global-optimum certification needs a complete rules specification, scry and draw decisions, actual interaction windows, objective calibration that includes artifact payoffs, better fixed or optimized mulligan policies, and sufficiently precise search-elimination bounds. A million additional games under the same incomplete assumptions would reduce Monte Carlo noise without resolving those issues.

No web research was used. The unrelated missing August screenshots were not needed. This audit provides source code, exact checks, search outputs, scenario results and an issue ledger. Large per-trial binary arrays are omitted from the delivery ZIP; the sources, seeds and rerun instructions regenerate them.
