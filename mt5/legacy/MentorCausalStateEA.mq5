//+------------------------------------------------------------------+
//| MentorCausalStateEA.mq5                                        |
//| Deterministic, tester-only implementation of the frozen Mentor  |
//| execution contract. No trade date or reference price fixtures.  |
//+------------------------------------------------------------------+
#property strict
#property version   "1.36"
#property description "Causal Mentor state machine research EA (tester only)"

#include <Trade/Trade.mqh>

enum MentorStage
  {
   STAGE_MAP=0,
   STAGE_SOURCE_TOUCHED=1,
   STAGE_SWEEPED=2,
   STAGE_CHOCH=3,
   STAGE_PENDING=4,
   STAGE_POSITION=5
  };

struct MentorWave
  {
   bool high_side;
   int index;
   int confirmed_index;
   datetime occurred_at;
   datetime available_at;
   double level;
   double wick_low;
   double wick_high;
   bool external;
   datetime rank_available_at;
  };

struct MentorZone
  {
   bool valid;
   bool bullish;
   ENUM_TIMEFRAMES timeframe;
   datetime origin_at;
   datetime available_at;
   datetime break_at;
   double low;
   double high;
   double broken_level;
  };

struct MentorState
  {
   MentorStage stage;
   bool bullish;
   string scope;
   string execution_model;
   string id;
   datetime prepared_at;
   datetime touched_at;
   datetime sweep_at;
   datetime choch_at;
   datetime last_reapproved_at;
   datetime last_map_bar;
   int map_reapprovals;
   double range_low;
   double range_high;
   double equilibrium;
   double objective;
   double source_invalidation;
   double mature_liquidity;
   double sweep_extreme;
   double choch_reference;
   double entry;
   double stop_loss;
   double take_profit;
   MentorZone root;
   MentorZone child;
   MentorZone execution;
  };

input long     InpMagicNumber=26080902;
input datetime InpTradeFrom=D'2025.09.01 00:00';
input datetime InpTradeTo=D'2025.10.01 00:00';
input int      InpHistoryBars=300;
input int      InpRootMaxAgeHours=120;
input int      InpMatureLiquidityMaxAgeMinutes=180;
input int      InpTriggerMaxMinutes=180;
input int      InpMaxPendingMinutes=720;
input double   InpPriceTolerance=0.03;
input int      InpMaxSpreadPoints=0;
input bool     InpWriteAuditCsv=true;

CTrade g_trade;
MentorState g_state;
MentorState g_watches[];
MentorState g_prepared_delivery[2];
string g_seen_touch_keys[];
string g_seen_lineage_keys[];
string g_used_delivery_keys[];
datetime g_last_m1=0;
int g_sequence=0;
MentorZone g_root_cache[6];
MentorZone g_child_cache[6];
MentorZone g_root_pool[];
MentorZone g_child_pool[];
datetime g_root_cache_m15=0;
datetime g_child_cache_m5=0;
int g_owner_direction=0;
int g_higher_direction=0;
bool g_lower_lead_used=false;

string TfName(const ENUM_TIMEFRAMES tf)
  {
   if(tf==PERIOD_H1) return "H1";
   if(tf==PERIOD_M30) return "M30";
   if(tf==PERIOD_M15) return "M15";
   if(tf==PERIOD_M5) return "M5";
   return "M1";
  }

int TfSeconds(const ENUM_TIMEFRAMES tf)
  {
   int value=PeriodSeconds(tf);
   return value>0 ? value : 60;
  }

bool Bull(const MqlRates &bar) { return bar.close>bar.open; }
bool Bear(const MqlRates &bar) { return bar.close<bar.open; }
bool Doji(const MqlRates &bar) { return bar.close==bar.open; }

double NormalizePrice(const double value)
  {
   return NormalizeDouble(value,(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS));
  }

double TickSize()
  {
   double value=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   return value>0.0 ? value : _Point;
  }

double CurrentSpreadPrice()
  {
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)) return 0.0;
   return MathMax(0.0,tick.ask-tick.bid);
  }

double HardBuffer()
  {
   return MathMax(TickSize(),MathMax(CurrentSpreadPrice(),(double)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*_Point));
  }

bool SpreadAllowed()
  {
   if(InpMaxSpreadPoints<=0) return true;
   return (long)SymbolInfoInteger(_Symbol,SYMBOL_SPREAD)<=InpMaxSpreadPoints;
  }

bool GetClosedRates(const ENUM_TIMEFRAMES tf,MqlRates &rates[])
  {
   ArrayFree(rates);
   ArraySetAsSeries(rates,false);
   int requested=InpHistoryBars;
   if(tf==PERIOD_M1) requested=MathMax(requested,9000);
   else if(tf==PERIOD_M5) requested=MathMax(requested,600);
   else if(tf==PERIOD_M15) requested=MathMax(requested,500);
   else if(tf==PERIOD_M30) requested=MathMax(requested,300);
   else if(tf==PERIOD_H1) requested=MathMax(requested,180);
   int copied=CopyRates(_Symbol,tf,1,requested,rates);
   return copied>=30;
  }

bool Contiguous(const MqlRates &rates[],const int left,const int right,const ENUM_TIMEFRAMES tf)
  {
   if(left<0 || right>=ArraySize(rates)) return false;
   for(int i=left+1;i<=right;i++)
      if(rates[i].time-rates[i-1].time!=TfSeconds(tf)) return false;
   return true;
  }

void ResetState(const string reason="")
  {
   if(reason!="" && g_state.id!="")
      PrintFormat("MentorCausal [%s] CANCEL %s",g_state.id,reason);
   ZeroMemory(g_state);
   g_state.stage=STAGE_MAP;
  }

string TouchKey(const MentorZone &root,const MentorZone &child)
  {
   return StringFormat("%s:%I64d:%s:%I64d:%s",TfName(root.timeframe),(long)root.origin_at,
                       TfName(child.timeframe),(long)child.origin_at,root.bullish?"L":"S");
  }

bool TouchKeySeen(const string key)
  {
   for(int i=0;i<ArraySize(g_seen_touch_keys);i++)
      if(g_seen_touch_keys[i]==key) return true;
   return false;
  }

void MarkTouchKeySeen(const string key)
  {
   if(TouchKeySeen(key)) return;
   int size=ArraySize(g_seen_touch_keys);
   ArrayResize(g_seen_touch_keys,size+1);
   g_seen_touch_keys[size]=key;
  }

bool LineageKeySeen(const string key)
  {
   for(int i=0;i<ArraySize(g_seen_lineage_keys);i++)
      if(g_seen_lineage_keys[i]==key) return true;
   return false;
  }

bool DeliveryKeyUsed(const string key)
  {
   for(int i=0;i<ArraySize(g_used_delivery_keys);i++)
      if(g_used_delivery_keys[i]==key) return true;
   return false;
  }

void MarkDeliveryKeyUsed(const string key)
  {
   if(DeliveryKeyUsed(key)) return;
   int size=ArraySize(g_used_delivery_keys);
   ArrayResize(g_used_delivery_keys,size+1);
   g_used_delivery_keys[size]=key;
  }

void MarkLineageKeySeen(const string key)
  {
   if(LineageKeySeen(key)) return;
   int size=ArraySize(g_seen_lineage_keys);
   ArrayResize(g_seen_lineage_keys,size+1);
   g_seen_lineage_keys[size]=key;
  }

void AddWatch(const MentorState &state)
  {
   int size=ArraySize(g_watches);
   ArrayResize(g_watches,size+1);
   g_watches[size]=state;
  }

void RemoveWatch(const int index)
  {
   int size=ArraySize(g_watches);
   if(index<0 || index>=size) return;
   for(int i=index;i<size-1;i++) g_watches[i]=g_watches[i+1];
   ArrayResize(g_watches,size-1);
  }

void ClearWatches()
  {
   ArrayResize(g_watches,0);
  }

void AuditLineageEvent(const string event_name,const MentorZone &root,const MentorZone &child,
                       const datetime known_at,const string detail)
  {
   MentorState observed;
   ZeroMemory(observed);
   observed.stage=STAGE_MAP;
   observed.bullish=root.bullish;
   observed.scope="UNCLASSIFIED";
   observed.id="LINEAGE";
   observed.prepared_at=known_at;
   observed.root=root;
   observed.child=child;
   g_state=observed;
   Audit(event_name,detail);
   ZeroMemory(g_state);
   g_state.stage=STAGE_MAP;
  }

