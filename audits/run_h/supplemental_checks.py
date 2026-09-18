"""Additional synthetic-only Run H checks; never modifies production."""
import copy
import inspect
from dataclasses import replace
from audit_helpers import REPO, save, digest
from mana_lab.cards import load_deck
from mana_lab.phase3_depth import structural_state_corpus
from mana_lab.phase3_config import load_phase3_config
from mana_lab.phase3_policies import validate_policy_freeze
from mana_lab.phase3_metrics import aggregate_trial_events, evaluate_critical_sequences
from mana_lab.policies import *
from mana_lab.simulator import enumerate_action_sequences, _selected_result, simulate_trial, _information_value
from mana_lab.mulligan import should_keep, BASELINE_MULLIGAN, ALTERNATE_MULLIGAN
from mana_lab.state import GameState, Permanent, make_card
from mana_lab.metrics import MetricEvidence, uncertainty_aware_dominance

deck=load_deck(REPO/'configs/decks/Strixpatch_Affinity_v1.3.deck.yaml')
cfg=load_phase3_config(REPO/'RUN_G_PHASE3_FROZEN_CONFIG.yaml')
out={}
o=ActionOption('hold',0,0,0,True,1,0)
develop=replace(o,key='develop',reserve_preserved=False,spell_executions=1)
out['reserve_difference']=[choose_action([o,develop],ALTERNATE_ACTION_POLICY,reserve_policy_name=p).key for p in (BASELINE_RESERVE_POLICY,ALTERNATE_RESERVE_POLICY)]
due=replace(o,key='due',due_executions=1,untapped_resources=0)
tempo=replace(o,key='tempo',untapped_resources=2)
out['sequencing_difference']=[choose_action([due,tempo],p).key for p in (BASELINE_ACTION_POLICY,ALTERNATE_ACTION_POLICY)]
hand=[make_card(str(i),n,land=n in deck.land_by_name) for i,n in enumerate(['Mistvault Bridge','Razortide Bridge','Thoughtcast','Thoughtcast','Dispatch','Glint Hawk','Myr Enforcer'])]
out['mulligan_difference']=[should_keep(hand,7,deck,p) for p in (BASELINE_MULLIGAN,ALTERNATE_MULLIGAN)]
# Search a small declared visible-state/revealed-pair corpus for genuine scry divergence.
out['scry_difference']=None
from itertools import combinations
for turn in (1,2,3,4):
    for names in combinations(['Ancient Den','Seat of the Synod','Thoughtcast','Glint Hawk','Myr Enforcer','Nihil Spellbomb'],2):
        s=GameState(turn=turn)
        s.battlefield=[Permanent(make_card('land','Seat of the Synod',artifact=True,land=True),land_spec=deck.land_by_name['Seat of the Synod'])]
        pair=tuple(make_card(str(i),n,land=n in deck.land_by_name) for i,n in enumerate(names))
        a,b=[make_scry_policy(deck,p)(pair,VisibleState.from_state(s)) for p in (BASELINE_SCRY_POLICY,ALTERNATE_SCRY_POLICY)]
        if a!=b: out['scry_difference']={'turn':turn,'revealed':names,'baseline':str(a),'alternate':str(b)}; break
    if out['scry_difference']:break
# Information valuations are distinct, but changing scale need not change lexicographic policy choices.
out['information_values']={p:_information_value([{'event':'information_node','kind':'draw','count':1}],p) for p in (BASELINE_INFORMATION_POLICY,CONSERVATIVE_INFORMATION_POLICY)}
out['independent_scry_argument']='scry_policy_name' in inspect.signature(simulate_trial).parameters
c=copy.deepcopy(cfg['policies']);c['identities']['sequencing_baseline']=c['identities']['scry_baseline']
try:validate_policy_freeze(c);out['wrong_policy_kind_accepted']=True
except ValueError:out['wrong_policy_kind_accepted']=False
out['wide_interval_equivalence']=uncertainty_aware_dominance({'m':MetricEvidence('higher',False,.4,-.001,.8,.0025,.005)}).status
out['nan_with_other_superiority']=uncertainty_aware_dominance({'unknown':MetricEvidence('higher',True,float('nan')),'good':MetricEvidence('higher',True,1)}).status
try:out['empty_vector']=uncertainty_aware_dominance({}).status
except ValueError:out['empty_vector']='rejected'
# Independent variants for each structural class: tapped source, visible land choice,
# two hidden libraries; record both true root and complete selected sequence.
rows=[]
for label,original in structural_state_corpus(deck):
    state=copy.deepcopy(original)
    state.battlefield[0].tapped=True
    state.hand.append(make_card('audit-land','Mistvault Bridge',artifact=True,land=True))
    choices={}
    for depth in (7,8,9):
        state.library=[make_card('hidden','Thoughtcast')]
        r=enumerate_action_sequences(state,deck,scry_policy_name=BASELINE_SCRY_POLICY,max_depth=depth)
        selected=_selected_result(r,BASELINE_ACTION_POLICY)
        choices[str(depth)]={'count':len(r),'max_actions':max(len(x.planner_actions) for x in r),'selected':selected.option.key}
    hidden=[]
    for card in ('Thoughtcast','Ancient Den'):
        state.library=[make_card('hidden',card,land=card in deck.land_by_name)]
        r=enumerate_action_sequences(state,deck,scry_policy_name=BASELINE_SCRY_POLICY,max_depth=8)
        hidden.append(_selected_result(r,BASELINE_ACTION_POLICY).option.key)
    rows.append({'class':label,'variants':choices,'hidden_library_invariant':hidden[0]==hidden[1]})
out['independent_depth_variants']=rows
def ev(i,kind,**kw):return dict(event_id=i,event=kind,turn=2,scenario='toy',replicate=1,trial_id=0,on_play=True,**kw)
opening=ev(1,'opening_hand',opening_land_count=2,mulligans=0,keep_size=7)
primary=ev(2,'spell_window',event_role='primary_pre_spend_opportunity',opportunity_id='one',castable=True,card='Baleful Strix',uid='one')
diag=dict(primary,event_id=3,event_role='post_spend_diagnostic')
out['diagnostic_not_denominator']=aggregate_trial_events([opening,primary,diag])['spell_opportunities']==1
out['empty_denominator_raw_counts']=aggregate_trial_events([opening])['spell_opportunities']==0
out['raw_cast_not_functional']=not evaluate_critical_sequences([ev(1,'spell_cast',card='Baleful Strix')])['T2_STRIX_UB']
out['loop_negative']=not evaluate_critical_sequences([])['T3_CRYOGEN_HAWK_LOOP']
out['repeated_same_instance_counts_as_double']=evaluate_critical_sequences([dict(ev(1,'spell_resolution',card='Glint Hawk',uid='one',functional=True),turn=4),dict(ev(2,'spell_resolution',card='Glint Hawk',uid='one',functional=True),turn=4)])['T4_DOUBLE_SPELL']
save('supplemental_checks.json',out)
print({k:v for k,v in out.items() if k!='independent_depth_variants'})
