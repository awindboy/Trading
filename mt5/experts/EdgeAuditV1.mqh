//+------------------------------------------------------------------+
//| EdgeAuditV1.mqh                                                  |
//| D-148 ENTRY SURVIVAL FAILURE TAXONOMY -- shadow measurement   |
//|                                                                  |
//| STRATEGY AUTHORITY: NONE                                         |
//| This module may observe and log. It may not change a trade.      |
//+------------------------------------------------------------------+

#define V1_EDGE_AUDIT_BUILD       "1.94R1L10"
#define V1_EDGE_AUDIT_PHASE       "ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW"
#define V1_EDGE_FLUSH_BATCH       256
#define V1_EDGE_ALL_MASK          15
#define V1_EDGE_H15               900
#define V1_EDGE_H1                3600
#define V1_EDGE_H4                14400
#define V1_EDGE_H24               86400

struct V1EdgeSnapshot
  {
   bool       valid;
   string     id;
   int        stage;
   string     timeframe;
   string     scenario_id;
   int        scope;
   int        direction;
   datetime   stage_at;
   double     reference_price;
   double     favorable_abs;
   double     adverse_abs;
   double     last_close;
   datetime   last_close_at;
   int        horizon_mask;
  };

struct V1EdgeMapTracker
  {
   bool              valid;
   ENUM_TIMEFRAMES   tf;
   string            owner_id;
   int               direction;
   datetime          owner_started_at;
   datetime          last_initial_bos_at;
   datetime          last_continuation_bos_at;
   datetime          last_directional_bos_at;
   datetime          last_protected_update_at;
   string            last_protected_id;
   int               continuation_bos_count;
   int               compatible_root_event_count;
   int               compatible_root_candidate_count;
   int               plan_count;
   int               physical_contact_count;
   string            last_compatible_root_structure_event_id;
  };

struct V1EdgeRootMeta
  {
   bool              valid;
   string            root_id;
   ENUM_TIMEFRAMES   root_tf;
   int               direction;
   string            source_reason;
   datetime          created_at;
   datetime          origin_time;
   string            linked_structure_event_id;
   int               linked_event_type;

   string            h1_owner_id_at_create;
   int               h1_direction_at_create;
   datetime          h1_owner_started_at_create;
   datetime          h1_last_bos_at_create;
   datetime          h1_last_protected_update_at_create;
   datetime          h1_last_protected_break_at_create;
   int               h1_continuation_bos_count_at_create;
   int               h1_root_event_ordinal;
   int               h1_root_candidate_ordinal;
   bool              h1_direction_match;

   string            m30_owner_id_at_create;
   int               m30_direction_at_create;
   datetime          m30_owner_started_at_create;
   datetime          m30_last_bos_at_create;
   datetime          m30_last_protected_update_at_create;
   datetime          m30_last_protected_break_at_create;
   int               m30_continuation_bos_count_at_create;
   int               m30_root_event_ordinal;
   int               m30_root_candidate_ordinal;
   bool              m30_direction_match;
  };

// D-145: only FVG-selected pending scenarios and actually filled trades are
// tracked on ticks. No Root/Sweep/CHoCH/FVG virtual barrier fan-out remains.
struct V1EdgePrefillTracker
  {
   bool       valid;
   int        scenario_index;
   string     scenario_id;
   int        direction;
   datetime   fvg_at;
   double     entry_boundary;
   double     fvg_width;
   double     max_favorable_abs;
   double     max_adverse_abs;
   datetime   max_favorable_at;
   datetime   max_adverse_at;
   datetime   first_tick_at;
   long       tick_count;
  };


// D-146: compact causal M30 state used only by +1R-success continuation audit.
struct V1EdgeD146M30State
  {
   bool       valid;
   bool       protected_available;
   bool       external_available;
   bool       range_available;
   int        trend;
   int        trend_direction;
   string     owner_id;
   datetime   owner_started_at;
   string     protected_id;
   double     protected_price;
   string     external_id;
   double     external_price;
   double     range_span;
   double     range_progress;
   double     remaining_to_external_r;
  };

struct V1EdgeRunnerTracker
  {
   bool       valid;
   int        scenario_index;
   string     scenario_id;
   int        scope;
   int        direction;
   datetime   fill_at;
   double     fill_price;
   double     normalized_sl;
   double     risk_distance;
   double     target_1r;
   double     target_2r;
   double     target_3r;
   double     structural_tp;
   bool       reached_1r;
   bool       resolved_1r;
   bool       resolved_2r;
   bool       resolved_3r;
   bool       resolved_structural;
   datetime   first_1r_at;
   double     max_favorable_r;
   double     max_adverse_r;
   double     max_adverse_before_1r_r;
   long       ticks_seen;

   long       h1_same_dir_events_at_fill;
   long       h1_opposite_dir_events_at_fill;
   long       m30_same_dir_events_at_fill;
   long       m30_opposite_dir_events_at_fill;
   long       m1_same_dir_events_at_fill;
   long       m1_opposite_dir_events_at_fill;
   long       h1_same_pb_events_at_fill;
   long       h1_opposite_pb_events_at_fill;
   long       m30_same_pb_events_at_fill;
   long       m30_opposite_pb_events_at_fill;
   long       m1_same_pb_events_at_fill;
   long       m1_opposite_pb_events_at_fill;

   // D-146 shadow-only continuation-state audit. These fields have no strategy authority.
   bool       d146_eligible;
   bool       d146_active;
   bool       d146_terminal;
   string     d146_terminal_outcome;
   datetime   d146_resolved_at;
   datetime   d146_last_tick_at;
   double     d146_last_tick_price;
   double     d146_post_1r_mfe_r;
   double     d146_post_1r_mae_r;

   int        d146_one_r_m30_trend;
   string     d146_one_r_m30_owner_id;
   datetime   d146_one_r_m30_owner_started_at;
   string     d146_one_r_m30_protected_id;
   double     d146_one_r_m30_protected_price;
   string     d146_one_r_m30_external_id;
   double     d146_one_r_m30_external_price;
   bool       d146_one_r_m30_range_available;
   double     d146_one_r_m30_range_span;
   double     d146_one_r_m30_range_progress;
   double     d146_one_r_m30_remaining_to_external_r;

   bool       d146_original_external_available;
   bool       d146_original_external_at_or_beyond_at_1r;
   bool       d146_original_external_delivered_after_1r;
   datetime   d146_original_external_delivered_at;
   bool       d146_original_external_replaced_after_1r;
   datetime   d146_original_external_replaced_at;

   string     d146_last_m30_owner_id;
   int        d146_last_m30_trend;
   string     d146_last_valid_m30_protected_id;
   double     d146_last_valid_m30_protected_price;
   string     d146_last_valid_m30_external_id;
   double     d146_last_valid_m30_external_price;

   long       d146_m30_same_direction_initial_bos_count;
   long       d146_m30_same_direction_bos_count;
   long       d146_m30_opposite_direction_event_count;
   long       d146_m30_protected_break_count;
   long       d146_m30_owner_change_count;
   long       d146_m30_trend_loss_count;
   long       d146_m30_outward_external_refresh_count;
   datetime   d146_first_outward_external_refresh_at;
   datetime   d146_first_deterioration_at;


   // D-148 shadow-only Entry-survival failure taxonomy. No strategy authority.
   bool       d148_eligible;
   bool       d148_pre_sl_resolved;
   bool       d148_post_sl_active;
   bool       d148_terminal;
   string     d148_terminal_outcome;
   datetime   d148_resolved_at;
   int        d148_original_map_tf;
   string     d148_original_owner_id;
   string     d148_root_id;
   bool       d148_original_authority_alive_at_fill;
   bool       d148_frozen_owner_invalidated;
   datetime   d148_frozen_owner_invalidated_at;
   bool       d148_map_support_loss_seen;
   datetime   d148_first_map_support_loss_at;
   int        d148_first_map_support_loss_direction;
   string     d148_first_map_support_loss_tf;
   string     d148_first_map_support_loss_owner_id;
   datetime   d148_post_sl_map_support_loss_at;
   int        d148_post_sl_map_support_loss_direction;
   string     d148_post_sl_map_support_loss_tf;
   string     d148_post_sl_map_support_loss_owner_id;
   datetime   d148_root_invalidated_at;
   string     d148_root_invalidation_reason;
   datetime   d148_sl_at;
   double     d148_sl_exit_side_price;
   double     d148_pre_sl_mfe_r;
   double     d148_pre_sl_mae_r;
   bool       d148_map_support_same_at_sl;
   bool       d148_entry_recovered_after_sl;
   datetime   d148_entry_recovered_at;
   bool       d148_one_r_recovered_after_sl;
   datetime   d148_one_r_recovered_at;
   double     d148_post_sl_max_adverse_r_from_fill;
   double     d148_post_sl_max_favorable_r_from_fill;
   long       d148_h1_same_events_at_sl;
   long       d148_h1_opp_events_at_sl;
   long       d148_m30_same_events_at_sl;
   long       d148_m30_opp_events_at_sl;
   long       d148_m1_same_events_at_sl;
   long       d148_m1_opp_events_at_sl;
   long       d148_h1_same_pb_at_sl;
   long       d148_h1_opp_pb_at_sl;
   long       d148_m30_same_pb_at_sl;
   long       d148_m30_opp_pb_at_sl;
   long       d148_m1_same_pb_at_sl;
   long       d148_m1_opp_pb_at_sl;
  };


bool             g_edge_enabled=false;
long             g_edge_rows=0;
long             g_edge_rows_since_flush=0;
long             g_edge_snapshots=0;
long             g_edge_labels=0;
long             g_edge_structure_snapshots=0;
long             g_edge_root_snapshots=0;
long             g_edge_physical_contacts=0;
datetime         g_edge_last_map_sample_at=0;
datetime         g_edge_h1_last_protected_break_at=0;
datetime         g_edge_m30_last_protected_break_at=0;
V1EdgeSnapshot   g_edge_active[];
V1EdgeMapTracker g_edge_h1_tracker;
V1EdgeMapTracker g_edge_m30_tracker;
V1EdgeRootMeta   g_edge_roots[];
V1EdgePrefillTracker g_edge_prefill[];
V1EdgeRunnerTracker  g_edge_runners[];
long g_edge_runner_fill_snapshots=0;
long g_edge_runner_one_r_snapshots=0;
long g_edge_runner_outcomes=0;
long g_edge_runner_skipped=0;
long g_edge_d146_armed=0;
long g_edge_d146_structure_events=0;
long g_edge_d146_original_external_deliveries=0;
long g_edge_d146_terminals=0;
long g_edge_d146_censored=0;

long g_edge_d148_eligible=0;
long g_edge_d148_one_r_controls=0;
long g_edge_d148_sl_failures=0;
long g_edge_d148_entry_recoveries=0;
long g_edge_d148_one_r_recoveries=0;
long g_edge_d148_map_loss_terminals=0;
long g_edge_d148_frozen_owner_invalidations=0;
long g_edge_d148_root_invalidations=0;
long g_edge_d148_censored=0;
long g_edge_d148_pre_sl_censored=0;

// Event counters are observation-only. They let the +1R snapshot measure how
// structure changed after Fill without turning any event into trade authority.
long g_edge_h1_dir_events[2];
long g_edge_m30_dir_events[2];
long g_edge_m1_dir_events[2];
long g_edge_h1_pb_events[2];
long g_edge_m30_pb_events[2];
long g_edge_m1_pb_events[2];

string EdgeAuditStageName(const int stage)
  {
   if(stage==V1_EDGE_STAGE_MAP)                        return "MAP";
   if(stage==V1_EDGE_STAGE_PLAN)                       return "PLAN";
   if(stage==V1_EDGE_STAGE_ROOT_CONTACT)               return "ROOT_CONTACT";
   if(stage==V1_EDGE_STAGE_SWEEP)                      return "SWEEP";
   if(stage==V1_EDGE_STAGE_CHOCH)                      return "CHOCH";
   if(stage==V1_EDGE_STAGE_FVG)                        return "FVG";
   if(stage==V1_EDGE_STAGE_FILL)                       return "ACTUAL_FILL";
   if(stage==V1_EDGE_STAGE_STRUCTURE_INITIAL_BOS)      return "STRUCTURE_INITIAL_BOS";
   if(stage==V1_EDGE_STAGE_STRUCTURE_BOS)              return "STRUCTURE_BOS";
   if(stage==V1_EDGE_STAGE_STRUCTURE_PROTECTED_BREAK)  return "STRUCTURE_PROTECTED_BREAK";
   if(stage==V1_EDGE_STAGE_ROOT_CREATED)               return "ROOT_CREATED";
   if(stage==V1_EDGE_STAGE_PHYSICAL_ROOT_CONTACT)      return "PHYSICAL_ROOT_CONTACT";
   return "UNKNOWN";
  }

string EdgeAuditPopulationName(const V1EdgeSnapshot &s)
  {
   if(s.scope!=V1_SCOPE_NONE)
      return ScenarioScopeName(s.scope);
   if(s.stage==V1_EDGE_STAGE_MAP)
      return "MAP_STATE";
   if(s.stage==V1_EDGE_STAGE_STRUCTURE_INITIAL_BOS ||
      s.stage==V1_EDGE_STAGE_STRUCTURE_BOS ||
      s.stage==V1_EDGE_STAGE_STRUCTURE_PROTECTED_BREAK)
      return "STRUCTURE_EVENT";
   if(s.stage==V1_EDGE_STAGE_ROOT_CREATED)
      return "ROOT_POPULATION";
   if(s.stage==V1_EDGE_STAGE_PHYSICAL_ROOT_CONTACT)
      return "PHYSICAL_ROOT_CONTACT_POPULATION";
   return "SHADOW_STATE";
  }

int EdgeAuditHorizonSeconds(const int bit)
  {
   if(bit==1) return V1_EDGE_H15;
   if(bit==2) return V1_EDGE_H1;
   if(bit==4) return V1_EDGE_H4;
   if(bit==8) return V1_EDGE_H24;
   return 0;
  }

string EdgeAuditHorizonName(const int bit)
  {
   if(bit==1) return "15M";
   if(bit==2) return "1H";
   if(bit==4) return "4H";
   if(bit==8) return "24H";
   return "UNKNOWN";
  }

string EdgeAuditTimeOrNA(const datetime value)
  {
   if(value<=0)
      return "NA";
   return TimeToString(value,TIME_DATE|TIME_SECONDS);
  }

long EdgeAuditAgeSeconds(const datetime now,const datetime then)
  {
   if(now<=0 || then<=0 || now<then)
      return -1;
   return (long)(now-then);
  }

int EdgeAuditStructureIndex(const ENUM_TIMEFRAMES tf)
  {
   if(tf==PERIOD_H1) return 1;
   if(tf==PERIOD_M30) return 2;
   return -1;
  }

void EdgeAuditClearMapTracker(V1EdgeMapTracker &tracker,const ENUM_TIMEFRAMES tf)
  {
   tracker.valid=false;
   tracker.tf=tf;
   tracker.owner_id="";
   tracker.direction=0;
   tracker.owner_started_at=0;
   tracker.last_initial_bos_at=0;
   tracker.last_continuation_bos_at=0;
   tracker.last_directional_bos_at=0;
   tracker.last_protected_update_at=0;
   tracker.last_protected_id="";
   tracker.continuation_bos_count=0;
   tracker.compatible_root_event_count=0;
   tracker.compatible_root_candidate_count=0;
   tracker.plan_count=0;
   tracker.physical_contact_count=0;
   tracker.last_compatible_root_structure_event_id="";
  }

bool EdgeAuditGetMapTracker(const ENUM_TIMEFRAMES tf,V1EdgeMapTracker &tracker)
  {
   if(tf==PERIOD_H1)
     {
      tracker=g_edge_h1_tracker;
      return tracker.valid;
     }
   if(tf==PERIOD_M30)
     {
      tracker=g_edge_m30_tracker;
      return tracker.valid;
     }
   EdgeAuditClearMapTracker(tracker,tf);
   return false;
  }

void EdgeAuditSetMapTracker(const ENUM_TIMEFRAMES tf,const V1EdgeMapTracker &tracker)
  {
   if(tf==PERIOD_H1)
      g_edge_h1_tracker=tracker;
   else if(tf==PERIOD_M30)
      g_edge_m30_tracker=tracker;
  }

