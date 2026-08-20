//+------------------------------------------------------------------+
//| EdgeAuditV1.mqh                                                  |
//| D-142A BASE EDGE AUDIT V1 -- shadow-only stage instrumentation  |
//|                                                                  |
//| STRATEGY AUTHORITY: NONE                                         |
//| This module may observe and log. It may not change a trade.      |
//+------------------------------------------------------------------+

#define V1_EDGE_AUDIT_BUILD       "1.92R1L4"
#define V1_EDGE_AUDIT_PHASE       "BASE_EDGE_AUDIT_V1_STAGE_FORWARD_SHADOW"
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

int            g_edge_handle=INVALID_HANDLE;
bool           g_edge_enabled=false;
long           g_edge_rows=0;
long           g_edge_rows_since_flush=0;
long           g_edge_snapshots=0;
long           g_edge_labels=0;
datetime       g_edge_last_map_sample_at=0;
V1EdgeSnapshot g_edge_active[];

string EdgeAuditStageName(const int stage)
  {
   if(stage==V1_EDGE_STAGE_MAP)          return "MAP";
   if(stage==V1_EDGE_STAGE_PLAN)         return "PLAN";
   if(stage==V1_EDGE_STAGE_ROOT_CONTACT) return "ROOT_CONTACT";
   if(stage==V1_EDGE_STAGE_SWEEP)        return "SWEEP";
   if(stage==V1_EDGE_STAGE_CHOCH)        return "CHOCH";
   if(stage==V1_EDGE_STAGE_FVG)          return "FVG";
   if(stage==V1_EDGE_STAGE_FILL)         return "ACTUAL_FILL";
   return "UNKNOWN";
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

void EdgeAuditWrite(const string event_name,
                    const string stage_name,
                    const datetime observed_at,
                    const datetime stage_at,
                    const string snapshot_id,
                    const string scenario_id,
                    const string scope_name,
                    const int direction,
                    const double reference_price,
                    const int horizon_seconds,
                    const double value1,
                    const double value2,
                    const double value3,
                    const string detail)
  {
   if(!g_edge_enabled || g_edge_handle==INVALID_HANDLE)
      return;

   FileWrite(g_edge_handle,
             TimeToString(observed_at,TIME_DATE|TIME_SECONDS),
             event_name,
             stage_name,
             _Symbol,
             stage_at>0 ? TimeToString(stage_at,TIME_DATE|TIME_SECONDS) : "NA",
             snapshot_id,
             scenario_id,
             scope_name,
             DirectionName(direction),
             reference_price,
             horizon_seconds,
             value1,
             value2,
             value3,
             detail);

   g_edge_rows++;
   g_edge_rows_since_flush++;
   if(g_edge_rows_since_flush>=V1_EDGE_FLUSH_BATCH ||
      event_name=="EDGE_AUDIT_START" ||
      event_name=="EDGE_AUDIT_STOP")
     {
      FileFlush(g_edge_handle);
      g_edge_rows_since_flush=0;
     }
  }

void EdgeAuditResetState()
  {
   if(g_edge_handle!=INVALID_HANDLE)
     {
      FileFlush(g_edge_handle);
      FileClose(g_edge_handle);
     }
   g_edge_handle=INVALID_HANDLE;
   g_edge_enabled=false;
   g_edge_rows=0;
   g_edge_rows_since_flush=0;
   g_edge_snapshots=0;
   g_edge_labels=0;
   g_edge_last_map_sample_at=0;
   ArrayResize(g_edge_active,0);
  }

bool EdgeAuditInit()
  {
   if(!InpEnableEdgeAudit)
      return true;

   ResetLastError();
   g_edge_handle=FileOpen(InpEdgeAuditCsvFile,
                          FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_SHARE_READ,
                          ',');
   if(g_edge_handle==INVALID_HANDLE)
     {
      PrintFormat("EDGE_AUDIT_V1 disabled: cannot open '%s', err=%d. Strategy execution is unchanged.",
                  InpEdgeAuditCsvFile,GetLastError());
      return false;
     }

   if(FileSize(g_edge_handle)==0)
      FileWrite(g_edge_handle,
                "observed_at","event","stage","symbol","stage_at",
                "snapshot_id","scenario_id","scope","direction",
                "reference_price","horizon_seconds","value1","value2",
                "value3","detail");

   FileSeek(g_edge_handle,0,SEEK_END);
   g_edge_enabled=true;

   EdgeAuditWrite("EDGE_AUDIT_START","SYSTEM",TimeCurrent(),0,"","","NONE",0,
                  0.0,0,0.0,0.0,0.0,
                  StringFormat("build=%s phase=%s strategy_authority=false map_sampling=H1_CADENCE stages=MAP|PLAN|ROOT_CONTACT|SWEEP|CHOCH|FVG|ACTUAL_FILL horizons=15M|1H|4H|24H fill_exact_virtual_barriers=DEFERRED_D142B",
                               V1_EDGE_AUDIT_BUILD,V1_EDGE_AUDIT_PHASE));
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

string EdgeAuditScenarioDetail(const int scenario_index,const string extra)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid)
      return "scenario_context=UNAVAILABLE "+extra;

   V1ScenarioPlan p=g_scenarios[scenario_index];
   return StringFormat(
      "active_map_tf=%s map_owner_id=%s h1_trend=%s h1_owner_id=%s m30_trend=%s m30_owner_id=%s reversal_permission=%s root_id=%s root_tf=%s root_bottom=%.10f root_top=%.10f sweep_id=%s sweep_extreme=%.10f choch_id=%s fvg_id=%s fvg_bottom=%.10f fvg_top=%.10f strategy_entry=%.10f strategy_sl=%.10f strategy_tp=%.10f planned_r=%.8f %s",
      TfName(p.active_map_tf),
      p.owner_id=="" ? "NA" : p.owner_id,
      TrendName(p.h1_trend_at_freeze),
      p.h1_owner_id_at_freeze=="" ? "NA" : p.h1_owner_id_at_freeze,
      TrendName(p.m30_trend_at_freeze),
      p.m30_owner_id_at_freeze=="" ? "NA" : p.m30_owner_id_at_freeze,
      ReversalPermissionName(p.reversal_permission_at_freeze),
      p.root_zone_id=="" ? "NA" : p.root_zone_id,
      TfName(p.source_tf),p.source_bottom,p.source_top,
      p.active_sweep_event_id=="" ? "NA" : p.active_sweep_event_id,
      p.active_sweep_extreme,
      p.scenario_choch_event_id=="" ? "NA" : p.scenario_choch_event_id,
      p.selected_fvg_id=="" ? "NA" : p.selected_fvg_id,
      p.selected_fvg_bottom,p.selected_fvg_top,
      p.strategy_entry_price,p.normalized_sl,p.final_objective_price,
      p.final_objective_planned_r,extra);
  }

