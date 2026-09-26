//+------------------------------------------------------------------+
//| V13HAOnlyMax10EA.mq5                                             |
//| V13 Baseline 0: standard H4 Heikin-Ashi, max-10 Journey.         |
//| GOLD# / RESEARCH TESTER ONLY / NO PRODUCTION AUTHORITY           |
//+------------------------------------------------------------------+
#property strict
#property version   "13.002"
#property description "V13 Baseline 0: standard H4 HA, one Child per same-color completed bar, max 10, opposite HA close-all/reverse."

#ifndef V13_EXECUTION_TEST
#include <Trade/Trade.mqh>
#endif

input long   InpMagicNumber     = 1300260926;
input double InpLotPerChild     = 0.01;
input int    InpDeviationPoints = 30;
input bool   InpVerbose         = true;

const ENUM_TIMEFRAMES SIGNAL_TF       = PERIOD_H4;
const int             MAX_CHILDREN    = 10;
const datetime        EVALUATION_START = D'2024.01.01 00:00:00';
const datetime        HA_WARMUP_START  = D'2022.01.03 00:00:00';

CTrade trade;

datetime g_current_h4_open = 0;
double   g_last_ha_open     = 0.0;
double   g_last_ha_close    = 0.0;
int      g_last_ha_color    = 0;
bool     g_ha_ready         = false;

bool     g_active_journey   = false;
int      g_journey_direction = 0; // +1 LONG/BULL, -1 SHORT/BEAR
int      g_children          = 0;
int      g_journey_id        = 0;
bool     g_halted            = false;
bool     g_pending_entry     = false;
bool     g_pending_close     = false;
datetime g_signal_time       = 0;
datetime g_execution_bar     = 0;
datetime g_next_attempt      = 0;
datetime g_last_signal       = 0;
int      g_target_color      = 0;
int      g_retry_delay       = 1;
int      g_retry_count       = 0;

// Only explicit non-execution responses are safe to resend. A timeout,
// PLACED, partial ENTRY, or connection ambiguity must never create a duplicate.
bool Retryable(const uint code)
  {
   return(code==TRADE_RETCODE_MARKET_CLOSED || code==TRADE_RETCODE_REQUOTE ||
          code==TRADE_RETCODE_PRICE_CHANGED || code==TRADE_RETCODE_PRICE_OFF ||
          code==TRADE_RETCODE_TOO_MANY_REQUESTS);
  }

void ResetRetry()
  {
   g_next_attempt=0;
   g_retry_delay=1;
  }

void DeferExecution(const string action,const uint code)
  {
   g_retry_count++;
   g_next_attempt=TimeCurrent()+g_retry_delay;
   // Log once per retry, never once per tick; no blocking Sleep loop.
   PrintFormat("V13_RETRY|action=%s|retcode=%u|delay=%d|signal=%s|positions=%d",
               action,code,g_retry_delay,
               TimeToString(g_signal_time,TIME_DATE|TIME_SECONDS),CountOwnPositions());
   g_retry_delay=(int)MathMin(30,g_retry_delay*2);
  }

//+------------------------------------------------------------------+
string DirectionName(const int direction)
  {
   return(direction > 0 ? "LONG" : "SHORT");
  }

//+------------------------------------------------------------------+
int HAColor(const double ha_open,const double ha_close,const int previous_color)
  {
   if(ha_close > ha_open)
      return 1;
   if(ha_close < ha_open)
      return -1;
   return previous_color; // exact equality inherits previous non-zero color
  }

//+------------------------------------------------------------------+
void HaltRun(const string reason)
  {
   if(g_halted)
      return;
   g_halted=true;
   PrintFormat("V13_HALT|time=%s|reason=%s",
               TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),reason);
  }

//+------------------------------------------------------------------+
bool ValidateRequestedVolume()
  {
   const double min_volume = SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   const double max_volume = SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   const double step       = SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);

   if(InpLotPerChild <= 0.0 || step <= 0.0)
      return false;
   if(InpLotPerChild < min_volume-1e-12 || InpLotPerChild > max_volume+1e-12)
      return false;

   const double step_units = InpLotPerChild/step;
   if(MathAbs(step_units-MathRound(step_units)) > 1e-8)
      return false;

   return true;
  }