datetime EdgeAuditLastProtectedBreakAt(const ENUM_TIMEFRAMES tf)
  {
   if(tf==PERIOD_H1)
      return g_edge_h1_last_protected_break_at;
   if(tf==PERIOD_M30)
      return g_edge_m30_last_protected_break_at;
   return 0;
  }

ENUM_TIMEFRAMES EdgeAuditHighestMapTf()
  {
   string name=HighestActiveMapName();
   if(name=="H1") return PERIOD_H1;
   if(name=="M30") return PERIOD_M30;
   return PERIOD_CURRENT;
  }

string EdgeAuditMapContextDetail(const ENUM_TIMEFRAMES tf,const datetime at,const string prefix)
  {
   int index=EdgeAuditStructureIndex(tf);
   V1EdgeMapTracker tracker;
   bool have=EdgeAuditGetMapTracker(tf,tracker);
   datetime last_pb=EdgeAuditLastProtectedBreakAt(tf);

   string trend=(index>=0 ? TrendName(g_structure[index].trend) : "NA");
   string owner=(index>=0 && g_structure[index].owner_id!="" ? g_structure[index].owner_id : "NA");
   string protected_id="NA";
   string protected_price="NA";
   string external_id="NA";
   string external_price="NA";
   if(index>=0)
     {
      if(g_structure[index].trend==V1_TREND_BULLISH)
        {
         if(g_structure[index].protected_low.valid)
           {
            protected_id=g_structure[index].protected_low.id;
            protected_price=DoubleToString(g_structure[index].protected_low.price,_Digits);
           }
         if(g_structure[index].external_high.valid)
           {
            external_id=g_structure[index].external_high.id;
            external_price=DoubleToString(g_structure[index].external_high.price,_Digits);
           }
        }
      else if(g_structure[index].trend==V1_TREND_BEARISH)
        {
         if(g_structure[index].protected_high.valid)
           {
            protected_id=g_structure[index].protected_high.id;
            protected_price=DoubleToString(g_structure[index].protected_high.price,_Digits);
           }
         if(g_structure[index].external_low.valid)
           {
            external_id=g_structure[index].external_low.id;
            external_price=DoubleToString(g_structure[index].external_low.price,_Digits);
           }
        }
     }

   if(!have)
      return StringFormat(
         "%s_tf=%s %s_trend=%s %s_owner_id=%s %s_tracker_available=false %s_last_protected_break_at=%s %s_last_protected_break_age_seconds=%I64d %s_protected_id=%s %s_protected_price=%s %s_external_id=%s %s_external_price=%s",
         prefix,TfName(tf),prefix,trend,prefix,owner,prefix,
         prefix,EdgeAuditTimeOrNA(last_pb),prefix,EdgeAuditAgeSeconds(at,last_pb),
         prefix,protected_id,prefix,protected_price,prefix,external_id,prefix,external_price);

   string timing=StringFormat(
      "%s_tf=%s %s_trend=%s %s_owner_id=%s %s_tracker_available=true %s_owner_direction=%s %s_owner_started_at=%s %s_owner_age_seconds=%I64d %s_last_initial_bos_at=%s %s_last_initial_bos_age_seconds=%I64d %s_last_continuation_bos_at=%s %s_last_continuation_bos_age_seconds=%I64d %s_last_directional_bos_at=%s %s_last_directional_bos_age_seconds=%I64d %s_last_protected_update_at=%s %s_last_protected_update_age_seconds=%I64d %s_last_protected_break_at=%s %s_last_protected_break_age_seconds=%I64d",
      prefix,TfName(tf),prefix,trend,prefix,owner,prefix,
      prefix,DirectionName(tracker.direction),
      prefix,EdgeAuditTimeOrNA(tracker.owner_started_at),prefix,EdgeAuditAgeSeconds(at,tracker.owner_started_at),
      prefix,EdgeAuditTimeOrNA(tracker.last_initial_bos_at),prefix,EdgeAuditAgeSeconds(at,tracker.last_initial_bos_at),
      prefix,EdgeAuditTimeOrNA(tracker.last_continuation_bos_at),prefix,EdgeAuditAgeSeconds(at,tracker.last_continuation_bos_at),
      prefix,EdgeAuditTimeOrNA(tracker.last_directional_bos_at),prefix,EdgeAuditAgeSeconds(at,tracker.last_directional_bos_at),
      prefix,EdgeAuditTimeOrNA(tracker.last_protected_update_at),prefix,EdgeAuditAgeSeconds(at,tracker.last_protected_update_at),
      prefix,EdgeAuditTimeOrNA(last_pb),prefix,EdgeAuditAgeSeconds(at,last_pb));
   string counts=StringFormat(
      "%s_continuation_bos_count=%d %s_compatible_root_event_count=%d %s_compatible_root_candidate_count=%d %s_plan_count=%d %s_physical_contact_count=%d %s_protected_id=%s %s_protected_price=%s %s_external_id=%s %s_external_price=%s",
      prefix,tracker.continuation_bos_count,prefix,tracker.compatible_root_event_count,
      prefix,tracker.compatible_root_candidate_count,prefix,tracker.plan_count,prefix,tracker.physical_contact_count,
      prefix,protected_id,prefix,protected_price,prefix,external_id,prefix,external_price);
   return timing+" "+counts;
  }

void EdgeAuditWrite(const string event_name,
                    const string timeframe,
                    const datetime available_at,
                    const string object_id,
                    const string detail)
  {
   if(!g_edge_enabled || !InpWriteEventCsv || g_log_handle==INVALID_HANDLE)
      return;

   FileWrite(g_log_handle,
             TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),
             event_name,
             timeframe,
             TimeToString(available_at,TIME_DATE|TIME_SECONDS),
             object_id,
             detail);

   // Keep the baseline logger's row counters independent so audit OFF/ON can
   // be parity-compared after filtering EDGE_AUDIT_* rows.
   g_edge_rows++;
   g_edge_rows_since_flush++;
   if(g_edge_rows_since_flush>=V1_EDGE_FLUSH_BATCH ||
      event_name=="EDGE_AUDIT_START" ||
      event_name=="EDGE_AUDIT_STOP")
     {
      FileFlush(g_log_handle);
      g_edge_rows_since_flush=0;
     }
  }

void EdgeAuditWriteSnapshotRow(const V1EdgeSnapshot &s,const string detail)
  {
   EdgeAuditWrite("EDGE_AUDIT_SNAPSHOT",s.timeframe,s.stage_at,s.id,
      StringFormat("stage=%s stage_at=%s snapshot_id=%s scenario_id=%s population=%s direction=%s reference_price=%.10f symbol=%s %s",
                   EdgeAuditStageName(s.stage),EdgeAuditTimeOrNA(s.stage_at),s.id,
                   s.scenario_id=="" ? "NA" : s.scenario_id,
                   EdgeAuditPopulationName(s),DirectionName(s.direction),s.reference_price,_Symbol,detail));
  }


int EdgeAuditDirectionSlot(const int direction)
  {
   return (direction>0 ? 0 : 1);
  }

long EdgeAuditDirCounter(const ENUM_TIMEFRAMES tf,const int direction)
  {
   int slot=EdgeAuditDirectionSlot(direction);
   if(tf==PERIOD_H1) return g_edge_h1_dir_events[slot];
   if(tf==PERIOD_M30) return g_edge_m30_dir_events[slot];
   if(tf==PERIOD_M1) return g_edge_m1_dir_events[slot];
   return 0;
  }

long EdgeAuditPbCounter(const ENUM_TIMEFRAMES tf,const int direction)
  {
   int slot=EdgeAuditDirectionSlot(direction);
   if(tf==PERIOD_H1) return g_edge_h1_pb_events[slot];
   if(tf==PERIOD_M30) return g_edge_m30_pb_events[slot];
   if(tf==PERIOD_M1) return g_edge_m1_pb_events[slot];
   return 0;
  }

void EdgeAuditCountStructureEvent(const ENUM_TIMEFRAMES tf,const int event_type,const int direction)
  {
   if(direction==0)
      return;
   int slot=EdgeAuditDirectionSlot(direction);
   if(event_type==V1_EVENT_INITIAL_BOS || event_type==V1_EVENT_BOS)
     {
      if(tf==PERIOD_H1) g_edge_h1_dir_events[slot]++;
      else if(tf==PERIOD_M30) g_edge_m30_dir_events[slot]++;
      else if(tf==PERIOD_M1) g_edge_m1_dir_events[slot]++;
     }
   else if(event_type==V1_EVENT_PROTECTED_BREAK)
     {
      if(tf==PERIOD_H1) g_edge_h1_pb_events[slot]++;
      else if(tf==PERIOD_M30) g_edge_m30_pb_events[slot]++;
      else if(tf==PERIOD_M1) g_edge_m1_pb_events[slot]++;
     }
  }

void EdgeAuditRemovePrefillAt(const int index)
  {
   int n=ArraySize(g_edge_prefill);
   if(index<0 || index>=n) return;
   if(index<n-1) g_edge_prefill[index]=g_edge_prefill[n-1];
   ArrayResize(g_edge_prefill,n-1);
  }

int EdgeAuditFindPrefill(const string scenario_id)
  {
   for(int i=ArraySize(g_edge_prefill)-1;i>=0;i--)
      if(g_edge_prefill[i].valid && g_edge_prefill[i].scenario_id==scenario_id)
         return i;
   return -1;
  }

void EdgeAuditRemoveRunnerAt(const int index)
  {
   int n=ArraySize(g_edge_runners);
   if(index<0 || index>=n) return;
   if(index<n-1) g_edge_runners[index]=g_edge_runners[n-1];
   ArrayResize(g_edge_runners,n-1);
  }

string EdgeAuditCurrentMapIdentity(const datetime at,const int scenario_direction)
  {
   ENUM_TIMEFRAMES tf=EdgeAuditHighestMapTf();
   int current_direction=HighestActiveMapDirection();
   string owner="NA";
   if(tf==PERIOD_H1) owner=g_structure[1].owner_id=="" ? "NA" : g_structure[1].owner_id;
   else if(tf==PERIOD_M30) owner=g_structure[2].owner_id=="" ? "NA" : g_structure[2].owner_id;
   return StringFormat("current_highest_map_tf=%s current_highest_map_direction=%s current_highest_map_owner_id=%s current_map_direction_matches_scenario=%s",
                       tf==PERIOD_CURRENT ? "NONE" : TfName(tf),DirectionName(current_direction),owner,
                       current_direction==scenario_direction ? "true" : "false");
  }

string EdgeAuditRangeContext(const ENUM_TIMEFRAMES tf,
                             const int direction,
                             const double price,
                             const double risk,
                             const string prefix)
  {
   int index=EdgeAuditStructureIndex(tf);
   if(index<0 || direction==0 || price<=0.0 || risk<=0.0)
      return StringFormat("%s_available=false",prefix);

   double protected_price=0.0;
   double external_price=0.0;
   bool compatible=false;
   if(direction>0 && g_structure[index].trend==V1_TREND_BULLISH &&
      g_structure[index].protected_low.valid && g_structure[index].external_high.valid)
     {
      protected_price=g_structure[index].protected_low.price;
      external_price=g_structure[index].external_high.price;
      compatible=true;
     }
   else if(direction<0 && g_structure[index].trend==V1_TREND_BEARISH &&
           g_structure[index].protected_high.valid && g_structure[index].external_low.valid)
     {
      protected_price=g_structure[index].protected_high.price;
      external_price=g_structure[index].external_low.price;
      compatible=true;
     }

   double span=MathAbs(external_price-protected_price);
   if(!compatible || span<=MathMax(LiquidityTickSize(),1.0e-12))
      return StringFormat("%s_available=false %s_trend=%s",prefix,prefix,TrendName(g_structure[index].trend));

   double progress=(direction>0 ? (price-protected_price)/span : (protected_price-price)/span);
   double from_protected_r=(direction>0 ? price-protected_price : protected_price-price)/risk;
   double remaining_external_r=(direction>0 ? external_price-price : price-external_price)/risk;
   return StringFormat("%s_available=true %s_trend=%s %s_protected_price=%.10f %s_external_price=%.10f %s_range_span=%.10f %s_progress=%.10f %s_from_protected_r=%.10f %s_remaining_to_external_r=%.10f",
                       prefix,prefix,TrendName(g_structure[index].trend),prefix,protected_price,prefix,external_price,
                       prefix,span,prefix,progress,prefix,from_protected_r,prefix,remaining_external_r);
  }

string EdgeAuditM30WaveContext(const int direction,const datetime at,const string prefix)
  {
   int n=ArraySize(g_regime_m30_waves);
   if(n<=0 || direction==0)
      return StringFormat("%s_available=false %s_wave_count=%d",prefix,prefix,n);

   int first=-1,last=-1;
   int valid_count=0;
   double leg_sum=0.0;
   int leg_count=0;
   bool have_high=false,have_low=false;
   double last_high=0.0,last_low=0.0;
   int progression_success=0,progression_total=0;

   for(int i=0;i<n;i++)
     {
      if(!g_regime_m30_waves[i].valid || !g_regime_m30_waves[i].is_wave ||
         g_regime_m30_waves[i].available_at>at)
         continue;
      if(first<0) first=i;
      if(last>=0)
        {
         leg_sum+=MathAbs(g_regime_m30_waves[i].price-g_regime_m30_waves[last].price);
         leg_count++;
        }
      last=i;
      valid_count++;

      if(g_regime_m30_waves[i].side==V1_SIDE_HIGH)
        {
         if(have_high)
           {
            progression_total++;
            if((direction>0 && g_regime_m30_waves[i].price>last_high) ||
               (direction<0 && g_regime_m30_waves[i].price<last_high)) progression_success++;
           }
         last_high=g_regime_m30_waves[i].price;
         have_high=true;
        }
      else if(g_regime_m30_waves[i].side==V1_SIDE_LOW)
        {
         if(have_low)
           {
            progression_total++;
            if((direction>0 && g_regime_m30_waves[i].price>last_low) ||
               (direction<0 && g_regime_m30_waves[i].price<last_low)) progression_success++;
           }
         last_low=g_regime_m30_waves[i].price;
         have_low=true;
        }
     }

   if(first<0 || last<0)
      return StringFormat("%s_available=false %s_wave_count=0",prefix,prefix);

   double mean_leg=(leg_count>0 ? leg_sum/(double)leg_count : 0.0);
   double net_advance=(direction>0 ? g_regime_m30_waves[last].price-g_regime_m30_waves[first].price :
                                      g_regime_m30_waves[first].price-g_regime_m30_waves[last].price);
   double net_advance_norm=(mean_leg>0.0 ? net_advance/mean_leg : 0.0);
   double progression=(progression_total>0 ? (double)progression_success/(double)progression_total : 0.0);

   int pb_count=0;
   datetime span_start=g_regime_m30_waves[first].available_at;
   for(int i=0;i<ArraySize(g_regime_m30_protected_breaks);i++)
      if(g_regime_m30_protected_breaks[i]>=span_start && g_regime_m30_protected_breaks[i]<=at)
         pb_count++;

   double recent_mean=0.0,prior_mean=0.0,expansion=0.0;
   if(valid_count>=V1_REGIME_WAVE_COUNT && n>=V1_REGIME_WAVE_COUNT)
     {
      double recent_sum=0.0,prior_sum=0.0;
      int recent_start=n-V1_REGIME_LEG_GROUP;
      int prior_start=recent_start-V1_REGIME_LEG_GROUP;
      if(prior_start>=1)
        {
         for(int i=recent_start;i<n;i++) recent_sum+=MathAbs(g_regime_m30_waves[i].price-g_regime_m30_waves[i-1].price);
         for(int i=prior_start;i<recent_start;i++) prior_sum+=MathAbs(g_regime_m30_waves[i].price-g_regime_m30_waves[i-1].price);
         recent_mean=recent_sum/(double)V1_REGIME_LEG_GROUP;
         prior_mean=prior_sum/(double)V1_REGIME_LEG_GROUP;
         if(prior_mean>0.0) expansion=recent_mean/prior_mean;
        }
     }

   return StringFormat("%s_available=true %s_wave_count=%d %s_progression_success=%d %s_progression_total=%d %s_progression=%.10f %s_mean_leg=%.10f %s_net_directional_advance=%.10f %s_net_directional_advance_norm=%.10f %s_protected_break_count=%d %s_recent4_leg_mean=%.10f %s_prior4_leg_mean=%.10f %s_leg_expansion_ratio=%.10f",
                       prefix,prefix,valid_count,prefix,progression_success,prefix,progression_total,prefix,progression,
                       prefix,mean_leg,prefix,net_advance,prefix,net_advance_norm,prefix,pb_count,
                       prefix,recent_mean,prefix,prior_mean,prefix,expansion);
  }

