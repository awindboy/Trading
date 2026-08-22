#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import shutil

EXPECTED_HEAD = "3bf78e1d34a6721b9fe32115f8f6af050babbda6"
EXPECTED_BASE_EA_BLOB = "a6312fc7d0554374058719e805c5b77ad91acd1a"
EA_PATH = Path("mt5/experts/MentorDeterministicV2EA.mq5")

D154B_DECL = r"""
// D-154B shadow-only confirmation-entry audit.
// Population: actual EXTERNAL_CONTINUATION fills observed while M1 is TRANSITION.
// It tests the first post-Fill M1 INITIAL_BOS without changing the real trade.
struct V2D154BTracker
  {
   bool       valid;
   int        scenario_index;
   string     scenario_id;
   int        direction;
   datetime   fill_at;
   double     original_fill;
   double     original_sl;
   double     original_risk;
   double     structural_tp;

   bool       first_initial_seen;
   int        first_initial_direction;
   datetime   first_initial_at;
   double     first_initial_bar_close;

   bool       primary_reference_logged;
   string     primary_outcome;
   datetime   primary_terminal_at;

   bool       candidate_armed;
   datetime   candidate_at;
   double     shadow_entry;
   double     shadow_entry_r_from_original;
   double     shadow_risk;
   double     shadow_plus1_price;
   double     structural_tp_r;
   double     spread_at_entry;

   bool       shadow_terminal;
   string     shadow_outcome;
   datetime   shadow_terminal_at;
   double     shadow_mfe_r;
   double     shadow_mae_r;

   bool       map_support_lost;
   datetime   map_support_lost_at;
  };

V2D154BTracker g_d154b_trackers[];
long g_d154b_transition_fills=0;
long g_d154b_first_same=0;
long g_d154b_first_opposite=0;
long g_d154b_no_initial_before_primary=0;
long g_d154b_candidates_armed=0;
long g_d154b_candidates_infeasible_room=0;
long g_d154b_shadow_plus1=0;
long g_d154b_shadow_sl=0;
long g_d154b_shadow_censored=0;

void D154BOnFill(const int scenario_index,const datetime observed_at);
void D154BOnStructureEvent(const V1StructureState &state,
                           const int event_type,
                           const int direction,
                           const MqlRates &bar,
                           const datetime available_at);
void D154BOnPrimaryReference(const int scenario_index,
                             const string outcome,
                             const datetime at);
void D154BAuditOnTick(const MqlTick &tick);
void D154BOnTesterStart(const datetime at);
void D154BOnTesterEnd(const datetime at);
"""

