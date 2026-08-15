//+------------------------------------------------------------------+
//| MentorDeterministicV1EA.mq5                                     |
//| Deterministic Mentor EA V1 - Phase 2 liquidity/sweep core       |
//|                                                                  |
//| Authority:                                                       |
//|   AGENTS.md                                                      |
//|   docs/ea/EA_SPEC.md                                             |
//|                                                                  |
//| Phase 2 intentionally DOES NOT submit orders.                    |
//| Structure/bootstrap is verified. This build adds active liquidity |
//| pools plus physical sweep/body-delivery consumption. Root/source, |
//| M1 execution, and broker-order layers remain disabled.            |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "Mentor deterministic V1 EA - Phase 2 liquidity/sweep core"

//--- execution identity / diagnostics
input long   InpMagicNumber        = 26081601;
input bool   InpWriteEventCsv      = true;
input bool   InpVerboseLog         = false;
input bool   InpLogBootstrapEvents = false;
input string InpEventCsvFile       = "mentor_v1_phase2_events.csv";

// IMPORTANT:
// V1 parity trading volume and broker-order execution are frozen in the spec,
// but are intentionally not active in this Phase 1 structure-only build.

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
  };

struct V1StructureState
  {
   ENUM_TIMEFRAMES tf;
   string          name;
   int             seconds;

   int             trend;
   int             transition_bias;
   datetime        transition_started_at;

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
          event_name=="LIQUIDITY_BODY_DELIVERY");

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
      "reason=%s trend=%s range_low=%.10f range_high=%.10f protected_low=%s protected_high=%s external_low=%s external_high=%s break_reference=%s",
      reason,
      TrendName(g_structure[tf_index].trend),
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
   g_liquidity_created=0;
   g_liquidity_sweeps=0;
   g_liquidity_body_deliveries=0;

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
   string id=StringFormat("%s:structure:%s:%I64d",
                          s.name,
                          EventName(event_type),
                          (long)bar.time);

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
         EnterTransition(s,-1,available_at);
         LogStateSnapshot(tf_index,available_at,"PROTECTED_BREAK");
         return;
        }

      if(s.external_high.valid && bar.close>s.external_high.price)
        {
         V1WaveRef broken;
         CopyWave(s.external_high,broken);
         CopyWave(broken,s.break_reference);

         if(s.correction_low.valid)
            CopyWave(s.correction_low,s.protected_low);

         if(s.protected_low.valid)
            CopyWave(s.protected_low,s.external_low);

         s.range_low=s.protected_low.valid ? s.protected_low.price : s.range_low;
         BuildDeliveryExtreme(s,V1_SIDE_HIGH,bar,available_at,s.external_high);
         s.range_high=s.external_high.price;
         ClearWave(s.correction_low);

         LogStructureEvent(s,V1_EVENT_BOS,1,
                           broken,s.protected_low,bar,available_at);
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
         EnterTransition(s,1,available_at);
         LogStateSnapshot(tf_index,available_at,"PROTECTED_BREAK");
         return;
        }

      if(s.external_low.valid && bar.close<s.external_low.price)
        {
         V1WaveRef broken;
         CopyWave(s.external_low,broken);
         CopyWave(broken,s.break_reference);

         if(s.correction_high.valid)
            CopyWave(s.correction_high,s.protected_high);

         if(s.protected_high.valid)
            CopyWave(s.protected_high,s.external_high);

         s.range_high=s.protected_high.valid ? s.protected_high.price : s.range_high;
         BuildDeliveryExtreme(s,V1_SIDE_LOW,bar,available_at,s.external_low);
         s.range_low=s.external_low.price;
         ClearWave(s.correction_high);

         LogStructureEvent(s,V1_EVENT_BOS,-1,
                           broken,s.protected_high,bar,available_at);
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
         LogStructureEvent(s,V1_EVENT_INITIAL_BOS,1,
                           broken,protected_ref,bar,available_at);
         return;
        }

      if(bar.close<s.neutral_low.price)
        {
         V1WaveRef broken;
         CopyWave(s.neutral_low,broken);
         V1WaveRef protected_ref;
         CopyWave(s.neutral_high,protected_ref);

         PromoteInitialTrend(s,-1,broken,bar,available_at);
         LogStructureEvent(s,V1_EVENT_INITIAL_BOS,-1,
                           broken,protected_ref,bar,available_at);
         return;
        }
     }
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
   g_init_state=V1_INIT_ACTIVE_MAP;
   LogLine("INIT_STATE","",now,"",InitStateName(g_init_state));

   // Phase 2 reconstructs active H4/H1/M30/M15 liquidity on the same causal
   // replay. Root/source ownership is still a later layer, so
   // STRUCTURAL_REACTION remains dormant.
   g_init_state=V1_INIT_SOURCE_CONTEXT;
   LogLine("INIT_STATE","",now,"","PHASE2_LIQUIDITY_READY_ROOT_SOURCE_NOT_YET_ATTACHED");

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
           StringFormat("READY_PHASE2_LIQUIDITY ready_at=%s h4_long_horizon_external=%d active_liquidity_total=%d",
                        TimeToString(g_bootstrap_ready_at,TIME_DATE|TIME_SECONDS),
                        h4_long_horizon_count,
                        ArraySize(g_liquidity)));

   for(int i=0;i<4;i++)
     {
      LogStateSnapshot(i,now,"BOOTSTRAP_COMPLETE");
      LogLiquiditySnapshot(i,now);
     }

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

   for(int i=0;i<ArraySize(events);i++)
     {
      ProcessClosedBar(events[i].tf_index,
                       events[i].bar,
                       events[i].available_at);
     }

   // Frozen architecture point:
   // Scenario/order authorization runs only AFTER all same-timeframe-close
   // structure/liquidity updates. Trading layer is intentionally absent in Phase 2.
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
           StringFormat("build=0.21 property_version=1.00 magic=%I64d phase=LIQUIDITY_CORE",
                        InpMagicNumber));

   // Do not fail initialization just because MT5 is still synchronizing history.
   TryInitialize();
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();

   LogLine("EA_STOP","",TimeCurrent(),"",
           StringFormat("reason=%d init_state=%s active_liquidity=%d created=%I64d sweeps=%I64d body_deliveries=%I64d",
                        reason,
                        InitStateName(g_init_state),
                        ArraySize(g_liquidity),
                        g_liquidity_created,
                        g_liquidity_sweeps,
                        g_liquidity_body_deliveries));

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
              "Phase2 trading disabled; runtime structure/liquidity events start here");
     }

   ProcessRuntimeClosedBars((datetime)tick.time);

   // No trade submission in Phase 2.
  }
//+------------------------------------------------------------------+
