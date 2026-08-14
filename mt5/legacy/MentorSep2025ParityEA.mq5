//+------------------------------------------------------------------+
//| MentorSep2025ParityEA.mq5                                       |
//| Calibration bridge between the September 2025 blind ledger and  |
//| MT5 Strategy Tester execution.                                  |
//|                                                                  |
//| IMPORTANT: the reference ledger schedules decisions in this EA.  |
//| It is not the autonomous Mentor strategy. Its purpose is to prove |
//| timestamp, Bid/Ask, pending-order and SL/TP parity before the      |
//| discretionary structure detector replaces the fixture scheduler. |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "September 2025 GOLD manual-ledger parity calibration"

#include <Trade/Trade.mqh>

input long     InpMagicNumber=26080901;
input bool     InpRequireMtfEvidence=true;
input bool     InpUseStopForCrossEntry=true;
input double   InpPriceTolerance=0.03;
input int      InpDecisionTimeOffsetMinutes=0;
input int      InpMaxEntryWaitMinutes=240;
input bool     InpWriteParityCsv=true;

struct ReferenceTrade
  {
   string id;
   datetime decision_at;
   datetime expected_fill_at;
   datetime expected_close_at;
   bool bullish;
   string scope;
   string execution_model;
   ENUM_TIMEFRAMES root_tf;
   datetime root_time;
   double root_low;
   double root_high;
   ENUM_TIMEFRAMES child_tf;
   datetime child_time;
   double child_low;
   double child_high;
   double entry;
   double stop_loss;
   double take_profit;
   string expected_result;
  };

CTrade g_trade;
ReferenceTrade g_reference[];
int g_next=0;
string g_active_id="";
datetime g_active_decision=0;
bool g_active_pending=false;
bool g_active_position=false;

datetime D(const string value)
  {
   return StringToTime(value)+InpDecisionTimeOffsetMinutes*60;
  }

void AddReference(const string id,
                  const string decision_at,
                  const string fill_at,
                  const string close_at,
                  const bool bullish,
                  const string scope,
                  const string model,
                  const ENUM_TIMEFRAMES root_tf,
                  const string root_time,
                  const double root_low,
                  const double root_high,
                  const ENUM_TIMEFRAMES child_tf,
                  const string child_time,
                  const double child_low,
                  const double child_high,
                  const double entry,
                  const double stop_loss,
                  const double take_profit,
                  const string expected_result)
  {
   int index=ArraySize(g_reference);
   ArrayResize(g_reference,index+1);
   g_reference[index].id=id;
   g_reference[index].decision_at=D(decision_at);
   g_reference[index].expected_fill_at=D(fill_at);
   g_reference[index].expected_close_at=D(close_at);
   g_reference[index].bullish=bullish;
   g_reference[index].scope=scope;
   g_reference[index].execution_model=model;
   g_reference[index].root_tf=root_tf;
   g_reference[index].root_time=D(root_time);
   g_reference[index].root_low=root_low;
   g_reference[index].root_high=root_high;
   g_reference[index].child_tf=child_tf;
   g_reference[index].child_time=D(child_time);
   g_reference[index].child_low=child_low;
   g_reference[index].child_high=child_high;
   g_reference[index].entry=entry;
   g_reference[index].stop_loss=stop_loss;
   g_reference[index].take_profit=take_profit;
   g_reference[index].expected_result=expected_result;
  }

