# Run H frozen configuration audit

Every scalar field in the supplied YAML is enumerated with its exact value and group-specific disposition in evidence/frozen_config_field_ledger.csv (**448 leaves**). Reference copy is unchanged. No scientific parameters were changed.

| Group | Status | Assessment |
| --- | --- | --- |
| schema_version | PASS | Version matches validator. |
| experiment | DESCRIPTIVE | Identity/date/purpose only; no evidence of post-result tuning observed. |
| phase_control | FAIL | Safe refusal now; no complete separately authorized production route. |
| input | PARTIAL | Deck and exact parent independently match; validator alone does not enforce parent mutation; simulator horizon is hardcoded 1..4. |
| candidate_space | PARTIAL | Counts/set/C0/boundary correct for deck; mutated c0 accepted; protection is not carried through stages. |
| pipeline | FAIL | Order labels implemented; prerequisite code/policy/seed/content verification prose not implemented. |
| randomness | PARTIAL | All six seed values distinct; production replicate/purpose allocation and inaccessible validation rows not implemented. |
| trial_plan | FAIL | 512/8192/32768 positive; adaptive batch/cap and replicate semantics not operational; zero adaptive batch accepted. |
| scenarios | FAIL | 50/50 values specified but invalid weights/depth accepted; no config consumer for independent policy axes. |
| policies | PARTIAL | Ten IDs and contract hashes present; typed role and execution/row binding missing. |
| metrics | FAIL | Lists present; full callable aggregation/output coverage absent. |
| decision_profiles | FAIL | Every component reviewed: direction/raw normalization/tolerances specified, but populations/weights/uncertainty not executed; unknown metrics and negative tolerances accepted. |
| screening | FAIL | Holm/family/near-boundary/retention prose lacks executed production procedure. |
| finalist_retention | FAIL | Union/minimum/soft target rules not computed; all-3-Bridge propagation beyond screening not explicitly realized. |
| validation | FAIL | Fresh numeric seed only; pairing isolation, multiplicity and adaptive coverage unimplemented. |
| dominance | PARTIAL | Low-level oriented bound relation implemented; invalid inputs/equivalence/complete dimension set unresolved. |
| robustness_scenarios | FAIL | Seven labels, no executor; independent scry choices cannot be passed to simulate_trial. |
| mechanics | FAIL | Registry hash enforced; relevance labels accepted without behavioral containment. |
| outputs | FAIL | Paths/schema names only; ambiguous parquet_or_csv; no complete production writers or joint provenance. |
| stop_conditions | FAIL | Some checks implemented; missing-event, lineage, scenario drift and paired-key conditions not fully enforced. |

Current nonzero budgets do not establish operational precision. The freeze does not say clearly whether counts are per replicate, per play/draw stratum or total, nor implement the allocation. Four replicate seeds cannot be treated as a production partition solely because they differ numerically from selection and validation seeds.

Mutation tests correctly reject zero screening, colliding seed values and an invalid registered policy hash. They accept unknown scenario sequencing, zero depth, zero adaptive batch, malformed C0, negative play weight, unknown profile metric, negative materiality and altered parent hash at validate_phase3_config. The overall supplied-archive gate independently verifies parent/source identity; these probes concern the validator's semantic guarantees, not bypass of an actually executed full gate.

Authorization cannot currently be represented as an external approved control without code changes: validator permits only pending/false and run_real always raises. The production path must first exist; simply changing a flag or YAML text is not enough.