string EdgeAuditM1Context(const int direction,const string prefix)
  {
   int trend_direction=TrendDirection(g_structure[5].trend);
   string protected_id="NA",external_id="NA";
   double protected_price=0.0,external_price=0.0;
   if(direction>0)
     {
      if(g_structure[5].protected_low.valid) { protected_id=g_structure[5].protected_low.id; protected_price=g_structure[5].protected_low.price; }
      if(g_structure[5].external_high.valid) { external_id=g_structure[5].external_high.id; external_price=g_structure[5].external_high.price; }
     }
   else
     {
      if(g_structure[5].protected_high.valid) { protected_id=g_structure[5].protected_high.id; protected_price=g_structure[5].protected_high.price; }
      if(g_structure[5].external_low.valid) { external_id=g_structure[5].external_low.id; external_price=g_structure[5].external_low.price; }
     }
   return StringFormat("%s_trend=%s %s_trend_direction=%s %s_direction_matches=%s %s_protected_id=%s %s_protected_price=%.10f %s_external_id=%s %s_external_price=%.10f",
                       prefix,TrendName(g_structure[5].trend),prefix,DirectionName(trend_direction),prefix,
                       trend_direction==direction ? "true" : "false",prefix,protected_id,prefix,protected_price,
                       prefix,external_id,prefix,external_price);
  }


//+------------------------------------------------------------------+
//| D-146 continuation-state audit helpers                           |
//+------------------------------------------------------------------+
void EdgeAuditD146ReadM30State(const V1StructureState &state,
                               const int direction,
                               const double price,
                               const double risk,
                               V1EdgeD146M30State &s)
  {
   s.valid=(state.tf==PERIOD_M30);
   s.protected_available=false;
   s.external_available=false;
   s.range_available=false;
   s.trend=state.trend;
   s.trend_direction=TrendDirection(state.trend);
   s.owner_id=state.owner_id;
   s.owner_started_at=state.owner_started_at;
   s.protected_id="";
   s.protected_price=0.0;
   s.external_id="";
   s.external_price=0.0;
   s.range_span=0.0;
   s.range_progress=0.0;
   s.remaining_to_external_r=0.0;

   if(direction>0)
     {
      if(state.protected_low.valid)
        {
         s.protected_available=true;
         s.protected_id=state.protected_low.id;
         s.protected_price=state.protected_low.price;
        }
      if(state.external_high.valid)
        {
         s.external_available=true;
         s.external_id=state.external_high.id;
         s.external_price=state.external_high.price;
        }
     }
   else if(direction<0)
     {
      if(state.protected_high.valid)
        {
         s.protected_available=true;
         s.protected_id=state.protected_high.id;
         s.protected_price=state.protected_high.price;
        }
      if(state.external_low.valid)
        {
         s.external_available=true;
         s.external_id=state.external_low.id;
         s.external_price=state.external_low.price;
        }
     }

   if(!s.valid || direction==0 || !s.protected_available || !s.external_available || price<=0.0)
      return;

   double span=MathAbs(s.external_price-s.protected_price);
   if(s.trend_direction!=direction || span<=MathMax(LiquidityTickSize(),1.0e-12))
      return;

   s.range_available=true;
   s.range_span=span;
   s.range_progress=(direction>0 ? (price-s.protected_price)/span : (s.protected_price-price)/span);
   if(risk>0.0)
      s.remaining_to_external_r=(direction>0 ? s.external_price-price : price-s.external_price)/risk;
  }

string EdgeAuditD146M30StateDetail(const V1EdgeD146M30State &s,const string prefix)
  {
   return StringFormat("%s_valid=%s %s_trend=%s %s_trend_direction=%s %s_owner_id=%s %s_owner_started_at=%s %s_protected_available=%s %s_protected_id=%s %s_protected_price=%.10f %s_external_available=%s %s_external_id=%s %s_external_price=%.10f %s_range_available=%s %s_range_span=%.10f %s_range_progress=%.10f %s_remaining_to_external_r=%.10f",
      prefix,s.valid ? "true" : "false",
      prefix,TrendName(s.trend),
      prefix,DirectionName(s.trend_direction),
      prefix,s.owner_id=="" ? "NA" : s.owner_id,
      prefix,EdgeAuditTimeOrNA(s.owner_started_at),
      prefix,s.protected_available ? "true" : "false",
      prefix,s.protected_id=="" ? "NA" : s.protected_id,
      prefix,s.protected_price,
      prefix,s.external_available ? "true" : "false",
      prefix,s.external_id=="" ? "NA" : s.external_id,
      prefix,s.external_price,
      prefix,s.range_available ? "true" : "false",
      prefix,s.range_span,
      prefix,s.range_progress,
      prefix,s.remaining_to_external_r);
  }

void EdgeAuditD146ResetRunner(V1EdgeRunnerTracker &r)
  {
   r.d146_eligible=(r.scope==V1_SCOPE_EXTERNAL_CONTINUATION);
   r.d146_active=false;
   r.d146_terminal=false;
   r.d146_terminal_outcome="";
   r.d146_resolved_at=0;
   r.d146_last_tick_at=0;
   r.d146_last_tick_price=0.0;
   r.d146_post_1r_mfe_r=0.0;
   r.d146_post_1r_mae_r=0.0;

   r.d146_one_r_m30_trend=V1_TREND_NEUTRAL;
   r.d146_one_r_m30_owner_id="";
   r.d146_one_r_m30_owner_started_at=0;
   r.d146_one_r_m30_protected_id="";
   r.d146_one_r_m30_protected_price=0.0;
   r.d146_one_r_m30_external_id="";
   r.d146_one_r_m30_external_price=0.0;
   r.d146_one_r_m30_range_available=false;
   r.d146_one_r_m30_range_span=0.0;
   r.d146_one_r_m30_range_progress=0.0;
   r.d146_one_r_m30_remaining_to_external_r=0.0;

   r.d146_original_external_available=false;
   r.d146_original_external_at_or_beyond_at_1r=false;
   r.d146_original_external_delivered_after_1r=false;
   r.d146_original_external_delivered_at=0;
   r.d146_original_external_replaced_after_1r=false;
   r.d146_original_external_replaced_at=0;

   r.d146_last_m30_owner_id="";
   r.d146_last_m30_trend=V1_TREND_NEUTRAL;
   r.d146_last_valid_m30_protected_id="";
   r.d146_last_valid_m30_protected_price=0.0;
   r.d146_last_valid_m30_external_id="";
   r.d146_last_valid_m30_external_price=0.0;

   r.d146_m30_same_direction_initial_bos_count=0;
   r.d146_m30_same_direction_bos_count=0;
   r.d146_m30_opposite_direction_event_count=0;
   r.d146_m30_protected_break_count=0;
   r.d146_m30_owner_change_count=0;
   r.d146_m30_trend_loss_count=0;
   r.d146_m30_outward_external_refresh_count=0;
   r.d146_first_outward_external_refresh_at=0;
   r.d146_first_deterioration_at=0;
  }

void EdgeAuditD146TrackTick(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(!r.d146_active || r.d146_terminal || r.risk_distance<=0.0 || px<=0.0)
      return;

   r.d146_last_tick_at=at;
   r.d146_last_tick_price=px;
   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;
   double favorable_after_1r=MathMax(0.0,signed_r-1.0);
   double adverse_after_1r=MathMax(0.0,1.0-signed_r);
   if(favorable_after_1r>r.d146_post_1r_mfe_r) r.d146_post_1r_mfe_r=favorable_after_1r;
   if(adverse_after_1r>r.d146_post_1r_mae_r) r.d146_post_1r_mae_r=adverse_after_1r;

   if(r.d146_original_external_available &&
      !r.d146_original_external_at_or_beyond_at_1r &&
      !r.d146_original_external_delivered_after_1r)
     {
      bool reached=(r.direction>0 ? px>=r.d146_one_r_m30_external_price : px<=r.d146_one_r_m30_external_price);
      if(reached)
        {
         r.d146_original_external_delivered_after_1r=true;
         r.d146_original_external_delivered_at=at;
         EdgeAuditWrite("EDGE_AUDIT_D146_ORIGINAL_EXTERNAL_DELIVERED","TICK",at,r.scenario_id,
            StringFormat("scenario_id=%s direction=%s one_r_at=%s original_external_id=%s original_external_price=%.10f delivered_at=%s exit_side_price=%.10f after_t0=true strategy_authority=false",
                         r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.first_1r_at),
                         r.d146_one_r_m30_external_id=="" ? "NA" : r.d146_one_r_m30_external_id,
                         r.d146_one_r_m30_external_price,EdgeAuditTimeOrNA(at),px));
         g_edge_d146_original_external_deliveries++;
        }
     }
  }

void EdgeAuditD146Arm(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(!r.d146_eligible || r.d146_active || r.d146_terminal || r.first_1r_at<=0)
      return;

   V1EdgeD146M30State s;
   EdgeAuditD146ReadM30State(g_structure[2],r.direction,px,r.risk_distance,s);
   r.d146_active=true;
   r.d146_last_tick_at=at;
   r.d146_last_tick_price=px;
   r.d146_one_r_m30_trend=s.trend;
   r.d146_one_r_m30_owner_id=s.owner_id;
   r.d146_one_r_m30_owner_started_at=s.owner_started_at;
   r.d146_one_r_m30_protected_id=s.protected_id;
   r.d146_one_r_m30_protected_price=s.protected_price;
   r.d146_one_r_m30_external_id=s.external_id;
   r.d146_one_r_m30_external_price=s.external_price;
   r.d146_one_r_m30_range_available=s.range_available;
   r.d146_one_r_m30_range_span=s.range_span;
   r.d146_one_r_m30_range_progress=s.range_progress;
   r.d146_one_r_m30_remaining_to_external_r=s.remaining_to_external_r;

   r.d146_original_external_available=s.external_available;
   if(s.external_available)
      r.d146_original_external_at_or_beyond_at_1r=(r.direction>0 ? px>=s.external_price : px<=s.external_price);

   r.d146_last_m30_owner_id=s.owner_id;
   r.d146_last_m30_trend=s.trend;
   if(s.protected_available)
     {
      r.d146_last_valid_m30_protected_id=s.protected_id;
      r.d146_last_valid_m30_protected_price=s.protected_price;
     }
   if(s.external_available)
     {
      r.d146_last_valid_m30_external_id=s.external_id;
      r.d146_last_valid_m30_external_price=s.external_price;
     }

   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;
   r.d146_post_1r_mfe_r=MathMax(0.0,signed_r-1.0);
   r.d146_post_1r_mae_r=MathMax(0.0,1.0-signed_r);

   EdgeAuditWrite("EDGE_AUDIT_D146_1R_STATE","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s scope=%s direction=%s fill_at=%s one_r_at=%s one_r_price=%.10f target_2r=%.10f risk_distance=%.10f original_external_available=%s original_external_at_or_beyond_at_1r=%s original_external_future_backfill=false %s %s strategy_authority=false",
         r.scenario_id,ScenarioScopeName(r.scope),DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),
         EdgeAuditTimeOrNA(at),px,r.target_2r,r.risk_distance,
         r.d146_original_external_available ? "true" : "false",
         r.d146_original_external_at_or_beyond_at_1r ? "true" : "false",
         EdgeAuditCurrentMapIdentity(at,r.direction),EdgeAuditD146M30StateDetail(s,"one_r_m30")));
   g_edge_d146_armed++;
  }

void EdgeAuditD146OnM30StructureEvent(const V1StructureState &state,
                                      const int event_type,
                                      const int event_direction,
                                      const V1WaveRef &broken,
                                      const V1WaveRef &protected_ref,
                                      const MqlRates &bar,
                                      const datetime available_at)
  {
   if(state.tf!=PERIOD_M30)
      return;

   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid || !g_edge_runners[i].d146_active || g_edge_runners[i].d146_terminal)
         continue;
      V1EdgeRunnerTracker r=g_edge_runners[i];
      if(available_at<r.first_1r_at)
         continue;

      string before_owner=r.d146_last_m30_owner_id;
      int before_trend=r.d146_last_m30_trend;
      string before_protected_id=r.d146_last_valid_m30_protected_id;
      double before_protected_price=r.d146_last_valid_m30_protected_price;
      string before_external_id=r.d146_last_valid_m30_external_id;
      double before_external_price=r.d146_last_valid_m30_external_price;

      V1EdgeD146M30State s;
      EdgeAuditD146ReadM30State(state,r.direction,bar.close,r.risk_distance,s);

      bool directional_event=(event_type==V1_EVENT_INITIAL_BOS || event_type==V1_EVENT_BOS);
      bool same_direction=(directional_event && event_direction==r.direction);
      bool opposite_direction=(directional_event && event_direction==-r.direction);
      bool protected_break=(event_type==V1_EVENT_PROTECTED_BREAK);
      bool owner_changed=(before_owner!="" && before_owner!=s.owner_id);
      bool trend_lost=(TrendDirection(before_trend)==r.direction && s.trend_direction!=r.direction);
      bool outward_refresh=false;
      if(same_direction && before_external_price>0.0 && s.external_available)
        {
         double eps=MathMax(LiquidityTickSize()*0.5,1.0e-12);
         outward_refresh=(r.direction>0 ? s.external_price>before_external_price+eps : s.external_price<before_external_price-eps);
        }

      if(event_type==V1_EVENT_INITIAL_BOS && same_direction)
         r.d146_m30_same_direction_initial_bos_count++;
      if(event_type==V1_EVENT_BOS && same_direction)
         r.d146_m30_same_direction_bos_count++;
      if(opposite_direction)
         r.d146_m30_opposite_direction_event_count++;
      if(protected_break)
         r.d146_m30_protected_break_count++;
      if(owner_changed)
         r.d146_m30_owner_change_count++;
      if(trend_lost)
         r.d146_m30_trend_loss_count++;
      if(outward_refresh)
        {
         r.d146_m30_outward_external_refresh_count++;
         if(r.d146_first_outward_external_refresh_at<=0)
            r.d146_first_outward_external_refresh_at=available_at;
        }

      if(r.d146_first_deterioration_at<=0 && (protected_break || opposite_direction || owner_changed || trend_lost))
         r.d146_first_deterioration_at=available_at;

      if(r.d146_original_external_available && s.external_available)
        {
         double eps=MathMax(LiquidityTickSize()*0.5,1.0e-12);
         bool replaced=(s.external_id!=r.d146_one_r_m30_external_id ||
                        MathAbs(s.external_price-r.d146_one_r_m30_external_price)>eps);
         if(replaced && !r.d146_original_external_replaced_after_1r)
           {
            r.d146_original_external_replaced_after_1r=true;
            r.d146_original_external_replaced_at=available_at;
           }
        }

      EdgeAuditWrite("EDGE_AUDIT_D146_M30_EVENT","M30",available_at,r.scenario_id,
         StringFormat("scenario_id=%s direction=%s one_r_at=%s event_type=%s event_direction=%s event_bar_open=%s event_available_at=%s same_direction=%s opposite_direction=%s protected_break=%s owner_changed=%s trend_lost=%s outward_external_refresh=%s broken_id=%s broken_price=%.10f protected_ref_id=%s protected_ref_price=%.10f before_owner_id=%s before_trend=%s before_protected_id=%s before_protected_price=%.10f before_external_id=%s before_external_price=%.10f %s strategy_authority=false",
            r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.first_1r_at),EventName(event_type),DirectionName(event_direction),
            EdgeAuditTimeOrNA(bar.time),EdgeAuditTimeOrNA(available_at),
            same_direction ? "true" : "false",opposite_direction ? "true" : "false",protected_break ? "true" : "false",
            owner_changed ? "true" : "false",trend_lost ? "true" : "false",outward_refresh ? "true" : "false",
            broken.valid ? broken.id : "NA",broken.valid ? broken.price : 0.0,
            protected_ref.valid ? protected_ref.id : "NA",protected_ref.valid ? protected_ref.price : 0.0,
            before_owner=="" ? "NA" : before_owner,TrendName(before_trend),
            before_protected_id=="" ? "NA" : before_protected_id,before_protected_price,
            before_external_id=="" ? "NA" : before_external_id,before_external_price,
            EdgeAuditD146M30StateDetail(s,"after_m30")));
      g_edge_d146_structure_events++;

      r.d146_last_m30_owner_id=s.owner_id;
      r.d146_last_m30_trend=s.trend;
      if(s.protected_available)
        {
         r.d146_last_valid_m30_protected_id=s.protected_id;
         r.d146_last_valid_m30_protected_price=s.protected_price;
        }
      if(s.external_available)
        {
         r.d146_last_valid_m30_external_id=s.external_id;
         r.d146_last_valid_m30_external_price=s.external_price;
        }

      g_edge_runners[i]=r;
     }
  }