void Audit(const string event_name,const string detail)
  {
   PrintFormat("MentorCausal [%s] %s %s",g_state.id,event_name,detail);
   if(!InpWriteAuditCsv) return;
   string path="trading_journal\\mentor_causal_state_v043.csv";
   bool exists=FileIsExist(path);
   int handle=FileOpen(path,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_SHARE_READ|FILE_SHARE_WRITE,',');
   if(handle==INVALID_HANDLE) return;
   if(!exists)
      FileWrite(handle,"event","scenario_id","tester_time","stage","direction","scope","root_tf","root_time","root_low","root_high","child_tf","child_time","child_low","child_high","objective","entry","sl","tp","detail");
   FileSeek(handle,0,SEEK_END);
   FileWrite(handle,event_name,g_state.id,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),EnumToString(g_state.stage),g_state.bullish?"long":"short",g_state.scope,TfName(g_state.root.timeframe),TimeToString(g_state.root.origin_at,TIME_DATE|TIME_MINUTES),DoubleToString(g_state.root.low,_Digits),DoubleToString(g_state.root.high,_Digits),TfName(g_state.child.timeframe),TimeToString(g_state.child.origin_at,TIME_DATE|TIME_MINUTES),DoubleToString(g_state.child.low,_Digits),DoubleToString(g_state.child.high,_Digits),DoubleToString(g_state.objective,_Digits),DoubleToString(g_state.entry,_Digits),DoubleToString(g_state.stop_loss,_Digits),DoubleToString(g_state.take_profit,_Digits),detail);
   FileClose(handle);
  }

int BuildWaves(const ENUM_TIMEFRAMES tf,const MqlRates &rates[],MentorWave &waves[])
  {
   ArrayResize(waves,0);
   int n=ArraySize(rates);
   int last_wave_index=-1;
   int last_side=0;
   for(int i=2;i<n;i++)
     {
      if(!Contiguous(rates,i-2,i,tf) || Doji(rates[i]) || Doji(rates[i-1]) || Doji(rates[i-2])) continue;
      int side=0;
      if(Bear(rates[i]) && Bear(rates[i-1]) && Bear(rates[i-2]) && last_side!=1) side=1;
      if(Bull(rates[i]) && Bull(rates[i-1]) && Bull(rates[i-2]) && last_side!=-1) side=-1;
      if(side==0) continue;
      int start=last_wave_index+1;
      if(start<0) start=0;
      int extreme=start;
      for(int j=start+1;j<=i;j++)
        {
         if(side==1 && rates[j].high>rates[extreme].high) extreme=j;
         if(side==-1 && rates[j].low<rates[extreme].low) extreme=j;
        }
      int size=ArraySize(waves);
      ArrayResize(waves,size+1);
      waves[size].high_side=(side==1);
      waves[size].index=extreme;
      waves[size].confirmed_index=i;
      waves[size].occurred_at=rates[extreme].time;
      waves[size].available_at=rates[i].time+TfSeconds(tf);
      waves[size].level=side==1 ? rates[extreme].high : rates[extreme].low;
      waves[size].wick_low=side==1 ? MathMax(rates[extreme].open,rates[extreme].close) : rates[extreme].low;
      waves[size].wick_high=side==1 ? rates[extreme].high : MathMin(rates[extreme].open,rates[extreme].close);
      waves[size].external=false;
      waves[size].rank_available_at=0;
      last_wave_index=extreme;
      last_side=side;
     }

   // Rank only waves that become protected structure or extend the active
   // external range. A recent three-colour swing is not external by default.
   int trend=0;
   int latest_high=-1,latest_low=-1;
   int protected_high=-1,protected_low=-1;
   int external_high=-1,external_low=-1;
   double local_high=0.0,local_low=0.0;
   int next_wave=0;
   for(int i=0;i<n;i++)
     {
      datetime available=rates[i].time+TfSeconds(tf);
      if(i>0 && rates[i].time-rates[i-1].time!=TfSeconds(tf) && tf==PERIOD_M1 &&
         rates[i].time-rates[i-1].time>TfSeconds(tf)*4)
        {
         trend=0;
         latest_high=-1; latest_low=-1;
         protected_high=-1; protected_low=-1;
         external_high=-1; external_low=-1;
         local_high=0.0; local_low=0.0;
        }

      double close=rates[i].close;
      if(trend>0)
        {
         if(protected_low>=0 && close<waves[protected_low].level)
           {
            int protected_wave=external_high>=0 ? external_high : latest_high;
            if(protected_wave>=0)
              {
               waves[protected_wave].external=true;
               if(waves[protected_wave].rank_available_at==0) waves[protected_wave].rank_available_at=available;
              }
            trend=-1;
            protected_high=protected_wave; protected_low=-1;
            external_high=protected_wave; external_low=-1;
            local_high=protected_wave>=0 ? waves[protected_wave].level : rates[i].high;
            local_low=rates[i].low;
           }
         else if(external_high>=0 && close>waves[external_high].level)
           {
            double broken_level=waves[external_high].level;
            int protected_wave=latest_low;
            if(protected_wave>=0)
              {
               waves[protected_wave].external=true;
               if(waves[protected_wave].rank_available_at==0) waves[protected_wave].rank_available_at=available;
              }
            trend=1;
            protected_low=protected_wave; protected_high=-1;
            external_low=protected_wave; external_high=-1;
            local_low=protected_wave>=0 ? waves[protected_wave].level : rates[i].low;
            local_high=MathMax(broken_level,rates[i].high);
           }
        }
      else if(trend<0)
        {
         if(protected_high>=0 && close>waves[protected_high].level)
           {
            int protected_wave=external_low>=0 ? external_low : latest_low;
            if(protected_wave>=0)
              {
               waves[protected_wave].external=true;
               if(waves[protected_wave].rank_available_at==0) waves[protected_wave].rank_available_at=available;
              }
            trend=1;
            protected_low=protected_wave; protected_high=-1;
            external_low=protected_wave; external_high=-1;
            local_low=protected_wave>=0 ? waves[protected_wave].level : rates[i].low;
            local_high=rates[i].high;
           }
         else if(external_low>=0 && close<waves[external_low].level)
           {
            double broken_level=waves[external_low].level;
            int protected_wave=latest_high;
            if(protected_wave>=0)
              {
               waves[protected_wave].external=true;
               if(waves[protected_wave].rank_available_at==0) waves[protected_wave].rank_available_at=available;
              }
            trend=-1;
            protected_high=protected_wave; protected_low=-1;
            external_high=protected_wave; external_low=-1;
            local_high=protected_wave>=0 ? waves[protected_wave].level : rates[i].high;
            local_low=MathMin(broken_level,rates[i].low);
           }
        }
      else if(latest_high>=0 && close>waves[latest_high].level)
        {
         int protected_wave=latest_low;
         if(protected_wave>=0)
           {
            waves[protected_wave].external=true;
            if(waves[protected_wave].rank_available_at==0) waves[protected_wave].rank_available_at=available;
           }
         trend=1;
         protected_low=protected_wave; protected_high=-1;
         external_low=protected_wave; external_high=-1;
         local_low=protected_wave>=0 ? waves[protected_wave].level : rates[i].low;
         local_high=rates[i].high;
        }
      else if(latest_low>=0 && close<waves[latest_low].level)
        {
         int protected_wave=latest_high;
         if(protected_wave>=0)
           {
            waves[protected_wave].external=true;
            if(waves[protected_wave].rank_available_at==0) waves[protected_wave].rank_available_at=available;
           }
         trend=-1;
         protected_high=protected_wave; protected_low=-1;
         external_high=protected_wave; external_low=-1;
         local_high=protected_wave>=0 ? waves[protected_wave].level : rates[i].high;
         local_low=rates[i].low;
        }

      while(next_wave<ArraySize(waves) && waves[next_wave].available_at<=available)
        {
         if(waves[next_wave].high_side)
           {
            latest_high=next_wave;
            if(trend>0 && (external_high<0 || waves[next_wave].level>=local_high))
              {
               waves[next_wave].external=true;
               if(waves[next_wave].rank_available_at==0) waves[next_wave].rank_available_at=available;
               external_high=next_wave;
               local_high=waves[next_wave].level;
              }
           }
         else
           {
            latest_low=next_wave;
            if(trend<0 && (external_low<0 || waves[next_wave].level<=local_low))
              {
               waves[next_wave].external=true;
               if(waves[next_wave].rank_available_at==0) waves[next_wave].rank_available_at=available;
               external_low=next_wave;
               local_low=waves[next_wave].level;
              }
           }
         next_wave++;
        }
      if(trend>0) local_high=MathMax(local_high,rates[i].high);
      if(trend<0) local_low=MathMin(local_low,rates[i].low);
     }
   return ArraySize(waves);
  }

int RateIndexAtOrBefore(const MqlRates &rates[],const datetime at)
  {
   for(int i=ArraySize(rates)-1;i>=0;i--)
      if(rates[i].time+60<=at || rates[i].time<=at) return i;
   return -1;
  }

bool ZoneActiveAt(const MentorZone &zone,const datetime at)
  {
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1)) return false;
   int outside=0;
   for(int i=0;i<ArraySize(m1);i++)
     {
      datetime known=m1[i].time+60;
      if(known<=zone.available_at || known>at) continue;
      bool invalid=zone.bullish ? m1[i].close<zone.low : m1[i].close>zone.high;
      outside=invalid ? outside+1 : 0;
      if(outside>=2) return false;
     }
   return true;
  }

