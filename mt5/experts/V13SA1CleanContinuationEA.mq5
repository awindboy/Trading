//+------------------------------------------------------------------+
//| V13SA1CleanContinuationEA.mq5                                   |
//| V13 SA-1: clean-continuation admission + unchanged HA-9 manage. |
//| GOLD# / RESEARCH TESTER ONLY / NO PRODUCTION AUTHORITY          |
//+------------------------------------------------------------------+
#property strict
#property version   "13.200"
#property description "V13 SA-1 research candidate: Child1 unchanged; add-ons require clean-continuation signal-H4 admission, then unchanged HA-9 proof/timeout/lock management."

#include <Trade/Trade.mqh>

input long   InpMagicNumber     = 1302060928;
input double InpLotPerChild     = 0.01;
input int    InpDeviationPoints = 30;
input bool   InpVerbose         = true;

const ENUM_TIMEFRAMES SIGNAL_TF = PERIOD_H4;
const ENUM_TIMEFRAMES PATH_TF   = PERIOD_H1;
#define MAX_CHILDREN 10
const datetime EVALUATION_START = D'2024.01.01 00:00:00';
const datetime HA_WARMUP_START  = D'2022.01.03 00:00:00';

CTrade trade;

datetime g_current_h4_open=0;
double   g_last_ha_open=0.0, g_last_ha_close=0.0;
int      g_last_ha_color=0;
bool     g_ha_ready=false;

datetime g_last_h1_signal=0;
double   g_last_h1_ha_open=0.0, g_last_h1_ha_close=0.0;
int      g_last_h1_ha_color=0;
bool     g_h1_ready=false;
datetime g_recent_h1_time[16];
int      g_recent_h1_color[16];
int      g_recent_h1_count=0;

bool     g_active_journey=false;
int      g_journey_direction=0;
int      g_children=0; // successful entries only
int      g_journey_id=0;
bool     g_halted=false;

bool     g_pending_entry=false;
bool     g_pending_close=false;
bool     g_pending_child_close=false;
int      g_pending_child_index=0;
string   g_pending_child_reason="";

datetime g_signal_time=0;
datetime g_execution_bar=0;
datetime g_last_signal=0;
int      g_target_color=0;
double   g_pending_signal_high=0.0;
double   g_pending_signal_low=0.0;

datetime g_next_attempt=0;
int      g_retry_delay=1;
int      g_retry_count=0;

ulong    g_child_ticket[MAX_CHILDREN+1];
bool     g_child_open[MAX_CHILDREN+1];
bool     g_child_managed[MAX_CHILDREN+1];
bool     g_child_proven[MAX_CHILDREN+1];
bool     g_child_just_armed[MAX_CHILDREN+1];
double   g_child_entry[MAX_CHILDREN+1];
double   g_child_target[MAX_CHILDREN+1];
double   g_child_lock[MAX_CHILDREN+1];
datetime g_child_proof_bar[MAX_CHILDREN+1];

string DirectionName(const int direction){ return(direction>0 ? "LONG" : "SHORT"); }

int HAColor(const double ha_open,const double ha_close,const int previous_color)
  {
   if(ha_close>ha_open) return 1;
   if(ha_close<ha_open) return -1;
   return previous_color;
  }

bool Retryable(const uint code)
  {
   return(code==TRADE_RETCODE_MARKET_CLOSED || code==TRADE_RETCODE_REQUOTE ||
          code==TRADE_RETCODE_PRICE_CHANGED || code==TRADE_RETCODE_PRICE_OFF ||
          code==TRADE_RETCODE_TOO_MANY_REQUESTS);
  }

void HaltRun(const string reason)
  {
   if(g_halted) return;
   g_halted=true;
   PrintFormat("V13SA1_HALT|time=%s|reason=%s",TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),reason);
  }

void ResetRetry(){ g_next_attempt=0; g_retry_delay=1; }

