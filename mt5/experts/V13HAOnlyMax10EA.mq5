//+------------------------------------------------------------------+
//| V13HAOnlyMax10EA.mq5                                             |
//| V13 Baseline 0: standard H4 Heikin-Ashi, max-10 Journey.         |
//| GOLD# / RESEARCH TESTER ONLY / NO PRODUCTION AUTHORITY           |
//+------------------------------------------------------------------+
#property strict
#property version   "13.001"
#property description "V13 Baseline 0: standard H4 HA, one Child per same-color completed bar, max 10, opposite HA close-all/reverse."

#include <Trade/Trade.mqh>

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
      return false;
     }

   g_children=next_child;
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
   if(expected!=g_children)
     {
      PrintFormat("V13_STATE_FAIL|reason=position_count_mismatch_before_close|journey=%d|children=%d|positions=%d",
                  g_journey_id,g_children,expected);
      return false;
     }

   for(int n=0;n<expected;n++)
     {
      const ulong ticket=LowestOwnPositionTicket();
      if(ticket==0 || !PositionSelectByTicket(ticket))
        {
         PrintFormat("V13_ORDER_FAIL|action=SELECT_FOR_CLOSE|journey=%d|ticket=%I64u|last_error=%d",
                     g_journey_id,ticket,GetLastError());
         return false;
        }

      const string child_comment=PositionGetString(POSITION_COMMENT);
      const double volume=PositionGetDouble(POSITION_VOLUME);
      const double entry_price=PositionGetDouble(POSITION_PRICE_OPEN);

      ResetLastError();
      const bool request_ok=trade.PositionClose(ticket,(ulong)InpDeviationPoints);
      if(!request_ok || !TradeRetcodeDone())
        {
         PrintFormat("V13_ORDER_FAIL|action=EXIT|journey=%d|ticket=%I64u|comment=%s|signal=%s|exec_bar=%s|retcode=%u|ret=%s|last_error=%d",
                     g_journey_id,ticket,child_comment,
                     TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),
                     TimeToString(execution_bar_time,TIME_DATE|TIME_MINUTES),
                     (uint)trade.ResultRetcode(),trade.ResultRetcodeDescription(),GetLastError());
         return false;
        }

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

   if(!PlaceChild(direction,signal_bar_time,execution_bar_time))
     {
      PrintFormat("V13_PENDING_ENTRY retcode=%u desc=%s", trade.ResultRetcode(), trade.ResultRetcodeDescription());
      return false;
     }
   return true;
  }

//+------------------------------------------------------------------+
void ProcessCompletedH4(const datetime execution_bar_time)
  {
   MqlRates completed[1];
   const int copied=CopyRates(_Symbol,SIGNAL_TF,1,1,completed);
   if(copied!=1)
     {
      PrintFormat("V13_PENDING_ENTRY retcode=%u desc=%s", trade.ResultRetcode(), trade.ResultRetcodeDescription());
      return;
     }

   const datetime signal_bar_time=completed[0].time;
   const int previous_color=g_last_ha_color;
   const double hc=(completed[0].open+completed[0].high+completed[0].low+completed[0].close)/4.0;
   const double ho=(g_last_ha_open+g_last_ha_close)/2.0;
   const int ha_color=HAColor(ho,hc,previous_color);

   // Advance HA state exactly once for this newly completed H4 bar.
   g_last_ha_open=ho;
   g_last_ha_close=hc;
   g_last_ha_color=ha_color;

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
         if(!PlaceChild(g_journey_direction,signal_bar_time,execution_bar_time))
            HaltRun("same-color Child entry failed");
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
   const int old_journey=g_journey_id;
   const int old_children=g_children;
   const int old_direction=g_journey_direction;

   if(!CloseAllJourneyPositions(signal_bar_time,execution_bar_time))
     {
      HaltRun("Journey close-all failed");
      return;
     }

   PrintFormat("V13_EVENT|JOURNEY_END|journey=%d|dir=%s|children=%d|signal=%s|exec=%s",
               old_journey,DirectionName(old_direction),old_children,
               TimeToString(signal_bar_time,TIME_DATE|TIME_MINUTES),
               TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS));

   g_active_journey=false;
   g_journey_direction=0;
   g_children=0;

   StartJourney(ha_color,signal_bar_time,execution_bar_time);
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      Print("V13_INIT_FAIL|reason=hedging position mode required for independent Child positions");
      return INIT_FAILED;
     }

   if(!ValidateRequestedVolume())
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
   trade.SetTypeFillingBySymbol(_Symbol);
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
   PrintFormat("V13_DEINIT|reason=%d|halted=%s|active=%s|journey=%d|children=%d|positions=%d",
               reason,g_halted ? "true" : "false",
               g_active_journey ? "true" : "false",
               g_journey_id,g_children,CountOwnPositions());
  }

//+------------------------------------------------------------------+
void OnTick()
  {
   if(g_halted || !g_ha_ready)
      return;

   const datetime current_h4_open=iTime(_Symbol,SIGNAL_TF,0);
   if(current_h4_open<=0 || current_h4_open==g_current_h4_open)
      return;

   g_current_h4_open=current_h4_open;
   ProcessCompletedH4(current_h4_open);
  }
//+------------------------------------------------------------------+