bool FindLatestCausalOb(const ENUM_TIMEFRAMES tf,const bool bullish,const datetime known_at,MentorZone &best)
  {
   ZeroMemory(best);
   MentorZone family[];
   CollectCausalObs(tf,bullish,known_at,family);
   for(int i=0;i<ArraySize(family);i++)
      if(!best.valid || family[i].available_at>best.available_at || (family[i].available_at==best.available_at && family[i].high-family[i].low<best.high-best.low)) best=family[i];
   return best.valid;
  }

int CollectCausalObs(const ENUM_TIMEFRAMES tf,const bool bullish,const datetime known_at,MentorZone &output[])
  {
   ArrayResize(output,0);
   MqlRates rates[];
   if(!GetClosedRates(tf,rates)) return 0;
   for(int origin=0;origin<ArraySize(rates);origin++)
     {
      if(!((bullish && Bear(rates[origin])) || (!bullish && Bull(rates[origin])))) continue;
      int confirmation=-1;
      int end=MathMin(ArraySize(rates)-1,origin+8);
      for(int i=origin+1;i<=end;i++)
        {
         if(!Contiguous(rates,i-1,i,tf)) break;
         bool another_opposite=(bullish && Bear(rates[i])) || (!bullish && Bull(rates[i]));
         if(another_opposite) break;
         if((bullish && rates[i].close>rates[origin].high) || (!bullish && rates[i].close<rates[origin].low)) { confirmation=i; break; }
        }
      if(confirmation<0) continue;
      datetime available=rates[confirmation].time+TfSeconds(tf);
      if(available>known_at || known_at-rates[origin].time>InpRootMaxAgeHours*3600) continue;
      bool duplicate=false;
      for(int z=0;z<ArraySize(output);z++)
         if(output[z].origin_at==rates[origin].time) { duplicate=true; break; }
      if(duplicate) continue;
      int size=ArraySize(output);
      ArrayResize(output,size+1);
      output[size].valid=true; output[size].bullish=bullish; output[size].timeframe=tf;
      output[size].origin_at=rates[origin].time; output[size].available_at=available; output[size].break_at=rates[confirmation].time;
      output[size].low=rates[origin].low; output[size].high=rates[origin].high; output[size].broken_level=bullish ? rates[origin].high : rates[origin].low;
     }
   return ArraySize(output);
  }

bool ZonesOverlap(const MentorZone &a,const MentorZone &b)
  {
   return MathMax(a.low,b.low)<=MathMin(a.high,b.high)+InpPriceTolerance;
  }

bool FindCausalChild(const MentorZone &root,const datetime known_at,MentorZone &child)
  {
   ZeroMemory(child);
   ENUM_TIMEFRAMES candidates[3]={PERIOD_M30,PERIOD_M15,PERIOD_M5};
   double distal_tolerance=MathMax(InpPriceTolerance,HardBuffer());
   for(int k=0;k<3;k++)
     {
      ENUM_TIMEFRAMES tf=candidates[k];
      if(TfSeconds(tf)>=TfSeconds(root.timeframe)) continue;
      MentorZone frame_child;
      ZeroMemory(frame_child);
      MentorZone family[];
      CollectCausalObs(tf,root.bullish,known_at,family);
      for(int i=0;i<ArraySize(family);i++)
        {
         MentorZone candidate=family[i];
         if(candidate.origin_at<root.origin_at || candidate.origin_at>=root.available_at) continue;
         if(!ZonesOverlap(root,candidate)) continue;
         // A refinement must preserve or exceed the parent's invalidation-side
         // distal. An interior candle that merely overlaps the parent is not
         // allowed to tighten the scenario stop.
         if(root.bullish && candidate.low>root.low+distal_tolerance) continue;
         if(!root.bullish && candidate.high<root.high-distal_tolerance) continue;
         bool replace=!frame_child.valid;
         if(frame_child.valid && root.bullish)
           {
            if(candidate.low<frame_child.low-InpPriceTolerance) replace=true;
            else if(MathAbs(candidate.low-frame_child.low)<=InpPriceTolerance && candidate.available_at>frame_child.available_at) replace=true;
           }
         if(frame_child.valid && !root.bullish)
           {
            if(candidate.high>frame_child.high+InpPriceTolerance) replace=true;
            else if(MathAbs(candidate.high-frame_child.high)<=InpPriceTolerance && candidate.available_at>frame_child.available_at) replace=true;
           }
         if(replace) frame_child=candidate;
         }
      if(frame_child.valid) { child=frame_child; return true; }
     }
   return false;
  }

void RefreshSourceCache(const datetime known_at)
  {
   MqlRates latest_m15[];
   ArraySetAsSeries(latest_m15,false);
   if(CopyRates(_Symbol,PERIOD_M15,1,1,latest_m15)!=1) return;
   ENUM_TIMEFRAMES roots[3]={PERIOD_M15,PERIOD_M30,PERIOD_H1};
   if(latest_m15[0].time!=g_root_cache_m15)
     {
      g_root_cache_m15=latest_m15[0].time;
      ArrayResize(g_root_pool,0);
      ArrayResize(g_child_pool,0);
      for(int d=0;d<2;d++)
        {
         bool bullish=(d==0);
         for(int k=0;k<3;k++)
           {
            int slot=d*3+k;
            ZeroMemory(g_root_cache[slot]);
            ZeroMemory(g_child_cache[slot]);
            FindLatestCausalOb(roots[k],bullish,known_at,g_root_cache[slot]);
            MentorZone family[];
            CollectCausalObs(roots[k],bullish,known_at,family);
            int first=MathMax(0,ArraySize(family)-200);
            for(int f=first;f<ArraySize(family);f++)
              {
               MentorZone executable_root=family[f];
               MentorZone child;
               if(!FindCausalChild(executable_root,known_at,child)) continue;
               if(child.timeframe==PERIOD_M15)
                 {
                  MentorZone grandchild;
                 if(FindCausalChild(child,known_at,grandchild))
                    {
                     child=grandchild;
                    }
                 }
               int size=ArraySize(g_root_pool);
               ArrayResize(g_root_pool,size+1);
               ArrayResize(g_child_pool,size+1);
               g_root_pool[size]=executable_root;
               g_child_pool[size]=child;
               string lineage_key=TouchKey(executable_root,child);
               if(!LineageKeySeen(lineage_key))
                 {
                  MentorState observed;
                  ZeroMemory(observed);
                  observed.stage=STAGE_MAP;
                  observed.bullish=executable_root.bullish;
                  observed.scope="UNCLASSIFIED";
                  observed.id="LINEAGE";
                  observed.root=executable_root;
                  observed.child=child;
                  g_state=observed;
                  Audit("LINEAGE_DISCOVERED",StringFormat("root_available=%s child_available=%s",
                        TimeToString(executable_root.available_at,TIME_DATE|TIME_MINUTES),
                        TimeToString(child.available_at,TIME_DATE|TIME_MINUTES)));
                  ZeroMemory(g_state);
                  g_state.stage=STAGE_MAP;
                  MarkLineageKeySeen(lineage_key);
                 }
              }
           }
        }
     }
  }

int MapDirectionOnFrame(const ENUM_TIMEFRAMES frame,const datetime known_at,double &range_low,double &range_high)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   if(CopyRates(_Symbol,frame,1,1200,rates)<300) return 0;
   int trend=0;
   bool have_latest_high=false,have_latest_low=false,have_protected_high=false,have_protected_low=false;
   double latest_high=0.0,latest_low=0.0,protected_high=0.0,protected_low=0.0;
   double external_high=0.0,external_low=0.0;
   for(int i=2;i<ArraySize(rates);i++)
     {
       datetime available=rates[i].time+TfSeconds(frame);
       if(available>known_at) break;
       int pivot=i-1;
       if(rates[pivot].high>rates[pivot-1].high && rates[pivot].high>rates[pivot+1].high)
         {
          latest_high=rates[pivot].high;
          have_latest_high=true;
         }
       if(rates[pivot].low<rates[pivot-1].low && rates[pivot].low<rates[pivot+1].low)
         {
          latest_low=rates[pivot].low;
          have_latest_low=true;
         }
       double close=rates[i].close;
       if(trend==0)
         {
          if(have_latest_high && close>latest_high)
            {
             trend=1;
             protected_low=latest_low; have_protected_low=have_latest_low;
             external_high=rates[i].high;
            }
          else if(have_latest_low && close<latest_low)
            {
             trend=-1;
             protected_high=latest_high; have_protected_high=have_latest_high;
             external_low=rates[i].low;
            }
         }
       else if(trend>0)
         {
          if(have_protected_low && close<protected_low)
            {
             trend=-1;
             protected_high=latest_high; have_protected_high=have_latest_high;
             external_low=rates[i].low;
            }
          else if(rates[i].high>external_high)
            {
             external_high=rates[i].high;
             protected_low=latest_low; have_protected_low=have_latest_low;
            }
         }
       else
         {
          if(have_protected_high && close>protected_high)
            {
             trend=1;
             protected_low=latest_low; have_protected_low=have_latest_low;
             external_high=rates[i].high;
            }
          else if(external_low==0.0 || rates[i].low<external_low)
            {
             external_low=rates[i].low;
             protected_high=latest_high; have_protected_high=have_latest_high;
            }
         }
      }
   if(trend>0 && have_protected_low && external_high>protected_low)
     {
      range_low=protected_low; range_high=external_high; return trend;
     }
   if(trend<0 && have_protected_high && protected_high>external_low)
     {
      range_low=external_low; range_high=protected_high; return trend;
     }
   range_low=0.0; range_high=0.0;
   return 0;
  }

