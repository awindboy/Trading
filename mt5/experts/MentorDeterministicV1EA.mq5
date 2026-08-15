//+------------------------------------------------------------------+
//| MentorDeterministicV1EA.mq5                                     |
//| Deterministic Mentor EA V1 - Phase 4B scenario/objective core   |
//|                                                                  |
//| Authority:                                                       |
//|   AGENTS.md                                                      |
//|   docs/ea/EA_SPEC.md                                             |
//|                                                                  |
//| Phase 4B intentionally DOES NOT submit orders.                   |
//| Structure/liquidity/Root/refinement/map core is verified. This  |
//| build adds frozen scenario/source-lineage/objective-family PLANs.  |
//| Source-contact/trigger/order layers remain disabled.                |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "Mentor deterministic V1 EA - Phase 4B scenario/objective core"

//--- execution identity / diagnostics
input long   InpMagicNumber        = 26081601;
input bool   InpWriteEventCsv      = true;
input bool   InpVerboseLog         = false;
input bool   InpLogBootstrapEvents = false;
input string InpEventCsvFile       = "mentor_v1_phase4b_events.csv";

// IMPORTANT:
// V1 parity trading volume and broker-order execution are frozen in the spec,
// but are intentionally not active in this Phase 4B scenario/objective build.

enum V1InitState
  {
   V1_INIT_SYNCING=0,
   V1_INIT_H4_INDEX,
   V1_INIT_ACTIVE_MAP,
   V1_INIT_SOURCE_CONTEXT,
   V1_READY,
   V1_INIT_EXECUTION_RECOVERY_REQUIRED,
   V1_INIT_ERROR
  };

enum V1TrendState
  {
   V1_TREND_NEUTRAL=0,
   V1_TREND_BULLISH,
   V1_TREND_BEARISH,
   V1_TREND_TRANSITION
  };

enum V1WaveSide
  {
   V1_SIDE_NONE=0,
   V1_SIDE_HIGH=1,
   V1_SIDE_LOW=-1
  };

enum V1StructureEventType
  {
   V1_EVENT_NONE=0,
   V1_EVENT_INITIAL_BOS,
   V1_EVENT_BOS,
   V1_EVENT_PROTECTED_BREAK
  };

enum V1LiquidityFamily
  {
   V1_LIQ_EXTERNAL_SWING=0,
   V1_LIQ_DEFENDED_RANGE_EDGE,
   V1_LIQ_STRUCTURAL_REACTION
  };

enum V1LiquidityConsumption
  {
   V1_LIQ_CONSUME_NONE=0,
   V1_LIQ_CONSUME_SWEEP,
   V1_LIQ_CONSUME_BODY_DELIVERY
  };

enum V1SourceKind
  {
   V1_SOURCE_ROOT=0,
   V1_SOURCE_CHILD
  };

enum V1SourceState
  {
   V1_SOURCE_ACTIVE=0,
   V1_SOURCE_INVALIDATED
  };

enum V1RefinementStatus
  {
   V1_REFINE_WAITING=0,
   V1_REFINE_READY,
   V1_REFINE_NO_CHILD,
   V1_REFINE_AMBIGUOUS_FIRST,
   V1_REFINE_STOPPED_AMBIGUOUS,
   V1_REFINE_INVALIDATED
  };

enum V1ReversalPermission
  {
   V1_REVERSAL_CLOSED=0,
   V1_REVERSAL_OPEN_FOR_LONG,
   V1_REVERSAL_OPEN_FOR_SHORT
  };

enum V1ReferenceEventType
  {
   V1_REFERENCE_NONE=0,
   V1_REFERENCE_TOUCH,
   V1_REFERENCE_SWEEP_REJECTION,
   V1_REFERENCE_CONTINUATION_BODY_BREAK
  };

enum V1ScenarioScope
  {
   V1_SCOPE_NONE=0,
   V1_SCOPE_EXTERNAL_CONTINUATION,
   V1_SCOPE_EXTERNAL_REVERSAL
  };

enum V1StrategyState
  {
   V1_STRATEGY_PLANNED=0,
   V1_STRATEGY_WAITING_TRIGGER,
   V1_STRATEGY_PENDING,
   V1_STRATEGY_FILLED,
   V1_STRATEGY_CANCELED,
   V1_STRATEGY_NO_TRADE
  };

struct V1MapControl
  {
   string            h1_owner_id;
   datetime          h1_owner_started_at;
   string            m30_owner_id;
   datetime          m30_owner_started_at;

   string            reversal_reference_id;
   string            reversal_reference_owner_id;
   int               reversal_reference_side;
   double            reversal_reference_price;
   datetime          reversal_reference_available_at;

   int               reversal_permission;
   datetime          reversal_permission_opened_at;
   int               reversal_permission_event_type;
   string            permission_reference_id;
   double            permission_reference_price;

   datetime          last_permission_closed_at;
   string            last_permission_close_reason;
   string            last_closed_permission_reference_id;
   datetime          last_closed_permission_opened_at;

   string            last_snapshot_signature;
  };

struct V1SourceZone
  {
   bool              valid;
   string            id;
   int               kind;
   ENUM_TIMEFRAMES   tf;
   int               direction;

   double            bottom;
   double            top;
   double            origin_open;
   double            origin_close;

   int               origin_index;
   datetime          origin_time;
   datetime          occurred_at;
   datetime          available_at;
   datetime          origin_window_start;
   datetime          origin_window_end;

   string            origin_wave_id;
   string            meaningful_swing_id;
   string            linked_structure_event_id;

   string            parent_zone_id;
   string            root_zone_id;
   string            scenario_owner_id;

   string            containment_type;
   int               linked_event_type;
   datetime          linked_event_bar_open;

   int               strategy_state;
   datetime          invalidated_at;
   string            invalidation_reason;
  };

struct V1WaveRef
  {
   bool       valid;
   bool       is_wave;
   bool       liquidity_registered;
   string     id;
   int        side;
   double     price;
   double     wick_bottom;
   double     wick_top;
   datetime   occurred_at;
   datetime   confirmed_at;
   datetime   available_at;

   // Deterministic swing-origin window used by Root/child OB discovery.
   datetime   origin_window_start;
   datetime   origin_window_end;
  };

struct V1RefinementEvent
  {
   bool              valid;
   int               event_type;
   int               direction;
   datetime          available_at;
   MqlRates          break_bar;
   V1WaveRef         meaningful_wave;
   string            event_id;
  };

struct V1ChildCandidate
  {
   bool              valid;
   ENUM_TIMEFRAMES   tf;
   int               direction;

   double            bottom;
   double            top;
   double            origin_open;
   double            origin_close;

   datetime          origin_time;
   datetime          available_at;
   datetime          origin_window_start;
   datetime          origin_window_end;

   V1WaveRef         meaningful_wave;
   int               linked_event_type;
   datetime          linked_event_bar_open;
   double            linked_event_close;
   string            linked_structure_event_id;
   string            containment_type;
  };

struct V1RefinementLineage
  {
   bool              valid;
   string            root_zone_id;
   string            final_child_id;
   string            path;
   int               child_count;
   int               status;
   datetime          frozen_at;
   datetime          snapshot_at;
   string            stop_reason;

   // Phase 4B audit: a source touched before PLAN freeze can never be
   // retrospectively converted into a new scenario.
   datetime          preplan_contact_at;
  };

struct V1ObjectiveCandidate
  {
   bool              valid;
   string            scenario_id;
   string            id;
   string            liquidity_id;
   int               family;
   ENUM_TIMEFRAMES   tf;
   int               side;
   double            price;
   datetime          available_at;
   int               order_index;
   bool              consumed;
   datetime          consumed_at;
  };

struct V1ScenarioPlan
  {
   bool              valid;
   string            id;
   int               strategy_state;
   int               scope;
   int               direction;

   ENUM_TIMEFRAMES   active_map_tf;
   string            owner_id;
   string            parent_context_id;

   int               h1_trend_at_freeze;
   string            h1_owner_id_at_freeze;
   int               m30_trend_at_freeze;
   string            m30_owner_id_at_freeze;
   int               reversal_permission_at_freeze;

   string            permission_reference_id;
   datetime          permission_opened_at;

   string            root_zone_id;
   string            final_source_id;
   ENUM_TIMEFRAMES   source_tf;
   double            source_bottom;
   double            source_top;

   double            map_range_low;
   double            map_range_high;
   double            map_eq;

   datetime          frozen_at;
   datetime          plan_reference_bar_open;
   double            plan_reference_price;
   double            primary_directional_horizon;
   int               objective_count;

   datetime          canceled_at;
   string            cancel_reason;
  };

struct V1ScenarioDraft
  {
   bool              valid;
   int               refinement_index;
   string            context_key;
   int               scope;
   int               direction;
   ENUM_TIMEFRAMES   active_map_tf;
   string            owner_id;
   string            parent_context_id;
   string            permission_reference_id;
   datetime          permission_opened_at;
   string            root_zone_id;
   string            final_source_id;
   double            range_low;
   double            range_high;
   double            eq;
  };

struct V1StructureState
  {
   ENUM_TIMEFRAMES tf;
   string          name;
   int             seconds;

   int             trend;
   int             transition_bias;
   datetime        transition_started_at;

   // Directional owner identity is created only by INITIAL_BOS and remains
   // stable across continuation BOS until the protected boundary is broken.
   string          owner_id;
   datetime        owner_started_at;

   // Compact working-set references. Historical wave trees are not retained.
   V1WaveRef       last_wave;
   V1WaveRef       neutral_high;
   V1WaveRef       neutral_low;
   V1WaveRef       external_high;
   V1WaveRef       external_low;
   V1WaveRef       protected_high;
   V1WaveRef       protected_low;
   V1WaveRef       break_reference;

   // Causal correction extremes after the current break reference occurred.
   V1WaveRef       correction_high;
   V1WaveRef       correction_low;

   double          range_high;
   double          range_low;

   // Bars needed only for 3-candle wave confirmation.
   MqlRates        recent0; // oldest of retained bars
   MqlRates        recent1;
   int             recent_count;

   // Causal-leg search starts on the bar after the prior wave occurrence.
   bool            leg_initialized;
   datetime        leg_start_time;

   // Rolling confirmed-wave window used only for the deterministic
   // four-wave DEFENDED_RANGE_EDGE detector.
   V1WaveRef       range_wave0;
   V1WaveRef       range_wave1;
   V1WaveRef       range_wave2;
   V1WaveRef       range_wave3;
   int             range_wave_count;

   long            processed_bars;
   long            confirmed_waves;
   long            structure_events;
  };

struct V1LiquidityPool
  {
   bool              valid;
   string            id;
   int               family;
   ENUM_TIMEFRAMES   tf;
   int               side;

   double            bottom;
   double            top;

   string            source_id;
   string            source_reason;

   datetime          occurred_at;
   datetime          available_at;

   bool              consumed;
   datetime          consumed_at;
   int               consumption_type;
  };

struct V1RuntimeBarEvent
  {
   int       tf_index;
   MqlRates  bar;
   datetime  available_at;
  };

// Frozen processing priority:
// H4 -> H1 -> M30 -> M15 -> M5 -> M1 -> authorization.
#define V1_TF_COUNT 6
ENUM_TIMEFRAMES g_timeframes[V1_TF_COUNT]=
  {
   PERIOD_H4,
   PERIOD_H1,
   PERIOD_M30,
   PERIOD_M15,
   PERIOD_M5,
   PERIOD_M1
  };

V1StructureState g_structure[V1_TF_COUNT];
V1LiquidityPool g_liquidity[];
V1SourceZone     g_sources[];
V1RefinementLineage g_refinements[];
string           g_pending_refinement_root_ids[];
V1ObjectiveCandidate g_objective_candidates[];
V1ScenarioPlan   g_scenarios[];
V1MapControl      g_map;
string            g_scenario_layer_signature="";
datetime         g_last_current_open[V1_TF_COUNT];
bool             g_cursor_bar_pending[V1_TF_COUNT];
datetime         g_history_first_date[V1_TF_COUNT];

V1InitState      g_init_state=V1_INIT_SYNCING;
datetime         g_bootstrap_ready_at=0;
datetime         g_execution_epoch_start=0;

int              g_log_handle=INVALID_HANDLE;
bool             g_bootstrap_started=false;
bool             g_bootstrap_finished=false;
bool             g_in_bootstrap_replay=false;

long             g_liquidity_created=0;
long             g_liquidity_sweeps=0;
long             g_liquidity_body_deliveries=0;
long             g_roots_created=0;
long             g_roots_price_invalidated=0;
long             g_roots_structure_invalidated=0;
long             g_children_created=0;
long             g_children_invalidated=0;
long             g_refinements_ready=0;
long             g_refinements_no_child=0;
long             g_refinements_ambiguous=0;
long             g_reference_touches=0;
long             g_reference_sweeps=0;
long             g_reference_continuations=0;
long             g_permission_opens=0;
long             g_permission_closes=0;
long             g_scenarios_planned=0;
long             g_scenarios_canceled=0;
long             g_scenarios_ambiguous=0;
long             g_scenarios_no_objective=0;
long             g_scenarios_precontact_rejected=0;
long             g_objective_candidates_frozen=0;

//+------------------------------------------------------------------+
//| Helpers                                                          |
//+------------------------------------------------------------------+
string TfName(const ENUM_TIMEFRAMES tf)
  {
   switch(tf)
     {
      case PERIOD_H4:  return "H4";
      case PERIOD_H1:  return "H1";
      case PERIOD_M30: return "M30";
      case PERIOD_M15: return "M15";
      case PERIOD_M5:  return "M5";
      case PERIOD_M1:  return "M1";
     }
   return EnumToString(tf);
  }

string TrendName(const int trend)
  {
   switch(trend)
     {
      case V1_TREND_BULLISH:    return "BULLISH";
      case V1_TREND_BEARISH:    return "BEARISH";
      case V1_TREND_TRANSITION: return "TRANSITION";
     }
   return "NEUTRAL";
  }

string SideName(const int side)
  {
   if(side==V1_SIDE_HIGH)
      return "HIGH";
   if(side==V1_SIDE_LOW)
      return "LOW";
   return "NONE";
  }

string EventName(const int event_type)
  {
   switch(event_type)
     {
      case V1_EVENT_INITIAL_BOS:    return "INITIAL_BOS";
      case V1_EVENT_BOS:            return "BOS";
      case V1_EVENT_PROTECTED_BREAK:return "PROTECTED_BREAK";
     }
   return "NONE";
  }

string LiquidityFamilyName(const int family)
  {
   switch(family)
     {
      case V1_LIQ_EXTERNAL_SWING:       return "EXTERNAL_SWING";
      case V1_LIQ_DEFENDED_RANGE_EDGE: return "DEFENDED_RANGE_EDGE";
      case V1_LIQ_STRUCTURAL_REACTION: return "STRUCTURAL_REACTION";
     }
   return "UNKNOWN";
  }

string LiquidityConsumptionName(const int consumption)
  {
   switch(consumption)
     {
      case V1_LIQ_CONSUME_SWEEP:         return "SWEEP";
      case V1_LIQ_CONSUME_BODY_DELIVERY: return "BODY_DELIVERY";
     }
   return "NONE";
  }

string SourceKindName(const int kind)
  {
   switch(kind)
     {
      case V1_SOURCE_ROOT:  return "ROOT";
      case V1_SOURCE_CHILD: return "CHILD";
     }
   return "UNKNOWN";
  }


string DirectionName(const int direction)
  {
   if(direction>0)
      return "LONG";
   if(direction<0)
      return "SHORT";
   return "NONE";
  }

bool IsRootTimeframeIndex(const int tf_index)
  {
   return (tf_index==1 || tf_index==2 || tf_index==3);
  }

bool IsRefinementTimeframe(const ENUM_TIMEFRAMES tf)
  {
   return (tf==PERIOD_M30 || tf==PERIOD_M15 || tf==PERIOD_M5);
  }

int TimeframeHierarchyRank(const ENUM_TIMEFRAMES tf)
  {
   if(tf==PERIOD_H1)  return 1;
   if(tf==PERIOD_M30) return 2;
   if(tf==PERIOD_M15) return 3;
   if(tf==PERIOD_M5)  return 4;
   if(tf==PERIOD_M1)  return 5;
   return 0;
  }

string RefinementStatusName(const int status)
  {
   switch(status)
     {
      case V1_REFINE_WAITING:           return "WAITING";
      case V1_REFINE_READY:             return "READY";
      case V1_REFINE_NO_CHILD:          return "NO_CHILD";
      case V1_REFINE_AMBIGUOUS_FIRST:   return "AMBIGUOUS_FIRST";
      case V1_REFINE_STOPPED_AMBIGUOUS: return "STOPPED_AMBIGUOUS";
      case V1_REFINE_INVALIDATED:       return "INVALIDATED";
     }
   return "UNKNOWN";
  }

string ReversalPermissionName(const int permission)
  {
   switch(permission)
     {
      case V1_REVERSAL_OPEN_FOR_LONG:  return "OPEN_FOR_LONG";
      case V1_REVERSAL_OPEN_FOR_SHORT: return "OPEN_FOR_SHORT";
     }
   return "CLOSED";
  }

string ReferenceEventName(const int event_type)
  {
   switch(event_type)
     {
      case V1_REFERENCE_TOUCH:                   return "TOUCH";
      case V1_REFERENCE_SWEEP_REJECTION:         return "SWEEP_REJECTION";
      case V1_REFERENCE_CONTINUATION_BODY_BREAK: return "CONTINUATION_BODY_BREAK";
     }
   return "NONE";
  }


string ScenarioScopeName(const int scope)
  {
   if(scope==V1_SCOPE_EXTERNAL_CONTINUATION)
      return "EXTERNAL_CONTINUATION";
   if(scope==V1_SCOPE_EXTERNAL_REVERSAL)
      return "EXTERNAL_REVERSAL";
   return "NONE";
  }

string StrategyStateName(const int state)
  {
   switch(state)
     {
      case V1_STRATEGY_PLANNED:         return "PLANNED";
      case V1_STRATEGY_WAITING_TRIGGER: return "WAITING_TRIGGER";
      case V1_STRATEGY_PENDING:         return "PENDING";
      case V1_STRATEGY_FILLED:          return "FILLED";
      case V1_STRATEGY_CANCELED:        return "CANCELED";
      case V1_STRATEGY_NO_TRADE:        return "NO_TRADE";
     }
   return "UNKNOWN";
  }

bool IsMatureDirectionalTrend(const int trend)
  {
   return (trend==V1_TREND_BULLISH || trend==V1_TREND_BEARISH);
  }

int TrendDirection(const int trend)
  {
   if(trend==V1_TREND_BULLISH)
      return 1;
   if(trend==V1_TREND_BEARISH)
      return -1;
   return 0;
  }

string InitStateName(const V1InitState state)
  {
   switch(state)
     {
      case V1_INIT_SYNCING:                     return "INIT_SYNCING";
      case V1_INIT_H4_INDEX:                    return "INIT_H4_INDEX";
      case V1_INIT_ACTIVE_MAP:                  return "INIT_ACTIVE_MAP";
      case V1_INIT_SOURCE_CONTEXT:              return "INIT_SOURCE_CONTEXT";
      case V1_READY:                            return "READY";
      case V1_INIT_EXECUTION_RECOVERY_REQUIRED: return "INIT_EXECUTION_RECOVERY_REQUIRED";
      case V1_INIT_ERROR:                       return "INIT_ERROR";
     }
   return "UNKNOWN";
  }

void ResetMapControl()
  {
   g_map.h1_owner_id="";
   g_map.h1_owner_started_at=0;
   g_map.m30_owner_id="";
   g_map.m30_owner_started_at=0;

   g_map.reversal_reference_id="";
   g_map.reversal_reference_owner_id="";
   g_map.reversal_reference_side=V1_SIDE_NONE;
   g_map.reversal_reference_price=0.0;
   g_map.reversal_reference_available_at=0;

   g_map.reversal_permission=V1_REVERSAL_CLOSED;
   g_map.reversal_permission_opened_at=0;
   g_map.reversal_permission_event_type=V1_REFERENCE_NONE;
   g_map.permission_reference_id="";
   g_map.permission_reference_price=0.0;

   g_map.last_permission_closed_at=0;
   g_map.last_permission_close_reason="";
   g_map.last_closed_permission_reference_id="";
   g_map.last_closed_permission_opened_at=0;

   g_map.last_snapshot_signature="";
  }

void ClearWave(V1WaveRef &wave)
  {
   wave.valid=false;
   wave.is_wave=false;
   wave.liquidity_registered=false;
   wave.id="";
   wave.side=V1_SIDE_NONE;
   wave.price=0.0;
   wave.wick_bottom=0.0;
   wave.wick_top=0.0;
   wave.occurred_at=0;
   wave.confirmed_at=0;
   wave.available_at=0;
   wave.origin_window_start=0;
   wave.origin_window_end=0;
  }

void CopyWave(const V1WaveRef &src,V1WaveRef &dst)
  {
   dst.valid=src.valid;
   dst.is_wave=src.is_wave;
   dst.liquidity_registered=src.liquidity_registered;
   dst.id=src.id;
   dst.side=src.side;
   dst.price=src.price;
   dst.wick_bottom=src.wick_bottom;
   dst.wick_top=src.wick_top;
   dst.occurred_at=src.occurred_at;
   dst.confirmed_at=src.confirmed_at;
   dst.available_at=src.available_at;
   dst.origin_window_start=src.origin_window_start;
   dst.origin_window_end=src.origin_window_end;
  }


int CandleColour(const MqlRates &bar)
  {
   if(bar.close>bar.open)
      return 1;
   if(bar.close<bar.open)
      return -1;
   return 0;
  }


