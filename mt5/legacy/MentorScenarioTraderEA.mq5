//+------------------------------------------------------------------+
//| MentorScenarioTraderEA.mq5                                      |
//| Experimental MT5 port of the Mentor Protocol.                    |
//|                                                                  |
//| Pipeline: H1/M30 OB owner -> causal LTF refinement -> sweep ->   |
//| CHoCH -> LTF OB retest -> fixed objective.                       |
//|                                                                  |
//| This EA is for Strategy Tester research. This build hard-blocks   |
//| live orders and is not a profitability claim.                     |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "Mentor Protocol research EA: causal HTF OB to LTF CHoCH retest"

#include <Trade/Trade.mqh>

enum MentorSizingMode
  {
   MENTOR_MIN_LOT=0,
   MENTOR_FIXED_LOT=1,
   MENTOR_RISK_PERCENT=2
  };

input bool             InpEnableLiveTrading=false;
input long             InpMagicNumber=26072001;
input datetime         InpTradeFrom=D'2025.01.06 00:00';
input datetime         InpTradeTo=D'2025.01.11 00:00';
input MentorSizingMode InpSizingMode=MENTOR_MIN_LOT;
input double           InpFixedLot=0.01;
input double           InpRiskPercent=1.0;
input int              InpMaxSpreadPoints=0;
input int              InpMaxHistoryBars=420;
input int              InpSweepLookbackBars=12;
input int              InpSignalCooldownBars=1;
input double           InpBufferTicks=1.0;
input bool             InpWriteJournalEvents=true;

struct MentorZone
  {
   bool valid;
   bool bullish;
   ENUM_TIMEFRAMES timeframe;
   datetime formed_at;
   double low;
   double high;
   int origin_index;
   int confirmation_index;
  };

struct MentorScenario
  {
   bool active;
   bool pending_sent;
   bool position_seen;
   bool bullish;
   ENUM_TIMEFRAMES owner_tf;
   ENUM_TIMEFRAMES refinement_tf;
   datetime armed_at;
   datetime sweep_at;
   datetime choch_at;
   datetime entry_zone_at;
   double sweep_extreme;
   double entry;
   double stop_loss;
   double take_profit;
   double entry_zone_low;
   double entry_zone_high;
   double owner_zone_low;
   double owner_zone_high;
   double objective;
   string id;
   string reason;
  };

CTrade g_trade;
MentorScenario g_scenario;
datetime g_last_m1_bar=0;
datetime g_last_signal_bar=0;
string g_last_signal_key="";
int g_event_sequence=0;

string TfName(const ENUM_TIMEFRAMES tf)
  {
   switch(tf)
     {
      case PERIOD_H1:  return "H1";
      case PERIOD_M30: return "M30";
      case PERIOD_M15: return "M15";
      case PERIOD_M5:  return "M5";
      case PERIOD_M1:  return "M1";
     }
   return EnumToString(tf);
  }

int TfSeconds(const ENUM_TIMEFRAMES tf)
  {
   int seconds=PeriodSeconds(tf);
   return seconds>0 ? seconds : 60;
  }

bool Bull(const MqlRates &bar)
  {
   return bar.close>bar.open;
  }

bool Bear(const MqlRates &bar)
  {
   return bar.close<bar.open;
  }

bool GetClosedRates(const ENUM_TIMEFRAMES tf,MqlRates &rates[])
  {
   ArrayFree(rates);
   ArraySetAsSeries(rates,false);
   int copied=CopyRates(_Symbol,tf,1,InpMaxHistoryBars,rates);
   return copied>=20;
  }

double CurrentSpreadPrice()
  {
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return 0.0;
   return MathMax(0.0,tick.ask-tick.bid);
  }

bool SpreadAllowed()
  {
   if(InpMaxSpreadPoints<=0)
      return true;
   long spread=0;
   if(!SymbolInfoInteger(_Symbol,SYMBOL_SPREAD,spread))
      return true;
   return spread<=InpMaxSpreadPoints;
  }

double TickSize()
  {
   double value=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   return value>0.0 ? value : _Point;
  }