void EdgeAuditD146Terminal(V1EdgeRunnerTracker &r,const string outcome,const datetime at,const double px)
  {
   if(!r.d146_active || r.d146_terminal)
      return;
   EdgeAuditD146TrackTick(r,at,px);

   V1EdgeD146M30State s;
   EdgeAuditD146ReadM30State(g_structure[2],r.direction,px,r.risk_distance,s);
   r.d146_active=false;
   r.d146_terminal=true;
   r.d146_terminal_outcome=outcome;
   r.d146_resolved_at=at;

   EdgeAuditWrite("EDGE_AUDIT_D146_TERMINAL","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s scope=%s direction=%s outcome=%s fill_at=%s one_r_at=%s resolved_at=%s time_from_1r_seconds=%I64d exit_side_price=%.10f post_1r_mfe_r=%.10f post_1r_mae_r=%.10f original_external_available=%s original_external_id=%s original_external_price=%.10f original_external_at_or_beyond_at_1r=%s original_external_delivered_after_1r=%s original_external_delivered_at=%s original_external_replaced_after_1r=%s original_external_replaced_at=%s m30_same_direction_initial_bos_count=%I64d m30_same_direction_bos_count=%I64d m30_opposite_direction_event_count=%I64d m30_protected_break_count=%I64d m30_owner_change_count=%I64d m30_trend_loss_count=%I64d m30_outward_external_refresh_count=%I64d first_outward_external_refresh_at=%s first_deterioration_at=%s one_r_m30_range_available=%s one_r_m30_range_progress=%.10f one_r_m30_remaining_to_external_r=%.10f %s strategy_authority=false",
         r.scenario_id,ScenarioScopeName(r.scope),DirectionName(r.direction),outcome,
         EdgeAuditTimeOrNA(r.fill_at),EdgeAuditTimeOrNA(r.first_1r_at),EdgeAuditTimeOrNA(at),
         EdgeAuditAgeSeconds(at,r.first_1r_at),px,r.d146_post_1r_mfe_r,r.d146_post_1r_mae_r,
         r.d146_original_external_available ? "true" : "false",
         r.d146_one_r_m30_external_id=="" ? "NA" : r.d146_one_r_m30_external_id,
         r.d146_one_r_m30_external_price,
         r.d146_original_external_at_or_beyond_at_1r ? "true" : "false",
         r.d146_original_external_delivered_after_1r ? "true" : "false",
         EdgeAuditTimeOrNA(r.d146_original_external_delivered_at),
         r.d146_original_external_replaced_after_1r ? "true" : "false",
         EdgeAuditTimeOrNA(r.d146_original_external_replaced_at),
         r.d146_m30_same_direction_initial_bos_count,r.d146_m30_same_direction_bos_count,
         r.d146_m30_opposite_direction_event_count,r.d146_m30_protected_break_count,
         r.d146_m30_owner_change_count,r.d146_m30_trend_loss_count,
         r.d146_m30_outward_external_refresh_count,EdgeAuditTimeOrNA(r.d146_first_outward_external_refresh_at),
         EdgeAuditTimeOrNA(r.d146_first_deterioration_at),
         r.d146_one_r_m30_range_available ? "true" : "false",
         r.d146_one_r_m30_range_progress,r.d146_one_r_m30_remaining_to_external_r,
         EdgeAuditD146M30StateDetail(s,"terminal_m30")));
   g_edge_d146_terminals++;
  }

void EdgeAuditD146Censor(V1EdgeRunnerTracker &r,const datetime at)
  {
   if(!r.d146_active || r.d146_terminal)
      return;
   V1EdgeD146M30State s;
   EdgeAuditD146ReadM30State(g_structure[2],r.direction,r.d146_last_tick_price,r.risk_distance,s);
   EdgeAuditWrite("EDGE_AUDIT_D146_CENSORED","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s direction=%s fill_at=%s one_r_at=%s censored_at=%s last_tick_at=%s last_tick_price=%.10f post_1r_mfe_r=%.10f post_1r_mae_r=%.10f original_external_delivered_after_1r=%s m30_same_direction_initial_bos_count=%I64d m30_same_direction_bos_count=%I64d m30_opposite_direction_event_count=%I64d m30_protected_break_count=%I64d m30_owner_change_count=%I64d m30_trend_loss_count=%I64d m30_outward_external_refresh_count=%I64d tester_end_right_censored=true %s strategy_authority=false",
         r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),EdgeAuditTimeOrNA(r.first_1r_at),
         EdgeAuditTimeOrNA(at),EdgeAuditTimeOrNA(r.d146_last_tick_at),r.d146_last_tick_price,
         r.d146_post_1r_mfe_r,r.d146_post_1r_mae_r,
         r.d146_original_external_delivered_after_1r ? "true" : "false",
         r.d146_m30_same_direction_initial_bos_count,r.d146_m30_same_direction_bos_count,
         r.d146_m30_opposite_direction_event_count,r.d146_m30_protected_break_count,
         r.d146_m30_owner_change_count,r.d146_m30_trend_loss_count,
         r.d146_m30_outward_external_refresh_count,EdgeAuditD146M30StateDetail(s,"censor_m30")));
   g_edge_d146_censored++;
  }

void EdgeAuditArmPrefill(const int scenario_index,const datetime stage_at)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) || !g_scenarios[scenario_index].valid)
      return;
   V1ScenarioPlan p=g_scenarios[scenario_index];
   if(p.selected_fvg_id=="" || p.selected_fvg_width<=0.0)
      return;
   int existing=EdgeAuditFindPrefill(p.id);
   if(existing>=0) EdgeAuditRemovePrefillAt(existing);
   int n=ArraySize(g_edge_prefill);
   if(ArrayResize(g_edge_prefill,n+1,32)<0) return;
   V1EdgePrefillTracker t;
   t.valid=true;
   t.scenario_index=scenario_index;
   t.scenario_id=p.id;
   t.direction=p.direction;
   t.fvg_at=stage_at;
   t.entry_boundary=(p.direction>0 ? p.selected_fvg_top : p.selected_fvg_bottom);
   t.fvg_width=p.selected_fvg_width;
   t.max_favorable_abs=0.0;
   t.max_adverse_abs=0.0;
   t.max_favorable_at=0;
   t.max_adverse_at=0;
   t.first_tick_at=0;
   t.tick_count=0;
   g_edge_prefill[n]=t;
  }

void EdgeAuditUpdatePrefill(V1EdgePrefillTracker &t,const MqlTick &tick)
  {
   if((datetime)tick.time<t.fvg_at) return;
   double px=(t.direction>0 ? tick.bid : tick.ask);
   if(px<=0.0) return;
   if(t.first_tick_at<=0) t.first_tick_at=(datetime)tick.time;
   t.tick_count++;
   double signed_distance=(t.direction>0 ? px-t.entry_boundary : t.entry_boundary-px);
   if(signed_distance>t.max_favorable_abs)
     { t.max_favorable_abs=signed_distance; t.max_favorable_at=(datetime)tick.time; }
   double adverse=MathMax(0.0,-signed_distance);
   if(adverse>t.max_adverse_abs)
     { t.max_adverse_abs=adverse; t.max_adverse_at=(datetime)tick.time; }
  }

string EdgeAuditPrefillDetail(const string scenario_id,const datetime fill_at,const double risk)
  {
   int index=EdgeAuditFindPrefill(scenario_id);
   if(index<0)
      return "prefill_tracker_available=false";
   V1EdgePrefillTracker t=g_edge_prefill[index];
   double fav_r=(risk>0.0 ? t.max_favorable_abs/risk : 0.0);
   double adv_r=(risk>0.0 ? t.max_adverse_abs/risk : 0.0);
   double fav_fvg=(t.fvg_width>0.0 ? t.max_favorable_abs/t.fvg_width : 0.0);
   return StringFormat("prefill_tracker_available=true fvg_to_fill_seconds=%I64d prefill_first_tick_at=%s prefill_tick_count=%I64d prefill_entry_boundary=%.10f prefill_fvg_width=%.10f prefill_max_favorable_abs=%.10f prefill_max_favorable_r=%.10f prefill_max_favorable_fvg_widths=%.10f prefill_max_favorable_at=%s prefill_max_adverse_abs=%.10f prefill_max_adverse_r=%.10f prefill_max_adverse_at=%s",
                       EdgeAuditAgeSeconds(fill_at,t.fvg_at),EdgeAuditTimeOrNA(t.first_tick_at),t.tick_count,
                       t.entry_boundary,t.fvg_width,t.max_favorable_abs,fav_r,fav_fvg,EdgeAuditTimeOrNA(t.max_favorable_at),
                       t.max_adverse_abs,adv_r,EdgeAuditTimeOrNA(t.max_adverse_at));
  }

string EdgeAuditRunnerMarketContext(const V1ScenarioPlan &p,
                                    const datetime at,
                                    const double price,
                                    const double risk,
                                    const string prefix)
  {
   string root_detail=EdgeAuditRootMetaDetail(p.root_zone_id,at);
   double objective_room_r=(risk>0.0 ? (p.direction>0 ? p.final_objective_price-price : price-p.final_objective_price)/risk : 0.0);
   double fvg_width_r=(risk>0.0 ? p.selected_fvg_width/risk : 0.0);
   return StringFormat("%s %s %s %s %s %s_root_tf=%s %s_root_id=%s %s_fvg_id=%s %s_fvg_width=%.10f %s_fvg_width_r=%.10f %s_objective_price=%.10f %s_objective_room_r=%.10f %s_contact_to_now_seconds=%I64d %s_sweep_to_now_seconds=%I64d %s_choch_to_now_seconds=%I64d %s_fvg_to_now_seconds=%I64d %s_plan_to_now_seconds=%I64d %s",
      EdgeAuditCurrentMapIdentity(at,p.direction),
      EdgeAuditMapContextDetail(PERIOD_H1,at,prefix+"_h1_map"),
      EdgeAuditMapContextDetail(PERIOD_M30,at,prefix+"_m30_map"),
      EdgeAuditRangeContext(PERIOD_H1,p.direction,price,risk,prefix+"_h1_range"),
      EdgeAuditRangeContext(PERIOD_M30,p.direction,price,risk,prefix+"_m30_range"),
      prefix,TfName(p.source_tf),prefix,p.root_zone_id,prefix,p.selected_fvg_id,prefix,p.selected_fvg_width,prefix,fvg_width_r,
      prefix,p.final_objective_price,prefix,objective_room_r,
      prefix,EdgeAuditAgeSeconds(at,p.source_contact_at),prefix,EdgeAuditAgeSeconds(at,p.active_sweep_at),
      prefix,EdgeAuditAgeSeconds(at,p.scenario_choch_at),prefix,EdgeAuditAgeSeconds(at,p.selected_fvg_available_at),
      prefix,EdgeAuditAgeSeconds(at,p.frozen_at),
      EdgeAuditM30WaveContext(p.direction,at,prefix+"_m30_wave"));
  }

void EdgeAuditEmitRunnerOutcome(V1EdgeRunnerTracker &r,
                                const string target,
                                const string outcome,
                                const datetime at,
                                const double px)
  {
   EdgeAuditWrite("EDGE_AUDIT_RUNNER_OUTCOME","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s scope=%s direction=%s fill_at=%s target=%s outcome=%s resolved_at=%s exit_side_price=%.10f fill_price=%.10f risk_distance=%.10f max_favorable_r=%.10f max_adverse_r=%.10f first_1r_at=%s strategy_authority=false",
                   r.scenario_id,ScenarioScopeName(r.scope),DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),target,outcome,
                   EdgeAuditTimeOrNA(at),px,r.fill_price,r.risk_distance,r.max_favorable_r,r.max_adverse_r,EdgeAuditTimeOrNA(r.first_1r_at)));
   g_edge_runner_outcomes++;
  }

void EdgeAuditSnapshotAtOneR(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(r.scenario_index<0 || r.scenario_index>=ArraySize(g_scenarios) || !g_scenarios[r.scenario_index].valid)
      return;
   V1ScenarioPlan p=g_scenarios[r.scenario_index];
   long elapsed=EdgeAuditAgeSeconds(at,r.fill_at);
   double speed=(elapsed>0 ? 3600.0/(double)elapsed : 0.0);
   long h1_same=EdgeAuditDirCounter(PERIOD_H1,r.direction)-r.h1_same_dir_events_at_fill;
   long h1_opp=EdgeAuditDirCounter(PERIOD_H1,-r.direction)-r.h1_opposite_dir_events_at_fill;
   long m30_same=EdgeAuditDirCounter(PERIOD_M30,r.direction)-r.m30_same_dir_events_at_fill;
   long m30_opp=EdgeAuditDirCounter(PERIOD_M30,-r.direction)-r.m30_opposite_dir_events_at_fill;
   long m1_same=EdgeAuditDirCounter(PERIOD_M1,r.direction)-r.m1_same_dir_events_at_fill;
   long m1_opp=EdgeAuditDirCounter(PERIOD_M1,-r.direction)-r.m1_opposite_dir_events_at_fill;
   long h1_pb_same=EdgeAuditPbCounter(PERIOD_H1,r.direction)-r.h1_same_pb_events_at_fill;
   long h1_pb_opp=EdgeAuditPbCounter(PERIOD_H1,-r.direction)-r.h1_opposite_pb_events_at_fill;
   long m30_pb_same=EdgeAuditPbCounter(PERIOD_M30,r.direction)-r.m30_same_pb_events_at_fill;
   long m30_pb_opp=EdgeAuditPbCounter(PERIOD_M30,-r.direction)-r.m30_opposite_pb_events_at_fill;
   long m1_pb_same=EdgeAuditPbCounter(PERIOD_M1,r.direction)-r.m1_same_pb_events_at_fill;
   long m1_pb_opp=EdgeAuditPbCounter(PERIOD_M1,-r.direction)-r.m1_opposite_pb_events_at_fill;

   EdgeAuditWrite("EDGE_AUDIT_RUNNER_1R_SNAPSHOT","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s scope=%s direction=%s fill_at=%s one_r_at=%s time_to_1r_seconds=%I64d one_r_speed_r_per_hour=%.10f fill_price=%.10f one_r_price=%.10f risk_distance=%.10f max_adverse_before_1r_r=%.10f h1_same_direction_events_since_fill=%I64d h1_opposite_direction_events_since_fill=%I64d m30_same_direction_events_since_fill=%I64d m30_opposite_direction_events_since_fill=%I64d m1_same_direction_events_since_fill=%I64d m1_opposite_direction_events_since_fill=%I64d h1_same_pb_since_fill=%I64d h1_opposite_pb_since_fill=%I64d m30_same_pb_since_fill=%I64d m30_opposite_pb_since_fill=%I64d m1_same_pb_since_fill=%I64d m1_opposite_pb_since_fill=%I64d %s %s strategy_authority=false",
         r.scenario_id,ScenarioScopeName(r.scope),DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),EdgeAuditTimeOrNA(at),elapsed,speed,
         r.fill_price,px,r.risk_distance,r.max_adverse_before_1r_r,
         h1_same,h1_opp,m30_same,m30_opp,m1_same,m1_opp,h1_pb_same,h1_pb_opp,m30_pb_same,m30_pb_opp,m1_pb_same,m1_pb_opp,
         EdgeAuditM1Context(r.direction,"one_r_m1"),EdgeAuditRunnerMarketContext(p,at,px,r.risk_distance,"one_r")));
   g_edge_runner_one_r_snapshots++;
  }