void EdgeAuditAppendSnapshot(V1EdgeSnapshot &s,const string detail,const bool track_forward)
  {
   EdgeAuditWrite("SNAPSHOT",EdgeAuditStageName(s.stage),s.stage_at,s.stage_at,
                  s.id,s.scenario_id,
                  s.scope==V1_SCOPE_NONE ? "MAP_STATE" : ScenarioScopeName(s.scope),
                  s.direction,s.reference_price,0,0.0,0.0,0.0,detail);
   g_edge_snapshots++;

   if(!track_forward)
      return;

   int n=ArraySize(g_edge_active);
   if(ArrayResize(g_edge_active,n+1,64)<0)
      return;
   g_edge_active[n]=s;
  }

void EdgeAuditOnScenarioStage(const int stage,
                              const int scenario_index,
                              const datetime stage_at,
                              const double reference_price,
                              const string extra)
  {
   if(!g_edge_enabled || stage_at<=0 || reference_price<=0.0 ||
      scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid)
      return;

   V1ScenarioPlan p=g_scenarios[scenario_index];
   V1EdgeSnapshot s;
   s.valid=true;
   s.id=StringFormat("edge:%s:%s:%I64d:%s",_Symbol,EdgeAuditStageName(stage),(long)stage_at,p.id);
   s.stage=stage;
   s.scenario_id=p.id;
   s.scope=p.scope;
   s.direction=p.direction;
   s.stage_at=stage_at;
   s.reference_price=reference_price;
   s.favorable_abs=0.0;
   s.adverse_abs=0.0;
   s.last_close=reference_price;
   s.last_close_at=stage_at;
   s.horizon_mask=0;

   // ACTUAL_FILL occurs at tick time, not necessarily on an M1 boundary.
   // Phase D-142A logs it for joining but does not pretend M1 OHLC gives exact
   // fill-to-horizon or barrier ordering. Exact tick virtuals are D-142B.
   bool track_forward=(stage!=V1_EDGE_STAGE_FILL);
   EdgeAuditAppendSnapshot(s,
      EdgeAuditScenarioDetail(scenario_index,
         "snapshot_contract=SHADOW_ONLY "+extra+
         (track_forward ? " forward_precision=M1_CAUSAL" : " forward_precision=DEFERRED_EXACT_TICK")),
      track_forward);
  }