double NormalizePrice(const double price)
  {
   return NormalizeDouble(price,(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS));
  }

double NormalizeVolume(double volume)
  {
   double minimum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maximum=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(minimum<=0.0) minimum=0.01;
   if(step<=0.0) step=minimum;
   volume=MathMax(minimum,MathMin(maximum,volume));
   volume=minimum+MathFloor((volume-minimum)/step+1e-9)*step;
   return NormalizeDouble(volume,2);
  }

bool CanSendOrders()
  {
   // This research build is intentionally tester-only. Live permission will
   // require a separate reviewed release after protocol parity and OOS gates.
   return (bool)MQLInfoInteger(MQL_TESTER);
  }

bool HasManagedPosition()
  {
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      string symbol=PositionGetSymbol(i);
      if(symbol!=_Symbol)
         continue;
      if((long)PositionGetInteger(POSITION_MAGIC)==InpMagicNumber)
         return true;
     }
   return false;
  }

bool HasManagedPending()
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0 || !OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL)!=_Symbol)
         continue;
      if((long)OrderGetInteger(ORDER_MAGIC)!=InpMagicNumber)
         continue;
      ENUM_ORDER_TYPE type=(ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE);
      if(type==ORDER_TYPE_BUY_LIMIT || type==ORDER_TYPE_SELL_LIMIT)
         return true;
     }
   return false;
  }

void ResetScenario()
  {
   ZeroMemory(g_scenario);
  }

void LogEvent(const string event_name,const string details)
  {
   PrintFormat("MentorScenarioTraderEA [%s] %s",event_name,details);
   if(!InpWriteJournalEvents)
      return;
   string directory="trading_journal";
   string file_name=directory+"\\mentor_scenario_events.jsonl";
   int handle=FileOpen(file_name,FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_SHARE_READ|FILE_SHARE_WRITE);
   if(handle==INVALID_HANDLE)
      return;
   FileSeek(handle,0,SEEK_END);
   string safe=details;
   StringReplace(safe,"\\","\\\\");
   StringReplace(safe,"\"","\\\"");
   string line=StringFormat("{\"event\":\"%s\",\"symbol\":\"%s\",\"time\":\"%s\",\"details\":\"%s\"}",
                            event_name,_Symbol,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),safe);
   FileWriteString(handle,line+"\r\n");
   FileClose(handle);
  }

bool SameDirectionThree(const MqlRates &rates[],const int i,const bool bullish)
  {
   if(i<2)
      return false;
   for(int j=i-2;j<=i;j++)
     {
      if(bullish && !Bull(rates[j])) return false;
      if(!bullish && !Bear(rates[j])) return false;
     }
   return true;
  }

bool IsFreshZone(const MqlRates &rates[],const int origin,const int last,const bool bullish,const double low,const double high)
  {
   if(origin<0 || origin>=last)
      return false;
   for(int i=origin+1;i<last;i++)
     {
      // The current, not-yet-processed reaction is allowed to touch a source.
      if(bullish && rates[i].close<low)
         return false;
      if(!bullish && rates[i].close>high)
         return false;
     }
   return high>low;
  }

bool FindLatestOB(const ENUM_TIMEFRAMES tf,const bool bullish,MentorZone &zone)
  {
   ZeroMemory(zone);
   MqlRates rates[];
   if(!GetClosedRates(tf,rates))
      return false;
   int n=ArraySize(rates);
   for(int i=n-1;i>=2;i--)
     {
      if(!SameDirectionThree(rates,i,bullish))
         continue;
      int origin=-1;
      for(int j=i-3;j>=MathMax(0,i-10);j--)
        {
         if(bullish && Bear(rates[j])) { origin=j; break; }
         if(!bullish && Bull(rates[j])) { origin=j; break; }
        }
      if(origin<0)
         continue;
      double low=rates[origin].low;
      double high=rates[origin].high;
      if(!IsFreshZone(rates,origin,n-1,bullish,low,high))
         continue;
      zone.valid=true;
      zone.bullish=bullish;
      zone.timeframe=tf;
      zone.formed_at=rates[i].time+TfSeconds(tf);
      zone.low=NormalizePrice(low);
      zone.high=NormalizePrice(high);
      zone.origin_index=origin;
      zone.confirmation_index=i;
      return true;
     }
   return false;
  }

