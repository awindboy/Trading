#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

EXPECTED_HEAD = "af4643738192b68109adc5ddc192234619690a20"
EXPECTED_EA_BLOB = "42b0632df8388dc8800c6b4b6820272c6cff1208"
EA_PATH = Path("mt5/experts/MentorDeterministicV2EA.mq5")

D154C_DECL = r"""
// D-154C shadow-only reacceleration-FVG audit.
// Population: actual EXTERNAL_CONTINUATION fills observed while M1 is TRANSITION.
// After the first same-direction post-Fill INITIAL_BOS, freeze the first new
// same-direction M1 FVG whose displacement candle starts after confirmation,
// then shadow its first executable retest using the original normalized SL.
struct V2D154CTracker
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

   bool       fvg_selected;
   bool       fvg_feasible;
   string     fvg_id;
   datetime   fvg_available_at;
   datetime   fvg_candle1_open;
   datetime   fvg_candle2_open;
   datetime   fvg_candle3_open;
   double     fvg_bottom;
   double     fvg_top;
   double     fvg_width;
   long       fvg_width_ticks;
   double     planned_entry;
   double     planned_entry_r_from_original;
   double     pullback_from_confirmation_r;
   double     planned_risk;
   double     planned_plus1;
   double     structural_tp_r;

   bool       primary_reference_logged;
   string     primary_outcome;
   datetime   primary_terminal_at;
   bool       preentry_terminal;
   string     preentry_terminal_reason;

   bool       shadow_filled;
   datetime   shadow_fill_at;
   double     shadow_fill_spread;
   bool       shadow_terminal;
   string     shadow_outcome;
   datetime   shadow_terminal_at;
   double     shadow_mfe_r;
   double     shadow_mae_r;

   bool       map_support_lost;
   datetime   map_support_lost_at;
  };

V2D154CTracker g_d154c_trackers[];
long g_d154c_transition_fills=0;
long g_d154c_first_same=0;
long g_d154c_first_opposite=0;
long g_d154c_no_initial_before_primary=0;
long g_d154c_fvg_selected=0;
long g_d154c_fvg_infeasible=0;
long g_d154c_retest_fills=0;
long g_d154c_preentry_plus1=0;
long g_d154c_preentry_sl=0;
long g_d154c_preentry_censored=0;
long g_d154c_retest_ambiguous=0;
long g_d154c_shadow_plus1=0;
long g_d154c_shadow_sl=0;
long g_d154c_shadow_censored=0;

void D154COnFill(const int scenario_index,const datetime observed_at);
void D154COnStructureEvent(const V1StructureState &state,
                           const int event_type,
                           const int direction,
                           const MqlRates &bar,
                           const datetime available_at);
void D154COnM1FvgDetection(const V1M1FvgDetection &fvg,
                           const datetime available_at);
void D154COnPrimaryReference(const int scenario_index,
                             const string outcome,
                             const datetime at);
void D154CAuditOnTick(const MqlTick &tick);
void D154COnTesterStart(const datetime at);
void D154COnTesterEnd(const datetime at);
"""

