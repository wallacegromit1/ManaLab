# Run H profiles and raw-event metrics

**FAIL — F-02/F-03.** Source copies: phase3_profiles.py, phase3_metrics.py, metrics.py and frozen YAML.

## Profiles

| Profile | Ordered vector | Declared aggregation (not implemented here) | De-correlated subset smaller |
| --- | --- | --- | --- |
| balanced | spell_level_on_time_castability higher, opponent_turn_interaction_availability higher, double_spell_success higher | desired-window-weighted mean across spells and turns 1-4; mean over held interaction opportunities at turns 2-4; mean of functional double-spell success at turns 3-4 | True |
| tempo_sensitive | usable_untapped_mana_by_turn higher, realized_etb_tapped_block lower, double_spell_success higher | turn-weighted mean with weights T1=.35 T2=.30 T3=.20 T4=.15; rate per land play through turn 4; mean at turns 3-4 | True |
| color_consistency | spell_level_on_time_castability higher, joint_UB_access_by_turn higher | desired-window-weighted mean for colored spells; weighted rate T2=.6 T3=.3 T4=.1 | True |
| interaction_sensitive | spell_plus_held_interaction_success higher, opponent_turn_interaction_availability higher, full_effect_metalcraft_interaction_availability higher | mean at turns 2-4 over own-main starts; mean over held interaction opportunities; mean over Dispatch/Blast held opportunities | True |
| double_spell_sensitive | double_spell_success higher, spell_plus_held_interaction_success higher | mean at turns 3-4 with T3=.4 T4=.6; mean at turns 3-4 | True |
| affinity_value_engine | spell_level_on_time_castability higher, critical_sequence_success higher | desired-window-weighted mean for Thoughtcast/Myr Enforcer/Refurbished Familiar/Utrom Monitor; mean of preregistered affinity and Cryogen/Hawk sequence predicates | False |

For each of six profiles the external fixture sets all components to .4 and improves the first by .1 in its declared direction. Expected better is returned. This establishes vector plumbing and direction, NOT weighted aggregation. Raw normalization is explicitly none; missing values with error mode reject. LOO returns component subsets and de-correlation selects declared names. Affinity's variant is unchanged, so the claim of substantive de-correlation is not established there.

Executable missing pieces: numeric population/window/scenario weighting, desired-window denominator, distinct all-spell/colored/affinity populations, paired uncertainty. evaluate_profile accepts only name->scalar and never consumes turns/scenarios/aggregation. compare_profile_vectors can return better for an early .006 advantage while ignoring a later large disadvantage, without any uncertainty input. Lexicographic priority is disclosed, but the claim that uncertain conflicts retain both is not implemented by this comparator. No opaque scalar master score was found in this new comparator; its hierarchy is nevertheless decision-sensitive.

## Registry and denominator checks

The registry covers 29 metric names with strings describing families. validate_aggregation_coverage checks names only. It is not a dispatch implementation. aggregate_trial_events outputs opening counts, selected turn snapshots, pooled primary spell counts, held interaction counts, ETB counts and predicates. It does not implement all registry outputs or profile-ready candidate/spell/paired/robustness tables.

Positive controls: duplicate event IDs reject; duplicate primary opportunities reject; repeated diagnostic windows do not enter the primary denominator; raw casts without functional resolution do not satisfy the T2 predicate. Empty opportunity counts are preserved as zero, but no defined downstream zero-denominator rate or not-applicable handling is implemented. Opening-only traces are accepted without required snapshots, and identity defaults mask missing fields. The function does not enforce one scenario/replicate/trial across rows. Distinct timing profiles are pooled. Turn rows can overwrite across identity groups.

## Eleven critical predicates

| Predicate | Independent assessment |
| --- | --- |
| T2_STRIX_UB | Exact-T2 positive and empty negative pass; by-T2 earlier-resolution semantics fail. Payment not joined. |
| T2_CRYOGEN | Exact-T2 resolution+draw passes; unrelated T4 draw wrongly satisfies it. |
| T2_THOUGHTCAST | Exact-T2 positive passes; earlier resolution incorrectly excluded. |
| T2_FAMILIAR | Exact-T2 positive passes; earlier resolution incorrectly excluded. |
| T2_MONITOR | Exact-T2 positive passes; earlier resolution incorrectly excluded. |
| T3_CRYOGEN_HAWK_LOOP | Valid production-field-shaped loop fails: returned versus card; exact-T3 Cryogen constraint and unconstrained draw/order join. Empty negative passes. |
| T3_DRAW_PLUS_INTERACTION | Simple positive/negative pass; no complete identity/held-window join validation. |
| T3_AFFINITY_PLUS_INTERACTION | Simple positive/negative pass; same missing join constraints. |
| T4_DOUBLE_SPELL | Two functional rows pass, one fails; cross-scenario pair and repeated same-instance rows falsely count without recast validation. |
| OPP_FULL_DISPATCH | T3 full positive/nonmetalcraft negative pass; valid T2 full event excluded. |
| OPP_FULL_BLAST | T3 full positive/nonmetalcraft negative pass; valid T2 full event excluded. |

Definitions are frozen in configs/experiments/Strixpatch_Affinity_v1.3.experiment.yaml:133 onward. Synthetic earlier-resolution probes test the stated by-turn predicate contract; they do not claim every T1 card resolution is reachable in this deck. Cryogen/Hawk and late-draw findings independently establish production-schema and causal join failures.

No profile, tolerance, event definition or mechanic rule was revised from candidate performance. All comparisons here are hand-made synthetic fixtures.