void LoadReferenceLedger()
  {
   ArrayResize(g_reference,0);
   AddReference("M50-001","2025.09.03 02:51","2025.09.03 03:04","2025.09.03 03:24",true,"EXTERNAL_CONTINUATION","HTF_OB_REACTION",PERIOD_M15,"2025.09.02 21:45",3525.08,3529.79,PERIOD_M5,"2025.09.02 21:50",3525.08,3527.25,3528.57,3524.75,3539.90,"TP");
   AddReference("M50-002","2025.09.04 04:36","2025.09.04 05:00","2025.09.04 06:11",false,"EXTERNAL_CONTINUATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M30,"2025.09.03 21:00",3574.21,3578.29,PERIOD_M5,"2025.09.03 21:10",3576.45,3578.24,3549.68,3553.52,3525.08,"TP");
   AddReference("M50-003","2025.09.04 19:28","2025.09.04 19:28","2025.09.05 06:54",false,"EXTERNAL_CONTINUATION","HTF_OB_REACTION",PERIOD_M15,"2025.09.04 16:15",3544.92,3554.09,PERIOD_M5,"2025.09.04 16:35",3553.00,3558.61,3552.46,3559.01,3510.52,"SL");
   AddReference("M50-004","2025.09.05 18:39","2025.09.05 18:39","2025.09.05 19:06",true,"EXTERNAL_CONTINUATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M30,"2025.09.05 14:00",3548.64,3555.05,PERIOD_M15,"2025.09.05 15:00",3548.67,3554.60,3591.63,3588.69,3597.78,"TP");
   AddReference("M50-005","2025.09.10 05:07","2025.09.10 05:22","2025.09.11 12:13",true,"EXTERNAL_CONTINUATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M15,"2025.09.10 04:15",3620.11,3627.29,PERIOD_M5,"2025.09.10 04:25",3620.11,3625.93,3632.96,3619.75,3674.52,"SL");
   AddReference("M50-006","2025.09.11 22:20","2025.09.11 22:25","2025.09.15 18:50",true,"EXTERNAL_CONTINUATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M15,"2025.09.11 17:30",3626.77,3635.28,PERIOD_M5,"2025.09.11 17:40",3626.77,3631.33,3635.48,3626.40,3674.52,"TP");
   AddReference("M50-007","2025.09.16 15:05","2025.09.16 15:06","2025.09.16 15:30",false,"INTERNAL_ROTATION","HTF_OB_REACTION",PERIOD_M15,"2025.09.16 12:45",3696.06,3698.80,PERIOD_M5,"2025.09.16 12:55",3697.37,3698.61,3695.68,3699.74,3690.40,"TP");
   AddReference("M50-008","2025.09.17 15:48","2025.09.17 15:50","2025.09.17 21:01",true,"EXTERNAL_CONTINUATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M15,"2025.09.17 14:45",3664.30,3669.81,PERIOD_M5,"2025.09.17 14:55",3664.30,3666.09,3676.02,3663.91,3702.86,"SL");
   AddReference("M50-009","2025.09.18 10:42","2025.09.18 11:10","2025.09.18 16:44",true,"EXTERNAL_CONTINUATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M15,"2025.09.15 15:15",3636.72,3640.61,PERIOD_M5,"2025.09.15 15:25",3637.08,3640.10,3654.60,3633.43,3707.32,"SL");
   AddReference("M50-010","2025.09.19 04:07","2025.09.19 04:46","2025.09.19 04:51",true,"EXTERNAL_CONTINUATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M15,"2025.09.18 17:15",3634.28,3640.79,PERIOD_M5,"2025.09.18 17:25",3634.75,3637.57,3645.24,3633.96,3707.32,"SL");
   AddReference("M50-011","2025.09.19 14:00","2025.09.19 14:03","2025.09.19 14:55",false,"INTERNAL_ROTATION","HTF_OB_REACTION",PERIOD_M15,"2025.09.19 08:15",3656.24,3659.66,PERIOD_M5,"2025.09.19 08:25",3657.19,3658.33,3655.40,3660.02,3646.47,"TP");
   AddReference("M50-012","2025.09.22 06:16","2025.09.22 06:17","2025.09.22 09:34",true,"EXTERNAL_CONTINUATION","HTF_OB_REACTION",PERIOD_M15,"2025.09.22 05:45",3685.35,3688.77,PERIOD_M5,"2025.09.22 05:55",3686.22,3687.65,3690.35,3684.99,3707.32,"TP");
   AddReference("M50-013","2025.09.23 20:34","2025.09.23 20:38","2025.09.23 21:45",false,"INTERNAL_ROTATION","HTF_OB_REACTION",PERIOD_M15,"2025.09.23 16:30",3780.45,3788.65,PERIOD_M5,"2025.09.23 16:35",3785.10,3787.33,3779.80,3787.65,3764.92,"TP");
   AddReference("M50-014","2025.09.25 17:57","2025.09.25 18:00","2025.09.25 18:15",true,"EXTERNAL_CONTINUATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M30,"2025.09.24 22:00",3717.39,3724.29,PERIOD_M15,"2025.09.24 22:15",3717.39,3721.42,3729.25,3717.04,3736.37,"TP");
   AddReference("M50-015","2025.09.29 04:48","2025.09.29 04:52","2025.09.29 05:15",true,"EXTERNAL_CONTINUATION","HTF_OB_REACTION",PERIOD_M30,"2025.09.29 02:30",3766.26,3772.36,PERIOD_M5,"2025.09.29 02:55",3766.26,3768.33,3773.99,3765.86,3788.57,"TP");
   AddReference("M50-016","2025.09.29 17:19","2025.09.29 17:21","2025.09.29 18:04",false,"INTERNAL_ROTATION","DELIVERY_FVG_REPLACEMENT",PERIOD_M15,"2025.09.29 14:45",3824.03,3831.24,PERIOD_M5,"2025.09.29 14:55",3828.01,3831.24,3819.07,3831.60,3809.20,"SL");
  }

double NormalizePrice(const double value)
  {
   return NormalizeDouble(value,(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS));
  }

double MinimumVolume()
  {
   double volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   return volume>0.0 ? volume : 0.01;
  }

bool HasManagedPosition()
  {
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      string symbol=PositionGetSymbol(i);
      if(symbol==_Symbol && (long)PositionGetInteger(POSITION_MAGIC)==InpMagicNumber)
         return true;
     }
   return false;
  }

bool HasManagedOrder()
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0 || !OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL)==_Symbol && (long)OrderGetInteger(ORDER_MAGIC)==InpMagicNumber)
         return true;
     }
   return false;
  }

bool HasManagedExposure()
  {
   return HasManagedPosition() || HasManagedOrder();
  }

bool ReadBarAt(const ENUM_TIMEFRAMES tf,const datetime open_time,MqlRates &bar)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates,false);
   int copied=CopyRates(_Symbol,tf,open_time,1,rates);
   if(copied!=1 || rates[0].time!=open_time)
      return false;
   bar=rates[0];
   return true;
  }

bool RangeContains(const MqlRates &bar,const double low,const double high)
  {
   return low>=bar.low-InpPriceTolerance && high<=bar.high+InpPriceTolerance && high>low;
  }

bool OppositeColour(const MqlRates &bar,const bool bullish)
  {
   if(bullish)
      return bar.close<bar.open;
   return bar.close>bar.open;
  }

bool ValidateFixtureEvidence(const ReferenceTrade &item,string &reason)
  {
   MqlRates root,child;
   if(!ReadBarAt(item.root_tf,item.root_time,root))
     {
      reason="ROOT_BAR_MISSING";
      return false;
     }
   if(!ReadBarAt(item.child_tf,item.child_time,child))
     {
      reason="CHILD_BAR_MISSING";
      return false;
     }
   if(!OppositeColour(root,item.bullish))
     {
      reason="ROOT_NOT_OPPOSITE_CANDLE";
      return false;
     }
   if(!RangeContains(root,item.root_low,item.root_high))
     {
      reason="ROOT_RANGE_MISMATCH";
      return false;
     }
   // A manually refined child may be a narrower sub-range of the M5/M15
   // candle. It must still be physically contained by that as-of candle.
   if(!RangeContains(child,item.child_low,item.child_high))
     {
      reason="CHILD_RANGE_MISMATCH";
      return false;
     }
   if(item.child_time>=item.decision_at || item.root_time>=item.decision_at)
     {
      reason="FUTURE_SOURCE_REFERENCE";
      return false;
     }
   if(item.bullish && !(item.stop_loss<item.entry && item.entry<item.take_profit))
     {
      reason="INVALID_LONG_GEOMETRY";
      return false;
     }
   if(!item.bullish && !(item.take_profit<item.entry && item.entry<item.stop_loss))
     {
      reason="INVALID_SHORT_GEOMETRY";
      return false;
     }
   reason="OK";
   return true;
  }

void AppendCsv(const string event_name,const ReferenceTrade &item,const string detail)
  {
   PrintFormat("MentorSepParity [%s] %s %s",event_name,item.id,detail);
   if(!InpWriteParityCsv)
      return;
   string path="trading_journal\\mentor_sep2025_parity_v2.csv";
   bool exists=FileIsExist(path);
   int handle=FileOpen(path,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_SHARE_READ|FILE_SHARE_WRITE,',');
   if(handle==INVALID_HANDLE)
      return;
   if(!exists)
      FileWrite(handle,"event","reference_id","tester_time","direction","entry","sl","tp","detail");
   FileSeek(handle,0,SEEK_END);
   FileWrite(handle,event_name,item.id,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),item.bullish?"long":"short",DoubleToString(item.entry,_Digits),DoubleToString(item.stop_loss,_Digits),DoubleToString(item.take_profit,_Digits),detail);
   FileClose(handle);
  }