D154B_BLOCK = r"""
//+------------------------------------------------------------------+
//| D-154B Post-Fill M1 confirmation-entry shadow audit              |
//| No real Entry/SL/TP/order/sizing/EM authority.                   |
//+------------------------------------------------------------------+
bool D154BEnabled()
  {
   return (InpV2D154BConfirmationAudit && InpV2D151CausalAudit);
  }

int D154BFindTracker(const int scenario_index)
  {
   for(int i=0;i<ArraySize(g_d154b_trackers);i++)
      if(g_d154b_trackers[i].valid &&
         g_d154b_trackers[i].scenario_index==scenario_index)
         return i;
   return -1;
  }

void D154BOnFill(const int scenario_index,const datetime observed_at)
  {
   if(!D154BEnabled() ||
      scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION ||
      g_structure[5].trend!=V1_TREND_TRANSITION ||
      D154BFindTracker(scenario_index)>=0)
      return;

   double risk=g_scenarios[scenario_index].exit_initial_risk_price;
   if(risk<=0.0)
      risk=MathAbs(g_scenarios[scenario_index].fill_price-
                   g_scenarios[scenario_index].normalized_sl);
   if(risk<=LiquidityTickSize())
     {
      LogLine("D154B_TRACKER_SKIPPED","M1",observed_at,g_scenarios[scenario_index].id,
              "reason=INVALID_ORIGINAL_RISK strategy_authority=false");
      return;
     }

   int n=ArraySize(g_d154b_trackers);
   if(ArrayResize(g_d154b_trackers,n+1)<0)
      return;

   V2D154BTracker t;
   t.valid=true;
   t.scenario_index=scenario_index;
   t.scenario_id=g_scenarios[scenario_index].id;
   t.direction=g_scenarios[scenario_index].direction;
   t.fill_at=g_scenarios[scenario_index].fill_at;
   t.original_fill=g_scenarios[scenario_index].fill_price;
   t.original_sl=g_scenarios[scenario_index].normalized_sl;
   t.original_risk=risk;
   t.structural_tp=g_scenarios[scenario_index].final_objective_price;
   t.first_initial_seen=false;
   t.first_initial_direction=0;
   t.first_initial_at=0;
   t.first_initial_bar_close=0.0;
   t.primary_reference_logged=false;
   t.primary_outcome="";
   t.primary_terminal_at=0;
   t.candidate_armed=false;
   t.candidate_at=0;
   t.shadow_entry=0.0;
   t.shadow_entry_r_from_original=0.0;
   t.shadow_risk=0.0;
   t.shadow_plus1_price=0.0;
   t.structural_tp_r=0.0;
   t.spread_at_entry=0.0;
   t.shadow_terminal=false;
   t.shadow_outcome="";
   t.shadow_terminal_at=0;
   t.shadow_mfe_r=0.0;
   t.shadow_mae_r=0.0;
   t.map_support_lost=false;
   t.map_support_lost_at=0;
   g_d154b_trackers[n]=t;
   g_d154b_transition_fills++;

   LogLine("D154B_TRANSITION_FILL","M1",observed_at,t.scenario_id,
           StringFormat("scenario_id=%s direction=%s fill_at_s=%I64d original_fill=%.10f original_sl=%.10f original_risk=%.10f structural_tp=%.10f m1_state_at_fill=%s transition_bias=%s strategy_authority=false",
                        t.scenario_id,DirectionName(t.direction),(long)t.fill_at,
                        t.original_fill,t.original_sl,t.original_risk,t.structural_tp,
                        TrendName(g_structure[5].trend),
                        DirectionName(g_structure[5].transition_bias)));
  }

void D154BMarkShadowTerminal(const int tracker_index,
                             const string outcome,
                             const datetime at,
                             const double terminal_r)
  {
   if(tracker_index<0 || tracker_index>=ArraySize(g_d154b_trackers))
      return;
   V2D154BTracker t=g_d154b_trackers[tracker_index];
   if(!t.valid || !t.candidate_armed || t.shadow_terminal)
      return;

   t.candidate_armed=false;
   t.shadow_terminal=true;
   t.shadow_outcome=outcome;
   t.shadow_terminal_at=at;
   if(terminal_r>t.shadow_mfe_r) t.shadow_mfe_r=terminal_r;
   if(terminal_r<t.shadow_mae_r) t.shadow_mae_r=terminal_r;

   if(outcome=="PLUS_1R") g_d154b_shadow_plus1++;
   else if(outcome=="ORIGINAL_SL") g_d154b_shadow_sl++;
   else if(outcome=="RIGHT_CENSORED") g_d154b_shadow_censored++;

   LogLine("D154B_SHADOW_TERMINAL","M1",at,t.scenario_id,
           StringFormat("scenario_id=%s direction=%s outcome=%s terminal_r=%.8f shadow_entry=%.10f shadow_risk=%.10f shadow_plus1=%.10f original_sl=%.10f structural_tp=%.10f structural_tp_r=%.8f confirmation_r_from_original=%.8f shadow_mfe_r=%.8f shadow_mae_r=%.8f map_support_lost=%s map_support_lost_at_s=%I64d primary_outcome=%s strategy_authority=false",
                        t.scenario_id,DirectionName(t.direction),outcome,terminal_r,
                        t.shadow_entry,t.shadow_risk,t.shadow_plus1_price,
                        t.original_sl,t.structural_tp,t.structural_tp_r,
                        t.shadow_entry_r_from_original,t.shadow_mfe_r,t.shadow_mae_r,
                        t.map_support_lost ? "true" : "false",(long)t.map_support_lost_at,
                        t.primary_reference_logged ? t.primary_outcome : "PENDING"));
   g_d154b_trackers[tracker_index]=t;
  }

void D154BOnStructureEvent(const V1StructureState &state,
                           const int event_type,
                           const int direction,
                           const MqlRates &bar,
                           const datetime available_at)
  {
   if(!D154BEnabled() ||
      state.tf!=PERIOD_M1 ||
      event_type!=V1_EVENT_INITIAL_BOS)
      return;

   for(int i=0;i<ArraySize(g_d154b_trackers);i++)
     {
      V2D154BTracker t=g_d154b_trackers[i];
      if(!t.valid || t.first_initial_seen || available_at<=t.fill_at)
         continue;

      int d151_index=D151FindTracker(t.scenario_index);
      if(d151_index<0)
         continue;
      if(g_d151_trackers[d151_index].reached_1r ||
         g_d151_trackers[d151_index].pre1_failure)
         continue;

      t.first_initial_seen=true;
      t.first_initial_direction=direction;
      t.first_initial_at=available_at;
      t.first_initial_bar_close=bar.close;

      string relation=(direction==t.direction ? "SAME_DIR" : "OPPOSITE_DIR");
      LogLine("D154B_FIRST_INITIAL_BOS","M1",available_at,t.scenario_id,
              StringFormat("scenario_id=%s direction=%s relation=%s event_direction=%s event_at_s=%I64d bar_close=%.10f minutes_after_fill=%.4f strategy_authority=false",
                           t.scenario_id,DirectionName(t.direction),relation,
                           DirectionName(direction),(long)available_at,bar.close,
                           (double)(available_at-t.fill_at)/60.0));

      if(direction!=t.direction)
        {
         g_d154b_first_opposite++;
         g_d154b_trackers[i]=t;
         continue;
        }

      g_d154b_first_same++;

      MqlTick q;
      if(!SymbolInfoTick(_Symbol,q) || q.bid<=0.0 || q.ask<=0.0)
        {
         g_d154b_candidates_infeasible_room++;
         LogLine("D154B_CANDIDATE_INFEASIBLE","M1",available_at,t.scenario_id,
                 StringFormat("scenario_id=%s reason=NO_EXECUTABLE_TICK bar_close=%.10f strategy_authority=false",
                              t.scenario_id,bar.close));
         g_d154b_trackers[i]=t;
         continue;
        }

      double entry=(t.direction>0 ? q.ask : q.bid);
      double shadow_risk=(double)t.direction*(entry-t.original_sl);
      if(shadow_risk<=LiquidityTickSize())
        {
         g_d154b_candidates_infeasible_room++;
         LogLine("D154B_CANDIDATE_INFEASIBLE","M1",available_at,t.scenario_id,
                 StringFormat("scenario_id=%s reason=NONPOSITIVE_ENTRY_TO_ORIGINAL_SL entry=%.10f original_sl=%.10f strategy_authority=false",
                              t.scenario_id,entry,t.original_sl));
         g_d154b_trackers[i]=t;
         continue;
        }

      double structural_room=(double)t.direction*(t.structural_tp-entry);
      double structural_tp_r=structural_room/shadow_risk;
      double entry_r_from_original=(double)t.direction*(entry-t.original_fill)/t.original_risk;

      t.candidate_at=available_at;
      t.shadow_entry=entry;
      t.shadow_entry_r_from_original=entry_r_from_original;
      t.shadow_risk=shadow_risk;
      t.shadow_plus1_price=entry+(double)t.direction*shadow_risk;
      t.structural_tp_r=structural_tp_r;
      t.spread_at_entry=q.ask-q.bid;

      if(structural_tp_r<1.0-1.0e-10)
        {
         g_d154b_candidates_infeasible_room++;
         LogLine("D154B_CANDIDATE_INFEASIBLE","M1",available_at,t.scenario_id,
                 StringFormat("scenario_id=%s reason=STRUCTURAL_TP_LT_PLUS_1R executable_entry=%.10f spread=%.10f original_r=%.8f shadow_risk=%.10f structural_tp=%.10f structural_tp_r=%.8f strategy_authority=false",
                              t.scenario_id,entry,t.spread_at_entry,entry_r_from_original,
                              shadow_risk,t.structural_tp,structural_tp_r));
         g_d154b_trackers[i]=t;
         continue;
        }

      t.candidate_armed=true;
      t.shadow_mfe_r=0.0;
      t.shadow_mae_r=0.0;
      g_d154b_candidates_armed++;

      LogLine("D154B_CANDIDATE_ARMED","M1",available_at,t.scenario_id,
              StringFormat("scenario_id=%s direction=%s confirmation_at_s=%I64d bar_close=%.10f executable_entry=%.10f spread=%.10f confirmation_r_from_original=%.8f original_sl=%.10f shadow_risk=%.10f shadow_plus1=%.10f structural_tp=%.10f structural_tp_r=%.8f entry_model=FIRST_TICK_AFTER_CAUSAL_INITIAL_BOS_CLOSE sl_model=ORIGINAL_NORMALIZED_SL target_model=PLUS_1R_FROM_SHADOW_ENTRY strategy_authority=false",
                           t.scenario_id,DirectionName(t.direction),(long)available_at,
                           bar.close,entry,t.spread_at_entry,entry_r_from_original,
                           t.original_sl,shadow_risk,t.shadow_plus1_price,
                           t.structural_tp,structural_tp_r));
      g_d154b_trackers[i]=t;
     }
  }

void D154BOnPrimaryReference(const int scenario_index,
                             const string outcome,
                             const datetime at)
  {
   if(!D154BEnabled())
      return;
   int i=D154BFindTracker(scenario_index);
   if(i<0)
      return;

   V2D154BTracker t=g_d154b_trackers[i];
   if(t.primary_reference_logged)
      return;

   t.primary_reference_logged=true;
   t.primary_outcome=outcome;
   t.primary_terminal_at=at;

   if(!t.first_initial_seen)
      g_d154b_no_initial_before_primary++;

   LogLine("D154B_PRIMARY_REFERENCE","M1",at,t.scenario_id,
           StringFormat("scenario_id=%s direction=%s primary_outcome=%s terminal_at_s=%I64d first_initial_seen=%s first_initial_relation=%s candidate_armed=%s shadow_terminal=%s strategy_authority=false",
                        t.scenario_id,DirectionName(t.direction),outcome,(long)at,
                        t.first_initial_seen ? "true" : "false",
                        !t.first_initial_seen ? "NONE" :
                           (t.first_initial_direction==t.direction ? "SAME_DIR" : "OPPOSITE_DIR"),
                        t.candidate_armed ? "true" : "false",
                        t.shadow_terminal ? "true" : "false"));
   g_d154b_trackers[i]=t;
  }

void D154BAuditOnTick(const MqlTick &tick)
  {
   if(!D154BEnabled())
      return;

   for(int i=0;i<ArraySize(g_d154b_trackers);i++)
     {
      V2D154BTracker t=g_d154b_trackers[i];
      if(!t.valid || !t.candidate_armed || t.shadow_terminal ||
         t.shadow_risk<=LiquidityTickSize())
         continue;

      double px=(t.direction>0 ? tick.bid : tick.ask);
      if(px<=0.0)
         continue;
      double r=(double)t.direction*(px-t.shadow_entry)/t.shadow_risk;

      if(r>t.shadow_mfe_r) t.shadow_mfe_r=r;
      if(r<t.shadow_mae_r) t.shadow_mae_r=r;

      if(!t.map_support_lost && D151HighestMapDirection()!=t.direction)
        {
         t.map_support_lost=true;
         t.map_support_lost_at=(datetime)tick.time;
         LogLine("D154B_MAP_SUPPORT_LOSS","M1",(datetime)tick.time,t.scenario_id,
                 StringFormat("scenario_id=%s shadow_r=%.8f highest_map_direction_now=%s candidate_remains_shadow_active=true strategy_authority=false",
                              t.scenario_id,r,DirectionName(D151HighestMapDirection())));
        }

      g_d154b_trackers[i]=t;

      // Executable-side barrier ordering. The original normalized SL remains
      // fixed; +1R is recomputed from the later executable confirmation entry.
      if(r<=-1.0+1.0e-10)
         D154BMarkShadowTerminal(i,"ORIGINAL_SL",(datetime)tick.time,r);
      else if(r>=1.0-1.0e-10)
         D154BMarkShadowTerminal(i,"PLUS_1R",(datetime)tick.time,r);
     }
  }

void D154BOnTesterStart(const datetime at)
  {
   if(!InpV2D154BConfirmationAudit)
      return;
   LogLine("D154B_RESEARCH_START","M1",at,"",
           StringFormat("enabled=%s build=2.04R0L4 population=ACTUAL_FILL_WHILE_M1_TRANSITION first_confirmation=FIRST_POST_FILL_M1_INITIAL_BOS candidate_entry=FIRST_EXECUTABLE_TICK_AFTER_CAUSAL_CONFIRMATION_CLOSE stop=ORIGINAL_NORMALIZED_SL target=PLUS_1R_FROM_SHADOW_ENTRY structural_tp_must_be_at_least_1R=true strategy_authority=false real_entry_change=false real_sl_change=false real_tp_change=false sizing_change=false em_change=false",
                        D154BEnabled() ? "true" : "false"));
  }

void D154BOnTesterEnd(const datetime at)
  {
   if(!InpV2D154BConfirmationAudit)
      return;

   if(D154BEnabled())
     {
      for(int i=0;i<ArraySize(g_d154b_trackers);i++)
        {
         V2D154BTracker t=g_d154b_trackers[i];
         if(!t.valid)
            continue;

         if(!t.primary_reference_logged)
           {
            int d151_index=D151FindTracker(t.scenario_index);
            string primary="RIGHT_CENSORED";
            if(d151_index>=0)
              {
               if(g_d151_trackers[d151_index].reached_1r) primary="PLUS_1R";
               else if(g_d151_trackers[d151_index].pre1_failure) primary="SL_FIRST";
              }
            D154BOnPrimaryReference(t.scenario_index,primary,at);
            t=g_d154b_trackers[i];
           }

         if(t.candidate_armed && !t.shadow_terminal)
            D154BMarkShadowTerminal(i,"RIGHT_CENSORED",at,0.0);
        }
     }

   LogLine("D154B_RESEARCH_STOP","M1",at,"",
           StringFormat("enabled=%s trackers=%d transition_fills=%I64d first_same=%I64d first_opposite=%I64d no_initial_before_primary=%I64d candidates_armed=%I64d candidates_infeasible_room=%I64d shadow_plus1=%I64d shadow_sl=%I64d shadow_censored=%I64d strategy_authority=false no_trade_modification=true",
                        D154BEnabled() ? "true" : "false",
                        ArraySize(g_d154b_trackers),g_d154b_transition_fills,
                        g_d154b_first_same,g_d154b_first_opposite,
                        g_d154b_no_initial_before_primary,g_d154b_candidates_armed,
                        g_d154b_candidates_infeasible_room,g_d154b_shadow_plus1,
                        g_d154b_shadow_sl,g_d154b_shadow_censored));
  }
"""