//+------------------------------------------------------------------+
//| D-148 Entry-survival failure taxonomy -- shadow only             |
//+------------------------------------------------------------------+
void EdgeAuditD148CurrentMapState(int &direction,string &tf_name,string &owner_id)
  {
   ENUM_TIMEFRAMES tf=EdgeAuditHighestMapTf();
   direction=HighestActiveMapDirection();
   tf_name=(tf==PERIOD_CURRENT ? "NONE" : TfName(tf));
   owner_id="NA";
   if(tf==PERIOD_H1 && g_structure[1].owner_id!="") owner_id=g_structure[1].owner_id;
   else if(tf==PERIOD_M30 && g_structure[2].owner_id!="") owner_id=g_structure[2].owner_id;
  }

bool EdgeAuditD148OriginalAuthorityAlive(const V1EdgeRunnerTracker &r)
  {
   int index=-1;
   if(r.d148_original_map_tf==(int)PERIOD_H1) index=1;
   else if(r.d148_original_map_tf==(int)PERIOD_M30) index=2;
   if(index<0 || r.d148_original_owner_id=="") return false;
   return (g_structure[index].owner_id==r.d148_original_owner_id &&
           TrendDirection(g_structure[index].trend)==r.direction);
  }

void EdgeAuditD148ResetRunner(V1EdgeRunnerTracker &r)
  {
   r.d148_eligible=false;
   r.d148_pre_sl_resolved=false;
   r.d148_post_sl_active=false;
   r.d148_terminal=false;
   r.d148_terminal_outcome="";
   r.d148_resolved_at=0;
   r.d148_original_map_tf=(int)PERIOD_CURRENT;
   r.d148_original_owner_id="";
   r.d148_root_id="";
   r.d148_original_authority_alive_at_fill=false;
   r.d148_frozen_owner_invalidated=false;
   r.d148_frozen_owner_invalidated_at=0;
   r.d148_map_support_loss_seen=false;
   r.d148_first_map_support_loss_at=0;
   r.d148_first_map_support_loss_direction=0;
   r.d148_first_map_support_loss_tf="";
   r.d148_first_map_support_loss_owner_id="";
   r.d148_post_sl_map_support_loss_at=0;
   r.d148_post_sl_map_support_loss_direction=0;
   r.d148_post_sl_map_support_loss_tf="";
   r.d148_post_sl_map_support_loss_owner_id="";
   r.d148_root_invalidated_at=0;
   r.d148_root_invalidation_reason="";
   r.d148_sl_at=0;
   r.d148_sl_exit_side_price=0.0;
   r.d148_pre_sl_mfe_r=0.0;
   r.d148_pre_sl_mae_r=0.0;
   r.d148_map_support_same_at_sl=false;
   r.d148_entry_recovered_after_sl=false;
   r.d148_entry_recovered_at=0;
   r.d148_one_r_recovered_after_sl=false;
   r.d148_one_r_recovered_at=0;
   r.d148_post_sl_max_adverse_r_from_fill=0.0;
   r.d148_post_sl_max_favorable_r_from_fill=-1.0e100;
   r.d148_h1_same_events_at_sl=0;
   r.d148_h1_opp_events_at_sl=0;
   r.d148_m30_same_events_at_sl=0;
   r.d148_m30_opp_events_at_sl=0;
   r.d148_m1_same_events_at_sl=0;
   r.d148_m1_opp_events_at_sl=0;
   r.d148_h1_same_pb_at_sl=0;
   r.d148_h1_opp_pb_at_sl=0;
   r.d148_m30_same_pb_at_sl=0;
   r.d148_m30_opp_pb_at_sl=0;
   r.d148_m1_same_pb_at_sl=0;
   r.d148_m1_opp_pb_at_sl=0;
  }

void EdgeAuditD148ArmAtFill(V1EdgeRunnerTracker &r,const V1ScenarioPlan &p,const datetime at)
  {
   EdgeAuditD148ResetRunner(r);
   if(p.scope!=V1_SCOPE_EXTERNAL_CONTINUATION) return;
   r.d148_eligible=true;
   r.d148_original_map_tf=(int)p.active_map_tf;
   r.d148_original_owner_id=p.owner_id;
   r.d148_root_id=p.root_zone_id;
   r.d148_original_authority_alive_at_fill=EdgeAuditD148OriginalAuthorityAlive(r);
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   g_edge_d148_eligible++;
   EdgeAuditWrite("EDGE_AUDIT_D148_FILL_STATE","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s direction=%s fill_at=%s active_map_tf_at_plan=%s frozen_owner_id=%s frozen_owner_alive_at_fill=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s current_map_support_same=%s root_id=%s fill_price=%.10f normalized_sl=%.10f target_1r=%.10f risk_distance=%.10f strategy_authority=false",
                   r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),TfName((ENUM_TIMEFRAMES)r.d148_original_map_tf),
                   r.d148_original_owner_id=="" ? "NA" : r.d148_original_owner_id,
                   r.d148_original_authority_alive_at_fill ? "true" : "false",map_tf,map_owner,DirectionName(map_dir),
                   map_dir==r.direction ? "true" : "false",r.d148_root_id=="" ? "NA" : r.d148_root_id,
                   r.fill_price,r.normalized_sl,r.target_1r,r.risk_distance));
  }

string EdgeAuditD148PostSlEventDelta(const V1EdgeRunnerTracker &r)
  {
   return StringFormat("post_sl_h1_same_events=%I64d post_sl_h1_opp_events=%I64d post_sl_m30_same_events=%I64d post_sl_m30_opp_events=%I64d post_sl_m1_same_events=%I64d post_sl_m1_opp_events=%I64d post_sl_h1_same_pb=%I64d post_sl_h1_opp_pb=%I64d post_sl_m30_same_pb=%I64d post_sl_m30_opp_pb=%I64d post_sl_m1_same_pb=%I64d post_sl_m1_opp_pb=%I64d",
      EdgeAuditDirCounter(PERIOD_H1,r.direction)-r.d148_h1_same_events_at_sl,
      EdgeAuditDirCounter(PERIOD_H1,-r.direction)-r.d148_h1_opp_events_at_sl,
      EdgeAuditDirCounter(PERIOD_M30,r.direction)-r.d148_m30_same_events_at_sl,
      EdgeAuditDirCounter(PERIOD_M30,-r.direction)-r.d148_m30_opp_events_at_sl,
      EdgeAuditDirCounter(PERIOD_M1,r.direction)-r.d148_m1_same_events_at_sl,
      EdgeAuditDirCounter(PERIOD_M1,-r.direction)-r.d148_m1_opp_events_at_sl,
      EdgeAuditPbCounter(PERIOD_H1,r.direction)-r.d148_h1_same_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_H1,-r.direction)-r.d148_h1_opp_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_M30,r.direction)-r.d148_m30_same_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_M30,-r.direction)-r.d148_m30_opp_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_M1,r.direction)-r.d148_m1_same_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_M1,-r.direction)-r.d148_m1_opp_pb_at_sl);
  }

void EdgeAuditD148Terminal(V1EdgeRunnerTracker &r,const string outcome,const datetime at,const double px)
  {
   if(!r.d148_eligible || r.d148_terminal) return;
   r.d148_post_sl_active=false;
   r.d148_terminal=true;
   r.d148_terminal_outcome=outcome;
   r.d148_resolved_at=at;
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   double extra_beyond_sl=MathMax(0.0,r.d148_post_sl_max_adverse_r_from_fill-1.0);
   string detail=StringFormat("scenario_id=%s direction=%s outcome=%s sl_at=%s resolved_at=%s exit_side_price=%.10f fill_price=%.10f risk_distance=%.10f pre_sl_mfe_r=%.10f pre_sl_mae_r=%.10f map_support_same_at_sl=%s entry_recovered_after_sl=%s entry_recovered_at=%s one_r_recovered_after_sl=%s one_r_recovered_at=%s post_sl_max_adverse_r_from_fill=%.10f post_sl_extra_beyond_sl_r=%.10f post_sl_max_favorable_r_from_fill=%.10f frozen_owner_invalidated=%s frozen_owner_invalidated_at=%s first_map_support_loss_at=%s first_map_support_loss_direction=%s first_map_support_loss_tf=%s first_map_support_loss_owner_id=%s post_sl_map_support_loss_at=%s post_sl_map_support_loss_direction=%s post_sl_map_support_loss_tf=%s post_sl_map_support_loss_owner_id=%s root_invalidated_at=%s root_invalidation_reason=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s strategy_authority=false",
      r.scenario_id,DirectionName(r.direction),outcome,EdgeAuditTimeOrNA(r.d148_sl_at),EdgeAuditTimeOrNA(at),px,r.fill_price,r.risk_distance,
      r.d148_pre_sl_mfe_r,r.d148_pre_sl_mae_r,r.d148_map_support_same_at_sl ? "true" : "false",
      r.d148_entry_recovered_after_sl ? "true" : "false",EdgeAuditTimeOrNA(r.d148_entry_recovered_at),
      r.d148_one_r_recovered_after_sl ? "true" : "false",EdgeAuditTimeOrNA(r.d148_one_r_recovered_at),
      r.d148_post_sl_max_adverse_r_from_fill,extra_beyond_sl,r.d148_post_sl_max_favorable_r_from_fill,
      r.d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(r.d148_frozen_owner_invalidated_at),
      EdgeAuditTimeOrNA(r.d148_first_map_support_loss_at),DirectionName(r.d148_first_map_support_loss_direction),
      r.d148_first_map_support_loss_tf=="" ? "NA" : r.d148_first_map_support_loss_tf,
      r.d148_first_map_support_loss_owner_id=="" ? "NA" : r.d148_first_map_support_loss_owner_id,
      EdgeAuditTimeOrNA(r.d148_post_sl_map_support_loss_at),DirectionName(r.d148_post_sl_map_support_loss_direction),
      r.d148_post_sl_map_support_loss_tf=="" ? "NA" : r.d148_post_sl_map_support_loss_tf,
      r.d148_post_sl_map_support_loss_owner_id=="" ? "NA" : r.d148_post_sl_map_support_loss_owner_id,
      EdgeAuditTimeOrNA(r.d148_root_invalidated_at),r.d148_root_invalidation_reason=="" ? "NA" : r.d148_root_invalidation_reason,
      map_tf,map_owner,DirectionName(map_dir));
   detail+=" "+EdgeAuditD148PostSlEventDelta(r);
   if(r.scenario_index>=0 && r.scenario_index<ArraySize(g_scenarios) && g_scenarios[r.scenario_index].valid)
      detail+=" "+EdgeAuditRunnerMarketContext(g_scenarios[r.scenario_index],at,px,r.risk_distance,"d148_terminal");
   EdgeAuditWrite("EDGE_AUDIT_D148_TERMINAL","TICK",at,r.scenario_id,detail);
   if(outcome=="ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS") g_edge_d148_one_r_recoveries++;
   else g_edge_d148_map_loss_terminals++;
  }

void EdgeAuditD148OnOneRBeforeSl(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(!r.d148_eligible || r.d148_pre_sl_resolved) return;
   r.d148_pre_sl_resolved=true;
   r.d148_terminal=true;
   r.d148_terminal_outcome="ONE_R_CONTROL";
   r.d148_resolved_at=at;
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   EdgeAuditWrite("EDGE_AUDIT_D148_1R_CONTROL","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s direction=%s one_r_at=%s exit_side_price=%.10f fill_price=%.10f risk_distance=%.10f pre_1r_mfe_r=%.10f pre_1r_mae_r=%.10f frozen_owner_invalidated_before_1r=%s frozen_owner_invalidated_at=%s map_support_loss_seen_before_1r=%s first_map_support_loss_at=%s root_invalidated_before_1r=%s root_invalidated_at=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s strategy_authority=false",
         r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(at),px,r.fill_price,r.risk_distance,r.max_favorable_r,r.max_adverse_r,
         r.d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(r.d148_frozen_owner_invalidated_at),
         r.d148_map_support_loss_seen ? "true" : "false",EdgeAuditTimeOrNA(r.d148_first_map_support_loss_at),
         r.d148_root_invalidated_at>0 ? "true" : "false",EdgeAuditTimeOrNA(r.d148_root_invalidated_at),map_tf,map_owner,DirectionName(map_dir)));
   g_edge_d148_one_r_controls++;
  }

void EdgeAuditD148FreezeSlCounters(V1EdgeRunnerTracker &r)
  {
   r.d148_h1_same_events_at_sl=EdgeAuditDirCounter(PERIOD_H1,r.direction);
   r.d148_h1_opp_events_at_sl=EdgeAuditDirCounter(PERIOD_H1,-r.direction);
   r.d148_m30_same_events_at_sl=EdgeAuditDirCounter(PERIOD_M30,r.direction);
   r.d148_m30_opp_events_at_sl=EdgeAuditDirCounter(PERIOD_M30,-r.direction);
   r.d148_m1_same_events_at_sl=EdgeAuditDirCounter(PERIOD_M1,r.direction);
   r.d148_m1_opp_events_at_sl=EdgeAuditDirCounter(PERIOD_M1,-r.direction);
   r.d148_h1_same_pb_at_sl=EdgeAuditPbCounter(PERIOD_H1,r.direction);
   r.d148_h1_opp_pb_at_sl=EdgeAuditPbCounter(PERIOD_H1,-r.direction);
   r.d148_m30_same_pb_at_sl=EdgeAuditPbCounter(PERIOD_M30,r.direction);
   r.d148_m30_opp_pb_at_sl=EdgeAuditPbCounter(PERIOD_M30,-r.direction);
   r.d148_m1_same_pb_at_sl=EdgeAuditPbCounter(PERIOD_M1,r.direction);
   r.d148_m1_opp_pb_at_sl=EdgeAuditPbCounter(PERIOD_M1,-r.direction);
  }

void EdgeAuditD148OnSlFirst(V1EdgeRunnerTracker &r,const datetime at,const double px,const double signed_r)
  {
   if(!r.d148_eligible || r.d148_pre_sl_resolved) return;
   r.d148_pre_sl_resolved=true;
   r.d148_sl_at=at;
   r.d148_sl_exit_side_price=px;
   r.d148_pre_sl_mfe_r=r.max_favorable_r;
   r.d148_pre_sl_mae_r=r.max_adverse_r;
   r.d148_post_sl_max_adverse_r_from_fill=MathMax(0.0,-signed_r);
   r.d148_post_sl_max_favorable_r_from_fill=signed_r;
   EdgeAuditD148FreezeSlCounters(r);
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   r.d148_map_support_same_at_sl=(map_dir==r.direction);
   g_edge_d148_sl_failures++;
   string detail=StringFormat("scenario_id=%s direction=%s sl_at=%s exit_side_price=%.10f fill_price=%.10f normalized_sl=%.10f risk_distance=%.10f pre_sl_mfe_r=%.10f pre_sl_mae_r=%.10f active_map_tf_at_plan=%s frozen_owner_id=%s frozen_owner_alive_at_fill=%s frozen_owner_invalidated_before_sl=%s frozen_owner_invalidated_at=%s map_support_loss_seen_before_sl=%s first_map_support_loss_at=%s map_support_same_at_sl=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s root_id=%s root_invalidated_before_sl=%s root_invalidated_at=%s root_invalidation_reason=%s strategy_authority=false",
      r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(at),px,r.fill_price,r.normalized_sl,r.risk_distance,
      r.d148_pre_sl_mfe_r,r.d148_pre_sl_mae_r,TfName((ENUM_TIMEFRAMES)r.d148_original_map_tf),
      r.d148_original_owner_id=="" ? "NA" : r.d148_original_owner_id,r.d148_original_authority_alive_at_fill ? "true" : "false",
      r.d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(r.d148_frozen_owner_invalidated_at),
      r.d148_map_support_loss_seen ? "true" : "false",EdgeAuditTimeOrNA(r.d148_first_map_support_loss_at),
      r.d148_map_support_same_at_sl ? "true" : "false",map_tf,map_owner,DirectionName(map_dir),
      r.d148_root_id=="" ? "NA" : r.d148_root_id,r.d148_root_invalidated_at>0 ? "true" : "false",
      EdgeAuditTimeOrNA(r.d148_root_invalidated_at),r.d148_root_invalidation_reason=="" ? "NA" : r.d148_root_invalidation_reason);
   if(r.scenario_index>=0 && r.scenario_index<ArraySize(g_scenarios) && g_scenarios[r.scenario_index].valid)
      detail+=" "+EdgeAuditRunnerMarketContext(g_scenarios[r.scenario_index],at,px,r.risk_distance,"d148_sl");
   EdgeAuditWrite("EDGE_AUDIT_D148_SL_FAILURE","TICK",at,r.scenario_id,detail);
   r.d148_post_sl_active=true;
   if(!r.d148_map_support_same_at_sl)
      EdgeAuditD148Terminal(r,"MAP_SUPPORT_NOT_SAME_AT_SL",at,px);
  }