bool ZonesOverlap(const MentorZone &parent,const MentorZone &child)
  {
   return MathMax(parent.low,child.low)<=MathMin(parent.high,child.high);
  }

bool PriceTouchesZone(const double low,const double high,const MentorZone &zone)
  {
   return high>=zone.low && low<=zone.high;
  }

bool FindLatestRefinement(const MentorZone &parent,const bool bullish,MentorZone &child)
  {
   ENUM_TIMEFRAMES candidates[3]={PERIOD_M5,PERIOD_M15,PERIOD_M30};
   for(int k=0;k<3;k++)
     {
      if(candidates[k]>=parent.timeframe)
         continue;
      MentorZone candidate;
      if(FindLatestOB(candidates[k],bullish,candidate) && candidate.formed_at>=parent.formed_at && ZonesOverlap(parent,candidate))
        {
         child=candidate;
         return true;
        }
     }
   return false;
  }

bool FindRecentTrend(const ENUM_TIMEFRAMES tf,int &trend,double &protected_high,double &protected_low)
  {
   trend=0;
   protected_high=0.0;
   protected_low=0.0;
   MqlRates rates[];
   if(!GetClosedRates(tf,rates))
      return false;
   int n=ArraySize(rates);
   double last_high=0.0,last_low=0.0;
   bool have_high=false,have_low=false;
   for(int i=2;i<n;i++)
     {
      if(SameDirectionThree(rates,i,false))
        {
         double high=rates[i-2].high;
         for(int j=i-2;j<=i;j++) high=MathMax(high,rates[j].high);
         last_high=high; have_high=true;
        }
      if(SameDirectionThree(rates,i,true))
        {
         double low=rates[i-2].low;
         for(int j=i-2;j<=i;j++) low=MathMin(low,rates[j].low);
         last_low=low; have_low=true;
        }
      if(have_high && rates[i].close>last_high)
        {
         trend=1;
         protected_low=last_low;
        }
      if(have_low && rates[i].close<last_low)
        {
         trend=-1;
         protected_high=last_high;
        }
     }
   return trend!=0;
  }

bool FindObjective(const bool bullish,const double reference,double &objective)
  {
   ENUM_TIMEFRAMES candidates[2]={PERIOD_H1,PERIOD_M30};
   double best=0.0;
   bool found=false;
   for(int k=0;k<2;k++)
     {
      MqlRates rates[];
      if(!GetClosedRates(candidates[k],rates)) continue;
      int n=ArraySize(rates);
      for(int i=2;i<n-1;i++)
        {
         if(bullish && SameDirectionThree(rates,i,false))
           {
            double level=rates[i-2].high;
            for(int j=i-2;j<=i;j++) level=MathMax(level,rates[j].high);
            if(level>reference && (!found || level<best)) { best=level; found=true; }
           }
         if(!bullish && SameDirectionThree(rates,i,true))
           {
            double level=rates[i-2].low;
            for(int j=i-2;j<=i;j++) level=MathMin(level,rates[j].low);
            if(level<reference && (!found || level>best)) { best=level; found=true; }
           }
        }
      if(found)
         break;
     }
   if(!found)
      return false;
   objective=NormalizePrice(best);
   return true;
  }