void DeferExecution(const string action,const uint code)
  {
   g_retry_count++;
   g_next_attempt=TimeCurrent()+g_retry_delay;
   PrintFormat("V13SA1_RETRY|action=%s|retcode=%u|delay=%d|signal=%s|positions=%d",
               action,code,g_retry_delay,TimeToString(g_signal_time,TIME_DATE|TIME_SECONDS),PositionsTotal());
   g_retry_delay=(int)MathMin(30,g_retry_delay*2);
  }

bool ValidateRequestedVolume()
  {
   const double min_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   const double max_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   const double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(InpLotPerChild<=0.0 || step<=0.0) return false;
   if(InpLotPerChild<min_volume-1e-12 || InpLotPerChild>max_volume+1e-12) return false;
   const double units=InpLotPerChild/step;
   return(MathAbs(units-MathRound(units))<=1e-8);
  }

int CountOwnPositions()
  {
   int count=0;
   for(int i=0;i<PositionsTotal();i++)
     {
      const ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber) continue;
      count++;
     }
   return count;
  }

int CountTrackedOpen()
  {
   int count=0;
   for(int i=1;i<=g_children && i<=MAX_CHILDREN;i++) if(g_child_open[i]) count++;
   return count;
  }

ulong LowestOwnPositionTicket()
  {
   ulong lowest=0;
   for(int i=0;i<PositionsTotal();i++)
     {
      const ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber) continue;
      if(lowest==0 || ticket<lowest) lowest=ticket;
     }
   return lowest;
  }

ulong FindOwnPositionByComment(const string comment)
  {
   for(int i=0;i<PositionsTotal();i++)
     {
      const ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber) continue;
      if(PositionGetString(POSITION_COMMENT)==comment) return ticket;
     }
   return 0;
  }

void ResetChildStates()
  {
   for(int i=0;i<=MAX_CHILDREN;i++)
     {
      g_child_ticket[i]=0; g_child_open[i]=false; g_child_managed[i]=false;
      g_child_proven[i]=false; g_child_just_armed[i]=false;
      g_child_entry[i]=0.0; g_child_target[i]=0.0; g_child_lock[i]=0.0; g_child_proof_bar[i]=0;
     }
   g_pending_child_close=false; g_pending_child_index=0; g_pending_child_reason="";
  }

bool ReconcileTrackedPositions()
  {
   const int actual=CountOwnPositions(), tracked=CountTrackedOpen();
   if(actual!=tracked)
     {
      PrintFormat("V13SA1_STATE_FAIL|reason=tracked_position_mismatch|actual=%d|tracked=%d|journey=%d|children=%d",actual,tracked,g_journey_id,g_children);
      HaltRun("untracked or unexpectedly missing Child position"); return false;
     }
   for(int i=1;i<=g_children;i++)
     if(g_child_open[i] && (g_child_ticket[i]==0 || !PositionSelectByTicket(g_child_ticket[i])))
       { HaltRun(StringFormat("tracked Child %d ticket missing",i)); return false; }
   return true;
  }

bool TradeRetcodeDone(){ return((uint)trade.ResultRetcode()==TRADE_RETCODE_DONE); }

void PushRecentH1(const datetime t,const int ha_color)
  {
   if(g_recent_h1_count<16)
     {
      g_recent_h1_time[g_recent_h1_count]=t; g_recent_h1_color[g_recent_h1_count]=ha_color; g_recent_h1_count++;
      return;
     }
   for(int i=1;i<16;i++){ g_recent_h1_time[i-1]=g_recent_h1_time[i]; g_recent_h1_color[i-1]=g_recent_h1_color[i]; }
   g_recent_h1_time[15]=t; g_recent_h1_color[15]=ha_color;
  }

