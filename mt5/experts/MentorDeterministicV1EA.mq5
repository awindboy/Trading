//+------------------------------------------------------------------+
//| MentorDeterministicV1EA_RegimeResearchV1.mq5                    |
//| Frozen Regime Research V1 variant on D-135A / build 1.91 core   |
//|                                                                  |
//| Authority:                                                       |
//|   AGENTS.md                                                      |
//|   docs/ea/EA_SPEC.md                                             |
//|                                                                  |
//| D135A canceled-pending lifecycle hotfix on D135 performance core. |
//| Root -> Sweep -> CHoCH -> causal fresh widest FVG -> geometry.       |
//| D134 strategy semantics unchanged; canceled live pending stays managed.       |
//| Opposite-direction coexistence is blocked; each scenario owns its lifecycle.   |
//| Live trading remains hard-blocked; tester execution only.        |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "Mentor deterministic V1 EA - frozen M30 Regime Research V1 variant"

enum V1StopLossModel
  {
   V1_SL_FVG_DISTAL_20=0,
   V1_SL_SWEEP_EXTREME,
   V1_SL_ROOT_OB_DISTAL_20
  };

enum V1RegimeResearchMode
  {
   // Preserve the existing numeric identities for saved Strategy Tester sets.
   V1_REGIME_PARENT_CLEAN_PERSISTENT=0,
   V1_REGIME_V1_CLEAN_PERSISTENT_EXPANDING=1,
   // Baseline control: no regime gate is allowed to reject a scenario.
   V1_REGIME_BASELINE_NO_GATE=2
  };

// Logging is diagnostic-only and has no strategy authority.
// RESEARCH_COMPACT keeps the causal facts needed for long-run regime analysis
// and execution reconstruction while suppressing high-volume detector chatter.
enum V1EventLogMode
  {
   V1_LOG_RESEARCH_COMPACT=0,
   V1_LOG_FULL_AUDIT
  };

//--- execution identity / diagnostics
input long   InpMagicNumber        = 26081901;
input bool   InpWriteEventCsv      = true;
input bool   InpVerboseLog         = false;
input bool   InpLogBootstrapEvents = false;
input V1StopLossModel InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20;
input V1RegimeResearchMode InpRegimeResearchMode = V1_REGIME_V1_CLEAN_PERSISTENT_EXPANDING;
input V1EventLogMode InpEventLogMode = V1_LOG_RESEARCH_COMPACT;
input string InpEventCsvFile       = "mentor_v1_regime_research_v1_compact_events.csv";

// D-137/D-138 frozen research contract. These are intentionally NOT inputs:
// 2022 OOS must not be tunable from Strategy Tester parameters.
#define V1_REGIME_WAVE_COUNT                 12
#define V1_REGIME_PROGRESSION_NUM             2
#define V1_REGIME_PROGRESSION_DEN             3
#define V1_REGIME_MAX_PROTECTED_BREAKS         1
#define V1_REGIME_LEG_GROUP                    4
#define V1_REGIME_EXPANSION_THRESHOLD        1.0

// IMPORTANT:
// This build may submit orders ONLY inside MT5 Strategy Tester. Live trading
// remains hard-blocked even if terminal/account Algo Trading permissions exist.
// V1 uses MINIMUM_VOLUME_PARITY and the frozen FVG/SL/TP geometry.

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
   V1_REFINE_ROOT_ONLY_READY,
   V1_REFINE_READY,
   V1_REFINE_NO_CHILD,
   V1_REFINE_AMBIGUOUS_FIRST,
   V1_REFINE_STOPPED_AMBIGUOUS,
   V1_REFINE_INVALIDATED
  };

enum V1RootReactionStatus
  {
   V1_ROOT_WATCH_WAITING_CONTACT=0,
   V1_ROOT_WATCH_DISCOVERING_CHILD,
   V1_ROOT_WATCH_READY,
   V1_ROOT_WATCH_AMBIGUOUS_FIRST,
   V1_ROOT_WATCH_STOPPED_AMBIGUOUS,
   V1_ROOT_WATCH_INVALIDATED,
   V1_ROOT_WATCH_INELIGIBLE_PRIOR_TOUCH,
   V1_ROOT_WATCH_ERROR
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
   V1_STRATEGY_WAITING_SWEEP,
   V1_STRATEGY_WAITING_TRIGGER, // active name shown as WAITING_CHOCH
   V1_STRATEGY_WAITING_FVG,
   V1_STRATEGY_WAITING_EXECUTION_GEOMETRY,
   V1_STRATEGY_PENDING,
   V1_STRATEGY_FILLED,
   V1_STRATEGY_MERGED_CONTRIBUTOR,
   V1_STRATEGY_CANCELED,
   V1_STRATEGY_NO_TRADE
  };

enum V1ExecutionStatus
  {
   V1_EXEC_NONE=0,
   V1_EXEC_STRATEGY_READY,
   V1_EXEC_PREFLIGHT_OK,
   V1_EXEC_PENDING_ACCEPTED,
   V1_EXEC_FILLED,
   V1_EXEC_EXECUTION_INFEASIBLE,
   V1_EXEC_REJECTED,
   V1_EXEC_CANCEL_REQUESTED,
   V1_EXEC_CANCELED,
   V1_EXEC_CANCEL_REJECTED,
   V1_EXEC_DIVERGENCE,
   V1_EXEC_CLOSED
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
   string            source_reason;
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
   bool              regime_research_rejected;

   string            containment_type;
   int               linked_event_type;
   datetime          linked_event_bar_open;

   int               strategy_state;
   datetime          invalidated_at;
   string            invalidation_reason;

   // D-122 audit: children must belong to a Root contact that occurred
   // before the child formed. Root objects keep these at zero until the
   // first causally observed runtime contact episode starts.
   datetime          root_contact_at;
   datetime          root_contact_bar_open;
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

struct V1RegimeResearchSnapshot
  {
   bool              valid;
   bool              parent_pass;
   bool              expansion_pass;
   bool              v1_pass;
   bool              selected_pass;
   int               wave_count;
   int               progression_success;
   int               progression_total;
   double            progression_ratio;
   int               protected_break_count;
   double            recent_leg_mean;
   double            prior_leg_mean;
   double            expansion_ratio;
   string            state_name;
   string            reason;
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
   string            source_reason;

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

   // Historical field retained only so the superseded Phase-4B code can
   // remain compile-compatible while disabled under D-122. It has no current
   // strategy authority.
   datetime          preplan_contact_at;

   // D-122 causal anchor. This is a physical Root-contact observation in
   // D122A; Phase 4B must separately qualify map/objective authority later.
   datetime          root_contact_at;
   datetime          root_contact_bar_open;
  };

struct V1ObjectiveCandidate
  {
   bool              valid;
   int               scenario_index; // D135 direct owner reference; historical ID remains audit authority
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

   // D-138 Regime Research V1 snapshot. Classification is frozen at the
   // baseline-equivalent PLAN moment and can never be recomputed for this plan.
   bool              regime_research_v1_evaluated;
   bool              regime_research_parent_pass;
   bool              regime_research_expansion_pass;
   bool              regime_research_v1_pass;
   int               regime_m30_wave_count;
   int               regime_progression_success;
   int               regime_progression_total;
   double            regime_progression_ratio;
   int               regime_protected_break_count;
   double            regime_recent_leg_mean;
   double            regime_prior_leg_mean;
   double            regime_leg_expansion_ratio;

   // Phase 4C source-contact / mature-sweep audit.
   datetime          source_contact_at;
   datetime          source_contact_bar_open;
   int               eligible_pool_count_at_contact;
   string            active_sweep_event_id;
   datetime          active_sweep_bar_open;
   datetime          active_sweep_at;
   double            active_sweep_extreme;
   int               authorized_sweep_count;

   // D-127 linear sequence state. No protected-reference snapshot is added
   // here: CHoCH authority comes directly from the independent M1 structure
   // detector after the scenario sweep stage has been satisfied.
   string            scenario_choch_event_id;
   datetime          scenario_choch_bar_open;
   datetime          scenario_choch_at;

   // D-128A causal FVG selection. Detector facts remain global; the
   // scenario freezes only the eligible same-direction Sweep->CHoCH set.
   int               eligible_fvg_count_at_choch;
   string            selected_fvg_id;
   int               selected_fvg_direction;
   datetime          selected_fvg_candle1_open;
   datetime          selected_fvg_candle2_open;
   datetime          selected_fvg_candle3_open;
   datetime          selected_fvg_available_at;
   double            selected_fvg_bottom;
   double            selected_fvg_top;
   double            selected_fvg_width;
   long              selected_fvg_width_ticks;
   datetime          fvg_frozen_at;
   datetime          no_trade_at;
   string            no_trade_reason;

   // D-128B deterministic execution geometry + frozen objective.
   bool              strategy_signal_valid;
   double            strategy_entry_price;
   double            raw_strategy_sl;
   double            normalized_sl;
   int               stop_loss_model;
   double            stop_loss_reference_price;
   double            stop_loss_reference_width;
   bool              stop_loss_merged_from_contributors;
   string            stop_loss_contributor_scenario_id;
   string            stop_loss_contributor_root_id;
   string            final_objective_id;
   int               final_objective_candidate_index; // D135 direct frozen-ledger reference
   string            final_objective_liquidity_id;
   double            final_objective_price;
   double            final_objective_planned_r;
   datetime          final_objective_selected_at;

   // D-129/D-130/D-131 execution and lifecycle ledger.
   // D-133 same-entry multi-Root contributor ledger.
   bool              execution_opportunity_merged;
   string            execution_master_scenario_id;
   string            execution_contributor_scenario_ids;
   string            execution_contributor_root_ids;
   int               execution_contributor_count;
   int               execution_status;
   string            terminal_reason;
   double            order_volume;
   datetime          pending_submitted_at;
   uint              request_id;
   ulong             broker_order_ticket;
   datetime          strategy_cancel_at;
   string            strategy_cancel_reason;
   bool              cancel_request_sent;
   datetime          fill_at;
   double            fill_price;
   ulong             broker_deal_ticket;
   ulong             broker_position_id;
   datetime          position_closed_at;
   double            exit_price;
   long              exit_reason;
   ulong             exit_deal_ticket;
   bool              execution_divergence;
   string            execution_divergence_reason;

   // Historical-bootstrap safety: if startup begins inside a frozen source,
   // contact authorization is disarmed until a closed M1 bar exits and a
   // later closed M1 bar re-enters the source.
   bool              startup_inside_source;
   bool              startup_exit_seen;

   datetime          canceled_at;
   string            cancel_reason;
  };

struct V1StrategyLiquidityConsumption
  {
   bool              valid;
   string            liquidity_id;
   datetime          consumed_at;
   int               consumption_type;
   string            reason;
  };

struct V1ScenarioEligiblePool
  {
   bool              valid;
   string            scenario_id;
   string            liquidity_id;
   int               family;
   ENUM_TIMEFRAMES   tf;
   int               side;
   double            bottom;
   double            top;
   datetime          available_at;
   bool              consumed;
   datetime          consumed_at;
   int               consumption_type;
   bool              authorized;
  };

struct V1GroupContactPool
  {
   bool              valid;
   string            scenario_id;
   string            liquidity_id;
   int               family;
   ENUM_TIMEFRAMES   tf;
   int               side;
   double            bottom;
   double            top;
   datetime          available_at;
   bool              consumed;
   datetime          consumed_at;
   int               consumption_type;
  };

// D-126 causal sweep-bar snapshot. Rebuilt for each M1 bar from state carried
// into that bar's close-timestamp group. It is not a Root-contact snapshot.
struct V1SweepBarSnapshotPool
  {
   bool              valid;
   string            scenario_id;
   string            liquidity_id;
   int               family;
   ENUM_TIMEFRAMES   tf;
   int               side;
   double            bottom;
   double            top;
   datetime          available_at;
   datetime          snapshot_bar_open;
  };
// D-126 retains every scenario-specific authorized sweep episode. No best
// pool/latest-sweep selection occurs before Phase 5A CHoCH linkage.
struct V1AuthorizedSweepEpisode
  {
   bool              valid;
   string            id;
   string            scenario_id;
   string            root_zone_id;
   int               direction;
   datetime          sweep_bar_open;
   datetime          available_at;
   int               pool_count;
   string            pool_ids;
  };

// D-127 detector-only M1 liquidity snapshot. It has no scenario/Root owner.
struct V1M1SweepDetectorPool
  {
   bool              valid;
   string            liquidity_id;
   int               family;
   ENUM_TIMEFRAMES   tf;
   int               side;
   double            bottom;
   double            top;
   datetime          available_at;
   datetime          snapshot_bar_open;
  };

struct V1M1SweepDetection
  {
   bool              valid;
   string            id;
   string            liquidity_id;
   int               family;
   ENUM_TIMEFRAMES   tf;
   int               side;
   double            bottom;
   double            top;
   datetime          pool_available_at;
   datetime          bar_open;
   datetime          available_at;
  };

struct V1M1ChochDetection
  {
   bool              valid;
   string            id;
   int               direction;
   string            broken_swing_id;
   double            broken_price;
   datetime          bar_open;
   datetime          available_at;
  };

// D-128A global M1 FVG detector fact. It knows nothing about Root/scenario.
struct V1M1FvgDetection
  {
   bool              valid;
   string            id;
   int               direction;
   datetime          candle1_open;
   datetime          candle2_open;
   datetime          candle3_open;
   datetime          available_at;
   double            bottom;
   double            top;
   double            width;
   long              width_ticks;
  };

struct V1ExecutionCandidate
  {
   bool              valid;
   int               scenario_index;
   string            scenario_id;
   int               direction;
   datetime          authorization_at;
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
   bool              strategy_consumed; // D135 O(1) M1-overlay membership on active pool
   datetime          consumed_at;
   int               consumption_type;
  };

struct V1RuntimeBarEvent
  {
   int       tf_index;
   MqlRates  bar;
   datetime  available_at;
  };

struct V1RootReactionTracker
  {
   bool              valid;
   string            id;
   string            root_zone_id;
   ENUM_TIMEFRAMES   root_tf;
   int               direction;
   int               status;

   datetime          watch_started_at;
   bool              bootstrap_root;
   bool              startup_inside_root;
   bool              startup_exit_seen;

   datetime          root_contact_at;
   datetime          root_contact_bar_open;

   string            current_parent_zone_id;
   string            final_child_id;
   string            path;
   int               child_count;
   datetime          lineage_updated_at;

   // Causal lower-TF structure snapshots are taken only when Root contact is
   // observed. Future lower-TF bars may emit optional child audit observations;
   // no child has strategy-source, entry, SL, TP, or cancellation authority.
   V1StructureState  m30_state;
   V1StructureState  m15_state;
   V1StructureState  m5_state;
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
V1RootReactionTracker g_root_reactions[];
string           g_optional_child_observation_ids[];
string           g_pending_refinement_root_ids[];
V1ObjectiveCandidate g_objective_candidates[];
V1ScenarioPlan   g_scenarios[];
// D-135 bounded runtime working sets. Historical ledgers above remain append-only
// for audit, but M1/tick hot paths iterate only currently actionable indices.
int              g_waiting_root_reaction_indices[];
int              g_ready_root_reaction_indices[];
int              g_waiting_sweep_scenario_indices[];
int              g_waiting_trigger_scenario_indices[];
int              g_waiting_execution_geometry_indices[];
int              g_active_execution_scenario_indices[];
long             g_root_reaction_state_version=0;
long             g_log_rows_since_flush=0;
long             g_log_rows_written=0;
long             g_log_rows_suppressed=0;
#define V1_CSV_FLUSH_BATCH 256
V1StrategyLiquidityConsumption g_strategy_liquidity_consumed[];
V1ScenarioEligiblePool g_scenario_eligible_pools[]; // superseded Phase-4C storage, runtime-dead
V1GroupContactPool g_group_contact_pools[];           // superseded Phase-4C storage, runtime-dead
V1SweepBarSnapshotPool g_sweep_bar_snapshot[];       // D-126 historical runtime-dead
V1AuthorizedSweepEpisode g_authorized_sweep_episodes[]; // D-126 historical runtime-dead
datetime          g_sweep_snapshot_bar_open=0;
V1M1SweepDetectorPool g_m1_sweep_detector_snapshot[];
V1M1SweepDetection g_m1_sweep_detections[];
V1M1ChochDetection g_m1_choch_detection;
V1M1FvgDetection g_m1_fvg_detections[];
V1ExecutionCandidate g_execution_candidates[];
datetime          g_m1_sweep_detector_bar_open=0;
V1MapControl      g_map;
string            g_scenario_layer_signature="";

// D-138 research-only rolling state. The baseline detector remains unchanged;
// this is a read-only attribution layer over already-confirmed M30 facts.
V1WaveRef         g_regime_m30_waves[];
datetime          g_regime_m30_protected_breaks[];
long              g_regime_plan_pass=0;
long              g_regime_plan_reject=0;

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
long             g_scenarios_no_objective=0;
long             g_objective_candidates_frozen=0;
long             g_source_contacts=0;
long             g_eligible_sweep_pools_frozen=0;
long             g_authorized_sweep_events=0;
long             g_authorized_sweep_pools=0;
long             g_strategy_m1_pool_consumptions=0;
long             g_structural_reaction_created=0;
long             g_root_watches_created=0;
long             g_root_watches_prior_touch_rejected=0;
long             g_root_contacts_observed=0;
long             g_root_contexts_ready=0;
long             g_post_contact_child_events=0;
long             g_optional_child_observations=0;
long             g_precontact_root_plans=0;
long             g_scenario_root_contacts=0;
long             g_root_contacts_without_preplan=0;
long             g_sweep_bar_snapshots=0;
long             g_sweep_snapshot_pools=0;
long             g_root_intersection_sweep_bars=0;
long             g_m1_sweep_detector_events=0;
long             g_scenario_sweep_accepts=0;
long             g_m1_choch_detector_events=0;
long             g_scenario_choch_accepts=0;
long             g_m1_fvg_detector_events=0;
long             g_m1_fvg_gap_rejections=0;
long             g_scenario_fvg_candidates=0;
long             g_scenario_fvg_preselection_retests=0;
long             g_scenario_fvg_selected=0;
long             g_scenario_no_causal_fvg=0;
long             g_scenario_ambiguous_fvg=0;
long             g_execution_geometry_ready=0;
long             g_no_r_eligible_objective=0;
long             g_simultaneous_authorization_ambiguous=0;
long             g_execution_opportunities_merged=0;
long             g_execution_contributors_merged=0;
long             g_exposure_blocked=0; // D134: opposite-direction exposure conflicts only
long             g_same_direction_addon_authorized=0;
long             g_opposite_direction_exposure_blocked=0;
long             g_execution_infeasible=0;
long             g_order_rejected=0;
long             g_orders_accepted=0;
long             g_positions_filled=0;
long             g_pending_cancellations=0;
long             g_cancel_rejected=0;
long             g_execution_divergences=0;
long             g_positions_closed=0;

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
      case V1_REFINE_ROOT_ONLY_READY:   return "ROOT_ONLY_READY";
      case V1_REFINE_READY:             return "READY";
      case V1_REFINE_NO_CHILD:          return "NO_CHILD";
      case V1_REFINE_AMBIGUOUS_FIRST:   return "AMBIGUOUS_FIRST";
      case V1_REFINE_STOPPED_AMBIGUOUS: return "STOPPED_AMBIGUOUS";
      case V1_REFINE_INVALIDATED:       return "INVALIDATED";
     }
   return "UNKNOWN";
  }

string RootReactionStatusName(const int status)
  {
   switch(status)
     {
      case V1_ROOT_WATCH_DISCOVERING_CHILD:       return "DISCOVERING_CHILD";
      case V1_ROOT_WATCH_READY:                   return "READY";
      case V1_ROOT_WATCH_AMBIGUOUS_FIRST:         return "AMBIGUOUS_FIRST";
      case V1_ROOT_WATCH_STOPPED_AMBIGUOUS:       return "STOPPED_AMBIGUOUS";
      case V1_ROOT_WATCH_INVALIDATED:             return "INVALIDATED";
      case V1_ROOT_WATCH_INELIGIBLE_PRIOR_TOUCH:  return "INELIGIBLE_PRIOR_TOUCH";
      case V1_ROOT_WATCH_ERROR:                   return "ERROR";
     }
   return "WAITING_CONTACT";
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
      case V1_STRATEGY_WAITING_SWEEP:   return "WAITING_SWEEP";
      case V1_STRATEGY_WAITING_TRIGGER: return "WAITING_CHOCH";
      case V1_STRATEGY_WAITING_FVG:     return "WAITING_FVG";
      case V1_STRATEGY_WAITING_EXECUTION_GEOMETRY: return "WAITING_EXECUTION_GEOMETRY";
      case V1_STRATEGY_PENDING:         return "PENDING";
      case V1_STRATEGY_FILLED:          return "FILLED";
      case V1_STRATEGY_MERGED_CONTRIBUTOR: return "MERGED_CONTRIBUTOR";
      case V1_STRATEGY_CANCELED:        return "CANCELED";
      case V1_STRATEGY_NO_TRADE:        return "NO_TRADE";
     }
   return "UNKNOWN";
  }
string StopLossModelName(const int model)
  {
   switch(model)
     {
      case V1_SL_FVG_DISTAL_20:     return "FVG_DISTAL_20";
      case V1_SL_SWEEP_EXTREME:     return "SWEEP_EXTREME";
      case V1_SL_ROOT_OB_DISTAL_20: return "ROOT_OB_DISTAL_20";
     }
   return "UNKNOWN";
  }

