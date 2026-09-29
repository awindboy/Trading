//+------------------------------------------------------------------+
//| V13LTFRouteQ75Q50_PolicyReplayEA.mq5                            |
//| Frozen-ledger execution harness for the V13 LTF route policy.    |
//| RESEARCH TESTER ONLY / NOT AN EMBEDDED MODEL / NOT LIVE READY    |
//+------------------------------------------------------------------+
#property strict
#property version   "13.302"
#property description "V13 LTF q75-entry/q50-repair frozen policy-ledger replay EA. Research tester only."

#include <Trade/Trade.mqh>

input string InpLedgerFile       = "V13\\v13_c1_ltf_route_q75_q50_policy_ledger.csv";
input bool   InpUseCommonFiles   = true;
input string InpRequiredSymbol   = "GOLD#";
input long   InpMagicNumber      = 1303092901;
input double InpFixedLot         = 0.01;
input int    InpDeviationPoints  = 30;
input int    InpRetrySeconds     = 1;
input bool   InpVerbose          = true;

struct PolicyEvent
  {
   string   event_id;
   datetime action_time;
   int      action_order;
   string   action;
   int      direction;
   double   volume;
   string   lane;
   string   reason;
   double   expected_price;
  };

CTrade trade;
PolicyEvent g_events[];
bool        g_done[];
int         g_event_count=0;
int         g_cursor=0;
int         g_expected_open=0;
datetime    g_next_retry=0;
bool        g_halted=false;
double      g_peak_equity=0.0;
double      g_max_equity_drawdown=0.0;
int         g_max_open_positions=0;

void UpdateRiskStats()
  {
   const double equity=AccountInfoDouble(ACCOUNT_EQUITY);
   if(g_peak_equity<=0.0 || equity>g_peak_equity) g_peak_equity=equity;
   g_max_equity_drawdown=MathMax(g_max_equity_drawdown,g_peak_equity-equity);
   g_max_open_positions=MathMax(g_max_open_positions,CountOwnPositions());
  }

string Trim(string value)
  {
   StringTrimLeft(value);
   StringTrimRight(value);
   if(StringLen(value)>=2 && StringSubstr(value,0,1)=="\"" &&
      StringSubstr(value,StringLen(value)-1,1)=="\"")
      value=StringSubstr(value,1,StringLen(value)-2);
   return value;
  }

void LogEvent(const string kind,const int index,const string detail="")
  {
   const string id=(index>=0 && index<g_event_count ? g_events[index].event_id : "-");
   PrintFormat("V13Q75_EVENT|%s|row=%d|id=%s|time=%s|%s",
               kind,index+2,id,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),detail);
  }

void Halt(const string reason,const int index=-1)
  {
   if(g_halted) return;
   g_halted=true;
   LogEvent("HALT",index,"reason="+reason);
  }

bool IsRetryable(const uint code)
  {
   return(code==TRADE_RETCODE_MARKET_CLOSED ||
          code==TRADE_RETCODE_REQUOTE ||
          code==TRADE_RETCODE_PRICE_CHANGED ||
          code==TRADE_RETCODE_PRICE_OFF ||
          code==TRADE_RETCODE_TOO_MANY_REQUESTS ||
          code==TRADE_RETCODE_CONNECTION ||
          code==TRADE_RETCODE_TIMEOUT ||
          code==TRADE_RETCODE_LOCKED ||
          code==TRADE_RETCODE_FROZEN);
  }

bool IsDoneRetcode(const uint code)
  {
   return(code==TRADE_RETCODE_DONE || code==TRADE_RETCODE_DONE_PARTIAL);
  }

bool ValidateVolume(const double volume)
  {
   const double minv=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   const double maxv=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   const double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(volume<=0.0 || step<=0.0 || volume<minv-1e-12 || volume>maxv+1e-12)
      return false;
   return(MathAbs(volume/step-MathRound(volume/step))<=1e-8);
  }

int CountOwnPositions()
  {
   int count=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      const ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber) continue;
      count++;
     }
   return count;
  }

string PositionTag(const int entry_index)
  {
   return StringFormat("V13Q75|%06d",entry_index+1);
  }