bool HasLeadingRootAtRangeEdge(const int direction,const datetime known_at,const double range_low,const double range_high)
  {
   for(int i=ArraySize(g_root_pool)-1;i>=0;i--)
     {
      MentorZone root=g_root_pool[i];
      if(!root.valid || root.bullish!=(direction>0) || root.available_at>known_at) continue;
      bool at_edge=root.bullish ? root.low<=range_low+HardBuffer() : root.high>=range_high-HardBuffer();
      if(!at_edge) continue;
      if(ZoneAtMeaningfulSwing(root,known_at)) return true;
     }
   return false;
  }

int LatestMapDirection(const datetime known_at,double &range_low,double &range_high)
  {
   double m30_low=0.0,m30_high=0.0,m15_low=0.0,m15_high=0.0;
   int m30=MapDirectionOnFrame(PERIOD_M30,known_at,m30_low,m30_high);
   int m15=MapDirectionOnFrame(PERIOD_M15,known_at,m15_low,m15_high);
   if(m30!=0)
     {
      if(g_higher_direction==0)
        {
         g_higher_direction=m30;
         g_owner_direction=m30;
         g_lower_lead_used=false;
        }
      else if(m30!=g_higher_direction)
        {
         g_higher_direction=m30;
         if(m30!=g_owner_direction)
           {
            g_owner_direction=m30;
            g_lower_lead_used=false;
           }
        }
      if(!g_lower_lead_used && m15!=0 && m15!=g_owner_direction && HasLeadingRootAtRangeEdge(m15,known_at,m30_low,m30_high))
        {
         g_owner_direction=m15;
         g_lower_lead_used=true;
        }
      if(g_owner_direction==m15 && g_owner_direction!=m30 && m15_high>m15_low)
        {
         range_low=m15_low; range_high=m15_high;
        }
      else
        {
         range_low=m30_low; range_high=m30_high;
        }
      return g_owner_direction;
     }
   if(m15!=0) { range_low=m15_low; range_high=m15_high; return m15; }
   return MapDirectionOnFrame(PERIOD_H1,known_at,range_low,range_high);
  }

bool LevelConsumed(const bool high_side,const double level,const datetime available_at,const datetime known_at)
  {
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1)) return true;
   for(int i=0;i<ArraySize(m1);i++)
     {
      datetime at=m1[i].time+60;
      if(at<=available_at || at>known_at) continue;
      if(high_side && m1[i].high>level+InpPriceTolerance) return true;
      if(!high_side && m1[i].low<level-InpPriceTolerance) return true;
     }
   return false;
  }

bool RootOwnsStructureBreakOnFrame(const MentorZone &root,const ENUM_TIMEFRAMES frame,const datetime known_at,double &broken_level)
  {
   MqlRates rates[];
   if(!GetClosedRates(frame,rates)) return false;
   MentorWave waves[];
   BuildWaves(frame,rates,waves);
   bool found=false;
   datetime latest_available=0;
   for(int w=0;w<ArraySize(waves);w++)
     {
       if(waves[w].available_at>root.origin_at || waves[w].high_side!=root.bullish) continue;
       bool broken=false;
       for(int i=0;i<ArraySize(rates);i++)
         {
         datetime available=rates[i].time+TfSeconds(frame);
         if(rates[i].time<root.origin_at || available>known_at || available>root.available_at) continue;
         if((root.bullish && rates[i].close>waves[w].level) || (!root.bullish && rates[i].close<waves[w].level))
           {
            broken=true;
            break;
           }
        }
      if(broken && (!found || waves[w].available_at>latest_available))
        {
         found=true;
         latest_available=waves[w].available_at;
         broken_level=waves[w].level;
        }
     }
   return found;
  }

bool RootOwnsStructureBreak(const MentorZone &root,const datetime known_at,double &broken_level)
  {
   ENUM_TIMEFRAMES frames[4]={PERIOD_H1,PERIOD_M30,PERIOD_M15,PERIOD_M5};
   bool found=false;
   double selected=0.0;
   for(int i=0;i<4;i++)
     {
      if(TfSeconds(frames[i])>TfSeconds(root.timeframe)) continue;
      double candidate=0.0;
      if(RootOwnsStructureBreakOnFrame(root,frames[i],known_at,candidate))
        {
         selected=candidate;
         found=true;
        }
     }
   broken_level=selected;
   return found;
  }

bool FindObjective(const bool bullish,const string scope,const double entry,const datetime known_at,double &objective)
  {
   ENUM_TIMEFRAMES frames[5]={PERIOD_H1,PERIOD_M30,PERIOD_M15,PERIOD_M5,PERIOD_M1};
   bool found=false;
   double best=0.0;
   for(int k=0;k<5;k++)
     {
      if(scope=="EXTERNAL_CONTINUATION" && (frames[k]==PERIOD_M5 || frames[k]==PERIOD_M1)) continue;
      MqlRates rates[];
      if(!GetClosedRates(frames[k],rates)) continue;
      MentorWave waves[];
      BuildWaves(frames[k],rates,waves);
      for(int w=0;w<ArraySize(waves);w++)
        {
         if(waves[w].available_at>known_at || waves[w].high_side!=bullish) continue;
         if(scope=="EXTERNAL_CONTINUATION" &&
            (!waves[w].external || waves[w].rank_available_at==0 || waves[w].rank_available_at>known_at)) continue;
         double level=waves[w].level;
         if((bullish && level<=entry) || (!bullish && level>=entry)) continue;
         if(LevelConsumed(waves[w].high_side,level,waves[w].available_at,known_at)) continue;
         if(!found || (bullish && level<best) || (!bullish && level>best)) { best=level; found=true; }
        }
     }
   objective=NormalizePrice(best);
   return found;
  }

bool BarTouches(const MqlRates &bar,const MentorZone &zone)
  {
   return bar.high>=zone.low && bar.low<=zone.high;
  }

bool FirstTouchIsCurrent(const MentorZone &zone,const MqlRates &current)
  {
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1)) return false;
   for(int i=0;i<ArraySize(m1);i++)
     {
      datetime known=m1[i].time+60;
      if(known<=zone.available_at || m1[i].time>current.time) continue;
      if(BarTouches(m1[i],zone)) return m1[i].time==current.time;
     }
   return false;
  }

datetime FirstTouchTime(const MentorZone &zone,const MqlRates &current)
  {
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1)) return 0;
   for(int i=0;i<ArraySize(m1);i++)
     {
      datetime known=m1[i].time+60;
      if(known<=zone.available_at || m1[i].time>current.time) continue;
      if(BarTouches(m1[i],zone)) return m1[i].time;
     }
   return 0;
  }

bool FindMatureSweep(const MqlRates &bar,const datetime known_at,double &liquidity,double &extreme)
  {
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1)) return false;
   int current=ArraySize(m1)-1;
   bool found=false;
   int oldest_breach=current+1;
   datetime oldest_maturity=0;
   int earliest=MathMax(1,current-InpMatureLiquidityMaxAgeMinutes);
   for(int i=earliest;i<=current-2;i++)
     {
      bool low_pivot=m1[i].low<m1[i-1].low && m1[i].low<m1[i+1].low;
      bool high_pivot=m1[i].high>m1[i-1].high && m1[i].high>m1[i+1].high;
      datetime mature_at=m1[i+1].time+60;
      if(mature_at>=bar.time || mature_at<g_state.touched_at) continue;
      if(g_state.bullish && low_pivot)
        {
         int breach=-1;
         double excursion=DBL_MAX;
         double reaction_high=-DBL_MAX;
         for(int j=i+2;j<=current;j++)
           {
            if(m1[j].time<mature_at+60) continue;
            if(breach<0) reaction_high=MathMax(reaction_high,m1[j].high);
            if(m1[j].low<m1[i].low)
              {
               if(breach<0) breach=j;
               excursion=MathMin(excursion,m1[j].low);
              }
           }
         bool recovered=false;
         for(int j=breach;j<current && breach>=0;j++)
            if(m1[j].close>m1[i].low) { recovered=true; break; }
         double pivot_range=m1[i].high-m1[i].low;
         bool mature_reaction=breach>=0 && reaction_high-m1[i].low>=MathMax(HardBuffer()*2.0,pivot_range);
         if(breach>=0 && breach<current && mature_reaction && !recovered &&
            (breach<oldest_breach || (breach==oldest_breach && (oldest_maturity==0 || mature_at<oldest_maturity))))
           {
            liquidity=m1[i].low;
            extreme=excursion;
            oldest_breach=breach;
            oldest_maturity=mature_at;
            found=true;
           }
        }
      if(!g_state.bullish && high_pivot)
        {
         int breach=-1;
         double excursion=-DBL_MAX;
         double reaction_low=DBL_MAX;
         for(int j=i+2;j<=current;j++)
           {
            if(m1[j].time<mature_at+60) continue;
            if(breach<0) reaction_low=MathMin(reaction_low,m1[j].low);
            if(m1[j].high>m1[i].high)
              {
               if(breach<0) breach=j;
               excursion=MathMax(excursion,m1[j].high);
              }
           }
         bool recovered=false;
         for(int j=breach;j<current && breach>=0;j++)
            if(m1[j].close<m1[i].high) { recovered=true; break; }
         double pivot_range=m1[i].high-m1[i].low;
         bool mature_reaction=breach>=0 && m1[i].high-reaction_low>=MathMax(HardBuffer()*2.0,pivot_range);
         if(breach>=0 && breach<current && mature_reaction && !recovered &&
            (breach<oldest_breach || (breach==oldest_breach && (oldest_maturity==0 || mature_at<oldest_maturity))))
           {
            liquidity=m1[i].high;
            extreme=excursion;
            oldest_breach=breach;
            oldest_maturity=mature_at;
            found=true;
           }
        }
     }
   if(!found) return false;
   return g_state.bullish ? bar.close>liquidity : bar.close<liquidity;
  }

