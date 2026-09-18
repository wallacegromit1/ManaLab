"""Render Run H audit findings and package evidence, not production results."""
import ast
import csv
import json
import platform
import shutil
import sys
import zipfile
from pathlib import Path
from audit_helpers import BASE, REPO, OUT, digest, save
import yaml

ROOT=Path(__file__).resolve().parent
def read(n):return json.loads((OUT/n).read_text())
def write(n,s):(ROOT/n).write_text(s.strip()+'\n')
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x).replace('|',' / ').replace('\n',' ') for x in row)+' |' for row in rows])
rep=read('reproduction.json');checks=read('adversarial_tests.json');prov=read('provenance.json');dep=read('depth_independent.json');sup=read('supplemental_checks.json')
cfg=yaml.safe_load((REPO/'RUN_G_PHASE3_FROZEN_CONFIG.yaml').read_text())
VERDICT='RUN H AUTHORIZATION — PHASE 3 NOT AUTHORIZED'
findings=[
('F-01','H-01','Executable frozen nine-stage pipeline','FAIL','Stage methods exist; stages 3–9 contain fixed fixtures, strings and assertions, not production evidence flow. run_real unconditionally raises. Forged prerequisite accepted.','Production orchestration and immutable dependency chain absent.'),
('F-02','H-02','Six executable named profiles','FAIL','Six scalar-vector arithmetic tests pass; profile aggregation metadata changes have no effect. No upstream profile-specific aggregator. Comparator ignores uncertainty.','Population, weighting and tie semantics could be invented after seeing results.'),
('F-03','H-03','All metrics and critical sequences executable','FAIL','29 registry routing labels, not 29 implementations. Incomplete/mixed traces accepted; by-turn and Cryogen/Hawk predicates fail.','Wrong numerators, denominators and cross-trial joins.'),
('F-04','H-04','Uncertainty-safe screening and frontier','FAIL','Low-level direction, missing-CI retention and explicit protections pass; no production paired-CI/multiplicity/frontier caller. Wide CI is labeled equivalent.','Adaptive and simultaneous uncertainty, reversibility and regret unimplemented.'),
('F-05','H-05','Policy identity and independent tap-out','FAIL','Tap-out genuinely differs; sequencing, mulligan and scry alternatives also differ. Registry accepts wrong policy kind; simulate_trial couples scry to sequencing.','Frozen robustness scenarios cannot be executed as declared; stage/row policy binding incomplete.'),
('F-06','H-06','No ranking-relevant mechanic gap','FAIL','28 registry rows reviewed. Tested primitives do not make all production actions available; NOT MATERIAL declarations do not contain indirect effects.','Blood/Familiar/resource/target/removal sensitivities remain unbounded.'),
('F-07','H-07','Six structural depth classes sufficient','FAIL','All six stable at 7/8/9/10, but maximum explored sequence lengths are only 2,2,3,2,4,2. Independent variants also checked.','Local stability does not stress depths 7–9 or establish pruning adequacy.'),
('F-08','—','Fresh reproducible cache-free identity','PASS','78 files match independently; content-tree hash matches; no immutable mutation; cross-extraction ordinary dry-run hashes equal.','Package identity repaired; stage-level binding remains F-01/F-05, not a package-manifest failure.'),
]
with (ROOT/'RUN_H_ACCEPTANCE_MATRIX.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['blocker','run_h_defect','run_g_claim','status','independent_reproduction_and_adversarial_result','remaining_risk','authorization_consequence','evidence'])
    for a,b,c,d,e,finding in findings:w.writerow([a,b,c,d,e,finding,'BLOCKS' if d=='FAIL' else 'CLOSED','evidence/adversarial_tests.json; evidence/reproduction.json; individual audit reports'])

# Preserve reference authority and inspected source verbatim, separate from production.
authority=ROOT/'authority';authority.mkdir(exist_ok=True)
for n in ['RUN_F_PHASE3_AUTHORIZATION_REPORT.md','RUN_F_ACCEPTANCE_MATRIX.csv','RUN_F_PHASE3_FROZEN_CONFIG.md','RUN_F_REPRODUCIBILITY.md','RUN_F_DEFECTS.md','audit_helpers.py']:
    shutil.copyfile(BASE/'run_f_audit'/n,authority/n)
for p in (BASE/'run_f_audit/evidence').glob('*'):
    if p.is_file():shutil.copyfile(p,authority/p.name)
reference=ROOT/'reference';reference.mkdir(exist_ok=True)
source_names=['phase3_pipeline','phase3_config','phase3_profiles','phase3_metrics','phase3_policies','phase3_depth','phase3_readiness','provenance','policies','simulator','statistics','metrics','effects']
locations={}
for name in source_names:
    p=REPO/'src/mana_lab'/f'{name}.py';shutil.copyfile(p,reference/p.name)
    locations[name]={n.name:n.lineno for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for n in ['RUN_G_PHASE3_FROZEN_CONFIG.yaml','RUN_G_MECHANICS_COVERAGE.csv']:
    shutil.copyfile(REPO/n,reference/n)
save('source_locations.json',locations)
save('audit_environment.json',{'python':sys.version,'platform':platform.platform(),'source_root':str(REPO),'authority_hashes':{p.name:digest(p) for p in authority.iterdir() if p.is_file()}})

write('RUN_H_PHASE3_AUTHORIZATION_REPORT.md',f'''
# {VERDICT}

Run H independently audited the exact Run G package on 2026-09-18. Seven Run F blockers remain open; F-08 package provenance is closed. Run G's readiness PASS is reproducible but is not evidence of production readiness. No conditional authorization is granted. Production was not patched.

## Integrity and reproduction

- Run G expected and observed SHA-256: `{rep['run_g_sha256']}`.
- Run E expected and observed SHA-256: `{rep['run_e_sha256']}`.
- ZIP integrity: no corrupt member. Required Run G reports/configuration present.
- Untouched parent: **179 tests pass**. Fresh G extraction A: **205 tests pass**. Fresh G extraction B: **205 tests pass**. Both gates return machine-readable PASS.
- D-01–D-11 regression modules remain passing in both full logs. These tests establish their tested properties, not all Phase 3 properties.
- Independent inclusion/exclusion and enumeration: **296,706**, unique identities; C0 once; **56** three-Bridge candidates. Enumeration was identity/count-only.
- External adversarial suite: **89 checks, 59 pass, 30 fail**. These are individual contract probes, not 30 independent blockers. Additional observations are in supplemental_checks.json.

## F-01–F-08 disposition

{table(['Blocker','Status','Independent result'],[(r[0],r[3],r[4]) for r in findings])}

## Production-path assessment

There is no complete execution path behind the authorization refusal. Stage 2 counts identities without persisting the candidate evidence required by later stages. Stages 3–9 exercise hardcoded examples or emit configuration prose. They do not simulate, aggregate all required metrics, select finalists, validate independently, run sensitivity scenarios, construct a real frontier or write the promised result tables. No real production path was run. Enabling execution requires new implementation, not simply authorization.

## Scientific assessment

Direction-aware low-level dominance and explicit low-N/uncertainty retention are improvements. They are not wired to aligned production paired differences, multiplicity control, sequentially valid adaptive intervals or an auditable frontier. Profile-specific weighted populations remain prose. This prevents scientific authorization even if orchestration were added.

## Mechanics and planner risk

Tested effect primitives and raw-only labels do not contain indirect mana and draw effects. Blood activation and Familiar's conditional draw can affect later resources without being explicit objective components. Depth stability is real for the supplied small states but does not exercise the declared depth boundary. No actual ranking impact is claimed or measured.

## Provenance

The 78-file cache-free manifest reconciles with content-tree SHA-256 `{prov['content_tree_hash']}`. Both extractions preserve immutable files and produce identical ordinary-content hashes for every dry-run JSON artifact. This repairs F-08. It does not repair missing verification of upstream artifact hashes at pipeline stages.

## Required next action

Separate **Run I remediation**, covering H-01–H-07 and their acceptance tests in RUN_H_DEFECTS.md. Re-audit after implementation. Do not launch Phase 3 or choose a mana base on this evidence.

## Limits and attestation

No screening, ranking, real shortlist/frontier, confirmatory candidate comparison or recommendation occurred. Two identical C0 traces under different labels were used solely for machinery invariance; performance summaries were not retained. The shipped suites were reproduced as requested and contain historical regression fixtures, not newly commissioned optimization. No web or external card-data updates were used. Missing production paths are explicitly untestable, not silently counted as passing. GitHub publication awaits a user-selected repository and scope.
''')

defect_details=[
('H-01','BLOCKER','F-01','phase3_pipeline.py:51,97,120,129,138,152,160,174,207; phase3_config.py:74',
 'Synthetic-only production stages; forged dependency accepted; incomplete config enforcement.',
 'run_real always raises, including regardless of control state. stage_04_medium accepts an external synthetic 03_screen.json containing only status PASS, matching config_hash and a forged artifact hash. It does not load candidate/event rows. C0/boundary protection is caller-supplied; no production caller derives all 56 protected IDs or carries them through every serious stage. The test with an empty protection set is a caller-contract probe, not a claim that an existing production optimizer eliminated C0.',
 'Implement testable production stages with typed input/output schemas, validated artifact/code/config/policy/seed lineage, candidate persistence, atomic immutable writes and restart semantics. Separate authorization identity from scientific config. Reject invalid planner bounds, seed use, adaptive counts, weights, C0, scenario policies and unknown metric references.',
 'Synthetic end-to-end pipeline executes actual simulation/aggregation/statistical paths; restart/tamper/missing-input tests; C0 and all boundary IDs survive each serious stage; authorization changes no scientific parameters.'),
('H-02','BLOCKER','F-02','phase3_profiles.py:17,52; frozen config decision_profiles',
 'Profiles consume flat scalars rather than executing declared populations, weights and uncertainty.',
 'All six hand-set scalar vectors compare correctly, but changing turns/aggregation leaves output unchanged. A single scalar name cannot distinguish all-spell, colored-spell and affinity-only castability. Comparator uses first component exceeding materiality, ignores uncertainty/no-worse constraints and later tradeoffs. Affinity de-correlated variant is identical to original; metadata presence is not substantive de-correlation.',
 'Implement profile-specific aggregation from validated raw sufficient statistics, explicit numeric weights and population IDs; use paired uncertainty and coherent conflict/tie semantics. Justify priority and truly test overlap/leave-one-out/de-correlated alternatives.',
 'Hand-calculated spell/turn/play-draw fixtures for every profile, not only preaggregated constants; conflicting components and overlapping intervals retain alternatives; altered weights/windows change the expected result.'),
('H-03','BLOCKER','F-03','phase3_metrics.py:11,56,63,91,148',
 'Aggregation coverage is a label registry; trace contracts and sequence joins are incomplete.',
 'An opening-hand-only trace is accepted; missing identity fields default; different desired-window profiles pool. Exact-turn checks violate by-T2 definitions. Cryogen/Hawk reader expects returned while producer logs card; draw counts are not constrained by source-instance/order/deadline. Cross-scenario resolutions count as double-spell. T2 full-effect interaction is ignored. Candidate/spell/paired/robustness tables are not produced.',
 'Implement every required aggregate with executable routing; reconstruct denominators by declared profile/opportunity/window; distinguish absent/not-applicable/incomplete; enforce complete trial identity and validated event joins. Correct all 11 predicates against frozen definitions.',
 'Production-schema positive/negative fixtures for every metric/predicate; no future draw satisfies earlier deadline; correct Hawk event field and draw ordering; duplicate/missing/mixed identities reject; real schema-shaped tables emitted from synthetic traces.'),
('H-04','BLOCKER','F-04','metrics.py:247,315; phase3_pipeline.py:16,97,160; statistics.py',
 'Uncertainty relation improved, but production multiplicity, adaptive precision and regret are absent.',
 'Stochastic missing intervals remain unresolved and lower-is-better legacy elimination is prevented. However reversed bounds are sorted, nonfinite inputs are not rejected, and CI [-.001,.8] at no-worse .0025/material .005 is labeled practically_equivalent. That is evidence of no worse, not two-sided equivalence. Holm appears as text, not an executed stage procedure. Caller-supplied intervals are not tied to keys, sample count, family or simultaneous coverage. profile_regret assumes scalar higher-is-better.',
 'Validate interval/data contracts and metric completeness; compute aligned paired differences and simultaneous family-corrected claims. Specify families across candidates/components/profiles/stages and sequential validity for adaptive looks. Implement uncertainty-aware frontier/regret and reversible screening ledger.',
 'Synthetic raw paired data reproduces manual intervals, duplicate/missing key rejection, adjusted and sequential boundary decisions, conflicting profiles and uncertain regret. Widening an interval cannot establish equivalence or new elimination.'),
('H-05','BLOCKER','F-05','phase3_policies.py:29,104; simulator.py:768; policies.py:196',
 'Independent reserve repaired; full scenario identity and execution binding remain incomplete.',
 'Reserve, sequencing, mulligan and scry alternatives intentionally differ in external fixtures. Registry hashes descriptive content; in-memory replacement is not caught by registry validation. Important qualification: on-disk behavior changes ARE covered by the complete file manifest at readiness. The defect is not a missing source file hash. Role-kind mismatch is accepted; simulate_trial has no independent scry argument and derives scry from sequencing, contradicting tempo_tapout and alternate_scry_information configurations. Output schema probe selects an arbitrary policy hash.',
 'Bind typed roles to exact code-tree plus policy contract, validate every scenario, independently pass all policy axes and planner bounds, and stamp complete identity on events/results/stage artifacts. Reconcile legacy policy text with the explicit new authoritative freeze.',
 'Unknown role and valid-hash/wrong-kind reject; each robustness tuple executes exactly declared policies; code-only on-disk changes fail before reuse; every result exposes all executed axes. Demonstrate a decision-sensitive information-policy state or explicitly constrain its claimed sensitivity.'),
('H-06','BLOCKER','F-06','RUN_G_MECHANICS_COVERAGE.csv; simulator.py:164; effects.py; tests/test_familiar.py',
 'Mechanics labels do not establish production reachability or ranking containment.',
 'Blood/Munitions/stun primitives are tested but not production planner actions. Blood needs own token, discard and mana, not an opponent target. Familiar test only checks no automatic draw; it does not implement promised zero-versus-available sensitivity. Excluding an explicit metric does not remove indirect draw, artifact, mana, sacrifice or future castability effects. Fountain recursion and removal/Bridge resilience have declarations rather than executable containment.',
 'Implement required production mechanics or preregister executable candidate-neutral containment scenarios justified against frozen rules. Track resource availability separately from target value; leave unresolved model uncertainty blocking robust claims.',
 'Production option/activation tests sensitive to payment, sacrifice, artifact thresholds, draw timing and legal target states. Every NOT MATERIAL claim links to an actual bound or sensitivity fixture, not self-reported relevance=false.'),
('H-07','MAJOR — authorization-blocking','F-07','phase3_depth.py:26,92; simulator.py:569,768',
 'Six named classes are present but depth evidence is not boundary-sensitive.',
 'At depths 7–10 longest explored paths are 2–4 actions. Shipped root_choices stores complete sequence keys; terminal_state_counts counts recorded prefixes, not independently established terminal nodes. Information policies change values but all shipped corpus choices remain identical. No Phase 3 production caller consumes frozen bounds.',
 'Add candidate-neutral reachable stress states where useful lines reach relevant depth/pruning limits; record true roots, nodes, branches, terminals, prunes and stopping reasons. Compare oracle/deeper searches where tractable, plus reserve/information axes and reveal boundaries.',
 'A deliberately truncated depth/pruning implementation must fail at least one corpus test. Test hidden-order invariance before reveal and legal divergence after reveal. Wire and stamp frozen depth/action limits in production.'),
]
write('RUN_H_DEFECTS.md','# Run H defects for separate Run I remediation\n\n'+VERDICT+'\n\n'+'\n\n'.join(f'## {id} — {title}\n\nSeverity: {sev}. Prior blocker: {prior}.\n\nSource: `{loc}` (verbatim copies in reference/; function-line map in evidence/source_locations.json).\n\nObserved: {obs}\n\nRequired remediation: {fix}\n\nAcceptance regression: {test}' for id,sev,prior,loc,title,obs,fix,test in defect_details)+'\n\nF-08 is closed for package-level identity. No production edits were made. Expected/observed failures in audit JSON are deliberate adversarial evidence; not failed audit execution.')

stages=[('01_validate','Partial','Deck/registry hashes, role registry, seed values and profile field presence checked; range/semantic coverage incomplete.'),('02_enumerate','Partial','Exact enumeration/count/C0 checked; no persisted candidate evidence/features passed onward.'),('03_screen','Demonstration only','Four fixed labels and hand-entered CIs; minimum 100 in fixture versus frozen 512; no real aligned event input.'),('04_medium','Stub','Writes pairing-key names, seed and count; no simulate_trial call.'),('05_select_finalists','Stub','Copies retention prose and protected_c0=True; no candidate set.'),('06_fresh_validation','Stub','Checks selection seed differs numerically; no isolated validator or adaptive loop.'),('07_robustness','Stub','Lists scenario IDs; does not run policies or containment.'),('08_frontier','Demonstration only','Four static dominance examples; no candidate frontier.'),('09_report','Schema probe only','Lists seven sample fields; no requested result tables/report.')]
write('RUN_H_PIPELINE_EXECUTABILITY_AUDIT.md',f'''# Run H pipeline executability

**FAIL — F-01/H-01.** Source: reference/phase3_pipeline.py and phase3_config.py.

{table(['Stage','Status','Actual behavior'],stages)}

All nine methods are callable and enforce the immediately preceding filename's presence. Missing prerequisites reject. But status/config_hash alone are accepted; neither artifact-content hash nor source/policy/seed/upstream chain is verified. Forged synthetic stage 03 was accepted by stage 04. _write overwrites files and unconditionally emits PASS/READINESS_DRY_RUN. There is no immutable resume protocol or complete production schema. Config is shallow-copied and _config_hash is a supplied string, not recomputed from mutated in-memory content at every stage.

No module import or call in this orchestrator reaches production simulation, paired-data computation or profile aggregation. Actual real execution is unconditionally refused. That refusal safely prevented optimization, but is not a complete gated implementation. Config validation also requires pending authorization and false execution. An external authorization token/record preserving scientific configuration is not implemented.

C0 and structural protection: the helper retains explicitly supplied protected IDs. An empty set allows even a C0 label to be eliminated by toy evidence; a toy 3-Bridge label is not automatically protected. This is a contract/integration gap, not real candidate elimination. No serious-stage candidate persistence exists to test end-to-end retention. The 56-member class count is correct, but counting is not retention.

Promised candidate, spell/turn, paired-difference, validation, robustness and frontier files cannot be generated by the staged production path. `.parquet_or_csv` also leaves serialization undecided. Stage 09 uses one arbitrarily sorted registry hash for a sample row, not the joint executed policy identity. Stop conditions are not fully executable.

Restart, tamper, code drift, stage-order, protection and validation-leakage gates must be tested through a real synthetic end-to-end workflow in Run I. No actual optimizer was enabled or run in Run H.
''')

groups={
'schema_version':('PASS','Version matches validator.'),'experiment':('DESCRIPTIVE','Identity/date/purpose only; no evidence of post-result tuning observed.'),
'phase_control':('FAIL','Safe refusal now; no complete separately authorized production route.'),
'input':('PARTIAL','Deck and exact parent independently match; validator alone does not enforce parent mutation; simulator horizon is hardcoded 1..4.'),
'candidate_space':('PARTIAL','Counts/set/C0/boundary correct for deck; mutated c0 accepted; protection is not carried through stages.'),
'pipeline':('FAIL','Order labels implemented; prerequisite code/policy/seed/content verification prose not implemented.'),
'randomness':('PARTIAL','All six seed values distinct; production replicate/purpose allocation and inaccessible validation rows not implemented.'),
'trial_plan':('FAIL','512/8192/32768 positive; adaptive batch/cap and replicate semantics not operational; zero adaptive batch accepted.'),
'scenarios':('FAIL','50/50 values specified but invalid weights/depth accepted; no config consumer for independent policy axes.'),
'policies':('PARTIAL','Ten IDs and contract hashes present; typed role and execution/row binding missing.'),
'metrics':('FAIL','Lists present; full callable aggregation/output coverage absent.'),
'decision_profiles':('FAIL','Every component reviewed: direction/raw normalization/tolerances specified, but populations/weights/uncertainty not executed; unknown metrics and negative tolerances accepted.'),
'screening':('FAIL','Holm/family/near-boundary/retention prose lacks executed production procedure.'),
'finalist_retention':('FAIL','Union/minimum/soft target rules not computed; all-3-Bridge propagation beyond screening not explicitly realized.'),
'validation':('FAIL','Fresh numeric seed only; pairing isolation, multiplicity and adaptive coverage unimplemented.'),
'dominance':('PARTIAL','Low-level oriented bound relation implemented; invalid inputs/equivalence/complete dimension set unresolved.'),
'robustness_scenarios':('FAIL','Seven labels, no executor; independent scry choices cannot be passed to simulate_trial.'),
'mechanics':('FAIL','Registry hash enforced; relevance labels accepted without behavioral containment.'),
'outputs':('FAIL','Paths/schema names only; ambiguous parquet_or_csv; no complete production writers or joint provenance.'),
'stop_conditions':('FAIL','Some checks implemented; missing-event, lineage, scenario drift and paired-key conditions not fully enforced.'),
}
ledger=[]
def walk(v,path):
    if isinstance(v,dict):
        for k,x in v.items():walk(x,path+[str(k)])
    elif isinstance(v,list):
        for i,x in enumerate(v):walk(x,path+[str(i)])
    else:
        status,note=groups[path[0]];ledger.append(['.'.join(path),json.dumps(v),status,note])
walk(cfg,[])
with (OUT/'frozen_config_field_ledger.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['field','frozen_value','assessment','reason']);w.writerows(ledger)
write('RUN_H_FROZEN_CONFIG_AUDIT.md',f'''# Run H frozen configuration audit

Every scalar field in the supplied YAML is enumerated with its exact value and group-specific disposition in evidence/frozen_config_field_ledger.csv (**{len(ledger)} leaves**). Reference copy is unchanged. No scientific parameters were changed.

{table(['Group','Status','Assessment'],[(k,*v) for k,v in groups.items()])}

Current nonzero budgets do not establish operational precision. The freeze does not say clearly whether counts are per replicate, per play/draw stratum or total, nor implement the allocation. Four replicate seeds cannot be treated as a production partition solely because they differ numerically from selection and validation seeds.

Mutation tests correctly reject zero screening, colliding seed values and an invalid registered policy hash. They accept unknown scenario sequencing, zero depth, zero adaptive batch, malformed C0, negative play weight, unknown profile metric, negative materiality and altered parent hash at validate_phase3_config. The overall supplied-archive gate independently verifies parent/source identity; these probes concern the validator's semantic guarantees, not bypass of an actually executed full gate.

Authorization cannot currently be represented as an external approved control without code changes: validator permits only pending/false and run_real always raises. The production path must first exist; simply changing a flag or YAML text is not enough.
''')

profile_rows=[]
for n,p in cfg['decision_profiles'].items():
    profile_rows.append([n,', '.join(x['metric']+' '+x['direction'] for x in p['metric_vector']),'; '.join(x['aggregation'] for x in p['metric_vector']),len(p['decorrelated_variant']['metrics'])<len(p['metric_vector'])])
write('RUN_H_PROFILE_AND_METRIC_AUDIT.md',f'''# Run H profiles and raw-event metrics

**FAIL — F-02/F-03.** Source copies: phase3_profiles.py, phase3_metrics.py, metrics.py and frozen YAML.

## Profiles

{table(['Profile','Ordered vector','Declared aggregation (not implemented here)','De-correlated subset smaller'],profile_rows)}

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
''')

write('RUN_H_STATISTICAL_AUDIT.md','''# Run H statistical audit

**FAIL — F-04/H-04, also F-01–F-03.** No real candidate inference was performed.

The low-level relation orients lower-is-better correctly, permits exact dimensions, retains overlapping/no-CI stochastic comparisons and requires a material improvement. Explicit protections and insufficient-N checks retain toy candidates. Exact/mixed/tie/conflict fixtures are in adversarial_tests.json. Empty vectors reject. These are meaningful repairs to the original Run F direction bug.

But a MetricEvidence object has no paired-key/sample-size/family/interval-method identity. The caller can call an estimate exact, omit a required dimension, or supply an unadjusted interval; the relation cannot validate the evidence provenance. Reversed confidence bounds are silently sorted. Nonfinite values are not rejected (the tested NaN comparisons return unresolved, not unsafe dominance). A wide positive interval can receive practically_equivalent without an upper equivalence bound. Distinguish equivalence, noninferiority and unresolved material superiority.

Existing Run E aligned-pair statistics/regressions still pass, and candidate-neutral randomization tests pass. The new pipeline does not call them to produce its claimed paired results. Numeric seed disjointness is verified, but there are no production selection/validation data stores or access boundary. Candidate-label invariance was independently verified on two identical C0 traces; this does not prove stage isolation. No winner's-curse containment is operational without real fresh validation of a frozen selection artifact.

Holm alpha .01 screening and .05 validation are text. The family (candidate pairs, components, profiles, stages and repeated looks), tests/interval inversion, dependent comparisons, and treatment of retained hypotheses are not executable. No adjusted interval was generated by the pipeline. Hand-supplied adjusted-looking bounds do not prove multiplicity control. Frozen adaptive 16384 batches/cap 131072 need an alpha-spending, time-uniform or otherwise valid predeclared sequential inference method; repeated nominal intervals at data-dependent stopping are insufficient.

512 / 8192 / 32768 trials are nonzero, not a demonstrated precision guarantee. Even a single worst-case Bernoulli mean at N=32768 has nominal 95% half-width about .0054 before multiplicity. Paired differences can be better or worse depending on covariance and outcome scale. This illustrative calculation is not a sufficiency claim or a candidate result. Replicate/stratum allocation and operational budget semantics remain ambiguous.

Uncertain screening comparisons are retained by the helper, but profile conflict, practical near-boundary sets, reversible elimination ledgers and uncertainty-aware candidate frontier are unimplemented. profile_regret is scalar best-minus-value, lacking direction, lexicographic profile definition or uncertainty. Raw measurements must remain distinct from profiles and sampling uncertainty from omitted-mechanic/policy uncertainty. No score is converted into match-win-rate points.
''')

mechanics=list(csv.DictReader((REPO/'RUN_G_MECHANICS_COVERAGE.csv').open()))
mechanic_rows=[]
for m in mechanics:
    name=m['mechanic'];special=any(x in name for x in ['opponent-dependent','Blood token activation','late recursion','Munitions activation','stun activation','target arrival','opponent removal'])
    note=('FAIL containment/reachability; see discussion below' if special else 'Listed primitive/production regression passes; not proof of full Phase 3 aggregation')
    testfiles=[x.strip() for x in m['test_evidence'].split(';') if x.strip().endswith('.py')]
    present=all((REPO/'tests'/x).exists() for x in testfiles) if testfiles else False
    mechanic_rows.append([name,m['status'],m['implementation'],m['test_evidence'],present,note])
with (OUT/'mechanic_row_review.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['mechanic','claimed_status','implementation','sensitive_test_reference','referenced_test_files_present','independent_assessment']);w.writerows(mechanic_rows)
depth_table=table(['Class','States at depth 9','Max actions at depth 9','Stable 7–10'],[(r['class'],r['depths']['9']['states'],r['depths']['9']['max_actions'],len({x['selected'] for x in r['depths'].values()})==1) for r in dep])
write('RUN_H_MECHANICS_AND_MODEL_RISK_AUDIT.md',f'''# Run H mechanics and model risk

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

{depth_table}

Depth 10 was also tested. Stability is reproduced, but no supplied path reaches 7 actions. Reported shipped terminal_state_counts are counts of returned recorded states/prefixes, not a separate terminal-node census; root_choices stores full sequence option keys. External helper records true first action separately.

Each class also received an independent tapped-source plus visible-Bridge-in-hand variant at 7/8/9 and two hidden library substitutions (supplemental_checks.json). Hidden-order invariance holds in these probes. Existing D-03 reveal/continuation regressions pass. No exhaustive post-reveal state-space claim is made.

Baseline versus tap-out, baseline versus tempo, mulligan, and scry are decision-sensitive in external synthetic fixtures. Information valuations differ (100 versus 35 for a one-card information node), but both information policies choose the same lines throughout the shipped corpus. A state demonstrating intentional information-policy decision divergence was not established; adequacy is unproven, not reported as PASS. Need stress tests that actually fail when depth/pruning or information boundaries are wrong, and a production caller that consumes frozen limits.
''')

write('RUN_H_PROVENANCE_REPRODUCIBILITY.md',f'''# Run H provenance and reproduction

**F-08 PASS (package identity only).**

Run G expected = observed `{rep['run_g_sha256']}`. Run E expected = observed `{rep['run_e_sha256']}`. ZIP test reports no corrupt member. Independently regenerated manifest exactly matches all **78** allowlisted source/config/test/project files, with no cache or generated entry. Content tree: `{prov['content_tree_hash']}`. Full file map: evidence/provenance.json.

Fresh A and B gates each pass 205 tests; parent passes 179. Source/config/test/report files outside outputs remain byte-identical before/after. Dry-run JSON ordinary byte hashes agree across A/B, without needing content normalization. Runtime duration/path strings in test/gate logs are not claimed byte-identical. Full logs and command arrays are retained.

The legacy Run E manifest retained inside history has stale cache entries; it is not the Run G current identity. New allowlist/source tree repairs that F-08 defect. ZIP hash identifies archive bytes; tree hash identifies selected immutable content and excludes its own output manifest, avoiding circularity. Actual executable policy source is included. A changed source byte is detected by file/tree validation, even if registry prose is unchanged. Pipeline-stage lineage still fails independently under H-01/H-05.

## Reproduce safely

Requires Python 3 and PyYAML. Retain exact input ZIPs; audit archive intentionally does not duplicate the large production inputs. Place this audit directory in a workspace as run_h_audit. Put Run G ZIP at workspace root. The helper defaults to Run E at /home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip; adjust only the audit helper PARENT path if using another host. Extract G into fresh run_h_work/a and run_h_work/b and E into run_h_work/parent (each ZIP contains mana-lab-pauper). Never extract over production or synced sources.

```sh
PYTHONDONTWRITEBYTECODE=1 python run_h_audit/audit_helpers.py reproduce
PYTHONDONTWRITEBYTECODE=1 python run_h_audit/audit_helpers.py adversarial
PYTHONDONTWRITEBYTECODE=1 python run_h_audit/supplemental_checks.py
```

The helper's reproduce mode runs the shipped one-command readiness gate in each fresh extract and the parent unittest suite. adversarial mode writes only external evidence/temp artifacts and performs no candidate performance screening. Contract FAIL records are expected audit findings; inspect JSON rather than interpreting process exit zero as production readiness. Generation helper build_reports.py uses original run_f_audit references as its authority source; packaged authority/ holds verbatim copies and their hashes for independent reading. Reference source copies are exact evidence, not an alternate repaired implementation.

Evidence limitations: independent enumeration order is checked as identity-set invariance; production performance candidate-order invariance cannot be established without a production pipeline. C0 label invariance is verified for two identical trials. Selection/validation end-to-end isolation and every-stage protected retention are blocked by missing implementation, not passed by assertion.
''')
write('RUN_H_NO_OPTIMIZATION_ATTESTATION.md','''# Run H no-optimization attestation

Run H performed integrity verification, source/config/test inspection, deterministic count/identity enumeration, shipped readiness/unit-test reproduction, synthetic profile/statistics/event fixtures, candidate-neutral planner states, and two identical C0-only machinery traces under different labels. No real candidate screening, scoring/ranking, shortlist, finalist selection, confirmatory comparison, frontier or recommendation was produced. Deterministic structural counts are not candidate performance results. Shipped regression suites were reproduced as required; historical fixture labels in their test logs are not new optimizer decisions.

Dry-run artifacts are inspected as synthetic demonstrations and emit no real performance ranking. C0 smoke evidence retains only equality/event-count machinery checks, not performance summaries. No scientific parameters were changed after any observations. No production file was patched. Source/config integrity was rechecked. All helpers and findings reside outside the Run G extracts. No external publication has occurred as part of this attestation; GitHub destination/scope remain subject to user direction.
''')
write('README.md',f'''# Mana Lab Pauper v1 — Run H audit

**{VERDICT}**

Start with RUN_H_PHASE3_AUTHORIZATION_REPORT.md and RUN_H_DEFECTS.md. RUN_H_ACCEPTANCE_MATRIX.csv maps F-01–F-08; specialist reports explain execution, config, metrics, statistics, mechanics and provenance. evidence/ holds reproducible observations/logs. reference/ contains byte-exact inspected Run G source/config excerpts; authority/ contains Run F audit authority and associated evidence. These copies are references, not production patches.

Reproduction: see RUN_H_PROVENANCE_REPRODUCIBILITY.md. No optimization or mana-base recommendation. Publication does not authorize Phase 3.
''')

# Non-circular internal audit manifest, then detached checksum of archive bytes.
manifest={str(p.relative_to(ROOT)):digest(p) for p in ROOT.rglob('*') if p.is_file() and p.name!='AUDIT_CONTENT_MANIFEST.json' and '__pycache__' not in p.parts}
(ROOT/'AUDIT_CONTENT_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
archive=BASE/'Mana_Lab_Pauper_v1_Run_H_Audit.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:z.write(p,'run_h_audit/'+str(p.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
checksum=digest(archive)
(BASE/'Mana_Lab_Pauper_v1_Run_H_Audit.zip.sha256').write_text(checksum+'  '+archive.name+'\n')
print(json.dumps({'verdict':VERDICT,'audit_files':len(manifest)+1,'archive_sha256':checksum,'archive_bytes':archive.stat().st_size},indent=2))