void LogLine(const string event_name,
             const string tf,
             const datetime available_at,
             const string object_id,
             const string detail)
  {
   if(g_in_bootstrap_replay && !InpLogBootstrapEvents)
     {
      bool high_volume=
         (event_name=="WAVE_CONFIRMED" ||
          event_name=="STRUCTURE_INITIAL_BOS" ||
          event_name=="STRUCTURE_BOS" ||
          event_name=="STRUCTURE_PROTECTED_BREAK" ||
          event_name=="LIQUIDITY_CREATED" ||
          event_name=="LIQUIDITY_SWEEP" ||
          event_name=="LIQUIDITY_BODY_DELIVERY" ||
          event_name=="ROOT_CREATED" ||
          event_name=="ROOT_INVALIDATED" ||
          event_name=="ROOT_REJECTED" ||
          event_name=="MAP_STATE" ||
          event_name=="REVERSAL_REFERENCE_SET" ||
          event_name=="REVERSAL_REFERENCE_CLEARED" ||
          event_name=="REVERSAL_REFERENCE_EVENT" ||
          event_name=="REVERSAL_PERMISSION_STATE");

      if(high_volume)
         return;
     }

   if(InpVerboseLog)
      PrintFormat("MentorV1 [%s] tf=%s available=%s id=%s %s",
                  event_name,
                  tf,
                  TimeToString(available_at,TIME_DATE|TIME_SECONDS),
                  object_id,
                  detail);

   if(!InpWriteEventCsv || g_log_handle==INVALID_HANDLE)
      return;

   FileWrite(g_log_handle,
             TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),
             event_name,
             tf,
             TimeToString(available_at,TIME_DATE|TIME_SECONDS),
             object_id,
             detail);
   FileFlush(g_log_handle);
  }

void LogStateSnapshot(const int tf_index,const datetime available_at,const string reason)
  {
   if(g_in_bootstrap_replay && !InpLogBootstrapEvents && reason=="PROTECTED_BREAK")
      return;

   string detail=StringFormat(
      "reason=%s trend=%s owner_id=%s owner_started_at=%s range_low=%.10f range_high=%.10f protected_low=%s protected_high=%s external_low=%s external_high=%s break_reference=%s",
      reason,
      TrendName(g_structure[tf_index].trend),
      g_structure[tf_index].owner_id=="" ? "NA" : g_structure[tf_index].owner_id,
      g_structure[tf_index].owner_started_at>0 ? TimeToString(g_structure[tf_index].owner_started_at,TIME_DATE|TIME_SECONDS) : "NA",
      g_structure[tf_index].range_low,
      g_structure[tf_index].range_high,
      g_structure[tf_index].protected_low.valid ? DoubleToString(g_structure[tf_index].protected_low.price,_Digits) : "NA",
      g_structure[tf_index].protected_high.valid ? DoubleToString(g_structure[tf_index].protected_high.price,_Digits) : "NA",
      g_structure[tf_index].external_low.valid ? DoubleToString(g_structure[tf_index].external_low.price,_Digits) : "NA",
      g_structure[tf_index].external_high.valid ? DoubleToString(g_structure[tf_index].external_high.price,_Digits) : "NA",
      g_structure[tf_index].break_reference.valid ? DoubleToString(g_structure[tf_index].break_reference.price,_Digits) : "NA");
   LogLine("STRUCTURE_STATE",g_structure[tf_index].name,available_at,"",detail);
  }

void ResetStructureState(V1StructureState &s,const ENUM_TIMEFRAMES tf)
  {
   s.tf=tf;
   s.name=TfName(tf);
   s.seconds=PeriodSeconds(tf);
   s.trend=V1_TREND_NEUTRAL;
   s.transition_bias=0;
   s.transition_started_at=0;
   s.owner_id="";
   s.owner_started_at=0;

   ClearWave(s.last_wave);
   ClearWave(s.neutral_high);
   ClearWave(s.neutral_low);
   ClearWave(s.external_high);
   ClearWave(s.external_low);
   ClearWave(s.protected_high);
   ClearWave(s.protected_low);
   ClearWave(s.break_reference);
   ClearWave(s.correction_high);
   ClearWave(s.correction_low);

   s.range_high=0.0;
   s.range_low=0.0;

   ZeroMemory(s.recent0);
   ZeroMemory(s.recent1);
   s.recent_count=0;

   s.leg_initialized=false;
   s.leg_start_time=0;

   ClearWave(s.range_wave0);
   ClearWave(s.range_wave1);
   ClearWave(s.range_wave2);
   ClearWave(s.range_wave3);
   s.range_wave_count=0;

   s.processed_bars=0;
   s.confirmed_waves=0;
   s.structure_events=0;
  }

void InitStructureState(const int tf_index)
  {
   ResetStructureState(g_structure[tf_index],g_timeframes[tf_index]);
  }

void InitializeAllStructureStates()
  {
   ArrayResize(g_liquidity,0);
   ArrayResize(g_sources,0);
   ArrayResize(g_refinements,0);
   ArrayResize(g_pending_refinement_root_ids,0);
   ArrayResize(g_objective_candidates,0);
   ArrayResize(g_scenarios,0);
   g_scenario_layer_signature="";
   g_liquidity_created=0;
   g_liquidity_sweeps=0;
   g_liquidity_body_deliveries=0;
   g_roots_created=0;
   g_roots_price_invalidated=0;
   g_roots_structure_invalidated=0;
   g_children_created=0;
   g_children_invalidated=0;
   g_refinements_ready=0;
   g_refinements_no_child=0;
   g_refinements_ambiguous=0;
   g_reference_touches=0;
   g_reference_sweeps=0;
   g_reference_continuations=0;
   g_permission_opens=0;
   g_permission_closes=0;
   g_scenarios_planned=0;
   g_scenarios_canceled=0;
   g_scenarios_ambiguous=0;
   g_scenarios_no_objective=0;
   g_scenarios_precontact_rejected=0;
   g_objective_candidates_frozen=0;
   ResetMapControl();

   for(int i=0;i<V1_TF_COUNT;i++)
     {
      InitStructureState(i);
      g_last_current_open[i]=0;
      g_cursor_bar_pending[i]=false;
      g_history_first_date[i]=0;
     }
  }

//+------------------------------------------------------------------+
//| History synchronization                                          |
//+------------------------------------------------------------------+
void KickHistoryRequests()
  {
   for(int i=0;i<V1_TF_COUNT;i++)
     {
      MqlRates probe[];
      ArraySetAsSeries(probe,false);
      ResetLastError();
      CopyRates(_Symbol,g_timeframes[i],0,3,probe);
     }
  }

bool AllSeriesSynchronized()
  {
   bool all_ready=true;
   for(int i=0;i<V1_TF_COUNT;i++)
     {
      long synchronized=0;
      if(!SeriesInfoInteger(_Symbol,g_timeframes[i],SERIES_SYNCHRONIZED,synchronized) ||
         synchronized==0)
        {
         all_ready=false;
         continue;
        }

      long first_date=0;
      if(SeriesInfoInteger(_Symbol,g_timeframes[i],SERIES_FIRSTDATE,first_date))
         g_history_first_date[i]=(datetime)first_date;
     }
   return all_ready;
  }

bool LoadFullRates(const ENUM_TIMEFRAMES tf,MqlRates &rates[])
  {
   long count_long=SeriesInfoInteger(_Symbol,tf,SERIES_BARS_COUNT);
   if(count_long<=0)
      return false;

   int count=(count_long>2000000000 ? 2000000000 : (int)count_long);
   ArrayResize(rates,0);
   ArraySetAsSeries(rates,false);

   ResetLastError();
   int copied=CopyRates(_Symbol,tf,0,count,rates);
   if(copied<=1)
     {
      PrintFormat("MentorV1 bootstrap CopyRates failed tf=%s copied=%d err=%d",
                  TfName(tf),copied,GetLastError());
      return false;
     }

   return true;
  }

int ClosedCount(const MqlRates &rates[],const int seconds,const datetime now)
  {
   int total=ArraySize(rates);
   if(total<=0)
      return 0;

   // If the final element is still the current open bar, exclude it.
   if(rates[total-1].time+seconds>now)
      return total-1;

   // Market can be closed and the last historical bar may already be closed.
   return total;
  }

datetime HistoricalAvailableAt(const MqlRates &rates[],
                               const int index,
                               const int seconds)
  {
   // Closed-bar information becomes causally available at the end of its
   // timeframe slot. A weekend/session gap must NOT delay Friday structure
   // availability until the first Monday bar.
   return rates[index].time+seconds;
  }


//+------------------------------------------------------------------+
//| Liquidity working-set logic                                      |
//+------------------------------------------------------------------+
double LiquidityTickSize()
  {
   double tick=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   if(tick<=0.0)
      tick=_Point;
   return tick;
  }

bool HasOneTickAbove(const double price,const double level)
  {
   double tick=LiquidityTickSize();
   double epsilon=tick*1.0e-6;
   return (price-level)>=tick-epsilon;
  }

bool HasOneTickBelow(const double price,const double level)
  {
   double tick=LiquidityTickSize();
   double epsilon=tick*1.0e-6;
   return (level-price)>=tick-epsilon;
  }

int FindActiveLiquidityById(const string id)
  {
   for(int i=0;i<ArraySize(g_liquidity);i++)
      if(g_liquidity[i].valid && g_liquidity[i].id==id)
         return i;
   return -1;
  }

void RemoveLiquidityAt(const int index)
  {
   int n=ArraySize(g_liquidity);
   if(index<0 || index>=n)
      return;

   if(index<n-1)
      g_liquidity[index]=g_liquidity[n-1];

   ArrayResize(g_liquidity,n-1);
  }

void MarkWaveRegisteredIfMatch(V1WaveRef &wave,const string source_id)
  {
   if(wave.valid && wave.id==source_id)
      wave.liquidity_registered=true;
  }

void MarkAllCurrentWaveCopiesRegistered(const int tf_index,const string source_id)
  {
   MarkWaveRegisteredIfMatch(g_structure[tf_index].last_wave,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].neutral_high,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].neutral_low,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].external_high,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].external_low,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].protected_high,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].protected_low,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].break_reference,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].correction_high,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].correction_low,source_id);

   MarkWaveRegisteredIfMatch(g_structure[tf_index].range_wave0,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].range_wave1,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].range_wave2,source_id);
   MarkWaveRegisteredIfMatch(g_structure[tf_index].range_wave3,source_id);
  }

bool AddLiquidityPool(const int tf_index,
                      const int family,
                      const int side,
                      const double bottom,
                      const double top,
                      const string source_id,
                      const string source_reason,
                      const datetime occurred_at,
                      const datetime available_at,
                      const string explicit_id="")
  {
   if(side!=V1_SIDE_HIGH && side!=V1_SIDE_LOW)
      return false;

   // Frozen D-104: H4 is a long-horizon EXTERNAL_SWING index only.
   if(tf_index==0 && family!=V1_LIQ_EXTERNAL_SWING)
      return false;

   double normalized_bottom=MathMin(bottom,top);
   double normalized_top=MathMax(bottom,top);

   string id=explicit_id;
   if(id=="")
      id=StringFormat("%s:liquidity:%s:%s:%s",
                      TfName(g_timeframes[tf_index]),
                      LiquidityFamilyName(family),
                      SideName(side),
                      source_id);

   if(FindActiveLiquidityById(id)>=0)
      return false;

   int n=ArraySize(g_liquidity);
   if(ArrayResize(g_liquidity,n+1,256)<0)
     {
      LogLine("LIQUIDITY_DETECTOR_ERROR",
              TfName(g_timeframes[tf_index]),
              available_at,
              "",
              "reason=LIQUIDITY_ARRAY_RESIZE_FAILED");
      return false;
     }

   g_liquidity[n].valid=true;
   g_liquidity[n].id=id;
   g_liquidity[n].family=family;
   g_liquidity[n].tf=g_timeframes[tf_index];
   g_liquidity[n].side=side;
   g_liquidity[n].bottom=normalized_bottom;
   g_liquidity[n].top=normalized_top;
   g_liquidity[n].source_id=source_id;
   g_liquidity[n].source_reason=source_reason;
   g_liquidity[n].occurred_at=occurred_at;
   g_liquidity[n].available_at=available_at;
   g_liquidity[n].consumed=false;
   g_liquidity[n].consumed_at=0;
   g_liquidity[n].consumption_type=V1_LIQ_CONSUME_NONE;

   g_liquidity_created++;

   string detail=StringFormat(
      "family=%s side=%s bottom=%.10f top=%.10f source_id=%s source_reason=%s occurred_at=%s available_at=%s",
      LiquidityFamilyName(family),
      SideName(side),
      normalized_bottom,
      normalized_top,
      source_id,
      source_reason,
      TimeToString(occurred_at,TIME_DATE|TIME_SECONDS),
      TimeToString(available_at,TIME_DATE|TIME_SECONDS));

   LogLine("LIQUIDITY_CREATED",
           TfName(g_timeframes[tf_index]),
           available_at,
           id,
           detail);

   return true;
  }

void EnsureExternalSwingLiquidity(const int tf_index,
                                  V1WaveRef &wave,
                                  const datetime rank_available_at,
                                  const string role_reason)
  {
   if(!wave.valid || !wave.is_wave || wave.liquidity_registered)
      return;

   string pool_id=StringFormat("%s:liquidity:EXTERNAL_SWING:%s:%s",
                               TfName(g_timeframes[tf_index]),
                               SideName(wave.side),
                               wave.id);

   if(FindActiveLiquidityById(pool_id)<0)
     {
      AddLiquidityPool(tf_index,
                       V1_LIQ_EXTERNAL_SWING,
                       wave.side,
                       wave.wick_bottom,
                       wave.wick_top,
                       wave.id,
                       role_reason,
                       wave.occurred_at,
                       rank_available_at,
                       pool_id);
     }

   // Mark every live copy, not just this reference. This prevents the same
   // structural reason from being resurrected after the pool is consumed.
   MarkAllCurrentWaveCopiesRegistered(tf_index,wave.id);
  }

void RegisterCurrentExternalLiquidity(const int tf_index,
                                      const datetime available_at)
  {
   // Protected references first so a swing that is both protected and
   // structural external is attributed to the stronger causal reason.
   EnsureExternalSwingLiquidity(tf_index,
                                g_structure[tf_index].protected_high,
                                available_at,
                                "PROTECTED_PROMOTION");
   EnsureExternalSwingLiquidity(tf_index,
                                g_structure[tf_index].protected_low,
                                available_at,
                                "PROTECTED_PROMOTION");
   EnsureExternalSwingLiquidity(tf_index,
                                g_structure[tf_index].external_high,
                                available_at,
                                "EXTERNAL_EXTREME_PROMOTION");
   EnsureExternalSwingLiquidity(tf_index,
                                g_structure[tf_index].external_low,
                                available_at,
                                "EXTERNAL_EXTREME_PROMOTION");
  }

void PushRangeWave(V1StructureState &s,const V1WaveRef &wave)
  {
   if(s.range_wave_count==0)
     {
      CopyWave(wave,s.range_wave0);
      s.range_wave_count=1;
      return;
     }

   if(s.range_wave_count==1)
     {
      CopyWave(wave,s.range_wave1);
      s.range_wave_count=2;
      return;
     }

   if(s.range_wave_count==2)
     {
      CopyWave(wave,s.range_wave2);
      s.range_wave_count=3;
      return;
     }

   if(s.range_wave_count==3)
     {
      CopyWave(wave,s.range_wave3);
      s.range_wave_count=4;
      return;
     }

   CopyWave(s.range_wave1,s.range_wave0);
   CopyWave(s.range_wave2,s.range_wave1);
   CopyWave(s.range_wave3,s.range_wave2);
   CopyWave(wave,s.range_wave3);
   s.range_wave_count=4;
  }

bool RangeBodyContained(const V1StructureState &s,
                        const datetime start_time,
                        const datetime end_time,
                        const double high_outer,
                        const double low_outer)
  {
   MqlRates bars[];
   ArraySetAsSeries(bars,false);

   ResetLastError();
   int copied=CopyRates(_Symbol,s.tf,start_time,end_time,bars);
   if(copied<=0)
     {
      LogLine("LIQUIDITY_DETECTOR_ERROR",
              s.name,
              end_time+s.seconds,
              "",
              StringFormat("reason=RANGE_COPYRATES_FAILED start=%s end=%s error=%d",
                           TimeToString(start_time,TIME_DATE|TIME_SECONDS),
                           TimeToString(end_time,TIME_DATE|TIME_SECONDS),
                           GetLastError()));
      return false;
     }

   for(int i=0;i<copied;i++)
     {
      if(bars[i].close>high_outer || bars[i].close<low_outer)
         return false;
     }

   return true;
  }

void TryCreateDefendedRangeLiquidity(const int tf_index,
                                     const MqlRates &confirmation_bar,
                                     const datetime available_at)
  {
   // H4 archive is intentionally EXTERNAL_SWING-only in V1.
   if(tf_index==0)
      return;

   if(g_structure[tf_index].range_wave_count<4)
      return;

   V1WaveRef high1,high2,low1,low2;
   ClearWave(high1);
   ClearWave(high2);
   ClearWave(low1);
   ClearWave(low2);

   bool pattern_high_first=
      (g_structure[tf_index].range_wave0.side==V1_SIDE_HIGH &&
       g_structure[tf_index].range_wave1.side==V1_SIDE_LOW &&
       g_structure[tf_index].range_wave2.side==V1_SIDE_HIGH &&
       g_structure[tf_index].range_wave3.side==V1_SIDE_LOW);

   bool pattern_low_first=
      (g_structure[tf_index].range_wave0.side==V1_SIDE_LOW &&
       g_structure[tf_index].range_wave1.side==V1_SIDE_HIGH &&
       g_structure[tf_index].range_wave2.side==V1_SIDE_LOW &&
       g_structure[tf_index].range_wave3.side==V1_SIDE_HIGH);

   if(!pattern_high_first && !pattern_low_first)
      return;

   if(pattern_high_first)
     {
      CopyWave(g_structure[tf_index].range_wave0,high1);
      CopyWave(g_structure[tf_index].range_wave2,high2);
      CopyWave(g_structure[tf_index].range_wave1,low1);
      CopyWave(g_structure[tf_index].range_wave3,low2);
     }
   else
     {
      CopyWave(g_structure[tf_index].range_wave1,high1);
      CopyWave(g_structure[tf_index].range_wave3,high2);
      CopyWave(g_structure[tf_index].range_wave0,low1);
      CopyWave(g_structure[tf_index].range_wave2,low2);
     }

   double high_bottom=MathMax(high1.wick_bottom,high2.wick_bottom);
   double high_top=MathMin(high1.wick_top,high2.wick_top);
   double low_bottom=MathMax(low1.wick_bottom,low2.wick_bottom);
   double low_top=MathMin(low1.wick_top,low2.wick_top);

   if(high_top<high_bottom || low_top<low_bottom)
      return;

   // The defended box must remain body-contained through the fourth
   // confirmation bar. Physical wick excursions alone do not disqualify it.
   if(!RangeBodyContained(g_structure[tf_index],
                          g_structure[tf_index].range_wave0.occurred_at,
                          confirmation_bar.time,
                          high_top,
                          low_bottom))
      return;

   string source_id=StringFormat("range:%s|%s|%s|%s",
                                 g_structure[tf_index].range_wave0.id,
                                 g_structure[tf_index].range_wave1.id,
                                 g_structure[tf_index].range_wave2.id,
                                 g_structure[tf_index].range_wave3.id);

   datetime occurred_at=g_structure[tf_index].range_wave3.occurred_at;

   AddLiquidityPool(tf_index,
                    V1_LIQ_DEFENDED_RANGE_EDGE,
                    V1_SIDE_HIGH,
                    high_bottom,
                    high_top,
                    source_id,
                    "FOUR_WAVE_DEFENDED_RANGE",
                    occurred_at,
                    available_at);

   AddLiquidityPool(tf_index,
                    V1_LIQ_DEFENDED_RANGE_EDGE,
                    V1_SIDE_LOW,
                    low_bottom,
                    low_top,
                    source_id,
                    "FOUR_WAVE_DEFENDED_RANGE",
                    occurred_at,
                    available_at);
  }

void LogLiquidityConsumption(const V1LiquidityPool &pool,
                             const MqlRates &bar,
                             const datetime available_at,
                             const int consumption_type)
  {
   double outer=(pool.side==V1_SIDE_HIGH ? pool.top : pool.bottom);
   double extreme=(pool.side==V1_SIDE_HIGH ? bar.high : bar.low);
   double tick=LiquidityTickSize();
   double penetration_ticks=
      (pool.side==V1_SIDE_HIGH ?
       (bar.high-pool.top)/tick :
       (pool.bottom-bar.low)/tick);

   string detail=StringFormat(
      "family=%s side=%s bottom=%.10f top=%.10f outer=%.10f pool_available_at=%s bar_open=%s high=%.10f low=%.10f close=%.10f extreme=%.10f penetration_ticks=%.4f consumption=%s",
      LiquidityFamilyName(pool.family),
      SideName(pool.side),
      pool.bottom,
      pool.top,
      outer,
      TimeToString(pool.available_at,TIME_DATE|TIME_SECONDS),
      TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
      bar.high,
      bar.low,
      bar.close,
      extreme,
      penetration_ticks,
      LiquidityConsumptionName(consumption_type));

   LogLine(consumption_type==V1_LIQ_CONSUME_SWEEP ?
              "LIQUIDITY_SWEEP" :
              "LIQUIDITY_BODY_DELIVERY",
           TfName(pool.tf),
           available_at,
           pool.id,
           detail);
  }