string ExecutionStatusName(const int status)
  {
   switch(status)
     {
      case V1_EXEC_STRATEGY_READY:       return "STRATEGY_READY";
      case V1_EXEC_PREFLIGHT_OK:         return "PREFLIGHT_OK";
      case V1_EXEC_PENDING_ACCEPTED:     return "PENDING_ACCEPTED";
      case V1_EXEC_FILLED:               return "FILLED";
      case V1_EXEC_EXECUTION_INFEASIBLE: return "EXECUTION_INFEASIBLE";
      case V1_EXEC_REJECTED:             return "REJECTED";
      case V1_EXEC_CANCEL_REQUESTED:     return "CANCEL_REQUESTED";
      case V1_EXEC_CANCELED:             return "CANCELED";
      case V1_EXEC_CANCEL_REJECTED:      return "CANCEL_REJECTED";
      case V1_EXEC_DIVERGENCE:           return "EXECUTION_DIVERGENCE";
      case V1_EXEC_CLOSED:               return "CLOSED";
     }
   return "NONE";
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



bool D135IndexListContains(const int &items[],const int value)
  {
   for(int i=0;i<ArraySize(items);i++)
      if(items[i]==value)
         return true;
   return false;
  }

void D135AddUniqueIndex(int &items[],const int value)
  {
   if(value<0 || D135IndexListContains(items,value))
      return;
   int n=ArraySize(items);
   if(ArrayResize(items,n+1,32)<0)
      return;
   items[n]=value;
  }

bool D135RemoveIndexValue(int &items[],const int value)
  {
   int n=ArraySize(items);
   for(int i=0;i<n;i++)
     {
      if(items[i]!=value)
         continue;
      for(int j=i+1;j<n;j++)
         items[j-1]=items[j];
      ArrayResize(items,n-1);
      return true;
     }
   return false;
  }

void D135UnregisterPreExecutionScenario(const int scenario_index)
  {
   D135RemoveIndexValue(g_waiting_sweep_scenario_indices,scenario_index);
   D135RemoveIndexValue(g_waiting_trigger_scenario_indices,scenario_index);
   D135RemoveIndexValue(g_waiting_execution_geometry_indices,scenario_index);
  }

string EventLogModeName(const V1EventLogMode mode)
  {
   if(mode==V1_LOG_FULL_AUDIT)
      return "FULL_AUDIT";
   return "RESEARCH_COMPACT";
  }

bool D135CriticalLogEvent(const string event_name)
  {
   return (event_name=="EA_START" ||
           event_name=="EA_STOP" ||
           event_name=="PENDING_ORDER_ACCEPTED" ||
           event_name=="PENDING_CANCEL_ACCEPTED" ||
           event_name=="PENDING_CANCEL_REJECTED" ||
           event_name=="POSITION_FILLED" ||
           event_name=="POSITION_CLOSED" ||
           event_name=="EXECUTION_DIVERGENCE" ||
           event_name=="ORDER_REJECTED");
  }

bool ResearchCompactLogEvent(const string event_name,const string tf)
  {
   // Regime Research V1 can be independently recomputed from these M30 facts.
   if(event_name=="WAVE_CONFIRMED")
      return (tf=="M30");
   if(event_name=="STRUCTURE_PROTECTED_BREAK")
      return (tf=="M30");

   // Research identity and PLAN-freeze classification.
   if(event_name=="EA_START" ||
      event_name=="EA_STOP" ||
      event_name=="INIT_STATE" ||
      event_name=="EXECUTION_EPOCH_START" ||
      event_name=="REGIME_RESEARCH_VARIANT_START" ||
      event_name=="REGIME_RESEARCH_PLAN_ACCEPTED" ||
      event_name=="REGIME_RESEARCH_PLAN_REJECTED" ||
      event_name=="REGIME_RESEARCH_STOP_SUMMARY" ||
      event_name=="D135_STOP_SUMMARY")
      return true;

   // Causal scenario path after a regime-accepted PLAN.
   if(event_name=="SCENARIO_PLANNED" ||
      event_name=="SCENARIO_ROOT_CONTACT_BOUND" ||
      event_name=="SCENARIO_SWEEP_ACCEPTED" ||
      event_name=="SCENARIO_CHOCH_ACCEPTED" ||
      event_name=="SCENARIO_FVG_SELECTED" ||
      event_name=="SCENARIO_FVG_NO_ENTRY" ||
      event_name=="SCENARIO_CANCELED" ||
      event_name=="SCENARIO_EXECUTION_NO_TRADE")
      return true;

   // Contributor merge, Entry/SL/TP and broker lifecycle.
   if(event_name=="EXECUTION_GEOMETRY_CANDIDATE_READY" ||
      event_name=="MERGED_STOP_SELECTED" ||
      event_name=="EXECUTION_CONTRIBUTOR_MERGED" ||
      event_name=="EXECUTION_CONTRIBUTOR_TERMINATED" ||
      event_name=="EXECUTION_OPPORTUNITY_MERGED" ||
      event_name=="EXECUTION_CONTRIBUTORS_EXHAUSTED" ||
      event_name=="FINAL_OBJECTIVE_SELECTED" ||
      event_name=="OBJECTIVE_ELIGIBILITY_EVALUATED" ||
      event_name=="EXECUTION_GEOMETRY_READY" ||
      event_name=="EXECUTION_PREFLIGHT_OK" ||
      event_name=="EXECUTION_AUTHORIZATION_BLOCKED" ||
      event_name=="SAME_DIRECTION_ADDON_AUTHORIZED" ||
      event_name=="PENDING_ORDER_ACCEPTED" ||
      event_name=="PENDING_CANCEL_ACCEPTED" ||
      event_name=="PENDING_CANCEL_REJECTED" ||
      event_name=="PARTIAL_FILL_RESIDUAL_CANCEL_ACCEPTED" ||
      event_name=="PARTIAL_FILL_RESIDUAL_CANCEL_REJECTED" ||
      event_name=="POSITION_FILLED" ||
      event_name=="POSITION_CLOSED")
      return true;

   // Failures that make a run unsuitable as profitability evidence.
   if(event_name=="INIT_EXECUTION_RECOVERY_REQUIRED" ||
      event_name=="LIQUIDITY_DETECTOR_ERROR" ||
      event_name=="SOURCE_DETECTOR_ERROR" ||
      event_name=="ROOT_REACTION_ERROR" ||
      event_name=="EXECUTION_PREFLIGHT_FAILED" ||
      event_name=="ORDER_REJECTED" ||
      event_name=="EXECUTION_DIVERGENCE")
      return true;

   return false;
  }

bool ShouldEmitLogEvent(const string event_name,const string tf)
  {
   if(D135CriticalLogEvent(event_name))
      return true;
   if(InpEventLogMode==V1_LOG_FULL_AUDIT)
      return true;
   return ResearchCompactLogEvent(event_name,tf);
  }

void LogLine(const string event_name,
             const string tf,
             const datetime available_at,
             const string object_id,
             const string detail)
  {
   if(!ShouldEmitLogEvent(event_name,tf))
     {
      g_log_rows_suppressed++;
      return;
     }

   // Preserve the historical FULL_AUDIT bootstrap-volume switch. Compact
   // mode deliberately keeps M30 wave/PB facts even during bootstrap so the
   // first PLAN snapshots remain independently reproducible.
   if(InpEventLogMode==V1_LOG_FULL_AUDIT &&
      g_in_bootstrap_replay &&
      !InpLogBootstrapEvents)
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
        {
         g_log_rows_suppressed++;
         return;
        }
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
   g_log_rows_written++;
   g_log_rows_since_flush++;
   if(g_log_rows_since_flush>=V1_CSV_FLUSH_BATCH || D135CriticalLogEvent(event_name))
     {
      FileFlush(g_log_handle);
      g_log_rows_since_flush=0;
     }
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
   ArrayResize(g_root_reactions,0);
   ArrayResize(g_optional_child_observation_ids,0);
   ArrayResize(g_pending_refinement_root_ids,0);
   ArrayResize(g_objective_candidates,0);
   ArrayResize(g_scenarios,0);
   ArrayResize(g_waiting_root_reaction_indices,0);
   ArrayResize(g_ready_root_reaction_indices,0);
   ArrayResize(g_waiting_sweep_scenario_indices,0);
   ArrayResize(g_waiting_trigger_scenario_indices,0);
   ArrayResize(g_waiting_execution_geometry_indices,0);
   ArrayResize(g_active_execution_scenario_indices,0);
   g_root_reaction_state_version=0;
   g_log_rows_since_flush=0;
   g_log_rows_written=0;
   g_log_rows_suppressed=0;
   ArrayResize(g_m1_sweep_detector_snapshot,0);
   ArrayResize(g_m1_sweep_detections,0);
   ArrayResize(g_m1_fvg_detections,0);
   ArrayResize(g_regime_m30_waves,0);
   ArrayResize(g_regime_m30_protected_breaks,0);
   g_regime_plan_pass=0;
   g_regime_plan_reject=0;
   g_m1_sweep_detector_bar_open=0;
   g_m1_choch_detection.valid=false;
   g_m1_choch_detection.id="";
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
   g_scenarios_no_objective=0;
   g_objective_candidates_frozen=0;
   g_root_watches_created=0;
   g_root_watches_prior_touch_rejected=0;
   g_root_contacts_observed=0;
   g_root_contexts_ready=0;
   g_post_contact_child_events=0;
   g_optional_child_observations=0;
   g_precontact_root_plans=0;
   g_scenario_root_contacts=0;
   g_root_contacts_without_preplan=0;
   g_m1_sweep_detector_events=0;
   g_scenario_sweep_accepts=0;
   g_m1_choch_detector_events=0;
   g_scenario_choch_accepts=0;
   g_m1_fvg_detector_events=0;
   g_m1_fvg_gap_rejections=0;
   g_scenario_fvg_candidates=0;
   g_scenario_fvg_preselection_retests=0;
   g_scenario_fvg_selected=0;
   g_scenario_no_causal_fvg=0;
   g_scenario_ambiguous_fvg=0;
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
//| D-138 frozen Regime Research V1 attribution                      |
//+------------------------------------------------------------------+
string RegimeResearchModeName(const V1RegimeResearchMode mode)
  {
   if(mode==V1_REGIME_BASELINE_NO_GATE)
      return "BASELINE_NO_REGIME_GATE";
   if(mode==V1_REGIME_PARENT_CLEAN_PERSISTENT)
      return "M30_CLEAN_PERSISTENT";
   return "M30_CLEAN_PERSISTENT_EXPANDING";
  }

void ClearRegimeResearchSnapshot(V1RegimeResearchSnapshot &snapshot)
  {
   snapshot.valid=false;
   snapshot.parent_pass=false;
   snapshot.expansion_pass=false;
   snapshot.v1_pass=false;
   snapshot.selected_pass=false;
   snapshot.wave_count=0;
   snapshot.progression_success=0;
   snapshot.progression_total=0;
   snapshot.progression_ratio=0.0;
   snapshot.protected_break_count=0;
   snapshot.recent_leg_mean=0.0;
   snapshot.prior_leg_mean=0.0;
   snapshot.expansion_ratio=0.0;
   snapshot.state_name="UNKNOWN";
   snapshot.reason="UNINITIALIZED";
  }

void PruneRegimeM30ProtectedBreaks()
  {
   if(ArraySize(g_regime_m30_waves)<V1_REGIME_WAVE_COUNT)
      return;

   datetime oldest=g_regime_m30_waves[0].available_at;
   int write=0;
   int n=ArraySize(g_regime_m30_protected_breaks);
   for(int i=0;i<n;i++)
     {
      if(g_regime_m30_protected_breaks[i]<oldest)
         continue;
      if(write!=i)
         g_regime_m30_protected_breaks[write]=g_regime_m30_protected_breaks[i];
      write++;
     }
   ArrayResize(g_regime_m30_protected_breaks,write);
  }

void PushRegimeM30Wave(const V1WaveRef &wave)
  {
   if(!wave.valid || !wave.is_wave)
      return;

   int n=ArraySize(g_regime_m30_waves);
   if(n<V1_REGIME_WAVE_COUNT)
     {
      if(ArrayResize(g_regime_m30_waves,n+1,V1_REGIME_WAVE_COUNT)<0)
         return;
      g_regime_m30_waves[n]=wave;
     }
   else
     {
      for(int i=1;i<V1_REGIME_WAVE_COUNT;i++)
         g_regime_m30_waves[i-1]=g_regime_m30_waves[i];
      g_regime_m30_waves[V1_REGIME_WAVE_COUNT-1]=wave;
     }

   PruneRegimeM30ProtectedBreaks();
  }

void RecordRegimeM30ProtectedBreak(const datetime available_at)
  {
   if(available_at<=0)
      return;
   int n=ArraySize(g_regime_m30_protected_breaks);
   if(ArrayResize(g_regime_m30_protected_breaks,n+1,16)<0)
      return;
   g_regime_m30_protected_breaks[n]=available_at;
   PruneRegimeM30ProtectedBreaks();
  }

bool EvaluateRegimeResearchSnapshot(const V1ScenarioDraft &draft,
                                    const datetime frozen_at,
                                    V1RegimeResearchSnapshot &snapshot)
  {
   ClearRegimeResearchSnapshot(snapshot);

   // Baseline control lives in this same executable for causal A/B/C tests.
   // It must not use regime state as a scenario authorization gate.
   // The research rolling buffers may still be maintained for diagnostics,
   // but no scope/progression/PB/expansion condition can reject a PLAN here.
   if(InpRegimeResearchMode==V1_REGIME_BASELINE_NO_GATE)
     {
      snapshot.valid=false;
      snapshot.selected_pass=true;
      snapshot.state_name="BASELINE_NO_REGIME_GATE";
      snapshot.reason="BASELINE_NO_REGIME_GATE";
      return true;
     }

   if(draft.scope!=V1_SCOPE_EXTERNAL_CONTINUATION)
     {
      snapshot.reason="SCOPE_NOT_EXTERNAL_CONTINUATION";
      return false;
     }

   int n=ArraySize(g_regime_m30_waves);
   snapshot.wave_count=n;
   if(n<V1_REGIME_WAVE_COUNT)
     {
      snapshot.reason="INSUFFICIENT_M30_WAVES";
      return false;
     }

   V1WaveRef waves[V1_REGIME_WAVE_COUNT];
   for(int i=0;i<V1_REGIME_WAVE_COUNT;i++)
     {
      if(!g_regime_m30_waves[i].valid ||
         !g_regime_m30_waves[i].is_wave ||
         g_regime_m30_waves[i].available_at>frozen_at)
        {
         snapshot.reason="M30_WAVE_NOT_CAUSALLY_AVAILABLE_AT_PLAN";
         return false;
        }
      waves[i]=g_regime_m30_waves[i];
     }

   bool have_high=false;
   bool have_low=false;
   double last_high=0.0;
   double last_low=0.0;
   int success=0;
   int total=0;

   for(int i=0;i<V1_REGIME_WAVE_COUNT;i++)
     {
      if(waves[i].side==V1_SIDE_HIGH)
        {
         if(have_high)
           {
            total++;
            if((draft.direction>0 && waves[i].price>last_high) ||
               (draft.direction<0 && waves[i].price<last_high))
               success++;
           }
         last_high=waves[i].price;
         have_high=true;
        }
      else if(waves[i].side==V1_SIDE_LOW)
        {
         if(have_low)
           {
            total++;
            if((draft.direction>0 && waves[i].price>last_low) ||
               (draft.direction<0 && waves[i].price<last_low))
               success++;
           }
         last_low=waves[i].price;
         have_low=true;
        }
     }

   snapshot.progression_success=success;
   snapshot.progression_total=total;
   if(total<=0)
     {
      snapshot.reason="NO_SAME_SIDE_M30_COMPARISONS";
      return false;
     }
   snapshot.progression_ratio=(double)success/(double)total;

   datetime span_start=waves[0].available_at;
   int pb_count=0;
   for(int i=0;i<ArraySize(g_regime_m30_protected_breaks);i++)
      if(g_regime_m30_protected_breaks[i]>=span_start &&
         g_regime_m30_protected_breaks[i]<=frozen_at)
         pb_count++;
   snapshot.protected_break_count=pb_count;

   bool progression_pass=
      (success*V1_REGIME_PROGRESSION_DEN >=
       total*V1_REGIME_PROGRESSION_NUM);
   bool stability_pass=(pb_count<=V1_REGIME_MAX_PROTECTED_BREAKS);
   snapshot.parent_pass=(progression_pass && stability_pass);

   double recent_sum=0.0;
   double prior_sum=0.0;
   int recent_start=V1_REGIME_WAVE_COUNT-V1_REGIME_LEG_GROUP;
   int prior_start=recent_start-V1_REGIME_LEG_GROUP;

   for(int i=recent_start;i<V1_REGIME_WAVE_COUNT;i++)
      recent_sum+=MathAbs(waves[i].price-waves[i-1].price);
   for(int i=prior_start;i<recent_start;i++)
      prior_sum+=MathAbs(waves[i].price-waves[i-1].price);

   snapshot.recent_leg_mean=recent_sum/(double)V1_REGIME_LEG_GROUP;
   snapshot.prior_leg_mean=prior_sum/(double)V1_REGIME_LEG_GROUP;
   if(snapshot.prior_leg_mean>0.0)
      snapshot.expansion_ratio=
         snapshot.recent_leg_mean/snapshot.prior_leg_mean;

   snapshot.expansion_pass=
      (snapshot.prior_leg_mean>0.0 &&
       snapshot.expansion_ratio>V1_REGIME_EXPANSION_THRESHOLD);
   snapshot.v1_pass=(snapshot.parent_pass && snapshot.expansion_pass);
   snapshot.selected_pass=
      (InpRegimeResearchMode==V1_REGIME_PARENT_CLEAN_PERSISTENT ?
       snapshot.parent_pass : snapshot.v1_pass);
   snapshot.valid=true;

   if(!progression_pass)
      snapshot.reason="PROGRESSION_BELOW_TWO_THIRDS";
   else if(!stability_pass)
      snapshot.reason="PROTECTED_BREAK_CHURN_GT_ONE";
   else if(InpRegimeResearchMode==V1_REGIME_V1_CLEAN_PERSISTENT_EXPANDING &&
           snapshot.prior_leg_mean<=0.0)
      snapshot.reason="INVALID_PRIOR_LEG_MEAN";
   else if(InpRegimeResearchMode==V1_REGIME_V1_CLEAN_PERSISTENT_EXPANDING &&
           !snapshot.expansion_pass)
      snapshot.reason="RECENT_M30_LEGS_NOT_EXPANDING";
   else
      snapshot.reason="PASS";

   if(snapshot.selected_pass)
      snapshot.state_name=RegimeResearchModeName(InpRegimeResearchMode);
   else
      snapshot.state_name="UNKNOWN";

   return snapshot.selected_pass;
  }

void LogRegimeResearchSnapshot(const string event_name,
                               const V1ScenarioDraft &draft,
                               const datetime frozen_at,
                               const V1RegimeResearchSnapshot &snapshot)
  {
   LogLine(event_name,
           "M30",
           frozen_at,
           draft.root_zone_id,
           StringFormat("mode=%s scope=%s direction=%s state=%s selected_pass=%s reason=%s wave_count=%d progression_success=%d progression_total=%d progression=%.8f progression_required=2/3 protected_break_count=%d protected_break_max=1 parent_pass=%s recent4_leg_mean=%.10f prior4_leg_mean=%.10f leg_expansion_ratio=%.8f expansion_required_gt=1.0 expansion_pass=%s v1_pass=%s snapshot=SCENARIO_PLAN_FREEZE complement_label=UNKNOWN threshold_inputs=false",
                        RegimeResearchModeName(InpRegimeResearchMode),
                        ScenarioScopeName(draft.scope),
                        DirectionName(draft.direction),
                        snapshot.state_name,
                        snapshot.selected_pass ? "true" : "false",
                        snapshot.reason,
                        snapshot.wave_count,
                        snapshot.progression_success,
                        snapshot.progression_total,
                        snapshot.progression_ratio,
                        snapshot.protected_break_count,
                        snapshot.parent_pass ? "true" : "false",
                        snapshot.recent_leg_mean,
                        snapshot.prior_leg_mean,
                        snapshot.expansion_ratio,
                        snapshot.expansion_pass ? "true" : "false",
                        snapshot.v1_pass ? "true" : "false"));
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
   g_liquidity[n].strategy_consumed=false;
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

// Phase 4C forward declarations used by the existing global detector
// and Phase 4B objective-family builder.
bool IsStrategyLiquidityConsumed(const string liquidity_id);
void PruneStrategyLiquidityConsumption(const string liquidity_id);
void MarkStrategyLiquidityConsumed(const string liquidity_id,
                                   const datetime consumed_at,
                                   const int consumption_type,
                                   const string reason);
void MarkScenarioPoolConsumed(const string liquidity_id,
                              const datetime consumed_at,
                              const int consumption_type);
int PhysicalConsumptionForBar(const int side,
                              const double bottom,
                              const double top,
                              const MqlRates &bar);
bool BarIntersectsSource(const MqlRates &bar,const V1ScenarioPlan &plan);
void PrepareD127M1SweepDetectorSnapshot(const datetime bar_open);
void EvaluateD127M1SweepDetector(const MqlRates &bar,const datetime available_at);
void ProcessD127ScenarioSweepStage(const MqlRates &bar,const datetime available_at);
void ProcessD127ScenarioChochStage(const MqlRates &bar,const datetime available_at);
void EvaluateD128AM1FvgDetector(const V1StructureState &state,const MqlRates &bar,const datetime available_at);
void ProcessD128AScenarioFvgFreeze(const int scenario_index,const MqlRates &choch_bar,const datetime available_at);
void PruneD128AM1FvgDetections();
void ProcessIntegratedExecutionAuthorizationEpoch(const datetime available_at);
void ManageIntegratedExecution(const MqlTick &tick);
bool HasManagedAccountExposure();

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

      // Phase 4C strategy overlay learns about every own-TF global
      // consumption before the compact pool object leaves RAM.
      MarkStrategyLiquidityConsumed(g_liquidity[i].id,
                                    available_at,
                                    consumption,
                                    "GLOBAL_OWN_TF");
      MarkScenarioPoolConsumed(g_liquidity[i].id,
                               available_at,
                               consumption);

      LogLiquidityConsumption(g_liquidity[i],bar,available_at,consumption);

      if(consumption==V1_LIQ_CONSUME_SWEEP)
         g_liquidity_sweeps++;
      else
         g_liquidity_body_deliveries++;

      // Active-memory compression: consumed liquidity leaves the working set.
      // Scenario contact snapshots already carry their own immutable copy, so
      // the cross-TF strategy-consumption overlay can also release this ID.
      string consumed_id=g_liquidity[i].id;
      RemoveLiquidityAt(i);
      PruneStrategyLiquidityConsumption(consumed_id);
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
      "STRUCTURAL_REACTION_AUTHORIZATION_DISABLED_D127_LINEAR_BASELINE");

   LogLine("LIQUIDITY_STATE",
           TfName(tf),
           available_at,
           "",
           detail);
  }

void EnsurePostContactRootWatches(const datetime snapshot_at,const bool bootstrap_scan);
void BindPreplannedScenarioToRootContact(const V1SourceZone &root,
                                             const MqlRates &bar,
                                             const datetime available_at);
void ProcessPostContactRootContacts(const MqlRates &bar,const datetime available_at);
void ProcessPostContactChildBar(const int tf_index,const MqlRates &bar,const datetime available_at);
void InvalidatePostContactRootTracker(const string root_id,const datetime available_at,const string reason);
void RollbackPostContactRefinementAfterChildInvalidation(const string root_id,const string child_id,const string parent_zone_id,const datetime available_at,const string reason);
void StoreRefinementLineage(const V1RefinementLineage &lineage);

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

int FindSourceIndexById(const string id)
  {
   for(int i=0;i<ArraySize(g_sources);i++)
     {
      if(g_sources[i].valid &&
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

string MergeObSourceReason(const string current_reason,
                           const string new_reason)
  {
   if(current_reason=="")
      return new_reason;
   if(new_reason=="" || current_reason==new_reason)
      return current_reason;
   if(StringFind(current_reason,new_reason)>=0)
      return current_reason;
   return current_reason+"|"+new_reason;
  }

int CollectFvgOriginObBars(const ENUM_TIMEFRAMES tf,
                           const int direction,
                           const V1WaveRef &meaningful_wave,
                           const MqlRates &break_bar,
                           MqlRates &origins[])
  {
   ArrayResize(origins,0);

   if(!meaningful_wave.valid ||
      !meaningful_wave.is_wave ||
      direction==0)
      return 0;

   // Baseline second OB recognizer. LAST_OPPOSITE_OB and FVG_ORIGIN_OB
   // are both active independently. Here Candle1 of every
   // direction-compatible three-candle FVG in the causal directional leg is
   // admitted as an additional OB candidate.
   datetime start_time=meaningful_wave.occurred_at;
   if(start_time<=0)
      start_time=meaningful_wave.origin_window_end;

   datetime end_time=break_bar.time;
   if(start_time<=0 || end_time<start_time)
      return 0;

   MqlRates bars[];
   ArraySetAsSeries(bars,false);

   ResetLastError();
   int copied=CopyRates(_Symbol,tf,start_time,end_time,bars);
   if(copied<3)
      return 0;

   int seconds=PeriodSeconds(tf);
   if(seconds<=0)
      return 0;

   for(int i=0;i<=copied-3;i++)
     {
      // Do not let a session/data gap fabricate a three-candle FVG.
      if((bars[i+1].time-bars[i].time)!=seconds ||
         (bars[i+2].time-bars[i+1].time)!=seconds)
         continue;

      bool directional_fvg=false;
      if(direction>0)
         directional_fvg=(bars[i+2].low>bars[i].high);
      else
         directional_fvg=(bars[i+2].high<bars[i].low);

      if(!directional_fvg)
         continue;

      int n=ArraySize(origins);
      if(ArrayResize(origins,n+1,16)<0)
         break;
      origins[n]=bars[i];
     }

   return ArraySize(origins);
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
      "kind=ROOT state=ACTIVE direction=%s source_reason=%s bottom=%.10f top=%.10f origin_open=%.10f origin_close=%.10f origin_index=%d origin_time=%s origin_window_start=%s origin_window_end=%s origin_wave_id=%s linked_event_type=%s linked_structure_event_id=%s break_bar_open=%s break_close=%.10f root_zone_id=%s scenario_owner_id=%s scenario_authority=false same_session_causal_path=true",
      DirectionName(root.direction),
      root.source_reason,
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

bool AddRootCandidateFromOrigin(const int tf_index,
                                const int event_type,
                                const int direction,
                                const V1WaveRef &meaningful_wave,
                                const MqlRates &break_bar,
                                const datetime available_at,
                                const MqlRates &origin_bar,
                                const string source_reason)
  {
   // Every recognizer feeds the same causal/session/strategy lifecycle. The
   // second recognizer broadens baseline recognition only; it does not bypass existing Root
   // validity rules.
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

   int existing=FindActiveSourceById(root_id);
   if(existing>=0)
     {
      string merged=MergeObSourceReason(g_sources[existing].source_reason,
                                        source_reason);
      if(merged!=g_sources[existing].source_reason)
        {
         string prior=g_sources[existing].source_reason;
         g_sources[existing].source_reason=merged;
         LogLine("OB_RECOGNITION_MERGED",
                 TfName(g_timeframes[tf_index]),
                 available_at,
                 root_id,
                 StringFormat("kind=ROOT direction=%s origin_time=%s previous_reason=%s added_reason=%s merged_reason=%s",
                              DirectionName(direction),
                              TimeToString(origin_bar.time,TIME_DATE|TIME_SECONDS),
                              prior,
                              source_reason,
                              merged));
         return true;
        }

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
   g_sources[n].source_reason=source_reason;
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

   // LAST_OPPOSITE_OB preserves the frozen swing-origin window. An
   // FVG-origin Root owns its Candle1 interval as the parent
   // refinement window so lower-TF refinement is projected into that OB.
   if(source_reason=="FVG_ORIGIN_OB")
     {
      g_sources[n].origin_window_start=origin_bar.time;
      g_sources[n].origin_window_end=
         origin_bar.time+PeriodSeconds(g_timeframes[tf_index])-1;
     }
   else
     {
      g_sources[n].origin_window_start=meaningful_wave.origin_window_start;
      g_sources[n].origin_window_end=meaningful_wave.origin_window_end;
     }

   g_sources[n].origin_wave_id=meaningful_wave.id;
   g_sources[n].meaningful_swing_id=meaningful_wave.id;
   g_sources[n].linked_structure_event_id=event_id;
   g_sources[n].parent_zone_id="";
   g_sources[n].root_zone_id=root_id;
   g_sources[n].scenario_owner_id="";
   g_sources[n].regime_research_rejected=false;
   g_sources[n].containment_type="ROOT";
   g_sources[n].linked_event_type=event_type;
   g_sources[n].linked_event_bar_open=break_bar.time;
   g_sources[n].strategy_state=V1_SOURCE_ACTIVE;
   g_sources[n].invalidated_at=0;
   g_sources[n].invalidation_reason="";
   g_sources[n].root_contact_at=0;
   g_sources[n].root_contact_bar_open=0;

   g_roots_created++;
   LogRootCreated(g_sources[n],event_type,break_bar);

   // D-122: Root creation never authorizes historical child refinement.
   // Runtime Root watches are registered only after the full same-timestamp
   // MTF group has completed, so a Root cannot self-contact on its creation bar.

   return true;
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

   bool recognized=false;
   bool found_any_recognizer=false;

   // Recognizer A: frozen baseline LAST_OPPOSITE_OB.
   MqlRates opposite_origin;
   ZeroMemory(opposite_origin);
   if(FindLastOppositeCandleInSwingOrigin(g_timeframes[tf_index],
                                          direction,
                                          meaningful_wave,
                                          opposite_origin))
     {
      found_any_recognizer=true;
      if(AddRootCandidateFromOrigin(tf_index,
                                    event_type,
                                    direction,
                                    meaningful_wave,
                                    break_bar,
                                    available_at,
                                    opposite_origin,
                                    "LAST_OPPOSITE_OB"))
         recognized=true;
     }

   // Recognizer B: Candle1-of-FVG OB is now baseline authority. Every
   // distinct physical Candle1 remains an independent Root contributor. It
   // never replaces or suppresses LAST_OPPOSITE_OB; same physical candles
   // are deduplicated by Root ID and recognition reasons are merged.
   MqlRates fvg_origins[];
   int fvg_count=CollectFvgOriginObBars(g_timeframes[tf_index],
                                        direction,
                                        meaningful_wave,
                                        break_bar,
                                        fvg_origins);
   if(fvg_count>0)
      found_any_recognizer=true;

   for(int i=0;i<fvg_count;i++)
     {
      if(AddRootCandidateFromOrigin(tf_index,
                                    event_type,
                                    direction,
                                    meaningful_wave,
                                    break_bar,
                                    available_at,
                                    fvg_origins[i],
                                    "FVG_ORIGIN_OB"))
         recognized=true;
     }

   if(!found_any_recognizer)
     {
      LogRootRejected(tf_index,
                      available_at,
                      event_type,
                      direction,
                      "NO_ELIGIBLE_OB_RECOGNIZER_MATCH",
                      meaningful_wave.id);
     }

   return recognized;
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
   InvalidatePostContactRootTracker(root_id,available_at,reason);

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

         // Descendant removal alone does not invalidate the Root reaction.
         // The owning caller decides whether this is a Root invalidation or
         // a child-only rollback under D-028 / D-122.
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
         string parent_zone_id=g_sources[i].parent_zone_id;

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

         RollbackPostContactRefinementAfterChildInvalidation(root_id,
                                                              child_id,
                                                              parent_zone_id,
                                                              available_at,
                                                              "PRICE_INVALIDATED");
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

void ClearD127M1ChochDetection()
  {
   g_m1_choch_detection.valid=false;
   g_m1_choch_detection.id="";
   g_m1_choch_detection.direction=0;
   g_m1_choch_detection.broken_swing_id="";
   g_m1_choch_detection.broken_price=0.0;
   g_m1_choch_detection.bar_open=0;
   g_m1_choch_detection.available_at=0;
  }

void RecordD127M1ChochDetection(const V1StructureState &s,
                                const int direction,
                                const V1WaveRef &broken,
                                const MqlRates &bar,
                                const datetime available_at)
  {
   if(s.tf!=PERIOD_M1 || !broken.valid)
      return;

   g_m1_choch_detection.valid=true;
   g_m1_choch_detection.id=BuildStructureEventId(s,V1_EVENT_PROTECTED_BREAK,bar);
   g_m1_choch_detection.direction=direction;
   g_m1_choch_detection.broken_swing_id=broken.id;
   g_m1_choch_detection.broken_price=broken.price;
   g_m1_choch_detection.bar_open=bar.time;
   g_m1_choch_detection.available_at=available_at;
   g_m1_choch_detector_events++;

   LogLine("M1_CHOCH_DETECTED",
           "M1",
           available_at,
           g_m1_choch_detection.id,
           StringFormat("direction=%s bar_open=%s close=%.10f broken_swing_id=%s broken_price=%.10f detector_source=STRUCTURE_PROTECTED_BREAK strategy_authority=false scenario_filter=false sweep_filter=false root_filter=false child_filter=false",
                        DirectionName(direction),
                        TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                        bar.close,
                        broken.id,
                        broken.price));
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
         if(tf_index==2)
            RecordRegimeM30ProtectedBreak(available_at);
         if(tf_index==5)
            RecordD127M1ChochDetection(s,-1,broken,bar,available_at);
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
         if(tf_index==2)
            RecordRegimeM30ProtectedBreak(available_at);
         if(tf_index==5)
            RecordD127M1ChochDetection(s,1,broken,bar,available_at);
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
   return (status==V1_REFINE_ROOT_ONLY_READY ||
           status==V1_REFINE_READY ||
           status==V1_REFINE_STOPPED_AMBIGUOUS);
  }

int FindScenarioById(const string scenario_id)
  {
   for(int i=0;i<ArraySize(g_scenarios);i++)
      if(g_scenarios[i].valid && g_scenarios[i].id==scenario_id)
         return i;
   return -1;
  }

int FindActiveScenarioForRoot(const string root_id)
  {
   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(!g_scenarios[i].valid ||
         g_scenarios[i].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[i].strategy_state==V1_STRATEGY_NO_TRADE)
         continue;
      if(g_scenarios[i].root_zone_id==root_id)
         return i;
     }
   return -1;
  }

bool HasActiveScenarioForRoot(const string root_id)
  {
   return (FindActiveScenarioForRoot(root_id)>=0);
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

bool RootWatchEligibleForPreContactPlan(const string root_id)
  {
   int tracker_index=FindRootReactionTrackerByRootId(root_id);
   if(tracker_index<0 ||
      !g_root_reactions[tracker_index].valid)
      return false;

   return (g_root_reactions[tracker_index].status==
              V1_ROOT_WATCH_WAITING_CONTACT &&
           g_root_reactions[tracker_index].root_contact_at==0);
  }

bool BuildRootScenarioDraft(const int root_index,
                            V1ScenarioDraft &draft,
                            string &reject_reason)
  {
   draft.valid=false;
   reject_reason="";

   if(root_index<0 ||
      root_index>=ArraySize(g_sources) ||
      !g_sources[root_index].valid ||
      g_sources[root_index].kind!=V1_SOURCE_ROOT ||
      g_sources[root_index].strategy_state!=V1_SOURCE_ACTIVE)
     {
      reject_reason="ROOT_NOT_ACTIVE";
      return false;
     }

   const string root_id=g_sources[root_index].id;

   if(HasActiveScenarioForRoot(root_id))
     {
      reject_reason="ACTIVE_SCENARIO_ALREADY_EXISTS_FOR_ROOT";
      return false;
     }

   if(!RootWatchEligibleForPreContactPlan(root_id))
     {
      reject_reason="ROOT_NOT_WAITING_PRECONTACT";
      return false;
     }

   int direction=g_sources[root_index].direction;
   if(direction==0)
     {
      reject_reason="ROOT_DIRECTION_NONE";
      return false;
     }

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
           {
            reject_reason="ROOT_DIRECTION_INCOMPATIBLE_WITH_H1_CONTINUATION";
            return false;
           }

         scope=V1_SCOPE_EXTERNAL_CONTINUATION;
         active_map_tf=PERIOD_H1;
         owner_id=g_structure[1].owner_id;
         parent_context_id=g_structure[1].owner_id;
        }
      else
        {
         int permission_direction=
            (g_map.reversal_permission==V1_REVERSAL_OPEN_FOR_LONG ? 1 : -1);

         if(direction!=permission_direction)
           {
            reject_reason="ROOT_DIRECTION_INCOMPATIBLE_WITH_REVERSAL_PERMISSION";
            return false;
           }

         if(!m30_mature ||
            TrendDirection(g_structure[2].trend)!=direction ||
            direction==h1_direction)
           {
            reject_reason="OPPOSITE_M30_REVERSAL_MAP_NOT_MATURE";
            return false;
           }

         scope=V1_SCOPE_EXTERNAL_REVERSAL;
         active_map_tf=PERIOD_M30;
         owner_id=g_structure[2].owner_id;
         parent_context_id=g_structure[1].owner_id;
         permission_reference_id=g_map.permission_reference_id;
         permission_opened_at=g_map.reversal_permission_opened_at;

         if(permission_reference_id=="" || permission_opened_at<=0)
           {
            reject_reason="REVERSAL_PERMISSION_IDENTITY_MISSING";
            return false;
           }
        }
     }
   else
     {
      if(!m30_mature ||
         direction!=TrendDirection(g_structure[2].trend))
        {
         reject_reason="M30_PRIMARY_MAP_NOT_COMPATIBLE";
         return false;
        }

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
     {
      reject_reason="ACTIVE_MAP_RANGE_UNAVAILABLE";
      return false;
     }

   // Current V1 requires the Root to belong to the active map context.
   // Premium/discount itself remains audit-only and is never a veto.
   if(g_sources[root_index].bottom<range_low ||
      g_sources[root_index].top>range_high)
     {
      reject_reason="ROOT_OUTSIDE_ACTIVE_MAP_RANGE";
      return false;
     }

   double eq=(range_low+range_high)*0.5;

   draft.valid=true;
   draft.refinement_index=-1;
   draft.scope=scope;
   draft.direction=direction;
   draft.active_map_tf=active_map_tf;
   draft.owner_id=owner_id;
   draft.parent_context_id=parent_context_id;
   draft.permission_reference_id=permission_reference_id;
   draft.permission_opened_at=permission_opened_at;
   draft.root_zone_id=root_id;
   // D-124/D-125: compatibility field only. Strategy source is always Root.
   draft.final_source_id=root_id;
   draft.range_low=range_low;
   draft.range_high=range_high;
   draft.eq=eq;

   // D-125: each physical Root is an independent scenario candidate.
   // Do not collapse multiple Roots sharing the same map context into an
   // shared-context ambiguity veto.
   draft.context_key=StringFormat("%s|%s|%s|%s|%s|ROOT=%s",
                                  ScenarioScopeName(scope),
                                  DirectionName(direction),
                                  TfName(active_map_tf),
                                  owner_id,
                                  parent_context_id,
                                  root_id);
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
   candidates[n].scenario_index=-1;
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
         g_liquidity[i].available_at>frozen_at ||
         g_liquidity[i].strategy_consumed)
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
            g_liquidity[i].available_at>frozen_at ||
            g_liquidity[i].strategy_consumed)
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

void BindRootScenarioOwner(const string root_id,
                           const string scenario_id)
  {
   int root_index=FindActiveSourceById(root_id);
   if(root_index<0 ||
      g_sources[root_index].kind!=V1_SOURCE_ROOT)
      return;

   if(g_sources[root_index].scenario_owner_id=="")
      g_sources[root_index].scenario_owner_id=scenario_id;
  }

void ReleaseRootScenarioOwner(const string root_id,
                              const string scenario_id)
  {
   int root_index=FindSourceIndexById(root_id);
   if(root_index<0 ||
      g_sources[root_index].kind!=V1_SOURCE_ROOT)
      return;

   if(g_sources[root_index].scenario_owner_id==scenario_id)
      g_sources[root_index].scenario_owner_id="";
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
   // D-135: consumption is propagated at the exact liquidity-consumption event
   // in MarkStrategyLiquidityConsumed(). Historical candidate polling here was
   // O(objectives * scenarios) and caused superlinear long-run tester cost.
  }

void CancelInvalidScenarioPlans(const datetime available_at)
  {
   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(!g_scenarios[i].valid ||
         g_scenarios[i].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[i].strategy_state==V1_STRATEGY_NO_TRADE ||
         g_scenarios[i].strategy_state==V1_STRATEGY_FILLED ||
         g_scenarios[i].strategy_state==V1_STRATEGY_MERGED_CONTRIBUTOR)
         continue;

      if(g_scenarios[i].strategy_state==V1_STRATEGY_PENDING &&
         g_scenarios[i].execution_contributor_count>1)
         continue;

      string reason="";

      int root_index=FindActiveSourceById(g_scenarios[i].root_zone_id);

      if(root_index<0 ||
         g_sources[root_index].kind!=V1_SOURCE_ROOT)
         reason="ROOT_INVALIDATED";
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
      D135UnregisterPreExecutionScenario(i);
      ReleaseRootScenarioOwner(g_scenarios[i].root_zone_id,
                                  g_scenarios[i].id);
      LogScenarioCanceled(g_scenarios[i],available_at,reason);
      g_scenarios_canceled++;
     }
  }

string BuildScenarioLayerSignature()
  {
   return StringFormat(
      "h1=%s|%s|m30=%s|%s|perm=%s|permref=%s|h1ext=%s|m30ext=%s|liq=%I64d/%I64d/%I64d|m1cons=%d|root_count=%d|root_state_ver=%I64d",
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
      g_liquidity_body_deliveries,
      ArraySize(g_strategy_liquidity_consumed),
      ArraySize(g_root_reactions),
      g_root_reaction_state_version);
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

   V1RegimeResearchSnapshot regime_snapshot;
   bool regime_pass=
      EvaluateRegimeResearchSnapshot(draft,frozen_at,regime_snapshot);
   if(!regime_pass)
     {
      g_sources[source_index].regime_research_rejected=true;
      g_regime_plan_reject++;
      LogRegimeResearchSnapshot("REGIME_RESEARCH_PLAN_REJECTED",
                                draft,
                                frozen_at,
                                regime_snapshot);
      return;
     }

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
   g_scenarios[n].regime_research_v1_evaluated=regime_snapshot.valid;
   g_scenarios[n].regime_research_parent_pass=regime_snapshot.parent_pass;
   g_scenarios[n].regime_research_expansion_pass=regime_snapshot.expansion_pass;
   g_scenarios[n].regime_research_v1_pass=regime_snapshot.v1_pass;
   g_scenarios[n].regime_m30_wave_count=regime_snapshot.wave_count;
   g_scenarios[n].regime_progression_success=regime_snapshot.progression_success;
   g_scenarios[n].regime_progression_total=regime_snapshot.progression_total;
   g_scenarios[n].regime_progression_ratio=regime_snapshot.progression_ratio;
   g_scenarios[n].regime_protected_break_count=regime_snapshot.protected_break_count;
   g_scenarios[n].regime_recent_leg_mean=regime_snapshot.recent_leg_mean;
   g_scenarios[n].regime_prior_leg_mean=regime_snapshot.prior_leg_mean;
   g_scenarios[n].regime_leg_expansion_ratio=regime_snapshot.expansion_ratio;
   g_scenarios[n].source_contact_at=0;
   g_scenarios[n].source_contact_bar_open=0;
   g_scenarios[n].eligible_pool_count_at_contact=0;
   g_scenarios[n].active_sweep_event_id="";
   g_scenarios[n].active_sweep_bar_open=0;
   g_scenarios[n].active_sweep_at=0;
   g_scenarios[n].active_sweep_extreme=0.0;
   g_scenarios[n].authorized_sweep_count=0;
   g_scenarios[n].scenario_choch_event_id="";
   g_scenarios[n].scenario_choch_bar_open=0;
   g_scenarios[n].scenario_choch_at=0;
   g_scenarios[n].eligible_fvg_count_at_choch=0;
   g_scenarios[n].selected_fvg_id="";
   g_scenarios[n].selected_fvg_direction=0;
   g_scenarios[n].selected_fvg_candle1_open=0;
   g_scenarios[n].selected_fvg_candle2_open=0;
   g_scenarios[n].selected_fvg_candle3_open=0;
   g_scenarios[n].selected_fvg_available_at=0;
   g_scenarios[n].selected_fvg_bottom=0.0;
   g_scenarios[n].selected_fvg_top=0.0;
   g_scenarios[n].selected_fvg_width=0.0;
   g_scenarios[n].selected_fvg_width_ticks=0;
   g_scenarios[n].fvg_frozen_at=0;
   g_scenarios[n].no_trade_at=0;
   g_scenarios[n].no_trade_reason="";
   g_scenarios[n].strategy_signal_valid=false;
   g_scenarios[n].strategy_entry_price=0.0;
   g_scenarios[n].raw_strategy_sl=0.0;
   g_scenarios[n].normalized_sl=0.0;
   g_scenarios[n].stop_loss_model=(int)InpStopLossModel;
   g_scenarios[n].stop_loss_reference_price=0.0;
   g_scenarios[n].stop_loss_reference_width=0.0;
   g_scenarios[n].stop_loss_merged_from_contributors=false;
   g_scenarios[n].stop_loss_contributor_scenario_id=scenario_id;
   g_scenarios[n].stop_loss_contributor_root_id=draft.root_zone_id;
   g_scenarios[n].final_objective_id="";
   g_scenarios[n].final_objective_candidate_index=-1;
   g_scenarios[n].final_objective_liquidity_id="";
   g_scenarios[n].final_objective_price=0.0;
   g_scenarios[n].final_objective_planned_r=0.0;
   g_scenarios[n].final_objective_selected_at=0;
   g_scenarios[n].execution_opportunity_merged=false;
   g_scenarios[n].execution_master_scenario_id=scenario_id;
   g_scenarios[n].execution_contributor_scenario_ids=scenario_id;
   g_scenarios[n].execution_contributor_root_ids=draft.root_zone_id;
   g_scenarios[n].execution_contributor_count=1;
   g_scenarios[n].execution_status=V1_EXEC_NONE;
   g_scenarios[n].terminal_reason="";
   g_scenarios[n].order_volume=0.0;
   g_scenarios[n].pending_submitted_at=0;
   g_scenarios[n].request_id=0;
   g_scenarios[n].broker_order_ticket=0;
   g_scenarios[n].strategy_cancel_at=0;
   g_scenarios[n].strategy_cancel_reason="";
   g_scenarios[n].cancel_request_sent=false;
   g_scenarios[n].fill_at=0;
   g_scenarios[n].fill_price=0.0;
   g_scenarios[n].broker_deal_ticket=0;
   g_scenarios[n].broker_position_id=0;
   g_scenarios[n].position_closed_at=0;
   g_scenarios[n].exit_price=0.0;
   g_scenarios[n].exit_reason=0;
   g_scenarios[n].exit_deal_ticket=0;
   g_scenarios[n].execution_divergence=false;
   g_scenarios[n].execution_divergence_reason="";
   g_scenarios[n].startup_inside_source=false;
   g_scenarios[n].startup_exit_seen=false;
   g_scenarios[n].canceled_at=0;
   g_scenarios[n].cancel_reason="";

   BindRootScenarioOwner(draft.root_zone_id,scenario_id);

   LogLine("SCENARIO_ROOT_BOUND",
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

      family[i].scenario_index=n;
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
           StringFormat("state=PLANNED scope=%s direction=%s active_map_tf=%s owner_id=%s parent_context_id=%s h1_trend_at_freeze=%s h1_owner_id_at_freeze=%s m30_trend_at_freeze=%s m30_owner_id_at_freeze=%s reversal_permission_at_freeze=%s permission_reference_id=%s permission_opened_at=%s root_zone_id=%s final_source_id=%s source_tf=%s source_bottom=%.10f source_top=%.10f map_range_low=%.10f map_range_high=%.10f map_eq=%.10f plan_reference_bar_open=%s plan_reference_price=%.10f primary_directional_horizon=%.10f objective_count=%d root_contact_required=true root_contact_at=NA strategy_source_kind=ROOT child_required=false linear_trigger_pipeline=true detector_sequence=ROOT_CONTACT_THEN_M1_SWEEP_THEN_M1_CHOCH fvg_search_enabled=true",
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

   g_regime_plan_pass++;
   LogRegimeResearchSnapshot("REGIME_RESEARCH_PLAN_ACCEPTED",
                             draft,
                             frozen_at,
                             regime_snapshot);
   g_scenarios_planned++;
   g_precontact_root_plans++;
  }

void RefreshScenarioLayer(const datetime available_at,const bool force=false)
  {
   // D-135: objective consumption is event-driven. First perform an O(1)
   // authority signature check; only real authority changes may scan the
   // historical scenario/source ledgers.
   string signature=BuildScenarioLayerSignature();
   if(!force && signature==g_scenario_layer_signature)
      return;
   g_scenario_layer_signature=signature;

   CancelInvalidScenarioPlans(available_at);

   for(int root_index=0;root_index<ArraySize(g_sources);root_index++)
     {
      if(!g_sources[root_index].valid ||
         g_sources[root_index].kind!=V1_SOURCE_ROOT ||
         g_sources[root_index].strategy_state!=V1_SOURCE_ACTIVE ||
         g_sources[root_index].regime_research_rejected)
         continue;

      const string root_id=g_sources[root_index].id;

      if(HasActiveScenarioForRoot(root_id) ||
         !RootWatchEligibleForPreContactPlan(root_id))
         continue;

      V1ScenarioDraft draft;
      string reject_reason="";
      if(!BuildRootScenarioDraft(root_index,draft,reject_reason))
         continue;

      V1ObjectiveCandidate family[];
      ArrayResize(family,0);
      datetime plan_reference_bar_open=0;
      double plan_reference_price=0.0;
      double primary_horizon=0.0;

      if(!BuildFrozenObjectiveFamily(draft,
                                     available_at,
                                     plan_reference_bar_open,
                                     plan_reference_price,
                                     primary_horizon,
                                     family))
        {
         LogLine("ROOT_SCENARIO_NOT_READY",
                 TfName(g_sources[root_index].tf),
                 available_at,
                 root_id,
                 StringFormat("reason=NO_OBJECTIVE_FAMILY scope=%s direction=%s active_map_tf=%s owner_id=%s strategy_source_kind=ROOT child_required=false Root_remains_watchable=true retrospective_plan_forbidden_after_contact=true",
                              ScenarioScopeName(draft.scope),
                              DirectionName(draft.direction),
                              TfName(draft.active_map_tf),
                              draft.owner_id));
         g_scenarios_no_objective++;
         continue;
        }

      StoreScenarioPlan(draft,
                        available_at,
                        plan_reference_bar_open,
                        plan_reference_price,
                        primary_horizon,
                        family);
     }
  }

//+------------------------------------------------------------------+
//| D-127 detector / sequence separation                             |
//+------------------------------------------------------------------+
void AddD127M1SweepDetectorPool(const V1LiquidityPool &pool,
                                const datetime bar_open)
  {
   int n=ArraySize(g_m1_sweep_detector_snapshot);
   if(ArrayResize(g_m1_sweep_detector_snapshot,n+1,256)<0)
      return;

   g_m1_sweep_detector_snapshot[n].valid=true;
   g_m1_sweep_detector_snapshot[n].liquidity_id=pool.id;
   g_m1_sweep_detector_snapshot[n].family=pool.family;
   g_m1_sweep_detector_snapshot[n].tf=pool.tf;
   g_m1_sweep_detector_snapshot[n].side=pool.side;
   g_m1_sweep_detector_snapshot[n].bottom=pool.bottom;
   g_m1_sweep_detector_snapshot[n].top=pool.top;
   g_m1_sweep_detector_snapshot[n].available_at=pool.available_at;
   g_m1_sweep_detector_snapshot[n].snapshot_bar_open=bar_open;
  }

void PrepareD127M1SweepDetectorSnapshot(const datetime bar_open)
  {
   ArrayResize(g_m1_sweep_detector_snapshot,0);
   ArrayResize(g_m1_sweep_detections,0);
   g_m1_sweep_detector_bar_open=bar_open;

   // Detector causality only: use liquidity that is already known when the
   // M1 bar begins. No Root, scenario, direction, distance, family-ranking,
   // child, or quality gate is applied here.
   for(int i=0;i<ArraySize(g_liquidity);i++)
     {
      if(!g_liquidity[i].valid ||
         g_liquidity[i].available_at>bar_open ||
         g_liquidity[i].strategy_consumed)
         continue;

      AddD127M1SweepDetectorPool(g_liquidity[i],bar_open);
     }
  }

void AddD127M1SweepDetection(const V1M1SweepDetectorPool &pool,
                             const MqlRates &bar,
                             const datetime available_at)
  {
   int n=ArraySize(g_m1_sweep_detections);
   if(ArrayResize(g_m1_sweep_detections,n+1,64)<0)
      return;

   string id=StringFormat("M1:sweep:%s:%I64d",
                          pool.liquidity_id,
                          (long)bar.time);

   g_m1_sweep_detections[n].valid=true;
   g_m1_sweep_detections[n].id=id;
   g_m1_sweep_detections[n].liquidity_id=pool.liquidity_id;
   g_m1_sweep_detections[n].family=pool.family;
   g_m1_sweep_detections[n].tf=pool.tf;
   g_m1_sweep_detections[n].side=pool.side;
   g_m1_sweep_detections[n].bottom=pool.bottom;
   g_m1_sweep_detections[n].top=pool.top;
   g_m1_sweep_detections[n].pool_available_at=pool.available_at;
   g_m1_sweep_detections[n].bar_open=bar.time;
   g_m1_sweep_detections[n].available_at=available_at;
   g_m1_sweep_detector_events++;

   LogLine("M1_SWEEP_DETECTED",
           "M1",
           available_at,
           id,
           StringFormat("liquidity_id=%s family=%s pool_tf=%s side=%s bottom=%.10f top=%.10f pool_available_at=%s bar_open=%s high=%.10f low=%.10f close=%.10f detector_only=true strategy_authority=false root_filter=false scenario_filter=false direction_filter=false root_intersection_required=false child_filter=false",
                        pool.liquidity_id,
                        LiquidityFamilyName(pool.family),
                        TfName(pool.tf),
                        SideName(pool.side),
                        pool.bottom,
                        pool.top,
                        TimeToString(pool.available_at,TIME_DATE|TIME_SECONDS),
                        TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                        bar.high,
                        bar.low,
                        bar.close));
  }

void EvaluateD127M1SweepDetector(const MqlRates &bar,
                                 const datetime available_at)
  {
   ArrayResize(g_m1_sweep_detections,0);
   if(g_m1_sweep_detector_bar_open!=bar.time)
      return;

   for(int i=0;i<ArraySize(g_m1_sweep_detector_snapshot);i++)
     {
      if(!g_m1_sweep_detector_snapshot[i].valid)
         continue;

      int consumption=PhysicalConsumptionForBar(
         g_m1_sweep_detector_snapshot[i].side,
         g_m1_sweep_detector_snapshot[i].bottom,
         g_m1_sweep_detector_snapshot[i].top,
         bar);

      if(consumption!=V1_LIQ_CONSUME_SWEEP)
         continue;

      AddD127M1SweepDetection(g_m1_sweep_detector_snapshot[i],
                              bar,
                              available_at);
     }
  }

void ProcessD127ScenarioSweepStage(const MqlRates &bar,
                                   const datetime available_at)
  {
   int pos=0;
   while(pos<ArraySize(g_waiting_sweep_scenario_indices))
     {
      int sidx=g_waiting_sweep_scenario_indices[pos];
      if(sidx<0 || sidx>=ArraySize(g_scenarios) ||
         !g_scenarios[sidx].valid ||
         g_scenarios[sidx].strategy_state!=V1_STRATEGY_WAITING_SWEEP ||
         g_scenarios[sidx].source_contact_at<=0)
        {
         D135RemoveIndexValue(g_waiting_sweep_scenario_indices,sidx);
         continue;
        }

      if(bar.time<g_scenarios[sidx].source_contact_at)
        { pos++; continue; }

      int required_side=(g_scenarios[sidx].direction>0 ? V1_SIDE_LOW : V1_SIDE_HIGH);
      int matched=0;
      string detector_ids="";
      string liquidity_ids="";
      for(int i=0;i<ArraySize(g_m1_sweep_detections);i++)
        {
         if(!g_m1_sweep_detections[i].valid || g_m1_sweep_detections[i].side!=required_side)
            continue;
         if(detector_ids!="") detector_ids+="|";
         detector_ids+=g_m1_sweep_detections[i].id;
         if(liquidity_ids!="") liquidity_ids+="|";
         liquidity_ids+=g_m1_sweep_detections[i].liquidity_id;
         matched++;
        }
      if(matched<=0)
        { pos++; continue; }

      string stage_id=StringFormat("%s:scenario_sweep:%I64d",g_scenarios[sidx].id,(long)bar.time);
      g_scenarios[sidx].active_sweep_event_id=stage_id;
      g_scenarios[sidx].active_sweep_bar_open=bar.time;
      g_scenarios[sidx].active_sweep_at=available_at;
      g_scenarios[sidx].active_sweep_extreme=(g_scenarios[sidx].direction>0 ? bar.low : bar.high);
      g_scenarios[sidx].authorized_sweep_count=matched;
      g_scenarios[sidx].strategy_state=V1_STRATEGY_WAITING_TRIGGER;
      D135RemoveIndexValue(g_waiting_sweep_scenario_indices,sidx);
      D135AddUniqueIndex(g_waiting_trigger_scenario_indices,sidx);
      g_scenario_sweep_accepts++;

      LogLine("SCENARIO_SWEEP_ACCEPTED","M1",available_at,stage_id,
              StringFormat("scenario_id=%s root_zone_id=%s direction=%s required_side=%s root_contact_at=%s sweep_bar_open=%s sweep_extreme=%.10f detector_count=%d detector_ids=%s liquidity_ids=%s state=WAITING_CHOCH rule=SEQUENCE_ONLY root_reintersection=false family_whitelist=false child_required=false choch_reference_freeze=false",
                           g_scenarios[sidx].id,g_scenarios[sidx].root_zone_id,DirectionName(g_scenarios[sidx].direction),SideName(required_side),
                           TimeToString(g_scenarios[sidx].source_contact_at,TIME_DATE|TIME_SECONDS),TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                           g_scenarios[sidx].active_sweep_extreme,matched,detector_ids,liquidity_ids));
     }
  }

void ProcessD127ScenarioChochStage(const MqlRates &bar,
                                   const datetime available_at)
  {
   if(!g_m1_choch_detection.valid || g_m1_choch_detection.bar_open!=bar.time)
      return;

   int pos=0;
   while(pos<ArraySize(g_waiting_trigger_scenario_indices))
     {
      int sidx=g_waiting_trigger_scenario_indices[pos];
      if(sidx<0 || sidx>=ArraySize(g_scenarios) ||
         !g_scenarios[sidx].valid ||
         g_scenarios[sidx].strategy_state!=V1_STRATEGY_WAITING_TRIGGER ||
         g_scenarios[sidx].active_sweep_at<=0)
        {
         D135RemoveIndexValue(g_waiting_trigger_scenario_indices,sidx);
         continue;
        }
      if(g_m1_choch_detection.direction!=g_scenarios[sidx].direction ||
         g_m1_choch_detection.bar_open<=g_scenarios[sidx].active_sweep_bar_open)
        { pos++; continue; }

      g_scenarios[sidx].scenario_choch_event_id=g_m1_choch_detection.id;
      g_scenarios[sidx].scenario_choch_bar_open=g_m1_choch_detection.bar_open;
      g_scenarios[sidx].scenario_choch_at=available_at;
      g_scenarios[sidx].strategy_state=V1_STRATEGY_WAITING_FVG;
      D135RemoveIndexValue(g_waiting_trigger_scenario_indices,sidx);
      g_scenario_choch_accepts++;

      LogLine("SCENARIO_CHOCH_ACCEPTED","M1",available_at,g_m1_choch_detection.id,
              StringFormat("scenario_id=%s root_zone_id=%s direction=%s scenario_sweep_event_id=%s sweep_bar_open=%s choch_bar_open=%s broken_swing_id=%s broken_price=%.10f state=WAITING_FVG rule=SEQUENCE_ONLY detector_source=M1_CHOCH_DETECTED extra_reference_filter=false opposite_trend_at_sweep_filter=false initial_bos_fallback=false child_required=false fvg_search_enabled=true order_authorization=false",
                           g_scenarios[sidx].id,g_scenarios[sidx].root_zone_id,DirectionName(g_scenarios[sidx].direction),g_scenarios[sidx].active_sweep_event_id,
                           TimeToString(g_scenarios[sidx].active_sweep_bar_open,TIME_DATE|TIME_SECONDS),TimeToString(g_m1_choch_detection.bar_open,TIME_DATE|TIME_SECONDS),
                           g_m1_choch_detection.broken_swing_id,g_m1_choch_detection.broken_price));

      ProcessD128AScenarioFvgFreeze(sidx,bar,available_at);
     }
  }


//+------------------------------------------------------------------+
//| D-128A independent M1 FVG detector + causal scenario selection   |
//+------------------------------------------------------------------+
double NormalizeD128APriceToTick(const double price)
  {
   double tick=LiquidityTickSize();
   int digits=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   if(tick<=0.0)
      return NormalizeDouble(price,digits);
   return NormalizeDouble(MathRound(price/tick)*tick,digits);
  }

long D128AWidthTicks(const double bottom,const double top)
  {
   double tick=LiquidityTickSize();
   if(tick<=0.0 || top<=bottom)
      return 0;
   return (long)MathRound((top-bottom)/tick);
  }
bool D128ABarIntersectsFvg(const MqlRates &bar,
                           const V1M1FvgDetection &fvg)
  {
   return (bar.high>=fvg.bottom && bar.low<=fvg.top);
  }

void AddD128AM1FvgDetection(const int direction,
                            const MqlRates &candle1,
                            const MqlRates &candle2,
                            const MqlRates &candle3,
                            const datetime available_at,
                            const double raw_bottom,
                            const double raw_top)
  {
   double bottom=NormalizeD128APriceToTick(raw_bottom);
   double top=NormalizeD128APriceToTick(raw_top);
   long width_ticks=D128AWidthTicks(bottom,top);
   if(width_ticks<=0 || top<=bottom)
      return;

   int n=ArraySize(g_m1_fvg_detections);
   if(ArrayResize(g_m1_fvg_detections,n+1,128)<0)
      return;

   string id=StringFormat("M1:fvg:%s:%I64d:%I64d",
                          DirectionName(direction),
                          (long)candle1.time,
                          (long)candle3.time);

   g_m1_fvg_detections[n].valid=true;
   g_m1_fvg_detections[n].id=id;
   g_m1_fvg_detections[n].direction=direction;
   g_m1_fvg_detections[n].candle1_open=candle1.time;
   g_m1_fvg_detections[n].candle2_open=candle2.time;
   g_m1_fvg_detections[n].candle3_open=candle3.time;
   g_m1_fvg_detections[n].available_at=available_at;
   g_m1_fvg_detections[n].bottom=bottom;
   g_m1_fvg_detections[n].top=top;
   g_m1_fvg_detections[n].width=top-bottom;
   g_m1_fvg_detections[n].width_ticks=width_ticks;
   g_m1_fvg_detector_events++;

   LogLine("M1_FVG_DETECTED",
           "M1",
           available_at,
           id,
           StringFormat("direction=%s candle1_open=%s candle2_open=%s candle3_open=%s bottom=%.10f top=%.10f width=%.10f width_ticks=%I64d available_at=%s detector_only=true scenario_filter=false root_filter=false sweep_filter=false choch_filter=false clock_contiguous=true",
                        DirectionName(direction),
                        TimeToString(candle1.time,TIME_DATE|TIME_SECONDS),
                        TimeToString(candle2.time,TIME_DATE|TIME_SECONDS),
                        TimeToString(candle3.time,TIME_DATE|TIME_SECONDS),
                        bottom,
                        top,
                        top-bottom,
                        width_ticks,
                        TimeToString(available_at,TIME_DATE|TIME_SECONDS)));
  }

void EvaluateD128AM1FvgDetector(const V1StructureState &state,
                                const MqlRates &bar,
                                const datetime available_at)
  {
   if(state.recent_count<2)
      return;

   MqlRates candle1=state.recent0;
   MqlRates candle2=state.recent1;
   MqlRates candle3=bar;

   bool bullish_geometry=(candle3.low>candle1.high);
   bool bearish_geometry=(candle3.high<candle1.low);
   if(!bullish_geometry && !bearish_geometry)
      return;

   bool contiguous=((candle2.time-candle1.time)==60 &&
                    (candle3.time-candle2.time)==60);
   if(!contiguous)
     {
      g_m1_fvg_gap_rejections++;
      LogLine("M1_FVG_REJECTED",
              "M1",
              available_at,
              "",
              StringFormat("reason=SESSION_OR_DATA_GAP_FVG direction=%s candle1_open=%s candle2_open=%s candle3_open=%s clock_contiguous=false strategy_authority=false",
                           bullish_geometry ? "LONG" : "SHORT",
                           TimeToString(candle1.time,TIME_DATE|TIME_SECONDS),
                           TimeToString(candle2.time,TIME_DATE|TIME_SECONDS),
                           TimeToString(candle3.time,TIME_DATE|TIME_SECONDS)));
      return;
     }

   if(bullish_geometry)
      AddD128AM1FvgDetection(1,
                             candle1,
                             candle2,
                             candle3,
                             available_at,
                             candle1.high,
                             candle3.low);
   else
      AddD128AM1FvgDetection(-1,
                             candle1,
                             candle2,
                             candle3,
                             available_at,
                             candle3.high,
                             candle1.low);
  }

bool D128AFvgWasRetestedBeforeSelection(const V1M1FvgDetection &fvg,
                                        const MqlRates &choch_bar,
                                        datetime &first_retest_bar_open,
                                        bool &history_error)
  {
   first_retest_bar_open=0;
   history_error=false;

   // Formation bar is never its own retest. Begin with the next causal M1 bar.
   datetime start=fvg.candle3_open+60;
   datetime prior_end=choch_bar.time-60;

   if(start<=prior_end)
     {
      MqlRates bars[];
      ArraySetAsSeries(bars,false);
      ResetLastError();
      int copied=CopyRates(_Symbol,PERIOD_M1,start,prior_end,bars);
      if(copied<0)
        {
         history_error=true;
         return false;
        }

      for(int i=0;i<copied;i++)
        {
         if(D128ABarIntersectsFvg(bars[i],fvg))
           {
            first_retest_bar_open=bars[i].time;
            return true;
           }
        }
     }

   // If the CHoCH bar is later than Candle3, it is also a completed bar before
   // selection at its close and therefore counts as a pre-selection retest.
   if(choch_bar.time>fvg.candle3_open && D128ABarIntersectsFvg(choch_bar,fvg))
     {
      first_retest_bar_open=choch_bar.time;
      return true;
     }

   return false;
  }

void MarkD128AScenarioNoTrade(const int scenario_index,
                              const datetime available_at,
                              const string reason,
                              const int eligible_count)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return;

   g_scenarios[scenario_index].eligible_fvg_count_at_choch=eligible_count;
   g_scenarios[scenario_index].strategy_state=V1_STRATEGY_NO_TRADE;
   g_scenarios[scenario_index].no_trade_at=available_at;
   g_scenarios[scenario_index].no_trade_reason=reason;
   ReleaseRootScenarioOwner(g_scenarios[scenario_index].root_zone_id,
                            g_scenarios[scenario_index].id);

   if(reason=="NO_CAUSAL_FRESH_FVG")
      g_scenario_no_causal_fvg++;
   else if(reason=="AMBIGUOUS_EXECUTION_FVG")
      g_scenario_ambiguous_fvg++;

   LogLine("SCENARIO_FVG_NO_ENTRY",
           "M1",
           available_at,
           g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s root_zone_id=%s direction=%s sweep_bar_open=%s choch_bar_open=%s eligible_fvg_count=%d reason=%s state=NO_TRADE entry_geometry_enabled=false order_authorization=false",
                        g_scenarios[scenario_index].id,
                        g_scenarios[scenario_index].root_zone_id,
                        DirectionName(g_scenarios[scenario_index].direction),
                        TimeToString(g_scenarios[scenario_index].active_sweep_bar_open,TIME_DATE|TIME_SECONDS),
                        TimeToString(g_scenarios[scenario_index].scenario_choch_bar_open,TIME_DATE|TIME_SECONDS),
                        eligible_count,
                        reason));
  }

void ProcessD128AScenarioFvgFreeze(const int scenario_index,
                                   const MqlRates &choch_bar,
                                   const datetime available_at)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid ||
      g_scenarios[scenario_index].strategy_state!=V1_STRATEGY_WAITING_FVG ||
      g_scenarios[scenario_index].active_sweep_at<=0 ||
      g_scenarios[scenario_index].scenario_choch_at<=0)
      return;

   int eligible_indices[];
   ArrayResize(eligible_indices,0);

   for(int i=0;i<ArraySize(g_m1_fvg_detections);i++)
     {
      if(!g_m1_fvg_detections[i].valid ||
         g_m1_fvg_detections[i].direction!=g_scenarios[scenario_index].direction)
         continue;

      // D-128A operational causal-leg boundary. Candle1 may precede the Sweep;
      // what matters is that the three-candle FVG becomes a confirmed detector
      // fact strictly AFTER the accepted Sweep close and no later than CHoCH.
      if(g_m1_fvg_detections[i].available_at<=g_scenarios[scenario_index].active_sweep_at ||
         g_m1_fvg_detections[i].available_at>g_scenarios[scenario_index].scenario_choch_at)
         continue;

      datetime first_retest=0;
      bool history_error=false;
      bool retested=D128AFvgWasRetestedBeforeSelection(g_m1_fvg_detections[i],
                                                        choch_bar,
                                                        first_retest,
                                                        history_error);
      if(history_error)
        {
         LogLine("SCENARIO_FVG_EXCLUDED",
                 "M1",
                 available_at,
                 g_m1_fvg_detections[i].id,
                 StringFormat("scenario_id=%s reason=FVG_FRESHNESS_HISTORY_ERROR fail_closed=true",
                              g_scenarios[scenario_index].id));
         continue;
        }

      if(retested)
        {
         g_scenario_fvg_preselection_retests++;
         LogLine("SCENARIO_FVG_EXCLUDED",
                 "M1",
                 available_at,
                 g_m1_fvg_detections[i].id,
                 StringFormat("scenario_id=%s reason=PRE_SELECTION_RETEST first_retest_bar_open=%s bottom=%.10f top=%.10f formation_bar_self_retest=false",
                              g_scenarios[scenario_index].id,
                              TimeToString(first_retest,TIME_DATE|TIME_SECONDS),
                              g_m1_fvg_detections[i].bottom,
                              g_m1_fvg_detections[i].top));
         continue;
        }

      int n=ArraySize(eligible_indices);
      if(ArrayResize(eligible_indices,n+1,16)<0)
         continue;
      eligible_indices[n]=i;
      g_scenario_fvg_candidates++;

      LogLine("SCENARIO_FVG_CANDIDATE",
              "M1",
              available_at,
              g_m1_fvg_detections[i].id,
              StringFormat("scenario_id=%s root_zone_id=%s direction=%s sweep_at=%s choch_at=%s candle1_open=%s candle2_open=%s candle3_open=%s fvg_available_at=%s bottom=%.10f top=%.10f width=%.10f width_ticks=%I64d fresh=true same_direction=true causal_availability_after_sweep=true candidate_freeze_at=%s",
                           g_scenarios[scenario_index].id,
                           g_scenarios[scenario_index].root_zone_id,
                           DirectionName(g_scenarios[scenario_index].direction),
                           TimeToString(g_scenarios[scenario_index].active_sweep_at,TIME_DATE|TIME_SECONDS),
                           TimeToString(g_scenarios[scenario_index].scenario_choch_at,TIME_DATE|TIME_SECONDS),
                           TimeToString(g_m1_fvg_detections[i].candle1_open,TIME_DATE|TIME_SECONDS),
                           TimeToString(g_m1_fvg_detections[i].candle2_open,TIME_DATE|TIME_SECONDS),
                           TimeToString(g_m1_fvg_detections[i].candle3_open,TIME_DATE|TIME_SECONDS),
                           TimeToString(g_m1_fvg_detections[i].available_at,TIME_DATE|TIME_SECONDS),
                           g_m1_fvg_detections[i].bottom,
                           g_m1_fvg_detections[i].top,
                           g_m1_fvg_detections[i].width,
                           g_m1_fvg_detections[i].width_ticks,
                           TimeToString(available_at,TIME_DATE|TIME_SECONDS)));
     }

   int eligible_count=ArraySize(eligible_indices);
   g_scenarios[scenario_index].eligible_fvg_count_at_choch=eligible_count;
   g_scenarios[scenario_index].fvg_frozen_at=available_at;

   if(eligible_count<=0)
     {
      MarkD128AScenarioNoTrade(scenario_index,
                              available_at,
                              "NO_CAUSAL_FRESH_FVG",
                              0);
      return;
     }

   long max_ticks=-1;
   int selected_index=-1;
   int max_count=0;
   for(int k=0;k<eligible_count;k++)
     {
      int idx=eligible_indices[k];
      long ticks=g_m1_fvg_detections[idx].width_ticks;
      if(ticks>max_ticks)
        {
         max_ticks=ticks;
         selected_index=idx;
         max_count=1;
        }
      else if(ticks==max_ticks)
         max_count++;
     }

   if(selected_index<0 || max_count!=1)
     {
      MarkD128AScenarioNoTrade(scenario_index,
                              available_at,
                              "AMBIGUOUS_EXECUTION_FVG",
                              eligible_count);
      return;
     }

   V1M1FvgDetection selected=g_m1_fvg_detections[selected_index];
   g_scenarios[scenario_index].selected_fvg_id=selected.id;
   g_scenarios[scenario_index].selected_fvg_direction=selected.direction;
   g_scenarios[scenario_index].selected_fvg_candle1_open=selected.candle1_open;
   g_scenarios[scenario_index].selected_fvg_candle2_open=selected.candle2_open;
   g_scenarios[scenario_index].selected_fvg_candle3_open=selected.candle3_open;
   g_scenarios[scenario_index].selected_fvg_available_at=selected.available_at;
   g_scenarios[scenario_index].selected_fvg_bottom=selected.bottom;
   g_scenarios[scenario_index].selected_fvg_top=selected.top;
   g_scenarios[scenario_index].selected_fvg_width=selected.width;
   g_scenarios[scenario_index].selected_fvg_width_ticks=selected.width_ticks;
   g_scenarios[scenario_index].strategy_state=V1_STRATEGY_WAITING_EXECUTION_GEOMETRY;
   D135AddUniqueIndex(g_waiting_execution_geometry_indices,scenario_index);
   g_scenario_fvg_selected++;

   LogLine("SCENARIO_FVG_SELECTED",
           "M1",
           available_at,
           selected.id,
           StringFormat("scenario_id=%s root_zone_id=%s direction=%s eligible_fvg_count=%d selection=WIDEST_TICK_NORMALIZED exact_max_tie=false candle1_open=%s candle2_open=%s candle3_open=%s available_at=%s bottom=%.10f top=%.10f width=%.10f width_ticks=%I64d fvg_frozen_at=%s state=WAITING_EXECUTION_GEOMETRY next_same_cycle=ENTRY_SL_TP_AND_EXECUTION_AUTHORIZATION",
                        g_scenarios[scenario_index].id,
                        g_scenarios[scenario_index].root_zone_id,
                        DirectionName(g_scenarios[scenario_index].direction),
                        eligible_count,
                        TimeToString(selected.candle1_open,TIME_DATE|TIME_SECONDS),
                        TimeToString(selected.candle2_open,TIME_DATE|TIME_SECONDS),
                        TimeToString(selected.candle3_open,TIME_DATE|TIME_SECONDS),
                        TimeToString(selected.available_at,TIME_DATE|TIME_SECONDS),
                        selected.bottom,
                        selected.top,
                        selected.width,
                        selected.width_ticks,
                        TimeToString(available_at,TIME_DATE|TIME_SECONDS)));
  }

void PruneD128AM1FvgDetections()
  {
   datetime earliest_sweep=0;
   for(int p=0;p<ArraySize(g_waiting_trigger_scenario_indices);p++)
     {
      int i=g_waiting_trigger_scenario_indices[p];
      if(i<0 || i>=ArraySize(g_scenarios) ||
         !g_scenarios[i].valid ||
         g_scenarios[i].strategy_state!=V1_STRATEGY_WAITING_TRIGGER ||
         g_scenarios[i].active_sweep_at<=0)
         continue;
      if(earliest_sweep==0 || g_scenarios[i].active_sweep_at<earliest_sweep)
         earliest_sweep=g_scenarios[i].active_sweep_at;
     }

   if(earliest_sweep==0)
     {
      ArrayResize(g_m1_fvg_detections,0);
      return;
     }

   int write=0;
   int n=ArraySize(g_m1_fvg_detections);
   for(int i=0;i<n;i++)
     {
      if(!g_m1_fvg_detections[i].valid || g_m1_fvg_detections[i].available_at<=earliest_sweep)
         continue;
      if(write!=i)
         g_m1_fvg_detections[write]=g_m1_fvg_detections[i];
      write++;
     }
   ArrayResize(g_m1_fvg_detections,write);
  }


//+------------------------------------------------------------------+
//| D-128B..D-133 strategy geometry + contributor execution          |
//+------------------------------------------------------------------+
double NormalizePriceFloorToTick(const double price)
  {
   double tick=LiquidityTickSize();
   int digits=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   if(tick<=0.0)
      return NormalizeDouble(price,digits);
   double units=MathFloor(price/tick+1.0e-10);
   return NormalizeDouble(units*tick,digits);
  }

double NormalizePriceCeilToTick(const double price)
  {
   double tick=LiquidityTickSize();
   int digits=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   if(tick<=0.0)
      return NormalizeDouble(price,digits);
   double units=MathCeil(price/tick-1.0e-10);
   return NormalizeDouble(units*tick,digits);
  }

bool IsPriceOnTickGrid(const double price)
  {
   double tick=LiquidityTickSize();
   if(tick<=0.0)
      return false;
   double nearest=MathRound(price/tick)*tick;
   return (MathAbs(price-nearest)<=tick*1.0e-6);
  }

void MarkExecutionNoTrade(const int scenario_index,
                          const datetime available_at,
                          const string reason,
                          const int execution_status)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return;

   if(!g_scenarios[scenario_index].valid || g_scenarios[scenario_index].strategy_state==V1_STRATEGY_FILLED)
      return;

   g_scenarios[scenario_index].strategy_state=V1_STRATEGY_NO_TRADE;
   g_scenarios[scenario_index].no_trade_at=available_at;
   g_scenarios[scenario_index].no_trade_reason=reason;
   g_scenarios[scenario_index].terminal_reason=reason;
   g_scenarios[scenario_index].execution_status=execution_status;
   ReleaseRootScenarioOwner(g_scenarios[scenario_index].root_zone_id,g_scenarios[scenario_index].id);

   LogLine("SCENARIO_EXECUTION_NO_TRADE",
           "M1",
           available_at,
           g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s direction=%s selected_fvg_id=%s entry=%.10f sl=%.10f final_objective_id=%s tp=%.10f strategy_signal_valid=%s execution_status=%s reason=%s state=NO_TRADE retry=false",
                        g_scenarios[scenario_index].id,
                        DirectionName(g_scenarios[scenario_index].direction),
                        g_scenarios[scenario_index].selected_fvg_id=="" ? "NA" : g_scenarios[scenario_index].selected_fvg_id,
                        g_scenarios[scenario_index].strategy_entry_price,
                        g_scenarios[scenario_index].normalized_sl,
                        g_scenarios[scenario_index].final_objective_id=="" ? "NA" : g_scenarios[scenario_index].final_objective_id,
                        g_scenarios[scenario_index].final_objective_price,
                        g_scenarios[scenario_index].strategy_signal_valid ? "true" : "false",
                        ExecutionStatusName(g_scenarios[scenario_index].execution_status),
                        reason));
  }