bool SendReferenceOrder(const ReferenceTrade &item)
  {
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick))
      return false;
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(30);
   double volume=MinimumVolume();
   double entry=NormalizePrice(item.entry);
   double sl=NormalizePrice(item.stop_loss);
   double tp=NormalizePrice(item.take_profit);
   bool sent=false;
   string comment="MentorParity "+item.id;

   if(item.bullish)
     {
      if(entry>tick.ask && InpUseStopForCrossEntry)
         sent=g_trade.BuyStop(volume,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0,comment);
      else
         sent=g_trade.BuyLimit(volume,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0,comment);
     }
   else
     {
      if(entry<tick.bid && InpUseStopForCrossEntry)
         sent=g_trade.SellStop(volume,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0,comment);
      else
         sent=g_trade.SellLimit(volume,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0,comment);
     }
   if(!sent)
     {
      AppendCsv("ORDER_REJECTED",item,StringFormat("ret=%u %s bid=%.2f ask=%.2f",g_trade.ResultRetcode(),g_trade.ResultRetcodeDescription(),tick.bid,tick.ask));
      return false;
     }
   g_active_id=item.id;
   g_active_decision=item.decision_at;
   g_active_pending=true;
   AppendCsv("ORDER_SENT",item,StringFormat("ticket=%I64u bid=%.2f ask=%.2f expected_fill=%s",g_trade.ResultOrder(),tick.bid,tick.ask,TimeToString(item.expected_fill_at,TIME_DATE|TIME_MINUTES)));
   return true;
  }

