//+------------------------------------------------------------------+
//| D154OStageAExporter.mq5                                          |
//| Outcome-blind raw M1 + spread exporter for D-154O Stage A.       |
//|                                                                  |
//| This is a standalone research script. It has no strategy, order, |
//| Entry, SL, TP, sizing, SP or EM authority.                       |
//+------------------------------------------------------------------+
#property strict
#property script_show_inputs

input datetime InpFromServerTime = D'2026.08.17 00:00:00';
input datetime InpToServerTime   = D'2026.08.23 23:59:59';
input int      InpSyncTimeoutSeconds = 120;

#define UNIVERSE_ID "D154O_STAGE_A_UL32_20260824"
#define EXPORTER_BUILD "D154O_STAGE_A_EXPORTER_R1"
#define RATES_FILE "D154O_STAGE_A_M1.csv"
#define META_FILE  "D154O_STAGE_A_METADATA.csv"
#define STATUS_FILE "D154O_STAGE_A_STATUS.csv"

string g_symbols[] =
  {
   "CADCHF#","CADJPY#","CHFJPY#","EURCAD#","EURCHF#","EURGBP#","EURJPY#","EURUSD#",
   "GBPCAD#","GBPCHF#","GBPJPY#","GBPUSD#","USDCAD#","USDCHF#","USDJPY#",
   "ADAUSD#","BCHUSD#","BTCUSD#","DOGEUSD#","ETHUSD#","SOLUSD#","XLMUSD#","XRPUSD#",
   "GOLD#","SILVER#","XAUEUR#","XPDUSD#","XPTUSD#","GAUCNH#","GAUUSD#","XAUCNH#","XAUJPY#"
  };

string g_asset_classes[] =
  {
   "FOREX","FOREX","FOREX","FOREX","FOREX","FOREX","FOREX","FOREX",
   "FOREX","FOREX","FOREX","FOREX","FOREX","FOREX","FOREX",
   "CRYPTO","CRYPTO","CRYPTO","CRYPTO","CRYPTO","CRYPTO","CRYPTO","CRYPTO",
   "METALS","METALS","METALS","METALS","METALS","METALS","METALS","METALS","METALS"
  };

bool LoadM1Rates(const string symbol,MqlRates &rates[],int &last_error)
  {
   ArrayFree(rates);
   ArraySetAsSeries(rates,false);

   uint started=GetTickCount();
   const uint timeout_ms=(uint)MathMax(1,InpSyncTimeoutSeconds)*1000;
   int copied=-1;
   last_error=0;

   while((uint)(GetTickCount()-started)<timeout_ms)
     {
      ResetLastError();
      copied=CopyRates(symbol,PERIOD_M1,InpFromServerTime,InpToServerTime,rates);
      last_error=GetLastError();
      if(copied>0)
         return true;
      Sleep(500);
     }

   return false;
  }

void WriteStatus(const string state,const int success_count,const int expected_count)
  {
   int h=FileOpen(STATUS_FILE,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(h==INVALID_HANDLE)
     {
      PrintFormat("D154O status FileOpen failed error=%d",GetLastError());
      return;
     }
   FileWrite(h,"universe_id","exporter_build","state","from_server","to_server","expected_symbols","successful_symbols","export_finished_terminal_time");
   FileWrite(h,UNIVERSE_ID,EXPORTER_BUILD,state,
             TimeToString(InpFromServerTime,TIME_DATE|TIME_SECONDS),
             TimeToString(InpToServerTime,TIME_DATE|TIME_SECONDS),
             expected_count,success_count,
             TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS));
   FileClose(h);
  }

