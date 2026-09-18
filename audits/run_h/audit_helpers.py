"""Run H external audit. No production edits or real-candidate comparisons."""
import argparse
import ast
import copy
import csv
import hashlib
import inspect
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from math import comb
from pathlib import Path
from unittest.mock import patch


BASE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / 'evidence'
REPO = BASE / 'run_h_work/a/mana-lab-pauper'
PARENT = Path('/home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip')
sys.path.insert(0, str(REPO / 'src'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, obj):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + '\n')


def reproduce():
    """Run parent suite and two fresh-package gates; capture all logs externally."""
    def run(label):
        root = BASE / 'run_h_work' / label / 'mana-lab-pauper'
        env = dict(os.environ, PYTHONPATH=str(root / 'src'), PYTHONDONTWRITEBYTECODE='1')
        source_before = {str(p.relative_to(root)): digest(p) for p in root.rglob('*')
                         if p.is_file() and ('outputs' not in p.relative_to(root).parts)}
        if label == 'parent':
            command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']
        else:
            command = [sys.executable, '-m', 'mana_lab.phase3_readiness', '--root', '.',
                       '--config', 'RUN_G_PHASE3_FROZEN_CONFIG.yaml', '--parent-zip', str(PARENT)]
        proc = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
        (OUT / f'{label}_stdout.txt').write_text(proc.stdout)
        (OUT / f'{label}_stderr.txt').write_text(proc.stderr)
        import re
        result = {'exit_code': proc.returncode, 'command': command}
        if label == 'parent':
            result['test_counts'] = re.findall(r'Ran (\d+) tests', proc.stderr)
        else:
            gate = json.loads(proc.stdout)
            save(f'{label}_readiness.json', gate)
            result['gate_status'] = gate['status']
            result['tests'] = gate['checks']['full_tests']
            log = root / 'outputs/run_g/readiness/unit_test_report.txt'
            (OUT / f'{label}_unit_tests.txt').write_bytes(log.read_bytes())
            result['dry_files'] = {p.name: digest(p) for p in
                                  (root / 'outputs/run_g/readiness/dry_run_a').glob('*.json')}
        result['immutable_files_unchanged'] = all(digest(root / p) == h for p, h in source_before.items())
        return label, result
    OUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = dict(pool.map(run, ['a', 'b', 'parent']))
    results['cross_extraction_dry_content_equal'] = results['a']['dry_files'] == results['b']['dry_files']
    results['run_g_sha256'] = digest(BASE / 'Mana_Lab_Pauper_v1_Run_G.zip')
    results['run_e_sha256'] = digest(PARENT)
    with zipfile.ZipFile(BASE / 'Mana_Lab_Pauper_v1_Run_G.zip') as z:
        results['zip_corruption'] = z.testzip()
        results['required_deliverables'] = sorted(n for n in z.namelist() if '/RUN_G_' in n)
    save('reproduction.json', results)
    print(json.dumps({k: v for k,v in results.items() if k not in ['a','b']}, indent=2))