void EdgeAuditOnMapSample(const datetime available_at,const string sample_reason)
  {
   if(!g_edge_enabled || available_at<=0 || available_at==g_edge_last_map_sample_at)
      return;

   int h1_seconds=PeriodSeconds(PERIOD_H1);
   if(h1_seconds<=0 || ((long)available_at % (long)h1_seconds)!=0)
      return;

   int direction=HighestActiveMapDirection();
   if(direction==0)
      return;

   string map_name=HighestActiveMapName();
   ENUM_TIMEFRAMES map_tf=(map_name=="H1" ? PERIOD_H1 :
                           (map_name=="M30" ? PERIOD_M30 : PERIOD_CURRENT));
   if(map_tf==PERIOD_CURRENT)
      return;

   double price=0.0;
   datetime m1_open=0;
   if(!LatestClosedM1CloseAt(available_at,price,m1_open) || price<=0.0)
      return;
   if(m1_open+PeriodSeconds(PERIOD_M1)!=available_at)
      return;

   string owner=(map_tf==PERIOD_H1 ? g_structure[1].owner_id : g_structure[2].owner_id);
   if(owner=="")
      return;

   V1EdgeSnapshot s;
   s.valid=true;
   s.id=StringFormat("edge:%s:MAP:%I64d:%s:%s",_Symbol,(long)available_at,TfName(map_tf),owner);
   s.stage=V1_EDGE_STAGE_MAP;
   s.scenario_id="MAP:"+TfName(map_tf)+":"+owner;
   s.scope=V1_SCOPE_NONE;
   s.direction=direction;
   s.stage_at=available_at;
   s.reference_price=price;
   s.favorable_abs=0.0;
   s.adverse_abs=0.0;
   s.last_close=price;
   s.last_close_at=available_at;
   s.horizon_mask=0;
   g_edge_last_map_sample_at=available_at;

   EdgeAuditAppendSnapshot(s,
      StringFormat("sample_reason=%s sampling=H1_CADENCE after_complete_timestamp_group=true active_map_tf=%s map_owner_id=%s h1_trend=%s h1_owner_id=%s m30_trend=%s m30_owner_id=%s reversal_permission=%s strategy_authority=false",
                   sample_reason,TfName(map_tf),owner,
                   TrendName(g_structure[1].trend),g_structure[1].owner_id=="" ? "NA" : g_structure[1].owner_id,
                   TrendName(g_structure[2].trend),g_structure[2].owner_id=="" ? "NA" : g_structure[2].owner_id,
                   ReversalPermissionName(g_map.reversal_permission)),true);
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

   EdgeAuditWrite("FORWARD_LABEL",EdgeAuditStageName(s.stage),observed_at,s.stage_at,
                  s.id,s.scenario_id,
                  s.scope==V1_SCOPE_NONE ? "MAP_STATE" : ScenarioScopeName(s.scope),
                  s.direction,s.reference_price,horizon,
                  signed_pct,mfe_pct,mae_pct,
                  StringFormat("horizon=%s target_at=%s end_at=%s end_price=%.10f end_lag_seconds=%I64d timing=%s values=signed_return_pct|mfe_pct|mae_pct",
                               EdgeAuditHorizonName(bit),TimeToString(target,TIME_DATE|TIME_SECONDS),
                               TimeToString(s.last_close_at,TIME_DATE|TIME_SECONDS),s.last_close,lag,timing));
   s.horizon_mask|=bit;
   g_edge_labels++;
  }