void OnStart()
  {
   const int expected=ArraySize(g_symbols);
   if(expected!=32 || ArraySize(g_asset_classes)!=expected)
     {
      Print("D154O_STAGE_A EXPORT ABORT: internal universe array mismatch");
      WriteStatus("INTERNAL_UNIVERSE_MISMATCH",0,expected);
      return;
     }

   if(InpToServerTime<InpFromServerTime)
     {
      Print("D154O_STAGE_A EXPORT ABORT: invalid time window");
      WriteStatus("INVALID_TIME_WINDOW",0,expected);
      return;
     }

   int rates_h=FileOpen(RATES_FILE,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(rates_h==INVALID_HANDLE)
     {
      PrintFormat("D154O_STAGE_A EXPORT ABORT: cannot open rates file error=%d",GetLastError());
      WriteStatus("RATES_FILE_OPEN_FAILED",0,expected);
      return;
     }

   int meta_h=FileOpen(META_FILE,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(meta_h==INVALID_HANDLE)
     {
      PrintFormat("D154O_STAGE_A EXPORT ABORT: cannot open metadata file error=%d",GetLastError());
      FileClose(rates_h);
      WriteStatus("META_FILE_OPEN_FAILED",0,expected);
      return;
     }

   FileWrite(rates_h,
             "universe_id","symbol","asset_class","time_server","time_epoch",
             "open","high","low","close","tick_volume","spread_points","real_volume",
             "point","digits");

   FileWrite(meta_h,
             "universe_id","symbol","asset_class","reference","select_ok","copy_ok","rows",
             "first_time_server","last_time_server","point","digits","symbol_path","trade_mode",
             "currency_base","currency_profit","last_error");

   int success_count=0;

   for(int s=0;s<expected;s++)
     {
      string symbol=g_symbols[s];
      string asset_class=g_asset_classes[s];
      bool reference=(symbol=="GOLD#");

      ResetLastError();
      bool select_ok=SymbolSelect(symbol,true);
      int select_error=GetLastError();

      double point=0.0;
      long digits=0;
      long trade_mode=0;
      string path="";
      string currency_base="";
      string currency_profit="";

      if(select_ok)
        {
         SymbolInfoDouble(symbol,SYMBOL_POINT,point);
         SymbolInfoInteger(symbol,SYMBOL_DIGITS,digits);
         SymbolInfoInteger(symbol,SYMBOL_TRADE_MODE,trade_mode);
         path=SymbolInfoString(symbol,SYMBOL_PATH);
         currency_base=SymbolInfoString(symbol,SYMBOL_CURRENCY_BASE);
         currency_profit=SymbolInfoString(symbol,SYMBOL_CURRENCY_PROFIT);
        }

      MqlRates rates[];
      int copy_error=select_error;
      bool copy_ok=false;
      int rows=0;

      if(select_ok)
        {
         copy_ok=LoadM1Rates(symbol,rates,copy_error);
         if(copy_ok)
            rows=ArraySize(rates);
        }

      string first_time="";
      string last_time="";
      if(copy_ok && rows>0)
        {
         first_time=TimeToString(rates[0].time,TIME_DATE|TIME_MINUTES);
         last_time=TimeToString(rates[rows-1].time,TIME_DATE|TIME_MINUTES);

         for(int i=0;i<rows;i++)
           {
            MqlRates r=rates[i];
            FileWrite(rates_h,
                      UNIVERSE_ID,symbol,asset_class,
                      TimeToString(r.time,TIME_DATE|TIME_MINUTES),(long)r.time,
                      DoubleToString(r.open,(int)digits),
                      DoubleToString(r.high,(int)digits),
                      DoubleToString(r.low,(int)digits),
                      DoubleToString(r.close,(int)digits),
                      (long)r.tick_volume,(int)r.spread,(long)r.real_volume,
                      DoubleToString(point,12),(int)digits);
           }
         success_count++;
        }

      FileWrite(meta_h,
                UNIVERSE_ID,symbol,asset_class,(reference?1:0),(select_ok?1:0),(copy_ok?1:0),rows,
                first_time,last_time,DoubleToString(point,12),(int)digits,path,(int)trade_mode,
                currency_base,currency_profit,copy_error);

      FileFlush(rates_h);
      FileFlush(meta_h);

      PrintFormat("D154O_STAGE_A [%d/%d] %s select=%s copy=%s rows=%d path=%s error=%d",
                  s+1,expected,symbol,(select_ok?"OK":"FAIL"),(copy_ok?"OK":"FAIL"),rows,path,copy_error);

      ArrayFree(rates);
     }

   FileClose(rates_h);
   FileClose(meta_h);

   string final_state=(success_count==expected ? "EXPORT_COMPLETE" : "EXPORT_INCOMPLETE");
   WriteStatus(final_state,success_count,expected);

   if(success_count==expected)
      PrintFormat("D154O_STAGE_A EXPORT COMPLETE: %d/%d symbols. Common Files: %s, %s, %s",
                  success_count,expected,RATES_FILE,META_FILE,STATUS_FILE);
   else
      PrintFormat("D154O_STAGE_A EXPORT INCOMPLETE: %d/%d symbols. Do not screen partial data.",
                  success_count,expected);
  }