void CancelExpiredReference(const ReferenceTrade &item)
  {
   if(!g_active_pending || g_active_position || HasManagedPosition() || !HasManagedOrder() || TimeCurrent()<=g_active_decision+InpMaxEntryWaitMinutes*60)
      return;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      ulong ticket=OrderGetTicket(i);
      if(ticket==0 || !OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL)!=_Symbol || (long)OrderGetInteger(ORDER_MAGIC)!=InpMagicNumber)
         continue;
      if(g_trade.OrderDelete(ticket))
         AppendCsv("ORDER_EXPIRED",item,"manual-ledger entry window elapsed");
     }
   g_active_pending=false;
   g_active_position=false;
   g_active_id="";
   g_next++;
  }

void ProcessSchedule()
  {
   if(g_next>=ArraySize(g_reference))
      return;
   ReferenceTrade item=g_reference[g_next];
   if(g_active_pending)
     {
      if(HasManagedPosition())
        {
         g_active_pending=false;
         g_active_position=true;
         return;
        }
      CancelExpiredReference(item);
      return;
     }
   if(g_active_position || HasManagedPosition())
      return;
   if(HasManagedExposure())
      return;
   if(TimeCurrent()<item.decision_at)
      return;
   string reason="SKIPPED";
   if(InpRequireMtfEvidence && !ValidateFixtureEvidence(item,reason))
     {
      AppendCsv("EVIDENCE_REJECTED",item,reason);
      g_next++;
      return;
     }
   SendReferenceOrder(item);
  }

int OnInit()
  {
   if(!(bool)MQLInfoInteger(MQL_TESTER))
     {
      Print("MentorSep2025ParityEA is Strategy Tester only.");
      return INIT_FAILED;
     }
   LoadReferenceLedger();
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   PrintFormat("MentorSep2025ParityEA loaded %d calibration decisions",ArraySize(g_reference));
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   ProcessSchedule();
  }

void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result)
  {
   if(trans.type!=TRADE_TRANSACTION_DEAL_ADD || trans.deal==0 || g_active_id=="")
      return;
   if(!HistoryDealSelect(trans.deal))
      return;
   long magic=HistoryDealGetInteger(trans.deal,DEAL_MAGIC);
   if(magic!=InpMagicNumber)
      return;
   long entry_type=HistoryDealGetInteger(trans.deal,DEAL_ENTRY);
   ReferenceTrade item=g_reference[g_next];
   double price=HistoryDealGetDouble(trans.deal,DEAL_PRICE);
   datetime deal_time=(datetime)HistoryDealGetInteger(trans.deal,DEAL_TIME);
   if(entry_type==DEAL_ENTRY_IN)
     {
      g_active_pending=false;
      g_active_position=true;
      AppendCsv("FILLED",item,StringFormat("actual=%s price=%.2f delta_seconds=%d",TimeToString(deal_time,TIME_DATE|TIME_SECONDS),price,(int)(deal_time-item.expected_fill_at)));
      return;
     }
   if(entry_type==DEAL_ENTRY_OUT || entry_type==DEAL_ENTRY_OUT_BY)
     {
      long reason=HistoryDealGetInteger(trans.deal,DEAL_REASON);
      string actual_result=(reason==DEAL_REASON_TP)?"TP":((reason==DEAL_REASON_SL)?"SL":"OTHER");
      AppendCsv("CLOSED",item,StringFormat("actual=%s price=%.2f result=%s expected=%s delta_seconds=%d",TimeToString(deal_time,TIME_DATE|TIME_SECONDS),price,actual_result,item.expected_result,(int)(deal_time-item.expected_close_at)));
      g_active_pending=false;
      g_active_position=false;
      g_active_id="";
      g_next++;
     }
  }

void OnDeinit(const int reason)
  {
   PrintFormat("MentorSep2025ParityEA stopped next=%d/%d reason=%d",g_next,ArraySize(g_reference),reason);
  }
