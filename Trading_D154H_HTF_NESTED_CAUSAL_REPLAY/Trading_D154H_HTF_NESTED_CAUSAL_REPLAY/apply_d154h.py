#!/usr/bin/env python3
from __future__ import annotations
import re,shutil,subprocess,sys
from pathlib import Path

BASE_HEAD='0c2561619b70eff6deafa90cf9a79730de2e5848'
EXPECTED_EA_BLOB='a7955756a34e7811e266933c75dc1dc848887eb3'
EA_PATH=Path("mt5/experts/MentorDeterministicV2EA.mq5")
EXPECTED_DOC_BLOBS={
    Path("docs/ea/HANDOFF.md"):'7fbe736aa85828a25c93a158c98f1383da0f2420',
    Path("docs/ea/v2/HANDOFF_V2.md"):'022cefcfd415ae7d0461c581caa77b94db0e8db3',
    Path("docs/ea/v2/RESEARCH_STATE_V2.md"):'645d0f205f12a08490fee21492b3908ccabde873',
    Path("docs/ea/v2/BACKLOG_V2.md"):'371393db7f0524de49d41c9dc994b776a087a261',
    Path("docs/ea/DECISIONS.md"):'c3b8ff7b0714a4ffdb1aa780f4541d48d7cd9410',
}
D154H_DECL=r'''
// D-154H shadow-only HTF nested causal replay.
// Records ordered H1/M30 structure events and scenario stage anchors so actual
// fills can be reconstructed as causal state-transition paths. No strategy authority.
struct V2D154HTracker
  {
   bool              valid;
   int               scenario_index;
   string            scenario_id;
   int               direction;
   datetime          fill_at;
   int               contributor_count;
   bool              primary_outcome_logged;
   string            primary_outcome;
   datetime          primary_outcome_at;
  };

V2D154HTracker g_d154h_trackers[];
long g_d154h_event_seq=0;
long g_d154h_htf_events=0;
long g_d154h_stage_rows=0;
long g_d154h_fills=0;
long g_d154h_plus1=0;
long g_d154h_sl=0;
long g_d154h_censored=0;

void D154HOnStructureEvent(const V1StructureState &state,
                           const int event_type,
                           const int direction,
                           const V1WaveRef &broken,
                           const V1WaveRef &protected_ref,
                           const MqlRates &bar,
                           const datetime available_at);
void D154HOnScenarioStage(const string stage,const int scenario_index,const datetime at);
void D154HOnFill(const int scenario_index,const datetime observed_at);
void D154HOnPrimaryReference(const int scenario_index,const string outcome,const datetime at);
void D154HOnTesterStart(const datetime at);
void D154HOnTesterEnd(const datetime at);
'''
D154H_BLOCK=r'''
//+------------------------------------------------------------------+
//| D-154H HTF nested causal replay                                  |
//| Observation only. No Entry/SL/TP/order/sizing/SP/EM authority.   |
//+------------------------------------------------------------------+
bool D154HEnabled()
  {
   return (InpV2D154HHTFNestedReplayAudit && InpV2D151CausalAudit);
  }

int D154HFindTracker(const int scenario_index)
  {
   for(int i=0;i<ArraySize(g_d154h_trackers);i++)
      if(g_d154h_trackers[i].valid && g_d154h_trackers[i].scenario_index==scenario_index)
         return i;
   return -1;
  }

string D154HWaveIdOrNA(const V1WaveRef &w)
  {
   return (w.valid && w.id!="" ? w.id : "NA");
  }

double D154HWavePriceOrZero(const V1WaveRef &w)
  {
   return (w.valid ? w.price : 0.0);
  }

string D154HStateDetail(const string prefix,const V1StructureState &s)
  {
   string core=StringFormat("%s_trend=%s %s_owner_id=%s %s_owner_started_s=%I64d %s_structure_events=%I64d",
                            prefix,TrendName(s.trend),
                            prefix,s.owner_id=="" ? "NA" : s.owner_id,
                            prefix,(long)s.owner_started_at,
                            prefix,s.structure_events);
   string refs=StringFormat("%s_protected_high_id=%s %s_protected_high=%.10f %s_protected_low_id=%s %s_protected_low=%.10f %s_external_high_id=%s %s_external_high=%.10f %s_external_low_id=%s %s_external_low=%.10f",
                            prefix,D154HWaveIdOrNA(s.protected_high),prefix,D154HWavePriceOrZero(s.protected_high),
                            prefix,D154HWaveIdOrNA(s.protected_low),prefix,D154HWavePriceOrZero(s.protected_low),
                            prefix,D154HWaveIdOrNA(s.external_high),prefix,D154HWavePriceOrZero(s.external_high),
                            prefix,D154HWaveIdOrNA(s.external_low),prefix,D154HWavePriceOrZero(s.external_low));
   return core+" "+refs;
  }

string D154HNestedRelation()
  {
   bool h1_mature=IsMatureDirectionalTrend(g_structure[1].trend) && g_structure[1].owner_id!="";
   bool m30_mature=IsMatureDirectionalTrend(g_structure[2].trend) && g_structure[2].owner_id!="";
   if(h1_mature)
     {
      if(m30_mature)
        {
         if(TrendDirection(g_structure[1].trend)==TrendDirection(g_structure[2].trend))
            return "H1_PRIMARY_M30_ALIGNED";
         return "H1_PRIMARY_M30_OPPOSITE";
        }
      if(g_structure[2].trend==V1_TREND_TRANSITION)
         return "H1_PRIMARY_M30_TRANSITION";
      return "H1_PRIMARY_M30_NEUTRAL";
     }
   if(m30_mature)
      return "M30_PRIMARY";
   if(g_structure[1].trend==V1_TREND_TRANSITION || g_structure[2].trend==V1_TREND_TRANSITION)
      return "NO_PRIMARY_TRANSITIONAL";
   return "NO_DIRECTIONAL_PRIMARY";
  }

void D154HOnStructureEvent(const V1StructureState &state,
                           const int event_type,
                           const int direction,
                           const V1WaveRef &broken,
                           const V1WaveRef &protected_ref,
                           const MqlRates &bar,
                           const datetime available_at)
  {
   if(!D154HEnabled() ||
      (state.tf!=PERIOD_H1 && state.tf!=PERIOD_M30) ||
      g_execution_epoch_start<=0 || available_at<g_execution_epoch_start)
      return;

   g_d154h_event_seq++;
   g_d154h_htf_events++;

   string post_trend=TrendName(state.trend);
   string post_owner=(state.owner_id=="" ? "NA" : state.owner_id);
   if(event_type==V1_EVENT_PROTECTED_BREAK)
     {
      post_trend="TRANSITION";
      post_owner="NA";
     }

   string detail=StringFormat("seq=%I64d event_type=%s event_direction=%s event_tf=%s event_owner_id=%s event_owner_started_s=%I64d bar_open_s=%I64d available_at_s=%I64d broken_id=%s broken_price=%.10f protected_ref_id=%s protected_ref_price=%.10f callback_trend=%s callback_owner_id=%s inferred_post_trend=%s inferred_post_owner_id=%s protected_break_post_transition_inferred=%s same_timestamp_priority=H1_THEN_M30 nested_relation_callback=%s",
                              g_d154h_event_seq,EventName(event_type),DirectionName(direction),TfName(state.tf),
                              state.owner_id=="" ? "NA" : state.owner_id,(long)state.owner_started_at,
                              (long)bar.time,(long)available_at,
                              broken.valid ? broken.id : "NA",broken.valid ? broken.price : 0.0,
                              protected_ref.valid ? protected_ref.id : "NA",protected_ref.valid ? protected_ref.price : 0.0,
                              TrendName(state.trend),state.owner_id=="" ? "NA" : state.owner_id,
                              post_trend,post_owner,event_type==V1_EVENT_PROTECTED_BREAK ? "true" : "false",
                              D154HNestedRelation());
   detail+=" "+D154HStateDetail("h1",g_structure[1]);
   detail+=" "+D154HStateDetail("m30",g_structure[2]);

   LogLine("D154H_HTF_EVENT",TfName(state.tf),available_at,
           BuildStructureEventId(state,event_type,bar),detail);
  }

void D154HOnScenarioStage(const string stage,const int scenario_index,const datetime at)
  {
   if(!D154HEnabled() ||
      scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION)
      return;

   V1ScenarioPlan p=g_scenarios[scenario_index];
   string detail=StringFormat("stage=%s seq_at_stage=%I64d scenario_id=%s direction=%s plan_map_tf=%s plan_owner_id=%s root_zone_id=%s source_tf=%s frozen_at_s=%I64d source_contact_at_s=%I64d sweep_at_s=%I64d choch_at_s=%I64d fvg_available_at_s=%I64d pending_submitted_at_s=%I64d fill_at_s=%I64d contributor_count=%d contributor_scenario_ids=%s contributor_root_ids=%s frozen_h1_trend=%s frozen_h1_owner_id=%s frozen_m30_trend=%s frozen_m30_owner_id=%s nested_relation_now=%s strategy_authority=false",
                              stage,g_d154h_event_seq,p.id,DirectionName(p.direction),TfName(p.active_map_tf),
                              p.owner_id=="" ? "NA" : p.owner_id,p.root_zone_id,TfName(p.source_tf),
                              (long)p.frozen_at,(long)p.source_contact_at,(long)p.active_sweep_at,(long)p.scenario_choch_at,
                              (long)p.selected_fvg_available_at,(long)p.pending_submitted_at,(long)p.fill_at,
                              p.execution_contributor_count,
                              p.execution_contributor_scenario_ids=="" ? p.id : p.execution_contributor_scenario_ids,
                              p.execution_contributor_root_ids=="" ? p.root_zone_id : p.execution_contributor_root_ids,
                              TrendName(p.h1_trend_at_freeze),p.h1_owner_id_at_freeze=="" ? "NA" : p.h1_owner_id_at_freeze,
                              TrendName(p.m30_trend_at_freeze),p.m30_owner_id_at_freeze=="" ? "NA" : p.m30_owner_id_at_freeze,
                              D154HNestedRelation());
   detail+=" "+D154HStateDetail("h1",g_structure[1]);
   detail+=" "+D154HStateDetail("m30",g_structure[2]);

   LogLine("D154H_STAGE_SNAPSHOT","M1",at,p.id,detail);
   g_d154h_stage_rows++;
  }

void D154HOnFill(const int scenario_index,const datetime observed_at)
  {
   if(!D154HEnabled() ||
      scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION ||
      D154HFindTracker(scenario_index)>=0)
      return;

   D154HOnScenarioStage("FILL",scenario_index,observed_at);

   V2D154HTracker t;
   ZeroMemory(t);
   t.valid=true;
   t.scenario_index=scenario_index;
   t.scenario_id=g_scenarios[scenario_index].id;
   t.direction=g_scenarios[scenario_index].direction;
   t.fill_at=observed_at;

   string contributors=g_scenarios[scenario_index].execution_contributor_scenario_ids;
   if(contributors=="") contributors=t.scenario_id;
   string ids[];
   ushort sep=(ushort)StringGetCharacter("|",0);
   int parsed=StringSplit(contributors,sep,ids);
   if(parsed<=0) parsed=1;
   t.contributor_count=parsed;

   int n=ArraySize(g_d154h_trackers);
   if(ArrayResize(g_d154h_trackers,n+1)<0)
      return;
   g_d154h_trackers[n]=t;
   g_d154h_fills++;

   LogLine("D154H_FILL_REPLAY_ANCHOR","M1",observed_at,t.scenario_id,
           StringFormat("scenario_id=%s direction=%s fill_at_s=%I64d event_seq_at_fill=%I64d contributor_count=%d contributor_scenario_ids=%s contributor_root_ids=%s plan_map_tf=%s plan_owner_id=%s nested_relation_at_fill=%s unit=ACTUAL_EXECUTION_FILL strategy_authority=false",
                        t.scenario_id,DirectionName(t.direction),(long)observed_at,g_d154h_event_seq,
                        t.contributor_count,contributors,
                        g_scenarios[scenario_index].execution_contributor_root_ids=="" ? g_scenarios[scenario_index].root_zone_id : g_scenarios[scenario_index].execution_contributor_root_ids,
                        TfName(g_scenarios[scenario_index].active_map_tf),
                        g_scenarios[scenario_index].owner_id=="" ? "NA" : g_scenarios[scenario_index].owner_id,
                        D154HNestedRelation()));
  }

void D154HOnPrimaryReference(const int scenario_index,const string outcome,const datetime at)
  {
   if(!D154HEnabled())
      return;
   int idx=D154HFindTracker(scenario_index);
   if(idx<0)
     {
      LogLine("D154H_INTEGRITY_WARNING","M1",at,"",
              StringFormat("scenario_index=%d outcome=%s reason=NO_FILL_TRACKER strategy_authority=false",scenario_index,outcome));
      return;
     }
   V2D154HTracker t=g_d154h_trackers[idx];
   if(t.primary_outcome_logged)
      return;
   t.primary_outcome_logged=true;
   t.primary_outcome=outcome;
   t.primary_outcome_at=at;
   g_d154h_trackers[idx]=t;

   if(outcome=="PLUS_1R") g_d154h_plus1++;
   else if(outcome=="SL_FIRST") g_d154h_sl++;
   else if(outcome=="RIGHT_CENSORED") g_d154h_censored++;

   LogLine("D154H_PRIMARY_OUTCOME","M1",at,t.scenario_id,
           StringFormat("scenario_id=%s direction=%s outcome=%s event_seq_at_outcome=%I64d contributor_count=%d discovery_use=SEQUENCE_TAXONOMY_ONLY no_same_sample_gate_promotion=true strategy_authority=false",
                        t.scenario_id,DirectionName(t.direction),outcome,g_d154h_event_seq,t.contributor_count));
  }

void D154HOnTesterStart(const datetime at)
  {
   if(!D154HEnabled())
      return;
   LogLine("D154H_RESEARCH_START","M1",at,"",
           "build=2.08R0L8 phase=V2_D154H_HTF_NESTED_CAUSAL_REPLAY population=ACTUAL_FILLED_CONTINUATION causal_window=PLAN_TO_FILL htf_events=H1_M30_INITIAL_BOS_BOS_PROTECTED_BREAK stage_anchors=PLAN_ROOT_CONTACT_SWEEP_CHOCH_PENDING_FILL merged_unit=ACTUAL_FILL purpose=RECONSTRUCT_ORDERED_HTF_STATE_TRANSITIONS discovery=GOLD23_NO_FILTER_PREDEFINED threshold_fit=false score=false same_sample_gate_promotion=false strategy_authority=false entry_change=false sl_change=false tp_change=false sizing_change=false sp_change=false em_change=false");
  }

void D154HOnTesterEnd(const datetime at)
  {
   if(!D154HEnabled())
      return;
   for(int i=0;i<ArraySize(g_d154h_trackers);i++)
      if(g_d154h_trackers[i].valid && !g_d154h_trackers[i].primary_outcome_logged)
         D154HOnPrimaryReference(g_d154h_trackers[i].scenario_index,"RIGHT_CENSORED",at);

   LogLine("D154H_RESEARCH_STOP","M1",at,"",
           StringFormat("build=2.08R0L8 htf_events=%I64d stage_rows=%I64d fills=%I64d plus1=%I64d sl_first=%I64d censored=%I64d purpose=SEQUENCE_DISCOVERY_ONLY strategy_authority=false no_trade_modification=true",
                        g_d154h_htf_events,g_d154h_stage_rows,g_d154h_fills,g_d154h_plus1,g_d154h_sl,g_d154h_censored));
  }
'''