void EdgeAuditD148TrackPostSl(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(!r.d148_post_sl_active || r.d148_terminal || r.risk_distance<=0.0) return;
   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;
   if(-signed_r>r.d148_post_sl_max_adverse_r_from_fill) r.d148_post_sl_max_adverse_r_from_fill=-signed_r;
   if(signed_r>r.d148_post_sl_max_favorable_r_from_fill) r.d148_post_sl_max_favorable_r_from_fill=signed_r;
   bool hit_entry=(r.direction>0 ? px>=r.fill_price : px<=r.fill_price);
   bool hit_one=(r.direction>0 ? px>=r.target_1r : px<=r.target_1r);
   if(hit_entry && !r.d148_entry_recovered_after_sl)
     {
      r.d148_entry_recovered_after_sl=true;
      r.d148_entry_recovered_at=at;
      g_edge_d148_entry_recoveries++;
      EdgeAuditWrite("EDGE_AUDIT_D148_ENTRY_RECOVERED","TICK",at,r.scenario_id,
         StringFormat("scenario_id=%s direction=%s sl_at=%s entry_recovered_at=%s exit_side_price=%.10f post_sl_max_adverse_r_from_fill=%.10f strategy_authority=false",
                      r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.d148_sl_at),EdgeAuditTimeOrNA(at),px,r.d148_post_sl_max_adverse_r_from_fill));
     }
   if(hit_one)
     {
      r.d148_one_r_recovered_after_sl=true;
      r.d148_one_r_recovered_at=at;
      EdgeAuditD148Terminal(r,"ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS",at,px);
     }
  }

void EdgeAuditD148OnStructureEvent(const V1StructureState &state,const int event_type,const int direction,const datetime available_at)
  {
   if(event_type!=V1_EVENT_PROTECTED_BREAK) return;
   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid || !g_edge_runners[i].d148_eligible || g_edge_runners[i].d148_terminal || g_edge_runners[i].d148_frozen_owner_invalidated) continue;
      if((int)state.tf!=g_edge_runners[i].d148_original_map_tf) continue;
      if(g_edge_runners[i].d148_original_owner_id=="" || state.owner_id!=g_edge_runners[i].d148_original_owner_id) continue;
      g_edge_runners[i].d148_frozen_owner_invalidated=true;
      g_edge_runners[i].d148_frozen_owner_invalidated_at=available_at;
      g_edge_d148_frozen_owner_invalidations++;
      EdgeAuditWrite("EDGE_AUDIT_D148_FROZEN_OWNER_INVALIDATED",TfName(state.tf),available_at,g_edge_runners[i].scenario_id,
         StringFormat("scenario_id=%s direction=%s active_map_tf_at_plan=%s frozen_owner_id=%s event_direction=%s invalidated_at=%s pre_sl_resolved=%s post_sl_active=%s callback_state_is_pre_transition=true protected_break_itself_is_causal_invalidation=true strategy_authority=false",
                      g_edge_runners[i].scenario_id,DirectionName(g_edge_runners[i].direction),TfName((ENUM_TIMEFRAMES)g_edge_runners[i].d148_original_map_tf),g_edge_runners[i].d148_original_owner_id,
                      DirectionName(direction),EdgeAuditTimeOrNA(available_at),g_edge_runners[i].d148_pre_sl_resolved ? "true" : "false",g_edge_runners[i].d148_post_sl_active ? "true" : "false"));
     }
  }

void EdgeAuditD148OnRootInvalidated(const V1SourceZone &root,const datetime available_at,const string reason)
  {
   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid || !g_edge_runners[i].d148_eligible || g_edge_runners[i].d148_terminal || g_edge_runners[i].d148_root_invalidated_at>0) continue;
      if(g_edge_runners[i].d148_root_id=="" || root.id!=g_edge_runners[i].d148_root_id) continue;
      g_edge_runners[i].d148_root_invalidated_at=available_at;
      g_edge_runners[i].d148_root_invalidation_reason=reason;
      g_edge_d148_root_invalidations++;
      EdgeAuditWrite("EDGE_AUDIT_D148_ROOT_INVALIDATED",TfName(root.tf),available_at,g_edge_runners[i].scenario_id,
         StringFormat("scenario_id=%s direction=%s root_id=%s root_tf=%s invalidated_at=%s reason=%s pre_sl_resolved=%s post_sl_active=%s strategy_authority=false",
                      g_edge_runners[i].scenario_id,DirectionName(g_edge_runners[i].direction),root.id,TfName(root.tf),EdgeAuditTimeOrNA(available_at),reason,
                      g_edge_runners[i].d148_pre_sl_resolved ? "true" : "false",g_edge_runners[i].d148_post_sl_active ? "true" : "false"));
     }
  }

void EdgeAuditD148OnMapSample(const datetime available_at,const string sample_reason)
  {
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid || !g_edge_runners[i].d148_eligible || g_edge_runners[i].d148_terminal) continue;
      if(map_dir==g_edge_runners[i].direction) continue;
      if(!g_edge_runners[i].d148_map_support_loss_seen)
        {
         g_edge_runners[i].d148_map_support_loss_seen=true;
         g_edge_runners[i].d148_first_map_support_loss_at=available_at;
         g_edge_runners[i].d148_first_map_support_loss_direction=map_dir;
         g_edge_runners[i].d148_first_map_support_loss_tf=map_tf;
         g_edge_runners[i].d148_first_map_support_loss_owner_id=map_owner;
         EdgeAuditWrite("EDGE_AUDIT_D148_MAP_SUPPORT_LOST",map_tf,available_at,g_edge_runners[i].scenario_id,
            StringFormat("scenario_id=%s direction=%s lost_at=%s sample_reason=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s pre_sl_resolved=%s post_sl_active=%s frozen_owner_invalidated=%s frozen_owner_invalidated_at=%s strategy_authority=false",
                         g_edge_runners[i].scenario_id,DirectionName(g_edge_runners[i].direction),EdgeAuditTimeOrNA(available_at),sample_reason,map_tf,map_owner,DirectionName(map_dir),
                         g_edge_runners[i].d148_pre_sl_resolved ? "true" : "false",g_edge_runners[i].d148_post_sl_active ? "true" : "false",
                         g_edge_runners[i].d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(g_edge_runners[i].d148_frozen_owner_invalidated_at)));
        }
      if(g_edge_runners[i].d148_post_sl_active)
        {
         if(g_edge_runners[i].d148_post_sl_map_support_loss_at<=0)
           {
            g_edge_runners[i].d148_post_sl_map_support_loss_at=available_at;
            g_edge_runners[i].d148_post_sl_map_support_loss_direction=map_dir;
            g_edge_runners[i].d148_post_sl_map_support_loss_tf=map_tf;
            g_edge_runners[i].d148_post_sl_map_support_loss_owner_id=map_owner;
           }
         double map_px=(g_edge_runners[i].direction>0 ? SymbolInfoDouble(_Symbol,SYMBOL_BID) : SymbolInfoDouble(_Symbol,SYMBOL_ASK));
         EdgeAuditD148Terminal(g_edge_runners[i],"MAP_SUPPORT_LOST_AFTER_SL",available_at,map_px);
        }
     }
  }

void EdgeAuditD148Censor(V1EdgeRunnerTracker &r,const datetime at)
  {
   if(!r.d148_eligible || r.d148_terminal) return;
   if(r.d148_post_sl_active)
     {
      r.d148_post_sl_active=false;
      r.d148_terminal=true;
      r.d148_terminal_outcome="RIGHT_CENSORED_AFTER_SL";
      r.d148_resolved_at=at;
      g_edge_d148_censored++;
      EdgeAuditWrite("EDGE_AUDIT_D148_CENSORED","TICK",at,r.scenario_id,
         StringFormat("scenario_id=%s direction=%s sl_at=%s censored_at=%s entry_recovered_after_sl=%s entry_recovered_at=%s post_sl_max_adverse_r_from_fill=%.10f post_sl_max_favorable_r_from_fill=%.10f frozen_owner_invalidated=%s frozen_owner_invalidated_at=%s first_map_support_loss_at=%s tester_end_right_censored=true strategy_authority=false",
                      r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.d148_sl_at),EdgeAuditTimeOrNA(at),
                      r.d148_entry_recovered_after_sl ? "true" : "false",EdgeAuditTimeOrNA(r.d148_entry_recovered_at),
                      r.d148_post_sl_max_adverse_r_from_fill,r.d148_post_sl_max_favorable_r_from_fill,
                      r.d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(r.d148_frozen_owner_invalidated_at),
                      EdgeAuditTimeOrNA(r.d148_first_map_support_loss_at)));
      return;
     }
   if(!r.d148_pre_sl_resolved)
     {
      r.d148_terminal=true;
      r.d148_terminal_outcome="RIGHT_CENSORED_BEFORE_1R_OR_SL";
      r.d148_resolved_at=at;
      g_edge_d148_pre_sl_censored++;
      EdgeAuditWrite("EDGE_AUDIT_D148_PRE_SL_CENSORED","TICK",at,r.scenario_id,
         StringFormat("scenario_id=%s direction=%s fill_at=%s censored_at=%s max_favorable_r=%.10f max_adverse_r=%.10f tester_end_right_censored=true strategy_authority=false",
                      r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),EdgeAuditTimeOrNA(at),r.max_favorable_r,r.max_adverse_r));
     }
  }

void EdgeAuditProcessRunner(V1EdgeRunnerTracker &r,const MqlTick &tick)
  {
   if((datetime)tick.time<r.fill_at) return;
   double px=(r.direction>0 ? tick.bid : tick.ask);
   if(px<=0.0 || r.risk_distance<=0.0) return;
   r.ticks_seen++;
   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;
   if(r.d148_post_sl_active)
     {
      EdgeAuditD148TrackPostSl(r,(datetime)tick.time,px);
      return;
     }
   if(signed_r>r.max_favorable_r) r.max_favorable_r=signed_r;
   if(-signed_r>r.max_adverse_r) r.max_adverse_r=-signed_r;
   if(!r.reached_1r && r.max_adverse_r>r.max_adverse_before_1r_r) r.max_adverse_before_1r_r=r.max_adverse_r;
   if(r.d146_active)
      EdgeAuditD146TrackTick(r,(datetime)tick.time,px);

   bool hit_sl=(r.direction>0 ? px<=r.normalized_sl : px>=r.normalized_sl);
   bool hit_1=(r.direction>0 ? px>=r.target_1r : px<=r.target_1r);
   bool hit_2=(r.direction>0 ? px>=r.target_2r : px<=r.target_2r);
   bool hit_3=(r.direction>0 ? px>=r.target_3r : px<=r.target_3r);
   bool hit_structural=(r.structural_tp>0.0 && (r.direction>0 ? px>=r.structural_tp : px<=r.structural_tp));

   if(hit_1 && !r.reached_1r)
     {
      r.reached_1r=true;
      r.resolved_1r=true;
      r.first_1r_at=(datetime)tick.time;
      EdgeAuditD148OnOneRBeforeSl(r,(datetime)tick.time,px);
      EdgeAuditEmitRunnerOutcome(r,"1R","REACHED_BEFORE_SL",(datetime)tick.time,px);
      EdgeAuditSnapshotAtOneR(r,(datetime)tick.time,px);
      // D-148 intentionally does not arm D-146 post-1R continuation tracking.
     }
   if(hit_2 && !r.resolved_2r)
     {
      if(r.d146_active) EdgeAuditD146Terminal(r,"+2R_REACHED",(datetime)tick.time,px);
      r.resolved_2r=true;
      EdgeAuditEmitRunnerOutcome(r,"2R","REACHED_BEFORE_SL",(datetime)tick.time,px);
     }
   if(hit_3 && !r.resolved_3r)
     { r.resolved_3r=true; EdgeAuditEmitRunnerOutcome(r,"3R","REACHED_BEFORE_SL",(datetime)tick.time,px); }
   if(hit_structural && !r.resolved_structural)
     { r.resolved_structural=true; EdgeAuditEmitRunnerOutcome(r,"STRUCTURAL_TP","REACHED_BEFORE_SL",(datetime)tick.time,px); }

   if(hit_sl)
     {
      if(!r.reached_1r) EdgeAuditD148OnSlFirst(r,(datetime)tick.time,px,signed_r);
      if(r.d146_active && r.reached_1r) EdgeAuditD146Terminal(r,"SL_AFTER_1R",(datetime)tick.time,px);
      if(!r.resolved_1r) { r.resolved_1r=true; EdgeAuditEmitRunnerOutcome(r,"1R","SL_FIRST",(datetime)tick.time,px); }
      if(!r.resolved_2r) { r.resolved_2r=true; EdgeAuditEmitRunnerOutcome(r,"2R","SL_FIRST",(datetime)tick.time,px); }
      if(!r.resolved_3r) { r.resolved_3r=true; EdgeAuditEmitRunnerOutcome(r,"3R","SL_FIRST",(datetime)tick.time,px); }
      if(!r.resolved_structural) { r.resolved_structural=true; EdgeAuditEmitRunnerOutcome(r,"STRUCTURAL_TP","SL_FIRST",(datetime)tick.time,px); }
     }
  }

void EdgeAuditResetState()
  {
   g_edge_enabled=false;
   g_edge_rows=0;
   g_edge_rows_since_flush=0;
   g_edge_snapshots=0;
   g_edge_labels=0;
   g_edge_structure_snapshots=0;
   g_edge_root_snapshots=0;
   g_edge_physical_contacts=0;
   g_edge_last_map_sample_at=0;
   g_edge_h1_last_protected_break_at=0;
   g_edge_m30_last_protected_break_at=0;
   ArrayResize(g_edge_active,0);
   ArrayResize(g_edge_roots,0);
   ArrayResize(g_edge_prefill,0);
   ArrayResize(g_edge_runners,0);
   g_edge_runner_fill_snapshots=0;
   g_edge_runner_one_r_snapshots=0;
   g_edge_runner_outcomes=0;
   g_edge_runner_skipped=0;
   g_edge_d146_armed=0;
   g_edge_d146_structure_events=0;
   g_edge_d146_original_external_deliveries=0;
   g_edge_d146_terminals=0;
   g_edge_d146_censored=0;
   g_edge_d148_eligible=0;
   g_edge_d148_one_r_controls=0;
   g_edge_d148_sl_failures=0;
   g_edge_d148_entry_recoveries=0;
   g_edge_d148_one_r_recoveries=0;
   g_edge_d148_map_loss_terminals=0;
   g_edge_d148_frozen_owner_invalidations=0;
   g_edge_d148_root_invalidations=0;
   g_edge_d148_censored=0;
   g_edge_d148_pre_sl_censored=0;
   ArrayInitialize(g_edge_h1_dir_events,0);
   ArrayInitialize(g_edge_m30_dir_events,0);
   ArrayInitialize(g_edge_m1_dir_events,0);
   ArrayInitialize(g_edge_h1_pb_events,0);
   ArrayInitialize(g_edge_m30_pb_events,0);
   ArrayInitialize(g_edge_m1_pb_events,0);
   EdgeAuditClearMapTracker(g_edge_h1_tracker,PERIOD_H1);
   EdgeAuditClearMapTracker(g_edge_m30_tracker,PERIOD_M30);
  }