bool FindMeaningfulChoch(const MqlRates &bar,const datetime known_at,double &reference,MentorZone &execution)
  {
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1)) return false;
   int current=ArraySize(m1)-1;
   int sweep_index=-1;
   for(int i=current-1;i>=0;i--)
      if(m1[i].time+60<=g_state.sweep_at) { sweep_index=i; break; }
   if(sweep_index<0 || current-sweep_index<3) return false;
   MentorWave waves[];
   BuildWaves(PERIOD_M1,m1,waves);
   int chosen_wave=-1;
   datetime earliest_control=g_state.touched_at-30*60;
   for(int w=0;w<ArraySize(waves);w++)
     {
      if(waves[w].available_at>g_state.sweep_at || waves[w].available_at<earliest_control) continue;
      if(waves[w].high_side!=g_state.bullish) continue;
      if(chosen_wave<0 || waves[w].available_at>waves[chosen_wave].available_at) chosen_wave=w;
     }
   if(chosen_wave<0) return false;
   reference=waves[chosen_wave].level;
   if((g_state.bullish && bar.close<=reference) || (!g_state.bullish && bar.close>=reference)) return false;

   // M1 confirms the reaction, but it cannot promote a micro pivot while the
   // M5 correction that brought price into the POI is still intact.
   MqlRates m5[];
   if(!GetClosedRates(PERIOD_M5,m5)) return false;
   int controlling_pivot=-1;
   datetime earliest_m5_control=g_state.touched_at-30*60;
   for(int i=1;i<ArraySize(m5)-1;i++)
     {
      datetime available_at=m5[i+1].time+TfSeconds(PERIOD_M5);
      if(available_at>g_state.sweep_at || available_at<earliest_m5_control) continue;
      bool pivot=g_state.bullish ? m5[i].high>m5[i-1].high && m5[i].high>m5[i+1].high
                                 : m5[i].low<m5[i-1].low && m5[i].low<m5[i+1].low;
      if(pivot) controlling_pivot=i;
     }
   if(controlling_pivot<0) return false;
   double correction_reference=g_state.bullish ? m5[controlling_pivot].high : m5[controlling_pivot].low;
   if((g_state.bullish && bar.close<=correction_reference) || (!g_state.bullish && bar.close>=correction_reference)) return false;

   int origin=-1;
   for(int i=current-1;i>sweep_index;i--)
     {
      if((g_state.bullish && Bear(m1[i])) || (!g_state.bullish && Bull(m1[i]))) { origin=i; break; }
     }
   if(origin<0) return false;
   ZeroMemory(execution);
   execution.valid=true; execution.bullish=g_state.bullish; execution.timeframe=PERIOD_M1;
   execution.origin_at=m1[origin].time; execution.available_at=known_at; execution.break_at=bar.time;
   execution.low=m1[origin].low; execution.high=m1[origin].high; execution.broken_level=reference;
   return true;
  }

bool HasManagedPosition()
  {
   for(int i=PositionsTotal()-1;i>=0;i--)
      if(PositionGetSymbol(i)==_Symbol && (long)PositionGetInteger(POSITION_MAGIC)==InpMagicNumber) return true;
   return false;
  }

bool HasManagedOrder()
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket>0 && OrderSelect(ticket) && OrderGetString(ORDER_SYMBOL)==_Symbol && (long)OrderGetInteger(ORDER_MAGIC)==InpMagicNumber) return true;
     }
   return false;
  }

void DeleteManagedOrders()
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket>0 && OrderSelect(ticket) && OrderGetString(ORDER_SYMBOL)==_Symbol && (long)OrderGetInteger(ORDER_MAGIC)==InpMagicNumber) g_trade.OrderDelete(ticket);
     }
  }

bool ZoneTouchedAfter(const MentorZone &zone,const datetime after_at,const datetime known_at)
  {
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1)) return true;
   for(int i=0;i<ArraySize(m1);i++)
     {
      datetime available=m1[i].time+60;
      if(available<=after_at || available>=known_at) continue;
      if(BarTouches(m1[i],zone)) return true;
     }
   return false;
  }

bool ZoneAtMeaningfulSwing(const MentorZone &zone,const datetime known_at)
  {
   MqlRates rates[];
   if(!GetClosedRates(zone.timeframe,rates)) return false;
   MentorWave waves[];
   BuildWaves(zone.timeframe,rates,waves);
   bool want_high=!zone.bullish;
   int seconds=TfSeconds(zone.timeframe);
   for(int w=0;w<ArraySize(waves);w++)
     {
      if(waves[w].available_at>known_at || waves[w].high_side!=want_high) continue;
      if(waves[w].occurred_at<zone.origin_at-seconds || waves[w].occurred_at>zone.break_at+seconds) continue;
      if(waves[w].wick_high>=zone.low-InpPriceTolerance && waves[w].wick_low<=zone.high+InpPriceTolerance) return true;
     }
   return false;
  }

bool CrossedMapWave(const MqlRates &bar,const bool bullish,const datetime prepared_at,double &broken_level)
  {
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1) || ArraySize(m1)<2) return false;
   MqlRates previous=m1[ArraySize(m1)-2];
   ENUM_TIMEFRAMES frames[4]={PERIOD_H1,PERIOD_M30,PERIOD_M15,PERIOD_M5};
   bool found=false;
   double best=0.0;
   for(int k=0;k<4;k++)
     {
      MqlRates rates[];
      if(!GetClosedRates(frames[k],rates)) continue;
      MentorWave waves[];
      BuildWaves(frames[k],rates,waves);
      for(int w=0;w<ArraySize(waves);w++)
        {
         if(waves[w].available_at>bar.time || waves[w].high_side!=bullish) continue;
         bool crossed=bullish ? previous.close<=waves[w].level && bar.close>waves[w].level : previous.close>=waves[w].level && bar.close<waves[w].level;
         if(!crossed) continue;
         if(!found || (bullish && waves[w].level>best) || (!bullish && waves[w].level<best))
           {
            found=true;
            best=waves[w].level;
           }
        }
     }
   broken_level=best;
   return found && bar.time+60>prepared_at;
  }

void ClearPrepared(const int index,const string reason,const datetime known_at)
  {
   if(index<0 || index>1 || !g_prepared_delivery[index].root.valid) return;
   g_state=g_prepared_delivery[index];
   Audit("PREPARED_RETIRED",StringFormat("reason=%s at=%s",reason,TimeToString(known_at,TIME_DATE|TIME_MINUTES)));
   ZeroMemory(g_prepared_delivery[index]);
   ZeroMemory(g_state);
   g_state.stage=STAGE_MAP;
  }