bool ObjectiveCandidateConsumedNow(const V1ObjectiveCandidate &candidate)
  {
   if(candidate.consumed)
      return true;
   if(IsStrategyLiquidityConsumed(candidate.liquidity_id))
      return true;
   return (FindActiveLiquidityById(candidate.liquidity_id)<0);
  }

bool SelectFinalObjectiveForScenario(const int scenario_index,
                                     const datetime available_at,
                                     string &failure_reason)
  {
   failure_reason="";
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
     {
      failure_reason="SCENARIO_INDEX_INVALID";
      return false;
     }

   double entry=g_scenarios[scenario_index].strategy_entry_price;
   double sl=g_scenarios[scenario_index].normalized_sl;
   double tick_size=LiquidityTickSize();
   if(tick_size<=0.0)
     {
      failure_reason="INVALID_SYMBOL_TICK_SIZE";
      return false;
     }
   double risk=(g_scenarios[scenario_index].direction>0 ? entry-sl : sl-entry);
   long risk_ticks=(long)MathRound(risk/tick_size);
   if(risk<=0.0 || risk_ticks<=0)
     {
      failure_reason="INVALID_ENTRY_SL_RISK";
      return false;
     }

   for(int order_index=0;order_index<g_scenarios[scenario_index].objective_count;order_index++)
     {
      int found=-1;
      for(int i=0;i<ArraySize(g_objective_candidates);i++)
        {
         if(g_objective_candidates[i].valid &&
            g_objective_candidates[i].scenario_id==g_scenarios[scenario_index].id &&
            g_objective_candidates[i].order_index==order_index)
           {
            found=i;
            break;
           }
        }
      if(found<0)
         continue;

      V1ObjectiveCandidate candidate=g_objective_candidates[found];
      if(ObjectiveCandidateConsumedNow(candidate))
        {
         LogLine("OBJECTIVE_ELIGIBILITY_EVALUATED",TfName(candidate.tf),available_at,candidate.id,
                 StringFormat("scenario_id=%s order_index=%d result=SKIP_CONSUMED price=%.10f",
                              g_scenarios[scenario_index].id,order_index,candidate.price));
         continue;
        }

      double reward=(g_scenarios[scenario_index].direction>0 ? candidate.price-entry : entry-candidate.price);
      if(reward<=0.0)
        {
         LogLine("OBJECTIVE_ELIGIBILITY_EVALUATED",TfName(candidate.tf),available_at,candidate.id,
                 StringFormat("scenario_id=%s order_index=%d result=SKIP_NONPOSITIVE_REWARD price=%.10f entry=%.10f",
                              g_scenarios[scenario_index].id,order_index,candidate.price,entry));
         continue;
        }

      long reward_ticks=(long)MathRound(reward/tick_size);
      if(reward_ticks<=0)
        {
         LogLine("OBJECTIVE_ELIGIBILITY_EVALUATED",TfName(candidate.tf),available_at,candidate.id,
                 StringFormat("scenario_id=%s order_index=%d result=SKIP_NONPOSITIVE_REWARD_TICKS price=%.10f entry=%.10f reward_ticks=%I64d",
                              g_scenarios[scenario_index].id,order_index,candidate.price,entry,reward_ticks));
         continue;
        }

      double planned_r=(double)reward_ticks/(double)risk_ticks;
      if(reward_ticks<risk_ticks)
        {
         LogLine("OBJECTIVE_ELIGIBILITY_EVALUATED",TfName(candidate.tf),available_at,candidate.id,
                 StringFormat("scenario_id=%s order_index=%d result=INTERMEDIATE_BELOW_1R price=%.10f risk=%.10f reward=%.10f risk_ticks=%I64d reward_ticks=%I64d planned_r=%.8f",
                              g_scenarios[scenario_index].id,order_index,candidate.price,risk,reward,risk_ticks,reward_ticks,planned_r));
         continue;
        }

      g_scenarios[scenario_index].final_objective_id=candidate.id;
      g_scenarios[scenario_index].final_objective_candidate_index=found;
      g_scenarios[scenario_index].final_objective_liquidity_id=candidate.liquidity_id;
      g_scenarios[scenario_index].final_objective_price=candidate.price;
      g_scenarios[scenario_index].final_objective_planned_r=planned_r;
      g_scenarios[scenario_index].final_objective_selected_at=available_at;

      LogLine("FINAL_OBJECTIVE_SELECTED",TfName(candidate.tf),available_at,candidate.id,
              StringFormat("scenario_id=%s liquidity_id=%s order_index=%d selection=NEAREST_FIRST_R_GE_1 entry=%.10f sl=%.10f tp=%.10f risk=%.10f reward=%.10f risk_ticks=%I64d reward_ticks=%I64d planned_r=%.8f exact_1r_tick_comparison=true no_max_r_optimization=true",
                           g_scenarios[scenario_index].id,candidate.liquidity_id,order_index,entry,sl,candidate.price,risk,reward,risk_ticks,reward_ticks,planned_r));
      return true;
     }

   failure_reason="NO_R_ELIGIBLE_OBJECTIVE";
   return false;
  }