D154C_BLOCK = r"""
//+------------------------------------------------------------------+
//| D-154C Post-confirmation reacceleration-FVG shadow audit         |
//| No real Entry/SL/TP/order/sizing/EM authority.                   |
//+------------------------------------------------------------------+
bool D154CEnabled()
  {
   return (InpV2D154CReaccelerationFvgAudit && InpV2D151CausalAudit);
  }

int D154CFindTracker(const int scenario_index)
  {
   for(int i=0;i<ArraySize(g_d154c_trackers);i++)
      if(g_d154c_trackers[i].valid &&
         g_d154c_trackers[i].scenario_index==scenario_index)
         return i;
   return -1;
  }

void D154COnFill(const int scenario_index,const datetime observed_at)
  {
   if(!D154CEnabled() ||
      scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION ||
      g_structure[5].trend!=V1_TREND_TRANSITION ||
      D154CFindTracker(scenario_index)>=0)
      return;

   double risk=g_scenarios[scenario_index].exit_initial_risk_price;
   if(risk<=0.0)
      risk=MathAbs(g_scenarios[scenario_index].fill_price-
                   g_scenarios[scenario_index].normalized_sl);
   if(risk<=LiquidityTickSize())
     {
      LogLine("D154C_TRACKER_SKIPPED","M1",observed_at,g_scenarios[scenario_index].id,
              "reason=INVALID_ORIGINAL_RISK strategy_authority=false");
      return;
     }

   int n=ArraySize(g_d154c_trackers);
   if(ArrayResize(g_d154c_trackers,n+1)<0)
      return;

   V2D154CTracker t;
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

   t.fvg_selected=false;
   t.fvg_feasible=false;
   t.fvg_id="";
   t.fvg_available_at=0;
   t.fvg_candle1_open=0;
   t.fvg_candle2_open=0;
   t.fvg_candle3_open=0;
   t.fvg_bottom=0.0;
   t.fvg_top=0.0;
   t.fvg_width=0.0;
   t.fvg_width_ticks=0;
   t.planned_entry=0.0;
   t.planned_entry_r_from_original=0.0;
   t.pullback_from_confirmation_r=0.0;
   t.planned_risk=0.0;
   t.planned_plus1=0.0;
   t.structural_tp_r=0.0;

   t.primary_reference_logged=false;
   t.primary_outcome="";
   t.primary_terminal_at=0;
   t.preentry_terminal=false;
   t.preentry_terminal_reason="";

   t.shadow_filled=false;
   t.shadow_fill_at=0;
   t.shadow_fill_spread=0.0;
   t.shadow_terminal=false;
   t.shadow_outcome="";
   t.shadow_terminal_at=0;
   t.shadow_mfe_r=0.0;
   t.shadow_mae_r=0.0;

   t.map_support_lost=false;
   t.map_support_lost_at=0;

   g_d154c_trackers[n]=t;
   g_d154c_transition_fills++;

   LogLine("D154C_TRANSITION_FILL","M1",observed_at,t.scenario_id,
           StringFormat("scenario_id=%s direction=%s fill_at_s=%I64d original_fill=%.10f original_sl=%.10f original_risk=%.10f structural_tp=%.10f m1_state_at_fill=%s strategy_authority=false",
                        t.scenario_id,DirectionName(t.direction),(long)t.fill_at,
                        t.original_fill,t.original_sl,t.original_risk,t.structural_tp,
                        TrendName(g_structure[5].trend)));
  }

void D154COnStructureEvent(const V1StructureState &state,
                           const int event_type,
                           const int direction,
                           const MqlRates &bar,
                           const datetime available_at)
  {
   if(!D154CEnabled() ||
      state.tf!=PERIOD_M1 ||
      event_type!=V1_EVENT_INITIAL_BOS)
      return;

   for(int i=0;i<ArraySize(g_d154c_trackers);i++)
     {
      V2D154CTracker t=g_d154c_trackers[i];
      if(!t.valid ||
         t.first_initial_seen ||
         t.primary_reference_logged ||
         available_at<=t.fill_at)
         continue;

      t.first_initial_seen=true;
      t.first_initial_direction=direction;
      t.first_initial_at=available_at;
      t.first_initial_bar_close=bar.close;

      string relation=(direction==t.direction ? "SAME_DIR" : "OPPOSITE_DIR");
      LogLine("D154C_FIRST_INITIAL_BOS","M1",available_at,t.scenario_id,
              StringFormat("scenario_id=%s direction=%s relation=%s event_direction=%s event_at_s=%I64d bar_close=%.10f confirmation_r_from_original=%.8f minutes_after_fill=%.4f next_if_same=WAIT_FIRST_POST_CONFIRMATION_FVG strategy_authority=false",
                           t.scenario_id,DirectionName(t.direction),relation,
                           DirectionName(direction),(long)available_at,bar.close,
                           (double)t.direction*(bar.close-t.original_fill)/t.original_risk,
                           (double)(available_at-t.fill_at)/60.0));

      if(direction==t.direction) g_d154c_first_same++;
      else g_d154c_first_opposite++;

      g_d154c_trackers[i]=t;
     }
  }

void D154COnM1FvgDetection(const V1M1FvgDetection &fvg,
                           const datetime available_at)
  {
   if(!D154CEnabled() || !fvg.valid)
      return;

   for(int i=0;i<ArraySize(g_d154c_trackers);i++)
     {
      V2D154CTracker t=g_d154c_trackers[i];
      if(!t.valid ||
         t.primary_reference_logged ||
         !t.first_initial_seen ||
         t.first_initial_direction!=t.direction ||
         t.fvg_selected)
         continue;

      if(fvg.direction!=t.direction ||
         available_at<=t.first_initial_at)
         continue;

      // Mechanism boundary: the FVG's displacement/middle candle must start
      // no earlier than the time at which the INITIAL_BOS became causally known.
      // Candle1 may be the confirmation bar; candle2/candle3 must be post-confirmation.
      if(fvg.candle2_open<t.first_initial_at)
         continue;

      t.fvg_selected=true;
      t.fvg_id=fvg.id;
      t.fvg_available_at=available_at;
      t.fvg_candle1_open=fvg.candle1_open;
      t.fvg_candle2_open=fvg.candle2_open;
      t.fvg_candle3_open=fvg.candle3_open;
      t.fvg_bottom=fvg.bottom;
      t.fvg_top=fvg.top;
      t.fvg_width=fvg.width;
      t.fvg_width_ticks=fvg.width_ticks;
      t.planned_entry=(t.direction>0 ? fvg.top : fvg.bottom);
      t.planned_entry_r_from_original=
         (double)t.direction*(t.planned_entry-t.original_fill)/t.original_risk;
      t.pullback_from_confirmation_r=
         (double)t.direction*(t.first_initial_bar_close-t.planned_entry)/t.original_risk;
      t.planned_risk=(double)t.direction*(t.planned_entry-t.original_sl);

      g_d154c_fvg_selected++;

      if(t.planned_risk<=LiquidityTickSize())
        {
         t.fvg_feasible=false;
         g_d154c_fvg_infeasible++;
         LogLine("D154C_FVG_INFEASIBLE","M1",available_at,t.scenario_id,
                 StringFormat("scenario_id=%s fvg_id=%s reason=NONPOSITIVE_ENTRY_TO_ORIGINAL_SL direction=%s planned_entry=%.10f original_sl=%.10f entry_r_from_original=%.8f strategy_authority=false",
                              t.scenario_id,t.fvg_id,DirectionName(t.direction),
                              t.planned_entry,t.original_sl,t.planned_entry_r_from_original));
         g_d154c_trackers[i]=t;
         continue;
        }

      double room=(double)t.direction*(t.structural_tp-t.planned_entry);
      t.structural_tp_r=room/t.planned_risk;
      t.planned_plus1=t.planned_entry+(double)t.direction*t.planned_risk;

      if(t.structural_tp_r<1.0-1.0e-10)
        {
         t.fvg_feasible=false;
         g_d154c_fvg_infeasible++;
         LogLine("D154C_FVG_INFEASIBLE","M1",available_at,t.scenario_id,
                 StringFormat("scenario_id=%s fvg_id=%s reason=STRUCTURAL_TP_LT_PLUS_1R direction=%s planned_entry=%.10f original_sl=%.10f planned_risk=%.10f structural_tp=%.10f structural_tp_r=%.8f entry_r_from_original=%.8f pullback_from_confirmation_r=%.8f strategy_authority=false",
                              t.scenario_id,t.fvg_id,DirectionName(t.direction),
                              t.planned_entry,t.original_sl,t.planned_risk,t.structural_tp,
                              t.structural_tp_r,t.planned_entry_r_from_original,
                              t.pullback_from_confirmation_r));
         g_d154c_trackers[i]=t;
         continue;
        }

      t.fvg_feasible=true;
      LogLine("D154C_FVG_SELECTED","M1",available_at,t.scenario_id,
              StringFormat("scenario_id=%s direction=%s fvg_id=%s fvg_available_at_s=%I64d candle1_open_s=%I64d candle2_open_s=%I64d candle3_open_s=%I64d bottom=%.10f top=%.10f width=%.10f width_ticks=%I64d selection=FIRST_SAME_DIR_POST_CONFIRMATION_FVG displacement_candle_post_confirmation=true planned_entry=%.10f entry_edge=%s entry_r_from_original=%.8f confirmation_bar_close=%.10f pullback_from_confirmation_r=%.8f original_sl=%.10f planned_risk=%.10f planned_plus1=%.10f structural_tp=%.10f structural_tp_r=%.8f state=WAIT_FIRST_RETEST strategy_authority=false",
                           t.scenario_id,DirectionName(t.direction),t.fvg_id,(long)t.fvg_available_at,
                           (long)t.fvg_candle1_open,(long)t.fvg_candle2_open,(long)t.fvg_candle3_open,
                           t.fvg_bottom,t.fvg_top,t.fvg_width,t.fvg_width_ticks,
                           t.planned_entry,t.direction>0 ? "FVG_TOP" : "FVG_BOTTOM",
                           t.planned_entry_r_from_original,t.first_initial_bar_close,
                           t.pullback_from_confirmation_r,t.original_sl,t.planned_risk,
                           t.planned_plus1,t.structural_tp,t.structural_tp_r));
      g_d154c_trackers[i]=t;
     }
  }

void D154COnPrimaryReference(const int scenario_index,
                             const string outcome,
                             const datetime at)
  {
   if(!D154CEnabled())
      return;
   int i=D154CFindTracker(scenario_index);
   if(i<0)
      return;

   V2D154CTracker t=g_d154c_trackers[i];
   if(t.primary_reference_logged)
      return;

   t.primary_reference_logged=true;
   t.primary_outcome=outcome;
   t.primary_terminal_at=at;

   if(!t.first_initial_seen)
      g_d154c_no_initial_before_primary++;

   if(!t.shadow_filled)
     {
      t.preentry_terminal=true;
      t.preentry_terminal_reason=outcome;
      if(outcome=="PLUS_1R") g_d154c_preentry_plus1++;
      else if(outcome=="SL_FIRST") g_d154c_preentry_sl++;
      else g_d154c_preentry_censored++;

      string stage="NO_SAME_DIR_CONFIRMATION";
      if(t.first_initial_seen && t.first_initial_direction!=t.direction)
         stage="FIRST_INITIAL_OPPOSITE";
      else if(t.first_initial_seen && !t.fvg_selected)
         stage="NO_POST_CONFIRMATION_FVG";
      else if(t.fvg_selected && !t.fvg_feasible)
         stage="FIRST_FVG_INFEASIBLE";
      else if(t.fvg_selected && t.fvg_feasible)
         stage="FVG_NO_RETEST_BEFORE_PRIMARY_TERMINAL";

      LogLine("D154C_PREENTRY_TERMINAL","M1",at,t.scenario_id,
              StringFormat("scenario_id=%s direction=%s primary_outcome=%s stage=%s first_initial_seen=%s first_initial_relation=%s fvg_selected=%s fvg_feasible=%s shadow_filled=false strategy_authority=false",
                           t.scenario_id,DirectionName(t.direction),outcome,stage,
                           t.first_initial_seen ? "true" : "false",
                           !t.first_initial_seen ? "NONE" :
                              (t.first_initial_direction==t.direction ? "SAME_DIR" : "OPPOSITE_DIR"),
                           t.fvg_selected ? "true" : "false",
                           t.fvg_feasible ? "true" : "false"));
     }
   else
     {
      LogLine("D154C_PRIMARY_REFERENCE_AFTER_SHADOW_FILL","M1",at,t.scenario_id,
              StringFormat("scenario_id=%s primary_outcome=%s shadow_fill_at_s=%I64d shadow_terminal=%s strategy_authority=false",
                           t.scenario_id,outcome,(long)t.shadow_fill_at,
                           t.shadow_terminal ? "true" : "false"));
     }

   g_d154c_trackers[i]=t;
  }

void D154CMarkShadowTerminal(const int tracker_index,
                             const string outcome,
                             const datetime at,
                             const double terminal_r)
  {
   if(tracker_index<0 || tracker_index>=ArraySize(g_d154c_trackers))
      return;

   V2D154CTracker t=g_d154c_trackers[tracker_index];
   if(!t.valid || !t.shadow_filled || t.shadow_terminal)
      return;

   t.shadow_terminal=true;
   t.shadow_outcome=outcome;
   t.shadow_terminal_at=at;
   if(terminal_r>t.shadow_mfe_r) t.shadow_mfe_r=terminal_r;
   if(terminal_r<t.shadow_mae_r) t.shadow_mae_r=terminal_r;

   if(outcome=="PLUS_1R") g_d154c_shadow_plus1++;
   else if(outcome=="ORIGINAL_SL") g_d154c_shadow_sl++;
   else if(outcome=="RIGHT_CENSORED") g_d154c_shadow_censored++;

   LogLine("D154C_SHADOW_TERMINAL","M1",at,t.scenario_id,
           StringFormat("scenario_id=%s direction=%s outcome=%s terminal_r=%.8f planned_entry=%.10f original_sl=%.10f planned_risk=%.10f planned_plus1=%.10f structural_tp=%.10f structural_tp_r=%.8f entry_r_from_original=%.8f pullback_from_confirmation_r=%.8f shadow_mfe_r=%.8f shadow_mae_r=%.8f map_support_lost=%s map_support_lost_at_s=%I64d primary_outcome=%s strategy_authority=false",
                        t.scenario_id,DirectionName(t.direction),outcome,terminal_r,
                        t.planned_entry,t.original_sl,t.planned_risk,t.planned_plus1,
                        t.structural_tp,t.structural_tp_r,t.planned_entry_r_from_original,
                        t.pullback_from_confirmation_r,t.shadow_mfe_r,t.shadow_mae_r,
                        t.map_support_lost ? "true" : "false",(long)t.map_support_lost_at,
                        t.primary_reference_logged ? t.primary_outcome : "PENDING"));
   g_d154c_trackers[tracker_index]=t;
  }

void D154CAuditOnTick(const MqlTick &tick)
  {
   if(!D154CEnabled())
      return;

   for(int i=0;i<ArraySize(g_d154c_trackers);i++)
     {
      V2D154CTracker t=g_d154c_trackers[i];
      if(!t.valid || t.shadow_terminal)
         continue;

      if(!t.shadow_filled)
        {
         if(t.preentry_terminal ||
            !t.fvg_selected ||
            !t.fvg_feasible ||
            (datetime)tick.time<t.fvg_available_at)
            continue;

         bool touched=(t.direction>0 ?
                       (tick.ask>0.0 && tick.ask<=t.planned_entry) :
                       (tick.bid>0.0 && tick.bid>=t.planned_entry));
         if(!touched)
            continue;

         // If the first executable retest tick is already through the original
         // stop on the exit side, the ordering inside the gap is unknowable.
         bool stop_same_tick=(t.direction>0 ?
                              (tick.bid>0.0 && tick.bid<=t.original_sl) :
                              (tick.ask>0.0 && tick.ask>=t.original_sl));
         if(stop_same_tick)
           {
            t.preentry_terminal=true;
            t.preentry_terminal_reason="RETEST_AND_SL_SAME_TICK_AMBIGUOUS";
            g_d154c_retest_ambiguous++;
            LogLine("D154C_RETEST_AMBIGUOUS","M1",(datetime)tick.time,t.scenario_id,
                    StringFormat("scenario_id=%s direction=%s fvg_id=%s planned_entry=%.10f original_sl=%.10f bid=%.10f ask=%.10f reason=RETEST_AND_SL_SAME_TICK_AMBIGUOUS no_outcome_imputation=true strategy_authority=false",
                                 t.scenario_id,DirectionName(t.direction),t.fvg_id,
                                 t.planned_entry,t.original_sl,tick.bid,tick.ask));
            g_d154c_trackers[i]=t;
            continue;
           }

         t.shadow_filled=true;
         t.shadow_fill_at=(datetime)tick.time;
         t.shadow_fill_spread=tick.ask-tick.bid;
         t.shadow_mfe_r=0.0;
         t.shadow_mae_r=0.0;
         g_d154c_retest_fills++;

         LogLine("D154C_RETEST_FILL","M1",(datetime)tick.time,t.scenario_id,
                 StringFormat("scenario_id=%s direction=%s fvg_id=%s fvg_available_at_s=%I64d shadow_fill_at_s=%I64d minutes_fvg_to_retest=%.4f planned_entry=%.10f executable_touch_bid=%.10f executable_touch_ask=%.10f spread=%.10f entry_model=FVG_PROXIMAL_EDGE_FIRST_EXECUTABLE_RETEST sl_model=ORIGINAL_NORMALIZED_SL target_model=PLUS_1R_FROM_FVG_EDGE structural_tp_retained=true strategy_authority=false",
                              t.scenario_id,DirectionName(t.direction),t.fvg_id,
                              (long)t.fvg_available_at,(long)t.shadow_fill_at,
                              (double)(t.shadow_fill_at-t.fvg_available_at)/60.0,
                              t.planned_entry,tick.bid,tick.ask,t.shadow_fill_spread));
         g_d154c_trackers[i]=t;
        }

      t=g_d154c_trackers[i];
      if(!t.shadow_filled || t.shadow_terminal ||
         t.planned_risk<=LiquidityTickSize())
         continue;

      double px=(t.direction>0 ? tick.bid : tick.ask);
      if(px<=0.0)
         continue;
      double r=(double)t.direction*(px-t.planned_entry)/t.planned_risk;
      if(r>t.shadow_mfe_r) t.shadow_mfe_r=r;
      if(r<t.shadow_mae_r) t.shadow_mae_r=r;

      if(!t.map_support_lost && D151HighestMapDirection()!=t.direction)
        {
         t.map_support_lost=true;
         t.map_support_lost_at=(datetime)tick.time;
         LogLine("D154C_MAP_SUPPORT_LOSS","M1",(datetime)tick.time,t.scenario_id,
                 StringFormat("scenario_id=%s shadow_r=%.8f highest_map_direction_now=%s shadow_remains_active=true strategy_authority=false",
                              t.scenario_id,r,DirectionName(D151HighestMapDirection())));
        }
      g_d154c_trackers[i]=t;

      if(r<=-1.0+1.0e-10)
         D154CMarkShadowTerminal(i,"ORIGINAL_SL",(datetime)tick.time,r);
      else if(r>=1.0-1.0e-10)
         D154CMarkShadowTerminal(i,"PLUS_1R",(datetime)tick.time,r);
     }
  }

void D154COnTesterStart(const datetime at)
  {
   if(!InpV2D154CReaccelerationFvgAudit)
      return;

   LogLine("D154C_RESEARCH_START","M1",at,"",
           StringFormat("enabled=%s build=2.05R0L5 population=ACTUAL_FILL_WHILE_M1_TRANSITION confirmation=FIRST_POST_FILL_M1_INITIAL_BOS first_same_dir_only=true source=FIRST_SAME_DIR_M1_FVG displacement_candle_start_must_be_at_or_after_confirmation=true entry=FVG_PROXIMAL_EDGE_FIRST_EXECUTABLE_RETEST stop=ORIGINAL_NORMALIZED_SL target=PLUS_1R_FROM_NEW_ENTRY structural_tp_retained=true structural_tp_must_be_at_least_1R=true primary_terminal_before_retest=NO_SHADOW_ENTRY post_sl_reentry=false second_fvg_retry=false strategy_authority=false",
                        D154CEnabled() ? "true" : "false"));
  }

void D154COnTesterEnd(const datetime at)
  {
   if(!InpV2D154CReaccelerationFvgAudit)
      return;

   if(D154CEnabled())
     {
      for(int i=0;i<ArraySize(g_d154c_trackers);i++)
        {
         V2D154CTracker t=g_d154c_trackers[i];
         if(!t.valid)
            continue;

         if(!t.primary_reference_logged)
            D154COnPrimaryReference(t.scenario_index,"RIGHT_CENSORED",at);

         t=g_d154c_trackers[i];
         if(t.shadow_filled && !t.shadow_terminal)
            D154CMarkShadowTerminal(i,"RIGHT_CENSORED",at,0.0);
        }
     }

   LogLine("D154C_RESEARCH_STOP","M1",at,"",
           StringFormat("enabled=%s trackers=%d transition_fills=%I64d first_same=%I64d first_opposite=%I64d no_initial_before_primary=%I64d fvg_selected=%I64d fvg_infeasible=%I64d retest_fills=%I64d preentry_plus1=%I64d preentry_sl=%I64d preentry_censored=%I64d retest_ambiguous=%I64d shadow_plus1=%I64d shadow_sl=%I64d shadow_censored=%I64d strategy_authority=false no_trade_modification=true",
                        D154CEnabled() ? "true" : "false",
                        ArraySize(g_d154c_trackers),g_d154c_transition_fills,
                        g_d154c_first_same,g_d154c_first_opposite,
                        g_d154c_no_initial_before_primary,g_d154c_fvg_selected,
                        g_d154c_fvg_infeasible,g_d154c_retest_fills,
                        g_d154c_preentry_plus1,g_d154c_preentry_sl,
                        g_d154c_preentry_censored,g_d154c_retest_ambiguous,
                        g_d154c_shadow_plus1,g_d154c_shadow_sl,
                        g_d154c_shadow_censored));
  }
"""