void EvaluateLiquidityConsumption(const int tf_index,
                                  const MqlRates &bar,
                                  const datetime available_at)
  {
   ENUM_TIMEFRAMES tf=g_timeframes[tf_index];

   int i=0;
   while(i<ArraySize(g_liquidity))
     {
      if(!g_liquidity[i].valid ||
         g_liquidity[i].tf!=tf ||
         g_liquidity[i].available_at>=available_at)
        {
         i++;
         continue;
        }

      int consumption=V1_LIQ_CONSUME_NONE;

      if(g_liquidity[i].side==V1_SIDE_HIGH)
        {
         if(bar.close>g_liquidity[i].top)
            consumption=V1_LIQ_CONSUME_BODY_DELIVERY;
         else if(HasOneTickAbove(bar.high,g_liquidity[i].top) &&
                 bar.close<=g_liquidity[i].top)
            consumption=V1_LIQ_CONSUME_SWEEP;
        }
      else if(g_liquidity[i].side==V1_SIDE_LOW)
        {
         if(bar.close<g_liquidity[i].bottom)
            consumption=V1_LIQ_CONSUME_BODY_DELIVERY;
         else if(HasOneTickBelow(bar.low,g_liquidity[i].bottom) &&
                 bar.close>=g_liquidity[i].bottom)
            consumption=V1_LIQ_CONSUME_SWEEP;
        }

      if(consumption==V1_LIQ_CONSUME_NONE)
        {
         i++;
         continue;
        }

      g_liquidity[i].consumed=true;
      g_liquidity[i].consumed_at=available_at;
      g_liquidity[i].consumption_type=consumption;

      LogLiquidityConsumption(g_liquidity[i],bar,available_at,consumption);

      if(consumption==V1_LIQ_CONSUME_SWEEP)
         g_liquidity_sweeps++;
      else
         g_liquidity_body_deliveries++;

      // Active-memory compression: consumed liquidity leaves the working set.
      // The event log remains the audit ledger.
      RemoveLiquidityAt(i);
     }
  }

int CountActiveLiquidity(const ENUM_TIMEFRAMES tf,const int family=-1)
  {
   int count=0;
   for(int i=0;i<ArraySize(g_liquidity);i++)
     {
      if(!g_liquidity[i].valid || g_liquidity[i].tf!=tf)
         continue;
      if(family>=0 && g_liquidity[i].family!=family)
         continue;
      count++;
     }
   return count;
  }

void LogLiquiditySnapshot(const int tf_index,const datetime available_at)
  {
   ENUM_TIMEFRAMES tf=g_timeframes[tf_index];

   int external_count=CountActiveLiquidity(tf,V1_LIQ_EXTERNAL_SWING);
   int range_count=CountActiveLiquidity(tf,V1_LIQ_DEFENDED_RANGE_EDGE);
   int reaction_count=CountActiveLiquidity(tf,V1_LIQ_STRUCTURAL_REACTION);

   string detail=StringFormat(
      "active_total=%d external_swing=%d defended_range_edge=%d structural_reaction=%d structural_reaction_status=%s",
      external_count+range_count+reaction_count,
      external_count,
      range_count,
      reaction_count,
      "WAITING_ROOT_SOURCE_LAYER");

   LogLine("LIQUIDITY_STATE",
           TfName(tf),
           available_at,
           "",
           detail);
  }

bool BuildRefinementForRoot(const string root_id,const datetime snapshot_at);
void BuildRefinementsForActiveRoots(const datetime snapshot_at);
void QueueRefinementRoot(const string root_id);
void ProcessPendingRefinements(const datetime snapshot_at);

//+------------------------------------------------------------------+
//| Phase 3B Root/source working-set logic                           |
//+------------------------------------------------------------------+
int FindActiveSourceById(const string id)
  {
   for(int i=0;i<ArraySize(g_sources);i++)
     {
      if(g_sources[i].valid &&
         g_sources[i].strategy_state==V1_SOURCE_ACTIVE &&
         g_sources[i].id==id)
         return i;
     }
   return -1;
  }

void RemoveSourceAt(const int index)
  {
   int n=ArraySize(g_sources);
   if(index<0 || index>=n)
      return;

   for(int i=index;i<n-1;i++)
      g_sources[i]=g_sources[i+1];

   ArrayResize(g_sources,n-1);
  }

bool SourcePathHasSessionGap(const ENUM_TIMEFRAMES tf,
                             const datetime start_time,
                             const datetime end_time)
  {
   if(start_time<=0 || end_time<=start_time)
      return false;

   MqlRates bars[];
   ArraySetAsSeries(bars,false);
   ResetLastError();
   int copied=CopyRates(_Symbol,tf,start_time,end_time,bars);
   if(copied<=0)
     {
      LogLine("SOURCE_DETECTOR_ERROR",
              TfName(tf),
              end_time+PeriodSeconds(tf),
              "",
              StringFormat("reason=ROOT_CAUSAL_PATH_COPYRATES_FAILED start=%s end=%s error=%d",
                           TimeToString(start_time,TIME_DATE|TIME_SECONDS),
                           TimeToString(end_time,TIME_DATE|TIME_SECONDS),
                           GetLastError()));
      return true;
     }

   if(copied==1)
      return false;

   int seconds=PeriodSeconds(tf);
   for(int i=1;i<copied;i++)
     {
      if((bars[i].time-bars[i-1].time)!=seconds)
         return true;
     }

   return false;
  }

bool FindLastOppositeCandleInSwingOrigin(const ENUM_TIMEFRAMES tf,
                                         const int direction,
                                         const V1WaveRef &meaningful_wave,
                                         MqlRates &origin_bar)
  {
   if(!meaningful_wave.valid || !meaningful_wave.is_wave)
      return false;

   datetime start_time=meaningful_wave.origin_window_start;
   datetime end_time=meaningful_wave.origin_window_end;

   if(start_time<=0)
      start_time=meaningful_wave.occurred_at;
   if(end_time<=0)
      end_time=meaningful_wave.occurred_at;
   if(end_time<start_time)
      return false;

   MqlRates bars[];
   ArraySetAsSeries(bars,false);

   ResetLastError();
   int copied=CopyRates(_Symbol,tf,start_time,end_time,bars);
   if(copied<=0)
     {
      LogLine("SOURCE_DETECTOR_ERROR",
              TfName(tf),
              end_time+PeriodSeconds(tf),
              meaningful_wave.id,
              StringFormat("reason=ROOT_ORIGIN_COPYRATES_FAILED start=%s end=%s error=%d",
                           TimeToString(start_time,TIME_DATE|TIME_SECONDS),
                           TimeToString(end_time,TIME_DATE|TIME_SECONDS),
                           GetLastError()));
      return false;
     }

   for(int i=copied-1;i>=0;i--)
     {
      int colour=CandleColour(bars[i]);

      if(direction>0 && colour<0)
        {
         origin_bar=bars[i];
         return true;
        }

      if(direction<0 && colour>0)
        {
         origin_bar=bars[i];
         return true;
        }
     }

   return false;
  }

string BuildStructureEventId(const V1StructureState &s,
                             const int event_type,
                             const MqlRates &bar)
  {
   return StringFormat("%s:structure:%s:%I64d",
                       s.name,
                       EventName(event_type),
                       (long)bar.time);
  }

void LogRootCreated(const V1SourceZone &root,
                    const int event_type,
                    const MqlRates &break_bar)
  {
   string detail=StringFormat(
      "kind=ROOT state=ACTIVE direction=%s source_reason=LAST_OPPOSITE_OB bottom=%.10f top=%.10f origin_open=%.10f origin_close=%.10f origin_index=%d origin_time=%s origin_window_start=%s origin_window_end=%s origin_wave_id=%s linked_event_type=%s linked_structure_event_id=%s break_bar_open=%s break_close=%.10f root_zone_id=%s scenario_owner_id=%s scenario_authority=false same_session_causal_path=true",
      DirectionName(root.direction),
      root.bottom,
      root.top,
      root.origin_open,
      root.origin_close,
      root.origin_index,
      TimeToString(root.origin_time,TIME_DATE|TIME_SECONDS),
      TimeToString(root.origin_window_start,TIME_DATE|TIME_SECONDS),
      TimeToString(root.origin_window_end,TIME_DATE|TIME_SECONDS),
      root.origin_wave_id,
      EventName(event_type),
      root.linked_structure_event_id,
      TimeToString(break_bar.time,TIME_DATE|TIME_SECONDS),
      break_bar.close,
      root.root_zone_id,
      root.scenario_owner_id=="" ? "UNBOUND" : root.scenario_owner_id);

   LogLine("ROOT_CREATED",
           TfName(root.tf),
           root.available_at,
           root.id,
           detail);
  }

void LogRootRejected(const int tf_index,
                     const datetime available_at,
                     const int event_type,
                     const int direction,
                     const string reason,
                     const string wave_id)
  {
   if(!IsRootTimeframeIndex(tf_index))
      return;

   string detail=StringFormat(
      "direction=%s event_type=%s reason=%s origin_wave_id=%s",
      DirectionName(direction),
      EventName(event_type),
      reason,
      wave_id=="" ? "NA" : wave_id);

   LogLine("ROOT_REJECTED",
           TfName(g_timeframes[tf_index]),
           available_at,
           "",
           detail);
  }

bool AddRootFromStructureEvent(const int tf_index,
                               const int event_type,
                               const int direction,
                               const V1WaveRef &meaningful_wave,
                               const MqlRates &break_bar,
                               const datetime available_at)
  {
   if(!IsRootTimeframeIndex(tf_index))
      return false;

   // Phase 3A only promotes Roots from mature directional delivery events.
   // Protected-break/TRANSITION events do not fabricate a new Root because
   // the current event contract does not yet own an unambiguous opposite
   // meaningful swing-origin reference.
   if(event_type!=V1_EVENT_INITIAL_BOS &&
      event_type!=V1_EVENT_BOS)
      return false;

   if(!meaningful_wave.valid || !meaningful_wave.is_wave)
     {
      LogRootRejected(tf_index,
                      available_at,
                      event_type,
                      direction,
                      "NO_CAUSAL_CORRECTION_OR_MEANINGFUL_WAVE",
                      "");
      return false;
     }

   MqlRates origin_bar;
   ZeroMemory(origin_bar);

   if(!FindLastOppositeCandleInSwingOrigin(g_timeframes[tf_index],
                                           direction,
                                           meaningful_wave,
                                           origin_bar))
     {
      LogRootRejected(tf_index,
                      available_at,
                      event_type,
                      direction,
                      "NO_OPPOSITE_CANDLE_IN_ORIGIN_WINDOW",
                      meaningful_wave.id);
      return false;
     }

   // A previous-session opposite candle cannot be attached to a displacement
   // whose causal path crosses a market closure.
   if(SourcePathHasSessionGap(g_timeframes[tf_index],
                              origin_bar.time,
                              break_bar.time))
     {
      LogRootRejected(tf_index,
                      available_at,
                      event_type,
                      direction,
                      "SESSION_GAP_CROSSED",
                      meaningful_wave.id);
      return false;
     }

   string event_id=
      BuildStructureEventId(g_structure[tf_index],event_type,break_bar);

   string root_id=StringFormat("%s:root:%s:%I64d:%s",
                               TfName(g_timeframes[tf_index]),
                               DirectionName(direction),
                               (long)origin_bar.time,
                               event_id);

   if(FindActiveSourceById(root_id)>=0)
     {
      LogRootRejected(tf_index,
                      available_at,
                      event_type,
                      direction,
                      "DUPLICATE_ACTIVE_ROOT",
                      meaningful_wave.id);
      return false;
     }

   int n=ArraySize(g_sources);
   if(ArrayResize(g_sources,n+1,128)<0)
     {
      LogLine("SOURCE_DETECTOR_ERROR",
              TfName(g_timeframes[tf_index]),
              available_at,
              "",
              "reason=SOURCE_ARRAY_RESIZE_FAILED");
      return false;
     }

   g_sources[n].valid=true;
   g_sources[n].id=root_id;
   g_sources[n].kind=V1_SOURCE_ROOT;
   g_sources[n].tf=g_timeframes[tf_index];
   g_sources[n].direction=direction;
   g_sources[n].bottom=origin_bar.low;
   g_sources[n].top=origin_bar.high;
   g_sources[n].origin_open=origin_bar.open;
   g_sources[n].origin_close=origin_bar.close;
   g_sources[n].origin_index=iBarShift(_Symbol,
                                       g_timeframes[tf_index],
                                       origin_bar.time,
                                       true);
   g_sources[n].origin_time=origin_bar.time;
   g_sources[n].occurred_at=origin_bar.time;
   g_sources[n].available_at=available_at;
   g_sources[n].origin_window_start=meaningful_wave.origin_window_start;
   g_sources[n].origin_window_end=meaningful_wave.origin_window_end;
   g_sources[n].origin_wave_id=meaningful_wave.id;
   g_sources[n].meaningful_swing_id=meaningful_wave.id;
   g_sources[n].linked_structure_event_id=event_id;
   g_sources[n].parent_zone_id="";
   g_sources[n].root_zone_id=root_id;
   g_sources[n].scenario_owner_id="";
   g_sources[n].containment_type="ROOT";
   g_sources[n].linked_event_type=event_type;
   g_sources[n].linked_event_bar_open=break_bar.time;
   g_sources[n].strategy_state=V1_SOURCE_ACTIVE;
   g_sources[n].invalidated_at=0;
   g_sources[n].invalidation_reason="";

   g_roots_created++;
   LogRootCreated(g_sources[n],event_type,break_bar);

   if(!g_in_bootstrap_replay)
      QueueRefinementRoot(root_id);

   return true;
  }

void LogRootInvalidated(const V1SourceZone &root,
                        const datetime available_at,
                        const string reason,
                        const MqlRates &bar)
  {
   string detail=StringFormat(
      "kind=%s state=INVALIDATED direction=%s bottom=%.10f top=%.10f close=%.10f bar_open=%s reason=%s linked_structure_event_id=%s origin_wave_id=%s",
      SourceKindName(root.kind),
      DirectionName(root.direction),
      root.bottom,
      root.top,
      bar.close,
      TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
      reason,
      root.linked_structure_event_id,
      root.origin_wave_id);

   LogLine("ROOT_INVALIDATED",
           TfName(root.tf),
           available_at,
           root.id,
           detail);
  }

int FindRefinementByRootId(const string root_id)
  {
   for(int i=0;i<ArraySize(g_refinements);i++)
      if(g_refinements[i].valid && g_refinements[i].root_zone_id==root_id)
         return i;
   return -1;
  }

void MarkRefinementInvalidated(const string root_id,
                               const datetime available_at,
                               const string reason)
  {
   int index=FindRefinementByRootId(root_id);
   if(index<0)
      return;

   if(g_refinements[index].status==V1_REFINE_INVALIDATED)
      return;

   g_refinements[index].status=V1_REFINE_INVALIDATED;
   g_refinements[index].snapshot_at=available_at;
   g_refinements[index].stop_reason=reason;

   LogLine("REFINEMENT_INVALIDATED",
           "",
           available_at,
           root_id,
           StringFormat("status=INVALIDATED final_child_id=%s child_count=%d reason=%s",
                        g_refinements[index].final_child_id=="" ? "NA" : g_refinements[index].final_child_id,
                        g_refinements[index].child_count,
                        reason));
  }

void LogChildInvalidated(const V1SourceZone &child,
                         const datetime available_at,
                         const string reason,
                         const MqlRates &bar)
  {
   string detail=StringFormat(
      "kind=CHILD state=INVALIDATED direction=%s parent_zone_id=%s root_zone_id=%s bottom=%.10f top=%.10f close=%.10f bar_open=%s reason=%s linked_structure_event_id=%s origin_wave_id=%s containment_type=%s",
      DirectionName(child.direction),
      child.parent_zone_id,
      child.root_zone_id,
      child.bottom,
      child.top,
      bar.close,
      TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
      reason,
      child.linked_structure_event_id,
      child.origin_wave_id,
      child.containment_type);

   LogLine("CHILD_INVALIDATED",
           TfName(child.tf),
           available_at,
           child.id,
           detail);
  }

void InvalidateChildDescendants(const string parent_id,
                                const datetime available_at,
                                const string reason,
                                const MqlRates &bar)
  {
   bool found=true;
   while(found)
     {
      found=false;

      for(int i=0;i<ArraySize(g_sources);i++)
        {
         if(!g_sources[i].valid ||
            g_sources[i].kind!=V1_SOURCE_CHILD ||
            g_sources[i].strategy_state!=V1_SOURCE_ACTIVE ||
            g_sources[i].parent_zone_id!=parent_id)
            continue;

         string child_id=g_sources[i].id;
         string root_id=g_sources[i].root_zone_id;

         InvalidateChildDescendants(child_id,available_at,reason,bar);

         int current=FindActiveSourceById(child_id);
         if(current>=0)
           {
            V1SourceZone audit=g_sources[current];
            audit.strategy_state=V1_SOURCE_INVALIDATED;
            audit.invalidated_at=available_at;
            audit.invalidation_reason=reason;
            LogChildInvalidated(audit,available_at,reason,bar);
            RemoveSourceAt(current);
            g_children_invalidated++;
           }

         MarkRefinementInvalidated(root_id,available_at,reason);
         found=true;
         break;
        }
     }
  }

void EvaluateChildPriceInvalidation(const int tf_index,
                                    const MqlRates &bar,
                                    const datetime available_at)
  {
   ENUM_TIMEFRAMES tf=g_timeframes[tf_index];

   bool found=true;
   while(found)
     {
      found=false;

      for(int i=0;i<ArraySize(g_sources);i++)
        {
         if(!g_sources[i].valid ||
            g_sources[i].kind!=V1_SOURCE_CHILD ||
            g_sources[i].tf!=tf ||
            g_sources[i].strategy_state!=V1_SOURCE_ACTIVE ||
            g_sources[i].available_at>=available_at)
            continue;

         bool invalid=false;
         if(g_sources[i].direction>0)
            invalid=(bar.close<g_sources[i].bottom);
         else if(g_sources[i].direction<0)
            invalid=(bar.close>g_sources[i].top);

         if(!invalid)
            continue;

         string child_id=g_sources[i].id;
         string root_id=g_sources[i].root_zone_id;

         InvalidateChildDescendants(child_id,available_at,"PARENT_INVALIDATED",bar);

         int current=FindActiveSourceById(child_id);
         if(current>=0)
           {
            V1SourceZone audit=g_sources[current];
            audit.strategy_state=V1_SOURCE_INVALIDATED;
            audit.invalidated_at=available_at;
            audit.invalidation_reason="PRICE_INVALIDATED";
            LogChildInvalidated(audit,available_at,"PRICE_INVALIDATED",bar);
            RemoveSourceAt(current);
            g_children_invalidated++;
           }

         MarkRefinementInvalidated(root_id,available_at,"PRICE_INVALIDATED");
         found=true;
         break;
        }
     }
  }

void InvalidateRootsForStructureOwner(const int tf_index,
                                      const datetime available_at,
                                      const MqlRates &bar)
  {
   ENUM_TIMEFRAMES tf=g_timeframes[tf_index];

   int i=0;
   while(i<ArraySize(g_sources))
     {
      if(!g_sources[i].valid ||
         g_sources[i].kind!=V1_SOURCE_ROOT ||
         g_sources[i].tf!=tf ||
         g_sources[i].strategy_state!=V1_SOURCE_ACTIVE)
        {
         i++;
         continue;
        }

      string root_id=g_sources[i].id;
      InvalidateChildDescendants(root_id,
                                 available_at,
                                 "PARENT_INVALIDATED",
                                 bar);

      int current=FindActiveSourceById(root_id);
      if(current<0)
         continue;

      g_sources[current].strategy_state=V1_SOURCE_INVALIDATED;
      g_sources[current].invalidated_at=available_at;
      g_sources[current].invalidation_reason="STRUCTURE_INVALIDATED";

      LogRootInvalidated(g_sources[current],
                         available_at,
                         "STRUCTURE_INVALIDATED",
                         bar);
      g_roots_structure_invalidated++;
      MarkRefinementInvalidated(root_id,available_at,"STRUCTURE_INVALIDATED");

      RemoveSourceAt(current);
     }
  }

void EvaluateRootPriceInvalidation(const int tf_index,
                                   const MqlRates &bar,
                                   const datetime available_at)
  {
   if(!IsRootTimeframeIndex(tf_index))
      return;

   ENUM_TIMEFRAMES tf=g_timeframes[tf_index];

   int i=0;
   while(i<ArraySize(g_sources))
     {
      if(!g_sources[i].valid ||
         g_sources[i].kind!=V1_SOURCE_ROOT ||
         g_sources[i].tf!=tf ||
         g_sources[i].strategy_state!=V1_SOURCE_ACTIVE ||
         g_sources[i].available_at>=available_at)
        {
         i++;
         continue;
        }

      bool invalid=false;
      if(g_sources[i].direction>0)
         invalid=(bar.close<g_sources[i].bottom);
      else if(g_sources[i].direction<0)
         invalid=(bar.close>g_sources[i].top);

      if(!invalid)
        {
         i++;
         continue;
        }

      string root_id=g_sources[i].id;
      InvalidateChildDescendants(root_id,
                                 available_at,
                                 "PARENT_INVALIDATED",
                                 bar);

      int current=FindActiveSourceById(root_id);
      if(current<0)
         continue;

      g_sources[current].strategy_state=V1_SOURCE_INVALIDATED;
      g_sources[current].invalidated_at=available_at;
      g_sources[current].invalidation_reason="PRICE_INVALIDATED";

      LogRootInvalidated(g_sources[current],
                         available_at,
                         "PRICE_INVALIDATED",
                         bar);
      g_roots_price_invalidated++;
      MarkRefinementInvalidated(root_id,available_at,"PRICE_INVALIDATED");

      RemoveSourceAt(current);
     }
  }

int CountActiveRoots(const ENUM_TIMEFRAMES tf,const int direction=0)
  {
   int count=0;
   for(int i=0;i<ArraySize(g_sources);i++)
     {
      if(!g_sources[i].valid ||
         g_sources[i].kind!=V1_SOURCE_ROOT ||
         g_sources[i].tf!=tf ||
         g_sources[i].strategy_state!=V1_SOURCE_ACTIVE)
         continue;

      if(direction!=0 && g_sources[i].direction!=direction)
         continue;

      count++;
     }
   return count;
  }