bool InitializeHAStateTF(const ENUM_TIMEFRAMES tf,double &last_open,double &last_close,int &last_color,datetime &last_signal)
  {
   const datetime last_completed=iTime(_Symbol,tf,1);
   if(last_completed<=0) return false;
   MqlRates rates[]; ArraySetAsSeries(rates,false);
   const int copied=CopyRates(_Symbol,tf,HA_WARMUP_START,last_completed,rates);
   if(copied<=0) return false;
   bool seeded=false; double po=0.0,pc=0.0; int ha_color=0; datetime final_time=0;
   for(int i=0;i<copied;i++)
     {
      if(rates[i].time>last_completed) break;
      const double hc=(rates[i].open+rates[i].high+rates[i].low+rates[i].close)/4.0;
      const double ho=!seeded ? (rates[i].open+rates[i].close)/2.0 : (po+pc)/2.0;
      const int c=HAColor(ho,hc,ha_color);
      seeded=true; po=ho; pc=hc; ha_color=c; final_time=rates[i].time;
     }
   if(!seeded || final_time!=last_completed) return false;
   last_open=po; last_close=pc; last_color=ha_color; last_signal=last_completed;
   return true;
  }

bool InitializeStates()
  {
   if(!InitializeHAStateTF(SIGNAL_TF,g_last_ha_open,g_last_ha_close,g_last_ha_color,g_last_signal)) return false;
   if(!InitializeHAStateTF(PATH_TF,g_last_h1_ha_open,g_last_h1_ha_close,g_last_h1_ha_color,g_last_h1_signal)) return false;
   g_ha_ready=true; g_h1_ready=true; return true;
  }

bool ProcessCompletedH1()
  {
   const datetime latest=iTime(_Symbol,PATH_TF,1);
   if(latest<=g_last_h1_signal) return true;
   MqlRates bars[]; ArraySetAsSeries(bars,false);
   const int copied=CopyRates(_Symbol,PATH_TF,g_last_h1_signal+1,latest,bars);
   if(copied<=0 || bars[copied-1].time!=latest) return false;
   for(int i=0;i<copied;i++)
     {
      const double hc=(bars[i].open+bars[i].high+bars[i].low+bars[i].close)/4.0;
      const double ho=(g_last_h1_ha_open+g_last_h1_ha_close)/2.0;
      const int ha_color=HAColor(ho,hc,g_last_h1_ha_color);
      g_last_h1_ha_open=ho; g_last_h1_ha_close=hc; g_last_h1_ha_color=ha_color; g_last_h1_signal=bars[i].time;
      PushRecentH1(bars[i].time,ha_color);
     }
   return true;
  }

bool SignalH4H1NoOpposition(const datetime signal_h4,const int direction,int &observed)
  {
   observed=0;
   const datetime end=signal_h4+4*60*60;
   for(int i=0;i<g_recent_h1_count;i++)
     {
      const datetime t=g_recent_h1_time[i];
      if(t<signal_h4 || t>=end) continue;
      observed++;
      if(g_recent_h1_color[i]!=direction) return false;
     }
   return(observed>0);
  }

bool SA1Admission(const MqlRates &completed,const double ha_open,const double ha_close,const int direction,
                  bool &raw_accept,bool &no_opp_wick,bool &h1_no_opp,int &h1_observed)
  {
   const double eps=_Point*0.1;
   raw_accept=(direction>0) ? (completed.close>ha_close+eps) : (completed.close<ha_close-eps);
   const double lower_wick=MathMin(ha_open,ha_close)-completed.low;
   const double upper_wick=completed.high-MathMax(ha_open,ha_close);
   const double opposite_wick=(direction>0 ? lower_wick : upper_wick);
   no_opp_wick=(opposite_wick<=eps);
   h1_no_opp=SignalH4H1NoOpposition(completed.time,direction,h1_observed);
   return(raw_accept && no_opp_wick && h1_no_opp);
  }