int FindEntryIndex(const string event_id)
  {
   for(int i=0;i<g_event_count;i++)
      if(g_events[i].event_id==event_id && g_events[i].action=="ENTRY") return i;
   return -1;
  }

int FindExitIndex(const string event_id)
  {
   for(int i=0;i<g_event_count;i++)
      if(g_events[i].event_id==event_id && g_events[i].action=="EXIT") return i;
   return -1;
  }

ulong FindPositionForEvent(const string event_id)
  {
   const int entry_index=FindEntryIndex(event_id);
   if(entry_index<0) return 0;
   const string tag=PositionTag(entry_index);
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      const ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber) continue;
      if(PositionGetString(POSITION_COMMENT)==tag) return ticket;
     }
   return 0;
  }

bool Reconcile(const int index)
  {
   const int actual=CountOwnPositions();
   if(actual==g_expected_open) return true;
   Halt(StringFormat("position_count_mismatch expected=%d actual=%d",g_expected_open,actual),index);
   return false;
  }

bool ParseDirection(const string text,int &direction)
  {
   const string value=Trim(text);
   if(value=="LONG" || value=="BUY" || value=="1") { direction=1; return true; }
   if(value=="SHORT" || value=="SELL" || value=="-1") { direction=-1; return true; }
   if(value=="" || value=="0") { direction=0; return true; }
   return false;
  }

bool LoadLedger()
  {
   int flags=FILE_READ|FILE_TXT|FILE_ANSI;
   if(InpUseCommonFiles) flags|=FILE_COMMON;
   ResetLastError();
   const int handle=FileOpen(InpLedgerFile,flags);
   if(handle==INVALID_HANDLE)
     {
      PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=ledger_open|file=%s|err=%d",InpLedgerFile,GetLastError());
      return false;
     }

   if(FileIsEnding(handle)) { FileClose(handle); return false; }
   string header=FileReadString(handle);
   StringReplace(header,"\r","");
   if(Trim(header)!="event_id,action_time,action_order,action,direction,volume,policy_lane,reason,expected_price")
     {
      PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=bad_header|header=%s",header);
      FileClose(handle); return false;
     }

   while(!FileIsEnding(handle))
     {
      string line=FileReadString(handle);
      StringReplace(line,"\r","");
      if(StringLen(Trim(line))==0) continue;
      string fields[];
      const int n=StringSplit(line,StringGetCharacter(",",0),fields);
      if(n!=9)
        {
         PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=bad_column_count|row=%d|columns=%d",g_event_count+2,n);
         FileClose(handle); return false;
        }
      ArrayResize(g_events,g_event_count+1);
      PolicyEvent e;
      e.event_id=Trim(fields[0]);
      e.action_time=StringToTime(Trim(fields[1]));
      e.action_order=(int)StringToInteger(Trim(fields[2]));
      e.action=Trim(fields[3]);
      if(!ParseDirection(fields[4],e.direction))
        {
         PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=bad_direction|row=%d",g_event_count+2);
         FileClose(handle); return false;
        }
      e.volume=StringToDouble(Trim(fields[5]));
      e.lane=Trim(fields[6]);
      e.reason=Trim(fields[7]);
      e.expected_price=StringToDouble(Trim(fields[8]));
      if(e.event_id=="" || e.action_time<=0 || (e.action!="ENTRY" && e.action!="EXIT"))
        {
         PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=bad_required_field|row=%d",g_event_count+2);
         FileClose(handle); return false;
        }
      if(e.action=="ENTRY" && (e.direction==0 || MathAbs(e.volume-InpFixedLot)>1e-8))
        {
         PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=entry_contract_mismatch|row=%d|volume=%.4f",g_event_count+2,e.volume);
         FileClose(handle); return false;
        }
      if(g_event_count>0)
        {
         PolicyEvent p=g_events[g_event_count-1];
         if(e.action_time<p.action_time || (e.action_time==p.action_time && e.action_order<p.action_order))
           {
            PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=unsorted_ledger|row=%d",g_event_count+2);
           FileClose(handle); return false;
           }
        }
      g_events[g_event_count]=e;
      g_event_count++;
     }
   FileClose(handle);
   if(g_event_count==0) return false;

   for(int i=0;i<g_event_count;i++)
     {
      int entries=0,exits=0;
      for(int j=0;j<g_event_count;j++)
        if(g_events[j].event_id==g_events[i].event_id)
          {
           if(g_events[j].action=="ENTRY") entries++;
           if(g_events[j].action=="EXIT") exits++;
          }
      if(entries!=1 || exits!=1 || FindExitIndex(g_events[i].event_id)<FindEntryIndex(g_events[i].event_id))
        {
         PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=event_pair_invalid|id=%s|entries=%d|exits=%d",g_events[i].event_id,entries,exits);
         return false;
        }
     }
   ArrayResize(g_done,g_event_count);
   ArrayInitialize(g_done,false);
   return true;
  }

