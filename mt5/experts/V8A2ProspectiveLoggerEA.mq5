//+------------------------------------------------------------------+
//| V8A2ProspectiveLoggerEA.mq5                                      |
//| Prospective all-M5 shadow logger for frozen V8-A + V8-A2         |
//+------------------------------------------------------------------+
#property strict
#property version "1.00"

input string InpA2IndicatorName = "V8MovementProbabilityA2ReliabilityIndicator";
input string InpControlIndicatorName = "V8MovementProbabilityIndicator";
input bool   InpRequireControlA = true;
input string InpFileName = "V8A2_prospective_m5.csv";

int g_a2=INVALID_HANDLE;
int g_a=INVALID_HANDLE;
datetime g_last_m5_open=0;

string StateName(const double r15,const double r30,const double r60)
{
   if(r15==EMPTY_VALUE || r30==EMPTY_VALUE || r60==EMPTY_VALUE) return "WARMUP";
   double mn=MathMin(r15,MathMin(r30,r60));
   double mx=MathMax(r15,MathMax(r30,r60));
   if(mn>=90.0) return "EXTREME";
   if(mn>=75.0) return "HIGH";
   if(mx<=25.0) return "QUIET";
   return "NORMAL";
}

bool ReadBufferOne(const int handle,const int buffer,const int shift,double &v)
{
   double a[1];
   if(CopyBuffer(handle,buffer,shift,1,a)!=1) return false;
   v=a[0];
   return true;
}

void WriteHeaderIfNeeded(const int fh)
{
   if(FileSize(fh)>0) return;
   FileWrite(fh,
      "decision_time","source_m5_time",
      "open","high","low","close","tick_volume","spread_points",
      "A_P15_pct","A_P30_pct","A_P60_pct",
      "A2_P15_pct","A2_P30_pct","A2_P60_pct",
      "A2_R15_pct","A2_R30_pct","A2_R60_pct","A2_consensus_rank_pct","A2_state");
}

void LogClosedM5()
{
   MqlRates r[1];
   if(CopyRates(_Symbol,PERIOD_M5,1,1,r)!=1) return;

   double a2[7];
   for(int b=0;b<7;b++)
      if(!ReadBufferOne(g_a2,b,1,a2[b])) return;

   double ca[3]={EMPTY_VALUE,EMPTY_VALUE,EMPTY_VALUE};
   if(g_a!=INVALID_HANDLE)
   {
      for(int b=0;b<3;b++)
         if(!ReadBufferOne(g_a,b,1,ca[b])) ca[b]=EMPTY_VALUE;
   }

   datetime source=r[0].time;
   datetime decision=source+PeriodSeconds(PERIOD_M5);
   string state=StateName(a2[3],a2[4],a2[5]);

   int fh=FileOpen(InpFileName,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_SHARE_READ,',');
   if(fh==INVALID_HANDLE)
   {
      Print("V8A2 logger: FileOpen failed err=",GetLastError());
      return;
   }
   WriteHeaderIfNeeded(fh);
   FileSeek(fh,0,SEEK_END);
   FileWrite(fh,
      TimeToString(decision,TIME_DATE|TIME_MINUTES),
      TimeToString(source,TIME_DATE|TIME_MINUTES),
      DoubleToString(r[0].open,_Digits),
      DoubleToString(r[0].high,_Digits),
      DoubleToString(r[0].low,_Digits),
      DoubleToString(r[0].close,_Digits),
      (long)r[0].tick_volume,
      (int)r[0].spread,
      (ca[0]==EMPTY_VALUE ? "" : DoubleToString(ca[0],8)),
      (ca[1]==EMPTY_VALUE ? "" : DoubleToString(ca[1],8)),
      (ca[2]==EMPTY_VALUE ? "" : DoubleToString(ca[2],8)),
      DoubleToString(a2[0],8),DoubleToString(a2[1],8),DoubleToString(a2[2],8),
      (a2[3]==EMPTY_VALUE ? "" : DoubleToString(a2[3],8)),
      (a2[4]==EMPTY_VALUE ? "" : DoubleToString(a2[4],8)),
      (a2[5]==EMPTY_VALUE ? "" : DoubleToString(a2[5],8)),
      (a2[6]==EMPTY_VALUE ? "" : DoubleToString(a2[6],8)),
      state);
   FileFlush(fh);
   FileClose(fh);
}

int OnInit()
{
   g_a2=iCustom(_Symbol,PERIOD_M5,InpA2IndicatorName);
   if(g_a2==INVALID_HANDLE)
   {
      Print("V8A2 logger: A2 handle failed err=",GetLastError());
      return INIT_FAILED;
   }
   g_a=iCustom(_Symbol,PERIOD_M5,InpControlIndicatorName);
   if(g_a==INVALID_HANDLE && InpRequireControlA)
   {
      Print("V8A2 logger: frozen control V8-A handle failed err=",GetLastError());
      IndicatorRelease(g_a2);
      return INIT_FAILED;
   }

   g_last_m5_open=iTime(_Symbol,PERIOD_M5,0);
   Print("V8A2 logger armed prospectively. No historical backfill. File=",InpFileName);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(g_a2!=INVALID_HANDLE) IndicatorRelease(g_a2);
   if(g_a!=INVALID_HANDLE) IndicatorRelease(g_a);
}

void OnTick()
{
   datetime cur=iTime(_Symbol,PERIOD_M5,0);
   if(cur<=0) return;
   if(g_last_m5_open==0) { g_last_m5_open=cur; return; }
   if(cur!=g_last_m5_open)
   {
      g_last_m5_open=cur;
      LogClosedM5();
   }
}
//+------------------------------------------------------------------+