bool FindSweepAndChoch(const bool bullish,const datetime after,const MentorZone &source,datetime &sweep_at,datetime &choch_at,double &extreme,MentorZone &entry_zone)
  {
   MqlRates rates[];
   if(!GetClosedRates(PERIOD_M1,rates))
      return false;
   int n=ArraySize(rates);
   int start=0;
   for(int i=0;i<n;i++)
      if(rates[i].time+60>after) { start=i; break; }
   start=MathMax(2,start);
   bool have_sweep=false;
   double sweep_extreme=bullish?DBL_MAX:-DBL_MAX;
   datetime sweep_time=0;
   for(int i=start;i<n;i++)
     {
      if(!PriceTouchesZone(rates[i].low,rates[i].high,source) && !have_sweep)
         continue;
      int left=MathMax(0,i-InpSweepLookbackBars);
      if(left>=i)
         continue;
      double local_low=rates[left].low,local_high=rates[left].high;
      for(int j=left+1;j<i;j++) { local_low=MathMin(local_low,rates[j].low); local_high=MathMax(local_high,rates[j].high); }
      if(bullish && rates[i].low<local_low && rates[i].close>local_low)
        {
         have_sweep=true; sweep_extreme=MathMin(sweep_extreme,rates[i].low); sweep_time=rates[i].time+60;
        }
      if(!bullish && rates[i].high>local_high && rates[i].close<local_high)
        {
         have_sweep=true; sweep_extreme=MathMax(sweep_extreme,rates[i].high); sweep_time=rates[i].time+60;
        }
      if(!have_sweep)
         continue;
      int prior_start=MathMax(0,i-InpSweepLookbackBars);
      double live_high=rates[prior_start].high,live_low=rates[prior_start].low;
      for(int j=prior_start;j<i;j++) { live_high=MathMax(live_high,rates[j].high); live_low=MathMin(live_low,rates[j].low); }
      if(bullish && rates[i].close>live_high && Bull(rates[i]))
        {
         int candle=-1;
         for(int j=i-1;j>=MathMax(0,i-8);j--) if(Bear(rates[j])) { candle=j; break; }
         if(candle<0) continue;
         entry_zone.valid=true; entry_zone.bullish=true; entry_zone.timeframe=PERIOD_M1;
         entry_zone.formed_at=rates[i].time+60; entry_zone.low=rates[candle].low; entry_zone.high=rates[candle].high;
         entry_zone.origin_index=candle; entry_zone.confirmation_index=i;
         sweep_at=sweep_time; choch_at=rates[i].time+60; extreme=sweep_extreme; return true;
        }
      if(!bullish && rates[i].close<live_low && Bear(rates[i]))
        {
         int candle=-1;
         for(int j=i-1;j>=MathMax(0,i-8);j--) if(Bull(rates[j])) { candle=j; break; }
         if(candle<0) continue;
         entry_zone.valid=true; entry_zone.bullish=false; entry_zone.timeframe=PERIOD_M1;
         entry_zone.formed_at=rates[i].time+60; entry_zone.low=rates[candle].low; entry_zone.high=rates[candle].high;
         entry_zone.origin_index=candle; entry_zone.confirmation_index=i;
         sweep_at=sweep_time; choch_at=rates[i].time+60; extreme=sweep_extreme; return true;
        }
     }
   return false;
  }

double LotForRisk(const bool bullish,const double entry,const double stop)
  {
   if(InpSizingMode==MENTOR_MIN_LOT)
      return NormalizeVolume(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN));
   if(InpSizingMode==MENTOR_FIXED_LOT)
      return NormalizeVolume(InpFixedLot);
   double risk_money=AccountInfoDouble(ACCOUNT_EQUITY)*InpRiskPercent/100.0;
   double loss=0.0;
   ENUM_ORDER_TYPE type=bullish?ORDER_TYPE_BUY:ORDER_TYPE_SELL;
   if(!OrderCalcProfit(type,_Symbol,1.0,entry,stop,loss) || loss>=0.0)
      return NormalizeVolume(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN));
   return NormalizeVolume(risk_money/MathAbs(loss));
  }

bool SourceInvalidated(const MentorScenario &scenario)
  {
   MqlRates rates[];
   if(!GetClosedRates(scenario.owner_tf,rates))
      return false;
   int n=ArraySize(rates);
   for(int i=0;i<n;i++)
     {
      datetime available=rates[i].time+TfSeconds(scenario.owner_tf);
      if(available<=scenario.armed_at) continue;
      if(scenario.bullish && rates[i].close<scenario.owner_zone_low) return true;
      if(!scenario.bullish && rates[i].close>scenario.owner_zone_high) return true;
     }
   return false;
  }