bool EntryExpired(const int index)
  {
   const int exit_index=FindExitIndex(g_events[index].event_id);
   return(exit_index>=0 && TimeCurrent()>=g_events[exit_index].action_time);
  }

bool ExecuteEntry(const int index)
  {
   PolicyEvent e=g_events[index];
   if(EntryExpired(index))
     {
      g_done[index]=true;
      LogEvent("ENTRY_EXPIRED",index,"reason=first_executable_tick_after_policy_exit");
      return true;
     }
   if(!Reconcile(index)) return false;
   const string tag=PositionTag(index);
   const double balance_before=AccountInfoDouble(ACCOUNT_BALANCE);
   ResetLastError();
   const bool request_ok=(e.direction>0)
      ? trade.Buy(InpFixedLot,_Symbol,0.0,0.0,0.0,tag)
      : trade.Sell(InpFixedLot,_Symbol,0.0,0.0,0.0,tag);
   const uint code=(uint)trade.ResultRetcode();
   if(!request_ok || !IsDoneRetcode(code))
     {
      LogEvent("ORDER_FAIL",index,StringFormat("action=ENTRY|retcode=%u|err=%d",code,GetLastError()));
      if(IsRetryable(code)) { g_next_retry=TimeCurrent()+MathMax(1,InpRetrySeconds); return false; }
      Halt(StringFormat("permanent_entry_failure retcode=%u",code),index); return false;
     }
   const ulong ticket=FindPositionForEvent(e.event_id);
   if(ticket==0 || !PositionSelectByTicket(ticket))
     {
      Halt("entry_fill_not_reconciled_by_comment",index); return false;
     }
   const double actual_volume=PositionGetDouble(POSITION_VOLUME);
   if(MathAbs(actual_volume-InpFixedLot)>1e-8)
     {
      Halt(StringFormat("entry_volume_mismatch expected=%.4f actual=%.4f",InpFixedLot,actual_volume),index); return false;
     }
   g_expected_open++;
   g_done[index]=true;
   UpdateRiskStats();
   const double balance_delta=AccountInfoDouble(ACCOUNT_BALANCE)-balance_before;
   LogEvent("ENTRY",index,StringFormat("lane=%s|dir=%s|reason=%s|ticket=%I64u|fill=%.5f|expected=%.5f|balance_delta=%.2f",
            e.lane,e.direction>0?"LONG":"SHORT",e.reason,ticket,PositionGetDouble(POSITION_PRICE_OPEN),e.expected_price,balance_delta));
   return Reconcile(index);
  }