void RefreshPreparedDelivery(const MqlRates &bar,const datetime known_at)
  {
   RefreshSourceCache(known_at);
   for(int index=0;index<2;index++)
     {
      if(!g_prepared_delivery[index].root.valid) continue;
      MentorState prepared=g_prepared_delivery[index];
      datetime closed_h1=(datetime)iTime(_Symbol,PERIOD_H1,1);
      if(closed_h1>0 && closed_h1>prepared.last_map_bar)
        {
         prepared.last_map_bar=closed_h1;
         prepared.map_reapprovals++;
         prepared.last_reapproved_at=known_at;
         g_prepared_delivery[index]=prepared;
        }
      bool body_invalid=prepared.bullish ? bar.close<prepared.source_invalidation : bar.close>prepared.source_invalidation;
      if(body_invalid || !ZoneActiveAt(prepared.root,known_at) || !ZoneActiveAt(prepared.child,known_at))
        {
         ClearPrepared(index,"SOURCE_INVALIDATED",known_at);
         continue;
        }
      if(BarTouches(bar,prepared.child))
        {
         ClearPrepared(index,"SOURCE_TOUCHED_REACTION_PATH",known_at);
         continue;
        }
      bool objective_delivered=prepared.bullish ? bar.high>=prepared.objective : bar.low<=prepared.objective;
      if(objective_delivered)
        {
         double replacement=0.0;
         double reference=prepared.bullish ? bar.close+TickSize() : bar.close-TickSize();
         if(FindObjective(prepared.bullish,"EXTERNAL_CONTINUATION",reference,known_at,replacement) &&
            ((prepared.bullish && replacement>bar.close) || (!prepared.bullish && replacement<bar.close)))
           {
            prepared.objective=NormalizePrice(replacement);
            prepared.take_profit=prepared.objective;
            prepared.last_reapproved_at=known_at;
            prepared.touched_at=known_at;
            g_prepared_delivery[index]=prepared;
            g_state=prepared;
            Audit("PREPARED_OBJECTIVE_REMAPPED",StringFormat("objective=%.2f",replacement));
            ZeroMemory(g_state); g_state.stage=STAGE_MAP;
           }
         else ClearPrepared(index,"OBJECTIVE_DELIVERED_NO_SUCCESSOR",known_at);
        }
      if(g_prepared_delivery[index].root.valid)
        {
         double broken_level=0.0;
         if(CrossedMapWave(bar,g_prepared_delivery[index].bullish,g_prepared_delivery[index].prepared_at,broken_level))
           {
            g_prepared_delivery[index].touched_at=known_at;
            g_prepared_delivery[index].last_reapproved_at=known_at;
            g_state=g_prepared_delivery[index];
            Audit("DELIVERY_OWNER_CONFIRMED",StringFormat("broken_map_wave=%.2f",broken_level));
            ZeroMemory(g_state); g_state.stage=STAGE_MAP;
           }
        }
     }

   for(int slot=0;slot<ArraySize(g_root_pool);slot++)
     {
      MentorZone root=g_root_pool[slot];
      MentorZone child=g_child_pool[slot];
      if(!root.valid || !child.valid) continue;
      datetime ready_at=root.available_at>child.available_at ? root.available_at : child.available_at;
      if(ready_at<InpTradeFrom || ready_at>known_at || known_at-ready_at>InpRootMaxAgeHours*3600) continue;
      if(!ZoneActiveAt(root,known_at) || !ZoneActiveAt(child,known_at)) continue;
      if(ZoneTouchedAfter(child,ready_at,known_at) || BarTouches(bar,child)) continue;
      if(!ZoneAtMeaningfulSwing(root,known_at) && !ZoneAtMeaningfulSwing(child,known_at)) continue;
      double reference=root.bullish ? child.high : child.low;
      double objective=0.0;
      double current_range_low=0.0,current_range_high=0.0;
      int current_map=LatestMapDirection(known_at,current_range_low,current_range_high);
      if(current_map==0 || !(current_range_high>current_range_low)) continue;
      double map_eq=(current_range_low+current_range_high)/2.0;
      double root_midpoint=(root.low+root.high)/2.0;
      if((root.bullish && root_midpoint>map_eq) || (!root.bullish && root_midpoint<map_eq)) continue;
      if(!FindObjective(root.bullish,"EXTERNAL_CONTINUATION",reference,known_at,objective)) continue;
      if((root.bullish && objective<=reference) || (!root.bullish && objective>=reference)) continue;
      double range_low=root.bullish ? MathMin(root.low,child.low) : objective;
      double range_high=root.bullish ? objective : MathMax(root.high,child.high);
      double midpoint=(root.low+root.high)/2.0;
      double eq=(range_low+range_high)/2.0;
      if((root.bullish && midpoint>eq) || (!root.bullish && midpoint<eq)) continue;
      int index=root.bullish ? 0 : 1;
      bool replace=!g_prepared_delivery[index].root.valid;
      if(!replace)
        {
         MentorState current=g_prepared_delivery[index];
         bool more_external=root.bullish ? MathMin(root.low,child.low)<current.source_invalidation : MathMax(root.high,child.high)>current.source_invalidation;
         replace=more_external;
        }
      if(!replace) continue;
      if(g_prepared_delivery[index].root.valid) ClearPrepared(index,"SUPERSEDED_BY_EXTERNAL_SOURCE",known_at);
      MentorState prepared;
      ZeroMemory(prepared);
      g_sequence++;
      prepared.stage=STAGE_MAP;
      prepared.bullish=root.bullish;
      prepared.scope="EXTERNAL_CONTINUATION";
      prepared.execution_model="DELIVERY_FVG_REPLACEMENT";
      prepared.id=StringFormat("MCS-%03d-%s",g_sequence,root.bullish?"L":"S");
      prepared.prepared_at=known_at;
      prepared.last_reapproved_at=known_at;
      prepared.last_map_bar=(datetime)iTime(_Symbol,PERIOD_H1,1);
      prepared.map_reapprovals=0;
      prepared.range_low=range_low; prepared.range_high=range_high; prepared.equilibrium=eq;
      prepared.objective=NormalizePrice(objective); prepared.take_profit=prepared.objective;
      prepared.root=root; prepared.child=child;
      prepared.source_invalidation=root.bullish ? MathMin(root.low,child.low) : MathMax(root.high,child.high);
      g_prepared_delivery[index]=prepared;
      g_state=prepared;
      Audit("DELIVERY_LINEAGE_PREPARED",StringFormat("range=%.2f..%.2f objective=%.2f",range_low,range_high,objective));
      ZeroMemory(g_state); g_state.stage=STAGE_MAP;
     }
  }

bool FindFreshDeliveryFvg(const MqlRates &m1[],MentorZone &fvg,MentorZone &causal_ob,double &protected_level)
  {
   ZeroMemory(fvg);
   ZeroMemory(causal_ob);
   int current=ArraySize(m1)-1;
   if(current<10 || !Contiguous(m1,current-2,current,PERIOD_M1)) return false;
   bool bullish=m1[current].low>m1[current-2].high+InpPriceTolerance;
   bool bearish=m1[current].high<m1[current-2].low-InpPriceTolerance;
   if(!bullish && !bearish) return false;
   if(bullish && m1[current].close<=m1[current-1].high) return false;
   if(bearish && m1[current].close>=m1[current-1].low) return false;

   int origin=-1;
   for(int i=current-1;i>=MathMax(1,current-8);i--)
     {
      if((bullish && Bear(m1[i])) || (bearish && Bull(m1[i]))) { origin=i; break; }
     }
   if(origin<0) return false;

   fvg.valid=true;
   fvg.bullish=bullish;
   fvg.timeframe=PERIOD_M1;
   fvg.origin_at=m1[current].time;
   fvg.available_at=m1[current].time+60;
   fvg.break_at=m1[current].time;
   fvg.low=bullish ? m1[current-2].high : m1[current].high;
   fvg.high=bullish ? m1[current].low : m1[current-2].low;

   causal_ob.valid=true;
   causal_ob.bullish=bullish;
   causal_ob.timeframe=PERIOD_M1;
   causal_ob.origin_at=m1[origin].time;
   causal_ob.available_at=fvg.available_at;
   causal_ob.break_at=m1[current].time;
   causal_ob.low=m1[origin].low;
   causal_ob.high=m1[origin].high;

   if(bullish)
     {
      protected_level=m1[origin].low;
      for(int i=MathMax(1,origin-5);i<=origin;i++) protected_level=MathMin(protected_level,m1[i].low);
     }
   else
     {
      protected_level=m1[origin].high;
      for(int i=origin;i<current;i++) protected_level=MathMax(protected_level,m1[i].high);
     }
   return true;
  }