bool PlaceChild(const int direction,const datetime signal_bar_time,const datetime execution_bar_time)
  {
   if(g_children>=MAX_CHILDREN) return true;
   if(!ReconcileTrackedPositions()) return false;
   const int next_child=g_children+1;
   const string comment=StringFormat("V13SA1|J%06d|C%02d|%s",g_journey_id,next_child,direction>0?"L":"S");
   const int before=CountOwnPositions();
   ResetLastError();
   const bool request_ok=(direction>0) ? trade.Buy(InpLotPerChild,_Symbol,0.0,0.0,0.0,comment) : trade.Sell(InpLotPerChild,_Symbol,0.0,0.0,0.0,comment);
   const uint code=(uint)trade.ResultRetcode();
   if(!request_ok || !TradeRetcodeDone())
     {
      PrintFormat("V13SA1_ORDER_FAIL|action=ENTRY|journey=%d|child=%d|retcode=%u|err=%d",g_journey_id,next_child,code,GetLastError());
      if(Retryable(code) && CountOwnPositions()==before) DeferExecution("ENTRY",code);
      else HaltRun(StringFormat("ENTRY unresolved/permanent failure retcode=%u",code));
      return false;
     }
   if(CountOwnPositions()!=before+1 || MathAbs(trade.ResultVolume()-InpLotPerChild)>1e-8){ HaltRun("ENTRY reconciliation failed"); return false; }
   const ulong ticket=FindOwnPositionByComment(comment);
   if(ticket==0 || !PositionSelectByTicket(ticket)){ HaltRun("ENTRY succeeded but ticket/comment cannot be reconciled"); return false; }
   g_children=next_child; g_child_ticket[next_child]=ticket; g_child_open[next_child]=true;
   g_child_entry[next_child]=PositionGetDouble(POSITION_PRICE_OPEN); g_child_managed[next_child]=(next_child>=2);
   g_child_proven[next_child]=false; g_child_just_armed[next_child]=false; g_child_proof_bar[next_child]=execution_bar_time;
   g_child_target[next_child]=(direction>0 ? g_pending_signal_high : g_pending_signal_low);
   ResetRetry();
   PrintFormat("V13SA1_EVENT|ENTRY|journey=%d|child=%d|dir=%s|ticket=%I64u|entry=%.5f|proof_target=%.5f|managed=%d|signal=%s",
               g_journey_id,next_child,DirectionName(direction),ticket,g_child_entry[next_child],g_child_target[next_child],g_child_managed[next_child],TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES));
   return true;
  }

bool CloseTrackedChild(const int child,const string reason)
  {
   if(child<1 || child>g_children || !g_child_open[child]){ g_pending_child_close=false; return true; }
   const ulong ticket=g_child_ticket[child]; if(ticket==0 || !PositionSelectByTicket(ticket)){ HaltRun("cannot select child for close"); return false; }
   const double volume=PositionGetDouble(POSITION_VOLUME), entry=PositionGetDouble(POSITION_PRICE_OPEN);
   ResetLastError(); const bool ok=trade.PositionClose(ticket,(ulong)InpDeviationPoints); const uint code=(uint)trade.ResultRetcode(); const bool remains=PositionSelectByTicket(ticket);
   if((!ok || !TradeRetcodeDone()) || remains)
     {
      if(code==TRADE_RETCODE_DONE_PARTIAL && remains && PositionGetDouble(POSITION_VOLUME)<volume) DeferExecution("CHILD_EXIT_REMAINDER",code);
      else if(Retryable(code) && remains && MathAbs(PositionGetDouble(POSITION_VOLUME)-volume)<1e-8) DeferExecution("CHILD_EXIT",code);
      else if(code==TRADE_RETCODE_POSITION_CLOSED && !remains){ g_child_open[child]=false; g_pending_child_close=false; ResetRetry(); return true; }
      else HaltRun(StringFormat("Child close unresolved/permanent failure retcode=%u",code));
      return false;
     }
   g_child_open[child]=false; g_pending_child_close=false; g_pending_child_index=0; g_pending_child_reason=""; ResetRetry();
   PrintFormat("V13SA1_EVENT|CHILD_EXIT|journey=%d|child=%d|reason=%s|ticket=%I64u|entry=%.5f|exit=%.5f",g_journey_id,child,reason,ticket,entry,trade.ResultPrice());
   return true;
  }