bool BuildEntryAndStopCandidateForScenario(const int scenario_index,
                                            const datetime available_at)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return false;

   if(!g_scenarios[scenario_index].valid ||
      g_scenarios[scenario_index].strategy_state!=V1_STRATEGY_WAITING_EXECUTION_GEOMETRY ||
      g_scenarios[scenario_index].selected_fvg_id=="" ||
      g_scenarios[scenario_index].selected_fvg_width<=0.0)
      return false;

   double entry=(g_scenarios[scenario_index].direction>0 ?
                 g_scenarios[scenario_index].selected_fvg_top :
                 g_scenarios[scenario_index].selected_fvg_bottom);

   double raw_sl=0.0;
   double sl_reference_price=0.0;
   double sl_reference_width=0.0;
   string geometry_failure="";

   if(InpStopLossModel==V1_SL_FVG_DISTAL_20)
     {
      sl_reference_price=(g_scenarios[scenario_index].direction>0 ?
                          g_scenarios[scenario_index].selected_fvg_bottom :
                          g_scenarios[scenario_index].selected_fvg_top);
      sl_reference_width=g_scenarios[scenario_index].selected_fvg_width;
      raw_sl=(g_scenarios[scenario_index].direction>0 ?
              sl_reference_price-0.20*sl_reference_width :
              sl_reference_price+0.20*sl_reference_width);
     }
   else if(InpStopLossModel==V1_SL_SWEEP_EXTREME)
     {
      if(g_scenarios[scenario_index].active_sweep_extreme<=0.0)
         geometry_failure="MISSING_ACCEPTED_SWEEP_EXTREME";
      else
        {
         sl_reference_price=g_scenarios[scenario_index].active_sweep_extreme;
         sl_reference_width=0.0;
         raw_sl=sl_reference_price;
        }
     }
   else if(InpStopLossModel==V1_SL_ROOT_OB_DISTAL_20)
     {
      double root_width=         g_scenarios[scenario_index].source_top-
         g_scenarios[scenario_index].source_bottom;

      if(root_width<=0.0)
         geometry_failure="INVALID_FROZEN_ROOT_WIDTH";
      else
        {
         sl_reference_price=(g_scenarios[scenario_index].direction>0 ?
                             g_scenarios[scenario_index].source_bottom :
                             g_scenarios[scenario_index].source_top);
         sl_reference_width=root_width;
         raw_sl=(g_scenarios[scenario_index].direction>0 ?
                 sl_reference_price-0.20*root_width :
                 sl_reference_price+0.20*root_width);
        }
     }
   else
      geometry_failure="UNKNOWN_STOP_LOSS_MODEL";

   if(geometry_failure!="")
     {
      MarkExecutionNoTrade(scenario_index,available_at,geometry_failure,V1_EXEC_NONE);
      return false;
     }

   double normalized_sl=(g_scenarios[scenario_index].direction>0 ?
                         NormalizePriceFloorToTick(raw_sl) :
                         NormalizePriceCeilToTick(raw_sl));

   if((g_scenarios[scenario_index].direction>0 && !(normalized_sl<entry)) ||
      (g_scenarios[scenario_index].direction<0 && !(normalized_sl>entry)))
     {
      MarkExecutionNoTrade(
         scenario_index,
         available_at,
         "INVALID_ENTRY_SL_GEOMETRY_"+StopLossModelName((int)InpStopLossModel),
         V1_EXEC_NONE);
      return false;
     }

   g_scenarios[scenario_index].strategy_entry_price=entry;
   g_scenarios[scenario_index].raw_strategy_sl=raw_sl;
   g_scenarios[scenario_index].normalized_sl=normalized_sl;
   g_scenarios[scenario_index].stop_loss_model=(int)InpStopLossModel;
   g_scenarios[scenario_index].stop_loss_reference_price=sl_reference_price;
   g_scenarios[scenario_index].stop_loss_reference_width=sl_reference_width;
   g_scenarios[scenario_index].stop_loss_merged_from_contributors=false;
   g_scenarios[scenario_index].stop_loss_contributor_scenario_id=g_scenarios[scenario_index].id;
   g_scenarios[scenario_index].stop_loss_contributor_root_id=g_scenarios[scenario_index].root_zone_id;

   LogLine("EXECUTION_GEOMETRY_CANDIDATE_READY","M1",available_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s direction=%s selected_fvg_id=%s entry=%.10f sl_model=%s individual_raw_sl=%.10f individual_normalized_sl=%.10f root_zone_id=%s stage=PRE_MERGE_NO_TP",
                        g_scenarios[scenario_index].id,
                        DirectionName(g_scenarios[scenario_index].direction),
                        g_scenarios[scenario_index].selected_fvg_id,
                        g_scenarios[scenario_index].strategy_entry_price,
                        StopLossModelName(g_scenarios[scenario_index].stop_loss_model),
                        g_scenarios[scenario_index].raw_strategy_sl,
                        g_scenarios[scenario_index].normalized_sl,
                        g_scenarios[scenario_index].root_zone_id));
   return true;
  }

void FinalizeExecutionGeometryReady(const int scenario_index,
                                    const datetime available_at)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return;

   g_scenarios[scenario_index].strategy_signal_valid=true;
   g_scenarios[scenario_index].execution_status=V1_EXEC_STRATEGY_READY;
   g_scenarios[scenario_index].terminal_reason="";
   g_execution_geometry_ready++;

   LogLine("EXECUTION_GEOMETRY_READY","M1",available_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s direction=%s selected_fvg_id=%s fvg_bottom=%.10f fvg_top=%.10f fvg_width=%.10f entry=%.10f sl_model=%s sl_reference_price=%.10f sl_reference_width=%.10f raw_sl=%.10f normalized_sl=%.10f sl_normalization=%s merged_from_contributors=%s sl_contributor_scenario_id=%s sl_contributor_root_id=%s contributor_count=%d final_objective_id=%s tp=%.10f planned_r=%.8f sizing=MINIMUM_VOLUME_PARITY strategy_signal_valid=true",
                        g_scenarios[scenario_index].id,
                        DirectionName(g_scenarios[scenario_index].direction),
                        g_scenarios[scenario_index].selected_fvg_id,
                        g_scenarios[scenario_index].selected_fvg_bottom,
                        g_scenarios[scenario_index].selected_fvg_top,
                        g_scenarios[scenario_index].selected_fvg_width,
                        g_scenarios[scenario_index].strategy_entry_price,
                        StopLossModelName(g_scenarios[scenario_index].stop_loss_model),
                        g_scenarios[scenario_index].stop_loss_reference_price,
                        g_scenarios[scenario_index].stop_loss_reference_width,
                        g_scenarios[scenario_index].raw_strategy_sl,
                        g_scenarios[scenario_index].normalized_sl,
                        g_scenarios[scenario_index].direction>0 ? "FLOOR_OUTWARD" : "CEIL_OUTWARD",
                        g_scenarios[scenario_index].stop_loss_merged_from_contributors ? "true" : "false",
                        g_scenarios[scenario_index].stop_loss_contributor_scenario_id,
                        g_scenarios[scenario_index].stop_loss_contributor_root_id,
                        g_scenarios[scenario_index].execution_contributor_count,
                        g_scenarios[scenario_index].final_objective_id,
                        g_scenarios[scenario_index].final_objective_price,
                        g_scenarios[scenario_index].final_objective_planned_r));
  }

bool IsHedgingAccount()
  {
   return ((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)==ACCOUNT_MARGIN_MODE_RETAIL_HEDGING);
  }

int ManagedOrderDirection(const ENUM_ORDER_TYPE type)
  {
   if(type==ORDER_TYPE_BUY_LIMIT || type==ORDER_TYPE_BUY_STOP || type==ORDER_TYPE_BUY_STOP_LIMIT)
      return 1;
   if(type==ORDER_TYPE_SELL_LIMIT || type==ORDER_TYPE_SELL_STOP || type==ORDER_TYPE_SELL_STOP_LIMIT)
      return -1;
   return 0;
  }

int ManagedPositionDirection(const ENUM_POSITION_TYPE type)
  {
   if(type==POSITION_TYPE_BUY)
      return 1;
   if(type==POSITION_TYPE_SELL)
      return -1;
   return 0;
  }

int CountManagedBrokerExposureDirection(const int direction)
  {
   if(direction==0)
      return 0;

   int count=0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0 ||
         OrderGetString(ORDER_SYMBOL)!=_Symbol ||
         (long)OrderGetInteger(ORDER_MAGIC)!=InpMagicNumber)
         continue;

      int order_direction=ManagedOrderDirection((ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE));
      if(order_direction==direction)
         count++;
     }

   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 ||
         PositionGetString(POSITION_SYMBOL)!=_Symbol ||
         (long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber)
         continue;

      int position_direction=ManagedPositionDirection((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE));
      if(position_direction==direction)
         count++;
     }

   return count;
  }

int ManagedBrokerExposureDirectionState()
  {
   bool have_long=(CountManagedBrokerExposureDirection(1)>0);
   bool have_short=(CountManagedBrokerExposureDirection(-1)>0);

   if(have_long && have_short)
      return 2;
   if(have_long)
      return 1;
   if(have_short)
      return -1;
   return 0;
  }

bool HasOppositeManagedExposure(const int direction)
  {
   if(direction>0)
      return (CountManagedBrokerExposureDirection(-1)>0);
   if(direction<0)
      return (CountManagedBrokerExposureDirection(1)>0);
   return true;
  }

bool FindManagedPositionByIdentifier(const ulong identifier,
                                     ulong &position_ticket,
                                     double &open_price)
  {
   position_ticket=0;
   open_price=0.0;
   if(identifier==0)
      return false;

   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 ||
         PositionGetString(POSITION_SYMBOL)!=_Symbol ||
         (long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber ||
         (ulong)PositionGetInteger(POSITION_IDENTIFIER)!=identifier)
         continue;

      position_ticket=ticket;
      open_price=PositionGetDouble(POSITION_PRICE_OPEN);
      return true;
     }

   return false;
  }

bool ScenarioOriginalPendingOrderLive(const int scenario_index)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return false;

   ulong ticket=g_scenarios[scenario_index].broker_order_ticket;
   if(ticket==0 || !OrderSelect(ticket))
      return false;

   if(OrderGetString(ORDER_SYMBOL)!=_Symbol ||
      (long)OrderGetInteger(ORDER_MAGIC)!=InpMagicNumber)
      return false;

   ENUM_ORDER_TYPE type=(ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE);
   return (type==ORDER_TYPE_BUY_LIMIT || type==ORDER_TYPE_SELL_LIMIT);
  }

bool HasUnresolvedExecutionRisk()
  {
   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(!g_scenarios[i].valid ||
         g_scenarios[i].strategy_state==V1_STRATEGY_MERGED_CONTRIBUTOR)
         continue;

      bool risky=(g_scenarios[i].execution_divergence ||
                  g_scenarios[i].execution_status==V1_EXEC_CANCEL_REJECTED);
      if(!risky)
         continue;

      if(ScenarioOriginalPendingOrderLive(i))
         return true;

      if(g_scenarios[i].broker_position_id>0)
        {
         ulong position_ticket=0;
         double open_price=0.0;
         if(FindManagedPositionByIdentifier(g_scenarios[i].broker_position_id,
                                            position_ticket,
                                            open_price))
            return true;
        }
     }

   return false;
  }

bool HasManagedAccountExposure()
  {
   return (ManagedBrokerExposureDirectionState()!=0);
  }

bool IsTesterExecutionEnvironment()
  {
   return ((bool)MQLInfoInteger(MQL_TESTER));
  }

bool IsCurrentTradeSessionOpen(const datetime when)
  {
   MqlDateTime now_parts;
   TimeToStruct(when,now_parts);
   ENUM_DAY_OF_WEEK day=(ENUM_DAY_OF_WEEK)now_parts.day_of_week;
   int now_seconds=now_parts.hour*3600+now_parts.min*60+now_parts.sec;

   for(uint index=0;index<32;index++)
     {
      datetime from=0,to=0;
      if(!SymbolInfoSessionTrade(_Symbol,day,index,from,to))
         break;
      MqlDateTime f,t;
      TimeToStruct(from,f);
      TimeToStruct(to,t);
      int fs=f.hour*3600+f.min*60+f.sec;
      int ts=t.hour*3600+t.min*60+t.sec;
      if(fs==ts)
         return true;
      if(fs<ts && now_seconds>=fs && now_seconds<ts)
         return true;
      if(fs>ts && (now_seconds>=fs || now_seconds<ts))
         return true;
     }
   return false;
  }

bool VolumeOnStep(const double volume,const double minimum,const double step)
  {
   if(step<=0.0)
      return false;
   double units=(volume-minimum)/step;
   return (MathAbs(units-MathRound(units))<=1.0e-8);
  }

bool IsAcceptableTradeRetcode(const uint retcode)
  {
   return (retcode==0 ||           retcode==TRADE_RETCODE_DONE ||
           retcode==TRADE_RETCODE_PLACED ||
           retcode==TRADE_RETCODE_DONE_PARTIAL);
  }

bool ObjectiveDeliveredAtTick(const V1ScenarioPlan &plan,const MqlTick &tick)
  {
   if(plan.final_objective_price<=0.0)
      return false;
   if(plan.direction>0)
      return tick.bid>=plan.final_objective_price;
   return tick.ask<=plan.final_objective_price;
  }

bool FinalObjectiveConsumed(const V1ScenarioPlan &plan)
  {
   if(plan.final_objective_liquidity_id=="")
      return false;

   int direct=plan.final_objective_candidate_index;
   if(direct>=0 && direct<ArraySize(g_objective_candidates) &&
      g_objective_candidates[direct].valid &&
      g_objective_candidates[direct].id==plan.final_objective_id)
     {
      return g_objective_candidates[direct].consumed;
     }

   // Defensive compatibility fallback for restored historical state.
   if(IsStrategyLiquidityConsumed(plan.final_objective_liquidity_id))
      return true;
   for(int i=0;i<ArraySize(g_objective_candidates);i++)
      if(g_objective_candidates[i].valid && g_objective_candidates[i].id==plan.final_objective_id)
         return g_objective_candidates[i].consumed;
   return false;
  }

bool BuildAndCheckPendingRequest(const int scenario_index,
                                 const MqlTick &tick,
                                 MqlTradeRequest &request,
                                 MqlTradeCheckResult &check,
                                 string &failure_reason)
  {
   ZeroMemory(request);
   ZeroMemory(check);
   failure_reason="";

   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
     { failure_reason="SCENARIO_INDEX_INVALID"; return false; }

   if(!g_scenarios[scenario_index].strategy_signal_valid)
     { failure_reason="STRATEGY_SIGNAL_NOT_VALID"; return false; }

   if(!IsHedgingAccount())
     { failure_reason="HEDGING_ACCOUNT_REQUIRED_FOR_INDEPENDENT_SCENARIO_POSITIONS"; return false; }

   if(!IsTesterExecutionEnvironment())
     { failure_reason="LIVE_EXECUTION_HARD_BLOCKED"; return false; }

   datetime current_m1_open=iTime(_Symbol,PERIOD_M1,0);
   if(current_m1_open<=0 ||
      current_m1_open!=g_scenarios[scenario_index].scenario_choch_bar_open+PeriodSeconds(PERIOD_M1))
     { failure_reason="DELAYED_SIGNAL_NOT_CURRENT_DECISION_CYCLE"; return false; }

   if(!(bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) ||
      !(bool)MQLInfoInteger(MQL_TRADE_ALLOWED) ||
      !(bool)AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) ||
      !(bool)AccountInfoInteger(ACCOUNT_TRADE_EXPERT))
     { failure_reason="ALGO_OR_ACCOUNT_TRADING_NOT_ALLOWED"; return false; }

   long trade_mode=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_MODE);
   if(trade_mode==SYMBOL_TRADE_MODE_DISABLED || trade_mode==SYMBOL_TRADE_MODE_CLOSEONLY)
     { failure_reason="SYMBOL_TRADE_MODE_DISALLOWS_ENTRY"; return false; }
   if(g_scenarios[scenario_index].direction>0 && trade_mode==SYMBOL_TRADE_MODE_SHORTONLY)
     { failure_reason="SYMBOL_SHORT_ONLY"; return false; }
   if(g_scenarios[scenario_index].direction<0 && trade_mode==SYMBOL_TRADE_MODE_LONGONLY)
     { failure_reason="SYMBOL_LONG_ONLY"; return false; }

   long order_mode=SymbolInfoInteger(_Symbol,SYMBOL_ORDER_MODE);
   if((order_mode & SYMBOL_ORDER_LIMIT)==0)
     { failure_reason="LIMIT_ORDER_NOT_SUPPORTED"; return false; }
   if((order_mode & SYMBOL_ORDER_SL)==0 || (order_mode & SYMBOL_ORDER_TP)==0)
     { failure_reason="ATTACHED_SL_TP_NOT_SUPPORTED"; return false; }

   long expiration_mode=SymbolInfoInteger(_Symbol,SYMBOL_EXPIRATION_MODE);
   long gtc_mode=SymbolInfoInteger(_Symbol,SYMBOL_ORDER_GTC_MODE);
   if((expiration_mode & SYMBOL_EXPIRATION_GTC)==0 || gtc_mode!=SYMBOL_ORDERS_GTC)
     { failure_reason="PERSISTENT_GTC_NOT_SUPPORTED"; return false; }

   if(!IsCurrentTradeSessionOpen((datetime)tick.time))
     { failure_reason="TRADE_SESSION_CLOSED_AT_SIGNAL"; return false; }

   if(!IsPriceOnTickGrid(g_scenarios[scenario_index].strategy_entry_price) ||
      !IsPriceOnTickGrid(g_scenarios[scenario_index].normalized_sl) ||
      !IsPriceOnTickGrid(g_scenarios[scenario_index].final_objective_price))
     { failure_reason="PRICE_NOT_ON_TICK_GRID"; return false; }

   double point=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   long stops_points=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance=MathMax(0.0,(double)stops_points*point);
   double eps=LiquidityTickSize()*1.0e-6;

   if(g_scenarios[scenario_index].direction>0)
     {
      if(tick.ask-g_scenarios[scenario_index].strategy_entry_price+eps<min_distance)
        { failure_reason="BUY_LIMIT_STOPSLEVEL_ENTRY"; return false; }
      if(g_scenarios[scenario_index].strategy_entry_price-g_scenarios[scenario_index].normalized_sl+eps<min_distance)
        { failure_reason="LONG_SL_STOPSLEVEL"; return false; }
      if(g_scenarios[scenario_index].final_objective_price-g_scenarios[scenario_index].strategy_entry_price+eps<min_distance)
        { failure_reason="LONG_TP_STOPSLEVEL"; return false; }
     }
   else
     {
      if(g_scenarios[scenario_index].strategy_entry_price-tick.bid+eps<min_distance)
        { failure_reason="SELL_LIMIT_STOPSLEVEL_ENTRY"; return false; }
      if(g_scenarios[scenario_index].normalized_sl-g_scenarios[scenario_index].strategy_entry_price+eps<min_distance)
        { failure_reason="SHORT_SL_STOPSLEVEL"; return false; }
      if(g_scenarios[scenario_index].strategy_entry_price-g_scenarios[scenario_index].final_objective_price+eps<min_distance)
        { failure_reason="SHORT_TP_STOPSLEVEL"; return false; }
     }

   double volume_min=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double volume_max=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double volume_step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(volume_min<=0.0 || volume_max<volume_min ||
      !VolumeOnStep(volume_min,volume_min,volume_step))
     { failure_reason="MINIMUM_VOLUME_PARITY_INVALID"; return false; }
   g_scenarios[scenario_index].order_volume=volume_min;

   request.action=TRADE_ACTION_PENDING;
   request.magic=(ulong)InpMagicNumber;
   request.symbol=_Symbol;
   request.volume=g_scenarios[scenario_index].order_volume;
   request.price=g_scenarios[scenario_index].strategy_entry_price;
   request.sl=g_scenarios[scenario_index].normalized_sl;
   request.tp=g_scenarios[scenario_index].final_objective_price;
   request.type=(g_scenarios[scenario_index].direction>0 ? ORDER_TYPE_BUY_LIMIT : ORDER_TYPE_SELL_LIMIT);
   request.type_filling=ORDER_FILLING_RETURN;
   request.type_time=ORDER_TIME_GTC;
   request.expiration=0;
   request.comment=StringFormat("MV1-%d-%s",scenario_index,g_scenarios[scenario_index].direction>0 ? "L" : "S");

   ResetLastError();
   if(!OrderCheck(request,check))
     {
      failure_reason=StringFormat("ORDERCHECK_CALL_FAILED_%d",GetLastError());
      return false;
     }
   if(!IsAcceptableTradeRetcode(check.retcode))
     {
      failure_reason=StringFormat("ORDERCHECK_RETCODE_%u_%s",check.retcode,check.comment);
      return false;
     }
   return true;
  }

bool SubmitPendingForScenario(const int scenario_index,const datetime available_at)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return false;

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
     {
      g_execution_infeasible++;
      MarkExecutionNoTrade(scenario_index,available_at,"NO_CURRENT_TICK_FOR_PREFLIGHT",V1_EXEC_EXECUTION_INFEASIBLE);
      return false;
     }

   if(ObjectiveDeliveredAtTick(g_scenarios[scenario_index],tick) || FinalObjectiveConsumed(g_scenarios[scenario_index]))
     {
      g_scenarios[scenario_index].strategy_state=V1_STRATEGY_CANCELED;
      g_scenarios[scenario_index].canceled_at=available_at;
      g_scenarios[scenario_index].cancel_reason="CANCELED_OBJECTIVE_DELIVERED";
      g_scenarios[scenario_index].strategy_cancel_at=available_at;
      g_scenarios[scenario_index].strategy_cancel_reason="CANCELED_OBJECTIVE_DELIVERED";
      ReleaseRootScenarioOwner(g_scenarios[scenario_index].root_zone_id,g_scenarios[scenario_index].id);
      LogScenarioCanceled(g_scenarios[scenario_index],available_at,"CANCELED_OBJECTIVE_DELIVERED");
      g_scenarios_canceled++;
      return false;
     }

   MqlTradeRequest request;
   MqlTradeCheckResult check;
   string failure_reason="";
   if(!BuildAndCheckPendingRequest(scenario_index,tick,request,check,failure_reason))
     {
      g_execution_infeasible++;
      MarkExecutionNoTrade(scenario_index,available_at,failure_reason,V1_EXEC_EXECUTION_INFEASIBLE);
      LogLine("EXECUTION_PREFLIGHT_FAILED","M1",available_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s reason=%s bid=%.10f ask=%.10f entry=%.10f sl=%.10f tp=%.10f stops_level=%I64d freeze_level=%I64d strategy_geometry_unchanged=true",
                           g_scenarios[scenario_index].id,failure_reason,tick.bid,tick.ask,g_scenarios[scenario_index].strategy_entry_price,g_scenarios[scenario_index].normalized_sl,g_scenarios[scenario_index].final_objective_price,
                           SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL),
                           SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL)));
      return false;
     }

   g_scenarios[scenario_index].execution_status=V1_EXEC_PREFLIGHT_OK;
   LogLine("EXECUTION_PREFLIGHT_OK","M1",available_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s bid=%.10f ask=%.10f entry=%.10f sl=%.10f tp=%.10f volume=%.8f tick_size=%.10f point=%.10f stops_level=%I64d freeze_level=%I64d order_time=GTC filling=RETURN",
                        g_scenarios[scenario_index].id,tick.bid,tick.ask,g_scenarios[scenario_index].strategy_entry_price,g_scenarios[scenario_index].normalized_sl,g_scenarios[scenario_index].final_objective_price,g_scenarios[scenario_index].order_volume,
                        LiquidityTickSize(),SymbolInfoDouble(_Symbol,SYMBOL_POINT),
                        SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL),
                        SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL)));

   MqlTradeResult result;
   ZeroMemory(result);
   ResetLastError();
   bool call_ok=OrderSend(request,result);
   if(!call_ok || !IsAcceptableTradeRetcode(result.retcode) || result.order==0)
     {
      g_order_rejected++;
      g_scenarios[scenario_index].request_id=result.request_id;
      MarkExecutionNoTrade(scenario_index,available_at,
                           StringFormat("ORDER_REJECTED_%u_%s",result.retcode,result.comment),
                           V1_EXEC_REJECTED);
      LogLine("ORDER_REJECTED","M1",available_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s call_ok=%s retcode=%u comment=%s request_id=%u order=%I64u deal=%I64u last_error=%d retry=false",
                           g_scenarios[scenario_index].id,call_ok ? "true" : "false",result.retcode,result.comment,result.request_id,result.order,result.deal,GetLastError()));
      return false;
     }

   g_scenarios[scenario_index].strategy_state=V1_STRATEGY_PENDING;
   g_scenarios[scenario_index].execution_status=V1_EXEC_PENDING_ACCEPTED;
   g_scenarios[scenario_index].pending_submitted_at=available_at;
   g_scenarios[scenario_index].request_id=result.request_id;
   g_scenarios[scenario_index].broker_order_ticket=result.order;
   D135AddUniqueIndex(g_active_execution_scenario_indices,scenario_index);
   g_orders_accepted++;

   LogLine("PENDING_ORDER_ACCEPTED","M1",available_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s order_ticket=%I64u request_id=%u direction=%s entry=%.10f sl_model=%s sl=%.10f tp=%.10f volume=%.8f contributor_count=%d merged=%s contributor_root_ids=%s order_time=GTC filling=RETURN strategy_state=PENDING",
                        g_scenarios[scenario_index].id,
                        result.order,
                        result.request_id,
                        DirectionName(g_scenarios[scenario_index].direction),
                        g_scenarios[scenario_index].strategy_entry_price,
                        StopLossModelName(g_scenarios[scenario_index].stop_loss_model),
                        g_scenarios[scenario_index].normalized_sl,
                        g_scenarios[scenario_index].final_objective_price,
                        g_scenarios[scenario_index].order_volume,
                        g_scenarios[scenario_index].execution_contributor_count,
                        g_scenarios[scenario_index].execution_opportunity_merged ? "true" : "false",
                        g_scenarios[scenario_index].execution_contributor_root_ids));
   return true;
  }

long D133PriceTickIndex(const double price)
  {
   double tick=LiquidityTickSize();
   if(tick<=0.0)
      return 0;
   return (long)MathRound(price/tick);
  }

bool D133SameEntryScenarioIdentity(const int a_index,const int b_index)
  {
   if(a_index<0 || b_index<0 ||
      a_index>=ArraySize(g_scenarios) ||
      b_index>=ArraySize(g_scenarios))
      return false;

   return (
      g_scenarios[a_index].direction==g_scenarios[b_index].direction &&
      g_scenarios[a_index].selected_fvg_id==g_scenarios[b_index].selected_fvg_id &&
      D133PriceTickIndex(g_scenarios[a_index].strategy_entry_price)==
         D133PriceTickIndex(g_scenarios[b_index].strategy_entry_price));
  }

bool D133AllCandidatesSameEntryScenario()
  {
   int count=ArraySize(g_execution_candidates);
   if(count<=1)
      return true;

   int master=g_execution_candidates[0].scenario_index;
   for(int i=1;i<count;i++)
      if(!D133SameEntryScenarioIdentity(master,g_execution_candidates[i].scenario_index))
         return false;

   return true;
  }

bool D133CurrentGroupContainsScenarioId(const string scenario_id)
  {
   for(int i=0;i<ArraySize(g_execution_candidates);i++)
      if(g_execution_candidates[i].valid &&
         g_execution_candidates[i].scenario_id==scenario_id)
         return true;
   return false;
  }

bool D133ScenarioHasLiveObjectiveAtPriceTick(const string scenario_id,
                                             const long price_tick,
                                             int &representative_index)
  {
   representative_index=-1;
   string representative_liquidity_id="";

   for(int i=0;i<ArraySize(g_objective_candidates);i++)
     {      if(!g_objective_candidates[i].valid ||
         g_objective_candidates[i].scenario_id!=scenario_id ||
         D133PriceTickIndex(g_objective_candidates[i].price)!=price_tick ||
         ObjectiveCandidateConsumedNow(g_objective_candidates[i]))
         continue;

      if(representative_index<0 ||
         StringCompare(g_objective_candidates[i].liquidity_id,
                       representative_liquidity_id,true)<0)
        {
         representative_index=i;
         representative_liquidity_id=g_objective_candidates[i].liquidity_id;
        }
     }

   return (representative_index>=0);
  }

bool D133PriceIsCommonToAllContributors(const long price_tick)
  {
   for(int i=0;i<ArraySize(g_execution_candidates);i++)
     {
      int idx=-1;
      if(!D133ScenarioHasLiveObjectiveAtPriceTick(
            g_execution_candidates[i].scenario_id,
            price_tick,
            idx))
         return false;
     }
   return true;
  }

bool D133SelectCommonFinalObjectiveForGroup(const int master_index,
                                            const datetime available_at,
                                            string &failure_reason)
  {
   failure_reason="";
   if(master_index<0 || master_index>=ArraySize(g_scenarios))
     {
      failure_reason="SCENARIO_INDEX_INVALID";
      return false;
     }

   double entry=g_scenarios[master_index].strategy_entry_price;
   double sl=g_scenarios[master_index].normalized_sl;
   double tick_size=LiquidityTickSize();
   if(tick_size<=0.0)
     {
      failure_reason="INVALID_SYMBOL_TICK_SIZE";
      return false;
     }

   double risk=(g_scenarios[master_index].direction>0 ? entry-sl : sl-entry);
   long risk_ticks=(long)MathRound(risk/tick_size);
   if(risk<=0.0 || risk_ticks<=0)
     {
      failure_reason="INVALID_ENTRY_SL_RISK";
      return false;
     }

   bool found=false;
   long best_reward_ticks=0;
   long best_price_tick=0;

   // The merged scenario may use only an objective PRICE that was frozen in
   // every contributing Root plan. This is the intersection of precommitted
   // objective families, not a union discovered after Entry.
   for(int i=0;i<ArraySize(g_objective_candidates);i++)
     {
      if(!g_objective_candidates[i].valid ||
         g_objective_candidates[i].scenario_id!=g_scenarios[master_index].id)
         continue;

      long price_tick=D133PriceTickIndex(g_objective_candidates[i].price);
      if(!D133PriceIsCommonToAllContributors(price_tick))
         continue;

      double price=g_objective_candidates[i].price;
      double reward=(g_scenarios[master_index].direction>0 ? price-entry : entry-price);
      long reward_ticks=(long)MathRound(reward/tick_size);
      if(reward<=0.0 || reward_ticks<=0 || reward_ticks<risk_ticks)
         continue;

      if(!found || reward_ticks<best_reward_ticks ||
         (reward_ticks==best_reward_ticks && price_tick<best_price_tick))
        {
         found=true;
         best_reward_ticks=reward_ticks;
         best_price_tick=price_tick;
        }
     }

   if(!found)
     {
      failure_reason="NO_COMMON_R_ELIGIBLE_OBJECTIVE";
      return false;
     }

   int representative=-1;
   string representative_id="";
   for(int i=0;i<ArraySize(g_objective_candidates);i++)
     {
      if(!g_objective_candidates[i].valid ||
         !D133CurrentGroupContainsScenarioId(g_objective_candidates[i].scenario_id) ||
         D133PriceTickIndex(g_objective_candidates[i].price)!=best_price_tick ||
         ObjectiveCandidateConsumedNow(g_objective_candidates[i]))
         continue;

      if(representative<0 ||
         StringCompare(g_objective_candidates[i].liquidity_id,representative_id,true)<0)
        {
         representative=i;
         representative_id=g_objective_candidates[i].liquidity_id;
        }
     }

   if(representative<0)
     {
      failure_reason="COMMON_OBJECTIVE_REPRESENTATIVE_MISSING";
      return false;
     }

   V1ObjectiveCandidate candidate=g_objective_candidates[representative];
   double reward=(g_scenarios[master_index].direction>0 ? candidate.price-entry : entry-candidate.price);
   double planned_r=(double)best_reward_ticks/(double)risk_ticks;

   g_scenarios[master_index].final_objective_id=candidate.id;
   g_scenarios[master_index].final_objective_candidate_index=representative;
   g_scenarios[master_index].final_objective_liquidity_id=candidate.liquidity_id;
   g_scenarios[master_index].final_objective_price=candidate.price;
   g_scenarios[master_index].final_objective_planned_r=planned_r;
   g_scenarios[master_index].final_objective_selected_at=available_at;

   LogLine("FINAL_OBJECTIVE_SELECTED",TfName(candidate.tf),available_at,candidate.id,
           StringFormat("scenario_id=%s liquidity_id=%s selection=MERGED_COMMON_FROZEN_PRICE_NEAREST_R_GE_1 contributor_count=%d entry=%.10f sl=%.10f tp=%.10f risk=%.10f reward=%.10f risk_ticks=%I64d reward_ticks=%I64d planned_r=%.8f common_to_all_contributors=true objective_union=false no_root_preference=true",
                        g_scenarios[master_index].id,
                        candidate.liquidity_id,
                        ArraySize(g_execution_candidates),
                        entry,sl,candidate.price,risk,reward,risk_ticks,best_reward_ticks,planned_r));
   return true;
  }