bool EdgeAuditInit()
  {
   if(!InpEnableEdgeAudit)
      return true;
   if(!InpWriteEventCsv || g_log_handle==INVALID_HANDLE)
     {
      Print("EDGE_AUDIT disabled: unified event CSV is not available. Strategy execution is unchanged.");
      return false;
     }
   g_edge_enabled=true;
   EdgeAuditWrite("EDGE_AUDIT_START","",TimeCurrent(),"",
      StringFormat("build=%s phase=%s strategy_authority=false unified_ledger=true event_csv=%s lightweight=true tick_tracking=CONTINUATION_PREFILL_FVG_SELECTED|CONTINUATION_ACTUAL_FILL_TO_1R_OR_SL|D148_POST_SL_FAILURE_ONLY front_end_forward_labels=false stage_virtual_barriers=false mirror_direction=false fill_snapshot=true first_1r_snapshot=true d146_post_1r_state=false d148_entry_survival_taxonomy=true d148_population=EXTERNAL_CONTINUATION_SL_BEFORE_1R d148_terminal=ORIGINAL_1R_RECOVERY_OR_MAP_SUPPORT_LOSS_OR_CENSOR d148_exit_mode_required=ORIGINAL observed_exit_mode=%s d148_no_time_cutoff=true d148_frozen_owner_break_is_context_not_terminal=true future_backfill=false strategy_change=false",
                   V1_EDGE_AUDIT_BUILD,V1_EDGE_AUDIT_PHASE,InpEventCsvFile,ExitManagementModeName((int)InpExitManagementMode)));
   return true;
  }

void EdgeAuditRemoveAt(const int index)
  {
   int n=ArraySize(g_edge_active);
   if(index<0 || index>=n)
      return;
   for(int i=index+1;i<n;i++)
      g_edge_active[i-1]=g_edge_active[i];
   ArrayResize(g_edge_active,n-1);
  }

int EdgeAuditFindRootMeta(const string root_id)
  {
   for(int i=ArraySize(g_edge_roots)-1;i>=0;i--)
      if(g_edge_roots[i].valid && g_edge_roots[i].root_id==root_id)
         return i;
   return -1;
  }

void EdgeAuditRemoveRootMetaAt(const int index)
  {
   int n=ArraySize(g_edge_roots);
   if(index<0 || index>=n)
      return;
   if(index<n-1)
      g_edge_roots[index]=g_edge_roots[n-1];
   ArrayResize(g_edge_roots,n-1);
  }

void EdgeAuditCaptureRootAgainstTracker(const ENUM_TIMEFRAMES tf,
                                        const V1SourceZone &root,
                                        string &owner_id,
                                        int &owner_direction,
                                        datetime &owner_started_at,
                                        datetime &last_bos_at,
                                        datetime &last_protected_update_at,
                                        datetime &last_protected_break_at,
                                        int &continuation_bos_count,
                                        int &root_event_ordinal,
                                        int &root_candidate_ordinal,
                                        bool &direction_match)
  {
   owner_id="";
   owner_direction=0;
   owner_started_at=0;
   last_bos_at=0;
   last_protected_update_at=0;
   last_protected_break_at=EdgeAuditLastProtectedBreakAt(tf);
   continuation_bos_count=0;
   root_event_ordinal=0;
   root_candidate_ordinal=0;
   direction_match=false;

   V1EdgeMapTracker tracker;
   if(!EdgeAuditGetMapTracker(tf,tracker))
      return;

   owner_id=tracker.owner_id;
   owner_direction=tracker.direction;
   owner_started_at=tracker.owner_started_at;
   last_bos_at=tracker.last_directional_bos_at;
   last_protected_update_at=tracker.last_protected_update_at;
   continuation_bos_count=tracker.continuation_bos_count;
   direction_match=(root.direction==tracker.direction && tracker.direction!=0);

   if(!direction_match)
      return;

   tracker.compatible_root_candidate_count++;
   if(tracker.last_compatible_root_structure_event_id!=root.linked_structure_event_id)
     {
      tracker.compatible_root_event_count++;
      tracker.last_compatible_root_structure_event_id=root.linked_structure_event_id;
     }
   root_event_ordinal=tracker.compatible_root_event_count;
   root_candidate_ordinal=tracker.compatible_root_candidate_count;
   EdgeAuditSetMapTracker(tf,tracker);
  }

string EdgeAuditRootMetaDetail(const string root_id,const datetime at)
  {
   int index=EdgeAuditFindRootMeta(root_id);
   if(index<0)
     {
      int source_index=FindSourceIndexById(root_id);
      if(source_index>=0)
        {
         V1SourceZone root=g_sources[source_index];
         return StringFormat("root_meta_available=false root_id=%s root_tf=%s root_created_at=%s root_age_seconds=%I64d root_origin_time=%s root_source_reason=%s root_direction=%s",
                             root_id,TfName(root.tf),EdgeAuditTimeOrNA(root.available_at),
                             EdgeAuditAgeSeconds(at,root.available_at),EdgeAuditTimeOrNA(root.origin_time),
                             root.source_reason,DirectionName(root.direction));
        }
      return "root_meta_available=false root_id="+root_id;
     }

   V1EdgeRootMeta m=g_edge_roots[index];
   return StringFormat(
      "root_meta_available=true root_id=%s root_tf=%s root_direction=%s root_source_reason=%s root_created_at=%s root_age_seconds=%I64d root_origin_time=%s root_origin_age_seconds=%I64d root_linked_structure_event_id=%s root_linked_event_type=%s root_create_h1_owner_id=%s root_create_h1_direction=%s root_create_h1_owner_started_at=%s root_create_h1_owner_age_seconds=%I64d root_create_h1_last_bos_at=%s root_create_h1_last_bos_age_seconds=%I64d root_create_h1_last_protected_update_at=%s root_create_h1_last_protected_update_age_seconds=%I64d root_create_h1_last_protected_break_at=%s root_create_h1_last_protected_break_age_seconds=%I64d root_create_h1_continuation_bos_count=%d root_create_h1_direction_match=%s h1_root_event_ordinal=%d h1_root_candidate_ordinal=%d root_create_m30_owner_id=%s root_create_m30_direction=%s root_create_m30_owner_started_at=%s root_create_m30_owner_age_seconds=%I64d root_create_m30_last_bos_at=%s root_create_m30_last_bos_age_seconds=%I64d root_create_m30_last_protected_update_at=%s root_create_m30_last_protected_update_age_seconds=%I64d root_create_m30_last_protected_break_at=%s root_create_m30_last_protected_break_age_seconds=%I64d root_create_m30_continuation_bos_count=%d root_create_m30_direction_match=%s m30_root_event_ordinal=%d m30_root_candidate_ordinal=%d",
      m.root_id,TfName(m.root_tf),DirectionName(m.direction),m.source_reason,
      EdgeAuditTimeOrNA(m.created_at),EdgeAuditAgeSeconds(at,m.created_at),
      EdgeAuditTimeOrNA(m.origin_time),EdgeAuditAgeSeconds(at,m.origin_time),
      m.linked_structure_event_id,EventName(m.linked_event_type),
      m.h1_owner_id_at_create=="" ? "NA" : m.h1_owner_id_at_create,DirectionName(m.h1_direction_at_create),
      EdgeAuditTimeOrNA(m.h1_owner_started_at_create),EdgeAuditAgeSeconds(at,m.h1_owner_started_at_create),
      EdgeAuditTimeOrNA(m.h1_last_bos_at_create),EdgeAuditAgeSeconds(at,m.h1_last_bos_at_create),
      EdgeAuditTimeOrNA(m.h1_last_protected_update_at_create),EdgeAuditAgeSeconds(at,m.h1_last_protected_update_at_create),
      EdgeAuditTimeOrNA(m.h1_last_protected_break_at_create),EdgeAuditAgeSeconds(at,m.h1_last_protected_break_at_create),
      m.h1_continuation_bos_count_at_create,m.h1_direction_match ? "true" : "false",m.h1_root_event_ordinal,m.h1_root_candidate_ordinal,
      m.m30_owner_id_at_create=="" ? "NA" : m.m30_owner_id_at_create,DirectionName(m.m30_direction_at_create),
      EdgeAuditTimeOrNA(m.m30_owner_started_at_create),EdgeAuditAgeSeconds(at,m.m30_owner_started_at_create),
      EdgeAuditTimeOrNA(m.m30_last_bos_at_create),EdgeAuditAgeSeconds(at,m.m30_last_bos_at_create),
      EdgeAuditTimeOrNA(m.m30_last_protected_update_at_create),EdgeAuditAgeSeconds(at,m.m30_last_protected_update_at_create),
      EdgeAuditTimeOrNA(m.m30_last_protected_break_at_create),EdgeAuditAgeSeconds(at,m.m30_last_protected_break_at_create),
      m.m30_continuation_bos_count_at_create,m.m30_direction_match ? "true" : "false",m.m30_root_event_ordinal,m.m30_root_candidate_ordinal);
  }

int EdgeAuditIncrementPlanCount(const ENUM_TIMEFRAMES tf,const string owner_id)
  {
   V1EdgeMapTracker tracker;
   if(!EdgeAuditGetMapTracker(tf,tracker) || tracker.owner_id!=owner_id)
      return 0;
   tracker.plan_count++;
   int ordinal=tracker.plan_count;
   EdgeAuditSetMapTracker(tf,tracker);
   return ordinal;
  }

string EdgeAuditScenarioDetail(const int scenario_index,const int stage,const datetime stage_at,const string extra)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid)
      return "scenario_context=UNAVAILABLE "+extra;

   V1ScenarioPlan p=g_scenarios[scenario_index];
   int plan_ordinal=0;
   if(stage==V1_EDGE_STAGE_PLAN)
      plan_ordinal=EdgeAuditIncrementPlanCount(p.active_map_tf,p.owner_id);

   ENUM_TIMEFRAMES current_map_tf=EdgeAuditHighestMapTf();
   string current_owner="";
   if(current_map_tf==PERIOD_H1) current_owner=g_structure[1].owner_id;
   else if(current_map_tf==PERIOD_M30) current_owner=g_structure[2].owner_id;
   int current_direction=HighestActiveMapDirection();

   return StringFormat(
      "active_map_tf=%s map_owner_id=%s h1_trend_at_freeze=%s h1_owner_id_at_freeze=%s m30_trend_at_freeze=%s m30_owner_id_at_freeze=%s reversal_permission_at_freeze=%s root_id=%s root_tf=%s root_bottom=%.10f root_top=%.10f plan_frozen_at=%s plan_age_seconds=%I64d owner_plan_ordinal=%d current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s frozen_owner_matches_current=%s frozen_direction_matches_current=%s sweep_id=%s sweep_extreme=%.10f choch_id=%s fvg_id=%s fvg_bottom=%.10f fvg_top=%.10f strategy_entry=%.10f strategy_sl=%.10f strategy_tp=%.10f planned_r=%.8f %s %s %s %s",
      TfName(p.active_map_tf),p.owner_id=="" ? "NA" : p.owner_id,
      TrendName(p.h1_trend_at_freeze),p.h1_owner_id_at_freeze=="" ? "NA" : p.h1_owner_id_at_freeze,
      TrendName(p.m30_trend_at_freeze),p.m30_owner_id_at_freeze=="" ? "NA" : p.m30_owner_id_at_freeze,
      ReversalPermissionName(p.reversal_permission_at_freeze),
      p.root_zone_id=="" ? "NA" : p.root_zone_id,TfName(p.source_tf),p.source_bottom,p.source_top,
      EdgeAuditTimeOrNA(p.frozen_at),EdgeAuditAgeSeconds(stage_at,p.frozen_at),plan_ordinal,
      current_map_tf==PERIOD_CURRENT ? "NONE" : TfName(current_map_tf),
      current_owner=="" ? "NA" : current_owner,DirectionName(current_direction),
      (current_owner!="" && current_owner==p.owner_id) ? "true" : "false",
      (current_direction!=0 && current_direction==p.direction) ? "true" : "false",
      p.active_sweep_event_id=="" ? "NA" : p.active_sweep_event_id,p.active_sweep_extreme,
      p.scenario_choch_event_id=="" ? "NA" : p.scenario_choch_event_id,
      p.selected_fvg_id=="" ? "NA" : p.selected_fvg_id,p.selected_fvg_bottom,p.selected_fvg_top,
      p.strategy_entry_price,p.normalized_sl,p.final_objective_price,p.final_objective_planned_r,
      EdgeAuditMapContextDetail(PERIOD_H1,stage_at,"h1_now"),
      EdgeAuditMapContextDetail(PERIOD_M30,stage_at,"m30_now"),
      EdgeAuditRootMetaDetail(p.root_zone_id,stage_at),extra);
  }

void EdgeAuditAppendSnapshot(V1EdgeSnapshot &s,const string detail,const bool track_forward)
  {
   EdgeAuditWriteSnapshotRow(s,detail);
   g_edge_snapshots++;
   if(!track_forward)
      return;

   int n=ArraySize(g_edge_active);
   if(ArrayResize(g_edge_active,n+1,64)<0)
      return;
   g_edge_active[n]=s;
  }

void EdgeAuditOnStructureEvent(const V1StructureState &state,
                               const int event_type,
                               const int direction,
                               const V1WaveRef &broken,
                               const V1WaveRef &protected_ref,
                               const MqlRates &bar,
                               const datetime available_at)
  {
   if(!g_edge_enabled)
      return;

   EdgeAuditCountStructureEvent(state.tf,event_type,direction);
   EdgeAuditD148OnStructureEvent(state,event_type,direction,available_at);
   // D-146 post-1R mechanism tracking is intentionally dormant in D-148.
   if(state.tf!=PERIOD_H1 && state.tf!=PERIOD_M30)
      return;

   V1EdgeMapTracker tracker;
   EdgeAuditGetMapTracker(state.tf,tracker);
   if(tracker.tf!=state.tf)
      EdgeAuditClearMapTracker(tracker,state.tf);

   if(event_type==V1_EVENT_INITIAL_BOS)
     {
      EdgeAuditClearMapTracker(tracker,state.tf);
      tracker.valid=true;
      tracker.owner_id=state.owner_id;
      tracker.direction=direction;
      tracker.owner_started_at=state.owner_started_at;
      tracker.last_initial_bos_at=available_at;
      tracker.last_directional_bos_at=available_at;
      if(protected_ref.valid)
        { tracker.last_protected_update_at=available_at; tracker.last_protected_id=protected_ref.id; }
      EdgeAuditSetMapTracker(state.tf,tracker);
     }
   else if(event_type==V1_EVENT_BOS)
     {
      if(!tracker.valid || tracker.owner_id!=state.owner_id)
        {
         EdgeAuditClearMapTracker(tracker,state.tf);
         tracker.valid=true;
         tracker.owner_id=state.owner_id;
         tracker.direction=TrendDirection(state.trend);
         tracker.owner_started_at=state.owner_started_at;
        }
      tracker.last_continuation_bos_at=available_at;
      tracker.last_directional_bos_at=available_at;
      tracker.continuation_bos_count++;
      if(protected_ref.valid && protected_ref.id!="" && protected_ref.id!=tracker.last_protected_id)
        { tracker.last_protected_update_at=available_at; tracker.last_protected_id=protected_ref.id; }
      EdgeAuditSetMapTracker(state.tf,tracker);
     }
   else if(event_type==V1_EVENT_PROTECTED_BREAK)
     {
      if(state.tf==PERIOD_H1) g_edge_h1_last_protected_break_at=available_at;
      else g_edge_m30_last_protected_break_at=available_at;
      EdgeAuditClearMapTracker(tracker,state.tf);
      EdgeAuditSetMapTracker(state.tf,tracker);
     }
  }

void EdgeAuditOnRootCreated(const V1SourceZone &root,
                            const int event_type,
                            const MqlRates &break_bar)
  {
   if(!g_edge_enabled || !root.valid || root.kind!=V1_SOURCE_ROOT)
      return;
   V1EdgeRootMeta m;
   m.valid=true;
   m.root_id=root.id;
   m.root_tf=root.tf;
   m.direction=root.direction;
   m.source_reason=root.source_reason;
   m.created_at=root.available_at;
   m.origin_time=root.origin_time;
   m.linked_structure_event_id=root.linked_structure_event_id;
   m.linked_event_type=event_type;
   EdgeAuditCaptureRootAgainstTracker(PERIOD_H1,root,
      m.h1_owner_id_at_create,m.h1_direction_at_create,m.h1_owner_started_at_create,
      m.h1_last_bos_at_create,m.h1_last_protected_update_at_create,m.h1_last_protected_break_at_create,
      m.h1_continuation_bos_count_at_create,m.h1_root_event_ordinal,m.h1_root_candidate_ordinal,m.h1_direction_match);
   EdgeAuditCaptureRootAgainstTracker(PERIOD_M30,root,
      m.m30_owner_id_at_create,m.m30_direction_at_create,m.m30_owner_started_at_create,
      m.m30_last_bos_at_create,m.m30_last_protected_update_at_create,m.m30_last_protected_break_at_create,
      m.m30_continuation_bos_count_at_create,m.m30_root_event_ordinal,m.m30_root_candidate_ordinal,m.m30_direction_match);
   int n=ArraySize(g_edge_roots);
   if(ArrayResize(g_edge_roots,n+1,128)<0) return;
   g_edge_roots[n]=m;
  }