bool ExecuteExit(const int index)
  {
   PolicyEvent e=g_events[index];
   if(!Reconcile(index)) return false;
   const ulong ticket=FindPositionForEvent(e.event_id);
   if(ticket==0)
     {
      const int entry_index=FindEntryIndex(e.event_id);
      if(entry_index>=0 && g_done[entry_index])
        {
         g_done[index]=true;
         LogEvent("EXIT_NO_POSITION",index,"reason=entry_expired_or_already_closed");
         return true;
        }
      Halt("exit_has_no_reconciled_entry",index); return false;
     }
   if(!PositionSelectByTicket(ticket)) { Halt("exit_ticket_select_failed",index); return false; }
   const double before=PositionGetDouble(POSITION_VOLUME);
   const double balance_before=AccountInfoDouble(ACCOUNT_BALANCE);
   ResetLastError();
   const bool request_ok=trade.PositionClose(ticket,(ulong)InpDeviationPoints);
   const uint code=(uint)trade.ResultRetcode();
   const bool remains=PositionSelectByTicket(ticket);
   if((!request_ok || !IsDoneRetcode(code)) || remains)
     {
      if(code==TRADE_RETCODE_POSITION_CLOSED && !remains)
        {
         g_expected_open--; g_done[index]=true;
         LogEvent("EXIT",index,"reason=broker_already_closed");
         return Reconcile(index);
        }
      LogEvent("ORDER_FAIL",index,StringFormat("action=EXIT|retcode=%u|err=%d|before_volume=%.4f",code,GetLastError(),before));
      if(IsRetryable(code) || code==TRADE_RETCODE_DONE_PARTIAL)
        { g_next_retry=TimeCurrent()+MathMax(1,InpRetrySeconds); return false; }
      Halt(StringFormat("permanent_exit_failure retcode=%u",code),index); return false;
     }
   g_expected_open--;
   g_done[index]=true;
   UpdateRiskStats();
   const double balance_delta=AccountInfoDouble(ACCOUNT_BALANCE)-balance_before;
   LogEvent("EXIT",index,StringFormat("lane=%s|reason=%s|ticket=%I64u|fill=%.5f|expected=%.5f|balance_delta=%.2f",
            e.lane,e.reason,ticket,trade.ResultPrice(),e.expected_price,balance_delta));
   return Reconcile(index);
  }

int OnInit()
  {
   if(_Symbol!=InpRequiredSymbol)
     {
      PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=symbol_mismatch|required=%s|actual=%s",InpRequiredSymbol,_Symbol);
      return INIT_FAILED;
     }
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {
      Print("V13Q75_EVENT|INIT_FAIL|reason=hedging_account_required");
      return INIT_FAILED;
     }
   if(!ValidateVolume(InpFixedLot))
     {
      PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=invalid_fixed_lot|lot=%.4f",InpFixedLot);
      return INIT_FAILED;
     }
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpDeviationPoints);
   trade.SetAsyncMode(false);
   if(CountOwnPositions()!=0)
     {
      Print("V13Q75_EVENT|INIT_FAIL|reason=preexisting_own_positions");
      return INIT_FAILED;
     }
   if(!LoadLedger())
     {
      PrintFormat("V13Q75_EVENT|INIT_FAIL|reason=ledger_validation|file=%s",InpLedgerFile);
      return INIT_FAILED;
     }
   PrintFormat("V13Q75_EVENT|INIT_OK|events=%d|file=%s|fixed_lot=%.4f|magic=%I64d",
               g_event_count,InpLedgerFile,InpFixedLot,InpMagicNumber);
   UpdateRiskStats();
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   UpdateRiskStats();
   if(g_halted || g_cursor>=g_event_count || TimeCurrent()<g_next_retry) return;
   while(g_cursor<g_event_count && !g_halted && g_events[g_cursor].action_time<=TimeCurrent())
     {
      if(g_done[g_cursor]) { g_cursor++; continue; }
      const bool complete=(g_events[g_cursor].action=="ENTRY")
         ? ExecuteEntry(g_cursor)
         : ExecuteExit(g_cursor);
      if(!complete) return;
      g_cursor++;
      g_next_retry=0;
     }
   if(g_cursor==g_event_count && !g_halted)
     {
      if(g_expected_open!=0) Halt("ledger_complete_with_open_positions",g_event_count-1);
      else
        {
         UpdateRiskStats();
         PrintFormat("V13Q75_EVENT|REPLAY_COMPLETE|events=%d|time=%s|balance=%.2f|equity=%.2f|max_equity_drawdown=%.2f|max_open=%d",
                     g_event_count,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),
                     AccountInfoDouble(ACCOUNT_BALANCE),AccountInfoDouble(ACCOUNT_EQUITY),
                     g_max_equity_drawdown,g_max_open_positions);
         ExpertRemove();
        }
     }
  }
//+------------------------------------------------------------------+