bool CloseAllJourneyPositions(const datetime signal_bar_time)
  {
   if(!ReconcileTrackedPositions()) return false;
   while(CountOwnPositions()>0)
     {
      const ulong ticket=LowestOwnPositionTicket(); if(ticket==0 || !PositionSelectByTicket(ticket)){ HaltRun("cannot select own position during Journey close"); return false; }
      int child=0; for(int i=1;i<=g_children;i++) if(g_child_open[i] && g_child_ticket[i]==ticket){ child=i; break; }
      if(child==0){ HaltRun("Journey close encountered untracked own position"); return false; }
      const double volume=PositionGetDouble(POSITION_VOLUME); ResetLastError();
      const bool ok=trade.PositionClose(ticket,(ulong)InpDeviationPoints); const uint code=(uint)trade.ResultRetcode(); const bool remains=PositionSelectByTicket(ticket);
      if((!ok || !TradeRetcodeDone()) || remains)
        {
         if(code==TRADE_RETCODE_DONE_PARTIAL && remains && PositionGetDouble(POSITION_VOLUME)<volume) DeferExecution("JOURNEY_EXIT_REMAINDER",code);
         else if(Retryable(code) && remains && MathAbs(PositionGetDouble(POSITION_VOLUME)-volume)<1e-8) DeferExecution("JOURNEY_EXIT",code);
         else if(code==TRADE_RETCODE_POSITION_CLOSED && !remains) g_child_open[child]=false;
         else HaltRun(StringFormat("Journey close unresolved/permanent failure retcode=%u",code));
         return false;
        }
      g_child_open[child]=false; ResetRetry();
      PrintFormat("V13SA1_EVENT|JOURNEY_CHILD_EXIT|journey=%d|child=%d|ticket=%I64u|signal=%s|exit=%.5f",g_journey_id,child,ticket,TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),trade.ResultPrice());
     }
   return true;
  }

void StartJourney(const int direction)
  {
   g_journey_id++; g_journey_direction=direction; g_children=0; g_active_journey=true; ResetChildStates();
   PrintFormat("V13SA1_EVENT|JOURNEY_START|journey=%d|dir=%s|signal=%s",g_journey_id,DirectionName(direction),TimeToString(g_signal_time,TIME_DATE|TIME_MINUTES));
   g_pending_entry=true; // Child1 unchanged: no SA-1 gate
  }

void ScheduleChildClose(const int child,const string reason)
  {
   if(g_pending_close || g_pending_child_close || child<2 || child>g_children || !g_child_open[child]) return;
   g_pending_child_close=true; g_pending_child_index=child; g_pending_child_reason=reason;
  }

void ExpireUnprovenAddOns(const datetime new_h4_open)
  {
   if(g_pending_close || g_pending_child_close) return;
   for(int i=2;i<=g_children;i++)
     if(g_child_open[i] && g_child_managed[i] && !g_child_proven[i] && g_child_proof_bar[i]>0 && g_child_proof_bar[i]<new_h4_open)
       {
        PrintFormat("V13SA1_EVENT|PROOF_TIMEOUT_DUE|journey=%d|child=%d|proof_bar=%s|now=%s",g_journey_id,i,TimeToString(g_child_proof_bar[i],TIME_DATE|TIME_MINUTES),TimeToString(new_h4_open,TIME_DATE|TIME_MINUTES));
        ScheduleChildClose(i,"PROOF_TIMEOUT"); return;
       }
  }