def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {n}")
    return text.replace(old,new,1)

def main() -> int:
    repo=Path.cwd()
    if not (repo/".git").exists():
        print("ERROR: run from Trading repository root.")
        return 2

    head=run("git","rev-parse","HEAD")
    if head!=EXPECTED_HEAD:
        print(f"ERROR: expected HEAD {EXPECTED_HEAD}, found {head}.")
        print("Fail-closed: D-154A research has not yet been committed by design.")
        return 2

    head_blob=run("git","rev-parse",f"HEAD:{EA_PATH.as_posix()}")
    if head_blob!=EXPECTED_BASE_EA_BLOB:
        print(f"ERROR: HEAD EA blob {head_blob}; expected {EXPECTED_BASE_EA_BLOB}.")
        return 2

    staged=run("git","diff","--cached","--name-only")
    if staged.strip():
        print("ERROR: staged changes exist. Fail-closed.")
        print(staged)
        return 2

    tracked=run("git","diff","--name-only")
    tracked_set={x.strip().replace("\\","/") for x in tracked.splitlines() if x.strip()}
    if tracked_set!={EA_PATH.as_posix()}:
        print("ERROR: expected the only tracked local modification to be the D-154A EA.")
        print("Tracked modifications:",sorted(tracked_set))
        return 2

    ea=repo/EA_PATH
    raw=ea.read_bytes()
    newline="\r\n" if b"\r\n" in raw else "\n"
    text=raw.decode("utf-8").replace("\r\n","\n")

    required_markers=[
        '#property version   "2.03"',
        'InpV2D154EntrySurvivalAudit = false;',
        'struct V2D154ATracker',
        'void D154AOnStructureEvent',
        'void D154AOnFill',
        'D154AOnTesterStart(TimeCurrent());',
        'D154AOnTesterEnd(TimeCurrent());',
    ]
    missing=[m for m in required_markers if m not in text]
    if missing:
        print("ERROR: local EA is not the expected D-154A working state.")
        for m in missing: print(" missing:",m)
        return 2
    if "D154B_" in text or "InpV2D154BConfirmationAudit" in text:
        print("ERROR: D-154B markers already exist; refusing double-apply.")
        return 2

    package_root=Path(__file__).resolve().parent
    repo_files=package_root/"repo_files"
    pending=[]
    for src in sorted(repo_files.rglob("*")):
        if not src.is_file(): continue
        rel=src.relative_to(repo_files)
        dst=repo/rel
        if dst.exists():
            print(f"ERROR: refusing to overwrite existing D-154B file: {rel}")
            return 2
        pending.append((src,rel,dst))

    # Build all changes in-memory before touching the repository.
    new=text
    new=replace_once(
        new,
        '#property version   "2.03"\n#property description "Mentor deterministic V2 EA - D154A entry survival ownership audit"',
        '#property version   "2.04"\n#property description "Mentor deterministic V2 EA - D154B post-fill confirmation shadow audit"',
        "property identity",
    )
    new=replace_once(
        new,
        'input bool   InpV2D154EntrySurvivalAudit = false;\n',
        'input bool   InpV2D154EntrySurvivalAudit = false;\n\n'
        '// D-154B shadow-only: for actual fills occurring while M1 is TRANSITION,\n'
        '// test the first post-Fill INITIAL_BOS as a delayed confirmation entry.\n'
        '// Requires D151 for exact original Fill/+1R/SL ordering; no strategy authority.\n'
        'input bool   InpV2D154BConfirmationAudit = false;\n',
        "D154B input",
    )
    new=replace_once(
        new,
        '   if(StringFind(event_name,"D154A_")==0)\n'
        '      return true;\n',
        '   if(StringFind(event_name,"D154A_")==0)\n'
        '      return true;\n'
        '   if(StringFind(event_name,"D154B_")==0)\n'
        '      return true;\n',
        "research compact whitelist",
    )
    new=replace_once(
        new,
        'void D154AConsiderSuccessorStage(const int candidate_scenario_index,\n'
        '                                 const string stage,\n'
        '                                 const datetime at);\n\n'
        'bool D151Enabled()',
        'void D154AConsiderSuccessorStage(const int candidate_scenario_index,\n'
        '                                 const string stage,\n'
        '                                 const datetime at);\n\n'
        + D154B_DECL + '\n\n'
        'bool D151Enabled()',
        "D154B declarations",
    )
    new=replace_once(
        new,
        '   D154AOnOneR(t.scenario_index,at);\n',
        '   D154AOnOneR(t.scenario_index,at);\n'
        '   D154BOnPrimaryReference(t.scenario_index,"PLUS_1R",at);\n',
        "D151 plus1 hook",
    )
    new=replace_once(
        new,
        '   D154AOnPre1Failure(t.scenario_index,at,t.map_support_same_at_sl,t.root_alive_at_sl);\n',
        '   D154AOnPre1Failure(t.scenario_index,at,t.map_support_same_at_sl,t.root_alive_at_sl);\n'
        '   D154BOnPrimaryReference(t.scenario_index,"SL_FIRST",at);\n',
        "D151 SL hook",
    )
    new=replace_once(
        new,
        '\n\nstring SmartPartialStateName(const int state)\n',
        '\n\n' + D154B_BLOCK + '\n\nstring SmartPartialStateName(const int state)\n',
        "D154B function block",
    )
    new=replace_once(
        new,
        '   D154AOnStructureEvent(s,event_type,direction,bar,available_at);\n'
        '  }\n',
        '   D154AOnStructureEvent(s,event_type,direction,bar,available_at);\n'
        '   D154BOnStructureEvent(s,event_type,direction,bar,available_at);\n'
        '  }\n',
        "M1 structure hook",
    )
    new=replace_once(
        new,
        '   D154AOnFill(scenario_index,observed_at);\n'
        '   g_positions_filled++;\n',
        '   D154AOnFill(scenario_index,observed_at);\n'
        '   D154BOnFill(scenario_index,observed_at);\n'
        '   g_positions_filled++;\n',
        "Fill hook",
    )
    new=replace_once(
        new,
        '   D154AOnTesterStart(TimeCurrent());\n'
        '   LogLine("D149_RESEARCH_START"',
        '   D154AOnTesterStart(TimeCurrent());\n'
        '   D154BOnTesterStart(TimeCurrent());\n'
        '   LogLine("D149_RESEARCH_START"',
        "tester start hook",
    )
    new=replace_once(
        new,
        '   D154AOnTesterEnd(TimeCurrent());\n'
        '   EdgeAuditDeinit(reason);\n',
        '   D154AOnTesterEnd(TimeCurrent());\n'
        '   D154BOnTesterEnd(TimeCurrent());\n'
        '   EdgeAuditDeinit(reason);\n',
        "tester end hook",
    )
    new=replace_once(
        new,
        '   D151AuditOnTick(tick);\n'
        '   EdgeAuditOnTick(tick);\n',
        '   D151AuditOnTick(tick);\n'
        '   D154BAuditOnTick(tick);\n'
        '   EdgeAuditOnTick(tick);\n',
        "tick hook",
    )

    new=new.replace("build=2.03R0L3","build=2.04R0L4")
    new=new.replace(
        "phase=V2_D154A_ENTRY_SURVIVAL_OWNERSHIP_AUDIT",
        "phase=V2_D154B_POST_FILL_CONFIRMATION_SHADOW",
    )
    new=new.replace(
        "strategy_semantics=V2_CONTINUATION_ONLY_PLUS_D151_D152_SP_RESEARCH_PLUS_D154A_SHADOW",
        "strategy_semantics=V2_CONTINUATION_ONLY_PLUS_D151_D152_SP_RESEARCH_PLUS_D154A_D154B_SHADOW",
    )

    # Fail before writing if the generated text does not contain all new invariants.
    generated_markers=[
        '#property version   "2.04"',
        'InpV2D154BConfirmationAudit = false;',
        'struct V2D154BTracker',
        'void D154BAuditOnTick',
        'D154BOnStructureEvent(s,event_type,direction,bar,available_at);',
        'D154BOnFill(scenario_index,observed_at);',
        'D154BOnTesterStart(TimeCurrent());',
        'D154BOnTesterEnd(TimeCurrent());',
    ]
    missing=[m for m in generated_markers if m not in new]
    if missing:
        raise RuntimeError("Generated D-154B text missing invariant(s): "+", ".join(missing))

    created=[]
    try:
        ea.write_bytes(new.replace("\n",newline).encode("utf-8"))
        for src,rel,dst in pending:
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            created.append(dst)

        subprocess.check_call(
            ["git","diff","--check","--",str(EA_PATH),*[str(x.relative_to(repo)) for x in created]],
            stdout=sys.stdout,stderr=sys.stderr
        )
    except Exception:
        ea.write_bytes(raw)
        for p in created:
            try: p.unlink()
            except OSError: pass
        raise

    print("D-154B local shadow package applied. No commit/push was performed.")
    print("HEAD remains:",head)
    print("Next:")
    print("  1) Compile MentorDeterministicV2EA.mq5 -> require 0 errors.")
    print("  2) Refresh Strategy Tester preset so InpV2D154BConfirmationAudit appears.")
    print("  3) python tools\\run_d154b_parity_gold_short.py")
    print("  4) python tools\\compare_d154b_parity.py <OFF.csv> <ON.csv>")
    print("  5) After PASS: python tools\\run_d154b_gold_btc_2025.py")
    print("  6) Return the generated ZIP.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