bool D133ApplyMergedStopToMaster(const int master_index,
                                 const datetime available_at)
  {
   if(master_index<0 || master_index>=ArraySize(g_scenarios) ||
      ArraySize(g_execution_candidates)<=1)
      return false;

   int chosen_index=master_index;
   double chosen_sl=g_scenarios[master_index].normalized_sl;
   string sl_list="";

   for(int i=0;i<ArraySize(g_execution_candidates);i++)
     {
      int idx=g_execution_candidates[i].scenario_index;
      if(idx<0 || idx>=ArraySize(g_scenarios))
         return false;

      if(sl_list!="")
         sl_list+="|";
      sl_list+=StringFormat("%s@%s@%.10f",
                            g_scenarios[idx].id,
                            g_scenarios[idx].root_zone_id,
                            g_scenarios[idx].normalized_sl);

      if((g_scenarios[master_index].direction>0 && g_scenarios[idx].normalized_sl<chosen_sl) ||
         (g_scenarios[master_index].direction<0 && g_scenarios[idx].normalized_sl>chosen_sl))
        {
         chosen_index=idx;
         chosen_sl=g_scenarios[idx].normalized_sl;
        }
     }

   g_scenarios[master_index].raw_strategy_sl=g_scenarios[chosen_index].raw_strategy_sl;
   g_scenarios[master_index].normalized_sl=g_scenarios[chosen_index].normalized_sl;
   g_scenarios[master_index].stop_loss_model=g_scenarios[chosen_index].stop_loss_model;
   g_scenarios[master_index].stop_loss_reference_price=g_scenarios[chosen_index].stop_loss_reference_price;
   g_scenarios[master_index].stop_loss_reference_width=g_scenarios[chosen_index].stop_loss_reference_width;
   g_scenarios[master_index].stop_loss_merged_from_contributors=true;
   g_scenarios[master_index].stop_loss_contributor_scenario_id=g_scenarios[chosen_index].id;
   g_scenarios[master_index].stop_loss_contributor_root_id=g_scenarios[chosen_index].root_zone_id;

   LogLine("MERGED_STOP_SELECTED","M1",available_at,g_scenarios[master_index].id,
           StringFormat("master_scenario_id=%s direction=%s sl_model=%s contributor_count=%d selection=OUTERMOST_CONTRIBUTOR_INVALIDATION merged_sl=%.10f sl_contributor_scenario_id=%s sl_contributor_root_id=%s contributor_sl_list=%s",
                        g_scenarios[master_index].id,
                        DirectionName(g_scenarios[master_index].direction),
                        StopLossModelName(g_scenarios[master_index].stop_loss_model),
                        ArraySize(g_execution_candidates),
                        g_scenarios[master_index].normalized_sl,
                        g_scenarios[master_index].stop_loss_contributor_scenario_id,
                        g_scenarios[master_index].stop_loss_contributor_root_id,
                        sl_list));
   return true;
  }

bool D133DelimitedListContains(const string list,const string value)
  {
   if(list=="" || value=="")
      return false;

   return (StringFind("|"+list+"|","|"+value+"|")>=0);
  }

bool D133ContributorAuthorityAlive(const int scenario_index)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return false;

   int root_index=FindActiveSourceById(g_scenarios[scenario_index].root_zone_id);
   if(root_index<0 || g_sources[root_index].kind!=V1_SOURCE_ROOT)
      return false;

   if(g_scenarios[scenario_index].scope==V1_SCOPE_EXTERNAL_CONTINUATION)
     {
      if(g_scenarios[scenario_index].active_map_tf==PERIOD_H1)
         return (g_structure[1].owner_id==g_scenarios[scenario_index].owner_id &&
                 IsMatureDirectionalTrend(g_structure[1].trend));

      if(g_scenarios[scenario_index].active_map_tf==PERIOD_M30)
         return (g_structure[2].owner_id==g_scenarios[scenario_index].owner_id &&
                 IsMatureDirectionalTrend(g_structure[2].trend));

      return false;
     }

   if(g_scenarios[scenario_index].scope==V1_SCOPE_EXTERNAL_REVERSAL)
     {
      if(g_map.last_permission_closed_at>g_scenarios[scenario_index].frozen_at &&
         g_map.last_permission_close_reason=="TERMINATED_BY_CONTINUATION" &&
         g_map.last_closed_permission_reference_id==
            g_scenarios[scenario_index].permission_reference_id &&
         g_map.last_closed_permission_opened_at==
            g_scenarios[scenario_index].permission_opened_at)
         return false;

      return true;
     }

   return false;
  }

int D133CountAliveContributors(const int master_index,string &alive_root_ids)
  {
   alive_root_ids="";
   if(master_index<0 || master_index>=ArraySize(g_scenarios))
      return 0;

   int alive=0;

   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(!g_scenarios[i].valid ||
         !D133DelimitedListContains(
            g_scenarios[master_index].execution_contributor_scenario_ids,
            g_scenarios[i].id))
         continue;

      if(!D133ContributorAuthorityAlive(i))
         continue;

      if(alive_root_ids!="")
         alive_root_ids+="|";
      alive_root_ids+=g_scenarios[i].root_zone_id;
      alive++;
     }

   return alive;
  }

void D133TerminateMergedSecondaries(const int master_index,
                                    const datetime available_at,
                                    const string reason)
  {
   if(master_index<0 || master_index>=ArraySize(g_scenarios))
      return;

   string master_id=g_scenarios[master_index].id;

   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(i==master_index ||
         !g_scenarios[i].valid ||
         g_scenarios[i].execution_master_scenario_id!=master_id ||
         g_scenarios[i].strategy_state!=V1_STRATEGY_MERGED_CONTRIBUTOR)
         continue;

      g_scenarios[i].strategy_state=V1_STRATEGY_CANCELED;
      g_scenarios[i].canceled_at=available_at;
      g_scenarios[i].cancel_reason=reason;
      ReleaseRootScenarioOwner(g_scenarios[i].root_zone_id,g_scenarios[i].id);
      g_scenarios_canceled++;

      LogLine("EXECUTION_CONTRIBUTOR_TERMINATED","M1",available_at,g_scenarios[i].id,
              StringFormat("master_scenario_id=%s contributor_scenario_id=%s contributor_root_id=%s reason=%s",
                           master_id,
                           g_scenarios[i].id,
                           g_scenarios[i].root_zone_id,
                           reason));
     }  }

void D133FreezeSameEntryContributorMerge(const datetime available_at)
  {
   int count=ArraySize(g_execution_candidates);
   if(count<=1)
      return;

   int master_index=g_execution_candidates[0].scenario_index;
   string master_id=g_scenarios[master_index].id;
   string scenario_ids="";
   string root_ids="";

   for(int i=0;i<count;i++)
     {
      int idx=g_execution_candidates[i].scenario_index;

      if(scenario_ids!="")
         scenario_ids+="|";
      if(root_ids!="")
         root_ids+="|";

      scenario_ids+=g_scenarios[idx].id;
      root_ids+=g_scenarios[idx].root_zone_id;
     }

   g_scenarios[master_index].execution_opportunity_merged=true;
   g_scenarios[master_index].execution_master_scenario_id=master_id;
   g_scenarios[master_index].execution_contributor_scenario_ids=scenario_ids;
   g_scenarios[master_index].execution_contributor_root_ids=root_ids;
   g_scenarios[master_index].execution_contributor_count=count;

   for(int i=1;i<count;i++)
     {
      int idx=g_execution_candidates[i].scenario_index;

      g_scenarios[idx].execution_opportunity_merged=true;
      g_scenarios[idx].execution_master_scenario_id=master_id;
      g_scenarios[idx].execution_contributor_scenario_ids=scenario_ids;
      g_scenarios[idx].execution_contributor_root_ids=root_ids;
      g_scenarios[idx].execution_contributor_count=count;
      g_scenarios[idx].strategy_state=V1_STRATEGY_MERGED_CONTRIBUTOR;

      LogLine("EXECUTION_CONTRIBUTOR_MERGED","M1",available_at,g_scenarios[idx].id,
              StringFormat("master_scenario_id=%s contributor_scenario_id=%s contributor_root_id=%s selected_fvg_id=%s entry=%.10f individual_sl=%.10f merged_sl=%.10f merge_basis=SAME_DIRECTION_SELECTED_FVG_ENTRY_TICK",
                           master_id,
                           g_scenarios[idx].id,
                           g_scenarios[idx].root_zone_id,
                           g_scenarios[idx].selected_fvg_id,
                           g_scenarios[idx].strategy_entry_price,
                           g_scenarios[idx].normalized_sl,
                           g_scenarios[master_index].normalized_sl));

      g_execution_contributors_merged++;
     }

   g_execution_opportunities_merged++;

   LogLine("EXECUTION_OPPORTUNITY_MERGED","M1",available_at,master_id,
           StringFormat("master_scenario_id=%s contributor_count=%d contributor_scenario_ids=%s contributor_root_ids=%s direction=%s selected_fvg_id=%s entry=%.10f sl_model=%s merged_sl=%.10f merge_basis=SAME_DIRECTION_SELECTED_FVG_ENTRY_TICK sl_equality_required=false tp_equality_required=false arbitrary_root_selection=false master_is_ledger_holder_only=true",
                        master_id,
                        count,
                        scenario_ids,
                        root_ids,
                        DirectionName(g_scenarios[master_index].direction),
                        g_scenarios[master_index].selected_fvg_id,
                        g_scenarios[master_index].strategy_entry_price,
                        StopLossModelName(g_scenarios[master_index].stop_loss_model),
                        g_scenarios[master_index].normalized_sl));
  }

void D133TerminateMergedSecondariesNoTrade(const int master_index,
                                           const datetime available_at,
                                           const string reason)
  {
   if(master_index<0 || master_index>=ArraySize(g_scenarios))
      return;

   string master_id=g_scenarios[master_index].id;
   for(int i=0;i<ArraySize(g_scenarios);i++)
     {
      if(i==master_index ||
         !g_scenarios[i].valid ||
         g_scenarios[i].execution_master_scenario_id!=master_id ||
         g_scenarios[i].strategy_state!=V1_STRATEGY_MERGED_CONTRIBUTOR)
         continue;

      g_scenarios[i].strategy_state=V1_STRATEGY_NO_TRADE;
      g_scenarios[i].no_trade_at=available_at;
      g_scenarios[i].no_trade_reason=reason;
      g_scenarios[i].terminal_reason=reason;
      ReleaseRootScenarioOwner(g_scenarios[i].root_zone_id,g_scenarios[i].id);

      LogLine("EXECUTION_CONTRIBUTOR_TERMINATED","M1",available_at,g_scenarios[i].id,
              StringFormat("master_scenario_id=%s contributor_scenario_id=%s contributor_root_id=%s reason=%s terminal_state=NO_TRADE scenario_level_no_trade_counted_on_master_only=true",
                           master_id,
                           g_scenarios[i].id,
                           g_scenarios[i].root_zone_id,
                           reason));
     }
  }

int D134FinalizeCurrentExecutionCandidateGroup(const datetime available_at)
  {
   int count=ArraySize(g_execution_candidates);
   if(count<=0)
      return -1;

   int master_index=g_execution_candidates[0].scenario_index;
   bool merged=(count>1);

   if(merged)
     {
      if(!D133ApplyMergedStopToMaster(master_index,available_at))
        {
         for(int i=0;i<count;i++)
            MarkExecutionNoTrade(g_execution_candidates[i].scenario_index,
                                 available_at,
                                 "MERGED_STOP_SELECTION_FAILED",
                                 V1_EXEC_NONE);
         return -1;
        }

      D133FreezeSameEntryContributorMerge(available_at);

      string objective_failure="";
      if(!D133SelectCommonFinalObjectiveForGroup(master_index,available_at,objective_failure))
        {
         if(objective_failure=="NO_COMMON_R_ELIGIBLE_OBJECTIVE")
            g_no_r_eligible_objective++;
         MarkExecutionNoTrade(master_index,available_at,objective_failure,V1_EXEC_NONE);
         D133TerminateMergedSecondariesNoTrade(master_index,available_at,objective_failure);
         return -1;
        }
     }
   else
     {
      string objective_failure="";
      if(!SelectFinalObjectiveForScenario(master_index,available_at,objective_failure))
        {
         if(objective_failure=="NO_R_ELIGIBLE_OBJECTIVE")
            g_no_r_eligible_objective++;
         MarkExecutionNoTrade(master_index,available_at,objective_failure,V1_EXEC_NONE);
         return -1;
        }
     }

   FinalizeExecutionGeometryReady(master_index,available_at);
   return master_index;
  }

void D134BlockReadyOpportunity(const int master_index,
                               const datetime available_at,
                               const string reason,
                               const int execution_status)
  {
   if(master_index<0 || master_index>=ArraySize(g_scenarios))
      return;

   int contributor_count=MathMax(1,g_scenarios[master_index].execution_contributor_count);

   MarkExecutionNoTrade(master_index,available_at,reason,execution_status);
   if(g_scenarios[master_index].execution_opportunity_merged)
      D133TerminateMergedSecondariesNoTrade(master_index,available_at,reason);

   LogLine("EXECUTION_AUTHORIZATION_BLOCKED","M1",available_at,g_scenarios[master_index].id,
           StringFormat("reason=%s direction=%s entry=%.10f contributor_count=%d same_direction_addons_allowed=true opposite_direction_coexistence=false delayed_submission=false",
                        reason,
                        DirectionName(g_scenarios[master_index].direction),
                        g_scenarios[master_index].strategy_entry_price,
                        contributor_count));
  }

void D134SubmitReadyOpportunity(const int master_index,
                                const datetime available_at)
  {
   if(master_index<0 || master_index>=ArraySize(g_scenarios))
      return;

   if(HasUnresolvedExecutionRisk())
     {
      D134BlockReadyOpportunity(master_index,
                                available_at,
                                "EXECUTION_DIVERGENCE_LOCK",
                                V1_EXEC_NONE);
      return;
     }

   if(HasOppositeManagedExposure(g_scenarios[master_index].direction))
     {
      g_exposure_blocked++;
      g_opposite_direction_exposure_blocked++;
      D134BlockReadyOpportunity(master_index,
                                available_at,
                                "OPPOSITE_DIRECTION_EXPOSURE_CONFLICT",
                                V1_EXEC_NONE);
      return;
     }

   int same_direction_exposure=
      CountManagedBrokerExposureDirection(g_scenarios[master_index].direction);

   if(same_direction_exposure>0)
     {
      g_same_direction_addon_authorized++;
      LogLine("SAME_DIRECTION_ADDON_AUTHORIZED","M1",available_at,g_scenarios[master_index].id,
              StringFormat("scenario_id=%s direction=%s entry=%.10f existing_same_direction_exposure_count=%d contributor_count=%d same_entry_contributor_merge=%s account_mode=HEDGING",
                           g_scenarios[master_index].id,
                           DirectionName(g_scenarios[master_index].direction),
                           g_scenarios[master_index].strategy_entry_price,
                           same_direction_exposure,
                           MathMax(1,g_scenarios[master_index].execution_contributor_count),
                           g_scenarios[master_index].execution_opportunity_merged ? "true" : "false"));
     }

   bool submitted=SubmitPendingForScenario(master_index,available_at);
   if(!submitted && g_scenarios[master_index].execution_opportunity_merged)
     {
      string terminal_reason=g_scenarios[master_index].terminal_reason;
      if(terminal_reason=="")
         terminal_reason=g_scenarios[master_index].cancel_reason;
      if(terminal_reason=="")
         terminal_reason="MERGED_OPPORTUNITY_NOT_SUBMITTED";

      D133TerminateMergedSecondariesNoTrade(
         master_index,
         available_at,
         terminal_reason);
     }
  }

void ProcessIntegratedExecutionAuthorizationEpoch(const datetime available_at)
  {
   ArrayResize(g_execution_candidates,0);

   // Stage 1: D-135 iterates only scenarios that reached execution geometry
   // in this M1 decision cycle. Final TP remains deferred until contributor merge.
   for(int p=0;p<ArraySize(g_waiting_execution_geometry_indices);p++)
     {
      int i=g_waiting_execution_geometry_indices[p];
      if(i<0 || i>=ArraySize(g_scenarios) ||
         !g_scenarios[i].valid ||
         g_scenarios[i].strategy_state!=V1_STRATEGY_WAITING_EXECUTION_GEOMETRY ||
         g_scenarios[i].fvg_frozen_at!=available_at)
         continue;
      if(!BuildEntryAndStopCandidateForScenario(i,available_at))
         continue;

      int n=ArraySize(g_execution_candidates);
      if(ArrayResize(g_execution_candidates,n+1,16)<0)
         continue;
      g_execution_candidates[n].valid=true;
      g_execution_candidates[n].scenario_index=i;
      g_execution_candidates[n].scenario_id=g_scenarios[i].id;
      g_execution_candidates[n].direction=g_scenarios[i].direction;
      g_execution_candidates[n].authorization_at=available_at;
     }
   ArrayResize(g_waiting_execution_geometry_indices,0);

   int total=ArraySize(g_execution_candidates);
   if(total<=0)
      return;

   // Preserve the complete epoch before reusing g_execution_candidates as a
   // temporary same-entry contributor group.
   V1ExecutionCandidate epoch_candidates[];
   if(ArrayResize(epoch_candidates,total)<0)
      return;

   for(int i=0;i<total;i++)
     {
      epoch_candidates[i].valid=g_execution_candidates[i].valid;
      epoch_candidates[i].scenario_index=g_execution_candidates[i].scenario_index;
      epoch_candidates[i].scenario_id=g_execution_candidates[i].scenario_id;
      epoch_candidates[i].direction=g_execution_candidates[i].direction;
      epoch_candidates[i].authorization_at=g_execution_candidates[i].authorization_at;
     }

   bool processed[];
   if(ArrayResize(processed,total)<0)
      return;
   for(int p=0;p<total;p++)
      processed[p]=false;

   // Stage 2: finalize each distinct Entry opportunity independently. Only
   // fully finalized opportunities participate in direction arbitration.
   int ready_master_indices[];
   ArrayResize(ready_master_indices,0);

   for(int i=0;i<total;i++)
     {
      if(processed[i] || !epoch_candidates[i].valid)
         continue;

      ArrayResize(g_execution_candidates,0);

      for(int j=i;j<total;j++)
        {
         if(processed[j] || !epoch_candidates[j].valid)
            continue;
         if(!D133SameEntryScenarioIdentity(
               epoch_candidates[i].scenario_index,
               epoch_candidates[j].scenario_index))
            continue;

         int n=ArraySize(g_execution_candidates);
         if(ArrayResize(g_execution_candidates,n+1,8)<0)
            continue;

         g_execution_candidates[n].valid=epoch_candidates[j].valid;
         g_execution_candidates[n].scenario_index=epoch_candidates[j].scenario_index;
         g_execution_candidates[n].scenario_id=epoch_candidates[j].scenario_id;
         g_execution_candidates[n].direction=epoch_candidates[j].direction;
         g_execution_candidates[n].authorization_at=epoch_candidates[j].authorization_at;
         processed[j]=true;
        }

      int master_index=D134FinalizeCurrentExecutionCandidateGroup(available_at);
      if(master_index<0)
         continue;

      int rn=ArraySize(ready_master_indices);
      if(ArrayResize(ready_master_indices,rn+1,8)<0)
         continue;
      ready_master_indices[rn]=master_index;
     }

   ArrayResize(g_execution_candidates,0);

   int ready_count=ArraySize(ready_master_indices);
   if(ready_count<=0)
      return;

   bool ready_long=false;
   bool ready_short=false;
   for(int i=0;i<ready_count;i++)
     {
      int idx=ready_master_indices[i];
      if(g_scenarios[idx].direction>0)
         ready_long=true;
      if(g_scenarios[idx].direction<0)
         ready_short=true;
     }

   // Direction arbitration happens only after each opportunity has valid
   // Entry/SL/TP. A non-executable opposite candidate cannot suppress a valid
   // side merely by reaching WAITING_EXECUTION_GEOMETRY.
   int pre_epoch_exposure_direction=ManagedBrokerExposureDirectionState();

   if(pre_epoch_exposure_direction==2)
     {
      for(int i=0;i<ready_count;i++)
         D134BlockReadyOpportunity(
            ready_master_indices[i],
            available_at,
            "BIDIRECTIONAL_MANAGED_EXPOSURE_INVARIANT_BROKEN",
            V1_EXEC_NONE);
      return;
     }

   if(ready_long && ready_short && pre_epoch_exposure_direction==0)
     {
      g_simultaneous_authorization_ambiguous+=ready_count;
      for(int i=0;i<ready_count;i++)
         D134BlockReadyOpportunity(
            ready_master_indices[i],
            available_at,
            "AMBIGUOUS_SIMULTANEOUS_OPPOSITE_DIRECTION_AUTHORIZATION",
            V1_EXEC_NONE);
      return;
     }

   // Same-direction distinct Entry opportunities are all allowed. If a
   // pre-existing exposure resolves the active side, opposite groups are
   // blocked individually while same-direction add-ons may submit.
   for(int i=0;i<ready_count;i++)
      D134SubmitReadyOpportunity(ready_master_indices[i],available_at);
  }

bool FindEntryDealForOrder(const ulong order_ticket,
                           const datetime from_time,
                           ulong &deal_ticket,
                           ulong &position_id,
                           datetime &deal_time,
                           double &deal_price)
  {
   deal_ticket=0;
   position_id=0;
   deal_time=0;
   deal_price=0.0;
   datetime from=(from_time>86400 ? from_time-86400 : 0);
   if(!HistorySelect(from,TimeCurrent()+60))
      return false;
   for(int i=HistoryDealsTotal()-1;i>=0;i--)
     {
      ulong deal=HistoryDealGetTicket(i);
      if(deal==0)
         continue;
      if(HistoryDealGetString(deal,DEAL_SYMBOL)!=_Symbol ||
         (long)HistoryDealGetInteger(deal,DEAL_MAGIC)!=InpMagicNumber ||
         (ulong)HistoryDealGetInteger(deal,DEAL_ORDER)!=order_ticket)
         continue;
      ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal,DEAL_ENTRY);
      if(entry!=DEAL_ENTRY_IN && entry!=DEAL_ENTRY_INOUT)
         continue;
      deal_ticket=deal;
      position_id=(ulong)HistoryDealGetInteger(deal,DEAL_POSITION_ID);
      deal_time=(datetime)HistoryDealGetInteger(deal,DEAL_TIME);
      deal_price=HistoryDealGetDouble(deal,DEAL_PRICE);
      return true;
     }
   return false;
  }

bool FindExitDealForPosition(const ulong position_id,
                             const datetime from_time,
                             ulong &deal_ticket,
                             datetime &deal_time,
                             double &deal_price,
                             long &deal_reason)
  {
   deal_ticket=0;
   deal_time=0;
   deal_price=0.0;
   deal_reason=0;
   if(position_id==0)
      return false;
   datetime from=(from_time>86400 ? from_time-86400 : 0);
   if(!HistorySelect(from,TimeCurrent()+60))
      return false;
   for(int i=HistoryDealsTotal()-1;i>=0;i--)
     {
      ulong deal=HistoryDealGetTicket(i);
      if(deal==0)
         continue;
      if(HistoryDealGetString(deal,DEAL_SYMBOL)!=_Symbol ||
         (long)HistoryDealGetInteger(deal,DEAL_MAGIC)!=InpMagicNumber ||
         (ulong)HistoryDealGetInteger(deal,DEAL_POSITION_ID)!=position_id)
         continue;
      ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal,DEAL_ENTRY);
      if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY && entry!=DEAL_ENTRY_INOUT)
         continue;
      deal_ticket=deal;
      deal_time=(datetime)HistoryDealGetInteger(deal,DEAL_TIME);
      deal_price=HistoryDealGetDouble(deal,DEAL_PRICE);
      deal_reason=HistoryDealGetInteger(deal,DEAL_REASON);
      return true;
     }
   return false;
  }

void MarkScenarioFilled(const int scenario_index,
                        const datetime observed_at,
                        const ulong deal_ticket,
                        const ulong position_id,
                        const datetime fill_at,
                        const double fill_price)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return;
   if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_FILLED)
      return;

   bool canceled_before_fill=(g_scenarios[scenario_index].strategy_cancel_at>0 ||
                              g_scenarios[scenario_index].execution_status==V1_EXEC_CANCEL_REJECTED ||
                              g_scenarios[scenario_index].execution_status==V1_EXEC_CANCEL_REQUESTED ||
                              g_scenarios[scenario_index].execution_status==V1_EXEC_CANCELED ||
                              g_scenarios[scenario_index].strategy_state==V1_STRATEGY_CANCELED);

   g_scenarios[scenario_index].strategy_state=V1_STRATEGY_FILLED;
   g_scenarios[scenario_index].execution_status=(canceled_before_fill ? V1_EXEC_DIVERGENCE : V1_EXEC_FILLED);
   g_scenarios[scenario_index].fill_at=fill_at>0 ? fill_at : observed_at;
   g_scenarios[scenario_index].fill_price=fill_price;
   g_scenarios[scenario_index].broker_deal_ticket=deal_ticket;
   g_scenarios[scenario_index].broker_position_id=position_id;
   g_positions_filled++;

   // D-133: once the shared order fills, the implementation master owns the
   // frozen server SL/TP lifecycle. Release every secondary contributor Root
   // so MERGED_CONTRIBUTOR state cannot block future independent scenarios.
   D133TerminateMergedSecondaries(
      scenario_index,
      g_scenarios[scenario_index].fill_at,
      "MASTER_FILLED_FROZEN_SL_TP");

   if(canceled_before_fill)
     {
      g_scenarios[scenario_index].execution_divergence=true;
      g_scenarios[scenario_index].execution_divergence_reason="FILLED_AFTER_STRATEGY_CANCELLATION";
      g_execution_divergences++;
     }

   LogLine("POSITION_FILLED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s order_ticket=%I64u deal_ticket=%I64u position_id=%I64u strategy_entry=%.10f actual_fill=%.10f fill_at=%s execution_status=%s divergence=%s",
                        g_scenarios[scenario_index].id,g_scenarios[scenario_index].broker_order_ticket,deal_ticket,position_id,g_scenarios[scenario_index].strategy_entry_price,g_scenarios[scenario_index].fill_price,
                        TimeToString(g_scenarios[scenario_index].fill_at,TIME_DATE|TIME_SECONDS),ExecutionStatusName(g_scenarios[scenario_index].execution_status),
                        g_scenarios[scenario_index].execution_divergence ? "true" : "false"));
  }

bool RequestPendingCancellation(const int scenario_index,
                                const datetime observed_at)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return false;
   if(g_scenarios[scenario_index].broker_order_ticket==0)
      return false;

   if(!OrderSelect(g_scenarios[scenario_index].broker_order_ticket))
      return false;

   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action=TRADE_ACTION_REMOVE;
   request.order=g_scenarios[scenario_index].broker_order_ticket;
   request.symbol=_Symbol;
   request.magic=(ulong)InpMagicNumber;

   g_scenarios[scenario_index].cancel_request_sent=true;
   g_scenarios[scenario_index].execution_status=V1_EXEC_CANCEL_REQUESTED;
   g_pending_cancellations++;

   bool call_ok=OrderSend(request,result);
   if(call_ok && IsAcceptableTradeRetcode(result.retcode))
     {
      g_scenarios[scenario_index].execution_status=V1_EXEC_CANCELED;
      LogLine("PENDING_CANCEL_ACCEPTED","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s order_ticket=%I64u retcode=%u comment=%s strategy_cancel_reason=%s",
                           g_scenarios[scenario_index].id,g_scenarios[scenario_index].broker_order_ticket,result.retcode,result.comment,g_scenarios[scenario_index].strategy_cancel_reason));
      return true;
     }

   g_scenarios[scenario_index].execution_status=V1_EXEC_CANCEL_REJECTED;
   g_cancel_rejected++;
   LogLine("PENDING_CANCEL_REJECTED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s order_ticket=%I64u retcode=%u comment=%s strategy_state=CANCELED broker_order_may_survive=true",
                        g_scenarios[scenario_index].id,g_scenarios[scenario_index].broker_order_ticket,result.retcode,result.comment));
   return false;
  }

bool RequestResidualPendingCancellationAfterFill(const int scenario_index,
                                                   const datetime observed_at,
                                                   const ulong residual_order_ticket)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) || residual_order_ticket==0)
      return false;
   if(!OrderSelect(residual_order_ticket))
      return false;

   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action=TRADE_ACTION_REMOVE;
   request.order=residual_order_ticket;
   request.symbol=_Symbol;
   request.magic=(ulong)InpMagicNumber;

   g_scenarios[scenario_index].cancel_request_sent=true;
   if(!g_scenarios[scenario_index].execution_divergence)
     {
      g_scenarios[scenario_index].execution_divergence=true;
      g_execution_divergences++;
     }
   g_scenarios[scenario_index].execution_divergence_reason="PARTIAL_FILL_WITH_RESIDUAL_PENDING";
   g_scenarios[scenario_index].execution_status=V1_EXEC_DIVERGENCE;
   g_pending_cancellations++;

   bool call_ok=OrderSend(request,result);
   if(call_ok && IsAcceptableTradeRetcode(result.retcode))
     {
      LogLine("PARTIAL_FILL_RESIDUAL_CANCEL_ACCEPTED","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s residual_order_ticket=%I64u retcode=%u comment=%s position_remains_managed=true",
                           g_scenarios[scenario_index].id,residual_order_ticket,result.retcode,result.comment));
      return true;
     }

   g_cancel_rejected++;
   LogLine("PARTIAL_FILL_RESIDUAL_CANCEL_REJECTED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s residual_order_ticket=%I64u call_ok=%s retcode=%u comment=%s retry=false exposure_lock_remains=true",
                        g_scenarios[scenario_index].id,residual_order_ticket,call_ok ? "true" : "false",result.retcode,result.comment));
   return false;
  }

void ReconcileScenarioExecution(const int scenario_index,const datetime observed_at,const bool force_history_probe=false)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return;
   if(!g_scenarios[scenario_index].valid ||
      g_scenarios[scenario_index].strategy_state==V1_STRATEGY_MERGED_CONTRIBUTOR ||
      g_scenarios[scenario_index].broker_order_ticket==0)
     {
      D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);
      return;
     }

   if(g_scenarios[scenario_index].position_closed_at!=0)
     {      D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);
      return;
     }

   // D-135A: a strategy-canceled scenario can still own a live broker
   // pending order. Keep it inside the execution working set until that exact
   // order is canceled, filled (divergence), or otherwise proven terminal.
   if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_PENDING ||
      g_scenarios[scenario_index].strategy_state==V1_STRATEGY_CANCELED ||
      g_scenarios[scenario_index].execution_status==V1_EXEC_CANCEL_REJECTED ||
      g_scenarios[scenario_index].execution_status==V1_EXEC_CANCEL_REQUESTED ||
      g_scenarios[scenario_index].execution_status==V1_EXEC_CANCELED)
     {
      bool pending_live=ScenarioOriginalPendingOrderLive(scenario_index);
      if(pending_live && !force_history_probe)
         return;

      ulong deal=0,deal_position_id=0;
      datetime deal_time=0;
      double deal_price=0.0;
      if(FindEntryDealForOrder(g_scenarios[scenario_index].broker_order_ticket,
                               g_scenarios[scenario_index].pending_submitted_at,
                               deal,deal_position_id,deal_time,deal_price))
        {
         MarkScenarioFilled(scenario_index,observed_at,deal,deal_position_id,deal_time,deal_price);
         if(ScenarioOriginalPendingOrderLive(scenario_index) && !g_scenarios[scenario_index].cancel_request_sent)
            RequestResidualPendingCancellationAfterFill(scenario_index,observed_at,g_scenarios[scenario_index].broker_order_ticket);
         return;
        }

      if(pending_live || ScenarioOriginalPendingOrderLive(scenario_index))
         return;

      if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[scenario_index].execution_status==V1_EXEC_CANCELED)
        {
         D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);
         return;
        }

      g_scenarios[scenario_index].execution_status=V1_EXEC_DIVERGENCE;
      g_scenarios[scenario_index].execution_divergence=true;
      g_scenarios[scenario_index].execution_divergence_reason="PENDING_DISAPPEARED_WITHOUT_FILL_OR_STRATEGY_CANCEL";
      g_execution_divergences++;
      LogLine("EXECUTION_DIVERGENCE","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s reason=%s order_ticket=%I64u scenario_scoped_reconciliation=true",
                           g_scenarios[scenario_index].id,g_scenarios[scenario_index].execution_divergence_reason,g_scenarios[scenario_index].broker_order_ticket));
      D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);
      return;
     }

   if(g_scenarios[scenario_index].strategy_state!=V1_STRATEGY_FILLED)
     {
      D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);
      return;
     }

   if(ScenarioOriginalPendingOrderLive(scenario_index))
     {
      if(!g_scenarios[scenario_index].execution_divergence)
        {
         g_scenarios[scenario_index].execution_divergence=true;
         g_scenarios[scenario_index].execution_divergence_reason="RESIDUAL_PENDING_AFTER_FILL";
         g_scenarios[scenario_index].execution_status=V1_EXEC_DIVERGENCE;
         g_execution_divergences++;
         LogLine("EXECUTION_DIVERGENCE","M1",observed_at,g_scenarios[scenario_index].id,
                 StringFormat("scenario_id=%s reason=%s residual_order_ticket=%I64u scenario_scoped_reconciliation=true other_same_direction_orders_untouched=true",
                              g_scenarios[scenario_index].id,g_scenarios[scenario_index].execution_divergence_reason,g_scenarios[scenario_index].broker_order_ticket));
        }
      if(!g_scenarios[scenario_index].cancel_request_sent)
         RequestResidualPendingCancellationAfterFill(scenario_index,observed_at,g_scenarios[scenario_index].broker_order_ticket);
      return;
     }

   ulong position_ticket=0;
   double position_open=0.0;
   if(FindManagedPositionByIdentifier(g_scenarios[scenario_index].broker_position_id,position_ticket,position_open))
      return;

   ulong exit_deal=0;
   datetime exit_time=0;
   double exit_price=0.0;
   long exit_reason=0;
   if(!FindExitDealForPosition(g_scenarios[scenario_index].broker_position_id,
                               g_scenarios[scenario_index].fill_at,
                               exit_deal,exit_time,exit_price,exit_reason))
      return;

   g_scenarios[scenario_index].position_closed_at=exit_time;
   g_scenarios[scenario_index].exit_price=exit_price;
   g_scenarios[scenario_index].exit_reason=exit_reason;
   g_scenarios[scenario_index].exit_deal_ticket=exit_deal;
   if(!g_scenarios[scenario_index].execution_divergence)
      g_scenarios[scenario_index].execution_status=V1_EXEC_CLOSED;
   g_positions_closed++;

   LogLine("POSITION_CLOSED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s exit_deal=%I64u position_id=%I64u exit_at=%s actual_exit=%.10f deal_reason=%I64d strategy_sl=%.10f strategy_tp=%.10f execution_status=%s scenario_scoped_reconciliation=true",
                        g_scenarios[scenario_index].id,exit_deal,g_scenarios[scenario_index].broker_position_id,
                        TimeToString(exit_time,TIME_DATE|TIME_SECONDS),exit_price,exit_reason,
                        g_scenarios[scenario_index].normalized_sl,g_scenarios[scenario_index].final_objective_price,
                        ExecutionStatusName(g_scenarios[scenario_index].execution_status)));
   D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);
  }

void ReconcileAllManagedExecutions(const datetime observed_at,const bool force_history_probe=false)
  {
   int pos=0;
   while(pos<ArraySize(g_active_execution_scenario_indices))
     {
      int scenario_index=g_active_execution_scenario_indices[pos];
      ReconcileScenarioExecution(scenario_index,observed_at,force_history_probe);
      if(pos<ArraySize(g_active_execution_scenario_indices) &&
         g_active_execution_scenario_indices[pos]==scenario_index)
         pos++;
     }
  }