bool DiscoverDeliveryReplacement(const MqlRates &bar,const datetime known_at)
  {
   if(HasManagedOrder() || HasManagedPosition() || !SpreadAllowed()) return false;
   MqlRates m1[];
   if(!GetClosedRates(PERIOD_M1,m1)) return false;
   MentorZone fvg,causal_ob;
   double protected_level=0.0;
   if(!FindFreshDeliveryFvg(m1,fvg,causal_ob,protected_level)) return false;

   int prepared_index=fvg.bullish ? 0 : 1;
   if(!g_prepared_delivery[prepared_index].root.valid) return false;
   MentorState prepared=g_prepared_delivery[prepared_index];
   double owner_range_low=0.0,owner_range_high=0.0;
   int owner_direction=LatestMapDirection(known_at,owner_range_low,owner_range_high);
   if(owner_direction!=(fvg.bullish?1:-1)) return false;
   MentorZone best_root=prepared.root;
   MentorZone best_child=prepared.child;
   if(best_root.bullish!=fvg.bullish || best_root.available_at>=fvg.available_at || best_child.available_at>=fvg.available_at) return false;
   if(prepared.map_reapprovals<2 || prepared.touched_at==0 || fvg.available_at<prepared.touched_at) return false;
   if(fvg.bullish && bar.close<=best_child.high) return false;
   if(!fvg.bullish && bar.close>=best_child.low) return false;
   string delivery_key=TouchKey(best_root,best_child);
   if(DeliveryKeyUsed(delivery_key)) return false;

   double entry=fvg.bullish ? fvg.high : fvg.low;
   // A delivery replacement is not the source's initial impulse FVG. Price
   // must already have delivered through the frozen source-to-objective EQ;
   // otherwise the original OB reaction remains the only permitted path.
   if((fvg.bullish && entry<=prepared.equilibrium) || (!fvg.bullish && entry>=prepared.equilibrium)) return false;
   if(fvg.high-fvg.low<HardBuffer()) return false;
   double objective=0.0;
   objective=prepared.objective;
   if((fvg.bullish && objective<=entry) || (!fvg.bullish && objective>=entry)) return false;
   double source_mid=(best_root.low+best_root.high)/2.0;
   double range_low=fvg.bullish ? MathMin(best_root.low,best_child.low) : objective;
   double range_high=fvg.bullish ? objective : MathMax(best_root.high,best_child.high);
   double eq=(range_low+range_high)/2.0;
   if((fvg.bullish && source_mid>eq) || (!fvg.bullish && source_mid<eq)) return false;

   MentorState replacement;
   ZeroMemory(replacement);
   g_sequence++;
   replacement.stage=STAGE_CHOCH;
   replacement.bullish=fvg.bullish;
   replacement.scope="EXTERNAL_CONTINUATION";
   replacement.execution_model="DELIVERY_FVG_REPLACEMENT";
   replacement.id=StringFormat("MCS-%03d-%s",g_sequence,fvg.bullish?"L":"S");
   replacement.prepared_at=prepared.prepared_at;
   replacement.touched_at=known_at;
   replacement.choch_at=known_at;
   replacement.last_reapproved_at=known_at;
   replacement.range_low=range_low;
   replacement.range_high=range_high;
   replacement.equilibrium=eq;
   replacement.objective=objective;
   replacement.take_profit=NormalizePrice(objective);
   replacement.root=best_root;
   replacement.child=best_child;
   replacement.execution=fvg;
   replacement.entry=NormalizePrice(entry);
   replacement.source_invalidation=protected_level;
   double invalidation=fvg.bullish ? MathMin(protected_level,causal_ob.low) : MathMax(protected_level,causal_ob.high);
   replacement.stop_loss=NormalizePrice(fvg.bullish ? invalidation-HardBuffer() : invalidation+HardBuffer());
   bool geometry=fvg.bullish ? replacement.stop_loss<replacement.entry && replacement.entry<replacement.take_profit : replacement.take_profit<replacement.entry && replacement.entry<replacement.stop_loss;
   if(!geometry) return false;

   g_state=replacement;
   Audit("DELIVERY_REPLACEMENT_ARMED",StringFormat("fvg=%.2f..%.2f causal_ob=%.2f..%.2f protected=%.2f",fvg.low,fvg.high,causal_ob.low,causal_ob.high,protected_level));
   if(!SendPending())
     {
      ZeroMemory(g_state);
      g_state.stage=STAGE_MAP;
      return false;
     }
   MarkDeliveryKeyUsed(delivery_key);
   ZeroMemory(g_prepared_delivery[prepared_index]);
   ClearWatches();
   return true;
  }

int DiscoverTouches(const MqlRates &bar,const datetime known_at)
  {
   if(HasManagedOrder() || HasManagedPosition() || !SpreadAllowed()) return 0;
   RefreshSourceCache(known_at);
   double range_low=0.0,range_high=0.0;
   int map=LatestMapDirection(known_at,range_low,range_high);
   double m30_low=0.0,m30_high=0.0;
   int m30_map=MapDirectionOnFrame(PERIOD_M30,known_at,m30_low,m30_high);
   if(map==0 || !(range_high>range_low)) return 0;
   int added=0;
   for(int slot=0;slot<ArraySize(g_root_pool);slot++)
     {
      MentorZone root=g_root_pool[slot];
      MentorZone child=g_child_pool[slot];
      if(!root.valid || !child.valid || !BarTouches(bar,child)) continue;
      string key=TouchKey(root,child);
      if(TouchKeySeen(key)) continue;
      if(!FirstTouchIsCurrent(child,bar))
        {
         datetime first_touch=FirstTouchTime(child,bar);
         AuditLineageEvent("TOUCH_STALE",root,child,known_at,StringFormat("first_touch=%s current=%s",
               TimeToString(first_touch,TIME_DATE|TIME_MINUTES),TimeToString(bar.time,TIME_DATE|TIME_MINUTES)));
         MarkTouchKeySeen(key);
         continue;
        }
      MarkTouchKeySeen(key);
      if(!ZoneActiveAt(root,known_at) || !ZoneActiveAt(child,known_at))
        {
         AuditLineageEvent("TOUCH_REJECTED",root,child,known_at,"SOURCE_NOT_ACTIVE");
         continue;
        }
      bool bullish=root.bullish;
      double eq=(range_low+range_high)/2.0;
      double midpoint=(root.low+root.high)/2.0;
      double owned_break=0.0;
      bool root_owns_break=RootOwnsStructureBreak(root,known_at,owned_break);
      if(!root_owns_break)
        {
         AuditLineageEvent("TOUCH_REJECTED",root,child,known_at,"ROOT_DOES_NOT_OWN_STRUCTURE_BREAK");
         continue;
        }
      if(!ZoneAtMeaningfulSwing(root,known_at) && !ZoneAtMeaningfulSwing(child,known_at))
        {
         AuditLineageEvent("TOUCH_REJECTED",root,child,known_at,"SOURCE_NOT_AT_MEANINGFUL_SWING");
         continue;
        }
      string scope=map==(bullish?1:-1) ? "EXTERNAL_CONTINUATION" : "INTERNAL_ROTATION";
      double range_width=range_high-range_low;
      if(scope=="INTERNAL_ROTATION")
        {
         bool at_external_edge=bullish ? midpoint<=range_low+range_width*0.20 : midpoint>=range_high-range_width*0.20;
         if(!at_external_edge)
           {
            AuditLineageEvent("TOUCH_REJECTED",root,child,known_at,StringFormat("INTERNAL_NOT_AT_EDGE map=%s range=%.2f..%.2f midpoint=%.2f",map>0?"long":"short",range_low,range_high,midpoint));
            continue;
           }
        }
      double objective=0.0;
      double reference=bullish ? child.high : child.low;
      if(scope=="EXTERNAL_CONTINUATION")
        {
         if(!FindObjective(bullish,scope,reference,known_at,objective) ||
            (bullish && objective<=reference) || (!bullish && objective>=reference))
           {
            AuditLineageEvent("TOUCH_REJECTED",root,child,known_at,StringFormat("NO_EXTERNAL_OBJECTIVE objective=%.2f reference=%.2f owned_break=%.2f",objective,reference,owned_break));
            continue;
           }
         if((bullish && midpoint>eq) || (!bullish && midpoint<eq))
           {
            AuditLineageEvent("TOUCH_REJECTED",root,child,known_at,StringFormat("WRONG_SCENARIO_PD_HALF map=%s eq=%.2f midpoint=%.2f broad_m30=%s %.2f..%.2f",map>0?"long":"short",eq,midpoint,m30_map>0?"long":m30_map<0?"short":"flat",m30_low,m30_high));
            continue;
           }
        }
      else if(!FindObjective(bullish,scope,reference,known_at,objective))
        {
         AuditLineageEvent("TOUCH_REJECTED",root,child,known_at,"NO_INTERNAL_OBJECTIVE");
         continue;
        }
      MentorState watch;
      ZeroMemory(watch);
      g_sequence++;
      watch.stage=STAGE_SOURCE_TOUCHED;
      watch.bullish=bullish;
      watch.scope=scope;
      watch.id=StringFormat("MCS-%03d-%s",g_sequence,bullish?"L":"S");
      watch.prepared_at=known_at;
      watch.touched_at=known_at;
      watch.last_reapproved_at=known_at;
      watch.range_low=range_low;
      watch.range_high=range_high;
      watch.equilibrium=eq;
      watch.objective=objective;
      watch.take_profit=objective;
      watch.root=root;
      watch.child=child;
      watch.source_invalidation=bullish ? MathMin(root.low,child.low) : MathMax(root.high,child.high);
      g_state=watch;
      Audit("SOURCE_TOUCHED",StringFormat("map=%s range=%.2f..%.2f eq=%.2f",map>0?"long":"short",range_low,range_high,eq));
      bool duplicate_child=false;
      for(int w=0;w<ArraySize(g_watches);w++)
        {
         if(g_watches[w].bullish!=watch.bullish || g_watches[w].child.origin_at!=watch.child.origin_at || g_watches[w].child.timeframe!=watch.child.timeframe) continue;
         if(TfSeconds(g_watches[w].root.timeframe)<=TfSeconds(watch.root.timeframe)) duplicate_child=true;
        }
      if(!duplicate_child) AddWatch(g_state);
      ZeroMemory(g_state);
      g_state.stage=STAGE_MAP;
      added++;
     }
   return added;
  }