void LogRootSnapshot(const int tf_index,const datetime available_at)
  {
   if(!IsRootTimeframeIndex(tf_index))
      return;

   int longs=CountActiveRoots(g_timeframes[tf_index],1);
   int shorts=CountActiveRoots(g_timeframes[tf_index],-1);

   string detail=StringFormat(
      "active_total=%d long=%d short=%d refinement_status=SEE_REFINEMENT_STATE",
      longs+shorts,
      longs,
      shorts);

   LogLine("ROOT_STATE",
           TfName(g_timeframes[tf_index]),
           available_at,
           "",
           detail);
  }

//+------------------------------------------------------------------+
//| Structure working-set logic                                      |
//+------------------------------------------------------------------+
void EnsureLegStart(V1StructureState &s,const MqlRates &bar)
  {
   if(!s.leg_initialized)
     {
      s.leg_initialized=true;
      s.leg_start_time=bar.time;
     }
  }

bool BuildWaveFromLeg(V1StructureState &s,
                      const int side,
                      const MqlRates &confirm_bar,
                      const datetime available_at,
                      V1WaveRef &wave)
  {
   ClearWave(wave);

   datetime start_time=s.leg_initialized ? s.leg_start_time : confirm_bar.time;
   if(start_time>confirm_bar.time)
      start_time=confirm_bar.time;

   MqlRates leg[];
   ArraySetAsSeries(leg,false);
   ResetLastError();
   int copied=CopyRates(_Symbol,s.tf,start_time,confirm_bar.time,leg);
   if(copied<=0)
     {
      PrintFormat("MentorV1 wave leg CopyRates failed tf=%s start=%s end=%s err=%d",
                  s.name,
                  TimeToString(start_time,TIME_DATE|TIME_SECONDS),
                  TimeToString(confirm_bar.time,TIME_DATE|TIME_SECONDS),
                  GetLastError());
      return false;
     }

   int extreme_index=0;
   if(side==V1_SIDE_HIGH)
     {
      for(int i=1;i<copied;i++)
         if(leg[i].high>leg[extreme_index].high)
            extreme_index=i;
     }
   else
     {
      for(int i=1;i<copied;i++)
         if(leg[i].low<leg[extreme_index].low)
            extreme_index=i;
     }

   MqlRates extreme=leg[extreme_index];

   wave.valid=true;
   wave.is_wave=true;
   wave.side=side;
   wave.confirmed_at=confirm_bar.time;
   wave.available_at=available_at;
   wave.occurred_at=extreme.time;

   if(side==V1_SIDE_HIGH)
     {
      wave.price=extreme.high;
      wave.wick_bottom=MathMax(extreme.open,extreme.close);
      wave.wick_top=extreme.high;
     }
   else
     {
      wave.price=extreme.low;
      wave.wick_bottom=extreme.low;
      wave.wick_top=MathMin(extreme.open,extreme.close);
     }

   wave.origin_window_start=start_time;
   wave.origin_window_end=wave.occurred_at;

   wave.id=StringFormat("%s:wave:%s:%I64d",
                        s.name,
                        SideName(side),
                        (long)wave.occurred_at);
   return true;
  }

void BuildDeliveryExtreme(V1StructureState &s,
                          const int side,
                          const MqlRates &bar,
                          const datetime available_at,
                          V1WaveRef &point)
  {
   ClearWave(point);
   point.valid=true;
   point.is_wave=false;
   point.side=side;
   point.occurred_at=bar.time;
   point.confirmed_at=bar.time;
   point.available_at=available_at;

   if(side==V1_SIDE_HIGH)
     {
      point.price=bar.high;
      point.wick_bottom=MathMax(bar.open,bar.close);
      point.wick_top=bar.high;
     }
   else
     {
      point.price=bar.low;
      point.wick_bottom=bar.low;
      point.wick_top=MathMin(bar.open,bar.close);
     }

   point.origin_window_start=bar.time;
   point.origin_window_end=bar.time;

   point.id=StringFormat("%s:delivery:%s:%I64d",
                         s.name,
                         SideName(side),
                         (long)bar.time);
  }

void UpdateNeutralReferences(V1StructureState &s,const V1WaveRef &wave)
  {
   if(wave.side==V1_SIDE_HIGH)
      CopyWave(wave,s.neutral_high);
   else if(wave.side==V1_SIDE_LOW)
      CopyWave(wave,s.neutral_low);

   if(s.neutral_high.valid)
      s.range_high=s.neutral_high.price;
   if(s.neutral_low.valid)
      s.range_low=s.neutral_low.price;
  }

void UpdateDirectionalWaveRoles(V1StructureState &s,const V1WaveRef &wave)
  {
   if(s.trend==V1_TREND_BULLISH)
     {
      if(wave.side==V1_SIDE_HIGH)
        {
         // The external high is the confirmed swing that owns the current
         // valid structural external extreme. The wave must explain the
         // current range high, not just be a lower internal pivot.
         if(s.range_high==0.0 || wave.price>=s.range_high-_Point*0.1)
           {
            CopyWave(wave,s.external_high);
            ClearWave(s.correction_low);
           }
        }
      else if(wave.side==V1_SIDE_LOW && s.external_high.valid &&
              wave.occurred_at>s.external_high.occurred_at)
        {
         if(!s.correction_low.valid || wave.price<s.correction_low.price)
            CopyWave(wave,s.correction_low);
        }
     }
   else if(s.trend==V1_TREND_BEARISH)
     {
      if(wave.side==V1_SIDE_LOW)
        {
         if(s.range_low==0.0 || wave.price<=s.range_low+_Point*0.1)
           {
            CopyWave(wave,s.external_low);
            ClearWave(s.correction_high);
           }
        }
      else if(wave.side==V1_SIDE_HIGH && s.external_low.valid &&
              wave.occurred_at>s.external_low.occurred_at)
        {
         if(!s.correction_high.valid || wave.price>s.correction_high.price)
            CopyWave(wave,s.correction_high);
        }
     }
  }

void EnterTransition(V1StructureState &s,
                     const int broken_direction,
                     const datetime available_at)
  {
   s.trend=V1_TREND_TRANSITION;
   s.transition_bias=broken_direction;
   s.transition_started_at=available_at;
   s.owner_id="";
   s.owner_started_at=0;

   // A mature opposite trend is NOT fabricated here.
   // Build a fresh two-sided post-break range before another INITIAL_BOS.
   ClearWave(s.neutral_high);
   ClearWave(s.neutral_low);
   ClearWave(s.external_high);
   ClearWave(s.external_low);
   ClearWave(s.protected_high);
   ClearWave(s.protected_low);
   ClearWave(s.break_reference);
   ClearWave(s.correction_high);
   ClearWave(s.correction_low);

   s.range_high=0.0;
   s.range_low=0.0;
  }

void PromoteInitialTrend(V1StructureState &s,
                         const int direction,
                         const V1WaveRef &broken_wave,
                         const MqlRates &break_bar,
                         const datetime available_at)
  {
   ClearWave(s.break_reference);

   if(direction>0)
     {
      s.trend=V1_TREND_BULLISH;
      CopyWave(s.neutral_low,s.protected_low);
      CopyWave(s.protected_low,s.external_low);
      ClearWave(s.protected_high);

      BuildDeliveryExtreme(s,V1_SIDE_HIGH,break_bar,available_at,s.external_high);

      ClearWave(s.correction_low);
      ClearWave(s.correction_high);
      s.range_low=s.protected_low.valid ? s.protected_low.price : broken_wave.price;
      s.range_high=s.external_high.price;
     }
   else
     {
      s.trend=V1_TREND_BEARISH;
      CopyWave(s.neutral_high,s.protected_high);
      CopyWave(s.protected_high,s.external_high);
      ClearWave(s.protected_low);

      BuildDeliveryExtreme(s,V1_SIDE_LOW,break_bar,available_at,s.external_low);

      ClearWave(s.correction_low);
      ClearWave(s.correction_high);
      s.range_high=s.protected_high.valid ? s.protected_high.price : broken_wave.price;
      s.range_low=s.external_low.price;
     }

   s.transition_bias=0;
   s.transition_started_at=0;
   ClearWave(s.neutral_high);
   ClearWave(s.neutral_low);
  }

void LogStructureEvent(V1StructureState &s,
                       const int event_type,
                       const int direction,
                       const V1WaveRef &broken,
                       const V1WaveRef &protected_ref,
                       const MqlRates &bar,
                       const datetime available_at)
  {
   s.structure_events++;
   string id=BuildStructureEventId(s,event_type,bar);

   string detail=StringFormat(
      "direction=%s bar_open=%s close=%.10f broken_id=%s broken_kind=%s broken_price=%.10f protected_id=%s protected_price=%s",
      direction>0 ? "LONG" : "SHORT",
      TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
      bar.close,
      broken.valid ? broken.id : "NA",
      broken.valid ? (broken.is_wave ? "WAVE" : "DELIVERY") : "NA",
      broken.valid ? broken.price : 0.0,
      protected_ref.valid ? protected_ref.id : "NA",
      protected_ref.valid ? DoubleToString(protected_ref.price,_Digits) : "NA");

   LogLine("STRUCTURE_"+EventName(event_type),s.name,available_at,id,detail);
  }

void EvaluateExistingStructureBreaks(const int tf_index,
                                     V1StructureState &s,
                                     const MqlRates &bar,
                                     const datetime available_at)
  {
   // Frozen ordering: use only objects that existed before this bar close.
   if(s.trend==V1_TREND_BULLISH)
     {
      if(s.protected_low.valid && bar.close<s.protected_low.price)
        {
         V1WaveRef broken,empty;
         CopyWave(s.protected_low,broken);
         ClearWave(empty);
         LogStructureEvent(s,V1_EVENT_PROTECTED_BREAK,-1,
                           broken,empty,bar,available_at);
         InvalidateRootsForStructureOwner(tf_index,available_at,bar);
         EnterTransition(s,-1,available_at);
         LogStateSnapshot(tf_index,available_at,"PROTECTED_BREAK");
         return;
        }

      if(s.external_high.valid && bar.close>s.external_high.price)
        {
         V1WaveRef broken,root_origin;
         CopyWave(s.external_high,broken);
         CopyWave(broken,s.break_reference);
         ClearWave(root_origin);

         // A continuation Root must come from the correction that actually
         // produced this BOS. If no confirmed causal correction exists at the
         // BOS close, Phase 3A does not fall back to an older protected swing.
         if(s.correction_low.valid)
           {
            CopyWave(s.correction_low,root_origin);
            CopyWave(s.correction_low,s.protected_low);
           }

         if(s.protected_low.valid)
            CopyWave(s.protected_low,s.external_low);

         s.range_low=s.protected_low.valid ? s.protected_low.price : s.range_low;
         BuildDeliveryExtreme(s,V1_SIDE_HIGH,bar,available_at,s.external_high);
         s.range_high=s.external_high.price;
         ClearWave(s.correction_low);

         LogStructureEvent(s,V1_EVENT_BOS,1,
                           broken,s.protected_low,bar,available_at);
         AddRootFromStructureEvent(tf_index,
                                   V1_EVENT_BOS,
                                   1,
                                   root_origin,
                                   bar,
                                   available_at);
         return;
        }
     }
   else if(s.trend==V1_TREND_BEARISH)
     {
      if(s.protected_high.valid && bar.close>s.protected_high.price)
        {
         V1WaveRef broken,empty;
         CopyWave(s.protected_high,broken);
         ClearWave(empty);
         LogStructureEvent(s,V1_EVENT_PROTECTED_BREAK,1,
                           broken,empty,bar,available_at);
         InvalidateRootsForStructureOwner(tf_index,available_at,bar);
         EnterTransition(s,1,available_at);
         LogStateSnapshot(tf_index,available_at,"PROTECTED_BREAK");
         return;
        }

      if(s.external_low.valid && bar.close<s.external_low.price)
        {
         V1WaveRef broken,root_origin;
         CopyWave(s.external_low,broken);
         CopyWave(broken,s.break_reference);
         ClearWave(root_origin);

         if(s.correction_high.valid)
           {
            CopyWave(s.correction_high,root_origin);
            CopyWave(s.correction_high,s.protected_high);
           }

         if(s.protected_high.valid)
            CopyWave(s.protected_high,s.external_high);

         s.range_high=s.protected_high.valid ? s.protected_high.price : s.range_high;
         BuildDeliveryExtreme(s,V1_SIDE_LOW,bar,available_at,s.external_low);
         s.range_low=s.external_low.price;
         ClearWave(s.correction_high);

         LogStructureEvent(s,V1_EVENT_BOS,-1,
                           broken,s.protected_high,bar,available_at);
         AddRootFromStructureEvent(tf_index,
                                   V1_EVENT_BOS,
                                   -1,
                                   root_origin,
                                   bar,
                                   available_at);
         return;
        }
     }
   else // NEUTRAL or TRANSITION
     {
      // Two-sided range is mandatory before INITIAL_BOS.
      if(!s.neutral_high.valid || !s.neutral_low.valid)
         return;

      if(bar.close>s.neutral_high.price)
        {
         V1WaveRef broken;
         CopyWave(s.neutral_high,broken);
         V1WaveRef protected_ref;
         CopyWave(s.neutral_low,protected_ref);

         PromoteInitialTrend(s,1,broken,bar,available_at);
         s.owner_id=BuildStructureEventId(s,V1_EVENT_INITIAL_BOS,bar);
         s.owner_started_at=available_at;
         LogStructureEvent(s,V1_EVENT_INITIAL_BOS,1,
                           broken,protected_ref,bar,available_at);
         AddRootFromStructureEvent(tf_index,
                                   V1_EVENT_INITIAL_BOS,
                                   1,
                                   protected_ref,
                                   bar,
                                   available_at);
         return;
        }

      if(bar.close<s.neutral_low.price)
        {
         V1WaveRef broken;
         CopyWave(s.neutral_low,broken);
         V1WaveRef protected_ref;
         CopyWave(s.neutral_high,protected_ref);

         PromoteInitialTrend(s,-1,broken,bar,available_at);
         s.owner_id=BuildStructureEventId(s,V1_EVENT_INITIAL_BOS,bar);
         s.owner_started_at=available_at;
         LogStructureEvent(s,V1_EVENT_INITIAL_BOS,-1,
                           broken,protected_ref,bar,available_at);
         AddRootFromStructureEvent(tf_index,
                                   V1_EVENT_INITIAL_BOS,
                                   -1,
                                   protected_ref,
                                   bar,
                                   available_at);
         return;
        }
     }
  }


//+------------------------------------------------------------------+
//| Phase 4A H1/M30 map ownership and reversal permission            |
//+------------------------------------------------------------------+
void ClearReversalPermission(const datetime available_at,
                             const string reason)
  {
   if(g_map.reversal_permission!=V1_REVERSAL_CLOSED)
     {
      string detail=StringFormat(
         "state=CLOSED previous=%s reason=%s opened_at=%s permission_event=%s permission_reference_id=%s permission_reference_price=%.10f",
         ReversalPermissionName(g_map.reversal_permission),
         reason,
         g_map.reversal_permission_opened_at>0 ?
            TimeToString(g_map.reversal_permission_opened_at,TIME_DATE|TIME_SECONDS) : "NA",
         ReferenceEventName(g_map.reversal_permission_event_type),
         g_map.permission_reference_id=="" ? "NA" : g_map.permission_reference_id,
         g_map.permission_reference_price);

      LogLine("REVERSAL_PERMISSION_STATE",
              "H1",
              available_at,
              g_map.permission_reference_id,
              detail);
      g_permission_closes++;
      g_map.last_permission_closed_at=available_at;
      g_map.last_permission_close_reason=reason;
      g_map.last_closed_permission_reference_id=g_map.permission_reference_id;
      g_map.last_closed_permission_opened_at=g_map.reversal_permission_opened_at;
     }

   g_map.reversal_permission=V1_REVERSAL_CLOSED;
   g_map.reversal_permission_opened_at=0;
   g_map.reversal_permission_event_type=V1_REFERENCE_NONE;
   g_map.permission_reference_id="";
   g_map.permission_reference_price=0.0;
  }

void ClearReversalReference(const datetime available_at,
                            const string reason)
  {
   if(g_map.reversal_reference_id!="")
     {
      string detail=StringFormat(
         "reason=%s old_reference_id=%s old_owner_id=%s side=%s price=%.10f reference_available_at=%s",
         reason,
         g_map.reversal_reference_id,
         g_map.reversal_reference_owner_id=="" ? "NA" : g_map.reversal_reference_owner_id,
         SideName(g_map.reversal_reference_side),
         g_map.reversal_reference_price,
         g_map.reversal_reference_available_at>0 ?
            TimeToString(g_map.reversal_reference_available_at,TIME_DATE|TIME_SECONDS) : "NA");

      LogLine("REVERSAL_REFERENCE_CLEARED",
              "H1",
              available_at,
              g_map.reversal_reference_id,
              detail);
     }

   g_map.reversal_reference_id="";
   g_map.reversal_reference_owner_id="";
   g_map.reversal_reference_side=V1_SIDE_NONE;
   g_map.reversal_reference_price=0.0;
   g_map.reversal_reference_available_at=0;
  }

void OpenReversalPermission(const int desired_permission,
                            const int event_type,
                            const datetime available_at)
  {
   if(desired_permission==V1_REVERSAL_CLOSED)
      return;

   if(g_map.reversal_permission==desired_permission)
      return;

   // A different open direction can only be valid after an owner transition.
   // Fail closed rather than silently rewriting the permission in place.
   if(g_map.reversal_permission!=V1_REVERSAL_CLOSED)
      ClearReversalPermission(available_at,"PERMISSION_DIRECTION_CHANGED");

   g_map.reversal_permission=desired_permission;
   g_map.reversal_permission_opened_at=available_at;
   g_map.reversal_permission_event_type=event_type;
   g_map.permission_reference_id=g_map.reversal_reference_id;
   g_map.permission_reference_price=g_map.reversal_reference_price;

   string detail=StringFormat(
      "state=%s opened_at=%s permission_event=%s permission_reference_id=%s permission_reference_price=%.10f current_h1_owner_id=%s",
      ReversalPermissionName(g_map.reversal_permission),
      TimeToString(available_at,TIME_DATE|TIME_SECONDS),
      ReferenceEventName(event_type),
      g_map.permission_reference_id,
      g_map.permission_reference_price,
      g_map.h1_owner_id=="" ? "NA" : g_map.h1_owner_id);

   LogLine("REVERSAL_PERMISSION_STATE",
           "H1",
           available_at,
           g_map.permission_reference_id,
           detail);
   g_permission_opens++;
  }

void EvaluateH1ReversalReference(const MqlRates &bar,
                                 const datetime available_at)
  {
   if(!IsMatureDirectionalTrend(g_structure[1].trend) ||
      g_structure[1].owner_id=="" ||
      g_map.reversal_reference_id=="" ||
      g_map.reversal_reference_owner_id!=g_structure[1].owner_id ||
      g_map.reversal_reference_available_at<=0 ||
      g_map.reversal_reference_available_at>=available_at)
      return;

   int event_type=V1_REFERENCE_NONE;
   int direction=TrendDirection(g_structure[1].trend);
   double ref=g_map.reversal_reference_price;

   // Frozen precedence:
   // 1) continuation body break
   // 2) wick penetration + close recovery
   // 3) touch
   if(direction>0)
     {
      if(bar.close>ref)
         event_type=V1_REFERENCE_CONTINUATION_BODY_BREAK;
      else if(bar.high>ref && bar.close<=ref)
         event_type=V1_REFERENCE_SWEEP_REJECTION;
      else if(bar.high>=ref)
         event_type=V1_REFERENCE_TOUCH;
     }
   else if(direction<0)
     {
      if(bar.close<ref)
         event_type=V1_REFERENCE_CONTINUATION_BODY_BREAK;
      else if(bar.low<ref && bar.close>=ref)
         event_type=V1_REFERENCE_SWEEP_REJECTION;
      else if(bar.low<=ref)
         event_type=V1_REFERENCE_TOUCH;
     }

   if(event_type==V1_REFERENCE_NONE)
      return;

   string detail=StringFormat(
      "event=%s h1_direction=%s owner_id=%s reference_id=%s reference_price=%.10f reference_available_at=%s bar_open=%s open=%.10f high=%.10f low=%.10f close=%.10f permission_before=%s",
      ReferenceEventName(event_type),
      DirectionName(direction),
      g_structure[1].owner_id,
      g_map.reversal_reference_id,
      ref,
      TimeToString(g_map.reversal_reference_available_at,TIME_DATE|TIME_SECONDS),
      TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
      bar.open,
      bar.high,
      bar.low,
      bar.close,
      ReversalPermissionName(g_map.reversal_permission));

   LogLine("REVERSAL_REFERENCE_EVENT",
           "H1",
           available_at,
           g_map.reversal_reference_id,
           detail);

   if(event_type==V1_REFERENCE_CONTINUATION_BODY_BREAK)
     {
      g_reference_continuations++;
      ClearReversalPermission(available_at,"TERMINATED_BY_CONTINUATION");
      return;
     }

   int desired=(direction>0 ?
                V1_REVERSAL_OPEN_FOR_SHORT :
                V1_REVERSAL_OPEN_FOR_LONG);

   if(event_type==V1_REFERENCE_SWEEP_REJECTION)
      g_reference_sweeps++;
   else
      g_reference_touches++;

   OpenReversalPermission(desired,event_type,available_at);
  }

void SetReversalReference(const V1WaveRef &reference,
                          const string owner_id,
                          const datetime available_at)
  {
   g_map.reversal_reference_id=reference.id;
   g_map.reversal_reference_owner_id=owner_id;
   g_map.reversal_reference_side=reference.side;
   g_map.reversal_reference_price=reference.price;
   g_map.reversal_reference_available_at=reference.available_at;

   string detail=StringFormat(
      "owner_id=%s side=%s price=%.10f reference_available_at=%s kind=%s permission=%s",
      owner_id,
      SideName(reference.side),
      reference.price,
      TimeToString(reference.available_at,TIME_DATE|TIME_SECONDS),
      reference.is_wave ? "WAVE" : "DELIVERY",
      ReversalPermissionName(g_map.reversal_permission));

   LogLine("REVERSAL_REFERENCE_SET",
           "H1",
           available_at,
           reference.id,
           detail);
  }

