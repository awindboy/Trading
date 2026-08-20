//+------------------------------------------------------------------+
//| EdgeAuditV1.mqh                                                  |
//| D-145 RUNNER MARKET-CONTEXT AUDIT -- lightweight shadow       |
//|                                                                  |
//| STRATEGY AUTHORITY: NONE                                         |
//| This module may observe and log. It may not change a trade.      |
//+------------------------------------------------------------------+

#define V1_EDGE_AUDIT_BUILD       "1.92R1L7"
#define V1_EDGE_AUDIT_PHASE       "RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT"
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

void EdgeAuditProcessRunner(V1EdgeRunnerTracker &r,const MqlTick &tick)
  {
   if((datetime)tick.time<r.fill_at) return;
   double px=(r.direction>0 ? tick.bid : tick.ask);
   if(px<=0.0 || r.risk_distance<=0.0) return;
   r.ticks_seen++;
   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;
   if(signed_r>r.max_favorable_r) r.max_favorable_r=signed_r;
   if(-signed_r>r.max_adverse_r) r.max_adverse_r=-signed_r;
   if(!r.reached_1r && r.max_adverse_r>r.max_adverse_before_1r_r) r.max_adverse_before_1r_r=r.max_adverse_r;

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
      EdgeAuditEmitRunnerOutcome(r,"1R","REACHED_BEFORE_SL",(datetime)tick.time,px);
      EdgeAuditSnapshotAtOneR(r,(datetime)tick.time,px);
     }
   if(hit_2 && !r.resolved_2r)
     { r.resolved_2r=true; EdgeAuditEmitRunnerOutcome(r,"2R","REACHED_BEFORE_SL",(datetime)tick.time,px); }
   if(hit_3 && !r.resolved_3r)
     { r.resolved_3r=true; EdgeAuditEmitRunnerOutcome(r,"3R","REACHED_BEFORE_SL",(datetime)tick.time,px); }
   if(hit_structural && !r.resolved_structural)
     { r.resolved_structural=true; EdgeAuditEmitRunnerOutcome(r,"STRUCTURAL_TP","REACHED_BEFORE_SL",(datetime)tick.time,px); }

   if(hit_sl)
     {
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
      StringFormat("build=%s phase=%s strategy_authority=false unified_ledger=true event_csv=%s lightweight=true tick_tracking=PREFILL_FVG_SELECTED|ACTUAL_FILL_ONLY front_end_forward_labels=false stage_virtual_barriers=false mirror_direction=false fill_snapshot=true first_1r_snapshot=true outcomes=1R|2R|3R|STRUCTURAL_TP_vs_SL hypotheses=MARKET_BACKGROUND|DIRECTIONAL_MATURITY|M30_NET_ADVANCE|PREFILL_DISPLACEMENT|POST_FILL_CONTINUATION strategy_change=false",
                   V1_EDGE_AUDIT_BUILD,V1_EDGE_AUDIT_PHASE,InpEventCsvFile));
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
   if(stage==V1_EDGE_STAGE_FVG)
      EdgeAuditArmPrefill(scenario_index,stage_at);
  }

void EdgeAuditOnMapSample(const datetime available_at,const string sample_reason)
  {
   // Disabled in D-145. Persistent MAP forward sampling was completed in D-143.
   return;
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
      if(g_edge_runners[i].resolved_1r && g_edge_runners[i].resolved_2r &&
         g_edge_runners[i].resolved_3r && g_edge_runners[i].resolved_structural)
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
      EdgeAuditWrite("EDGE_AUDIT_RUNNER_CENSORED","TICK",now,g_edge_runners[i].scenario_id,
         StringFormat("scenario_id=%s direction=%s fill_at=%s reached_1r=%s resolved_1r=%s resolved_2r=%s resolved_3r=%s resolved_structural=%s max_favorable_r=%.10f max_adverse_r=%.10f tester_end_right_censored=true strategy_authority=false",
                      g_edge_runners[i].scenario_id,DirectionName(g_edge_runners[i].direction),EdgeAuditTimeOrNA(g_edge_runners[i].fill_at),
                      g_edge_runners[i].reached_1r ? "true" : "false",g_edge_runners[i].resolved_1r ? "true" : "false",
                      g_edge_runners[i].resolved_2r ? "true" : "false",g_edge_runners[i].resolved_3r ? "true" : "false",
                      g_edge_runners[i].resolved_structural ? "true" : "false",g_edge_runners[i].max_favorable_r,g_edge_runners[i].max_adverse_r));
     }
   EdgeAuditWrite("EDGE_AUDIT_STOP","",now,"",
      StringFormat("reason=%d rows=%I64d fill_snapshots=%I64d one_r_snapshots=%I64d runner_outcomes=%I64d runner_skipped=%I64d active_prefill=%d active_runners=%d front_end_forward_labels=false stage_virtual_barriers=false lightweight=true strategy_authority=false",
                   reason,g_edge_rows,g_edge_runner_fill_snapshots,g_edge_runner_one_r_snapshots,g_edge_runner_outcomes,
                   g_edge_runner_skipped,ArraySize(g_edge_prefill),ArraySize(g_edge_runners)));
   g_edge_enabled=false;
  }
//+------------------------------------------------------------------+