void ManageIntegratedExecution(const MqlTick &tick)
  {
   datetime observed_at=(datetime)tick.time;
   ReconcileAllManagedExecutions(observed_at,false);

   int active_snapshot[];
   int active_count=ArraySize(g_active_execution_scenario_indices);
   ArrayResize(active_snapshot,active_count);
   for(int a=0;a<active_count;a++)
      active_snapshot[a]=g_active_execution_scenario_indices[a];

   for(int a=0;a<active_count;a++)
     {
      int scenario_index=active_snapshot[a];
      if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
         !g_scenarios[scenario_index].valid ||
         g_scenarios[scenario_index].strategy_state==V1_STRATEGY_MERGED_CONTRIBUTOR ||
         g_scenarios[scenario_index].broker_order_ticket==0)
         continue;

      // Filled positions are individually owned by their frozen server SL/TP.
      // Same-direction later scenarios may coexist in separate hedging positions.
      if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_FILLED)
         continue;

      if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_PENDING &&
         (FinalObjectiveConsumed(g_scenarios[scenario_index]) ||
          ObjectiveDeliveredAtTick(g_scenarios[scenario_index],tick)))
        {
         g_scenarios[scenario_index].strategy_state=V1_STRATEGY_CANCELED;
         g_scenarios[scenario_index].canceled_at=observed_at;
         g_scenarios[scenario_index].cancel_reason="CANCELED_OBJECTIVE_DELIVERED";
         g_scenarios[scenario_index].strategy_cancel_at=observed_at;
         g_scenarios[scenario_index].strategy_cancel_reason="CANCELED_OBJECTIVE_DELIVERED";
         ReleaseRootScenarioOwner(g_scenarios[scenario_index].root_zone_id,
                                  g_scenarios[scenario_index].id);
         D133TerminateMergedSecondaries(
            scenario_index,
            observed_at,
            "CANCELED_OBJECTIVE_DELIVERED");
         LogScenarioCanceled(
            g_scenarios[scenario_index],
            observed_at,
            "CANCELED_OBJECTIVE_DELIVERED");
         g_scenarios_canceled++;
        }
      else if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_PENDING &&
              g_scenarios[scenario_index].execution_contributor_count>1)
        {
         string alive_root_ids="";
         int alive=D133CountAliveContributors(scenario_index,alive_root_ids);

         if(alive<=0)
           {
            g_scenarios[scenario_index].strategy_state=V1_STRATEGY_CANCELED;
            g_scenarios[scenario_index].canceled_at=observed_at;
            g_scenarios[scenario_index].cancel_reason="CANCELED_ALL_CONTRIBUTORS_INVALID";
            g_scenarios[scenario_index].strategy_cancel_at=observed_at;
            g_scenarios[scenario_index].strategy_cancel_reason="CANCELED_ALL_CONTRIBUTORS_INVALID";
            ReleaseRootScenarioOwner(g_scenarios[scenario_index].root_zone_id,
                                     g_scenarios[scenario_index].id);

            D133TerminateMergedSecondaries(
               scenario_index,
               observed_at,
               "CANCELED_ALL_CONTRIBUTORS_INVALID");

            LogLine("EXECUTION_CONTRIBUTORS_EXHAUSTED","M1",observed_at,g_scenarios[scenario_index].id,
                    StringFormat("master_scenario_id=%s contributor_count=%d alive_contributors=0 contributor_root_ids=%s action=CANCEL_PENDING",
                                 g_scenarios[scenario_index].id,
                                 g_scenarios[scenario_index].execution_contributor_count,
                                 g_scenarios[scenario_index].execution_contributor_root_ids));

            LogScenarioCanceled(
               g_scenarios[scenario_index],
               observed_at,
               "CANCELED_ALL_CONTRIBUTORS_INVALID");
            g_scenarios_canceled++;
           }
        }
      else if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_CANCELED &&
              g_scenarios[scenario_index].strategy_cancel_at==0)
        {
         g_scenarios[scenario_index].strategy_cancel_at=
            g_scenarios[scenario_index].canceled_at>0 ?
            g_scenarios[scenario_index].canceled_at :
            observed_at;

         if(g_scenarios[scenario_index].cancel_reason=="ROOT_INVALIDATED")
            g_scenarios[scenario_index].strategy_cancel_reason=
               "CANCELED_SOURCE_INVALIDATED";
         else
            g_scenarios[scenario_index].strategy_cancel_reason=
               "CANCELED_DIRECTION_AUTHORITY";
        }

      if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_CANCELED &&
         ScenarioOriginalPendingOrderLive(scenario_index) &&
         !g_scenarios[scenario_index].cancel_request_sent)
         RequestPendingCancellation(scenario_index,observed_at);
     }

   ReconcileAllManagedExecutions(observed_at,false);
  }

//+------------------------------------------------------------------+
//| D-126 corrected Phase 4C Root-reaction sweep authorization       |
//+------------------------------------------------------------------+
bool IsD126StrategicSweepFamily(const int family)
  {
   // STRUCTURAL_REACTION ownership remains separately blocked.
   return (family==V1_LIQ_EXTERNAL_SWING ||
           family==V1_LIQ_DEFENDED_RANGE_EDGE);
  }

void AddD126SweepSnapshotPool(const string scenario_id,
                              const V1LiquidityPool &pool,
                              const datetime bar_open)
  {
   int n=ArraySize(g_sweep_bar_snapshot);
   if(ArrayResize(g_sweep_bar_snapshot,n+1,256)<0)
      return;

   g_sweep_bar_snapshot[n].valid=true;
   g_sweep_bar_snapshot[n].scenario_id=scenario_id;
   g_sweep_bar_snapshot[n].liquidity_id=pool.id;
   g_sweep_bar_snapshot[n].family=pool.family;
   g_sweep_bar_snapshot[n].tf=pool.tf;
   g_sweep_bar_snapshot[n].side=pool.side;
   g_sweep_bar_snapshot[n].bottom=pool.bottom;
   g_sweep_bar_snapshot[n].top=pool.top;
   g_sweep_bar_snapshot[n].available_at=pool.available_at;
   g_sweep_bar_snapshot[n].snapshot_bar_open=bar_open;
   g_sweep_snapshot_pools++;
  }

void PrepareD126SweepBarSnapshot(const datetime bar_open)
  {
   ArrayResize(g_sweep_bar_snapshot,0);
   g_sweep_snapshot_bar_open=bar_open;

   if(bar_open<=0 ||
      g_execution_epoch_start<=0 ||
      bar_open<g_execution_epoch_start)
      return;

   int scenario_count=0;

   for(int sidx=0;sidx<ArraySize(g_scenarios);sidx++)
     {
      if(!g_scenarios[sidx].valid ||
         (g_scenarios[sidx].strategy_state!=V1_STRATEGY_WAITING_SWEEP &&
          g_scenarios[sidx].strategy_state!=V1_STRATEGY_WAITING_TRIGGER) ||
         g_scenarios[sidx].source_contact_at<=0 ||
         g_scenarios[sidx].source_contact_at>bar_open)
         continue;

      int root_index=FindActiveSourceById(g_scenarios[sidx].root_zone_id);
      if(root_index<0 || g_sources[root_index].kind!=V1_SOURCE_ROOT)
         continue;

      scenario_count++;
      int required_side=
         (g_scenarios[sidx].direction>0 ? V1_SIDE_LOW : V1_SIDE_HIGH);

      for(int i=0;i<ArraySize(g_liquidity);i++)
        {
         if(!g_liquidity[i].valid ||
            !IsD126StrategicSweepFamily(g_liquidity[i].family) ||
            g_liquidity[i].side!=required_side ||
            g_liquidity[i].available_at>=bar_open ||
            g_liquidity[i].strategy_consumed)
            continue;

         AddD126SweepSnapshotPool(g_scenarios[sidx].id,
                                  g_liquidity[i],
                                  bar_open);
        }
     }

   if(scenario_count>0)
      g_sweep_bar_snapshots++;  }

bool D126SnapshotContainsScenario(const string scenario_id)
  {
   for(int i=0;i<ArraySize(g_sweep_bar_snapshot);i++)
      if(g_sweep_bar_snapshot[i].valid &&
         g_sweep_bar_snapshot[i].scenario_id==scenario_id)
         return true;
   return false;
  }

void StoreD126AuthorizedSweepEpisode(const string episode_id,
                                     const V1ScenarioPlan &plan,
                                     const datetime bar_open,
                                     const datetime available_at,
                                     const int pool_count,
                                     const string pool_ids)
  {
   int n=ArraySize(g_authorized_sweep_episodes);
   if(ArrayResize(g_authorized_sweep_episodes,n+1,128)<0)
      return;

   g_authorized_sweep_episodes[n].valid=true;
   g_authorized_sweep_episodes[n].id=episode_id;
   g_authorized_sweep_episodes[n].scenario_id=plan.id;
   g_authorized_sweep_episodes[n].root_zone_id=plan.root_zone_id;
   g_authorized_sweep_episodes[n].direction=plan.direction;
   g_authorized_sweep_episodes[n].sweep_bar_open=bar_open;
   g_authorized_sweep_episodes[n].available_at=available_at;
   g_authorized_sweep_episodes[n].pool_count=pool_count;
   g_authorized_sweep_episodes[n].pool_ids=pool_ids;
  }

void EvaluateD126RootReactionSweeps(const MqlRates &bar,
                                    const datetime available_at)
  {
   if(g_sweep_snapshot_bar_open<=0 ||
      g_sweep_snapshot_bar_open!=bar.time)
      return;

   for(int sidx=0;sidx<ArraySize(g_scenarios);sidx++)
     {
      if(!g_scenarios[sidx].valid ||
         (g_scenarios[sidx].strategy_state!=V1_STRATEGY_WAITING_SWEEP &&
          g_scenarios[sidx].strategy_state!=V1_STRATEGY_WAITING_TRIGGER) ||
         g_scenarios[sidx].source_contact_at<=0 ||
         g_scenarios[sidx].source_contact_at>bar.time ||
         !D126SnapshotContainsScenario(g_scenarios[sidx].id))
         continue;

      if(!BarIntersectsSource(bar,g_scenarios[sidx]))
         continue;

      int authorized_count=0;
      string pool_ids="";

      for(int pidx=0;pidx<ArraySize(g_sweep_bar_snapshot);pidx++)
        {
         if(!g_sweep_bar_snapshot[pidx].valid ||
            g_sweep_bar_snapshot[pidx].scenario_id!=g_scenarios[sidx].id ||
            g_sweep_bar_snapshot[pidx].snapshot_bar_open!=bar.time)
            continue;

         int physical=
            PhysicalConsumptionForBar(g_sweep_bar_snapshot[pidx].side,
                                      g_sweep_bar_snapshot[pidx].bottom,
                                      g_sweep_bar_snapshot[pidx].top,
                                      bar);
         if(physical!=V1_LIQ_CONSUME_SWEEP)
            continue;

         authorized_count++;
         g_authorized_sweep_pools++;

         if(pool_ids!="")
            pool_ids+="|";
         pool_ids+=g_sweep_bar_snapshot[pidx].liquidity_id;

         double tick=LiquidityTickSize();
         double penetration_ticks=
            (g_sweep_bar_snapshot[pidx].side==V1_SIDE_HIGH ?
             (bar.high-g_sweep_bar_snapshot[pidx].top)/tick :
             (g_sweep_bar_snapshot[pidx].bottom-bar.low)/tick);

         LogLine("AUTHORIZED_SWEEP_POOL",
                 "M1",
                 available_at,
                 g_sweep_bar_snapshot[pidx].liquidity_id,
                 StringFormat("scenario_id=%s root_zone_id=%s strategy_source_kind=ROOT family=%s pool_tf=%s side=%s bottom=%.10f top=%.10f pool_available_at=%s pool_snapshot_anchor=%s sweep_bar_open=%s penetration_ticks=%.4f physical=SWEEP root_intersection=true same_contact_bar=false child_required=false snapshot_policy=PER_M1_BAR_PREOPEN_CAUSAL structural_reaction_family=false selection=RETAIN_ALL_FOR_PHASE5A",
                              g_scenarios[sidx].id,
                              g_scenarios[sidx].root_zone_id,
                              LiquidityFamilyName(g_sweep_bar_snapshot[pidx].family),
                              TfName(g_sweep_bar_snapshot[pidx].tf),
                              SideName(g_sweep_bar_snapshot[pidx].side),
                              g_sweep_bar_snapshot[pidx].bottom,
                              g_sweep_bar_snapshot[pidx].top,
                              TimeToString(g_sweep_bar_snapshot[pidx].available_at,TIME_DATE|TIME_SECONDS),
                              TimeToString(g_sweep_bar_snapshot[pidx].snapshot_bar_open,TIME_DATE|TIME_SECONDS),
                              TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                              penetration_ticks));
        }

      if(authorized_count<=0)
         continue;

      string episode_id=
         StringFormat("%s:authorized_sweep:%I64d",
                      g_scenarios[sidx].id,
                      (long)bar.time);

      StoreD126AuthorizedSweepEpisode(episode_id,
                                      g_scenarios[sidx],
                                      bar.time,
                                      available_at,
                                      authorized_count,
                                      pool_ids);

      if(g_scenarios[sidx].strategy_state==V1_STRATEGY_WAITING_SWEEP)
         g_scenarios[sidx].strategy_state=V1_STRATEGY_WAITING_TRIGGER;

      g_scenarios[sidx].authorized_sweep_count+=authorized_count;
      g_authorized_sweep_events++;
      g_root_intersection_sweep_bars++;

      LogLine("AUTHORIZED_SWEEP",
              "M1",
              available_at,
              episode_id,
              StringFormat("scenario_id=%s root_zone_id=%s strategy_source_kind=ROOT direction=%s required_side=%s root_contact_at=%s root_contact_bar_open=%s sweep_bar_open=%s pool_count=%d pool_ids=%s root_intersection=true same_contact_bar=false child_required=false snapshot_policy=PER_M1_BAR_PREOPEN_CAUSAL active_sweep_selection=DEFERRED_PHASE5A state=WAITING_TRIGGER phase5a_choch_search_enabled=false structural_reaction_creation=false order_authorization=false",
                           g_scenarios[sidx].id,
                           g_scenarios[sidx].root_zone_id,
                           DirectionName(g_scenarios[sidx].direction),
                           SideName(g_scenarios[sidx].direction>0 ? V1_SIDE_LOW : V1_SIDE_HIGH),
                           TimeToString(g_scenarios[sidx].source_contact_at,TIME_DATE|TIME_SECONDS),
                           TimeToString(g_scenarios[sidx].source_contact_bar_open,TIME_DATE|TIME_SECONDS),
                           TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                           authorized_count,
                           pool_ids));
     }
  }

//+------------------------------------------------------------------+
//| Superseded Phase 4C contact-snapshot implementation (runtime-dead)|
//+------------------------------------------------------------------+
bool IsSweepEligibleLiquidityFamily(const int family)
  {
   return (family==V1_LIQ_EXTERNAL_SWING ||
           family==V1_LIQ_DEFENDED_RANGE_EDGE ||
           family==V1_LIQ_STRUCTURAL_REACTION);
  }

int FindStrategyLiquidityConsumption(const string liquidity_id)
  {
   for(int i=0;i<ArraySize(g_strategy_liquidity_consumed);i++)
      if(g_strategy_liquidity_consumed[i].valid &&
         g_strategy_liquidity_consumed[i].liquidity_id==liquidity_id)
         return i;
   return -1;
  }

bool IsStrategyLiquidityConsumed(const string liquidity_id)
  {
   return (FindStrategyLiquidityConsumption(liquidity_id)>=0);
  }

void PruneStrategyLiquidityConsumption(const string liquidity_id)
  {
   int index=FindStrategyLiquidityConsumption(liquidity_id);
   if(index<0)
      return;

   int n=ArraySize(g_strategy_liquidity_consumed);
   if(index<n-1)
      g_strategy_liquidity_consumed[index]=g_strategy_liquidity_consumed[n-1];
   ArrayResize(g_strategy_liquidity_consumed,n-1);
  }


void D135MarkFrozenObjectivesConsumedByLiquidity(const string liquidity_id,
                                                 const datetime consumed_at)
  {
   if(liquidity_id=="")
      return;
   for(int i=0;i<ArraySize(g_objective_candidates);i++)
     {
      if(!g_objective_candidates[i].valid ||
         g_objective_candidates[i].consumed ||
         g_objective_candidates[i].liquidity_id!=liquidity_id)
         continue;
      int plan_index=g_objective_candidates[i].scenario_index;
      if(plan_index<0 || plan_index>=ArraySize(g_scenarios) ||
         !g_scenarios[plan_index].valid)
         plan_index=FindScenarioById(g_objective_candidates[i].scenario_id);
      if(plan_index<0 ||
         g_scenarios[plan_index].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[plan_index].strategy_state==V1_STRATEGY_NO_TRADE)
         continue;

      g_objective_candidates[i].consumed=true;
      g_objective_candidates[i].consumed_at=consumed_at;
      LogLine("OBJECTIVE_CANDIDATE_CONSUMED",
              TfName(g_objective_candidates[i].tf),
              consumed_at,
              g_objective_candidates[i].id,
              StringFormat("scenario_id=%s liquidity_id=%s order_index=%d price=%.10f action=KEEP_FROZEN_ORDER_SKIP_IF_LATER_TP_SELECTION",
                           g_objective_candidates[i].scenario_id,
                           g_objective_candidates[i].liquidity_id,
                           g_objective_candidates[i].order_index,
                           g_objective_candidates[i].price));
     }
  }

void MarkStrategyLiquidityConsumed(const string liquidity_id,
                                   const datetime consumed_at,
                                   const int consumption_type,
                                   const string reason)
  {
   if(liquidity_id=="")
      return;

   // D-135 propagates frozen-objective consumption exactly at the causal
   // liquidity-consumption timestamp rather than polling the whole ledger.
   int active_liquidity=FindActiveLiquidityById(liquidity_id);
   if(active_liquidity>=0)
      g_liquidity[active_liquidity].strategy_consumed=true;
   D135MarkFrozenObjectivesConsumedByLiquidity(liquidity_id,consumed_at);

   int existing=FindStrategyLiquidityConsumption(liquidity_id);
   if(existing>=0)
      return;

   int n=ArraySize(g_strategy_liquidity_consumed);
   if(ArrayResize(g_strategy_liquidity_consumed,n+1,256)<0)
      return;

   g_strategy_liquidity_consumed[n].valid=true;
   g_strategy_liquidity_consumed[n].liquidity_id=liquidity_id;
   g_strategy_liquidity_consumed[n].consumed_at=consumed_at;
   g_strategy_liquidity_consumed[n].consumption_type=consumption_type;
   g_strategy_liquidity_consumed[n].reason=reason;
  }

void MarkScenarioPoolConsumed(const string liquidity_id,
                              const datetime consumed_at,
                              const int consumption_type)
  {
   for(int i=0;i<ArraySize(g_group_contact_pools);i++)
     {
      if(!g_group_contact_pools[i].valid ||
         g_group_contact_pools[i].liquidity_id!=liquidity_id)
         continue;

      g_group_contact_pools[i].consumed=true;
      g_group_contact_pools[i].consumed_at=consumed_at;
      g_group_contact_pools[i].consumption_type=consumption_type;
     }

   for(int i=0;i<ArraySize(g_scenario_eligible_pools);i++)
     {
      if(!g_scenario_eligible_pools[i].valid ||
         g_scenario_eligible_pools[i].liquidity_id!=liquidity_id ||
         g_scenario_eligible_pools[i].consumed)
         continue;

      g_scenario_eligible_pools[i].consumed=true;
      g_scenario_eligible_pools[i].consumed_at=consumed_at;
      g_scenario_eligible_pools[i].consumption_type=consumption_type;
     }
  }

int PhysicalConsumptionForBar(const int side,
                              const double bottom,
                              const double top,
                              const MqlRates &bar)
  {
   if(side==V1_SIDE_HIGH)
     {
      if(bar.close>top)
         return V1_LIQ_CONSUME_BODY_DELIVERY;
      if(HasOneTickAbove(bar.high,top) && bar.close<=top)
         return V1_LIQ_CONSUME_SWEEP;
     }
   else if(side==V1_SIDE_LOW)
     {
      if(bar.close<bottom)
         return V1_LIQ_CONSUME_BODY_DELIVERY;
      if(HasOneTickBelow(bar.low,bottom) && bar.close>=bottom)
         return V1_LIQ_CONSUME_SWEEP;
     }
   return V1_LIQ_CONSUME_NONE;
  }

void UpdateM1StrategyLiquidityOverlay(const MqlRates &bar,
                                      const datetime available_at)
  {
   for(int i=0;i<ArraySize(g_liquidity);i++)
     {
      if(!g_liquidity[i].valid ||
         g_liquidity[i].strategy_consumed ||
         g_liquidity[i].available_at>bar.time)         continue;

      int consumption=
         PhysicalConsumptionForBar(g_liquidity[i].side,
                                   g_liquidity[i].bottom,
                                   g_liquidity[i].top,
                                   bar);
      if(consumption==V1_LIQ_CONSUME_NONE)
         continue;

      MarkStrategyLiquidityConsumed(g_liquidity[i].id,
                                    available_at,
                                    consumption,
                                    "M1_PHYSICAL_OVERLAY");
      MarkScenarioPoolConsumed(g_liquidity[i].id,
                               available_at,
                               consumption);
      g_strategy_m1_pool_consumptions++;

      LogLine("STRATEGY_LIQUIDITY_M1_CONSUMED",
              "M1",
              available_at,
              g_liquidity[i].id,
              StringFormat("pool_tf=%s family=%s side=%s bottom=%.10f top=%.10f pool_available_at=%s bar_open=%s high=%.10f low=%.10f close=%.10f consumption=%s strategy_overlay=true",
                           TfName(g_liquidity[i].tf),
                           LiquidityFamilyName(g_liquidity[i].family),
                           SideName(g_liquidity[i].side),
                           g_liquidity[i].bottom,
                           g_liquidity[i].top,
                           TimeToString(g_liquidity[i].available_at,TIME_DATE|TIME_SECONDS),
                           TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                           bar.high,
                           bar.low,
                           bar.close,
                           LiquidityConsumptionName(consumption)));
     }
  }

void AddGroupContactPool(const string scenario_id,
                         const V1LiquidityPool &pool)
  {
   int n=ArraySize(g_group_contact_pools);
   if(ArrayResize(g_group_contact_pools,n+1,128)<0)
      return;

   g_group_contact_pools[n].valid=true;
   g_group_contact_pools[n].scenario_id=scenario_id;
   g_group_contact_pools[n].liquidity_id=pool.id;
   g_group_contact_pools[n].family=pool.family;
   g_group_contact_pools[n].tf=pool.tf;
   g_group_contact_pools[n].side=pool.side;
   g_group_contact_pools[n].bottom=pool.bottom;
   g_group_contact_pools[n].top=pool.top;
   g_group_contact_pools[n].available_at=pool.available_at;
   g_group_contact_pools[n].consumed=false;
   g_group_contact_pools[n].consumed_at=0;
   g_group_contact_pools[n].consumption_type=V1_LIQ_CONSUME_NONE;
  }

void PrepareGroupContactPoolSnapshot(const datetime group_time)
  {
   ArrayResize(g_group_contact_pools,0);

   if(group_time<=0)
      return;

   datetime contact_bar_open=group_time-PeriodSeconds(PERIOD_M1);

   for(int s=0;s<ArraySize(g_scenarios);s++)
     {
      if(!g_scenarios[s].valid ||
         g_scenarios[s].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[s].strategy_state==V1_STRATEGY_NO_TRADE ||
         g_scenarios[s].source_contact_at>0 ||
         g_scenarios[s].frozen_at>=group_time)
         continue;

      if(FindActiveSourceById(g_scenarios[s].final_source_id)<0)
         continue;

      int required_side=
         (g_scenarios[s].direction>0 ? V1_SIDE_LOW : V1_SIDE_HIGH);

      for(int i=0;i<ArraySize(g_liquidity);i++)
        {
         if(!g_liquidity[i].valid ||
            !IsSweepEligibleLiquidityFamily(g_liquidity[i].family) ||
            g_liquidity[i].side!=required_side ||
            g_liquidity[i].available_at>=contact_bar_open ||
            g_liquidity[i].strategy_consumed)
            continue;

         AddGroupContactPool(g_scenarios[s].id,g_liquidity[i]);
        }
     }
  }

int PersistScenarioContactPools(const string scenario_id)
  {
   int count=0;

   for(int i=0;i<ArraySize(g_group_contact_pools);i++)
     {
      if(!g_group_contact_pools[i].valid ||
         g_group_contact_pools[i].scenario_id!=scenario_id)
         continue;

      int n=ArraySize(g_scenario_eligible_pools);
      if(ArrayResize(g_scenario_eligible_pools,n+1,128)<0)
         continue;

      g_scenario_eligible_pools[n].valid=true;
      g_scenario_eligible_pools[n].scenario_id=scenario_id;
      g_scenario_eligible_pools[n].liquidity_id=
         g_group_contact_pools[i].liquidity_id;
      g_scenario_eligible_pools[n].family=
         g_group_contact_pools[i].family;
      g_scenario_eligible_pools[n].tf=
         g_group_contact_pools[i].tf;
      g_scenario_eligible_pools[n].side=
         g_group_contact_pools[i].side;
      g_scenario_eligible_pools[n].bottom=
         g_group_contact_pools[i].bottom;
      g_scenario_eligible_pools[n].top=
         g_group_contact_pools[i].top;
      g_scenario_eligible_pools[n].available_at=
         g_group_contact_pools[i].available_at;
      g_scenario_eligible_pools[n].consumed=
         g_group_contact_pools[i].consumed;
      g_scenario_eligible_pools[n].consumed_at=
         g_group_contact_pools[i].consumed_at;
      g_scenario_eligible_pools[n].consumption_type=
         g_group_contact_pools[i].consumption_type;
      g_scenario_eligible_pools[n].authorized=false;
      count++;
     }

   return count;
  }

void LogScenarioEligiblePoolsAtContact(const int scenario_index,
                                       const datetime available_at)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios))
      return;

   for(int i=0;i<ArraySize(g_scenario_eligible_pools);i++)
     {
      if(!g_scenario_eligible_pools[i].valid ||
         g_scenario_eligible_pools[i].scenario_id!=g_scenarios[scenario_index].id)
         continue;

      g_eligible_sweep_pools_frozen++;

      LogLine("SWEEP_ELIGIBLE_POOL_FROZEN",
              TfName(g_scenario_eligible_pools[i].tf),
              available_at,
              g_scenario_eligible_pools[i].liquidity_id,
              StringFormat("scenario_id=%s family=%s pool_tf=%s side=%s bottom=%.10f top=%.10f pool_available_at=%s source_contact_bar_open=%s mature_preexisting=true consumed_on_contact_bar=%s contact_bar_consumption=%s",
                           g_scenarios[scenario_index].id,
                           LiquidityFamilyName(g_scenario_eligible_pools[i].family),
                           TfName(g_scenario_eligible_pools[i].tf),
                           SideName(g_scenario_eligible_pools[i].side),
                           g_scenario_eligible_pools[i].bottom,
                           g_scenario_eligible_pools[i].top,
                           TimeToString(g_scenario_eligible_pools[i].available_at,TIME_DATE|TIME_SECONDS),
                           TimeToString(g_scenarios[scenario_index].source_contact_bar_open,TIME_DATE|TIME_SECONDS),
                           (g_scenario_eligible_pools[i].consumed &&
                            g_scenario_eligible_pools[i].consumed_at==available_at) ?
                              "true" : "false",
                           (g_scenario_eligible_pools[i].consumed &&
                            g_scenario_eligible_pools[i].consumed_at==available_at) ?
                              LiquidityConsumptionName(g_scenario_eligible_pools[i].consumption_type) :
                              "NONE"));
     }
  }

bool BarIntersectsSource(const MqlRates &bar,const V1ScenarioPlan &plan)
  {
   return (bar.high>=plan.source_bottom &&
           bar.low<=plan.source_top);
  }

double StartupReferencePrice()
  {
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return 0.0;

   if(tick.last>0.0)
      return tick.last;
   if(tick.bid>0.0)
      return tick.bid;
   if(tick.ask>0.0)
      return tick.ask;
   return 0.0;
  }

void InitializeStartupSourceReentryGuards(const datetime now)
  {
   double price=StartupReferencePrice();
   if(price<=0.0)
      return;

   for(int s=0;s<ArraySize(g_scenarios);s++)
     {
      if(!g_scenarios[s].valid ||
         g_scenarios[s].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[s].strategy_state==V1_STRATEGY_NO_TRADE ||
         g_scenarios[s].source_contact_at>0)
         continue;

      if(price<g_scenarios[s].source_bottom ||
         price>g_scenarios[s].source_top)
         continue;

      g_scenarios[s].startup_inside_source=true;
      g_scenarios[s].startup_exit_seen=false;

      LogLine("STARTUP_SOURCE_REENTRY_REQUIRED",
              "M1",
              now,
              g_scenarios[s].id,
              StringFormat("scenario_id=%s final_source_id=%s startup_price=%.10f source_bottom=%.10f source_top=%.10f contact_disarmed=true required=EXIT_THEN_REENTRY",
                           g_scenarios[s].id,
                           g_scenarios[s].final_source_id,
                           price,
                           g_scenarios[s].source_bottom,
                           g_scenarios[s].source_top));
     }
  }

void ProcessScenarioSourceContactAndSweep(const MqlRates &bar,
                                          const datetime available_at)
  {
   UpdateM1StrategyLiquidityOverlay(bar,available_at);

   for(int s=0;s<ArraySize(g_scenarios);s++)
     {
      if(!g_scenarios[s].valid ||
         g_scenarios[s].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[s].strategy_state==V1_STRATEGY_NO_TRADE)
         continue;

      int source_index=FindActiveSourceById(g_scenarios[s].final_source_id);
      if(source_index<0)
         continue;

      bool intersects=BarIntersectsSource(bar,g_scenarios[s]);

      if(g_scenarios[s].source_contact_at==0 &&
         g_scenarios[s].startup_inside_source &&
         !g_scenarios[s].startup_exit_seen)
        {
         if(!intersects)
           {
            g_scenarios[s].startup_exit_seen=true;
            LogLine("STARTUP_SOURCE_EXIT",
                    "M1",
                    available_at,
                    g_scenarios[s].id,
                    StringFormat("scenario_id=%s final_source_id=%s bar_open=%s source_bottom=%.10f source_top=%.10f reentry_armed=true",
                                 g_scenarios[s].id,
                                 g_scenarios[s].final_source_id,
                                 TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                                 g_scenarios[s].source_bottom,
                                 g_scenarios[s].source_top));
           }
         continue;
        }

      if(g_scenarios[s].source_contact_at==0)
        {
         if(available_at<=g_scenarios[s].frozen_at ||
            available_at<=g_sources[source_index].available_at ||
            !intersects)
            continue;

         g_scenarios[s].source_contact_at=available_at;
         g_scenarios[s].source_contact_bar_open=bar.time;
         g_scenarios[s].strategy_state=V1_STRATEGY_WAITING_TRIGGER;
         g_scenarios[s].eligible_pool_count_at_contact=
            PersistScenarioContactPools(g_scenarios[s].id);
         g_source_contacts++;

         LogScenarioEligiblePoolsAtContact(s,available_at);

         LogLine("SOURCE_CONTACT",
                 "M1",
                 available_at,
                 g_scenarios[s].id,
                 StringFormat("state=WAITING_TRIGGER scope=%s direction=%s final_source_id=%s source_tf=%s source_bottom=%.10f source_top=%.10f bar_open=%s high=%.10f low=%.10f close=%.10f source_available_at=%s plan_frozen_at=%s eligible_pool_count=%d sweep_search_enabled=true choch_search_enabled=false",
                              ScenarioScopeName(g_scenarios[s].scope),
                              DirectionName(g_scenarios[s].direction),
                              g_scenarios[s].final_source_id,
                              TfName(g_scenarios[s].source_tf),
                              g_scenarios[s].source_bottom,
                              g_scenarios[s].source_top,
                              TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                              bar.high,                              bar.low,
                              bar.close,
                              TimeToString(g_sources[source_index].available_at,TIME_DATE|TIME_SECONDS),
                              TimeToString(g_scenarios[s].frozen_at,TIME_DATE|TIME_SECONDS),
                              g_scenarios[s].eligible_pool_count_at_contact));
        }

      if(g_scenarios[s].source_contact_at==0 || !intersects)
         continue;

      string pool_ids="";
      int authorized_count=0;

      for(int p=0;p<ArraySize(g_scenario_eligible_pools);p++)
        {
         if(!g_scenario_eligible_pools[p].valid ||
            g_scenario_eligible_pools[p].scenario_id!=g_scenarios[s].id ||
            g_scenario_eligible_pools[p].authorized)
            continue;

         if(g_scenario_eligible_pools[p].consumed &&
            g_scenario_eligible_pools[p].consumed_at<available_at)
            continue;

         int physical=
            PhysicalConsumptionForBar(g_scenario_eligible_pools[p].side,
                                      g_scenario_eligible_pools[p].bottom,
                                      g_scenario_eligible_pools[p].top,
                                      bar);

         if(physical==V1_LIQ_CONSUME_BODY_DELIVERY)
           {
            if(!g_scenario_eligible_pools[p].consumed)
              {
               g_scenario_eligible_pools[p].consumed=true;
               g_scenario_eligible_pools[p].consumed_at=available_at;
               g_scenario_eligible_pools[p].consumption_type=physical;
               MarkStrategyLiquidityConsumed(
                  g_scenario_eligible_pools[p].liquidity_id,
                  available_at,
                  physical,
                  "M1_SCENARIO_BODY_DELIVERY");
              }
            continue;
           }

         if(physical!=V1_LIQ_CONSUME_SWEEP)
            continue;

         if(g_scenario_eligible_pools[p].consumed &&
            g_scenario_eligible_pools[p].consumed_at==available_at &&
            g_scenario_eligible_pools[p].consumption_type!=V1_LIQ_CONSUME_SWEEP)
            continue;

         if(!g_scenario_eligible_pools[p].consumed)
           {
            g_scenario_eligible_pools[p].consumed=true;
            g_scenario_eligible_pools[p].consumed_at=available_at;
            g_scenario_eligible_pools[p].consumption_type=V1_LIQ_CONSUME_SWEEP;
            MarkStrategyLiquidityConsumed(
               g_scenario_eligible_pools[p].liquidity_id,
               available_at,
               V1_LIQ_CONSUME_SWEEP,
               "M1_AUTHORIZED_SWEEP");
           }

         g_scenario_eligible_pools[p].authorized=true;
         authorized_count++;
         g_authorized_sweep_pools++;

         if(pool_ids!="")
            pool_ids+="|";
         pool_ids+=g_scenario_eligible_pools[p].liquidity_id;

         double tick=LiquidityTickSize();
         double penetration_ticks=
            (g_scenario_eligible_pools[p].side==V1_SIDE_HIGH ?
             (bar.high-g_scenario_eligible_pools[p].top)/tick :
             (g_scenario_eligible_pools[p].bottom-bar.low)/tick);

         LogLine("AUTHORIZED_SWEEP_POOL",
                 "M1",
                 available_at,
                 g_scenario_eligible_pools[p].liquidity_id,
                 StringFormat("scenario_id=%s family=%s pool_tf=%s side=%s bottom=%.10f top=%.10f pool_available_at=%s source_contact_bar_open=%s sweep_bar_open=%s penetration_ticks=%.4f physical=SWEEP source_intersection=true",
                              g_scenarios[s].id,
                              LiquidityFamilyName(g_scenario_eligible_pools[p].family),
                              TfName(g_scenario_eligible_pools[p].tf),
                              SideName(g_scenario_eligible_pools[p].side),
                              g_scenario_eligible_pools[p].bottom,
                              g_scenario_eligible_pools[p].top,
                              TimeToString(g_scenario_eligible_pools[p].available_at,TIME_DATE|TIME_SECONDS),
                              TimeToString(g_scenarios[s].source_contact_bar_open,TIME_DATE|TIME_SECONDS),
                              TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                              penetration_ticks));
        }

      if(authorized_count<=0)
         continue;

      string sweep_event_id=StringFormat("%s:authorized_sweep:%I64d",
                                         g_scenarios[s].id,
                                         (long)bar.time);

      if(g_scenarios[s].active_sweep_event_id!="" &&
         g_scenarios[s].active_sweep_event_id!=sweep_event_id)
        {
         LogLine("AUTHORIZED_SWEEP_REPLACED",
                 "M1",
                 available_at,
                 g_scenarios[s].active_sweep_event_id,
                 StringFormat("scenario_id=%s old_sweep_event_id=%s new_sweep_event_id=%s reason=NEW_VALID_PRE_CHOCH_SWEEP",
                              g_scenarios[s].id,
                              g_scenarios[s].active_sweep_event_id,
                              sweep_event_id));
        }

      bool same_bar_contact=
         (g_scenarios[s].source_contact_at==available_at);

      g_scenarios[s].active_sweep_event_id=sweep_event_id;
      g_scenarios[s].active_sweep_bar_open=bar.time;
      g_scenarios[s].active_sweep_at=available_at;
      g_scenarios[s].authorized_sweep_count+=authorized_count;
      g_authorized_sweep_events++;

      LogLine("AUTHORIZED_SWEEP",
              "M1",
              available_at,
              sweep_event_id,
              StringFormat("scenario_id=%s direction=%s required_side=%s final_source_id=%s source_contact_at=%s source_contact_bar_open=%s sweep_bar_open=%s pool_count=%d pool_ids=%s same_bar_contact=%s source_intersection=true choch_search_enabled=true",
                           g_scenarios[s].id,
                           DirectionName(g_scenarios[s].direction),
                           SideName(g_scenarios[s].direction>0 ? V1_SIDE_LOW : V1_SIDE_HIGH),
                           g_scenarios[s].final_source_id,
                           TimeToString(g_scenarios[s].source_contact_at,TIME_DATE|TIME_SECONDS),
                           TimeToString(g_scenarios[s].source_contact_bar_open,TIME_DATE|TIME_SECONDS),
                           TimeToString(bar.time,TIME_DATE|TIME_SECONDS),
                           authorized_count,
                           pool_ids,
                           same_bar_contact ? "true" : "false"));
     }
  }