string HighestActiveMapName()
  {
   if(IsMatureDirectionalTrend(g_structure[1].trend) &&
      g_structure[1].owner_id!="")
      return "H1";

   if(IsMatureDirectionalTrend(g_structure[2].trend) &&
      g_structure[2].owner_id!="")
      return "M30";

   return "NONE";
  }

int HighestActiveMapDirection()
  {
   if(IsMatureDirectionalTrend(g_structure[1].trend) &&
      g_structure[1].owner_id!="")
      return TrendDirection(g_structure[1].trend);

   if(IsMatureDirectionalTrend(g_structure[2].trend) &&
      g_structure[2].owner_id!="")
      return TrendDirection(g_structure[2].trend);

   return 0;
  }

void LogMapSnapshot(const datetime available_at,
                    const string reason,
                    const bool force=false)
  {
   string signature=StringFormat(
      "h1=%s|%s|m30=%s|%s|ref=%s|%.10f|perm=%s|permref=%s",
      TrendName(g_structure[1].trend),
      g_structure[1].owner_id,
      TrendName(g_structure[2].trend),
      g_structure[2].owner_id,
      g_map.reversal_reference_id,
      g_map.reversal_reference_price,
      ReversalPermissionName(g_map.reversal_permission),
      g_map.permission_reference_id);

   if(!force && signature==g_map.last_snapshot_signature)
      return;

   g_map.last_snapshot_signature=signature;

   string detail=StringFormat(
      "reason=%s highest_active_map=%s direction=%s h1_trend=%s h1_owner_id=%s h1_owner_started_at=%s m30_trend=%s m30_owner_id=%s m30_owner_started_at=%s reversal_reference_id=%s reversal_reference_price=%s reversal_reference_available_at=%s reversal_permission=%s permission_opened_at=%s permission_event=%s permission_reference_id=%s",
      reason,
      HighestActiveMapName(),
      DirectionName(HighestActiveMapDirection()),
      TrendName(g_structure[1].trend),
      g_structure[1].owner_id=="" ? "NA" : g_structure[1].owner_id,
      g_structure[1].owner_started_at>0 ?
         TimeToString(g_structure[1].owner_started_at,TIME_DATE|TIME_SECONDS) : "NA",
      TrendName(g_structure[2].trend),
      g_structure[2].owner_id=="" ? "NA" : g_structure[2].owner_id,
      g_structure[2].owner_started_at>0 ?
         TimeToString(g_structure[2].owner_started_at,TIME_DATE|TIME_SECONDS) : "NA",
      g_map.reversal_reference_id=="" ? "NA" : g_map.reversal_reference_id,
      g_map.reversal_reference_id=="" ? "NA" : DoubleToString(g_map.reversal_reference_price,_Digits),
      g_map.reversal_reference_available_at>0 ?
         TimeToString(g_map.reversal_reference_available_at,TIME_DATE|TIME_SECONDS) : "NA",
      ReversalPermissionName(g_map.reversal_permission),
      g_map.reversal_permission_opened_at>0 ?
         TimeToString(g_map.reversal_permission_opened_at,TIME_DATE|TIME_SECONDS) : "NA",
      ReferenceEventName(g_map.reversal_permission_event_type),
      g_map.permission_reference_id=="" ? "NA" : g_map.permission_reference_id);

   LogLine("MAP_STATE","",available_at,"",detail);
  }

void RefreshMapControlAfterStructure(const datetime available_at)
  {
   bool h1_mature=
      IsMatureDirectionalTrend(g_structure[1].trend) &&
      g_structure[1].owner_id!="";

   string new_h1_owner=(h1_mature ? g_structure[1].owner_id : "");

   if(new_h1_owner!=g_map.h1_owner_id)
     {
      if(g_map.reversal_permission!=V1_REVERSAL_CLOSED)
         ClearReversalPermission(available_at,"H1_OWNER_CHANGED");

      ClearReversalReference(available_at,"H1_OWNER_CHANGED");

      g_map.h1_owner_id=new_h1_owner;
      g_map.h1_owner_started_at=
         (new_h1_owner=="" ? 0 : g_structure[1].owner_started_at);
     }

   bool m30_mature=
      IsMatureDirectionalTrend(g_structure[2].trend) &&
      g_structure[2].owner_id!="";

   g_map.m30_owner_id=(m30_mature ? g_structure[2].owner_id : "");
   g_map.m30_owner_started_at=
      (m30_mature ? g_structure[2].owner_started_at : 0);

   if(!h1_mature)
     {
      if(g_map.reversal_permission!=V1_REVERSAL_CLOSED)
         ClearReversalPermission(available_at,"H1_NOT_DIRECTIONAL");

      if(g_map.reversal_reference_id!="")
         ClearReversalReference(available_at,"H1_NOT_DIRECTIONAL");

      LogMapSnapshot(available_at,"MAP_REFRESH");
      return;
     }

   V1WaveRef reference;
   ClearWave(reference);

   if(g_structure[1].trend==V1_TREND_BULLISH)
      CopyWave(g_structure[1].external_high,reference);
   else
      CopyWave(g_structure[1].external_low,reference);

   if(!reference.valid)
     {
      ClearReversalReference(available_at,"MISSING_H1_EXTERNAL_REFERENCE");
      LogMapSnapshot(available_at,"MAP_REFRESH");
      return;
     }

   bool set_reference=false;

   if(g_map.reversal_reference_id=="" ||
      g_map.reversal_reference_owner_id!=g_structure[1].owner_id)
      set_reference=true;
   else if(g_structure[1].trend==V1_TREND_BULLISH &&
           reference.price>g_map.reversal_reference_price)
      set_reference=true;
   else if(g_structure[1].trend==V1_TREND_BEARISH &&
           reference.price<g_map.reversal_reference_price)
      set_reference=true;

   if(set_reference)
      SetReversalReference(reference,g_structure[1].owner_id,available_at);

   LogMapSnapshot(available_at,"MAP_REFRESH");
  }

//+------------------------------------------------------------------+
//| Phase 4B scenario + frozen objective-family planning             |
//+------------------------------------------------------------------+
bool IsRefinementReadyStatus(const int status)
  {
   return (status==V1_REFINE_READY ||
           status==V1_REFINE_STOPPED_AMBIGUOUS);
  }

int FindActiveScenarioByContextKey(const string context_key)
  {
   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(!g_scenarios[i].valid ||
         g_scenarios[i].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[i].strategy_state==V1_STRATEGY_NO_TRADE)
         continue;

      string key=StringFormat("%s|%s|%s|%s|%s",
                              ScenarioScopeName(g_scenarios[i].scope),
                              DirectionName(g_scenarios[i].direction),
                              TfName(g_scenarios[i].active_map_tf),
                              g_scenarios[i].owner_id,
                              g_scenarios[i].parent_context_id);
      if(g_scenarios[i].scope==V1_SCOPE_EXTERNAL_REVERSAL)
         key+="|"+g_scenarios[i].permission_reference_id;

      if(key==context_key)
         return i;
     }
   return -1;
  }

int FindScenarioById(const string scenario_id)
  {
   for(int i=0;i<ArraySize(g_scenarios);i++)
      if(g_scenarios[i].valid && g_scenarios[i].id==scenario_id)
         return i;
   return -1;
  }

bool HasActiveScenarioForRoot(const string root_id)
  {
   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(!g_scenarios[i].valid ||
         g_scenarios[i].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[i].strategy_state==V1_STRATEGY_NO_TRADE)
         continue;
      if(g_scenarios[i].root_zone_id==root_id)
         return true;
     }
   return false;
  }

bool GetActiveMapRange(const ENUM_TIMEFRAMES tf,
                       const int direction,
                       double &range_low,
                       double &range_high,
                       double &directional_boundary)
  {
   int index=-1;
   if(tf==PERIOD_H1)
      index=1;
   else if(tf==PERIOD_M30)
      index=2;
   else
      return false;

   if(direction>0)
     {
      if(g_structure[index].trend!=V1_TREND_BULLISH ||
         !g_structure[index].protected_low.valid ||
         !g_structure[index].external_high.valid)
         return false;

      range_low=g_structure[index].protected_low.price;
      range_high=g_structure[index].external_high.price;
      directional_boundary=g_structure[index].external_high.price;
     }
   else
     {
      if(g_structure[index].trend!=V1_TREND_BEARISH ||
         !g_structure[index].external_low.valid ||
         !g_structure[index].protected_high.valid)
         return false;

      range_low=g_structure[index].external_low.price;
      range_high=g_structure[index].protected_high.price;
      directional_boundary=g_structure[index].external_low.price;
     }

   return (range_high>range_low);
  }

bool FindReadyLineageSource(const int refinement_index,
                            int &root_index,
                            int &source_index)
  {
   root_index=-1;
   source_index=-1;

   if(refinement_index<0 ||
      refinement_index>=ArraySize(g_refinements) ||
      !g_refinements[refinement_index].valid ||
      !IsRefinementReadyStatus(g_refinements[refinement_index].status) ||
      g_refinements[refinement_index].final_child_id=="")
      return false;

   root_index=FindActiveSourceById(g_refinements[refinement_index].root_zone_id);
   source_index=FindActiveSourceById(g_refinements[refinement_index].final_child_id);

   if(root_index<0 || source_index<0)
      return false;

   if(g_sources[root_index].kind!=V1_SOURCE_ROOT ||
      g_sources[source_index].kind!=V1_SOURCE_CHILD ||
      g_sources[root_index].direction!=g_sources[source_index].direction ||
      g_sources[source_index].root_zone_id!=g_sources[root_index].id)
      return false;

   return true;
  }

bool BuildScenarioDraft(const int refinement_index,
                        V1ScenarioDraft &draft)
  {
   draft.valid=false;

   int root_index=-1;
   int source_index=-1;
   if(!FindReadyLineageSource(refinement_index,root_index,source_index))
      return false;

   if(HasActiveScenarioForRoot(g_sources[root_index].id))
      return false;

   if(g_refinements[refinement_index].preplan_contact_at>0)
      return false;

   int direction=g_sources[source_index].direction;
   if(direction==0)
      return false;

   bool h1_mature=
      IsMatureDirectionalTrend(g_structure[1].trend) &&
      g_structure[1].owner_id!="";
   bool m30_mature=
      IsMatureDirectionalTrend(g_structure[2].trend) &&
      g_structure[2].owner_id!="";

   int scope=V1_SCOPE_NONE;
   ENUM_TIMEFRAMES active_map_tf=PERIOD_CURRENT;
   string owner_id="";
   string parent_context_id="";
   string permission_reference_id="";
   datetime permission_opened_at=0;

   if(h1_mature)
     {
      int h1_direction=TrendDirection(g_structure[1].trend);

      if(g_map.reversal_permission==V1_REVERSAL_CLOSED)
        {
         if(direction!=h1_direction)
            return false;

         scope=V1_SCOPE_EXTERNAL_CONTINUATION;
         active_map_tf=PERIOD_H1;
         owner_id=g_structure[1].owner_id;
         parent_context_id=g_structure[1].owner_id;
        }
      else
        {
         int permission_direction=
            (g_map.reversal_permission==V1_REVERSAL_OPEN_FOR_LONG ? 1 : -1);

         if(direction!=permission_direction ||
            !m30_mature ||
            TrendDirection(g_structure[2].trend)!=direction ||
            direction==h1_direction)
            return false;

         scope=V1_SCOPE_EXTERNAL_REVERSAL;
         active_map_tf=PERIOD_M30;
         owner_id=g_structure[2].owner_id;
         parent_context_id=g_structure[1].owner_id;
         permission_reference_id=g_map.permission_reference_id;
         permission_opened_at=g_map.reversal_permission_opened_at;

         if(permission_reference_id=="" || permission_opened_at<=0)
            return false;
        }
     }
   else
     {
      if(!m30_mature ||
         direction!=TrendDirection(g_structure[2].trend))
         return false;

      scope=V1_SCOPE_EXTERNAL_CONTINUATION;
      active_map_tf=PERIOD_M30;
      owner_id=g_structure[2].owner_id;
      parent_context_id="";
     }

   double range_low=0.0;
   double range_high=0.0;
   double boundary=0.0;
   if(!GetActiveMapRange(active_map_tf,
                         direction,
                         range_low,
                         range_high,
                         boundary))
      return false;

   double source_mid=(g_sources[source_index].bottom+
                      g_sources[source_index].top)*0.5;

   // The source must belong to the current active map, not merely overlap it.
   if(g_sources[source_index].bottom<range_low ||
      g_sources[source_index].top>range_high)
      return false;

   double eq=(range_low+range_high)*0.5;

   // Premium/discount is a frozen continuation gate.
   if(scope==V1_SCOPE_EXTERNAL_CONTINUATION)
     {
      if(direction>0 && source_mid>eq)
         return false;
      if(direction<0 && source_mid<eq)
         return false;
     }

   draft.valid=true;
   draft.refinement_index=refinement_index;
   draft.scope=scope;
   draft.direction=direction;
   draft.active_map_tf=active_map_tf;
   draft.owner_id=owner_id;
   draft.parent_context_id=parent_context_id;
   draft.permission_reference_id=permission_reference_id;
   draft.permission_opened_at=permission_opened_at;
   draft.root_zone_id=g_sources[root_index].id;
   draft.final_source_id=g_sources[source_index].id;
   draft.range_low=range_low;
   draft.range_high=range_high;
   draft.eq=eq;

   draft.context_key=StringFormat("%s|%s|%s|%s|%s",
                                  ScenarioScopeName(scope),
                                  DirectionName(direction),
                                  TfName(active_map_tf),
                                  owner_id,
                                  parent_context_id);
   if(scope==V1_SCOPE_EXTERNAL_REVERSAL)
      draft.context_key+="|"+permission_reference_id;

   return true;
  }

double ObjectivePrice(const V1LiquidityPool &pool)
  {
   if(pool.side==V1_SIDE_HIGH)
      return pool.top;
   if(pool.side==V1_SIDE_LOW)
      return pool.bottom;
   return 0.0;
  }

bool LatestClosedM1CloseAt(const datetime snapshot_at,
                           double &price,
                           datetime &bar_open)
  {
   price=0.0;
   bar_open=0;
   if(snapshot_at<=0)
      return false;

   int shift=iBarShift(_Symbol,PERIOD_M1,snapshot_at-1,false);
   if(shift<0)
      return false;

   MqlRates bar[];
   ArraySetAsSeries(bar,false);
   if(CopyRates(_Symbol,PERIOD_M1,shift,1,bar)!=1)
      return false;

   if(bar[0].time+PeriodSeconds(PERIOD_M1)>snapshot_at)
      return false;

   price=bar[0].close;
   bar_open=bar[0].time;
   return true;
  }

void AddObjectiveDraft(V1ObjectiveCandidate &candidates[],
                       const V1LiquidityPool &pool)
  {
   int n=ArraySize(candidates);
   if(ArrayResize(candidates,n+1,32)<0)
      return;

   candidates[n].valid=true;
   candidates[n].scenario_id="";
   candidates[n].id="";
   candidates[n].liquidity_id=pool.id;
   candidates[n].family=pool.family;
   candidates[n].tf=pool.tf;
   candidates[n].side=pool.side;
   candidates[n].price=ObjectivePrice(pool);
   candidates[n].available_at=pool.available_at;
   candidates[n].order_index=0;
   candidates[n].consumed=false;
   candidates[n].consumed_at=0;
  }

void SortObjectiveDrafts(V1ObjectiveCandidate &candidates[],
                         const int direction)
  {
   int n=ArraySize(candidates);
   for(int i=1;i<n;i++)
     {
      V1ObjectiveCandidate key=candidates[i];
      int j=i-1;

      while(j>=0)
        {
         bool move=false;
         if(direction>0)
            move=(candidates[j].price>key.price);
         else
            move=(candidates[j].price<key.price);

         if(!move)
            break;

         candidates[j+1]=candidates[j];
         j--;
        }

      candidates[j+1]=key;
     }

   for(int i=0;i<n;i++)
      candidates[i].order_index=i;
  }

bool BuildFrozenObjectiveFamily(const V1ScenarioDraft &draft,
                                const datetime frozen_at,
                                datetime &plan_reference_bar_open,
                                double &plan_reference_price,
                                double &primary_horizon,
                                V1ObjectiveCandidate &candidates[])
  {
   ArrayResize(candidates,0);

   if(!LatestClosedM1CloseAt(frozen_at,
                             plan_reference_price,
                             plan_reference_bar_open))
      return false;

   double range_low=0.0;
   double range_high=0.0;
   double directional_boundary=0.0;
   if(!GetActiveMapRange(draft.active_map_tf,
                         draft.direction,
                         range_low,
                         range_high,
                         directional_boundary))
      return false;

   int target_side=(draft.direction>0 ? V1_SIDE_HIGH : V1_SIDE_LOW);

   V1ObjectiveCandidate primary[];
   ArrayResize(primary,0);

   for(int i=0;i<ArraySize(g_liquidity);i++)
     {
      if(!g_liquidity[i].valid ||
         g_liquidity[i].consumed ||
         g_liquidity[i].family!=V1_LIQ_EXTERNAL_SWING ||
         g_liquidity[i].side!=target_side ||
         g_liquidity[i].available_at>frozen_at)
         continue;

      bool timeframe_ok=false;

      if(draft.scope==V1_SCOPE_EXTERNAL_CONTINUATION &&
         draft.active_map_tf==PERIOD_H1)
         timeframe_ok=(g_liquidity[i].tf==PERIOD_H1 ||
                       g_liquidity[i].tf==PERIOD_M30);
      else
         timeframe_ok=(g_liquidity[i].tf==PERIOD_M30);

      if(!timeframe_ok)
         continue;

      double price=ObjectivePrice(g_liquidity[i]);

      if(draft.direction>0)
        {
         if(price<=plan_reference_price ||
            price<directional_boundary)
            continue;
        }
      else
        {
         if(price>=plan_reference_price ||
            price>directional_boundary)
            continue;
        }

      AddObjectiveDraft(primary,g_liquidity[i]);
     }

   if(ArraySize(primary)>0)
     {
      primary_horizon=primary[0].price;
      for(int i=1;i<ArraySize(primary);i++)
        {
         if(draft.direction>0)
            primary_horizon=MathMax(primary_horizon,primary[i].price);
         else
            primary_horizon=MathMin(primary_horizon,primary[i].price);
        }
     }
   else
      primary_horizon=plan_reference_price;

   for(int i=0;i<ArraySize(primary);i++)
     {
      int n=ArraySize(candidates);
      if(ArrayResize(candidates,n+1,32)<0)
         continue;
      candidates[n]=primary[i];
     }

   // H4 is a long-horizon extension only. It is never an early-reversal map
   // or source authority.
   if(draft.scope==V1_SCOPE_EXTERNAL_CONTINUATION)
     {
      for(int i=0;i<ArraySize(g_liquidity);i++)
        {
         if(!g_liquidity[i].valid ||
            g_liquidity[i].consumed ||
            g_liquidity[i].family!=V1_LIQ_EXTERNAL_SWING ||
            g_liquidity[i].tf!=PERIOD_H4 ||
            g_liquidity[i].side!=target_side ||
            g_liquidity[i].available_at>frozen_at)
            continue;

         double price=ObjectivePrice(g_liquidity[i]);

         if(draft.direction>0)
           {
            if(price<=primary_horizon)
               continue;
           }
         else
           {
            if(price>=primary_horizon)
               continue;
           }

         AddObjectiveDraft(candidates,g_liquidity[i]);
        }
     }

   SortObjectiveDrafts(candidates,draft.direction);
   return (ArraySize(candidates)>0);
  }

void BindLineageScenarioOwner(const string root_id,
                              const string scenario_id)
  {
   for(int i=0;i<ArraySize(g_sources);i++)
     {
      if(!g_sources[i].valid ||
         g_sources[i].strategy_state!=V1_SOURCE_ACTIVE ||
         g_sources[i].root_zone_id!=root_id)
         continue;

      if(g_sources[i].scenario_owner_id=="")
         g_sources[i].scenario_owner_id=scenario_id;
     }
  }

void ReleaseLineageScenarioOwner(const string root_id,
                                 const string scenario_id)
  {
   for(int i=0;i<ArraySize(g_sources);i++)
     {
      if(!g_sources[i].valid ||
         g_sources[i].root_zone_id!=root_id)
         continue;

      if(g_sources[i].scenario_owner_id==scenario_id)
         g_sources[i].scenario_owner_id="";
     }
  }

void LogScenarioCanceled(const V1ScenarioPlan &plan,
                         const datetime available_at,
                         const string reason)
  {
   LogLine("SCENARIO_CANCELED",
           TfName(plan.active_map_tf),
           available_at,
           plan.id,
           StringFormat("state=CANCELED scope=%s direction=%s owner_id=%s parent_context_id=%s root_zone_id=%s final_source_id=%s reason=%s",
                        ScenarioScopeName(plan.scope),
                        DirectionName(plan.direction),
                        plan.owner_id,
                        plan.parent_context_id=="" ? "NONE" : plan.parent_context_id,
                        plan.root_zone_id,
                        plan.final_source_id,
                        reason));
  }

void RefreshObjectiveCandidateConsumption(const datetime available_at)
  {
   for(int i=0;i<ArraySize(g_objective_candidates);i++)
     {
      if(!g_objective_candidates[i].valid ||
         g_objective_candidates[i].consumed)
         continue;

      int plan_index=FindScenarioById(g_objective_candidates[i].scenario_id);
      if(plan_index<0)
         continue;

      if(FindActiveLiquidityById(g_objective_candidates[i].liquidity_id)>=0)
         continue;

      g_objective_candidates[i].consumed=true;
      g_objective_candidates[i].consumed_at=available_at;

      LogLine("OBJECTIVE_CANDIDATE_CONSUMED",
              TfName(g_objective_candidates[i].tf),
              available_at,
              g_objective_candidates[i].id,
              StringFormat("scenario_id=%s liquidity_id=%s order_index=%d price=%.10f action=KEEP_FROZEN_ORDER_SKIP_IF_LATER_TP_SELECTION",
                           g_objective_candidates[i].scenario_id,
                           g_objective_candidates[i].liquidity_id,
                           g_objective_candidates[i].order_index,
                           g_objective_candidates[i].price));
     }
  }