bool ObjectiveDelivered(const MentorScenario &scenario)
  {
   MqlRates rates[];
   if(!GetClosedRates(PERIOD_M1,rates)) return false;
   for(int i=0;i<ArraySize(rates);i++)
     {
      if(rates[i].time+60<=scenario.armed_at) continue;
      if(scenario.bullish && rates[i].high>=scenario.objective) return true;
      if(!scenario.bullish && rates[i].low<=scenario.objective) return true;
     }
   return false;
  }

bool BuildScenario(const MqlRates &last_bar)
  {
   if(g_scenario.active || HasManagedPending() || HasManagedPosition() || !SpreadAllowed())
      return false;
   ENUM_TIMEFRAMES parents[2]={PERIOD_H1,PERIOD_M30};
   for(int direction=0;direction<2;direction++)
     {
      bool bullish=(direction==0);
      for(int p=0;p<2;p++)
        {
         int trend=0; double ph=0.0,pl=0.0;
         if(!FindRecentTrend(parents[p],trend,ph,pl)) continue;
         if((bullish && trend!=1) || (!bullish && trend!=-1)) continue;
         MentorZone parent;
         if(!FindLatestOB(parents[p],bullish,parent)) continue;
         if(!PriceTouchesZone(last_bar.low,last_bar.high,parent)) continue;
         MentorZone refinement;
         if(!FindLatestRefinement(parent,bullish,refinement))
            continue;
         if(!PriceTouchesZone(last_bar.low,last_bar.high,refinement))
            continue;
         double objective=0.0;
         double reference=bullish?parent.high:parent.low;
         if(!FindObjective(bullish,reference,objective)) continue;
         datetime sweep_at=0,choch_at=0; double extreme=0.0; MentorZone entry_zone;
         if(!FindSweepAndChoch(bullish,parent.formed_at,refinement,sweep_at,choch_at,extreme,entry_zone))
            continue;
         if(sweep_at<=parent.formed_at || choch_at<=sweep_at || entry_zone.formed_at<choch_at)
            continue;
         double buffer=MathMax(SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*_Point,MathMax(CurrentSpreadPrice()*3.0,TickSize()*InpBufferTicks));
         double entry=bullish?entry_zone.high:entry_zone.low;
         double stop=bullish?MathMin(extreme,entry_zone.low)-buffer:MathMax(extreme,entry_zone.high)+buffer;
         if((bullish && !(stop<entry && entry<objective)) || (!bullish && !(objective<entry && entry<stop)))
            continue;
         g_scenario.active=true;
         g_scenario.bullish=bullish;
         g_scenario.owner_tf=parents[p];
         g_scenario.refinement_tf=refinement.timeframe;
         g_scenario.armed_at=last_bar.time+60;
         g_scenario.sweep_at=sweep_at;
         g_scenario.choch_at=choch_at;
         g_scenario.entry_zone_at=entry_zone.formed_at;
         g_scenario.sweep_extreme=extreme;
         g_scenario.entry=NormalizePrice(entry);
         g_scenario.stop_loss=NormalizePrice(stop);
         g_scenario.take_profit=NormalizePrice(objective);
         g_scenario.entry_zone_low=entry_zone.low;
         g_scenario.entry_zone_high=entry_zone.high;
         g_scenario.owner_zone_low=parent.low;
         g_scenario.owner_zone_high=parent.high;
         g_scenario.objective=objective;
         g_scenario.id=StringFormat("%s-%s-%I64d",TfName(parents[p]),bullish?"L":"S",(long)g_scenario.choch_at);
         g_scenario.reason=StringFormat("owner=%s refinement=%s sweep=%s choch=%s",TfName(parents[p]),TfName(refinement.timeframe),TimeToString(sweep_at,TIME_DATE|TIME_MINUTES),TimeToString(choch_at,TIME_DATE|TIME_MINUTES));
         LogEvent("SCENARIO_ARMED",g_scenario.id+" "+g_scenario.reason);
         return true;
        }
     }
   return false;
  }