def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()

def regex_once(text: str, pattern: str, repl, label: str, flags: int = 0) -> str:
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise RuntimeError(f"{label}: expected one regex match, found {n}")
    return new

def text_once(text: str, old: str, new: str, label: str) -> str:
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f"{label}: expected one text match, found {n}")
    return text.replace(old,new,1)

def transform_source(text: str) -> str:
    if "InpV2D154CReaccelerationFvgAudit" in text or "D154C_" in text:
        raise RuntimeError("D-154C markers already exist; refusing double-apply.")

    new=text

    new=regex_once(
        new,
        r'#property version\s+"2\.04"\s*\n#property description\s+"Mentor deterministic V2 EA - D154B post-fill confirmation shadow audit"',
        '#property version   "2.05"\n#property description "Mentor deterministic V2 EA - D154C reacceleration FVG shadow audit"',
        "property identity",
    )

    new=regex_once(
        new,
        r'(input bool\s+InpV2D154BConfirmationAudit\s*=\s*false;\s*\n)',
        r'\1\n// D-154C shadow-only: after same-direction M1 owner completion, freeze the\n'
        r'// first new same-direction M1 FVG and shadow its first retest.\n'
        r'// Original normalized SL and structural TP remain frozen; no strategy authority.\n'
        r'input bool   InpV2D154CReaccelerationFvgAudit = false;\n',
        "D154C input",
    )

    new=regex_once(
        new,
        r'(if\s*\(StringFind\(event_name,"D154B_"\)==0\)\s*\n\s*return true;)',
        r'\1\n   if(StringFind(event_name,"D154C_")==0)\n      return true;',
        "research compact whitelist",
    )

    new=regex_once(
        new,
        r'(^bool D151Enabled\(\)\s*\n)',
        D154C_DECL + '\n\n' + r'\1',
        "D154C declarations",
        flags=re.MULTILINE,
    )

    # Exact D151 primary barrier hooks; D154C must observe the same causal terminal.
    new=text_once(
        new,
        '   D154BOnPrimaryReference(t.scenario_index,"PLUS_1R",at);\n',
        '   D154BOnPrimaryReference(t.scenario_index,"PLUS_1R",at);\n'
        '   D154COnPrimaryReference(t.scenario_index,"PLUS_1R",at);\n',
        "D151 +1R hook",
    )
    new=text_once(
        new,
        '   D154BOnPrimaryReference(t.scenario_index,"SL_FIRST",at);\n',
        '   D154BOnPrimaryReference(t.scenario_index,"SL_FIRST",at);\n'
        '   D154COnPrimaryReference(t.scenario_index,"SL_FIRST",at);\n',
        "D151 SL hook",
    )

    new=regex_once(
        new,
        r'(^string SmartPartialStateName\(const int state\)\s*\n)',
        D154C_BLOCK + '\n\n' + r'\1',
        "D154C function block",
        flags=re.MULTILINE,
    )

    new=text_once(
        new,
        '   D154BOnStructureEvent(s,event_type,direction,bar,available_at);\n',
        '   D154BOnStructureEvent(s,event_type,direction,bar,available_at);\n'
        '   D154COnStructureEvent(s,event_type,direction,bar,available_at);\n',
        "M1 structure hook",
    )

    new=text_once(
        new,
        '   g_m1_fvg_detector_events++;\n',
        '   g_m1_fvg_detector_events++;\n'
        '   D154COnM1FvgDetection(g_m1_fvg_detections[n],available_at);\n',
        "generic M1 FVG detector hook",
    )

    new=text_once(
        new,
        '   D154BOnFill(scenario_index,observed_at);\n',
        '   D154BOnFill(scenario_index,observed_at);\n'
        '   D154COnFill(scenario_index,observed_at);\n',
        "Fill hook",
    )

    new=text_once(
        new,
        '   D154BOnTesterStart(TimeCurrent());\n',
        '   D154BOnTesterStart(TimeCurrent());\n'
        '   D154COnTesterStart(TimeCurrent());\n',
        "tester start hook",
    )

    new=text_once(
        new,
        '   D154BOnTesterEnd(TimeCurrent());\n',
        '   D154BOnTesterEnd(TimeCurrent());\n'
        '   D154COnTesterEnd(TimeCurrent());\n',
        "tester end hook",
    )

    new=text_once(
        new,
        '   D154BAuditOnTick(tick);\n',
        '   D154BAuditOnTick(tick);\n'
        '   D154CAuditOnTick(tick);\n',
        "tick hook",
    )

    # Research identity only; no strategy semantics.
    new=new.replace("build=2.04R0L4","build=2.05R0L5")
    new=new.replace("property_version=2.02","property_version=2.05")
    new=new.replace(
        "phase=V2_D154B_POST_FILL_CONFIRMATION_SHADOW",
        "phase=V2_D154C_REACCELERATION_FVG_SHADOW",
    )
    new=new.replace(
        "strategy_semantics=V2_CONTINUATION_ONLY_PLUS_D151_D152_SP_RESEARCH_PLUS_D154A_D154B_SHADOW",
        "strategy_semantics=V2_CONTINUATION_ONLY_PLUS_D151_D152_SP_RESEARCH_PLUS_D154A_D154B_D154C_SHADOW",
    )

    required=[
        '#property version   "2.05"',
        'InpV2D154CReaccelerationFvgAudit = false;',
        'struct V2D154CTracker',
        'D154COnM1FvgDetection(g_m1_fvg_detections[n],available_at);',
        'D154COnFill(scenario_index,observed_at);',
        'D154COnTesterStart(TimeCurrent());',
        'D154COnTesterEnd(TimeCurrent());',
        'D154CAuditOnTick(tick);',
    ]
    missing=[m for m in required if m not in new]
    if missing:
        raise RuntimeError("generated source missing invariant(s): "+", ".join(missing))
    return new