def run(*args:str)->str:
    return subprocess.check_output(list(args),text=True,stderr=subprocess.STDOUT).strip()

def text_once(s,old,new,label):
    c=s.count(old)
    if c!=1: raise RuntimeError(f"{label}: expected one marker, found {c}")
    return s.replace(old,new,1)

def regex_once(s,pat,repl,label,flags=0):
    out,n=re.subn(pat,repl,s,count=1,flags=flags)
    if n!=1: raise RuntimeError(f"{label}: expected one regex match, found {n}")
    return out

def normalize(raw:bytes)->str:
    return raw.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n")

def verify_local_equals_head(repo:Path,path:Path)->None:
    local=normalize((repo/path).read_bytes())
    head=normalize(subprocess.check_output(["git","show",f"HEAD:{path.as_posix()}"] ))
    if local!=head:
        print(f"ERROR: {path} has real local content changes relative to HEAD. Fail-closed.")
        diff=subprocess.run(["git","diff","--unified=3","--",path.as_posix()],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout
        print("\n".join(diff.splitlines()[:120])); raise SystemExit(2)

def transform_source(text:str)->str:
    if "InpV2D154HHTFNestedReplayAudit" in text or "D154H_RESEARCH_START" in text:
        raise RuntimeError("D-154H markers already exist; refusing double-apply.")
    new=text
    new=regex_once(new,r'#property version\s+"2\.07"\s*\n#property description\s+"Mentor deterministic V2 EA - D154G HTF Root birth lineage audit"',
                   '#property version   "2.08"\n#property description "Mentor deterministic V2 EA - D154H HTF nested causal replay"',"property identity")
    new=text_once(new,
        'input bool   InpV2D154GHTFRootLineageAudit = false;\n',
        'input bool   InpV2D154GHTFRootLineageAudit = false;\n\n'
        '// D-154H shadow-only: replay ordered H1/M30 state transitions from PLAN to Fill.\n'
        '// No Entry/SL/TP/order/sizing/SP/EM authority.\n'
        'input bool   InpV2D154HHTFNestedReplayAudit = false;\n',"D154H input")
    new=text_once(new,
        '   if(StringFind(event_name,"D154G_")==0)\n      return true;\n',
        '   if(StringFind(event_name,"D154G_")==0)\n      return true;\n'
        '   if(StringFind(event_name,"D154H_")==0)\n      return true;\n',"compact log whitelist")
    new=regex_once(new,r'(^bool D151Enabled\(\)\s*\n)',D154H_DECL+'\n\n'+r'\1',"D154H declarations",flags=re.MULTILINE)
    new=regex_once(new,r'(^bool D154GEnabled\(\)\s*\n)',D154H_BLOCK+'\n\n'+r'\1',"D154H block",flags=re.MULTILINE)
    new=text_once(new,
        '   D154COnStructureEvent(s,event_type,direction,bar,available_at);\n',
        '   D154COnStructureEvent(s,event_type,direction,bar,available_at);\n   D154HOnStructureEvent(s,event_type,direction,broken,protected_ref,bar,available_at);\n',"HTF event hook")
    new=text_once(new,
        '   EdgeAuditOnScenarioStage(V1_EDGE_STAGE_PLAN,n,frozen_at,plan_reference_price,\n',
        '   D154HOnScenarioStage("PLAN",n,frozen_at);\n   EdgeAuditOnScenarioStage(V1_EDGE_STAGE_PLAN,n,frozen_at,plan_reference_price,\n',"PLAN stage hook")
    new=text_once(new,
        '   D154FOnRootContact(scenario_index,bar,available_at);\n',
        '   D154FOnRootContact(scenario_index,bar,available_at);\n   D154HOnScenarioStage("ROOT_CONTACT",scenario_index,available_at);\n',"ROOT_CONTACT stage hook")
    new=text_once(new,
        '      D154FOnSweepAccepted(sidx,bar,available_at);\n',
        '      D154FOnSweepAccepted(sidx,bar,available_at);\n      D154HOnScenarioStage("SWEEP",sidx,available_at);\n',"SWEEP stage hook")
    new=text_once(new,
        '      D154FOnChochAccepted(sidx,bar,available_at);\n',
        '      D154FOnChochAccepted(sidx,bar,available_at);\n      D154HOnScenarioStage("CHOCH",sidx,available_at);\n',"CHOCH stage hook")
    new=text_once(new,
        '   g_orders_accepted++;\n\n   LogLine("PENDING_ORDER_ACCEPTED"',
        '   g_orders_accepted++;\n   D154HOnScenarioStage("PENDING",scenario_index,available_at);\n\n   LogLine("PENDING_ORDER_ACCEPTED"',"PENDING stage hook")
    new=text_once(new,
        '   D154GOnFill(scenario_index,observed_at);\n   g_positions_filled++;\n',
        '   D154GOnFill(scenario_index,observed_at);\n   D154HOnFill(scenario_index,observed_at);\n   g_positions_filled++;\n',"fill hook")
    new=text_once(new,
        '   D154GOnPrimaryReference(t.scenario_index,"PLUS_1R",at);\n',
        '   D154GOnPrimaryReference(t.scenario_index,"PLUS_1R",at);\n   D154HOnPrimaryReference(t.scenario_index,"PLUS_1R",at);\n',"+1R hook")
    new=text_once(new,
        '   D154GOnPrimaryReference(t.scenario_index,"SL_FIRST",at);\n',
        '   D154GOnPrimaryReference(t.scenario_index,"SL_FIRST",at);\n   D154HOnPrimaryReference(t.scenario_index,"SL_FIRST",at);\n',"SL hook")
    new=text_once(new,
        '   D154GOnTesterStart(TimeCurrent());\n',
        '   D154GOnTesterStart(TimeCurrent());\n   D154HOnTesterStart(TimeCurrent());\n',"tester start")
    new=text_once(new,
        '   D154GOnTesterEnd(TimeCurrent());\n',
        '   D154GOnTesterEnd(TimeCurrent());\n   D154HOnTesterEnd(TimeCurrent());\n',"tester end")
    new=new.replace("build=2.07R0L7","build=2.08R0L8")
    new=new.replace("phase=V2_D154G_HTF_ROOT_BIRTH_LINEAGE_AUDIT trackers=","phase=V2_D154H_HTF_NESTED_CAUSAL_REPLAY trackers=")
    new=new.replace("strategy_semantics=V2_CONTINUATION_ONLY_PLUS_D151_D152_SP_RESEARCH_PLUS_D154A_D154B_D154C_D154F_D154G_SHADOW",
                    "strategy_semantics=V2_CONTINUATION_ONLY_PLUS_D151_D152_SP_RESEARCH_PLUS_D154A_D154B_D154C_D154F_D154G_D154H_SHADOW")
    req=['#property version   "2.08"','InpV2D154HHTFNestedReplayAudit = false;','struct V2D154HTracker',
         'D154HOnStructureEvent(s,event_type,direction,broken,protected_ref,bar,available_at);',
         'D154HOnScenarioStage("PLAN",n,frozen_at);','D154HOnScenarioStage("ROOT_CONTACT",scenario_index,available_at);',
         'D154HOnScenarioStage("SWEEP",sidx,available_at);','D154HOnScenarioStage("CHOCH",sidx,available_at);',
         'D154HOnScenarioStage("PENDING",scenario_index,available_at);','D154HOnFill(scenario_index,observed_at);',
         'D154HOnPrimaryReference(t.scenario_index,"PLUS_1R",at);','D154HOnPrimaryReference(t.scenario_index,"SL_FIRST",at);',
         'D154HOnTesterStart(TimeCurrent());','D154HOnTesterEnd(TimeCurrent());']
    miss=[x for x in req if x not in new]
    if miss: raise RuntimeError("generated EA missing invariant(s): "+", ".join(miss))
    return new

def main()->int:
    repo=Path.cwd()
    if not (repo/'.git').exists(): print('ERROR: run from Trading repository root.'); return 2
    head=run('git','rev-parse','HEAD')
    if head!=BASE_HEAD:
        print(f'ERROR: exact Git HEAD required for D-154H. expected={BASE_HEAD} actual={head}'); return 2
    blob=run('git','rev-parse',f'HEAD:{EA_PATH.as_posix()}')
    if blob!=EXPECTED_EA_BLOB:
        print(f'ERROR: committed EA blob changed. expected={EXPECTED_EA_BLOB} actual={blob}'); return 2
    if run('git','diff','--cached','--name-only','--',EA_PATH.as_posix()): print('ERROR: EA has staged changes.'); return 2
    verify_local_equals_head(repo,EA_PATH)
    for path,expected in EXPECTED_DOC_BLOBS.items():
        actual=run('git','rev-parse',f'HEAD:{path.as_posix()}')
        if actual!=expected: print(f'ERROR: committed doc changed: {path} expected={expected} actual={actual}'); return 2
        if run('git','diff','--cached','--name-only','--',path.as_posix()): print(f'ERROR: staged doc changes: {path}'); return 2
        verify_local_equals_head(repo,path)

    package=Path(__file__).resolve().parent
    new_tools=['tools/compare_d154h_parity.py','tools/run_d154h_parity_gold23_q1.py','tools/run_d154h_discovery_gold23.py','tools/summarize_d154h_nested_replay.py']
    new_docs=['docs/ea/v2/D154G_HTF_ROOT_BIRTH_LINEAGE_RESULTS.md','docs/ea/v2/D154H_HTF_NESTED_CAUSAL_REPLAY.md']
    for rel in new_tools+new_docs:
        if (repo/rel).exists(): print(f'ERROR: target already exists: {rel}'); return 2

    raw=(repo/EA_PATH).read_bytes(); newline='\r\n' if b'\r\n' in raw else '\n'; had_bom=raw.startswith(b'\xef\xbb\xbf')
    try: generated=transform_source(normalize(raw))
    except Exception as e: print('ERROR: EA transform failed:',e); return 2

    backups=[]; created=[]
    try:
        bak=repo/(EA_PATH.as_posix()+'.d154h_bak'); shutil.copy2(repo/EA_PATH,bak); backups.append((repo/EA_PATH,bak))
        out=generated.replace('\n',newline).encode('utf-8');
        if had_bom: out=b'\xef\xbb\xbf'+out
        (repo/EA_PATH).write_bytes(out)

        for rel in ['docs/ea/v2/HANDOFF_V2.md','docs/ea/v2/RESEARCH_STATE_V2.md','docs/ea/v2/BACKLOG_V2.md']:
            dst=repo/rel; bak=repo/(rel+'.d154h_bak'); shutil.copy2(dst,bak); backups.append((dst,bak)); shutil.copy2(package/'repo_files'/rel,dst)

        hp=repo/'docs/ea/HANDOFF.md'; bak=repo/'docs/ea/HANDOFF.md.d154h_bak'; shutil.copy2(hp,bak); backups.append((hp,bak))
        ht=normalize(hp.read_bytes())
        old='''> **V2 ACTIVE ROUTING — 2026-08-22 / D-154G**  
> Current V2 phase is `D-154G HTF ROOT BIRTH LINEAGE AUDIT`. For active V2 work, `docs/ea/v2/HANDOFF_V2.md` and `docs/ea/v2/AGENTS_V2.md` override stale phase labels in the historical body below.  
> D-154F local M1 lineage / TRANSITION hypotheses were not promoted; baseline strategy semantics remain unchanged.
'''
        newbanner='''> **V2 ACTIVE ROUTING — 2026-08-22 / D-154H**  
> Current V2 phase is `D-154H HTF NESTED CAUSAL REPLAY`. For active V2 work, `docs/ea/v2/HANDOFF_V2.md` and `docs/ea/v2/AGENTS_V2.md` override stale phase labels in the historical body below.  
> D-154G did not promote a Root-lineage or refresh veto; baseline strategy semantics remain unchanged.
'''
        if ht.count(old)!=1: raise RuntimeError('root HANDOFF D154G banner marker mismatch')
        hp.write_text(ht.replace(old,newbanner,1),encoding='utf-8',newline='')

        dp=repo/'docs/ea/DECISIONS.md'; bak=repo/'docs/ea/DECISIONS.md.d154h_bak'; shutil.copy2(dp,bak); backups.append((dp,bak))
        dt=normalize(dp.read_bytes())
        if '## D-154H — Preserve ordered HTF state transitions before designing another Entry gate' in dt: raise RuntimeError('D154H decision already exists')
        decision='''

## D-154H — Preserve ordered HTF state transitions before designing another Entry gate

Status: `RESEARCH / SHADOW-ONLY`  
Date: `2026-08-22`

Decision:
- D-154G prior-owner Root reuse had zero observed coverage across 457 discovery+validation fills.
- GOLD23 same-owner pre-entry BOS refresh did not generalize; no refresh-cancel rule is promoted.
- Simple static H1/M30 alignment also did not generalize.
- The next phase must not add another scalar threshold, quality score, or market-specific exception.
- D-154H records ordered H1/M30 INITIAL_BOS/BOS/PROTECTED_BREAK events and exact PLAN/Root-contact/Sweep/CHOCH/Pending/Fill stage anchors.
- The actual Fill remains the outcome unit even with merged Root contributors.
- D-154H is discovery instrumentation only: no sequence discovered on GOLD23 may become a strategy gate until separately frozen and validated.
- Entry, SL, TP, sizing, order lifecycle, SP and EM authority are unchanged.
'''
        dp.write_text(dt.rstrip()+decision+'\n',encoding='utf-8',newline='')

        for rel in new_tools+new_docs:
            dst=repo/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(package/'repo_files'/rel,dst); created.append(dst)
    except Exception as e:
        print('ERROR during apply:',e)
        for dst,bak in reversed(backups):
            try:
                if bak.exists(): shutil.copy2(bak,dst)
            except OSError: pass
        for p in created:
            try:p.unlink()
            except OSError:pass
        return 2
    finally:
        for _,bak in backups:
            try:bak.unlink()
            except OSError:pass

    print('D-154H HTF nested causal replay package applied.')
    print('EA target build: 2.08R0L8')
    print('No commit/push performed.')
    print('Next: compile 0 errors, refresh tester preset, then:')
    print(r'  python tools\run_d154h_parity_gold23_q1.py --dry-run')
    print(r'  python tools\run_d154h_parity_gold23_q1.py')
    return 0

if __name__=='__main__': raise SystemExit(main())