void CancelInvalidScenarioPlans(const datetime available_at)
  {
   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(!g_scenarios[i].valid ||
         g_scenarios[i].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[i].strategy_state==V1_STRATEGY_NO_TRADE)
         continue;

      string reason="";

      int root_index=FindActiveSourceById(g_scenarios[i].root_zone_id);
      int source_index=FindActiveSourceById(g_scenarios[i].final_source_id);

      if(root_index<0 || source_index<0)
         reason="SOURCE_LINEAGE_INVALIDATED";
      else if(g_scenarios[i].scope==V1_SCOPE_EXTERNAL_CONTINUATION)
        {
         if(g_scenarios[i].active_map_tf==PERIOD_H1)
           {
            if(g_structure[1].owner_id!=g_scenarios[i].owner_id ||
               !IsMatureDirectionalTrend(g_structure[1].trend))
               reason="CONTINUATION_OWNER_INVALIDATED";
           }
         else if(g_scenarios[i].active_map_tf==PERIOD_M30)
           {
            if(g_structure[2].owner_id!=g_scenarios[i].owner_id ||
               !IsMatureDirectionalTrend(g_structure[2].trend))
               reason="CONTINUATION_OWNER_INVALIDATED";
           }
        }
      else if(g_scenarios[i].scope==V1_SCOPE_EXTERNAL_REVERSAL)
        {
         if(g_map.last_permission_closed_at>g_scenarios[i].frozen_at &&
            g_map.last_permission_close_reason=="TERMINATED_BY_CONTINUATION" &&
            g_map.last_closed_permission_reference_id==
               g_scenarios[i].permission_reference_id &&
            g_map.last_closed_permission_opened_at==
               g_scenarios[i].permission_opened_at)
            reason="EARLY_REVERSAL_PERMISSION_TERMINATED";
        }

      if(reason=="")
         continue;

      g_scenarios[i].strategy_state=V1_STRATEGY_CANCELED;
      g_scenarios[i].canceled_at=available_at;
      g_scenarios[i].cancel_reason=reason;
      ReleaseLineageScenarioOwner(g_scenarios[i].root_zone_id,
                                  g_scenarios[i].id);
      LogScenarioCanceled(g_scenarios[i],available_at,reason);
      g_scenarios_canceled++;
     }
  }

void AuditPrePlanSourceContact(const MqlRates &bar,
                               const datetime available_at)
  {
   for(int i=0;i<ArraySize(g_refinements);i++)
     {
      if(!g_refinements[i].valid ||
         !IsRefinementReadyStatus(g_refinements[i].status) ||
         g_refinements[i].final_child_id=="" ||
         g_refinements[i].preplan_contact_at>0 ||
         HasActiveScenarioForRoot(g_refinements[i].root_zone_id) ||
         available_at<=g_refinements[i].frozen_at)
         continue;

      int source_index=FindActiveSourceById(g_refinements[i].final_child_id);
      if(source_index<0)
         continue;

      if(bar.high>=g_sources[source_index].bottom &&
         bar.low<=g_sources[source_index].top)
        {
         g_refinements[i].preplan_contact_at=available_at;
         LogLine("PREPLAN_SOURCE_CONTACT",
                 "M1",
                 available_at,
                 g_refinements[i].root_zone_id,
                 StringFormat("final_source_id=%s source_bottom=%.10f source_top=%.10f refinement_frozen_at=%s action=BLOCK_RETROSPECTIVE_PLAN",
                              g_refinements[i].final_child_id,
                              g_sources[source_index].bottom,
                              g_sources[source_index].top,
                              TimeToString(g_refinements[i].frozen_at,TIME_DATE|TIME_SECONDS)));
         g_scenarios_precontact_rejected++;
        }
     }
  }

void AuditBootstrapPrePlanContacts(const datetime snapshot_at)
  {
   for(int i=0;i<ArraySize(g_refinements);i++)
     {
      if(!g_refinements[i].valid ||
         !IsRefinementReadyStatus(g_refinements[i].status) ||
         g_refinements[i].final_child_id=="" ||
         g_refinements[i].preplan_contact_at>0)
         continue;

      int source_index=FindActiveSourceById(g_refinements[i].final_child_id);
      if(source_index<0)
         continue;

      MqlRates bars[];
      ArraySetAsSeries(bars,false);
      int copied=CopyRates(_Symbol,
                           PERIOD_M1,
                           g_refinements[i].frozen_at,
                           snapshot_at,
                           bars);
      if(copied<=0)
         continue;

      for(int k=0;k<copied;k++)
        {
         datetime bar_available=bars[k].time+PeriodSeconds(PERIOD_M1);
         if(bar_available<=g_refinements[i].frozen_at ||
            bar_available>snapshot_at)
            continue;

         if(bars[k].high>=g_sources[source_index].bottom &&
            bars[k].low<=g_sources[source_index].top)
           {
            g_refinements[i].preplan_contact_at=bar_available;
            LogLine("PREPLAN_SOURCE_CONTACT",
                    "M1",
                    snapshot_at,
                    g_refinements[i].root_zone_id,
                    StringFormat("historical_contact_at=%s final_source_id=%s source_bottom=%.10f source_top=%.10f refinement_frozen_at=%s action=BLOCK_RETROSPECTIVE_PLAN",
                                 TimeToString(bar_available,TIME_DATE|TIME_SECONDS),
                                 g_refinements[i].final_child_id,
                                 g_sources[source_index].bottom,
                                 g_sources[source_index].top,
                                 TimeToString(g_refinements[i].frozen_at,TIME_DATE|TIME_SECONDS)));
            g_scenarios_precontact_rejected++;
            break;
           }
        }
     }
  }

string BuildScenarioLayerSignature()
  {
   string signature=StringFormat(
      "h1=%s|%s|m30=%s|%s|perm=%s|permref=%s|h1ext=%s|m30ext=%s|liq=%I64d/%I64d/%I64d",
      TrendName(g_structure[1].trend),
      g_structure[1].owner_id,
      TrendName(g_structure[2].trend),
      g_structure[2].owner_id,
      ReversalPermissionName(g_map.reversal_permission),
      g_map.permission_reference_id,
      g_structure[1].trend==V1_TREND_BULLISH ?
         g_structure[1].external_high.id : g_structure[1].external_low.id,
      g_structure[2].trend==V1_TREND_BULLISH ?
         g_structure[2].external_high.id : g_structure[2].external_low.id,
      g_liquidity_created,
      g_liquidity_sweeps,
      g_liquidity_body_deliveries);

   for(int i=0;i<ArraySize(g_refinements);i++)
     {
      if(!g_refinements[i].valid)
         continue;

      signature+=StringFormat("|R:%s:%s:%d:%I64d",
                              g_refinements[i].root_zone_id,
                              g_refinements[i].final_child_id,
                              g_refinements[i].status,
                              (long)g_refinements[i].preplan_contact_at);
     }

   return signature;
  }

void StoreScenarioPlan(const V1ScenarioDraft &draft,
                       const datetime frozen_at,
                       const datetime plan_reference_bar_open,
                       const double plan_reference_price,
                       const double primary_horizon,
                       V1ObjectiveCandidate &family[])
  {
   int source_index=FindActiveSourceById(draft.final_source_id);
   if(source_index<0)
      return;

   string scenario_id=StringFormat("scenario:%s:%s:%I64d:%s",
                                   ScenarioScopeName(draft.scope),
                                   DirectionName(draft.direction),
                                   (long)frozen_at,
                                   draft.final_source_id);

   int n=ArraySize(g_scenarios);
   if(ArrayResize(g_scenarios,n+1,32)<0)
      return;

   g_scenarios[n].valid=true;
   g_scenarios[n].id=scenario_id;
   g_scenarios[n].strategy_state=V1_STRATEGY_PLANNED;
   g_scenarios[n].scope=draft.scope;
   g_scenarios[n].direction=draft.direction;
   g_scenarios[n].active_map_tf=draft.active_map_tf;
   g_scenarios[n].owner_id=draft.owner_id;
   g_scenarios[n].parent_context_id=draft.parent_context_id;
   g_scenarios[n].h1_trend_at_freeze=g_structure[1].trend;
   g_scenarios[n].h1_owner_id_at_freeze=g_structure[1].owner_id;
   g_scenarios[n].m30_trend_at_freeze=g_structure[2].trend;
   g_scenarios[n].m30_owner_id_at_freeze=g_structure[2].owner_id;
   g_scenarios[n].reversal_permission_at_freeze=g_map.reversal_permission;
   g_scenarios[n].permission_reference_id=draft.permission_reference_id;
   g_scenarios[n].permission_opened_at=draft.permission_opened_at;
   g_scenarios[n].root_zone_id=draft.root_zone_id;
   g_scenarios[n].final_source_id=draft.final_source_id;
   g_scenarios[n].source_tf=g_sources[source_index].tf;
   g_scenarios[n].source_bottom=g_sources[source_index].bottom;
   g_scenarios[n].source_top=g_sources[source_index].top;
   g_scenarios[n].map_range_low=draft.range_low;
   g_scenarios[n].map_range_high=draft.range_high;
   g_scenarios[n].map_eq=draft.eq;
   g_scenarios[n].frozen_at=frozen_at;
   g_scenarios[n].plan_reference_bar_open=plan_reference_bar_open;
   g_scenarios[n].plan_reference_price=plan_reference_price;
   g_scenarios[n].primary_directional_horizon=primary_horizon;
   g_scenarios[n].objective_count=ArraySize(family);
   g_scenarios[n].canceled_at=0;
   g_scenarios[n].cancel_reason="";

   BindLineageScenarioOwner(draft.root_zone_id,scenario_id);

   LogLine("SCENARIO_LINEAGE_BOUND",
           TfName(g_sources[source_index].tf),
           frozen_at,
           scenario_id,
           StringFormat("root_zone_id=%s final_source_id=%s source_tf=%s source_bottom=%.10f source_top=%.10f scenario_owner_id=%s",
                        draft.root_zone_id,
                        draft.final_source_id,
                        TfName(g_sources[source_index].tf),
                        g_sources[source_index].bottom,
                        g_sources[source_index].top,
                        scenario_id));

   for(int i=0;i<ArraySize(family);i++)
     {
      int c=ArraySize(g_objective_candidates);
      if(ArrayResize(g_objective_candidates,c+1,64)<0)
         continue;

      family[i].scenario_id=scenario_id;
      family[i].id=StringFormat("%s:objective:%d",
                                scenario_id,
                                family[i].order_index);
      g_objective_candidates[c]=family[i];
      g_objective_candidates_frozen++;

      LogLine("OBJECTIVE_CANDIDATE_FROZEN",
              TfName(family[i].tf),
              frozen_at,
              family[i].id,
              StringFormat("scenario_id=%s order_index=%d liquidity_id=%s family=%s side=%s price=%.10f available_at=%s primary_or_extension=%s",
                           scenario_id,
                           family[i].order_index,
                           family[i].liquidity_id,
                           LiquidityFamilyName(family[i].family),
                           SideName(family[i].side),
                           family[i].price,
                           TimeToString(family[i].available_at,TIME_DATE|TIME_SECONDS),
                           family[i].tf==PERIOD_H4 ? "H4_EXTENSION" : "PRIMARY"));
     }

   LogLine("SCENARIO_PLANNED",
           TfName(draft.active_map_tf),
           frozen_at,
           scenario_id,
           StringFormat("state=PLANNED scope=%s direction=%s active_map_tf=%s owner_id=%s parent_context_id=%s h1_trend_at_freeze=%s h1_owner_id_at_freeze=%s m30_trend_at_freeze=%s m30_owner_id_at_freeze=%s reversal_permission_at_freeze=%s permission_reference_id=%s permission_opened_at=%s root_zone_id=%s final_source_id=%s source_tf=%s source_bottom=%.10f source_top=%.10f map_range_low=%.10f map_range_high=%.10f map_eq=%.10f plan_reference_bar_open=%s plan_reference_price=%.10f primary_directional_horizon=%.10f objective_count=%d trigger_search_enabled=false",
                        ScenarioScopeName(draft.scope),
                        DirectionName(draft.direction),
                        TfName(draft.active_map_tf),
                        draft.owner_id,
                        draft.parent_context_id=="" ? "NONE" : draft.parent_context_id,
                        TrendName(g_structure[1].trend),
                        g_structure[1].owner_id=="" ? "NA" : g_structure[1].owner_id,
                        TrendName(g_structure[2].trend),
                        g_structure[2].owner_id=="" ? "NA" : g_structure[2].owner_id,
                        ReversalPermissionName(g_map.reversal_permission),
                        draft.permission_reference_id=="" ? "NA" : draft.permission_reference_id,
                        draft.permission_opened_at>0 ?
                           TimeToString(draft.permission_opened_at,TIME_DATE|TIME_SECONDS) : "NA",
                        draft.root_zone_id,
                        draft.final_source_id,
                        TfName(g_sources[source_index].tf),
                        g_sources[source_index].bottom,
                        g_sources[source_index].top,
                        draft.range_low,
                        draft.range_high,
                        draft.eq,
                        TimeToString(plan_reference_bar_open,TIME_DATE|TIME_SECONDS),
                        plan_reference_price,
                        primary_horizon,
                        ArraySize(family)));

   g_scenarios_planned++;
  }

void RefreshScenarioLayer(const datetime available_at,const bool force=false)
  {
   RefreshObjectiveCandidateConsumption(available_at);
   CancelInvalidScenarioPlans(available_at);

   string signature=BuildScenarioLayerSignature();
   if(!force && signature==g_scenario_layer_signature)
      return;
   g_scenario_layer_signature=signature;

   V1ScenarioDraft drafts[];
   ArrayResize(drafts,0);

   for(int i=0;i<ArraySize(g_refinements);i++)
     {
      V1ScenarioDraft draft;
      if(!BuildScenarioDraft(i,draft))
         continue;

      int n=ArraySize(drafts);
      if(ArrayResize(drafts,n+1,16)<0)
         continue;
      drafts[n]=draft;
     }

   bool processed[];
   ArrayResize(processed,ArraySize(drafts));
   ArrayInitialize(processed,false);

   for(int i=0;i<ArraySize(drafts);i++)
     {
      if(processed[i] || !drafts[i].valid)
         continue;

      int matches=0;
      int selected=-1;
      string roots="";

      for(int j=i;j<ArraySize(drafts);j++)
        {
         if(processed[j] || !drafts[j].valid)
            continue;

         if(drafts[j].context_key!=drafts[i].context_key)
            continue;

         processed[j]=true;
         matches++;
         selected=j;
         if(roots!="")
            roots+="|";
         roots+=drafts[j].root_zone_id;
        }

      if(FindActiveScenarioByContextKey(drafts[i].context_key)>=0)
         continue;

      if(matches>1)
        {
         LogLine("SCENARIO_REJECTED",
                 TfName(drafts[i].active_map_tf),
                 available_at,
                 drafts[i].context_key,
                 StringFormat("reason=AMBIGUOUS_ROOT_LINEAGE scope=%s direction=%s candidate_count=%d root_ids=%s",
                              ScenarioScopeName(drafts[i].scope),
                              DirectionName(drafts[i].direction),
                              matches,
                              roots));
         g_scenarios_ambiguous++;
         continue;
        }

      if(selected<0)
         continue;

      V1ObjectiveCandidate family[];
      datetime plan_reference_bar_open=0;
      double plan_reference_price=0.0;
      double primary_horizon=0.0;

      if(!BuildFrozenObjectiveFamily(drafts[selected],
                                     available_at,
                                     plan_reference_bar_open,
                                     plan_reference_price,
                                     primary_horizon,
                                     family))
        {
         LogLine("SCENARIO_REJECTED",
                 TfName(drafts[selected].active_map_tf),
                 available_at,
                 drafts[selected].root_zone_id,
                 StringFormat("reason=NO_OBJECTIVE_FAMILY scope=%s direction=%s root_zone_id=%s final_source_id=%s",
                              ScenarioScopeName(drafts[selected].scope),
                              DirectionName(drafts[selected].direction),
                              drafts[selected].root_zone_id,
                              drafts[selected].final_source_id));
         g_scenarios_no_objective++;
         continue;
        }

      StoreScenarioPlan(drafts[selected],
                        available_at,
                        plan_reference_bar_open,
                        plan_reference_price,
                        primary_horizon,
                        family);
     }
  }

void LogScenarioSnapshot(const datetime available_at)
  {
   int planned=0;
   int canceled=0;
   int continuation=0;
   int reversal=0;

   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(!g_scenarios[i].valid)
         continue;

      if(g_scenarios[i].strategy_state==V1_STRATEGY_CANCELED)
        {
         canceled++;
         continue;
        }

      planned++;
      if(g_scenarios[i].scope==V1_SCOPE_EXTERNAL_CONTINUATION)
         continuation++;
      else if(g_scenarios[i].scope==V1_SCOPE_EXTERNAL_REVERSAL)
         reversal++;
     }

   LogLine("SCENARIO_STATE",
           "",
           available_at,
           "",
           StringFormat("active_planned=%d continuation=%d early_reversal=%d canceled=%d objective_candidates_frozen=%I64d preplan_contact_rejected=%I64d ambiguous=%I64d no_objective=%I64d source_contact_authorization=DEFERRED",
                        planned,
                        continuation,
                        reversal,
                        canceled,
                        g_objective_candidates_frozen,
                        g_scenarios_precontact_rejected,
                        g_scenarios_ambiguous,
                        g_scenarios_no_objective));
  }


void ShiftRecentBars(V1StructureState &s,const MqlRates &bar)
  {
   if(s.recent_count==0)
     {
      s.recent0=bar;
      s.recent_count=1;
      return;
     }

   if(s.recent_count==1)
     {
      s.recent1=bar;
      s.recent_count=2;
      return;
     }

   s.recent0=s.recent1;
   s.recent1=bar;
  }

bool ConfirmWaveIfAny(V1StructureState &s,
                      const MqlRates &bar,
                      const datetime available_at)
  {
   // We need the two previous closed bars plus this newly closed bar.
   if(s.recent_count<2)
      return false;

   MqlRates first=s.recent0;
   MqlRates second=s.recent1;
   MqlRates third=bar;

   // "Three consecutive candles" means consecutive broker bars in the
   // observed series. Clock continuity across a session gap is NOT required
   // for market-structure waves; that strict gate belongs only to the later
   // M1 execution-FVG qualification rule.
   int c1=CandleColour(first);
   int c2=CandleColour(second);
   int c3=CandleColour(third);

   int side=V1_SIDE_NONE;
   if(c1==-1 && c2==-1 && c3==-1)
      side=V1_SIDE_HIGH;
   else if(c1==1 && c2==1 && c3==1)
      side=V1_SIDE_LOW;

   // Doji automatically interrupts because its colour is 0.
   if(side==V1_SIDE_NONE)
      return false;

   // Alternating confirmed-wave contract: do not confirm the same side twice
   // without an opposite confirmed wave in between.
   if(s.last_wave.valid && s.last_wave.side==side)
      return false;

   V1WaveRef wave;
   if(!BuildWaveFromLeg(s,side,third,available_at,wave))
      return false;
   s.confirmed_waves++;

   string detail=StringFormat(
      "side=%s price=%.10f occurred=%s confirmed_bar=%s wick_bottom=%.10f wick_top=%.10f trend_at_confirmation=%s",
      SideName(side),
      wave.price,
      TimeToString(wave.occurred_at,TIME_DATE|TIME_SECONDS),
      TimeToString(third.time,TIME_DATE|TIME_SECONDS),
      wave.wick_bottom,
      wave.wick_top,
      TrendName(s.trend));
   LogLine("WAVE_CONFIRMED",s.name,available_at,wave.id,detail);

   CopyWave(wave,s.last_wave);
   PushRangeWave(s,wave);

   if(s.trend==V1_TREND_NEUTRAL || s.trend==V1_TREND_TRANSITION)
      UpdateNeutralReferences(s,wave);
   else
      UpdateDirectionalWaveRoles(s,wave);

   // The next causal leg begins on the bar AFTER the actual swing occurrence,
   // not after the later confirmation bar.
   s.leg_initialized=true;
   s.leg_start_time=wave.occurred_at+s.seconds;
   return true;
  }


void UpdateDirectionalRanges(V1StructureState &s,const MqlRates &bar)
  {
   if(s.trend==V1_TREND_BULLISH)
     {
      if(s.range_high==0.0)
         s.range_high=bar.high;
      else
         s.range_high=MathMax(s.range_high,bar.high);

      if(s.protected_low.valid)
         s.range_low=s.protected_low.price;
     }
   else if(s.trend==V1_TREND_BEARISH)
     {
      if(s.range_low==0.0)
         s.range_low=bar.low;
      else
         s.range_low=MathMin(s.range_low,bar.low);

      if(s.protected_high.valid)
         s.range_high=s.protected_high.price;
     }
  }


//+------------------------------------------------------------------+
//| Phase 3B targeted causal LTF refinement                          |
//+------------------------------------------------------------------+
void ClearRefinementEvent(V1RefinementEvent &event)
  {
   event.valid=false;
   event.event_type=V1_EVENT_NONE;
   event.direction=0;
   event.available_at=0;
   ZeroMemory(event.break_bar);
   ClearWave(event.meaningful_wave);
   event.event_id="";
  }

void ClearChildCandidate(V1ChildCandidate &candidate)
  {
   candidate.valid=false;
   candidate.tf=PERIOD_CURRENT;
   candidate.direction=0;
   candidate.bottom=0.0;
   candidate.top=0.0;
   candidate.origin_open=0.0;
   candidate.origin_close=0.0;
   candidate.origin_time=0;
   candidate.available_at=0;
   candidate.origin_window_start=0;
   candidate.origin_window_end=0;
   ClearWave(candidate.meaningful_wave);
   candidate.linked_event_type=V1_EVENT_NONE;
   candidate.linked_event_bar_open=0;
   candidate.linked_event_close=0.0;
   candidate.linked_structure_event_id="";
   candidate.containment_type="";
  }

