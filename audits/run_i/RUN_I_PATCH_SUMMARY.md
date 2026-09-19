# Run I patch summary

| Defect | Files/functions | Remediation | Residual |
|---|---|---|---|
| H-01 | `phase3_pipeline.Phase3Pipeline`, `phase3_config.validate_phase3_config`, `phase3_stage_schemas.validate_stage_envelope` | Persists full legal identity set and raw C0-neutral events, checks lineage/payload hashes, atomic writes/restart, exact protected set; declared RNG mapping | Stages 04/05/06/08/09 lack complete production candidate algorithms |
| H-02 | `phase3_profiles.aggregate_profile_events`, `compare_profile_trials`, `component_population_id` | Six raw event-based ordered profile vectors, explicit populations and weighted turns | Not called by real candidate-selection/validation stages; further sensitivity tests needed |
| H-03 | `phase3_metrics.*`, `state.GameState.draw`, `simulator.cast_card` | Source IDs, by-turn predicates, duplicate/mixed ID rejection, trace-derived tables | Full executable numeric routes and complete joins/denominators not finished |
| H-04 | `statistics.paired_difference`, `holm_family`, `adaptive_paired_difference`; `metrics.uncertainty_aware_*` | Finite CI validation, keyed paired intervals, Holm, sequential Bonferroni, oriented frontier/regret | Production multiplicity families and reversible screen ledger missing |
| H-05 | `phase3_policies.validate_policy_freeze`, `simulator.simulate_trial` | Typed roles, scry decoupled from sequencing, all axes traced | Production-stage binding and information decision sensitivity incomplete |
| H-06 | `simulator.generate_legal_actions`, `apply_planner_action`; `phase3_model_risk.*` | Blood planner action and resource/target, draw, sacrifice/removal counterfactuals | Fountain recursion and indirect decision sensitivity unresolved |
| H-07 | `simulator.enumerate_action_sequences`, `phase3_depth.planner_depth_audit` | Instrumented search, new seven-action stress, depth-3 failure vs depth-10 | Target-horizon and alternative-policy boundary proof incomplete |

Historical Run E/Run G tests are reproduced from untouched archives; the
Run I tests cover selected defects but are not exhaustive authorization
tests. No optimization, ranking, shortlist or recommendation was run.