bool SendScenarioOrder()
  {
   if(!g_scenario.active || g_scenario.pending_sent || HasManagedPending() || HasManagedPosition())
      return false;
   if(!CanSendOrders())
     {
      LogEvent("ORDER_BLOCKED_RESEARCH_ONLY",g_scenario.id+" tester=false");
      ResetScenario();
      return false;
     }
   if(SourceInvalidated(g_scenario))
     {
      LogEvent("SCENARIO_CANCELLED",g_scenario.id+" source_tf_invalidation");
      ResetScenario(); return false;
     }
   if(ObjectiveDelivered(g_scenario))
     {
      LogEvent("SCENARIO_CANCELLED",g_scenario.id+" objective_delivered_before_entry");
      ResetScenario(); return false;
     }
   double volume=LotForRisk(g_scenario.bullish,g_scenario.entry,g_scenario.stop_loss);
   string comment="MentorV1 "+g_scenario.id;
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(20);
   bool sent=false;
   if(g_scenario.bullish)
      sent=g_trade.BuyLimit(volume,g_scenario.entry,_Symbol,g_scenario.stop_loss,g_scenario.take_profit,ORDER_TIME_GTC,0,comment);
   else
      sent=g_trade.SellLimit(volume,g_scenario.entry,_Symbol,g_scenario.stop_loss,g_scenario.take_profit,ORDER_TIME_GTC,0,comment);
   if(!sent)
     {
      LogEvent("ORDER_REJECTED",StringFormat("%s ret=%u %s",g_scenario.id,g_trade.ResultRetcode(),g_trade.ResultRetcodeDescription()));
      return false;
     }
   g_scenario.pending_sent=true;
   g_last_signal_key=g_scenario.id;
   LogEvent("ORDER_SENT",StringFormat("%s entry=%.2f sl=%.2f tp=%.2f lot=%.2f",g_scenario.id,g_scenario.entry,g_scenario.stop_loss,g_scenario.take_profit,volume));
   return true;
  }

void ManageScenario()
  {
   if(!g_scenario.active)
      return;
   if(HasManagedPosition())
     {
      if(!g_scenario.position_seen)
        {
         g_scenario.position_seen=true;
         LogEvent("POSITION_OPEN",g_scenario.id);
        }
      return;
     }
   if(g_scenario.pending_sent && !HasManagedPending())
     {
      LogEvent("PENDING_GONE",g_scenario.id);
      ResetScenario();
      return;
     }
   if(!g_scenario.pending_sent)
      SendScenarioOrder();
  }

void ProcessNewM1Bar()
  {
   MqlRates rates[];
   if(!GetClosedRates(PERIOD_M1,rates)) return;
   MqlRates last=rates[ArraySize(rates)-1];
   if(last.time==g_last_m1_bar) return;
   g_last_m1_bar=last.time;
   ManageScenario();
   datetime available=last.time+60;
   if(available<InpTradeFrom || (InpTradeTo>0 && available>=InpTradeTo))
      return;
   if(g_scenario.active)
     {
      if(SourceInvalidated(g_scenario))
        {
         LogEvent("SCENARIO_CANCELLED",g_scenario.id+" source_tf_invalidation");
         ResetScenario();
         return;
        }
      if(!g_scenario.pending_sent)
         SendScenarioOrder();
      return;
     }
   BuildScenario(last);
  }

int OnInit()
  {
   ResetScenario();
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   if(_Period!=PERIOD_M1)
      Print("MentorScenarioTraderEA: attach to an M1 chart for the intended tester protocol; current=",EnumToString((ENUM_TIMEFRAMES)_Period));
   LogEvent("EA_START",StringFormat("version=1.00 tester=%s live=%s",MQLInfoInteger(MQL_TESTER)?"true":"false",InpEnableLiveTrading?"true":"false"));
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   LogEvent("EA_STOP",IntegerToString(reason));
  }

void OnTick()
  {
   MqlRates current[];
   if(CopyRates(_Symbol,PERIOD_M1,0,1,current)!=1)
      return;
   ProcessNewM1Bar();
  }