ENUM_TIMEFRAMES RefinementTimeframeByRank(const int rank)
  {
   if(rank==2) return PERIOD_M30;
   if(rank==3) return PERIOD_M15;
   if(rank==4) return PERIOD_M5;
   return PERIOD_CURRENT;
  }

bool ConfirmWaveQuiet(V1StructureState &state,
                      const MqlRates &bar,
                      const datetime available_at)
  {
   if(state.recent_count<2)
      return false;

   MqlRates first=state.recent0;
   MqlRates second=state.recent1;
   MqlRates third=bar;

   int c1=CandleColour(first);
   int c2=CandleColour(second);
   int c3=CandleColour(third);

   int side=V1_SIDE_NONE;
   if(c1==-1 && c2==-1 && c3==-1)
      side=V1_SIDE_HIGH;
   else if(c1==1 && c2==1 && c3==1)
      side=V1_SIDE_LOW;

   if(side==V1_SIDE_NONE)
      return false;

   if(state.last_wave.valid && state.last_wave.side==side)
      return false;

   V1WaveRef wave;
   if(!BuildWaveFromLeg(state,side,third,available_at,wave))
      return false;

   state.confirmed_waves++;
   CopyWave(wave,state.last_wave);

   if(state.trend==V1_TREND_NEUTRAL ||
      state.trend==V1_TREND_TRANSITION)
      UpdateNeutralReferences(state,wave);
   else
      UpdateDirectionalWaveRoles(state,wave);

   state.leg_initialized=true;
   state.leg_start_time=wave.occurred_at+state.seconds;
   return true;
  }

bool EvaluateLocalRefinementBreak(V1StructureState &state,
                                  const MqlRates &bar,
                                  const datetime available_at,
                                  V1RefinementEvent &event)
  {
   ClearRefinementEvent(event);

   if(state.trend==V1_TREND_BULLISH)
     {
      if(state.protected_low.valid &&
         bar.close<state.protected_low.price)
        {
         EnterTransition(state,-1,available_at);
         return false;
        }

      if(state.external_high.valid &&
         bar.close>state.external_high.price)
        {
         V1WaveRef broken,root_origin;
         CopyWave(state.external_high,broken);
         CopyWave(broken,state.break_reference);
         ClearWave(root_origin);

         if(state.correction_low.valid)
           {
            CopyWave(state.correction_low,root_origin);
            CopyWave(state.correction_low,state.protected_low);
           }

         if(state.protected_low.valid)
            CopyWave(state.protected_low,state.external_low);

         state.range_low=
            state.protected_low.valid ? state.protected_low.price : state.range_low;
         BuildDeliveryExtreme(state,
                              V1_SIDE_HIGH,
                              bar,
                              available_at,
                              state.external_high);
         state.range_high=state.external_high.price;
         ClearWave(state.correction_low);

         if(root_origin.valid && root_origin.is_wave)
           {
            event.valid=true;
            event.event_type=V1_EVENT_BOS;
            event.direction=1;
            event.available_at=available_at;
            event.break_bar=bar;
            CopyWave(root_origin,event.meaningful_wave);
            event.event_id=BuildStructureEventId(state,V1_EVENT_BOS,bar);
            return true;
           }

         return false;
        }
     }
   else if(state.trend==V1_TREND_BEARISH)
     {
      if(state.protected_high.valid &&
         bar.close>state.protected_high.price)
        {
         EnterTransition(state,1,available_at);
         return false;
        }

      if(state.external_low.valid &&
         bar.close<state.external_low.price)
        {
         V1WaveRef broken,root_origin;
         CopyWave(state.external_low,broken);
         CopyWave(broken,state.break_reference);
         ClearWave(root_origin);

         if(state.correction_high.valid)
           {
            CopyWave(state.correction_high,root_origin);
            CopyWave(state.correction_high,state.protected_high);
           }

         if(state.protected_high.valid)
            CopyWave(state.protected_high,state.external_high);

         state.range_high=
            state.protected_high.valid ? state.protected_high.price : state.range_high;
         BuildDeliveryExtreme(state,
                              V1_SIDE_LOW,
                              bar,
                              available_at,
                              state.external_low);
         state.range_low=state.external_low.price;
         ClearWave(state.correction_high);

         if(root_origin.valid && root_origin.is_wave)
           {
            event.valid=true;
            event.event_type=V1_EVENT_BOS;
            event.direction=-1;
            event.available_at=available_at;
            event.break_bar=bar;
            CopyWave(root_origin,event.meaningful_wave);
            event.event_id=BuildStructureEventId(state,V1_EVENT_BOS,bar);
            return true;
           }

         return false;
        }
     }
   else
     {
      if(!state.neutral_high.valid || !state.neutral_low.valid)
         return false;

      if(bar.close>state.neutral_high.price)
        {
         V1WaveRef broken,protected_ref;
         CopyWave(state.neutral_high,broken);
         CopyWave(state.neutral_low,protected_ref);

         PromoteInitialTrend(state,1,broken,bar,available_at);
         state.owner_id=BuildStructureEventId(state,V1_EVENT_INITIAL_BOS,bar);
         state.owner_started_at=available_at;

         event.valid=true;
         event.event_type=V1_EVENT_INITIAL_BOS;
         event.direction=1;
         event.available_at=available_at;
         event.break_bar=bar;
         CopyWave(protected_ref,event.meaningful_wave);
         event.event_id=
            BuildStructureEventId(state,V1_EVENT_INITIAL_BOS,bar);
         return true;
        }

      if(bar.close<state.neutral_low.price)
        {
         V1WaveRef broken,protected_ref;
         CopyWave(state.neutral_low,broken);
         CopyWave(state.neutral_high,protected_ref);

         PromoteInitialTrend(state,-1,broken,bar,available_at);
         state.owner_id=BuildStructureEventId(state,V1_EVENT_INITIAL_BOS,bar);
         state.owner_started_at=available_at;

         event.valid=true;
         event.event_type=V1_EVENT_INITIAL_BOS;
         event.direction=-1;
         event.available_at=available_at;
         event.break_bar=bar;
         CopyWave(protected_ref,event.meaningful_wave);
         event.event_id=
            BuildStructureEventId(state,V1_EVENT_INITIAL_BOS,bar);
         return true;
        }
     }

   return false;
  }

bool GeometryActiveThrough(const ENUM_TIMEFRAMES tf,
                           const int direction,
                           const double bottom,
                           const double top,
                           const datetime source_available_at,
                           const datetime through_at)
  {
   if(through_at<=source_available_at)
      return true;

   MqlRates bars[];
   ArraySetAsSeries(bars,false);

   ResetLastError();
   int copied=CopyRates(_Symbol,
                        tf,
                        source_available_at,
                        through_at,
                        bars);
   if(copied<0)
     {
      LogLine("SOURCE_DETECTOR_ERROR",
              TfName(tf),
              through_at,
              "",
              StringFormat("reason=REFINEMENT_VALIDITY_COPYRATES_FAILED from=%s to=%s error=%d",
                           TimeToString(source_available_at,TIME_DATE|TIME_SECONDS),
                           TimeToString(through_at,TIME_DATE|TIME_SECONDS),
                           GetLastError()));
      return false;
     }

   int seconds=PeriodSeconds(tf);
   for(int i=0;i<copied;i++)
     {
      datetime close_at=bars[i].time+seconds;
      if(close_at<=source_available_at || close_at>through_at)
         continue;

      if(direction>0 && bars[i].close<bottom)
         return false;

      if(direction<0 && bars[i].close>top)
         return false;
     }

   return true;
  }

bool SameChildCandidate(const V1ChildCandidate &a,
                        const V1ChildCandidate &b)
  {
   double epsilon=MathMax(_Point,1.0e-10)*0.1;
   return (a.tf==b.tf &&
           a.direction==b.direction &&
           a.origin_time==b.origin_time &&
           MathAbs(a.bottom-b.bottom)<=epsilon &&
           MathAbs(a.top-b.top)<=epsilon);
  }

void AddChildCandidateUnique(V1ChildCandidate &candidates[],
                             const V1ChildCandidate &candidate)
  {
   for(int i=0;i<ArraySize(candidates);i++)
     {
      if(!SameChildCandidate(candidates[i],candidate))
         continue;

      // The same source candle can create more than one later structure
      // delivery event. Its first causal confirmation owns availability.
      if(candidate.available_at<candidates[i].available_at)
         candidates[i]=candidate;
      return;
     }

   int n=ArraySize(candidates);
   if(ArrayResize(candidates,n+1,32)<0)
      return;

   candidates[n]=candidate;
  }

bool CandidateEventAdjacent(const V1SourceZone &parent,
                            const V1ChildCandidate &candidate)
  {
   if(candidate.origin_time<parent.origin_time)
      return false;

   if(parent.origin_window_end>0 &&
      candidate.origin_time>parent.origin_window_end)
      return false;

   if(candidate.meaningful_wave.origin_window_start<
      parent.origin_window_start)
      return false;

   if(candidate.available_at>parent.available_at)
      return false;

   return true;
  }

bool DiscoverChildCandidates(const V1SourceZone &parent,
                             const ENUM_TIMEFRAMES child_tf,
                             const datetime lineage_freeze_at,
                             V1ChildCandidate &candidates[])
  {
   ArrayResize(candidates,0);

   if(!IsRefinementTimeframe(child_tf))
      return true;

   int parent_rank=TimeframeHierarchyRank(parent.tf);
   int child_rank=TimeframeHierarchyRank(child_tf);
   if(child_rank<=parent_rank)
      return true;

   datetime scan_start=parent.origin_window_start;
   if(scan_start<=0)
      scan_start=parent.origin_time;

   datetime scan_end=parent.available_at;
   if(scan_end<=scan_start)
      return true;

   MqlRates bars[];
   ArraySetAsSeries(bars,false);

   ResetLastError();
   int copied=CopyRates(_Symbol,child_tf,scan_start,scan_end,bars);
   if(copied<=0)
     {
      LogLine("SOURCE_DETECTOR_ERROR",
              TfName(child_tf),
              lineage_freeze_at,
              parent.id,
              StringFormat("reason=REFINEMENT_REPLAY_COPYRATES_FAILED parent=%s start=%s end=%s error=%d",
                           parent.id,
                           TimeToString(scan_start,TIME_DATE|TIME_SECONDS),
                           TimeToString(scan_end,TIME_DATE|TIME_SECONDS),
                           GetLastError()));
      return false;
     }

   V1StructureState local_state;
   ResetStructureState(local_state,child_tf);

   int seconds=PeriodSeconds(child_tf);

   for(int i=0;i<copied;i++)
     {
      datetime available=bars[i].time+seconds;
      if(available>parent.available_at)
         continue;

      local_state.processed_bars++;
      EnsureLegStart(local_state,bars[i]);

      V1RefinementEvent event;
      bool has_event=
         EvaluateLocalRefinementBreak(local_state,
                                      bars[i],
                                      available,
                                      event);

      UpdateDirectionalRanges(local_state,bars[i]);
      ConfirmWaveQuiet(local_state,bars[i],available);
      ShiftRecentBars(local_state,bars[i]);

      if(!has_event ||
         !event.valid ||
         event.direction!=parent.direction)
         continue;

      MqlRates origin_bar;
      ZeroMemory(origin_bar);

      if(!FindLastOppositeCandleInSwingOrigin(child_tf,
                                              event.direction,
                                              event.meaningful_wave,
                                              origin_bar))
         continue;

      // Frozen same-price-event time relation.
      if(origin_bar.time<parent.origin_time ||
         (parent.origin_window_end>0 &&
          origin_bar.time>parent.origin_window_end) ||
         origin_bar.time>event.available_at ||
         event.available_at>parent.available_at)
         continue;

      if(SourcePathHasSessionGap(child_tf,
                                 origin_bar.time,
                                 event.break_bar.time))
         continue;

      V1ChildCandidate candidate;
      ClearChildCandidate(candidate);

      candidate.valid=true;
      candidate.tf=child_tf;
      candidate.direction=event.direction;
      candidate.bottom=origin_bar.low;
      candidate.top=origin_bar.high;
      candidate.origin_open=origin_bar.open;
      candidate.origin_close=origin_bar.close;
      candidate.origin_time=origin_bar.time;
      candidate.available_at=event.available_at;
      candidate.origin_window_start=
         event.meaningful_wave.origin_window_start;
      candidate.origin_window_end=
         event.meaningful_wave.origin_window_end;
      CopyWave(event.meaningful_wave,candidate.meaningful_wave);
      candidate.linked_event_type=event.event_type;
      candidate.linked_event_bar_open=event.break_bar.time;
      candidate.linked_event_close=event.break_bar.close;
      candidate.linked_structure_event_id=event.event_id;

      bool contained=
         (parent.bottom<=candidate.bottom &&
          candidate.top<=parent.top);

      if(contained)
         candidate.containment_type="CONTAINED";
      else if(CandidateEventAdjacent(parent,candidate))
         candidate.containment_type="EVENT_ADJACENT";
      else
         continue;

      // Candidate must still be structurally ACTIVE when the Root lineage
      // is first frozen. Later invalidation must not resolve an ambiguity
      // retrospectively.
      if(!GeometryActiveThrough(child_tf,
                                candidate.direction,
                                candidate.bottom,
                                candidate.top,
                                candidate.available_at,
                                lineage_freeze_at))
         continue;

      AddChildCandidateUnique(candidates,candidate);
     }

   return true;
  }

string BuildChildId(const V1SourceZone &parent,
                    const V1ChildCandidate &candidate)
  {
   return StringFormat("%s:child:%s:%I64d:%s:parent:%s",
                       TfName(candidate.tf),
                       DirectionName(candidate.direction),
                       (long)candidate.origin_time,
                       candidate.linked_structure_event_id,
                       parent.id);
  }

void CandidateToSourcePreview(const V1SourceZone &parent,
                              const V1SourceZone &root,
                              const V1ChildCandidate &candidate,
                              V1SourceZone &child)
  {
   child.valid=true;
   child.id=BuildChildId(parent,candidate);
   child.kind=V1_SOURCE_CHILD;
   child.tf=candidate.tf;
   child.direction=candidate.direction;

   child.bottom=candidate.bottom;
   child.top=candidate.top;
   child.origin_open=candidate.origin_open;
   child.origin_close=candidate.origin_close;

   child.origin_index=iBarShift(_Symbol,
                                candidate.tf,
                                candidate.origin_time,
                                true);
   child.origin_time=candidate.origin_time;
   child.occurred_at=candidate.origin_time;
   child.available_at=candidate.available_at;
   child.origin_window_start=candidate.origin_window_start;
   child.origin_window_end=candidate.origin_window_end;

   child.origin_wave_id=candidate.meaningful_wave.id;
   child.meaningful_swing_id=candidate.meaningful_wave.id;
   child.linked_structure_event_id=
      candidate.linked_structure_event_id;

   child.parent_zone_id=parent.id;
   child.root_zone_id=root.id;
   child.scenario_owner_id="";

   child.containment_type=candidate.containment_type;
   child.linked_event_type=candidate.linked_event_type;
   child.linked_event_bar_open=
      candidate.linked_event_bar_open;

   child.strategy_state=V1_SOURCE_ACTIVE;
   child.invalidated_at=0;
   child.invalidation_reason="";
  }

void LogChildCreated(const V1SourceZone &child,
                     const datetime lineage_frozen_at)
  {
   string detail=StringFormat(
      "kind=CHILD state=ACTIVE direction=%s parent_zone_id=%s root_zone_id=%s bottom=%.10f top=%.10f origin_open=%.10f origin_close=%.10f origin_time=%s origin_window_start=%s origin_window_end=%s origin_wave_id=%s linked_event_type=%s linked_structure_event_id=%s linked_event_bar_open=%s containment_type=%s child_available_at=%s lineage_frozen_at=%s scenario_owner_id=UNBOUND scenario_authority=false",
      DirectionName(child.direction),
      child.parent_zone_id,
      child.root_zone_id,
      child.bottom,
      child.top,
      child.origin_open,
      child.origin_close,
      TimeToString(child.origin_time,TIME_DATE|TIME_SECONDS),
      TimeToString(child.origin_window_start,TIME_DATE|TIME_SECONDS),
      TimeToString(child.origin_window_end,TIME_DATE|TIME_SECONDS),
      child.origin_wave_id,
      EventName(child.linked_event_type),
      child.linked_structure_event_id,
      TimeToString(child.linked_event_bar_open,TIME_DATE|TIME_SECONDS),
      child.containment_type,
      TimeToString(child.available_at,TIME_DATE|TIME_SECONDS),
      TimeToString(lineage_frozen_at,TIME_DATE|TIME_SECONDS));

   LogLine("CHILD_CREATED",
           TfName(child.tf),
           lineage_frozen_at,
           child.id,
           detail);
  }

bool AddActiveChildSource(const V1SourceZone &child,
                          const datetime lineage_frozen_at)
  {
   if(FindActiveSourceById(child.id)>=0)
      return true;

   int n=ArraySize(g_sources);
   if(ArrayResize(g_sources,n+1,128)<0)
     {
      LogLine("SOURCE_DETECTOR_ERROR",
              TfName(child.tf),
              lineage_frozen_at,
              child.root_zone_id,
              "reason=CHILD_SOURCE_ARRAY_RESIZE_FAILED");
      return false;
     }

   g_sources[n]=child;
   g_children_created++;
   LogChildCreated(g_sources[n],lineage_frozen_at);
   return true;
  }

void StoreRefinementLineage(const V1RefinementLineage &lineage)
  {
   int existing=FindRefinementByRootId(lineage.root_zone_id);
   if(existing>=0)
     {
      g_refinements[existing]=lineage;
      return;
     }

   int n=ArraySize(g_refinements);
   if(ArrayResize(g_refinements,n+1,64)<0)
      return;

   g_refinements[n]=lineage;
  }

void LogRefinementFrozen(const V1RefinementLineage &lineage)
  {
   string detail=StringFormat(
      "status=%s child_count=%d final_child_id=%s path=%s frozen_at=%s snapshot_at=%s stop_reason=%s scenario_authority=false",
      RefinementStatusName(lineage.status),
      lineage.child_count,
      lineage.final_child_id=="" ? "NA" : lineage.final_child_id,
      lineage.path=="" ? lineage.root_zone_id : lineage.path,
      TimeToString(lineage.frozen_at,TIME_DATE|TIME_SECONDS),
      TimeToString(lineage.snapshot_at,TIME_DATE|TIME_SECONDS),
      lineage.stop_reason=="" ? "NA" : lineage.stop_reason);

   LogLine("REFINEMENT_FROZEN",
           "",
           lineage.frozen_at,
           lineage.root_zone_id,
           detail);
  }

bool BuildRefinementForRoot(const string root_id,
                            const datetime snapshot_at)
  {
   if(FindRefinementByRootId(root_id)>=0)
      return true;

   int root_index=FindActiveSourceById(root_id);
   if(root_index<0 ||
      g_sources[root_index].kind!=V1_SOURCE_ROOT)
      return false;

   V1SourceZone root=g_sources[root_index];
   datetime freeze_at=root.available_at;
   datetime snapshot=(snapshot_at>freeze_at ? snapshot_at : freeze_at);

   V1SourceZone selected_sources[];
   ArrayResize(selected_sources,0);

   V1SourceZone current_parent=root;

   int status=V1_REFINE_WAITING;
   string stop_reason="";

   int start_rank=TimeframeHierarchyRank(root.tf)+1;

   for(int rank=start_rank;rank<=4;rank++)
     {
      ENUM_TIMEFRAMES child_tf=RefinementTimeframeByRank(rank);
      if(child_tf==PERIOD_CURRENT)
         continue;

      V1ChildCandidate candidates[];
      ArrayResize(candidates,0);

      if(!DiscoverChildCandidates(current_parent,
                                  child_tf,
                                  freeze_at,
                                  candidates))
        {
         status=(ArraySize(selected_sources)==0 ?
                 V1_REFINE_NO_CHILD :
                 V1_REFINE_READY);
         stop_reason="REFINEMENT_REPLAY_ERROR_FAIL_CLOSED";
         break;
        }

      int contained_count=0;
      for(int i=0;i<ArraySize(candidates);i++)
         if(candidates[i].containment_type=="CONTAINED")
            contained_count++;

      V1ChildCandidate preferred[];
      ArrayResize(preferred,0);

      for(int i=0;i<ArraySize(candidates);i++)
        {
         if(contained_count>0 &&
            candidates[i].containment_type!="CONTAINED")
            continue;

         int n=ArraySize(preferred);
         if(ArrayResize(preferred,n+1,16)<0)
            continue;
         preferred[n]=candidates[i];
        }

      if(ArraySize(preferred)==0)
         continue;

      if(ArraySize(preferred)>1)
        {
         if(ArraySize(selected_sources)==0)
           {
            status=V1_REFINE_AMBIGUOUS_FIRST;
            stop_reason=StringFormat("AMBIGUOUS_%s_CHILD_COUNT_%d",
                                     TfName(child_tf),
                                     ArraySize(preferred));
            g_refinements_ambiguous++;
           }
         else
           {
            status=V1_REFINE_STOPPED_AMBIGUOUS;
            stop_reason=StringFormat("STOPPED_AT_AMBIGUOUS_%s_CHILD_COUNT_%d",
                                     TfName(child_tf),
                                     ArraySize(preferred));
            g_refinements_ambiguous++;
           }
         break;
        }

      V1SourceZone preview;
      CandidateToSourcePreview(current_parent,
                               root,
                               preferred[0],
                               preview);

      int n=ArraySize(selected_sources);
      if(ArrayResize(selected_sources,n+1,8)<0)
        {
         status=(n==0 ? V1_REFINE_NO_CHILD : V1_REFINE_READY);
         stop_reason="SELECTED_CHILD_ARRAY_RESIZE_FAILED";
         break;
        }

      selected_sources[n]=preview;
      current_parent=preview;
     }

   if(status==V1_REFINE_WAITING)
     {
      if(ArraySize(selected_sources)==0)
        {
         status=V1_REFINE_NO_CHILD;
         stop_reason="NO_CAUSAL_LOWER_TF_CHILD";
        }
      else
         status=V1_REFINE_READY;
     }

   string path=root.id;
   string final_child_id="";

   for(int i=0;i<ArraySize(selected_sources);i++)
     {
      path=path+">"+selected_sources[i].id;
      final_child_id=selected_sources[i].id;
     }

   // Bootstrap snapshot can be later than the historical lineage-freeze time.
   // Do not let a child that was later price-invalidated remain in the active
   // working set. This does not use later invalidation to resolve ambiguity;
   // ambiguity was already decided using freeze_at above.
   bool active_at_snapshot=true;
   for(int i=0;i<ArraySize(selected_sources);i++)
     {
      if(!GeometryActiveThrough(selected_sources[i].tf,
                                selected_sources[i].direction,
                                selected_sources[i].bottom,
                                selected_sources[i].top,
                                freeze_at,
                                snapshot))
        {
         active_at_snapshot=false;
         stop_reason="SELECTED_CHILD_INVALID_AT_SNAPSHOT";
         status=V1_REFINE_INVALIDATED;
         break;
        }
     }

   if(active_at_snapshot &&
      ArraySize(selected_sources)>0 &&
      status!=V1_REFINE_AMBIGUOUS_FIRST &&
      status!=V1_REFINE_NO_CHILD)
     {
      for(int i=0;i<ArraySize(selected_sources);i++)
        {
         if(!AddActiveChildSource(selected_sources[i],freeze_at))
           {
            status=V1_REFINE_INVALIDATED;
            stop_reason="CHILD_PUBLICATION_FAILED";
            active_at_snapshot=false;
            break;
           }

        }
     }

   V1RefinementLineage lineage;
   lineage.valid=true;
   lineage.root_zone_id=root.id;
   lineage.final_child_id=final_child_id;
   lineage.path=path;
   lineage.child_count=ArraySize(selected_sources);
   lineage.status=status;
   lineage.frozen_at=freeze_at;
   lineage.snapshot_at=snapshot;
   lineage.stop_reason=stop_reason;
   lineage.preplan_contact_at=0;

   StoreRefinementLineage(lineage);

   if(status==V1_REFINE_READY ||
      status==V1_REFINE_STOPPED_AMBIGUOUS)
      g_refinements_ready++;
   else if(status==V1_REFINE_NO_CHILD)
      g_refinements_no_child++;
   else if(status==V1_REFINE_AMBIGUOUS_FIRST)
     {
      // Counter already incremented above.
     }

   LogRefinementFrozen(lineage);
   return true;
  }