bool ReactionExtremeOccurredAfterContact(const V1ScenarioPlan &plan,
                                         const V1WaveRef &wave)
  {
   if(plan.source_contact_at<=0 ||
      plan.source_contact_bar_open<=0 ||
      wave.occurred_at<=0)
      return false;

   datetime source_bar_end=
      wave.occurred_at+PeriodSeconds(plan.source_tf);
   datetime search_start=
      (wave.occurred_at>plan.source_contact_bar_open ?
       wave.occurred_at :
       plan.source_contact_bar_open);

   if(search_start>=source_bar_end)
      return false;

   MqlRates m1[];
   ArraySetAsSeries(m1,false);
   int copied=CopyRates(_Symbol,
                        PERIOD_M1,
                        (datetime)search_start,
                        source_bar_end-1,
                        m1);
   if(copied<=0)
      return false;

   double tick=LiquidityTickSize();

   for(int i=0;i<copied;i++)
     {
      datetime m1_available=m1[i].time+PeriodSeconds(PERIOD_M1);
      if(m1_available<plan.source_contact_at)
         continue;

      bool intersects=
         (m1[i].high>=plan.source_bottom &&
          m1[i].low<=plan.source_top);
      if(!intersects)
         continue;

      if(wave.side==V1_SIDE_LOW &&
         MathAbs(m1[i].low-wave.price)<=tick*0.5)
         return true;

      if(wave.side==V1_SIDE_HIGH &&
         MathAbs(m1[i].high-wave.price)<=tick*0.5)
         return true;
     }

   return false;
  }

void TryCreateStructuralReactionLiquidity(const int tf_index,
                                          const datetime available_at)
  {
   if(!g_structure[tf_index].last_wave.valid ||
      !g_structure[tf_index].last_wave.is_wave ||
      g_structure[tf_index].last_wave.available_at!=available_at)
      return;

   V1WaveRef wave;
   CopyWave(g_structure[tf_index].last_wave,wave);

   for(int s=0;s<ArraySize(g_scenarios);s++)
     {
      if(!g_scenarios[s].valid ||
         g_scenarios[s].strategy_state==V1_STRATEGY_CANCELED ||
         g_scenarios[s].strategy_state==V1_STRATEGY_NO_TRADE ||
         g_scenarios[s].source_contact_at<=0 ||
         g_scenarios[s].source_tf!=g_timeframes[tf_index] ||
         available_at<=g_scenarios[s].source_contact_at)
         continue;

      int expected_side=
         (g_scenarios[s].direction>0 ? V1_SIDE_LOW : V1_SIDE_HIGH);
      if(wave.side!=expected_side)
         continue;

      int source_index=FindActiveSourceById(g_scenarios[s].final_source_id);
      if(source_index<0 ||
         g_sources[source_index].scenario_owner_id!=g_scenarios[s].id)
         continue;

      if(!ReactionExtremeOccurredAfterContact(g_scenarios[s],wave))
         continue;

      string pool_id=StringFormat("%s:liquidity:STRUCTURAL_REACTION:%s:%s:%s",
                                  TfName(g_timeframes[tf_index]),
                                  SideName(wave.side),
                                  g_scenarios[s].final_source_id,
                                  wave.id);

      if(FindActiveLiquidityById(pool_id)>=0 ||
         IsStrategyLiquidityConsumed(pool_id))
         continue;

      string causal_source=StringFormat("%s|%s",
                                        g_scenarios[s].final_source_id,
                                        wave.id);

      if(AddLiquidityPool(tf_index,
                          V1_LIQ_STRUCTURAL_REACTION,
                          wave.side,
                          wave.wick_bottom,
                          wave.wick_top,
                          causal_source,
                          "STRUCTURALLY_OWNED_OB_REACTION",
                          wave.occurred_at,
                          available_at,
                          pool_id))
        {
         g_structural_reaction_created++;

         LogLine("STRUCTURAL_REACTION_CREATED",
                 TfName(g_timeframes[tf_index]),
                 available_at,
                 pool_id,
                 StringFormat("scenario_id=%s final_source_id=%s direction=%s reaction_wave_id=%s reaction_side=%s reaction_occurred_at=%s source_contact_at=%s source_contact_bar_open=%s reaction_extreme_after_contact_proven_on_m1=true same_first_position_eligible=false",
                              g_scenarios[s].id,
                              g_scenarios[s].final_source_id,
                              DirectionName(g_scenarios[s].direction),
                              wave.id,
                              SideName(wave.side),
                              TimeToString(wave.occurred_at,TIME_DATE|TIME_SECONDS),
                              TimeToString(g_scenarios[s].source_contact_at,TIME_DATE|TIME_SECONDS),
                              TimeToString(g_scenarios[s].source_contact_bar_open,TIME_DATE|TIME_SECONDS)));
        }
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
           StringFormat("active_planned=%d continuation=%d early_reversal=%d canceled=%d objective_candidates_frozen=%I64d no_objective=%I64d precontact_root_plans=%I64d scenario_root_contacts=%I64d root_contacts_without_preplan=%I64d strategy_source_kind=ROOT child_required=false linear_trigger_pipeline=true fvg_authorization=true entry_sl_tp=true tester_pending_execution=true live_execution=false",
                        planned,
                        continuation,
                        reversal,
                        canceled,
                        g_objective_candidates_frozen,
                        g_scenarios_no_objective,
                        g_precontact_root_plans,
                        g_scenario_root_contacts,
                        g_root_contacts_without_preplan));
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
   if(s.tf==PERIOD_M30)
      PushRegimeM30Wave(wave);
   PushRangeWave(s,wave);

   if(s.trend==V1_TREND_NEUTRAL || s.trend==V1_TREND_TRANSITION)
      UpdateNeutralReferences(s,wave);
   else
      UpdateDirectionalWaveRoles(s,wave);

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
//| D122A post-contact causal LTF refinement                         |
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
   candidate.source_reason="";
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
      if(state.protected_low.valid && bar.close<state.protected_low.price)
        {
         EnterTransition(state,-1,available_at);
         return false;
        }

      if(state.external_high.valid && bar.close>state.external_high.price)
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

         state.range_low=state.protected_low.valid ? state.protected_low.price : state.range_low;
         BuildDeliveryExtreme(state,V1_SIDE_HIGH,bar,available_at,state.external_high);
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
      if(state.protected_high.valid && bar.close>state.protected_high.price)
        {
         EnterTransition(state,1,available_at);
         return false;
        }

      if(state.external_low.valid && bar.close<state.external_low.price)
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

         state.range_high=state.protected_high.valid ? state.protected_high.price : state.range_high;
         BuildDeliveryExtreme(state,V1_SIDE_LOW,bar,available_at,state.external_low);
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
         V1WaveRef broken,protected_ref;         CopyWave(state.neutral_high,broken);
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
         event.event_id=BuildStructureEventId(state,V1_EVENT_INITIAL_BOS,bar);
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
         event.event_id=BuildStructureEventId(state,V1_EVENT_INITIAL_BOS,bar);
         return true;
        }
     }

   return false;
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

      string merged=MergeObSourceReason(candidates[i].source_reason,candidate.source_reason);
      if(candidate.available_at<candidates[i].available_at)
        {
         V1ChildCandidate replacement=candidate;
         replacement.source_reason=merged;
         candidates[i]=replacement;
        }
      else
         candidates[i].source_reason=merged;
      return;
     }

   int n=ArraySize(candidates);
   if(ArrayResize(candidates,n+1,32)<0)
      return;
   candidates[n]=candidate;
  }

bool BarIntersectsZone(const MqlRates &bar,const double bottom,const double top)
  {
   return (bar.high>=bottom && bar.low<=top);
  }

bool WaveIntersectsSource(const V1WaveRef &wave,const V1SourceZone &source)
  {
   if(!wave.valid || !source.valid)
      return false;

   double bottom=wave.wick_bottom;
   double top=wave.wick_top;
   if(top<bottom || (top==0.0 && bottom==0.0))
     {
      bottom=wave.price;
      top=wave.price;
     }
   return (top>=source.bottom && bottom<=source.top);
  }

int FindRootReactionTrackerByRootId(const string root_id)
  {
   for(int i=0;i<ArraySize(g_root_reactions);i++)
      if(g_root_reactions[i].valid && g_root_reactions[i].root_zone_id==root_id)
         return i;
   return -1;
  }

int CountChildrenInLineagePath(const string path)
  {
   int count=0;
   int pos=0;
   while(true)
     {
      int found=StringFind(path,">",pos);
      if(found<0)
         break;
      count++;
      pos=found+1;
     }
   return count;
  }

void RollbackPostContactRefinementAfterChildInvalidation(const string root_id,
                                                         const string child_id,
                                                         const string parent_zone_id,
                                                         const datetime available_at,
                                                         const string reason)
  {
   int index=FindRootReactionTrackerByRootId(root_id);
   if(index<0)
      return;

   if(g_root_reactions[index].status==V1_ROOT_WATCH_INVALIDATED ||
      g_root_reactions[index].status==V1_ROOT_WATCH_INELIGIBLE_PRIOR_TOUCH ||
      g_root_reactions[index].status==V1_ROOT_WATCH_ERROR)
      return;

   string marker=">"+child_id;
   int cut=StringFind(g_root_reactions[index].path,marker);
   if(cut>=0)
      g_root_reactions[index].path=StringSubstr(g_root_reactions[index].path,0,cut);

   int parent_index=FindActiveSourceById(parent_zone_id);
   if(parent_index<0)
     {
      InvalidatePostContactRootTracker(root_id,available_at,"ROLLBACK_PARENT_NOT_ACTIVE");
      return;
     }

   g_root_reactions[index].current_parent_zone_id=parent_zone_id;
   g_root_reactions[index].child_count=CountChildrenInLineagePath(g_root_reactions[index].path);
   g_root_reactions[index].final_child_id=(g_sources[parent_index].kind==V1_SOURCE_CHILD ? parent_zone_id : "");
   g_root_reactions[index].status=V1_ROOT_WATCH_READY;
   g_root_reactions[index].lineage_updated_at=available_at;

   int refinement_index=FindRefinementByRootId(root_id);
   if(refinement_index>=0)
     {
      g_refinements[refinement_index].final_child_id=g_root_reactions[index].final_child_id;
      g_refinements[refinement_index].path=g_root_reactions[index].path;
      g_refinements[refinement_index].child_count=g_root_reactions[index].child_count;
      g_refinements[refinement_index].status=V1_REFINE_ROOT_ONLY_READY;
      g_refinements[refinement_index].frozen_at=available_at;
      g_refinements[refinement_index].snapshot_at=available_at;
      g_refinements[refinement_index].stop_reason="ROOT_CONTEXT_READY_OPTIONAL_CHILD_AUDIT_ONLY";
     }

   LogLine("REFINEMENT_UPDATED","",available_at,root_id,
           StringFormat("status=%s child_count=%d final_child_id=%s path=%s invalidated_child_id=%s rollback_parent_id=%s reason=%s Root_remains_ACTIVE=true new_post_contact_child_allowed=true strategy_authority=false",
                        RootReactionStatusName(g_root_reactions[index].status),
                        g_root_reactions[index].child_count,
                        g_root_reactions[index].final_child_id=="" ? "NA" : g_root_reactions[index].final_child_id,
                        g_root_reactions[index].path,child_id,parent_zone_id,reason));
  }

void InvalidatePostContactRootTracker(const string root_id,const datetime available_at,const string reason)
  {
   int index=FindRootReactionTrackerByRootId(root_id);
   if(index<0)
      return;

   if(g_root_reactions[index].status==V1_ROOT_WATCH_INVALIDATED ||
      g_root_reactions[index].status==V1_ROOT_WATCH_INELIGIBLE_PRIOR_TOUCH ||
      g_root_reactions[index].status==V1_ROOT_WATCH_ERROR)
      return;

   bool no_child=(g_root_reactions[index].child_count==0);
   g_root_reactions[index].status=V1_ROOT_WATCH_INVALIDATED;
   g_root_reactions[index].lineage_updated_at=available_at;
   D135RemoveIndexValue(g_waiting_root_reaction_indices,index);
   D135RemoveIndexValue(g_ready_root_reaction_indices,index);
   g_root_reaction_state_version++;

   LogLine("ROOT_REACTION_INVALIDATED",TfName(g_root_reactions[index].root_tf),available_at,root_id,
           StringFormat("status=INVALIDATED root_contact_at=%s child_count=%d final_child_id=%s no_post_contact_child=%s reason=%s strategy_authority=false",
                        g_root_reactions[index].root_contact_at>0 ? TimeToString(g_root_reactions[index].root_contact_at,TIME_DATE|TIME_SECONDS) : "NA",
                        g_root_reactions[index].child_count,
                        g_root_reactions[index].final_child_id=="" ? "NA" : g_root_reactions[index].final_child_id,
                        no_child ? "true" : "false",reason));
  }

bool RootHadClosedM1TouchAfterAvailability(const V1SourceZone &root,
                                           const datetime through_at,
                                           bool &prior_touch,
                                           datetime &first_touch_at)
  {
   prior_touch=false;
   first_touch_at=0;
   if(root.available_at<=0 || through_at<=root.available_at)
      return true;

   MqlRates bars[];
   ArraySetAsSeries(bars,false);
   ResetLastError();
   int copied=CopyRates(_Symbol,PERIOD_M1,root.available_at,through_at,bars);
   if(copied<0)
     {
      LogLine("SOURCE_DETECTOR_ERROR","M1",through_at,root.id,
              StringFormat("reason=ROOT_UNCONSUMED_AUDIT_COPYRATES_FAILED from=%s to=%s error=%d",
                           TimeToString(root.available_at,TIME_DATE|TIME_SECONDS),
                           TimeToString(through_at,TIME_DATE|TIME_SECONDS),GetLastError()));
      return false;
     }

   for(int i=0;i<copied;i++)
     {
      datetime bar_available=bars[i].time+PeriodSeconds(PERIOD_M1);
      if(bar_available<=root.available_at || bar_available>through_at)
         continue;
      if(!BarIntersectsZone(bars[i],root.bottom,root.top))
         continue;
      prior_touch=true;
      first_touch_at=bar_available;
      return true;
     }
   return true;
  }

bool ReconstructQuietStructureThrough(const ENUM_TIMEFRAMES tf,const datetime through_at,V1StructureState &state)
  {
   ResetStructureState(state,tf);
   datetime start_at=0;
   int tf_index=-1;
   for(int k=0;k<V1_TF_COUNT;k++)
      if(g_timeframes[k]==tf)
        { tf_index=k; break; }
   if(tf_index>=0 && g_history_first_date[tf_index]>0)
      start_at=g_history_first_date[tf_index];

   MqlRates bars[];
   ArraySetAsSeries(bars,false);
   ResetLastError();
   int copied=CopyRates(_Symbol,tf,start_at,through_at,bars);
   if(copied<0)
      return false;

   int seconds=PeriodSeconds(tf);
   for(int i=0;i<copied;i++)
     {
      datetime available_at=bars[i].time+seconds;
      if(available_at>through_at)
         continue;
      state.processed_bars++;
      EnsureLegStart(state,bars[i]);
      V1RefinementEvent ignored_event;
      EvaluateLocalRefinementBreak(state,bars[i],available_at,ignored_event);
      UpdateDirectionalRanges(state,bars[i]);
      ConfirmWaveQuiet(state,bars[i],available_at);
      ShiftRecentBars(state,bars[i]);
     }
   return true;
  }

bool SnapshotReactionStates(V1RootReactionTracker &tracker,const datetime contact_at)
  {
   tracker.m30_state=g_structure[2];
   tracker.m15_state=g_structure[3];
   if(!ReconstructQuietStructureThrough(PERIOD_M5,contact_at,tracker.m5_state))
      return false;
   return true;
  }

void StoreWaitingPostContactLineage(const V1RootReactionTracker &tracker)
  {
   V1RefinementLineage lineage;
   lineage.valid=true;
   lineage.root_zone_id=tracker.root_zone_id;
   lineage.final_child_id="";
   lineage.path=tracker.root_zone_id;
   lineage.child_count=0;
   lineage.status=V1_REFINE_ROOT_ONLY_READY;
   lineage.frozen_at=tracker.root_contact_at;
   lineage.snapshot_at=tracker.root_contact_at;
   lineage.stop_reason="ROOT_CONTEXT_READY_CHILD_AUDIT_ONLY";
   lineage.preplan_contact_at=0;
   lineage.root_contact_at=tracker.root_contact_at;
   lineage.root_contact_bar_open=tracker.root_contact_bar_open;
   StoreRefinementLineage(lineage);
  }

void RegisterPostContactRootWatch(const V1SourceZone &root,const datetime snapshot_at,const bool bootstrap_scan)  {
   if(!root.valid || root.kind!=V1_SOURCE_ROOT || root.strategy_state!=V1_SOURCE_ACTIVE || FindRootReactionTrackerByRootId(root.id)>=0)
      return;

   V1RootReactionTracker tracker;
   tracker.valid=true;
   tracker.id=StringFormat("rootwatch:%s:%I64d",root.id,(long)snapshot_at);
   tracker.root_zone_id=root.id;
   tracker.root_tf=root.tf;
   tracker.direction=root.direction;
   tracker.status=V1_ROOT_WATCH_WAITING_CONTACT;
   tracker.watch_started_at=snapshot_at;
   tracker.bootstrap_root=bootstrap_scan;
   tracker.startup_inside_root=false;
   tracker.startup_exit_seen=false;
   tracker.root_contact_at=0;
   tracker.root_contact_bar_open=0;
   tracker.current_parent_zone_id=root.id;
   tracker.final_child_id="";
   tracker.path=root.id;
   tracker.child_count=0;
   tracker.lineage_updated_at=0;
   ResetStructureState(tracker.m30_state,PERIOD_M30);
   ResetStructureState(tracker.m15_state,PERIOD_M15);
   ResetStructureState(tracker.m5_state,PERIOD_M5);

   bool prior_touch=false;
   datetime first_touch=0;
   if(bootstrap_scan)
     {
      if(!RootHadClosedM1TouchAfterAvailability(root,snapshot_at,prior_touch,first_touch))
         tracker.status=V1_ROOT_WATCH_ERROR;
      else if(prior_touch)
         tracker.status=V1_ROOT_WATCH_INELIGIBLE_PRIOR_TOUCH;
     }

   double price=StartupReferencePrice();
   if(tracker.status==V1_ROOT_WATCH_WAITING_CONTACT && price>0.0 && price>=root.bottom && price<=root.top)
     {
      tracker.startup_inside_root=true;
      tracker.startup_exit_seen=false;
     }

   int n=ArraySize(g_root_reactions);
   if(ArrayResize(g_root_reactions,n+1,64)<0)
      return;
   g_root_reactions[n]=tracker;
   g_root_reaction_state_version++;
   if(tracker.status==V1_ROOT_WATCH_WAITING_CONTACT)
      D135AddUniqueIndex(g_waiting_root_reaction_indices,n);

   if(tracker.status==V1_ROOT_WATCH_INELIGIBLE_PRIOR_TOUCH)
     {
      g_root_watches_prior_touch_rejected++;
      LogLine("ROOT_WATCH_SKIPPED",TfName(root.tf),snapshot_at,root.id,
              StringFormat("reason=PRIOR_CLOSED_M1_TOUCH root_available_at=%s first_touch_at=%s bottom=%.10f top=%.10f d122a_fresh_reaction_guard=FAIL Root_strategy_state_remains=ACTIVE consumption_semantics=NOT_GENERALIZED strategy_authority=false",
                           TimeToString(root.available_at,TIME_DATE|TIME_SECONDS),TimeToString(first_touch,TIME_DATE|TIME_SECONDS),root.bottom,root.top));
      return;
     }

   if(tracker.status==V1_ROOT_WATCH_ERROR)
     {
      LogLine("ROOT_WATCH_SKIPPED",TfName(root.tf),snapshot_at,root.id,"reason=UNCONSUMED_AUDIT_ERROR fail_closed=true strategy_authority=false");
      return;
     }

   g_root_watches_created++;
   LogLine("ROOT_WATCH_CREATED",TfName(root.tf),snapshot_at,root.id,
           StringFormat("status=WAITING_CONTACT direction=%s source_reason=%s root_available_at=%s bottom=%.10f top=%.10f bootstrap_root=%s startup_inside_root=%s prior_closed_touch=false d122a_fresh_reaction_guard=PASS consumption_semantics=NOT_GENERALIZED strategy_authority=false map_objective_qualification=PENDING_PRECONTACT_PHASE4B_PLAN",
                        DirectionName(root.direction),root.source_reason,TimeToString(root.available_at,TIME_DATE|TIME_SECONDS),root.bottom,root.top,
                        bootstrap_scan ? "true" : "false",tracker.startup_inside_root ? "true" : "false"));
  }

void EnsurePostContactRootWatches(const datetime snapshot_at,const bool bootstrap_scan)
  {
   for(int i=0;i<ArraySize(g_sources);i++)
     {
      if(!g_sources[i].valid || g_sources[i].kind!=V1_SOURCE_ROOT || g_sources[i].strategy_state!=V1_SOURCE_ACTIVE)
         continue;
      RegisterPostContactRootWatch(g_sources[i],snapshot_at,bootstrap_scan);
     }
  }

void BindPreplannedScenarioToRootContact(const V1SourceZone &root,const MqlRates &bar,const datetime available_at)
  {
   int scenario_index=FindActiveScenarioForRoot(root.id);
   if(scenario_index<0)
     {
      g_root_contacts_without_preplan++;
      LogLine("ROOT_CONTACT_WITHOUT_PREPLAN","M1",available_at,root.id,
              StringFormat("contact_bar_open=%s strategy_source_kind=ROOT reason=NO_ACTIVE_PRECONTACT_MAP_OBJECTIVE_PLAN retrospective_plan_forbidden=true linear_trigger_pipeline=true",TimeToString(bar.time,TIME_DATE|TIME_SECONDS)));
      return;
     }

   if(g_scenarios[scenario_index].frozen_at>=available_at)
     {
      g_root_contacts_without_preplan++;
      g_scenarios[scenario_index].strategy_state=V1_STRATEGY_CANCELED;
      g_scenarios[scenario_index].canceled_at=available_at;
      g_scenarios[scenario_index].cancel_reason="PLAN_NOT_STRICTLY_BEFORE_CONTACT";
      ReleaseRootScenarioOwner(root.id,g_scenarios[scenario_index].id);
      g_scenarios_canceled++;
      LogLine("ROOT_CONTACT_WITHOUT_PREPLAN","M1",available_at,root.id,
              StringFormat("scenario_id=%s plan_frozen_at=%s contact_at=%s reason=PLAN_NOT_STRICTLY_BEFORE_CONTACT fail_closed=true scenario_canceled=true retrospective_plan_forbidden=true linear_trigger_pipeline=true",
                           g_scenarios[scenario_index].id,TimeToString(g_scenarios[scenario_index].frozen_at,TIME_DATE|TIME_SECONDS),TimeToString(available_at,TIME_DATE|TIME_SECONDS)));
      return;
     }

   g_scenarios[scenario_index].source_contact_at=available_at;
   g_scenarios[scenario_index].source_contact_bar_open=bar.time;
   g_scenarios[scenario_index].strategy_state=V1_STRATEGY_WAITING_SWEEP;
   D135AddUniqueIndex(g_waiting_sweep_scenario_indices,scenario_index);
   g_scenario_root_contacts++;

   LogLine("SCENARIO_ROOT_CONTACT_BOUND","M1",available_at,g_scenarios[scenario_index].id,
           StringFormat("root_zone_id=%s strategy_source_id=%s strategy_source_kind=ROOT plan_frozen_at=%s root_contact_at=%s root_contact_bar_open=%s scope=%s direction=%s active_map_tf=%s objective_count=%d state=WAITING_SWEEP child_required=false linear_trigger_pipeline=true next_stage=WAITING_SWEEP",
                        root.id,root.id,TimeToString(g_scenarios[scenario_index].frozen_at,TIME_DATE|TIME_SECONDS),TimeToString(available_at,TIME_DATE|TIME_SECONDS),
                        TimeToString(bar.time,TIME_DATE|TIME_SECONDS),ScenarioScopeName(g_scenarios[scenario_index].scope),DirectionName(g_scenarios[scenario_index].direction),TfName(g_scenarios[scenario_index].active_map_tf),g_scenarios[scenario_index].objective_count));
  }

void ProcessPostContactRootContacts(const MqlRates &bar,const datetime available_at)
  {
   int pos=0;
   while(pos<ArraySize(g_waiting_root_reaction_indices))
     {
      int i=g_waiting_root_reaction_indices[pos];
      if(i<0 || i>=ArraySize(g_root_reactions) ||
         !g_root_reactions[i].valid ||
         g_root_reactions[i].status!=V1_ROOT_WATCH_WAITING_CONTACT)
        {
         D135RemoveIndexValue(g_waiting_root_reaction_indices,i);
         continue;
        }

      int root_index=FindActiveSourceById(g_root_reactions[i].root_zone_id);
      if(root_index<0 || g_sources[root_index].kind!=V1_SOURCE_ROOT)
        {
         InvalidatePostContactRootTracker(g_root_reactions[i].root_zone_id,available_at,"ROOT_NOT_ACTIVE");
         continue;
        }

      V1SourceZone root=g_sources[root_index];
      bool intersects=BarIntersectsZone(bar,root.bottom,root.top);
      if(g_root_reactions[i].startup_inside_root && !g_root_reactions[i].startup_exit_seen)
        {
         if(!intersects)
           {
            g_root_reactions[i].startup_exit_seen=true;
            LogLine("ROOT_WATCH_EXIT","M1",available_at,root.id,
                    StringFormat("bar_open=%s bottom=%.10f top=%.10f later_reentry_armed=true strategy_authority=false",TimeToString(bar.time,TIME_DATE|TIME_SECONDS),root.bottom,root.top));
           }
         pos++;
         continue;
        }

      if(!intersects || available_at<=root.available_at || available_at<=g_root_reactions[i].watch_started_at ||
         (g_execution_epoch_start>0 && available_at<=g_execution_epoch_start))
        { pos++; continue; }

      g_root_reactions[i].status=V1_ROOT_WATCH_READY;
      g_root_reactions[i].root_contact_at=available_at;
      g_root_reactions[i].root_contact_bar_open=bar.time;
      g_root_reactions[i].current_parent_zone_id=root.id;
      g_root_reactions[i].path=root.id;
      g_root_reactions[i].lineage_updated_at=available_at;
      D135RemoveIndexValue(g_waiting_root_reaction_indices,i);
      g_root_reaction_state_version++;
      if(!SnapshotReactionStates(g_root_reactions[i],available_at))
        {
         g_root_reactions[i].status=V1_ROOT_WATCH_ERROR;
         g_root_reaction_state_version++;
         LogLine("ROOT_REACTION_ERROR","M1",available_at,root.id,"reason=M5_STRUCTURE_CONTEXT_RECONSTRUCTION_FAILED fail_closed=true strategy_authority=false");
         continue;
        }
      D135AddUniqueIndex(g_ready_root_reaction_indices,i);

      g_sources[root_index].root_contact_at=available_at;
      g_sources[root_index].root_contact_bar_open=bar.time;
      StoreWaitingPostContactLineage(g_root_reactions[i]);
      BindPreplannedScenarioToRootContact(root,bar,available_at);
      int bound_scenario=FindActiveScenarioForRoot(root.id);
      bool has_preplan=(bound_scenario>=0 && g_scenarios[bound_scenario].source_contact_at==available_at && g_scenarios[bound_scenario].frozen_at<available_at);

      g_root_contacts_observed++;
      g_root_contexts_ready++;
      LogLine("ROOT_CONTEXT_READY","M1",available_at,root.id,
              StringFormat("strategy_source_id=%s strategy_source_kind=ROOT optional_child_observation=ENABLED child_strategy_authority=false entry_geometry=M1_FVG sl_geometry=D134_INPUT_SELECTED root_contact_at=%s strategy_authority=false phase4b_scenario_qualified=%s map_objective_qualification=%s scenario_id=%s linear_trigger_pipeline=true",
                           root.id,TimeToString(available_at,TIME_DATE|TIME_SECONDS),has_preplan ? "true" : "false",
                           has_preplan ? "PRECONTACT_PLAN_FROZEN" : "NO_PRECONTACT_PLAN",has_preplan ? g_scenarios[bound_scenario].id : "NA"));
      LogLine("ROOT_CONTACT_OBSERVED","M1",available_at,root.id,
              StringFormat("direction=%s root_tf=%s root_available_at=%s contact_bar_open=%s bottom=%.10f top=%.10f optional_child_observation_enabled=true child_strategy_authority=false root_remains_strategy_source=true historical_child_authorization=false phase4b_precontact_plan_checked=true linear_trigger_pipeline=true",
                           DirectionName(root.direction),TfName(root.tf),TimeToString(root.available_at,TIME_DATE|TIME_SECONDS),TimeToString(bar.time,TIME_DATE|TIME_SECONDS),root.bottom,root.top));
     }
  }
void TryAddPostContactChildCandidate(const V1RootReactionTracker &tracker,
                                     const V1SourceZone &parent,
                                     const ENUM_TIMEFRAMES child_tf,
                                     const datetime parent_causal_after,
                                     const V1RefinementEvent &event,
                                     const MqlRates &origin_bar,
                                     const string source_reason,
                                     V1ChildCandidate &candidates[])
  {
   if(event.available_at<=parent_causal_after ||
      event.break_bar.time<parent_causal_after ||
      event.meaningful_wave.available_at<=parent_causal_after ||
      event.meaningful_wave.occurred_at<parent_causal_after ||
      origin_bar.time<parent_causal_after)
      return;

   if(event.direction!=tracker.direction || !WaveIntersectsSource(event.meaningful_wave,parent))
      return;

   if(SourcePathHasSessionGap(child_tf,origin_bar.time,event.break_bar.time))
      return;

   V1ChildCandidate candidate;
   ClearChildCandidate(candidate);
   candidate.valid=true;
   candidate.tf=child_tf;
   candidate.direction=event.direction;
   candidate.source_reason=source_reason;
   candidate.bottom=origin_bar.low;
   candidate.top=origin_bar.high;
   candidate.origin_open=origin_bar.open;
   candidate.origin_close=origin_bar.close;
   candidate.origin_time=origin_bar.time;
   candidate.available_at=event.available_at;

   if(source_reason=="FVG_ORIGIN_OB")
     {
      candidate.origin_window_start=origin_bar.time;
      candidate.origin_window_end=origin_bar.time+PeriodSeconds(child_tf)-1;
     }
   else
     {
      candidate.origin_window_start=event.meaningful_wave.origin_window_start;
      candidate.origin_window_end=event.meaningful_wave.origin_window_end;
     }

   CopyWave(event.meaningful_wave,candidate.meaningful_wave);
   candidate.linked_event_type=event.event_type;
   candidate.linked_event_bar_open=event.break_bar.time;
   candidate.linked_event_close=event.break_bar.close;
   candidate.linked_structure_event_id=event.event_id;

   bool contained=(parent.bottom<=candidate.bottom && candidate.top<=parent.top);
   candidate.containment_type=(contained ? "CONTAINED" : "EVENT_ADJACENT");
   AddChildCandidateUnique(candidates,candidate);
  }

string BuildChildId(const V1SourceZone &parent,const V1ChildCandidate &candidate)
  {
   return StringFormat("%s:child:%s:%I64d:%s:parent:%s",
                       TfName(candidate.tf),DirectionName(candidate.direction),(long)candidate.origin_time,
                       candidate.linked_structure_event_id,parent.id);
  }

void CandidateToSourcePreview(const V1SourceZone &parent,
                              const V1SourceZone &root,
                              const V1ChildCandidate &candidate,
                              const datetime root_contact_at,
                              const datetime root_contact_bar_open,
                              V1SourceZone &child)
  {
   child.valid=true;
   child.id=BuildChildId(parent,candidate);
   child.kind=V1_SOURCE_CHILD;
   child.tf=candidate.tf;
   child.direction=candidate.direction;
   child.source_reason=candidate.source_reason;
   child.bottom=candidate.bottom;
   child.top=candidate.top;
   child.origin_open=candidate.origin_open;
   child.origin_close=candidate.origin_close;
   child.origin_index=iBarShift(_Symbol,candidate.tf,candidate.origin_time,true);
   child.origin_time=candidate.origin_time;
   child.occurred_at=candidate.origin_time;
   child.available_at=candidate.available_at;
   child.origin_window_start=candidate.origin_window_start;
   child.origin_window_end=candidate.origin_window_end;
   child.origin_wave_id=candidate.meaningful_wave.id;
   child.meaningful_swing_id=candidate.meaningful_wave.id;
   child.linked_structure_event_id=candidate.linked_structure_event_id;
   child.parent_zone_id=parent.id;
   child.root_zone_id=root.id;
   child.scenario_owner_id="";
   child.regime_research_rejected=false;
   child.containment_type=candidate.containment_type;
   child.linked_event_type=candidate.linked_event_type;
   child.linked_event_bar_open=candidate.linked_event_bar_open;
   child.strategy_state=V1_SOURCE_ACTIVE;
   child.invalidated_at=0;
   child.invalidation_reason="";
   child.root_contact_at=root_contact_at;
   child.root_contact_bar_open=root_contact_bar_open;
  }