//+------------------------------------------------------------------+
int CountOwnPositions()
  {
   int count=0;
   const int total=PositionsTotal();
   for(int i=0;i<total;i++)
     {
      const ulong ticket=PositionGetTicket(i);
      if(ticket==0)
         continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol)
         continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber)
         continue;
      count++;
     }
   return count;
  }

//+------------------------------------------------------------------+
ulong LowestOwnPositionTicket()
  {
   ulong lowest=0;
   const int total=PositionsTotal();
   for(int i=0;i<total;i++)
     {
      const ulong ticket=PositionGetTicket(i);
      if(ticket==0)
         continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol)
         continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber)
         continue;
      if(lowest==0 || ticket<lowest)
         lowest=ticket;
     }
   return lowest;
  }

//+------------------------------------------------------------------+
bool InitializeHAState()
  {
   const datetime last_completed=iTime(_Symbol,SIGNAL_TF,1);
   if(last_completed<=0)
     {
      Print("V13_INIT_FAIL|reason=no completed H4 bar available");
      return false;
     }

   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   const int copied=CopyRates(_Symbol,SIGNAL_TF,HA_WARMUP_START,last_completed,rates);
   if(copied<=0)
     {
      PrintFormat("V13_INIT_FAIL|reason=CopyRates warmup failed|err=%d",GetLastError());
      return false;
     }

   bool seeded=false;
   double prev_ha_open=0.0;
   double prev_ha_close=0.0;
   int prev_color=0;
   datetime final_time=0;

   for(int i=0;i<copied;i++)
     {
      if(rates[i].time>last_completed)
         break;

      const double hc=(rates[i].open+rates[i].high+rates[i].low+rates[i].close)/4.0;
      double ho=0.0;
      if(!seeded)
        {
         ho=(rates[i].open+rates[i].close)/2.0;
         seeded=true;
        }
      else
        {
         ho=(prev_ha_open+prev_ha_close)/2.0;
        }

      const int ha_color=HAColor(ho,hc,prev_color);
      prev_ha_open=ho;
      prev_ha_close=hc;
      prev_color=ha_color;
      final_time=rates[i].time;
     }

   if(!seeded || final_time!=last_completed)
     {
      PrintFormat("V13_INIT_FAIL|reason=warmup did not reach last completed H4|last=%s|final=%s|copied=%d",
                  TimeToString(last_completed,TIME_DATE|TIME_MINUTES),
                  TimeToString(final_time,TIME_DATE|TIME_MINUTES),copied);
      return false;
     }

   g_last_ha_open=prev_ha_open;
   g_last_ha_close=prev_ha_close;
   g_last_ha_color=prev_color;
   g_ha_ready=true;
   g_last_signal=last_completed;

   if(InpVerbose)
      PrintFormat("V13_INIT|symbol=%s|last_completed=%s|ha_open=%.5f|ha_close=%.5f|color=%d|warmup_bars=%d",
                  _Symbol,TimeToString(last_completed,TIME_DATE|TIME_MINUTES),
                  g_last_ha_open,g_last_ha_close,g_last_ha_color,copied);
   return true;
  }

//+------------------------------------------------------------------+
bool TradeRetcodeDone()
  {
   return((uint)trade.ResultRetcode()==TRADE_RETCODE_DONE);
  }