void EdgeAuditOnRootInvalidated(const V1SourceZone &root,
                                const datetime available_at,
                                const string reason,
                                const MqlRates &bar)
  {
   if(!g_edge_enabled || !root.valid || root.kind!=V1_SOURCE_ROOT)
      return;
   EdgeAuditD148OnRootInvalidated(root,available_at,reason);
   int index=EdgeAuditFindRootMeta(root.id);
   if(index>=0) EdgeAuditRemoveRootMetaAt(index);
  }

void EdgeAuditOnPhysicalRootContact(const V1SourceZone &root,
                                    const MqlRates &bar,
                                    const datetime available_at,
                                    const int bound_scenario,
                                    const bool has_preplan)
  {
   // D-145 does not track the full Root-contact population on ticks. D-143
   // already supplied that census. Keep this hook intentionally lightweight.
   return;
  }

void EdgeAuditOnScenarioStage(const int stage,
                              const int scenario_index,
                              const datetime stage_at,
                              const double reference_price,
                              const string extra)
  {
   if(!g_edge_enabled || scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid)
      return;
   // The only pre-fill tick state retained is displacement after the selected
   // execution FVG. PLAN/Contact/Sweep/CHoCH forward labels were answered by D-143.
   if(stage==V1_EDGE_STAGE_FVG && g_scenarios[scenario_index].scope==V1_SCOPE_EXTERNAL_CONTINUATION)
      EdgeAuditArmPrefill(scenario_index,stage_at);
  }

void EdgeAuditOnMapSample(const datetime available_at,const string sample_reason)
  {
   // Persistent forward labels remain disabled. D-148 only checks the current
   // H1/M30 directional support at completed timestamp groups for active taxonomy trackers.
   if(!g_edge_enabled) return;
   EdgeAuditD148OnMapSample(available_at,sample_reason);
  }

void EdgeAuditUpdateExcursion(V1EdgeSnapshot &s,const MqlRates &bar)
  {
   if(s.direction>0)
     {
      s.favorable_abs=MathMax(s.favorable_abs,MathMax(0.0,bar.high-s.reference_price));
      s.adverse_abs=MathMax(s.adverse_abs,MathMax(0.0,s.reference_price-bar.low));
     }
   else
     {
      s.favorable_abs=MathMax(s.favorable_abs,MathMax(0.0,s.reference_price-bar.low));
      s.adverse_abs=MathMax(s.adverse_abs,MathMax(0.0,bar.high-s.reference_price));
     }
   s.last_close=bar.close;
   s.last_close_at=bar.time+PeriodSeconds(PERIOD_M1);
  }

void EdgeAuditEmitLabel(V1EdgeSnapshot &s,const int bit,const datetime observed_at,const string timing)
  {
   if((s.horizon_mask & bit)!=0)
      return;

   int horizon=EdgeAuditHorizonSeconds(bit);
   datetime target=s.stage_at+horizon;
   double move=(s.direction>0 ? s.last_close-s.reference_price : s.reference_price-s.last_close);
   double signed_pct=move/s.reference_price*100.0;
   double mfe_pct=s.favorable_abs/s.reference_price*100.0;
   double mae_pct=-s.adverse_abs/s.reference_price*100.0;
   long lag=(long)(target-s.last_close_at);

   EdgeAuditWrite("EDGE_AUDIT_FORWARD_LABEL",s.timeframe,observed_at,s.id,
      StringFormat("stage=%s stage_at=%s snapshot_id=%s scenario_id=%s population=%s direction=%s reference_price=%.10f horizon_seconds=%d horizon=%s target_at=%s end_at=%s end_price=%.10f end_lag_seconds=%I64d signed_return_pct=%.10f mfe_pct=%.10f mae_pct=%.10f timing=%s symbol=%s",
                   EdgeAuditStageName(s.stage),EdgeAuditTimeOrNA(s.stage_at),s.id,
                   s.scenario_id=="" ? "NA" : s.scenario_id,EdgeAuditPopulationName(s),DirectionName(s.direction),
                   s.reference_price,horizon,EdgeAuditHorizonName(bit),EdgeAuditTimeOrNA(target),
                   EdgeAuditTimeOrNA(s.last_close_at),s.last_close,lag,signed_pct,mfe_pct,mae_pct,timing,_Symbol));
   s.horizon_mask|=bit;
   g_edge_labels++;
  }

void EdgeAuditProcessOneHorizon(V1EdgeSnapshot &s,const int bit,
                                const datetime bar_open,const datetime bar_available)
  {
   if((s.horizon_mask & bit)!=0)
      return;
   datetime target=s.stage_at+EdgeAuditHorizonSeconds(bit);

   if(target<=bar_open)
     {
      EdgeAuditEmitLabel(s,bit,bar_open,"LAST_CAUSAL_CLOSE_AT_OR_BEFORE_TARGET");
      return;
     }
   if(target>bar_open && target<=bar_available)
      EdgeAuditEmitLabel(s,bit,bar_available,"M1_CLOSE_AT_TARGET");
  }

void EdgeAuditOnM1BarBeforeStrategy(const MqlRates &bar,const datetime available_at)
  {
   // No rolling M1 forward-label population in D-145.
   return;
  }

void EdgeAuditOnActualFill(const int scenario_index,const datetime observed_at)
  {
   if(!g_edge_enabled || scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid)
      return;
   V1ScenarioPlan p=g_scenarios[scenario_index];
   if(p.fill_price<=0.0)
      return;

   long lag=(p.fill_at>0 ? (long)(observed_at-p.fill_at) : -1);
   double risk=MathAbs(p.fill_price-p.normalized_sl);
   if(p.fill_at<=0 || lag!=0 || p.normalized_sl<=0.0 || risk<=MathMax(LiquidityTickSize(),1.0e-12))
     {
      g_edge_runner_skipped++;
      EdgeAuditWrite("EDGE_AUDIT_RUNNER_SKIPPED","TICK",observed_at,p.id,
         StringFormat("scenario_id=%s reason=INVALID_OR_LATE_FILL_ANCHOR fill_at=%s observed_at=%s observation_lag_seconds=%I64d fill_price=%.10f normalized_sl=%.10f risk_distance=%.10f exact_tick_runner_not_reconstructed=true strategy_authority=false",
                      p.id,EdgeAuditTimeOrNA(p.fill_at),EdgeAuditTimeOrNA(observed_at),lag,p.fill_price,p.normalized_sl,risk));
      int stale=EdgeAuditFindPrefill(p.id); if(stale>=0) EdgeAuditRemovePrefillAt(stale);
      return;
     }

   string prefill=EdgeAuditPrefillDetail(p.id,p.fill_at,risk);
   EdgeAuditWrite("EDGE_AUDIT_RUNNER_FILL_SNAPSHOT","TICK",observed_at,p.id,
      StringFormat("scenario_id=%s scope=%s direction=%s fill_at=%s observed_at=%s fill_price=%.10f normalized_sl=%.10f risk_distance=%.10f target_1r=%.10f target_2r=%.10f target_3r=%.10f structural_tp=%.10f planned_r=%.10f active_map_tf_at_plan=%s frozen_owner_id=%s h1_trend_at_plan=%s m30_trend_at_plan=%s root_id=%s root_tf=%s root_bottom=%.10f root_top=%.10f selected_fvg_id=%s selected_fvg_bottom=%.10f selected_fvg_top=%.10f selected_fvg_width=%.10f %s %s %s strategy_authority=false",
         p.id,ScenarioScopeName(p.scope),DirectionName(p.direction),EdgeAuditTimeOrNA(p.fill_at),EdgeAuditTimeOrNA(observed_at),
         p.fill_price,p.normalized_sl,risk,
         p.direction>0 ? p.fill_price+risk : p.fill_price-risk,
         p.direction>0 ? p.fill_price+2.0*risk : p.fill_price-2.0*risk,
         p.direction>0 ? p.fill_price+3.0*risk : p.fill_price-3.0*risk,
         p.final_objective_price,p.final_objective_planned_r,TfName(p.active_map_tf),p.owner_id,
         TrendName(p.h1_trend_at_freeze),TrendName(p.m30_trend_at_freeze),p.root_zone_id,TfName(p.source_tf),p.source_bottom,p.source_top,
         p.selected_fvg_id,p.selected_fvg_bottom,p.selected_fvg_top,p.selected_fvg_width,
         prefill,EdgeAuditM1Context(p.direction,"fill_m1"),EdgeAuditRunnerMarketContext(p,p.fill_at,p.fill_price,risk,"fill")));
   g_edge_runner_fill_snapshots++;

   int old=EdgeAuditFindPrefill(p.id); if(old>=0) EdgeAuditRemovePrefillAt(old);

   // D-148 runner population is continuation-only. Reversal outcomes are outside this research question.
   if(p.scope!=V1_SCOPE_EXTERNAL_CONTINUATION) return;

   int n=ArraySize(g_edge_runners);
   if(ArrayResize(g_edge_runners,n+1,16)<0) return;
   V1EdgeRunnerTracker r;
   r.valid=true;
   r.scenario_index=scenario_index;
   r.scenario_id=p.id;
   r.scope=p.scope;
   r.direction=p.direction;
   r.fill_at=p.fill_at;
   r.fill_price=p.fill_price;
   r.normalized_sl=p.normalized_sl;
   r.risk_distance=risk;
   r.target_1r=(p.direction>0 ? p.fill_price+risk : p.fill_price-risk);
   r.target_2r=(p.direction>0 ? p.fill_price+2.0*risk : p.fill_price-2.0*risk);
   r.target_3r=(p.direction>0 ? p.fill_price+3.0*risk : p.fill_price-3.0*risk);
   r.structural_tp=p.final_objective_price;
   r.reached_1r=false;
   r.resolved_1r=false;
   r.resolved_2r=false;
   r.resolved_3r=false;
   r.resolved_structural=false;
   r.first_1r_at=0;
   r.max_favorable_r=0.0;
   r.max_adverse_r=0.0;
   r.max_adverse_before_1r_r=0.0;
   r.ticks_seen=0;
   EdgeAuditD146ResetRunner(r);
   EdgeAuditD148ArmAtFill(r,p,observed_at);
   r.h1_same_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_H1,p.direction);
   r.h1_opposite_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_H1,-p.direction);
   r.m30_same_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_M30,p.direction);
   r.m30_opposite_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_M30,-p.direction);
   r.m1_same_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_M1,p.direction);
   r.m1_opposite_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_M1,-p.direction);
   r.h1_same_pb_events_at_fill=EdgeAuditPbCounter(PERIOD_H1,p.direction);
   r.h1_opposite_pb_events_at_fill=EdgeAuditPbCounter(PERIOD_H1,-p.direction);
   r.m30_same_pb_events_at_fill=EdgeAuditPbCounter(PERIOD_M30,p.direction);
   r.m30_opposite_pb_events_at_fill=EdgeAuditPbCounter(PERIOD_M30,-p.direction);
   r.m1_same_pb_events_at_fill=EdgeAuditPbCounter(PERIOD_M1,p.direction);
   r.m1_opposite_pb_events_at_fill=EdgeAuditPbCounter(PERIOD_M1,-p.direction);
   g_edge_runners[n]=r;
  }

void EdgeAuditOnTick(const MqlTick &tick)
  {
   if(!g_edge_enabled)
      return;

   int i=0;
   while(i<ArraySize(g_edge_prefill))
     {
      if(!g_edge_prefill[i].valid)
        { EdgeAuditRemovePrefillAt(i); continue; }
      int s=g_edge_prefill[i].scenario_index;
      if(s<0 || s>=ArraySize(g_scenarios) || !g_scenarios[s].valid ||
         g_scenarios[s].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[s].strategy_state==V1_STRATEGY_NO_TRADE ||
         g_scenarios[s].strategy_state==V1_STRATEGY_MERGED_CONTRIBUTOR)
        { EdgeAuditRemovePrefillAt(i); continue; }
      EdgeAuditUpdatePrefill(g_edge_prefill[i],tick);
      i++;
     }

   i=0;
   while(i<ArraySize(g_edge_runners))
     {
      if(!g_edge_runners[i].valid)
        { EdgeAuditRemoveRunnerAt(i); continue; }
      EdgeAuditProcessRunner(g_edge_runners[i],tick);
      if(g_edge_runners[i].d148_terminal && g_edge_runners[i].d148_terminal_outcome=="ONE_R_CONTROL")
        { EdgeAuditRemoveRunnerAt(i); continue; }
      if(g_edge_runners[i].resolved_1r && g_edge_runners[i].resolved_2r &&
         g_edge_runners[i].resolved_3r && g_edge_runners[i].resolved_structural &&
         !g_edge_runners[i].d148_post_sl_active)
        { EdgeAuditRemoveRunnerAt(i); continue; }
      i++;
     }
  }

void EdgeAuditDeinit(const int reason)
  {
   if(!g_edge_enabled)
      return;
   datetime now=TimeCurrent();
   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid) continue;
      if(g_edge_runners[i].d146_active) EdgeAuditD146Censor(g_edge_runners[i],now);
      EdgeAuditD148Censor(g_edge_runners[i],now);
      EdgeAuditWrite("EDGE_AUDIT_RUNNER_CENSORED","TICK",now,g_edge_runners[i].scenario_id,
         StringFormat("scenario_id=%s direction=%s fill_at=%s reached_1r=%s resolved_1r=%s resolved_2r=%s resolved_3r=%s resolved_structural=%s max_favorable_r=%.10f max_adverse_r=%.10f tester_end_right_censored=true strategy_authority=false",
                      g_edge_runners[i].scenario_id,DirectionName(g_edge_runners[i].direction),EdgeAuditTimeOrNA(g_edge_runners[i].fill_at),
                      g_edge_runners[i].reached_1r ? "true" : "false",g_edge_runners[i].resolved_1r ? "true" : "false",
                      g_edge_runners[i].resolved_2r ? "true" : "false",g_edge_runners[i].resolved_3r ? "true" : "false",
                      g_edge_runners[i].resolved_structural ? "true" : "false",g_edge_runners[i].max_favorable_r,g_edge_runners[i].max_adverse_r));
     }
   EdgeAuditWrite("EDGE_AUDIT_STOP","",now,"",
      StringFormat("reason=%d rows=%I64d fill_snapshots=%I64d one_r_snapshots=%I64d runner_outcomes=%I64d runner_skipped=%I64d d146_armed=%I64d d146_structure_events=%I64d d146_original_external_deliveries=%I64d d146_terminals=%I64d d146_censored=%I64d d148_eligible=%I64d d148_one_r_controls=%I64d d148_sl_failures=%I64d d148_entry_recoveries=%I64d d148_one_r_recoveries=%I64d d148_map_loss_terminals=%I64d d148_frozen_owner_invalidations=%I64d d148_root_invalidations=%I64d d148_censored=%I64d d148_pre_sl_censored=%I64d active_prefill=%d active_runners=%d front_end_forward_labels=false stage_virtual_barriers=false lightweight=true strategy_authority=false",
                   reason,g_edge_rows,g_edge_runner_fill_snapshots,g_edge_runner_one_r_snapshots,g_edge_runner_outcomes,
                   g_edge_runner_skipped,g_edge_d146_armed,g_edge_d146_structure_events,g_edge_d146_original_external_deliveries,
                   g_edge_d146_terminals,g_edge_d146_censored,g_edge_d148_eligible,g_edge_d148_one_r_controls,g_edge_d148_sl_failures,
                   g_edge_d148_entry_recoveries,g_edge_d148_one_r_recoveries,g_edge_d148_map_loss_terminals,g_edge_d148_frozen_owner_invalidations,
                   g_edge_d148_root_invalidations,g_edge_d148_censored,g_edge_d148_pre_sl_censored,ArraySize(g_edge_prefill),ArraySize(g_edge_runners)));
   g_edge_enabled=false;
  }
//+------------------------------------------------------------------+