void EdgeAuditProcessOneHorizon(V1EdgeSnapshot &s,const int bit,
                                const datetime bar_open,const datetime bar_available)
  {
   if((s.horizon_mask & bit)!=0)
      return;
   datetime target=s.stage_at+EdgeAuditHorizonSeconds(bit);

   // If the next bar opens at/after target, the previous close is the latest
   // causally known price at the target. This handles session gaps without
   // backdating a reopening price.
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
   if(!g_edge_enabled)
      return;

   int i=0;
   while(i<ArraySize(g_edge_active))
     {
      if(!g_edge_active[i].valid)
        {
         EdgeAuditRemoveAt(i);
         continue;
        }

      // Snapshot was not known while a bar that opened before stage_at formed.
      if(g_edge_active[i].stage_at>bar.time)
        {
         i++;
         continue;
        }

      // Gap targets must be resolved against the previous causal close before
      // incorporating the newly opened bar.
      EdgeAuditProcessOneHorizon(g_edge_active[i],1,bar.time,bar.time);
      EdgeAuditProcessOneHorizon(g_edge_active[i],2,bar.time,bar.time);
      EdgeAuditProcessOneHorizon(g_edge_active[i],4,bar.time,bar.time);
      EdgeAuditProcessOneHorizon(g_edge_active[i],8,bar.time,bar.time);

      EdgeAuditUpdateExcursion(g_edge_active[i],bar);

      EdgeAuditProcessOneHorizon(g_edge_active[i],1,bar.time,available_at);
      EdgeAuditProcessOneHorizon(g_edge_active[i],2,bar.time,available_at);
      EdgeAuditProcessOneHorizon(g_edge_active[i],4,bar.time,available_at);
      EdgeAuditProcessOneHorizon(g_edge_active[i],8,bar.time,available_at);

      if(g_edge_active[i].horizon_mask==V1_EDGE_ALL_MASK)
        {
         EdgeAuditRemoveAt(i);
         continue;
        }
      i++;
     }
  }

void EdgeAuditOnActualFill(const int scenario_index,const datetime observed_at)
  {
   if(!g_edge_enabled || scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      !g_scenarios[scenario_index].valid)
      return;
   V1ScenarioPlan p=g_scenarios[scenario_index];
   if(p.fill_price<=0.0)
      return;

   EdgeAuditOnScenarioStage(V1_EDGE_STAGE_FILL,scenario_index,observed_at,p.fill_price,
      StringFormat("actual_fill_at=%s observed_at=%s observation_lag_seconds=%I64d exact_virtual_barriers=DEFERRED_D142B",
                   p.fill_at>0 ? TimeToString(p.fill_at,TIME_DATE|TIME_SECONDS) : "NA",
                   TimeToString(observed_at,TIME_DATE|TIME_SECONDS),
                   p.fill_at>0 ? (long)(observed_at-p.fill_at) : -1));
  }

void EdgeAuditOnTick(const MqlTick &tick)
  {
   // D-142A deliberately performs no tick-level shadow strategy. This hook is
   // retained so D-142B can add exact virtual barriers only after D-142A parity.
   return;
  }

void EdgeAuditDeinit(const int reason)
  {
   if(!g_edge_enabled || g_edge_handle==INVALID_HANDLE)
      return;

   datetime now=TimeCurrent();
   for(int i=0;i<ArraySize(g_edge_active);i++)
     {
      if(!g_edge_active[i].valid)
         continue;
      EdgeAuditWrite("RIGHT_CENSORED",EdgeAuditStageName(g_edge_active[i].stage),now,
                     g_edge_active[i].stage_at,g_edge_active[i].id,g_edge_active[i].scenario_id,
                     g_edge_active[i].scope==V1_SCOPE_NONE ? "MAP_STATE" : ScenarioScopeName(g_edge_active[i].scope),
                     g_edge_active[i].direction,g_edge_active[i].reference_price,0,
                     (double)g_edge_active[i].horizon_mask,0.0,0.0,
                     "value1=completed_horizon_mask unresolved_horizons_not_synthesized=true");
     }

   EdgeAuditWrite("EDGE_AUDIT_STOP","SYSTEM",now,0,"","","NONE",0,0.0,0,
                  (double)g_edge_snapshots,(double)g_edge_labels,(double)ArraySize(g_edge_active),
                  StringFormat("reason=%d rows=%I64d snapshots=%I64d forward_labels=%I64d active_right_censored=%d strategy_authority=false",
                               reason,g_edge_rows,g_edge_snapshots,g_edge_labels,ArraySize(g_edge_active)));
   FileFlush(g_edge_handle);
   FileClose(g_edge_handle);
   g_edge_handle=INVALID_HANDLE;
   g_edge_enabled=false;
  }
//+------------------------------------------------------------------+