bool ScenarioInvalidated(const MqlRates &bar,const datetime known_at,string &reason)
  {
   if(g_state.bullish && bar.close<g_state.source_invalidation) { reason="SOURCE_BODY_INVALIDATION"; return true; }
   if(!g_state.bullish && bar.close>g_state.source_invalidation) { reason="SOURCE_BODY_INVALIDATION"; return true; }
   if((g_state.bullish && bar.high>=g_state.objective) || (!g_state.bullish && bar.low<=g_state.objective)) { reason="OBJECTIVE_DELIVERED"; return true; }
   if(g_state.stage>=STAGE_SWEEPED && known_at-g_state.sweep_at>InpTriggerMaxMinutes*60) { reason="TRIGGER_EPISODE_ENDED"; return true; }
   if(g_state.stage==STAGE_PENDING && known_at-g_state.choch_at>InpMaxPendingMinutes*60) { reason="PENDING_NOT_REAPPROVED"; return true; }
   return false;
  }

bool SendPending()
  {
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)) return false;
   double volume=MathMax(0.01,SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN));
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_owner_direction=0;
   g_higher_direction=0;
   g_lower_lead_used=false;
   g_trade.SetDeviationInPoints(30);
   bool sent=false;
   if(g_state.bullish)
     {
      if(g_state.entry>tick.ask) sent=g_trade.BuyStop(volume,g_state.entry,_Symbol,g_state.stop_loss,g_state.take_profit,ORDER_TIME_GTC,0,g_state.id);
      else sent=g_trade.BuyLimit(volume,g_state.entry,_Symbol,g_state.stop_loss,g_state.take_profit,ORDER_TIME_GTC,0,g_state.id);
     }
   else
     {
      if(g_state.entry<tick.bid) sent=g_trade.SellStop(volume,g_state.entry,_Symbol,g_state.stop_loss,g_state.take_profit,ORDER_TIME_GTC,0,g_state.id);
      else sent=g_trade.SellLimit(volume,g_state.entry,_Symbol,g_state.stop_loss,g_state.take_profit,ORDER_TIME_GTC,0,g_state.id);
     }
   if(!sent) { Audit("ORDER_REJECTED",StringFormat("ret=%u %s",g_trade.ResultRetcode(),g_trade.ResultRetcodeDescription())); return false; }
   g_state.stage=STAGE_PENDING;
   Audit("ORDER_SENT",StringFormat("model=%s entry=%.2f sl=%.2f tp=%.2f",g_state.execution_model,g_state.entry,g_state.stop_loss,g_state.take_profit));
   return true;
  }

int AdvanceWatch(MentorState &watch,const MqlRates &bar,const datetime known_at)
  {
   g_state=watch;
   string reason="";
   if(ScenarioInvalidated(bar,known_at,reason))
     {
      PrintFormat("MentorCausal [%s] CANCEL %s",g_state.id,reason);
      ZeroMemory(g_state);
      g_state.stage=STAGE_MAP;
      return -1;
     }
   if(g_state.stage==STAGE_SOURCE_TOUCHED)
     {
      double level=0.0,extreme=0.0;
      if(FindMatureSweep(bar,known_at,level,extreme))
        {
         g_state.stage=STAGE_SWEEPED; g_state.sweep_at=known_at; g_state.mature_liquidity=level; g_state.sweep_extreme=extreme;
         Audit("MATURE_SWEEP",StringFormat("liquidity=%.2f extreme=%.2f",level,extreme));
        }
      watch=g_state;
      ZeroMemory(g_state);
      g_state.stage=STAGE_MAP;
      return 0;
     }
   if(g_state.stage==STAGE_SWEEPED)
     {
      double reference=0.0; MentorZone execution;
      if(FindMeaningfulChoch(bar,known_at,reference,execution))
        {
         g_state.stage=STAGE_CHOCH; g_state.choch_at=known_at; g_state.choch_reference=reference; g_state.execution=execution;
         g_state.execution_model="HTF_OB_REACTION";
         g_state.entry=g_state.bullish ? execution.high : execution.low;
         double buffer=HardBuffer();
         g_state.stop_loss=g_state.bullish ? MathMin(MathMin(g_state.child.low,execution.low),g_state.sweep_extreme)-buffer : MathMax(MathMax(g_state.child.high,execution.high),g_state.sweep_extreme)+buffer;
         g_state.entry=NormalizePrice(g_state.entry); g_state.stop_loss=NormalizePrice(g_state.stop_loss); g_state.take_profit=NormalizePrice(g_state.objective);
         bool geometry=g_state.bullish ? g_state.stop_loss<g_state.entry && g_state.entry<g_state.take_profit : g_state.take_profit<g_state.entry && g_state.entry<g_state.stop_loss;
         Audit("MEANINGFUL_CHOCH",StringFormat("reference=%.2f execution=%.2f..%.2f",reference,execution.low,execution.high));
         if(!geometry)
           {
            PrintFormat("MentorCausal [%s] CANCEL INVALID_ORDER_GEOMETRY",g_state.id);
            ZeroMemory(g_state);
            g_state.stage=STAGE_MAP;
            return -1;
           }
         if(SendPending()) return 1;
         ZeroMemory(g_state);
         g_state.stage=STAGE_MAP;
         return -1;
        }
      watch=g_state;
      ZeroMemory(g_state);
      g_state.stage=STAGE_MAP;
      return 0;
     }
   ZeroMemory(g_state);
   g_state.stage=STAGE_MAP;
   return -1;
  }

void AdvanceActive(const MqlRates &bar,const datetime known_at)
  {
   if(g_state.stage==STAGE_POSITION)
     {
      if(!HasManagedPosition()) ResetState();
      return;
     }
   if(g_state.stage!=STAGE_PENDING) return;
   string reason="";
   if(ScenarioInvalidated(bar,known_at,reason)) { DeleteManagedOrders(); ResetState(reason); return; }
   if(HasManagedPosition()) { g_state.stage=STAGE_POSITION; Audit("POSITION_OPEN",""); return; }
   if(!HasManagedOrder()) ResetState("PENDING_GONE");
  }

void ProcessNewM1()
  {
   MqlRates rates[];
   if(!GetClosedRates(PERIOD_M1,rates)) return;
   MqlRates bar=rates[ArraySize(rates)-1];
   if(bar.time==g_last_m1) return;
   g_last_m1=bar.time;
   datetime known_at=bar.time+60;
   if(known_at<InpTradeFrom || known_at>=InpTradeTo) return;
   if(g_state.stage==STAGE_PENDING || g_state.stage==STAGE_POSITION)
     {
      AdvanceActive(bar,known_at);
      return;
     }
   for(int i=ArraySize(g_watches)-1;i>=0;i--)
     {
      int result=AdvanceWatch(g_watches[i],bar,known_at);
      if(result>0)
        {
         ClearWatches();
         return;
        }
      if(result<0) RemoveWatch(i);
     }
   RefreshPreparedDelivery(bar,known_at);
   if(DiscoverDeliveryReplacement(bar,known_at)) return;
   DiscoverTouches(bar,known_at);
  }

int OnInit()
  {
   if(!(bool)MQLInfoInteger(MQL_TESTER))
     {
      Print("MentorCausalStateEA is tester-only.");
      return INIT_FAILED;
     }
   ResetState();
   ArrayResize(g_watches,0);
   ArrayResize(g_seen_touch_keys,0);
   ArrayResize(g_seen_lineage_keys,0);
   ArrayResize(g_used_delivery_keys,0);
   ZeroMemory(g_prepared_delivery[0]);
   ZeroMemory(g_prepared_delivery[1]);
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   Print("MentorCausalStateEA v0.43 started without reference fixtures");
   return INIT_SUCCEEDED;
  }

void OnTick() { ProcessNewM1(); }

void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result)
  {
   if(trans.type!=TRADE_TRANSACTION_DEAL_ADD || trans.deal==0 || !HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetString(trans.deal,DEAL_SYMBOL)!=_Symbol || (long)HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=InpMagicNumber) return;
   ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal,DEAL_ENTRY);
   if(entry==DEAL_ENTRY_IN) Audit("FILLED",StringFormat("price=%.2f",HistoryDealGetDouble(trans.deal,DEAL_PRICE)));
   if(entry==DEAL_ENTRY_OUT || entry==DEAL_ENTRY_OUT_BY) Audit("CLOSED",StringFormat("price=%.2f profit=%.2f",HistoryDealGetDouble(trans.deal,DEAL_PRICE),HistoryDealGetDouble(trans.deal,DEAL_PROFIT)));
  }