//+------------------------------------------------------------------+
bool PlaceChild(const int direction,const datetime signal_bar_time,const datetime execution_bar_time)
  {
   if(g_children>=MAX_CHILDREN)
      return true;

   const int next_child=g_children+1;
   const string comment=StringFormat("V13|J%06d|C%02d|%s",
                                     g_journey_id,next_child,
                                     direction>0 ? "L" : "S");

   ResetLastError();
   bool request_ok=false;
   if(direction>0)
      request_ok=trade.Buy(InpLotPerChild,_Symbol,0.0,0.0,0.0,comment);
   else
      request_ok=trade.Sell(InpLotPerChild,_Symbol,0.0,0.0,0.0,comment);

   if(!request_ok || !TradeRetcodeDone())
     {
      PrintFormat("V13_ORDER_FAIL|action=ENTRY|journey=%d|child=%d|dir=%s|signal=%s|exec_bar=%s|retcode=%u|ret=%s|last_error=%d",
                  g_journey_id,next_child,DirectionName(direction),
                  TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),
                  TimeToString(execution_bar_time,TIME_DATE|TIME_MINUTES),
                  (uint)trade.ResultRetcode(),trade.ResultRetcodeDescription(),GetLastError());
      const uint code=(uint)trade.ResultRetcode();
      if(Retryable(code) && CountOwnPositions()==g_children)
         DeferExecution("ENTRY",code);
      else
         HaltRun(StringFormat("ENTRY unresolved/permanent failure; do not resend retcode=%u",code));
      return false;
     }

   // DONE must correspond to exactly one full independent hedging position.
   if(CountOwnPositions()!=g_children+1 ||
      MathAbs(trade.ResultVolume()-InpLotPerChild)>1e-8)
     {
      HaltRun("ENTRY success cannot be reconciled to one full Child");
      return false;
     }

   g_children=next_child;
   ResetRetry();
   PrintFormat("V13_EVENT|ENTRY|journey=%d|child=%d|dir=%s|signal=%s|exec=%s|deal=%I64u|price=%.5f|volume=%.2f",
               g_journey_id,g_children,DirectionName(direction),
               TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),
               TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),
               trade.ResultDeal(),trade.ResultPrice(),InpLotPerChild);
   return true;
  }

//+------------------------------------------------------------------+
bool CloseAllJourneyPositions(const datetime signal_bar_time,const datetime execution_bar_time)
  {
   const int expected=CountOwnPositions();
   if(expected>g_children)
     {
      PrintFormat("V13_STATE_FAIL|reason=position_count_mismatch_before_close|journey=%d|children=%d|positions=%d",
                  g_journey_id,g_children,expected);
      HaltRun("unexpected extra positions during close");
      return false;
     }

   for(int n=0;n<expected;n++)
     {
      const ulong ticket=LowestOwnPositionTicket();
      if(ticket==0 || !PositionSelectByTicket(ticket))
        {
         PrintFormat("V13_ORDER_FAIL|action=SELECT_FOR_CLOSE|journey=%d|ticket=%I64u|last_error=%d",
                     g_journey_id,ticket,GetLastError());
         HaltRun("cannot select own position during close");
         return false;
        }

      const string child_comment=PositionGetString(POSITION_COMMENT);
      const double volume=PositionGetDouble(POSITION_VOLUME);
      const double entry_price=PositionGetDouble(POSITION_PRICE_OPEN);

      ResetLastError();
      const bool request_ok=trade.PositionClose(ticket,(ulong)InpDeviationPoints);
      const uint code=(uint)trade.ResultRetcode();
      const bool remains=PositionSelectByTicket(ticket);
      if((!request_ok || !TradeRetcodeDone()) || remains)
        {
         PrintFormat("V13_ORDER_FAIL|action=EXIT|journey=%d|ticket=%I64u|comment=%s|signal=%s|exec_bar=%s|retcode=%u|ret=%s|last_error=%d",
                     g_journey_id,ticket,child_comment,
                     TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),
                     TimeToString(execution_bar_time,TIME_DATE|TIME_MINUTES),
                     (uint)trade.ResultRetcode(),trade.ResultRetcodeDescription(),GetLastError());
         if(code==TRADE_RETCODE_DONE_PARTIAL && remains &&
            PositionGetDouble(POSITION_VOLUME)<volume)
            DeferExecution("EXIT_REMAINDER",code);
         else if(Retryable(code) && remains &&
                 MathAbs(PositionGetDouble(POSITION_VOLUME)-volume)<1e-8)
            DeferExecution("EXIT",code);
         else if(code==TRADE_RETCODE_POSITION_CLOSED && !remains)
            continue;
         else
            HaltRun(StringFormat("EXIT unresolved/permanent failure; retcode=%u",code));
         return false;
        }

      ResetRetry();

      PrintFormat("V13_EVENT|EXIT|journey=%d|ticket=%I64u|comment=%s|signal=%s|exec=%s|deal=%I64u|entry=%.5f|exit=%.5f|volume=%.2f",
                  g_journey_id,ticket,child_comment,
                  TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),
                  TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),
                  trade.ResultDeal(),entry_price,trade.ResultPrice(),volume);
     }

   const int remaining=CountOwnPositions();
   if(remaining!=0)
     {
      PrintFormat("V13_STATE_FAIL|reason=positions_remain_after_close|journey=%d|remaining=%d",
                  g_journey_id,remaining);
      HaltRun("unexpected remaining positions after close");
      return false;
     }

   return true;
  }