void LogChildCreated(const V1SourceZone &child,const datetime lineage_frozen_at)
  {
   string detail=StringFormat(      "kind=CHILD state=ACTIVE direction=%s source_reason=%s parent_zone_id=%s root_zone_id=%s bottom=%.10f top=%.10f origin_open=%.10f origin_close=%.10f origin_time=%s origin_window_start=%s origin_window_end=%s origin_wave_id=%s linked_event_type=%s linked_structure_event_id=%s linked_event_bar_open=%s containment_type=%s child_available_at=%s root_contact_at=%s root_contact_bar_open=%s post_contact=true lineage_frozen_at=%s scenario_owner_id=UNBOUND strategy_authority=false",
      DirectionName(child.direction),child.source_reason,child.parent_zone_id,child.root_zone_id,child.bottom,child.top,
      child.origin_open,child.origin_close,TimeToString(child.origin_time,TIME_DATE|TIME_SECONDS),
      TimeToString(child.origin_window_start,TIME_DATE|TIME_SECONDS),TimeToString(child.origin_window_end,TIME_DATE|TIME_SECONDS),
      child.origin_wave_id,EventName(child.linked_event_type),child.linked_structure_event_id,
      TimeToString(child.linked_event_bar_open,TIME_DATE|TIME_SECONDS),child.containment_type,
      TimeToString(child.available_at,TIME_DATE|TIME_SECONDS),TimeToString(child.root_contact_at,TIME_DATE|TIME_SECONDS),
      TimeToString(child.root_contact_bar_open,TIME_DATE|TIME_SECONDS),TimeToString(lineage_frozen_at,TIME_DATE|TIME_SECONDS));
   LogLine("CHILD_CREATED",TfName(child.tf),lineage_frozen_at,child.id,detail);
  }

bool AddActiveChildSource(const V1SourceZone &child,const datetime lineage_frozen_at)
  {
   if(FindActiveSourceById(child.id)>=0)
      return true;
   int n=ArraySize(g_sources);
   if(ArrayResize(g_sources,n+1,128)<0)
     {
      LogLine("SOURCE_DETECTOR_ERROR",TfName(child.tf),lineage_frozen_at,child.root_zone_id,"reason=CHILD_SOURCE_ARRAY_RESIZE_FAILED");
      return false;
     }
   g_sources[n]=child;
   g_children_created++;
   g_post_contact_child_events++;
   LogChildCreated(g_sources[n],lineage_frozen_at);
   return true;
  }

void StoreRefinementLineage(const V1RefinementLineage &lineage)
  {
   int existing=FindRefinementByRootId(lineage.root_zone_id);
   if(existing>=0)
     { g_refinements[existing]=lineage; return; }
   int n=ArraySize(g_refinements);
   if(ArrayResize(g_refinements,n+1,64)<0)
      return;
   g_refinements[n]=lineage;
  }

void LogPostContactRefinement(const string event_name,const V1RefinementLineage &lineage,const int tracker_status)
  {
   LogLine(event_name,"",lineage.snapshot_at,lineage.root_zone_id,
           StringFormat("status=%s refinement_status=%s child_count=%d final_child_id=%s path=%s root_contact_at=%s root_contact_bar_open=%s frozen_at=%s stop_reason=%s post_contact=true scenario_authority=false linear_trigger_pipeline=ACTIVE_CHILD_INDEPENDENT",
                        RootReactionStatusName(tracker_status),RefinementStatusName(lineage.status),lineage.child_count,
                        lineage.final_child_id=="" ? "NA" : lineage.final_child_id,lineage.path,
                        TimeToString(lineage.root_contact_at,TIME_DATE|TIME_SECONDS),TimeToString(lineage.root_contact_bar_open,TIME_DATE|TIME_SECONDS),
                        TimeToString(lineage.frozen_at,TIME_DATE|TIME_SECONDS),lineage.stop_reason=="" ? "NA" : lineage.stop_reason));
  }

void PublishTrackerLineage(const int tracker_index,const datetime available_at,const string stop_reason,const string event_name)
  {
   if(tracker_index<0 || tracker_index>=ArraySize(g_root_reactions))
      return;
   V1RootReactionTracker tracker=g_root_reactions[tracker_index];
   V1RefinementLineage lineage;
   lineage.valid=true;
   lineage.root_zone_id=tracker.root_zone_id;
   lineage.final_child_id=tracker.final_child_id;
   lineage.path=tracker.path;
   lineage.child_count=tracker.child_count;
   lineage.status=(tracker.status==V1_ROOT_WATCH_INVALIDATED ? V1_REFINE_INVALIDATED : V1_REFINE_ROOT_ONLY_READY);
   lineage.frozen_at=tracker.root_contact_at;
   lineage.snapshot_at=available_at;
   lineage.stop_reason=stop_reason;
   lineage.preplan_contact_at=0;
   lineage.root_contact_at=tracker.root_contact_at;
   lineage.root_contact_bar_open=tracker.root_contact_bar_open;
   StoreRefinementLineage(lineage);
   LogPostContactRefinement(event_name,lineage,tracker.status);
  }

bool OptionalChildObservationSeen(const string observation_id)
  {
   for(int i=0;i<ArraySize(g_optional_child_observation_ids);i++)
      if(g_optional_child_observation_ids[i]==observation_id)
         return true;
   return false;
  }

bool RecordOptionalChildObservation(const V1SourceZone &child,const datetime observed_at)
  {
   if(OptionalChildObservationSeen(child.id))
      return false;
   int n=ArraySize(g_optional_child_observation_ids);
   if(ArrayResize(g_optional_child_observation_ids,n+1,64)<0)
     {
      LogLine("SOURCE_DETECTOR_ERROR",TfName(child.tf),observed_at,child.root_zone_id,"reason=OPTIONAL_CHILD_AUDIT_ID_ARRAY_RESIZE_FAILED");
      return false;
     }
   g_optional_child_observation_ids[n]=child.id;
   g_optional_child_observations++;
   g_post_contact_child_events++;
   LogLine("OPTIONAL_CHILD_OBSERVED",TfName(child.tf),observed_at,child.id,
           StringFormat("audit_only=true strategy_authority=false strategy_source_id=%s strategy_source_kind=ROOT child_direction=%s source_reason=%s bottom=%.10f top=%.10f origin_time=%s child_available_at=%s root_contact_at=%s containment_type=%s linked_structure_event_id=%s entry_authority=false sl_authority=false tp_authority=false cancellation_authority=false",
                        child.root_zone_id,DirectionName(child.direction),child.source_reason,child.bottom,child.top,
                        TimeToString(child.origin_time,TIME_DATE|TIME_SECONDS),TimeToString(child.available_at,TIME_DATE|TIME_SECONDS),
                        TimeToString(child.root_contact_at,TIME_DATE|TIME_SECONDS),child.containment_type,child.linked_structure_event_id));
   return true;
  }

void ProcessReactionStateForTracker(const int tracker_index,
                                    V1StructureState &state,
                                    const ENUM_TIMEFRAMES child_tf,
                                    const MqlRates &bar,
                                    const datetime available_at)
  {
   if(tracker_index<0 || tracker_index>=ArraySize(g_root_reactions))
      return;
   if(g_root_reactions[tracker_index].status!=V1_ROOT_WATCH_READY)
      return;
   if(available_at<=g_root_reactions[tracker_index].root_contact_at)
      return;

   state.processed_bars++;
   EnsureLegStart(state,bar);
   V1RefinementEvent event;
   bool has_event=EvaluateLocalRefinementBreak(state,bar,available_at,event);
   UpdateDirectionalRanges(state,bar);
   ConfirmWaveQuiet(state,bar,available_at);
   ShiftRecentBars(state,bar);

   if(!has_event || !event.valid || event.direction!=g_root_reactions[tracker_index].direction)
      return;

   int root_index=FindActiveSourceById(g_root_reactions[tracker_index].root_zone_id);
   if(root_index<0 || g_sources[root_index].kind!=V1_SOURCE_ROOT)
     {
      InvalidatePostContactRootTracker(g_root_reactions[tracker_index].root_zone_id,available_at,"ROOT_NOT_ACTIVE");
      return;
     }

   V1SourceZone root=g_sources[root_index];
   if(TimeframeHierarchyRank(child_tf)<=TimeframeHierarchyRank(root.tf))
      return;

   datetime causal_after=g_root_reactions[tracker_index].root_contact_at;
   V1ChildCandidate candidates[];
   ArrayResize(candidates,0);

   MqlRates opposite_origin;
   ZeroMemory(opposite_origin);
   if(FindLastOppositeCandleInSwingOrigin(child_tf,event.direction,event.meaningful_wave,opposite_origin))
      TryAddPostContactChildCandidate(g_root_reactions[tracker_index],root,child_tf,causal_after,event,opposite_origin,"LAST_OPPOSITE_OB",candidates);

   MqlRates fvg_origins[];
   int fvg_count=CollectFvgOriginObBars(child_tf,event.direction,event.meaningful_wave,event.break_bar,fvg_origins);
   for(int k=0;k<fvg_count;k++)
      TryAddPostContactChildCandidate(g_root_reactions[tracker_index],root,child_tf,causal_after,event,fvg_origins[k],"FVG_ORIGIN_OB",candidates);

   int newly_recorded=0;
   for(int i=0;i<ArraySize(candidates);i++)
     {
      V1SourceZone child;
      CandidateToSourcePreview(root,root,candidates[i],g_root_reactions[tracker_index].root_contact_at,g_root_reactions[tracker_index].root_contact_bar_open,child);
      if(child.available_at<=g_root_reactions[tracker_index].root_contact_at || child.origin_time<causal_after)
         continue;
      if(RecordOptionalChildObservation(child,available_at))
        {
         newly_recorded++;
         g_root_reactions[tracker_index].child_count++;
         g_root_reactions[tracker_index].final_child_id=child.id;
         g_root_reactions[tracker_index].path+=">"+child.id;
         g_root_reactions[tracker_index].lineage_updated_at=available_at;
        }
     }

   if(newly_recorded>0)
      LogLine("OPTIONAL_CHILD_AUDIT_STATE",TfName(child_tf),available_at,g_root_reactions[tracker_index].root_zone_id,
              StringFormat("new_observations=%d total_observations=%d root_remains_strategy_source=true no_child_gate=true no_child_selection=true entry_geometry=M1_FVG sl_geometry=D134_INPUT_SELECTED",
                           newly_recorded,g_root_reactions[tracker_index].child_count));
  }

void ProcessPostContactChildBar(const int tf_index,const MqlRates &bar,const datetime available_at)
  {
   if(tf_index<2 || tf_index>4)
      return;
   ENUM_TIMEFRAMES child_tf=g_timeframes[tf_index];
   int pos=0;
   while(pos<ArraySize(g_ready_root_reaction_indices))
     {
      int i=g_ready_root_reaction_indices[pos];
      if(i<0 || i>=ArraySize(g_root_reactions) ||
         !g_root_reactions[i].valid ||
         g_root_reactions[i].status!=V1_ROOT_WATCH_READY ||
         g_root_reactions[i].root_contact_at<=0)
        {
         D135RemoveIndexValue(g_ready_root_reaction_indices,i);
         continue;
        }
      if(available_at<=g_root_reactions[i].root_contact_at)
        { pos++; continue; }
      int root_index=FindActiveSourceById(g_root_reactions[i].root_zone_id);
      if(root_index<0 || g_sources[root_index].kind!=V1_SOURCE_ROOT)
        {
         InvalidatePostContactRootTracker(g_root_reactions[i].root_zone_id,available_at,"ROOT_NOT_ACTIVE");
         continue;
        }
      if(TimeframeHierarchyRank(child_tf)<=TimeframeHierarchyRank(g_sources[root_index].tf))
        { pos++; continue; }
      if(tf_index==2)         ProcessReactionStateForTracker(i,g_root_reactions[i].m30_state,child_tf,bar,available_at);
      else if(tf_index==3)
         ProcessReactionStateForTracker(i,g_root_reactions[i].m15_state,child_tf,bar,available_at);
      else
         ProcessReactionStateForTracker(i,g_root_reactions[i].m5_state,child_tf,bar,available_at);
      pos++;
     }
  }

int CountActiveChildren(const ENUM_TIMEFRAMES tf)
  {
   int count=0;
   for(int i=0;i<ArraySize(g_sources);i++)
      if(g_sources[i].valid && g_sources[i].kind==V1_SOURCE_CHILD && g_sources[i].strategy_state==V1_SOURCE_ACTIVE && g_sources[i].tf==tf)
         count++;
   return count;
  }

void LogRefinementSnapshot(const int tf_index,const datetime available_at)
  {
   if(!IsRootTimeframeIndex(tf_index))
      return;
   int ready=0,no_child=0,ambiguous=0,invalidated=0;
   ENUM_TIMEFRAMES root_tf=g_timeframes[tf_index];
   for(int i=0;i<ArraySize(g_refinements);i++)
     {
      if(!g_refinements[i].valid)
         continue;
      int root_index=FindActiveSourceById(g_refinements[i].root_zone_id);
      if(root_index<0 || g_sources[root_index].kind!=V1_SOURCE_ROOT || g_sources[root_index].tf!=root_tf)
         continue;
      if(g_refinements[i].status==V1_REFINE_ROOT_ONLY_READY || g_refinements[i].status==V1_REFINE_READY || g_refinements[i].status==V1_REFINE_STOPPED_AMBIGUOUS)
         ready++;
      else if(g_refinements[i].status==V1_REFINE_NO_CHILD) no_child++;
      else if(g_refinements[i].status==V1_REFINE_AMBIGUOUS_FIRST) ambiguous++;
      else if(g_refinements[i].status==V1_REFINE_INVALIDATED) invalidated++;
     }

   int waiting_contact=0,discovering_child=0,prior_touch_ineligible=0;
   for(int i=0;i<ArraySize(g_root_reactions);i++)
     {
      if(!g_root_reactions[i].valid || g_root_reactions[i].root_tf!=root_tf) continue;
      if(g_root_reactions[i].status==V1_ROOT_WATCH_WAITING_CONTACT) waiting_contact++;
      else if(g_root_reactions[i].status==V1_ROOT_WATCH_DISCOVERING_CHILD) discovering_child++;
      else if(g_root_reactions[i].status==V1_ROOT_WATCH_INELIGIBLE_PRIOR_TOUCH) prior_touch_ineligible++;
     }
   string detail=StringFormat("ready=%d no_child_terminal=%d ambiguous_first=%d invalidated=%d waiting_root_contact=%d discovering_post_contact_child=%d prior_touch_ineligible=%d active_m30_children=%d active_m15_children=%d active_m5_children=%d historical_child_authorization=false child_strategy_authority=false optional_child_audit_only=true linear_trigger_pipeline=ACTIVE_CHILD_INDEPENDENT",
      ready,no_child,ambiguous,invalidated,waiting_contact,discovering_child,prior_touch_ineligible,
      CountActiveChildren(PERIOD_M30),CountActiveChildren(PERIOD_M15),CountActiveChildren(PERIOD_M5));
   LogLine("REFINEMENT_STATE",TfName(root_tf),available_at,"",detail);
  }

void ProcessClosedBar(const int tf_index,const MqlRates &bar,const datetime available_at)
  {
   g_structure[tf_index].processed_bars++;
   if(tf_index==5) ClearD127M1ChochDetection();
   EnsureLegStart(g_structure[tf_index],bar);
   EvaluateLiquidityConsumption(tf_index,bar,available_at);
   EvaluateRootPriceInvalidation(tf_index,bar,available_at);
   EvaluateChildPriceInvalidation(tf_index,bar,available_at);
   if(tf_index==1) EvaluateH1ReversalReference(bar,available_at);
   EvaluateExistingStructureBreaks(tf_index,g_structure[tf_index],bar,available_at);
   UpdateDirectionalRanges(g_structure[tf_index],bar);
   bool new_wave=ConfirmWaveIfAny(g_structure[tf_index],bar,available_at);
   if(tf_index==5) EvaluateD128AM1FvgDetector(g_structure[tf_index],bar,available_at);
   RegisterCurrentExternalLiquidity(tf_index,available_at);
   if(new_wave)
     {
      TryCreateDefendedRangeLiquidity(tf_index,bar,available_at);
     }
   ShiftRecentBars(g_structure[tf_index],bar);
   if(tf_index==2 || tf_index==3 || tf_index==4)
      ProcessPostContactChildBar(tf_index,bar,available_at);
   if(tf_index==5)
     {
      UpdateM1StrategyLiquidityOverlay(bar,available_at);
      ProcessPostContactRootContacts(bar,available_at);
      EvaluateD127M1SweepDetector(bar,available_at);
      ProcessD127ScenarioSweepStage(bar,available_at);
      ProcessD127ScenarioChochStage(bar,available_at);
      ProcessIntegratedExecutionAuthorizationEpoch(available_at);
      PruneD128AM1FvgDetections();
     }
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
   if(!LoadFullRates(PERIOD_H4,h4) || !LoadFullRates(PERIOD_H1,h1) || !LoadFullRates(PERIOD_M30,m30) || !LoadFullRates(PERIOD_M15,m15))
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
   while(true)
     {
      int selected=-1;
      datetime selected_available=0;
      for(int k=0;k<4;k++)
        {
         if(pos[k]>=closed[k]) continue;
         datetime available=0;
         if(k==0) available=HistoricalAvailableAt(h4,pos[k],PeriodSeconds(PERIOD_H4));
         else if(k==1) available=HistoricalAvailableAt(h1,pos[k],PeriodSeconds(PERIOD_H1));
         else if(k==2) available=HistoricalAvailableAt(m30,pos[k],PeriodSeconds(PERIOD_M30));
         else available=HistoricalAvailableAt(m15,pos[k],PeriodSeconds(PERIOD_M15));
         if(available>now) continue;
         if(selected<0 || available<selected_available || (available==selected_available && k<selected))
           { selected=k; selected_available=available; }
        }
      if(selected<0) break;
      if(selected==0) ProcessClosedBar(0,h4[pos[0]++],selected_available);
      else if(selected==1) ProcessClosedBar(1,h1[pos[1]++],selected_available);
      else if(selected==2) ProcessClosedBar(2,m30[pos[2]++],selected_available);
      else ProcessClosedBar(3,m15[pos[3]++],selected_available);
     }
   g_in_bootstrap_replay=false;
   EnsurePostContactRootWatches(now,true);
   RefreshScenarioLayer(now,true);
   g_init_state=V1_INIT_ACTIVE_MAP;
   LogLine("INIT_STATE","",now,"",InitStateName(g_init_state));
   g_init_state=V1_INIT_SOURCE_CONTEXT;
   LogLine("INIT_STATE","",now,"","INTEGRATED_BASELINE_EXECUTION_READY_TESTER_ONLY");
   for(int i=0;i<V1_TF_COUNT;i++)
     {
      g_last_current_open[i]=iTime(_Symbol,g_timeframes[i],0);
      g_cursor_bar_pending[i]=false;
      if(g_last_current_open[i]>0)
        {
         datetime theoretical_close=g_last_current_open[i]+PeriodSeconds(g_timeframes[i]);
         g_cursor_bar_pending[i]=(theoretical_close>now);
        }
      if(g_history_first_date[i]>0)
         LogLine("HISTORY_FIRST_DATE",TfName(g_timeframes[i]),now,"",TimeToString(g_history_first_date[i],TIME_DATE|TIME_SECONDS));
     }
   InitStructureState(4);
   InitStructureState(5);
   g_bootstrap_ready_at=now;
   g_init_state=V1_READY;
   g_bootstrap_finished=true;
   int h4_long_horizon_count=CountActiveLiquidity(PERIOD_H4,V1_LIQ_EXTERNAL_SWING);
   LogLine("INIT_STATE","",g_bootstrap_ready_at,"",
           StringFormat("READY_INTEGRATED_BASELINE_EXECUTION ready_at=%s h4_long_horizon_external=%d active_liquidity_total=%d active_sources=%d root_watches_created=%I64d prior_touch_ineligible=%I64d root_contexts_ready=%I64d scenarios_planned=%I64d phase4b_planning_enabled=true m1_sweep_detector=true scenario_sweep_sequence=true m1_choch_detector=true scenario_choch_sequence=true fvg_authorization=true entry_sl_tp=true tester_pending_execution=true live_execution=false",
                        TimeToString(g_bootstrap_ready_at,TIME_DATE|TIME_SECONDS),h4_long_horizon_count,ArraySize(g_liquidity),ArraySize(g_sources),
                        g_root_watches_created,g_root_watches_prior_touch_rejected,g_root_contexts_ready,g_scenarios_planned));
   for(int i=0;i<4;i++)
     {
      LogStateSnapshot(i,now,"BOOTSTRAP_COMPLETE");
      LogLiquiditySnapshot(i,now);
      LogRootSnapshot(i,now);
      LogRefinementSnapshot(i,now);
     }
   LogMapSnapshot(now,"BOOTSTRAP_COMPLETE",true);
   return true;
  }

bool TryInitialize()
  {
   if(g_bootstrap_finished) return true;
   if(!AllSeriesSynchronized())
     {
      g_init_state=V1_INIT_SYNCING;
      KickHistoryRequests();
      return false;
     }
   if(g_bootstrap_started) return false;
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

void AddRuntimeEvent(V1RuntimeBarEvent &events[],const int tf_index,const MqlRates &bar,const datetime available_at)
  {
   int n=ArraySize(events);
   ArrayResize(events,n+1);
   events[n].tf_index=tf_index;
   events[n].bar=bar;
   events[n].available_at=available_at;
  }

void CollectNewClosedBars(const int tf_index,V1RuntimeBarEvent &events[],const datetime observed_at)
  {   if(observed_at<=0) return;
   ENUM_TIMEFRAMES tf=g_timeframes[tf_index];
   datetime current_open=iTime(_Symbol,tf,0);
   if(current_open<=0) return;
   if(g_last_current_open[tf_index]==0)
     { g_last_current_open[tf_index]=current_open; return; }
   if(current_open<=g_last_current_open[tf_index]) return;
   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   ResetLastError();
   int copied=CopyRates(_Symbol,tf,g_last_current_open[tf_index],current_open,rates);
   if(copied<=1)
     {
      PrintFormat("MentorV1 runtime CopyRates retry tf=%s copied=%d err=%d",TfName(tf),copied,GetLastError());
      return;
     }
   int first_index=(g_cursor_bar_pending[tf_index] ? 0 : 1);
   for(int i=first_index;i<copied-1;i++)
     {
      datetime available=rates[i].time+PeriodSeconds(tf);
      if(available>observed_at) available=observed_at;
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
         bool same_but_lower_priority=(events[j].available_at==key.available_at && events[j].tf_index>key.tf_index);
         if(!later && !same_but_lower_priority) break;
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
   for(int i=0;i<V1_TF_COUNT;i++) CollectNewClosedBars(i,events,observed_at);
   if(ArraySize(events)==0) return;
   SortRuntimeEvents(events);
   datetime group_time=0;
   bool group_pre_m1_authorization_done=false;
   for(int i=0;i<ArraySize(events);i++)
     {
      if(group_time==0 || events[i].available_at!=group_time)
        {
         if(group_time!=0)
           { EnsurePostContactRootWatches(group_time,false); RefreshScenarioLayer(group_time,false); }
         group_time=events[i].available_at;
         group_pre_m1_authorization_done=false;
         datetime d127_m1_bar_open=0;
         for(int j=i;j<ArraySize(events) && events[j].available_at==group_time;j++)
            if(events[j].tf_index==5) { d127_m1_bar_open=events[j].bar.time; break; }
         if(d127_m1_bar_open>0) PrepareD127M1SweepDetectorSnapshot(d127_m1_bar_open);
         else
           {
            ArrayResize(g_m1_sweep_detector_snapshot,0);
            ArrayResize(g_m1_sweep_detections,0);
            g_m1_sweep_detector_bar_open=0;
           }
        }
      if(events[i].tf_index==5 && !group_pre_m1_authorization_done)
        {
         EnsurePostContactRootWatches(group_time,false);
         RefreshScenarioLayer(group_time,false);
         group_pre_m1_authorization_done=true;
        }
      ProcessClosedBar(events[i].tf_index,events[i].bar,events[i].available_at);
     }
   if(group_time!=0)
     { EnsurePostContactRootWatches(group_time,false); RefreshScenarioLayer(group_time,false); }
   ArrayResize(g_m1_sweep_detector_snapshot,0);
   ArrayResize(g_m1_sweep_detections,0);
   g_m1_sweep_detector_bar_open=0;
  }

int OnInit()
  {
   InitializeAllStructureStates();
   if(InpWriteEventCsv)
     {
      g_log_handle=FileOpen(InpEventCsvFile,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_SHARE_READ,',');
      if(g_log_handle!=INVALID_HANDLE)
        {
         if(FileSize(g_log_handle)==0)
            FileWrite(g_log_handle,"observed_at","event","timeframe","available_at","object_id","detail");
         FileSeek(g_log_handle,0,SEEK_END);
        }
      else PrintFormat("MentorV1 failed to open event CSV '%s', err=%d",InpEventCsvFile,GetLastError());
     }
   EventSetTimer(1);
   KickHistoryRequests();
   LogLine("EA_START","",TimeCurrent(),"",
           StringFormat("build=1.92R1L2 property_version=1.00 magic=%I64d phase=REGIME_RESEARCH_V1_LOG_OPTIMIZED_BASELINE_TOGGLE strategy_semantics=D134_EXECUTION_CORE_UNCHANGED fvg_origin_ob_baseline=true sl_model=%s regime_mode=%s event_log_mode=%s same_entry_root_merge=true same_direction_addons=true opposite_direction_coexistence=false hedging_account_required=true account_margin_mode=%I64d tester_execution_only=true live_execution=false",
                        InpMagicNumber,
                        StopLossModelName((int)InpStopLossModel),
                        RegimeResearchModeName(InpRegimeResearchMode),
                        EventLogModeName(InpEventLogMode),
                        AccountInfoInteger(ACCOUNT_MARGIN_MODE)));
   LogLine("REGIME_RESEARCH_VARIANT_START","M30",TimeCurrent(),"",
           StringFormat("mode=%s event_log_mode=%s regime_gate_enabled=%s gate_scope=%s plan_snapshot=true wave_count=12 progression_required=2/3 protected_break_max=1 expansion_required_gt=1.0 expansion_required_only_in_v1_mode=true thresholds_are_not_inputs=true baseline_no_gate_available=true pending_cancel_retry_change=false strategy_core_change=false",
                        RegimeResearchModeName(InpRegimeResearchMode),
                        EventLogModeName(InpEventLogMode),
                        (InpRegimeResearchMode==V1_REGIME_BASELINE_NO_GATE ? "false" : "true"),
                        (InpRegimeResearchMode==V1_REGIME_BASELINE_NO_GATE ? "NONE" : "EXTERNAL_CONTINUATION")));
   if(HasManagedAccountExposure())
     {
      g_init_state=V1_INIT_EXECUTION_RECOVERY_REQUIRED;
      LogLine("INIT_EXECUTION_RECOVERY_REQUIRED","",TimeCurrent(),"","Existing symbol+magic pending/position detected at startup; this build will not guess scenario provenance or submit new exposure");
      return INIT_SUCCEEDED;
     }
   TryInitialize();
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   LogLine("EA_STOP","",TimeCurrent(),"",
           StringFormat("reason=%d init_state=%s active_liquidity=%d liquidity_created=%I64d sweeps=%I64d body_deliveries=%I64d active_sources=%d roots_created=%I64d root_price_invalidated=%I64d root_structure_invalidated=%I64d root_watches_created=%I64d root_watches_prior_touch_rejected=%I64d root_contacts_observed=%I64d root_contexts_ready=%I64d children_created_strategy_sources=%I64d optional_child_observations=%I64d post_contact_child_events=%I64d children_invalidated_strategy_sources=%I64d legacy_refinements_ready=%I64d legacy_refinements_no_child=%I64d legacy_refinements_ambiguous=%I64d reference_touches=%I64d reference_sweeps=%I64d reference_continuations=%I64d permission_opens=%I64d permission_closes=%I64d reversal_permission=%s scenarios_planned=%I64d scenarios_canceled=%I64d scenarios_no_objective=%I64d objective_candidates_frozen=%I64d precontact_root_plans=%I64d scenario_root_contacts=%I64d root_contacts_without_preplan=%I64d m1_sweep_detected=%I64d scenario_sweeps_accepted=%I64d m1_choch_detected=%I64d scenario_choch_accepted=%I64d m1_fvg_detected=%I64d m1_fvg_gap_rejected=%I64d scenario_fvg_candidates=%I64d scenario_fvg_preselection_retests=%I64d scenario_fvg_selected=%I64d scenario_no_causal_fvg=%I64d scenario_ambiguous_fvg=%I64d execution_geometry_ready=%I64d no_r_eligible_objective=%I64d simultaneous_authorization_ambiguous=%I64d exposure_blocked=%I64d execution_infeasible=%I64d order_rejected=%I64d orders_accepted=%I64d positions_filled=%I64d pending_cancellations=%I64d cancel_rejected=%I64d execution_divergences=%I64d positions_closed=%I64d d126_authorized_sweep_events_historical_runtime_dead=%I64d d126_authorized_sweep_pools_historical_runtime_dead=%I64d structural_reaction_created=%I64d source_contacts_superseded_phase4c=%I64d",
                        reason,InitStateName(g_init_state),ArraySize(g_liquidity),g_liquidity_created,g_liquidity_sweeps,g_liquidity_body_deliveries,ArraySize(g_sources),
                        g_roots_created,g_roots_price_invalidated,g_roots_structure_invalidated,g_root_watches_created,g_root_watches_prior_touch_rejected,
                        g_root_contacts_observed,g_root_contexts_ready,g_children_created,g_optional_child_observations,g_post_contact_child_events,g_children_invalidated,
                        g_refinements_ready,g_refinements_no_child,g_refinements_ambiguous,g_reference_touches,g_reference_sweeps,g_reference_continuations,
                        g_permission_opens,g_permission_closes,ReversalPermissionName(g_map.reversal_permission),g_scenarios_planned,g_scenarios_canceled,
                        g_scenarios_no_objective,g_objective_candidates_frozen,g_precontact_root_plans,g_scenario_root_contacts,g_root_contacts_without_preplan,
                        g_m1_sweep_detector_events,g_scenario_sweep_accepts,g_m1_choch_detector_events,g_scenario_choch_accepts,g_m1_fvg_detector_events,
                        g_m1_fvg_gap_rejections,g_scenario_fvg_candidates,g_scenario_fvg_preselection_retests,g_scenario_fvg_selected,g_scenario_no_causal_fvg,
                        g_scenario_ambiguous_fvg,g_execution_geometry_ready,g_no_r_eligible_objective,g_simultaneous_authorization_ambiguous,g_exposure_blocked,
                        g_execution_infeasible,g_order_rejected,g_orders_accepted,g_positions_filled,g_pending_cancellations,g_cancel_rejected,g_execution_divergences,
                        g_positions_closed,g_authorized_sweep_events,g_authorized_sweep_pools,g_structural_reaction_created,g_source_contacts));
   LogLine("REGIME_RESEARCH_STOP_SUMMARY","M30",TimeCurrent(),"",
           StringFormat("mode=%s event_log_mode=%s plan_pass=%I64d plan_reject=%I64d rolling_m30_waves=%d rolling_m30_protected_breaks=%d csv_rows_written=%I64d log_calls_suppressed=%I64d thresholds_are_not_inputs=true baseline_no_gate_available=true strategy_core_change=false",
                        RegimeResearchModeName(InpRegimeResearchMode),
                        EventLogModeName(InpEventLogMode),
                        g_regime_plan_pass,
                        g_regime_plan_reject,
                        ArraySize(g_regime_m30_waves),
                        ArraySize(g_regime_m30_protected_breaks),
                        g_log_rows_written,
                        g_log_rows_suppressed));
   LogLine("D135_STOP_SUMMARY","",TimeCurrent(),"",
           StringFormat("strategy_semantics=D134_UNCHANGED sl_model=%s event_log_mode=%s fvg_origin_ob_baseline=true same_entry_root_merge=true same_direction_addons=true opposite_direction_coexistence=false hedging_account_required=true merged_execution_opportunities=%I64d merged_contributor_branches=%I64d simultaneous_opposite_ambiguous_opportunities=%I64d same_direction_addon_authorized=%I64d opposite_direction_exposure_blocked=%I64d perf_waiting_root=%d perf_ready_root=%d perf_waiting_sweep=%d perf_waiting_trigger=%d perf_waiting_geometry=%d perf_active_execution=%d csv_flush_batch=%d csv_rows_written=%I64d log_calls_suppressed=%I64d strategy_core_change=false research_toggle_extension=true",

                        StopLossModelName((int)InpStopLossModel),
                        EventLogModeName(InpEventLogMode),
                        g_execution_opportunities_merged,
                        g_execution_contributors_merged,
                        g_simultaneous_authorization_ambiguous,
                        g_same_direction_addon_authorized,
                        g_opposite_direction_exposure_blocked,
                        ArraySize(g_waiting_root_reaction_indices),
                        ArraySize(g_ready_root_reaction_indices),
                        ArraySize(g_waiting_sweep_scenario_indices),
                        ArraySize(g_waiting_trigger_scenario_indices),
                        ArraySize(g_waiting_execution_geometry_indices),
                        ArraySize(g_active_execution_scenario_indices),
                        V1_CSV_FLUSH_BATCH,
                        g_log_rows_written,
                        g_log_rows_suppressed));

   if(g_log_handle!=INVALID_HANDLE)
     {
      FileFlush(g_log_handle);
      FileClose(g_log_handle);
      g_log_handle=INVALID_HANDLE;
     }
  }

void OnTimer()
  {
   if(g_init_state==V1_INIT_EXECUTION_RECOVERY_REQUIRED || g_init_state==V1_INIT_ERROR) return;
   if(g_init_state!=V1_READY) TryInitialize();
  }

void OnTick()
  {
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)) return;
   if(g_init_state!=V1_READY)
     {
      if(g_init_state==V1_INIT_EXECUTION_RECOVERY_REQUIRED || g_init_state==V1_INIT_ERROR) return;
      TryInitialize();
      if(g_init_state!=V1_READY) return;
     }
   if(g_execution_epoch_start==0)
     {
      g_execution_epoch_start=(datetime)tick.time;
      LogLine("EXECUTION_EPOCH_START","M1",g_execution_epoch_start,"",
              StringFormat("D135 perf-optimized / D134 semantics unchanged: Root->Sweep->CHoCH->causal widest FVG->same-entry Root merge->%s merged SL->common frozen objective TP; hedging same-direction independent add-ons allowed; opposite-direction coexistence blocked; live execution hard-blocked",
                           StopLossModelName((int)InpStopLossModel)));
     }
   ProcessRuntimeClosedBars((datetime)tick.time);
   ManageIntegratedExecution(tick);
  }

void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result)
  {
   if(g_init_state==V1_READY)
      ReconcileAllManagedExecutions(TimeCurrent(),true);
  }
//+------------------------------------------------------------------+