def main() -> int:
    repo=Path.cwd()
    if not (repo/".git").exists():
        print("ERROR: run from the Trading repository root.")
        return 2

    head=run("git","rev-parse","HEAD")
    if head!=EXPECTED_HEAD:
        print(f"ERROR: expected HEAD {EXPECTED_HEAD}, found {head}.")
        print("Fail-closed: refresh from GitHub or request a rebased package.")
        return 2

    blob=run("git","rev-parse",f"HEAD:{EA_PATH.as_posix()}")
    if blob!=EXPECTED_EA_BLOB:
        print(f"ERROR: expected committed EA blob {EXPECTED_EA_BLOB}, found {blob}.")
        return 2

    ea_staged=run("git","diff","--cached","--name-only","--",EA_PATH.as_posix())
    if ea_staged.strip():
        print("ERROR: V2 EA has staged changes. Fail-closed.")
        print(ea_staged)
        return 2
    ea_unstaged=run("git","diff","--name-only","--",EA_PATH.as_posix())
    if ea_unstaged.strip():
        print("ERROR: V2 EA has unstaged changes. Fail-closed.")
        print(ea_unstaged)
        return 2

    package_root=Path(__file__).resolve().parent
    repo_files=package_root/"repo_files"
    pending=[]
    for src in sorted(repo_files.rglob("*")):
        if not src.is_file():
            continue
        rel=src.relative_to(repo_files)
        dst=repo/rel
        if dst.exists():
            print(f"ERROR: refusing to overwrite existing D-154C file: {rel}")
            return 2
        pending.append((src,rel,dst))

    raw=(repo/EA_PATH).read_bytes()
    newline="\r\n" if b"\r\n" in raw else "\n"
    text=raw.decode("utf-8").replace("\r\n","\n")

    # All source transformations occur in memory. Any missing/duplicate anchor
    # raises before the repository is touched.
    try:
        new=transform_source(text)
    except Exception as e:
        print("ERROR:",e)
        print("Fail-closed: no repository files changed.")
        return 2

    created=[]
    try:
        (repo/EA_PATH).write_bytes(new.replace("\n",newline).encode("utf-8"))
        for src,rel,dst in pending:
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            created.append(dst)

        subprocess.check_call(
            ["git","diff","--check","--",EA_PATH.as_posix(),
             *[str(x.relative_to(repo)) for x in created]],
            stdout=sys.stdout,stderr=sys.stderr
        )
    except Exception:
        (repo/EA_PATH).write_bytes(raw)
        for x in created:
            try: x.unlink()
            except OSError: pass
        raise

    print("D-154C local shadow package applied. No commit/push was performed.")
    print("HEAD remains:",head)
    print("Target local build: 2.05R0L5 / V2_D154C_REACCELERATION_FVG_SHADOW")
    print("Next:")
    print("  1) Compile MentorDeterministicV2EA.mq5 -> require 0 errors.")
    print("  2) Refresh Strategy Tester preset so InpV2D154CReaccelerationFvgAudit appears.")
    print("  3) python tools\\run_d154c_parity_gold_q1.py")
    print("  4) python tools\\compare_d154c_parity.py <OFF.csv> <ON.csv>")
    print("  5) Only after PASS: python tools\\run_d154c_gold_btc_2025.py")
    print("  6) Return the generated ZIP.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