def adversarial():
    from mana_lab.phase3_config import load_phase3_config, validate_phase3_config
    from mana_lab.phase3_pipeline import Phase3Pipeline, safe_screen_decision
    from mana_lab.phase3_profiles import evaluate_profile, compare_profile_vectors, leave_one_component_out, decorrelated_profile
    from mana_lab.phase3_policies import validate_policy_freeze, policy_hashes
    from mana_lab.phase3_metrics import aggregate_trial_events, evaluate_critical_sequences, validate_event_stream, AGGREGATION_METHODS
    from mana_lab.metrics import MetricEvidence as E, uncertainty_aware_dominance as dom, pareto_dominates
    from mana_lab.provenance import source_manifest, validate_manifest, content_tree_hash
    from mana_lab.cards import load_deck
    from mana_lab.candidates import enumerate_candidates
    from mana_lab.phase3_depth import structural_state_corpus
    from mana_lab.simulator import enumerate_action_sequences, _selected_result, simulate_trial, generate_legal_actions
    from mana_lab.policies import BASELINE_ACTION_POLICY, BASELINE_SCRY_POLICY, BASELINE_INFORMATION_POLICY, CONSERVATIVE_INFORMATION_POLICY
    from mana_lab.phase3_readiness import validate_mechanic_registry
    config = load_phase3_config(REPO / 'RUN_G_PHASE3_FROZEN_CONFIG.yaml')
    deck = load_deck(REPO / config['input']['deck_spec']['path'])
    records = []
    def check(name, expected, observed, finding):
        records.append({'test':name,'expected':expected,'observed':observed,
                        'status':'PASS' if observed == expected else 'FAIL','finding':finding})
    def rejected(fn):
        try:
            fn()
            return False
        except (ValueError, RuntimeError, KeyError, TypeError):
            return True
    # Mutations exist in memory only; no production input is edited.
    mutations = [
        ('zero_screening', lambda c:c['trial_plan'].__setitem__('screening_trials_per_candidate',0), True),
        ('seed_collision', lambda c:c['randomness'].__setitem__('validation_seed',c['randomness']['selection_seed']),True),
        ('bad_policy_hash',lambda c:c['policies']['identities']['reserve_alternate'].__setitem__('content_hash','0'*64),True),
        ('unknown_scenario_policy',lambda c:c['robustness_scenarios'][0].__setitem__('sequencing','unknown'),True),
        ('zero_depth',lambda c:c['scenarios'].__setitem__('planner_search_depth',0),True),
        ('zero_adaptive_batch',lambda c:c['trial_plan'].__setitem__('validation_adaptive_batch',0),True),
        ('wrong_c0',lambda c:c['candidate_space']['c0'].__setitem__('Ancient Den',99),True),
        ('invalid_mix',lambda c:c['scenarios']['primary_play_draw'][0].__setitem__('weight',-4),True),
        ('unknown_metric',lambda c:c['decision_profiles']['balanced']['metric_vector'][0].__setitem__('metric','invented'),True),
        ('negative_tolerance',lambda c:c['decision_profiles']['balanced']['metric_vector'][0].__setitem__('materiality_tolerance',-1),True),
        ('wrong_parent_hash',lambda c:c['input']['parent_archive'].__setitem__('sha256','0'*64),True),
    ]
    for name, mutate, expected in mutations:
        c = copy.deepcopy(config); mutate(c)
        check('config_'+name,expected,rejected(lambda:validate_phase3_config(c,REPO)),'H-01/H-02/H-05')
    # Fixed-vector arithmetic for all six profiles; aggregation is tested separately.
    for name,p in config['decision_profiles'].items():
        a={x['metric']:0.4 for x in p['metric_vector']}; b=dict(a)
        first=p['metric_vector'][0]; a[first['metric']] += .1 if first['direction']=='higher' else -.1
        check('profile_arithmetic_'+name,'better',compare_profile_vectors(evaluate_profile(p,a),evaluate_profile(p,b)),'H-02')
        check('profile_overlap_'+name,True,bool(p['overlap_rationale'] and leave_one_component_out(p) and decorrelated_profile(p)['metric_vector']),'H-02')
    p=config['decision_profiles']['balanced']; vals={x['metric']: .5 for x in p['metric_vector']}
    changed=copy.deepcopy(p); changed['metric_vector'][0]['turns']=[99]; changed['metric_vector'][0]['aggregation']='different population'
    check('profile_aggregation_affects_evaluation',True,evaluate_profile(p,vals)!=evaluate_profile(changed,vals),'H-02')
    def event(i,typ,t=0,**kwargs):
        return dict(event_id=i,event=typ,turn=t,scenario='toy',replicate=1,trial_id=0,on_play=True,**kwargs)
    opening=event(1,'opening_hand',opening_land_count=2,mulligans=0,keep_size=7)
    check('incomplete_trace_rejected',True,rejected(lambda:aggregate_trial_events([opening])),'H-03')
    duplicate=[opening,dict(opening)]
    check('duplicate_event_rejected',True,rejected(lambda:validate_event_stream(duplicate)),'H-03')
    check('missing_identity_rejected',True,rejected(lambda:validate_event_stream([{'event_id':1,'event':'opening_hand'}])),'H-03')
    primary=event(2,'spell_window',2,event_role='primary_pre_spend_opportunity',opportunity_id='one',castable=True,profile='baseline_practical',card='Baleful Strix',uid='s')
    dup=dict(primary,event_id=3)
    check('duplicate_opportunity_rejected',True,rejected(lambda:validate_event_stream([opening,primary,dup])),'H-03')
    alternate=dict(primary,event_id=3,opportunity_id='two',profile='value_development')
    check('profile_population_kept_separate',1,aggregate_trial_events([opening,primary,alternate])['spell_opportunities'],'H-03')
    # Every critical sequence positive/negative; specific malformed joins below.
    cardmap={'T2_STRIX_UB':'Baleful Strix','T2_CRYOGEN':'Cryogen Relic','T2_THOUGHTCAST':'Thoughtcast','T2_FAMILIAR':'Refurbished Familiar','T2_MONITOR':'Utrom Monitor'}
    for seq,card in cardmap.items():
        ev=[event(1,'spell_resolution',2,card=card,functional=True,uid='x')]
        if seq=='T2_CRYOGEN':ev.append(event(2,'draw',2,reason='Cryogen Relic enter draw'))
        check(seq+'_positive',True,evaluate_critical_sequences(ev)[seq],'H-03')
        check(seq+'_negative',False,evaluate_critical_sequences([])[seq],'H-03')
        if seq!='T2_CRYOGEN':
            check(seq+'_by_turn_two',True,evaluate_critical_sequences([dict(ev[0],turn=1)])[seq],'H-03')
    loop=[event(1,'spell_resolution',2,card='Cryogen Relic',uid='c',functional=True),event(2,'draw',2,reason='Cryogen Relic enter draw'),event(3,'glint_hawk_return',3,card='Cryogen Relic',uid='c'),event(4,'draw',3,reason='Cryogen Relic leave draw'),event(5,'spell_resolution',3,card='Glint Hawk',uid='h',functional=True)]
    check('T3_CRYOGEN_HAWK_LOOP_positive',True,evaluate_critical_sequences(loop)['T3_CRYOGEN_HAWK_LOOP'],'H-03')
    for seq,card in [('T3_DRAW_PLUS_INTERACTION','Baleful Strix'),('T3_AFFINITY_PLUS_INTERACTION','Thoughtcast')]:
        ev=[event(1,'spell_resolution',3,card=card,functional=True),event(2,'opponent_window',3,card='Dispatch',payable=True)]
        check(seq+'_positive',True,evaluate_critical_sequences(ev)[seq],'H-03')
        check(seq+'_negative',False,evaluate_critical_sequences([])[seq],'H-03')
    double=[event(1,'spell_resolution',4,card='Glint Hawk',uid='h',functional=True),event(2,'spell_resolution',4,card='Nihil Spellbomb',uid='n',functional=True)]
    check('T4_DOUBLE_SPELL_positive',True,evaluate_critical_sequences(double)['T4_DOUBLE_SPELL'],'H-03')
    check('T4_DOUBLE_SPELL_negative',False,evaluate_critical_sequences(double[:1])['T4_DOUBLE_SPELL'],'H-03')
    mixed=[double[0],dict(double[1],scenario='different')]
    check('cross_scenario_double_spell_rejected',False,evaluate_critical_sequences(mixed)['T4_DOUBLE_SPELL'],'H-03')
    for seq,card in [('OPP_FULL_DISPATCH','Dispatch'),('OPP_FULL_BLAST','Galvanic Blast')]:
        ev=[event(1,'opponent_window',2,card=card,payable=True,metalcraft=True)]
        check(seq+'_turn_two',True,evaluate_critical_sequences(ev)[seq],'H-03')
        check(seq+'_turn_three',True,evaluate_critical_sequences([dict(ev[0],turn=3)])[seq],'H-03')
        check(seq+'_negative',False,evaluate_critical_sequences([dict(ev[0],metalcraft=False)])[seq],'H-03')
    late_draw=[event(1,'spell_resolution',2,card='Cryogen Relic',functional=True),event(2,'draw',4,reason='Cryogen Relic enter draw')]
    check('cryogen_late_draw_not_linked_to_t2',False,evaluate_critical_sequences(late_draw)['T2_CRYOGEN'],'H-03')
    # Dispatch names in the coverage table are not callable implementations.
    import mana_lab.phase3_metrics as pm
    missing_routes=sorted(set(AGGREGATION_METHODS.values())-set(vars(pm)))
    check('aggregation_routes_are_callable',[],missing_routes,'H-03')
    fixtures={
        'exact_dominates':({'m':E('higher',True,1)},'dominates'),
        'inferior':({'m':E('higher',True,-1)},'dominated_or_incomparable'),
        'mixed_directions':({'a':E('higher',True,1),'b':E('lower',True,-1)},'dominates'),
        'tie':({'m':E('higher',True,0)},'practically_equivalent'),
        'within_tolerance':({'m':E('higher',True,-.001,no_worse_tolerance=.0025,materiality_tolerance=.005)},'practically_equivalent'),
        'uncertain':({'m':E('higher',False,.01,-.1,.1)},'unresolved'),
        'missing_ci':({'m':E('higher',False,.1)},'unresolved'),
        'conflict':({'a':E('higher',True,1),'b':E('higher',True,-1)},'dominated_or_incomparable'),
        'mixed_exact_stochastic':({'a':E('higher',True,1),'b':E('higher',False,.2,.1,.3)},'dominates'),
    }
    for name,(e,expected) in fixtures.items():check('dominance_'+name,expected,dom(e).status,'H-04')
    check('legacy_lower_metric_safety',False,pareto_dominates({'unused_mana':5},{'unused_mana':1},['unused_mana']),'H-04')
    check('reversed_ci_rejected',True,rejected(lambda:dom({'m':E('higher',False,.2,.4,.1)})),'H-04')
    check('nan_rejected',True,rejected(lambda:dom({'m':E('higher',True,float('nan'))})),'H-04')
    d=dom({'m':E('higher',False,.1,.08,.12)})
    for name,trials,protected in [('C0',512,{'C0'}),('toy',1,{'C0'})]:
        check('screen_'+name+'_retained',True,safe_screen_decision(name,d,protected_candidates=protected,trials=trials,minimum_trials=512).startswith('RETAIN'),'H-04')
    check('unresolved_retained',True,safe_screen_decision('toy',dom({'m':E('higher',False,1)}),protected_candidates={'C0'},trials=512,minimum_trials=512).startswith('RETAIN'),'H-04')
    check('C0_protection_is_intrinsic',True,safe_screen_decision('C0',d,protected_candidates=set(),trials=512,minimum_trials=512).startswith('RETAIN'),'H-01')
    check('toy_boundary_class_protected',True,safe_screen_decision('TOY_3_BRIDGE',d,protected_candidates={'C0'},trials=512,minimum_trials=512).startswith('RETAIN'),'H-01')
    # Tamper only with external synthetic stage artifacts.
    with tempfile.TemporaryDirectory(dir=OUT) as tmp:
        pipeline=Phase3Pipeline(REPO,config,tmp)
        check('real_path_exists',False,rejected(pipeline.run_real),'H-01')
        check('missing_prerequisite_rejected',True,rejected(pipeline.stage_04_medium),'H-01')
        (Path(tmp)/'03_screen.json').write_text(json.dumps({'status':'PASS','config_hash':config['_config_hash'],'artifact_content_hash':'FORGED'}))
        check('forged_prerequisite_rejected',True,rejected(pipeline.stage_04_medium),'H-01')
    before=policy_hashes()
    import mana_lab.policies as policies
    with patch.object(policies,'choose_action',lambda options,*args,**kwargs:list(options)[-1]):
        check('policy_freeze_detects_in_memory_behavior_replacement',True,rejected(lambda:validate_policy_freeze(config['policies'])),'H-05')
    check('hashes_cover_all_ten_roles',10,len(before),'H-05')
    # Depth sensitivity, including deeper tractable endpoint and information policy.
    depth_rows=[]
    for label,state in structural_state_corpus(deck):
        row={'class':label,'depths':{}}
        for depth in (7,8,9,10):
            results=enumerate_action_sequences(state,deck,scry_policy_name=BASELINE_SCRY_POLICY,max_depth=depth)
            selected=_selected_result(results,BASELINE_ACTION_POLICY)
            row['depths'][str(depth)]={'states':len(results),'max_actions':max(len(r.planner_actions) for r in results),'selected':selected.option.key,'root':str(selected.planner_actions[0].key) if selected.planner_actions else 'PASS'}
        choices={}
        for info in (BASELINE_INFORMATION_POLICY,CONSERVATIVE_INFORMATION_POLICY):
            results=enumerate_action_sequences(state,deck,scry_policy_name=BASELINE_SCRY_POLICY,max_depth=8,information_policy_name=info)
            choices[info]=_selected_result(results,BASELINE_ACTION_POLICY).option.key
        row['information_choices']=choices
        depth_rows.append(row)
    save('depth_independent.json',depth_rows)
    check('depth_corpus_reaches_depth_boundary',True,any(r['depths']['9']['max_actions']>=7 for r in depth_rows),'H-07')
    # Independent count by polynomial inclusion/exclusion and canonical set.
    count=sum((-1)**(a+b)*comb(4,a)*comb(6,b)*comb(15-4*a-5*b+9,9)
              for a in range(5) for b in range(7) if 15-4*a-5*b>=0)
    candidates=list(enumerate_candidates(deck)); keys=sorted(c.key for c in candidates)
    c0='|'.join(f'{n}:{dict(deck.current_mana_base).get(n,0)}' for n in sorted(l.name for l in deck.lands))
    candidate_evidence={'inclusion_exclusion':count,'production_count':len(keys),'unique':len(set(keys)),'C0':keys.count(c0),'three_bridge':sum(c.bridge_count==3 for c in candidates),'canonical_set_sha256':hashlib.sha256('\n'.join(keys).encode()).hexdigest(),'reverse_order_set_equal':sorted(c.key for c in reversed(candidates))==keys}
    save('candidate_identity.json',candidate_evidence)
    check('independent_count',296706,count,'NONE')
    check('C0_once',1,candidate_evidence['C0'],'NONE')
    check('boundary_count',56,candidate_evidence['three_bridge'],'NONE')
    manifest=source_manifest(REPO)
    independent={str(p.relative_to(REPO)):digest(p) for directory in ['src','tests','configs'] for p in (REPO/directory).rglob('*') if p.is_file() and p.suffix in ['.py','.yaml']}
    for name in ['RUN_G_PHASE3_FROZEN_CONFIG.yaml','RUN_G_MECHANICS_COVERAGE.csv','pyproject.toml']:independent[name]=digest(REPO/name)
    check('manifest_independent_file_equality',independent,manifest,'F-08')
    check('manifest_reconciles',True,validate_manifest(REPO,REPO/'outputs/run_g/source_config_manifest.json'),'F-08')
    save('provenance.json',{'files':independent,'content_tree_hash':content_tree_hash(manifest),'file_count':len(manifest)})
    # Mechanic failure injection in an external CSV, with classification unchanged.
    rows=list(csv.DictReader((REPO/'RUN_G_MECHANICS_COVERAGE.csv').open()))
    with tempfile.TemporaryDirectory(dir=OUT) as tmp:
        rows[0]['status']='NOT IMPLEMENTED'
        path=Path(tmp)/'registry.csv'
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        check('declared_ranking_gap_blocks',True,rejected(lambda:validate_mechanic_registry(path)),'H-06')
    # One protected C0 pair: label invariance only, no performance interpretation.
    kwargs=dict(candidate_label='protected-a',scenario_label='run-h-protected',trial=0,seed=2026091702,on_play=True,mulligan_policy='baseline_functional_london',sequencing_policy='baseline_hand_demand')
    a,ae=simulate_trial(deck,dict(deck.current_mana_base),**kwargs)
    kwargs['candidate_label']='protected-b'
    b,be=simulate_trial(deck,dict(deck.current_mana_base),**kwargs)
    a.pop('candidate');b.pop('candidate')
    check('protected_label_invariance',True,a==b and ae==be,'NONE')
    save('protected_smoke.json',{'same_summary_without_label':a==b,'same_raw_events':ae==be,'event_count':len(ae),'scope':'noninferential C0 only; no performance summaries retained'})
    save('adversarial_tests.json',records)
    print(json.dumps({'checks':len(records),'passed':sum(r['status']=='PASS' for r in records),'failed':sum(r['status']=='FAIL' for r in records),'failures':[r['test'] for r in records if r['status']=='FAIL']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['reproduce','adversarial'])
    args=parser.parse_args()
    globals()[args.mode]()