//+------------------------------------------------------------------+
bool StartJourney(const int direction,const datetime signal_bar_time,const datetime execution_bar_time)
  {
   g_journey_id++;
   g_journey_direction=direction;
   g_children=0;
   g_active_journey=true;

   PrintFormat("V13_EVENT|JOURNEY_START|journey=%d|dir=%s|signal=%s|exec_bar=%s",
               g_journey_id,DirectionName(direction),
               TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),
               TimeToString(execution_bar_time,TIME_DATE|TIME_MINUTES));

   g_pending_entry=true;
   return true;
  }

//+------------------------------------------------------------------+
void ServiceExecution()
  {
   if(g_halted || TimeCurrent()<g_next_attempt)
      return;
   if(g_pending_close)
     {
      if(!CloseAllJourneyPositions(g_signal_time,g_execution_bar))
         return;
      PrintFormat("V13_EVENT|JOURNEY_END|journey=%d|children=%d|exec=%s",
                  g_journey_id,g_children,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS));
      g_pending_close=false;
      g_active_journey=false;
      g_children=0;
      g_journey_direction=0;
      // Closing is latched. Reopen only in the latest completed HA direction,
      // not a stale reversal that failed hours ago.
      StartJourney(g_target_color,g_signal_time,g_execution_bar);
     }
   if(g_pending_entry)
     {
      if(CountOwnPositions()!=g_children)
        {
         HaltRun("position mismatch before pending ENTRY");
         return;
        }
      if(PlaceChild(g_journey_direction,g_signal_time,g_execution_bar))
         g_pending_entry=false;
     }
  }

// Signal consumption never submits orders. This prevents catch-up orders when
// history is temporarily unavailable and several bars arrive together.
void ObserveCompletedH4(const MqlRates &completed,const datetime execution_bar_time)
  {
   const datetime signal_bar_time=completed.time;
   const int previous_color=g_last_ha_color;
   const double hc=(completed.open+completed.high+completed.low+completed.close)/4.0;
   const double ho=(g_last_ha_open+g_last_ha_close)/2.0;
   const int ha_color=HAColor(ho,hc,previous_color);

   // Advance HA state exactly once for this newly completed H4 bar.
   g_last_ha_open=ho;
   g_last_ha_close=hc;
   g_last_ha_color=ha_color;
   g_last_signal=signal_bar_time;

   if(g_pending_entry)
      PrintFormat("V13_ENTRY_EXPIRED|old_signal=%s|new_signal=%s",
                  TimeToString(g_signal_time,TIME_DATE|TIME_MINUTES),
                  TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES));
   g_pending_entry=false;
   g_signal_time=signal_bar_time;
   g_execution_bar=execution_bar_time;
   g_target_color=ha_color;

   if(InpVerbose)
      PrintFormat("V13_EVENT|HA_CLOSE|bar=%s|known_at=%s|ha_open=%.5f|ha_close=%.5f|color=%d|prev_color=%d",
                  TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),
                  TimeToString(execution_bar_time,TIME_DATE|TIME_MINUTES),
                  ho,hc,ha_color,previous_color);

   // Warm-up/state before the evaluation boundary may update HA only.
   if(signal_bar_time<EVALUATION_START)
      return;

   if(ha_color==0 || previous_color==0)
      return;

   if(g_pending_close)
      return; // continue closing even if color changes again before market opens

   if(!g_active_journey)
     {
      // Start flat. The first V13 Journey requires a new post-boundary color flip.
      if(ha_color!=previous_color)
         StartJourney(ha_color,signal_bar_time,execution_bar_time);
      return;
     }

   const int actual_positions=CountOwnPositions();
   if(actual_positions!=g_children)
     {
      HaltRun(StringFormat("active Child/position mismatch children=%d positions=%d",
                           g_children,actual_positions));
      return;
     }

   if(ha_color==g_journey_direction)
     {
      if(g_children<MAX_CHILDREN)
        {
         g_pending_entry=true;
        }
      else if(InpVerbose)
        {
         PrintFormat("V13_EVENT|CAP_HOLD|journey=%d|dir=%s|signal=%s|children=%d",
                     g_journey_id,DirectionName(g_journey_direction),
                     TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),g_children);
        }
      return;
     }

   // Opposite completed HA: close all old Children, then start the opposite Journey.
   g_pending_close=true;
   ResetRetry(); // a newly required exit takes priority over a failed entry
  }