void ManageAddOnChildren()
  {
   if(g_halted || !g_active_journey || g_pending_close || g_pending_child_close) return;
   if(!ReconcileTrackedPositions()) return;
   MqlTick tick; if(!SymbolInfoTick(_Symbol,tick)) return; const double eps=_Point*0.1;
   for(int i=2;i<=g_children;i++)
     {
      if(!g_child_open[i] || !g_child_managed[i]) continue;
      if(!g_child_proven[i])
        {
         const bool proof=(g_journey_direction>0) ? (tick.bid>g_child_target[i]+eps) : (tick.bid<g_child_target[i]-eps);
         if(proof)
           {
            g_child_proven[i]=true;
            g_child_lock[i]=(g_journey_direction>0) ? MathMax(g_child_entry[i],g_child_target[i]) : MathMin(g_child_entry[i],g_child_target[i]);
            g_child_just_armed[i]=true;
            PrintFormat("V13SA1_EVENT|PROOF|journey=%d|child=%d|target=%.5f|lock=%.5f|bid=%.5f|ask=%.5f",g_journey_id,i,g_child_target[i],g_child_lock[i],tick.bid,tick.ask);
           }
         continue;
        }
      if(g_child_just_armed[i]) g_child_just_armed[i]=false;
      const bool hit=(g_journey_direction>0) ? (tick.bid<=g_child_lock[i]+eps) : (tick.ask>=g_child_lock[i]-eps);
      if(hit)
        {
         PrintFormat("V13SA1_EVENT|LOCK_HIT|journey=%d|child=%d|lock=%.5f|bid=%.5f|ask=%.5f",g_journey_id,i,g_child_lock[i],tick.bid,tick.ask);
         ScheduleChildClose(i,"BREAKOUT_LOCK"); return;
        }
     }
  }

void ServiceExecution()
  {
   if(g_halted || TimeCurrent()<g_next_attempt) return;
   if(g_pending_close)
     {
      g_pending_child_close=false; g_pending_child_index=0; g_pending_child_reason="";
      if(!CloseAllJourneyPositions(g_signal_time)) return;
      PrintFormat("V13SA1_EVENT|JOURNEY_END|journey=%d|children=%d|exec=%s",g_journey_id,g_children,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS));
      g_pending_close=false; g_active_journey=false; g_children=0; g_journey_direction=0; StartJourney(g_target_color);
     }
   if(g_pending_child_close)
     {
      const int child=g_pending_child_index; const string reason=g_pending_child_reason;
      if(!CloseTrackedChild(child,reason)) return;
     }
   if(g_pending_entry)
     {
      if(!ReconcileTrackedPositions()) return;
      if(PlaceChild(g_journey_direction,g_signal_time,g_execution_bar)) g_pending_entry=false;
     }
  }

void ObserveCompletedH4(const MqlRates &completed,const datetime execution_bar_time)
  {
   const datetime signal_bar_time=completed.time; const int previous_color=g_last_ha_color;
   const double hc=(completed.open+completed.high+completed.low+completed.close)/4.0;
   const double ho=(g_last_ha_open+g_last_ha_close)/2.0;
   const int ha_color=HAColor(ho,hc,previous_color);
   g_last_ha_open=ho; g_last_ha_close=hc; g_last_ha_color=ha_color; g_last_signal=signal_bar_time;

   if(g_pending_entry) PrintFormat("V13SA1_ENTRY_EXPIRED|old_signal=%s|new_signal=%s",TimeToString(g_signal_time,TIME_DATE|TIME_MINUTES),TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES));
   g_pending_entry=false; g_signal_time=signal_bar_time; g_execution_bar=execution_bar_time; g_target_color=ha_color;
   g_pending_signal_high=completed.high; g_pending_signal_low=completed.low;

   if(InpVerbose) PrintFormat("V13SA1_EVENT|HA_CLOSE|bar=%s|known_at=%s|high=%.5f|low=%.5f|close=%.5f|ha_open=%.5f|ha_close=%.5f|color=%d|prev=%d",
      TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),TimeToString(execution_bar_time,TIME_DATE|TIME_MINUTES),completed.high,completed.low,completed.close,ho,hc,ha_color,previous_color);

   if(signal_bar_time<EVALUATION_START || ha_color==0 || previous_color==0) return;
   if(g_pending_close) return;
   if(!g_active_journey){ if(ha_color!=previous_color) StartJourney(ha_color); return; }
   if(!ReconcileTrackedPositions()) return;

   if(ha_color==g_journey_direction)
     {
      if(g_children>=MAX_CHILDREN){ if(InpVerbose) PrintFormat("V13SA1_EVENT|CAP_HOLD|journey=%d|children=%d",g_journey_id,g_children); return; }
      bool raw_accept=false,no_wick=false,h1_no_opp=false; int h1_observed=0;
      const bool admit=SA1Admission(completed,ho,hc,g_journey_direction,raw_accept,no_wick,h1_no_opp,h1_observed);
      PrintFormat("V13SA1_EVENT|ADMISSION|journey=%d|next_child=%d|signal=%s|admit=%d|raw_close_accept=%d|no_opposite_wick=%d|h1_no_opposition=%d|h1_observed=%d",
                  g_journey_id,g_children+1,TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),admit,raw_accept,no_wick,h1_no_opp,h1_observed);
      if(admit) g_pending_entry=true;
      // Rejecting a signal does not consume a successful Child number and is never backfilled using future price.
      return;
     }

   g_pending_close=true; g_pending_child_close=false; ResetRetry();
  }