void BuildRefinementsForActiveRoots(const datetime snapshot_at)
  {
   string root_ids[];
   ArrayResize(root_ids,0);

   for(int i=0;i<ArraySize(g_sources);i++)
     {
      if(!g_sources[i].valid ||
         g_sources[i].kind!=V1_SOURCE_ROOT ||
         g_sources[i].strategy_state!=V1_SOURCE_ACTIVE)
         continue;

      int n=ArraySize(root_ids);
      if(ArrayResize(root_ids,n+1,32)<0)
         continue;
      root_ids[n]=g_sources[i].id;
     }

   for(int i=0;i<ArraySize(root_ids);i++)
      BuildRefinementForRoot(root_ids[i],snapshot_at);
  }

void QueueRefinementRoot(const string root_id)
  {
   if(root_id=="")
      return;

   for(int i=0;i<ArraySize(g_pending_refinement_root_ids);i++)
      if(g_pending_refinement_root_ids[i]==root_id)
         return;

   int n=ArraySize(g_pending_refinement_root_ids);
   if(ArrayResize(g_pending_refinement_root_ids,n+1,16)<0)
      return;

   g_pending_refinement_root_ids[n]=root_id;
  }

void ProcessPendingRefinements(const datetime snapshot_at)
  {
   if(ArraySize(g_pending_refinement_root_ids)==0)
      return;

   string pending[];
   ArrayResize(pending,ArraySize(g_pending_refinement_root_ids));

   for(int i=0;i<ArraySize(g_pending_refinement_root_ids);i++)
      pending[i]=g_pending_refinement_root_ids[i];

   ArrayResize(g_pending_refinement_root_ids,0);

   for(int i=0;i<ArraySize(pending);i++)
      BuildRefinementForRoot(pending[i],snapshot_at);
  }

int CountActiveChildren(const ENUM_TIMEFRAMES tf)
  {
   int count=0;
   for(int i=0;i<ArraySize(g_sources);i++)
     {
      if(g_sources[i].valid &&
         g_sources[i].kind==V1_SOURCE_CHILD &&
         g_sources[i].strategy_state==V1_SOURCE_ACTIVE &&
         g_sources[i].tf==tf)
         count++;
     }
   return count;
  }

void LogRefinementSnapshot(const int tf_index,
                           const datetime available_at)
  {
   if(!IsRootTimeframeIndex(tf_index))
      return;

   int ready=0;
   int no_child=0;
   int ambiguous=0;
   int invalidated=0;

   ENUM_TIMEFRAMES root_tf=g_timeframes[tf_index];

   for(int i=0;i<ArraySize(g_refinements);i++)
     {
      if(!g_refinements[i].valid)
         continue;

      int root_index=FindActiveSourceById(g_refinements[i].root_zone_id);
      if(root_index<0 ||
         g_sources[root_index].kind!=V1_SOURCE_ROOT ||
         g_sources[root_index].tf!=root_tf)
         continue;

      if(g_refinements[i].status==V1_REFINE_READY ||
         g_refinements[i].status==V1_REFINE_STOPPED_AMBIGUOUS)
         ready++;
      else if(g_refinements[i].status==V1_REFINE_NO_CHILD)
         no_child++;
      else if(g_refinements[i].status==V1_REFINE_AMBIGUOUS_FIRST)
         ambiguous++;
      else if(g_refinements[i].status==V1_REFINE_INVALIDATED)
         invalidated++;
     }

   string detail=StringFormat(
      "ready=%d no_child=%d ambiguous_first=%d invalidated=%d active_m30_children=%d active_m15_children=%d active_m5_children=%d structural_reaction=DEFERRED_TO_REFINED_SOURCE_REACTION_REPLAY",
      ready,
      no_child,
      ambiguous,
      invalidated,
      CountActiveChildren(PERIOD_M30),
      CountActiveChildren(PERIOD_M15),
      CountActiveChildren(PERIOD_M5));

   LogLine("REFINEMENT_STATE",
           TfName(root_tf),
           available_at,
           "",
           detail);
  }

void ProcessClosedBar(const int tf_index,
                      const MqlRates &bar,
                      const datetime available_at)
  {
   g_structure[tf_index].processed_bars++;

   EnsureLegStart(g_structure[tf_index],bar);

   // Frozen within-close order:
   // 1) consume/invalidate pre-existing objects
   // 2) update structure state
   // 3) publish newly confirmed objects
   // 4) dependent authorization (not yet attached)
   //
   // Liquidity consumption comes first so a pool created at this same close
   // can never self-sweep from the bar's already-completed wick.
   EvaluateLiquidityConsumption(tf_index,bar,available_at);
   EvaluateRootPriceInvalidation(tf_index,bar,available_at);
   EvaluateChildPriceInvalidation(tf_index,bar,available_at);

   // H1 reversal-reference interaction uses only the reference that existed
   // before this close. New references are published after structure update.
   if(tf_index==1)
      EvaluateH1ReversalReference(bar,available_at);

   EvaluateExistingStructureBreaks(tf_index,
                                   g_structure[tf_index],
                                   bar,
                                   available_at);
   UpdateDirectionalRanges(g_structure[tf_index],bar);

   bool new_wave=ConfirmWaveIfAny(g_structure[tf_index],bar,available_at);

   // Structural rank may have changed either through BOS/INITIAL_BOS or through
   // the newly confirmed wave. Only confirmed WAVE references can create
   // EXTERNAL_SWING liquidity; synthetic delivery extremes cannot.
   RegisterCurrentExternalLiquidity(tf_index,available_at);

   if(new_wave)
      TryCreateDefendedRangeLiquidity(tf_index,bar,available_at);

   ShiftRecentBars(g_structure[tf_index],bar);

   // This is audit-only. It does not activate trigger search in Phase 4B.
   // It only blocks retrospective PLAN creation after an already-passed source.
   if(tf_index==5)
      AuditPrePlanSourceContact(bar,available_at);

   if(tf_index==1 || tf_index==2)
      RefreshMapControlAfterStructure(available_at);
  }

//+------------------------------------------------------------------+
//| Bootstrap                                                        |
//+------------------------------------------------------------------+
bool BootstrapStructureCore()
  {
   datetime now=TimeCurrent();

   MqlRates h4[],h1[],m30[],m15[];
   if(!LoadFullRates(PERIOD_H4,h4) ||
      !LoadFullRates(PERIOD_H1,h1) ||
      !LoadFullRates(PERIOD_M30,m30) ||
      !LoadFullRates(PERIOD_M15,m15))
      return false;

   int closed[4];
   closed[0]=ClosedCount(h4,PeriodSeconds(PERIOD_H4),now);
   closed[1]=ClosedCount(h1,PeriodSeconds(PERIOD_H1),now);
   closed[2]=ClosedCount(m30,PeriodSeconds(PERIOD_M30),now);
   closed[3]=ClosedCount(m15,PeriodSeconds(PERIOD_M15),now);

   int pos[4]={0,0,0,0};

   g_init_state=V1_INIT_H4_INDEX;
   LogLine("INIT_STATE","",now,"",InitStateName(g_init_state));
   g_in_bootstrap_replay=true;

   // Chronological multiway merge.
   // Tie priority is H4 -> H1 -> M30 -> M15.
   while(true)
     {
      int selected=-1;
      datetime selected_available=0;

      for(int k=0;k<4;k++)
        {
         if(pos[k]>=closed[k])
            continue;

         datetime available=0;
         if(k==0)
            available=HistoricalAvailableAt(h4,pos[k],PeriodSeconds(PERIOD_H4));
         else if(k==1)
            available=HistoricalAvailableAt(h1,pos[k],PeriodSeconds(PERIOD_H1));
         else if(k==2)
            available=HistoricalAvailableAt(m30,pos[k],PeriodSeconds(PERIOD_M30));
         else
            available=HistoricalAvailableAt(m15,pos[k],PeriodSeconds(PERIOD_M15));

         if(available>now)
            continue;

         if(selected<0 ||
            available<selected_available ||
            (available==selected_available && k<selected))
           {
            selected=k;
            selected_available=available;
           }
        }

      if(selected<0)
         break;

      if(selected==0)
         ProcessClosedBar(0,h4[pos[0]++],selected_available);
      else if(selected==1)
         ProcessClosedBar(1,h1[pos[1]++],selected_available);
      else if(selected==2)
         ProcessClosedBar(2,m30[pos[2]++],selected_available);
      else
         ProcessClosedBar(3,m15[pos[3]++],selected_available);
     }

   g_in_bootstrap_replay=false;

   // Hierarchical bootstrap: first reconstruct active H1/M30/M15 Roots,
   // then perform targeted lower-TF replay only for those surviving Roots.
   BuildRefinementsForActiveRoots(now);

   // A source already crossed after its refinement freeze cannot receive a
   // retrospective scenario at startup.
   AuditBootstrapPrePlanContacts(now);
   RefreshScenarioLayer(now,true);

   g_init_state=V1_INIT_ACTIVE_MAP;
   LogLine("INIT_STATE","",now,"",InitStateName(g_init_state));

   g_init_state=V1_INIT_SOURCE_CONTEXT;
   LogLine("INIT_STATE","",now,"","PHASE4B_SCENARIO_OBJECTIVE_READY_SOURCE_CONTACT_NOT_YET_ATTACHED");

   for(int i=0;i<V1_TF_COUNT;i++)
     {
      g_last_current_open[i]=iTime(_Symbol,g_timeframes[i],0);
      g_cursor_bar_pending[i]=false;

      if(g_last_current_open[i]>0)
        {
         datetime theoretical_close=
            g_last_current_open[i]+PeriodSeconds(g_timeframes[i]);

         // If the latest visible slot is still open at READY, it must be
         // processed once a later bar appears. If it already closed before
         // READY (typical weekend/session closure), bootstrap has either
         // processed it or Phase-1 runtime intentionally starts after it.
         g_cursor_bar_pending[i]=(theoretical_close>now);
        }

      if(g_history_first_date[i]>0)
         LogLine("HISTORY_FIRST_DATE",
                 TfName(g_timeframes[i]),
                 now,
                 "",
                 TimeToString(g_history_first_date[i],TIME_DATE|TIME_SECONDS));
     }

   // M5 / M1 execution structure intentionally starts clean at READY.
   InitStructureState(4);
   InitStructureState(5);

   g_bootstrap_ready_at=now;
   g_init_state=V1_READY;
   g_bootstrap_finished=true;

   int h4_long_horizon_count=
      CountActiveLiquidity(PERIOD_H4,V1_LIQ_EXTERNAL_SWING);

   LogLine("INIT_STATE","",g_bootstrap_ready_at,"",
           StringFormat("READY_PHASE4B_SCENARIO_OBJECTIVE ready_at=%s h4_long_horizon_external=%d active_liquidity_total=%d active_sources=%d",
                        TimeToString(g_bootstrap_ready_at,TIME_DATE|TIME_SECONDS),
                        h4_long_horizon_count,
                        ArraySize(g_liquidity),
                        ArraySize(g_sources)));

   for(int i=0;i<4;i++)
     {
      LogStateSnapshot(i,now,"BOOTSTRAP_COMPLETE");
      LogLiquiditySnapshot(i,now);
      LogRootSnapshot(i,now);
      LogRefinementSnapshot(i,now);
     }

   LogMapSnapshot(now,"BOOTSTRAP_COMPLETE",true);
   LogScenarioSnapshot(now);

   return true;
  }

bool TryInitialize()
  {
   if(g_bootstrap_finished)
      return true;

   if(!AllSeriesSynchronized())
     {
      g_init_state=V1_INIT_SYNCING;
      KickHistoryRequests();
      return false;
     }

   if(g_bootstrap_started)
      return false;

   g_bootstrap_started=true;
   bool ok=BootstrapStructureCore();
   if(!ok)
     {
      g_bootstrap_started=false;
      g_init_state=V1_INIT_SYNCING;
      KickHistoryRequests();
      return false;
     }

   return true;
  }

//+------------------------------------------------------------------+
//| Runtime closed-bar scheduler                                     |
//+------------------------------------------------------------------+
void AddRuntimeEvent(V1RuntimeBarEvent &events[],
                     const int tf_index,
                     const MqlRates &bar,
                     const datetime available_at)
  {
   int n=ArraySize(events);
   ArrayResize(events,n+1);
   events[n].tf_index=tf_index;
   events[n].bar=bar;
   events[n].available_at=available_at;
  }

void CollectNewClosedBars(const int tf_index,
                          V1RuntimeBarEvent &events[],
                          const datetime observed_at)
  {
   if(observed_at<=0)
      return;

   ENUM_TIMEFRAMES tf=g_timeframes[tf_index];
   datetime current_open=iTime(_Symbol,tf,0);
   if(current_open<=0)
      return;

   if(g_last_current_open[tf_index]==0)
     {
      g_last_current_open[tf_index]=current_open;
      return;
     }

   if(current_open<=g_last_current_open[tf_index])
      return;

   MqlRates rates[];
   ArraySetAsSeries(rates,false);

   // Include the old current bar through the new current bar.
   ResetLastError();
   int copied=CopyRates(_Symbol,
                        tf,
                        g_last_current_open[tf_index],
                        current_open,
                        rates);
   if(copied<=1)
     {
      // Do not advance the cursor if the history interval is not ready.
      PrintFormat("MentorV1 runtime CopyRates retry tf=%s copied=%d err=%d",
                  TfName(tf),copied,GetLastError());
      return;
     }

   int first_index=(g_cursor_bar_pending[tf_index] ? 0 : 1);

   for(int i=first_index;i<copied-1;i++)
     {
      datetime available=rates[i].time+PeriodSeconds(tf);
      if(available>observed_at)
         available=observed_at;

      AddRuntimeEvent(events,tf_index,rates[i],available);
     }

   g_last_current_open[tf_index]=current_open;
   g_cursor_bar_pending[tf_index]=true;
  }

void SortRuntimeEvents(V1RuntimeBarEvent &events[])
  {
   int n=ArraySize(events);
   for(int i=1;i<n;i++)
     {
      V1RuntimeBarEvent key=events[i];
      int j=i-1;
      while(j>=0)
        {
         bool later=(events[j].available_at>key.available_at);
         bool same_but_lower_priority=
            (events[j].available_at==key.available_at &&
             events[j].tf_index>key.tf_index);

         if(!later && !same_but_lower_priority)
            break;

         events[j+1]=events[j];
         j--;
        }
      events[j+1]=key;
     }
  }

void ProcessRuntimeClosedBars(const datetime observed_at)
  {
   V1RuntimeBarEvent events[];
   ArrayResize(events,0);

   for(int i=0;i<V1_TF_COUNT;i++)
      CollectNewClosedBars(i,events,observed_at);

   if(ArraySize(events)==0)
      return;

   SortRuntimeEvents(events);

   datetime group_time=0;

   for(int i=0;i<ArraySize(events);i++)
     {
      if(group_time!=0 &&
         events[i].available_at!=group_time)
        {
         // Dependent source refinement is evaluated only after every
         // H4/H1/M30/M15/M5/M1 close sharing the timestamp has been processed.
         ProcessPendingRefinements(group_time);
         RefreshScenarioLayer(group_time);
        }

      group_time=events[i].available_at;

      ProcessClosedBar(events[i].tf_index,
                       events[i].bar,
                       events[i].available_at);
     }

   if(group_time!=0)
     {
      ProcessPendingRefinements(group_time);
      RefreshScenarioLayer(group_time);
     }

   // Source-contact / trigger / order authorization remains deferred.
  }

//+------------------------------------------------------------------+
//| MQL5 event handlers                                              |
//+------------------------------------------------------------------+
int OnInit()
  {
   InitializeAllStructureStates();

   if(InpWriteEventCsv)
     {
      g_log_handle=FileOpen(InpEventCsvFile,
                            FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_SHARE_READ,
                            ',');
      if(g_log_handle!=INVALID_HANDLE)
        {
         if(FileSize(g_log_handle)==0)
            FileWrite(g_log_handle,
                      "observed_at",
                      "event",
                      "timeframe",
                      "available_at",
                      "object_id",
                      "detail");
         FileSeek(g_log_handle,0,SEEK_END);
        }
      else
        {
         PrintFormat("MentorV1 failed to open event CSV '%s', err=%d",
                     InpEventCsvFile,GetLastError());
        }
     }

   EventSetTimer(1);
   KickHistoryRequests();

   LogLine("EA_START","",TimeCurrent(),"",
           StringFormat("build=0.60 property_version=1.00 magic=%I64d phase=SCENARIO_OBJECTIVE_CORE",
                        InpMagicNumber));

   // Do not fail initialization just because MT5 is still synchronizing history.
   TryInitialize();
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();

   LogLine("EA_STOP","",TimeCurrent(),"",
           StringFormat("reason=%d init_state=%s active_liquidity=%d liquidity_created=%I64d sweeps=%I64d body_deliveries=%I64d active_sources=%d roots_created=%I64d root_price_invalidated=%I64d root_structure_invalidated=%I64d children_created=%I64d children_invalidated=%I64d refinements_ready=%I64d refinements_no_child=%I64d refinements_ambiguous=%I64d reference_touches=%I64d reference_sweeps=%I64d reference_continuations=%I64d permission_opens=%I64d permission_closes=%I64d reversal_permission=%s scenarios_planned=%I64d scenarios_canceled=%I64d scenarios_ambiguous=%I64d scenarios_no_objective=%I64d preplan_contact_rejected=%I64d objective_candidates_frozen=%I64d",
                        reason,
                        InitStateName(g_init_state),
                        ArraySize(g_liquidity),
                        g_liquidity_created,
                        g_liquidity_sweeps,
                        g_liquidity_body_deliveries,
                        ArraySize(g_sources),
                        g_roots_created,
                        g_roots_price_invalidated,
                        g_roots_structure_invalidated,
                        g_children_created,
                        g_children_invalidated,
                        g_refinements_ready,
                        g_refinements_no_child,
                        g_refinements_ambiguous,
                        g_reference_touches,
                        g_reference_sweeps,
                        g_reference_continuations,
                        g_permission_opens,
                        g_permission_closes,
                        ReversalPermissionName(g_map.reversal_permission),
                        g_scenarios_planned,
                        g_scenarios_canceled,
                        g_scenarios_ambiguous,
                        g_scenarios_no_objective,
                        g_scenarios_precontact_rejected,
                        g_objective_candidates_frozen));

   if(g_log_handle!=INVALID_HANDLE)
     {
      FileFlush(g_log_handle);
      FileClose(g_log_handle);
      g_log_handle=INVALID_HANDLE;
     }
  }

void OnTimer()
  {
   if(g_init_state!=V1_READY)
      TryInitialize();
  }

void OnTick()
  {
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return;

   if(g_init_state!=V1_READY)
     {
      TryInitialize();
      if(g_init_state!=V1_READY)
         return;
     }

   if(g_execution_epoch_start==0)
     {
      g_execution_epoch_start=(datetime)tick.time;
      LogLine("EXECUTION_EPOCH_START","M1",g_execution_epoch_start,"",
              "Phase4B trading disabled; scenario/objective PLAN may freeze before source contact");
     }

   ProcessRuntimeClosedBars((datetime)tick.time);

   // No trade submission in Phase 4B.
  }
//+------------------------------------------------------------------+