bool ProcessCompletedH4(const datetime execution_bar_time)
  {
   MqlRates completed[];
   ArraySetAsSeries(completed,false);
   const datetime latest=iTime(_Symbol,SIGNAL_TF,1);
   if(latest<=g_last_signal)
      return false;
   ResetLastError();
   const int copied=CopyRates(_Symbol,SIGNAL_TF,g_last_signal+1,latest,completed);
   // Do not mark the H4 boundary consumed before its data are actually present.
   if(copied<=0 || completed[copied-1].time!=latest)
     {
      if(TimeCurrent()>=g_next_attempt)
        {
         PrintFormat("V13_HISTORY_WAIT|err=%d|latest=%s",GetLastError(),TimeToString(latest));
         g_next_attempt=TimeCurrent()+5;
        }
      return false;
     }
   for(int i=0;i<copied && !g_halted;i++)
      ObserveCompletedH4(completed[i],execution_bar_time);
   return !g_halted;
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      Print("V13_INIT_FAIL|reason=hedging position mode required for independent Child positions");
      return INIT_FAILED;
     }

   if(InpDeviationPoints<0 || InpMagicNumber<=0 || !ValidateRequestedVolume())
     {
      PrintFormat("V13_INIT_FAIL|reason=invalid InpLotPerChild %.8f for symbol volume constraints",InpLotPerChild);
      return INIT_FAILED;
     }

   if(CountOwnPositions()!=0)
     {
      Print("V13_INIT_FAIL|reason=pre-existing position with V13 magic on current symbol");
      return INIT_FAILED;
     }

   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpDeviationPoints);
   if(!trade.SetTypeFillingBySymbol(_Symbol))
     {
      Print("V13_INIT_FAIL|reason=unsupported symbol filling mode");
      return INIT_FAILED;
     }
   trade.SetAsyncMode(false);

   g_current_h4_open=iTime(_Symbol,SIGNAL_TF,0);
   if(g_current_h4_open<=0)
     {
      Print("V13_INIT_FAIL|reason=current H4 bar unavailable");
      return INIT_FAILED;
     }

   if(!InitializeHAState())
      return INIT_FAILED;

   PrintFormat("V13_READY|symbol=%s|evaluation_start=%s|max_children=%d|lot_per_child=%.2f|magic=%I64d|current_h4=%s",
               _Symbol,TimeToString(EVALUATION_START,TIME_DATE|TIME_MINUTES),
               MAX_CHILDREN,InpLotPerChild,InpMagicNumber,
               TimeToString(g_current_h4_open,TIME_DATE|TIME_MINUTES));
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   PrintFormat("V13_DEINIT|reason=%d|halted=%s|active=%s|journey=%d|children=%d|positions=%d|retries=%d|pending_entry=%d|pending_close=%d",
               reason,g_halted ? "true" : "false",
               g_active_journey ? "true" : "false",
               g_journey_id,g_children,CountOwnPositions(),g_retry_count,g_pending_entry,g_pending_close);
  }

//+------------------------------------------------------------------+
void OnTick()
  {
   if(g_halted || !g_ha_ready)
      return;

   const datetime current_h4_open=iTime(_Symbol,SIGNAL_TF,0);
   if(current_h4_open<=0)
      return;

   if(current_h4_open!=g_current_h4_open)
     {
      if(!ProcessCompletedH4(current_h4_open))
         return; // never execute a stale pending entry while new HA is unknown
      g_current_h4_open=current_h4_open;
     }
   ServiceExecution();
  }
//+------------------------------------------------------------------+