bool ProcessCompletedH4(const datetime execution_bar_time)
  {
   MqlRates completed[]; ArraySetAsSeries(completed,false);
   const datetime latest=iTime(_Symbol,SIGNAL_TF,1); if(latest<=g_last_signal) return false;
   ResetLastError(); const int copied=CopyRates(_Symbol,SIGNAL_TF,g_last_signal+1,latest,completed);
   if(copied<=0 || completed[copied-1].time!=latest)
     {
      if(TimeCurrent()>=g_next_attempt){ PrintFormat("V13SA1_HISTORY_WAIT|err=%d|latest=%s",GetLastError(),TimeToString(latest)); g_next_attempt=TimeCurrent()+5; }
      return false;
     }
   for(int i=0;i<copied && !g_halted;i++) ObserveCompletedH4(completed[i],execution_bar_time);
   return !g_halted;
  }

int OnInit()
  {
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING){ Print("V13SA1_INIT_FAIL|reason=hedging mode required"); return INIT_FAILED; }
   if(InpDeviationPoints<0 || InpMagicNumber<=0 || !ValidateRequestedVolume()) return INIT_FAILED;
   if(CountOwnPositions()!=0){ Print("V13SA1_INIT_FAIL|reason=pre-existing position with this magic"); return INIT_FAILED; }
   trade.SetExpertMagicNumber(InpMagicNumber); trade.SetDeviationInPoints(InpDeviationPoints); if(!trade.SetTypeFillingBySymbol(_Symbol)) return INIT_FAILED; trade.SetAsyncMode(false);
   ResetChildStates(); g_current_h4_open=iTime(_Symbol,SIGNAL_TF,0);
   if(g_current_h4_open<=0 || !InitializeStates()) return INIT_FAILED;
   PrintFormat("V13SA1_READY|symbol=%s|version=13.200|max_children=%d|child1=baseline|admission=rawclose_nooppwick_h1noopp|management=ha9_proof_lock_timeout|magic=%I64d",_Symbol,MAX_CHILDREN,InpMagicNumber);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   PrintFormat("V13SA1_DEINIT|reason=%d|halted=%d|journey=%d|children=%d|open_tracked=%d|positions=%d|retries=%d",reason,g_halted,g_journey_id,g_children,CountTrackedOpen(),CountOwnPositions(),g_retry_count);
  }

void OnTick()
  {
   if(g_halted || !g_ha_ready || !g_h1_ready) return;
   if(!ReconcileTrackedPositions()) return;
   const datetime current_h4_open=iTime(_Symbol,SIGNAL_TF,0); if(current_h4_open<=0) return;
   if(current_h4_open!=g_current_h4_open)
     {
      // Existing HA-9 children expire before the new H4 can prove them.
      ExpireUnprovenAddOns(current_h4_open);
      // Bring H1 HA state through the just-completed signal H4 before evaluating SA-1 admission.
      if(!ProcessCompletedH1()) return;
      if(!ProcessCompletedH4(current_h4_open)) return;
      g_current_h4_open=current_h4_open;
     }
   ServiceExecution(); if(g_halted) return; ManageAddOnChildren(); ServiceExecution();
  }
//+------------------------------------------------------------------+
