#property script_show_inputs
#property strict

input datetime InpFromServerTime = D'2022.01.01 00:00:00';
input datetime InpToServerTime   = D'2026.09.19 00:00:00';
input string   InpOutputFile     = "V12_PHASE1D_MQL5_CALENDAR_SNAPSHOT.csv";
input int      InpChunkDays      = 31;
input int      InpRetries        = 8;

string CsvEscape(const string value)
  {
   string escaped=value;
   StringReplace(escaped,"\"","\"\"");
   return "\""+escaped+"\"";
  }

string BoolText(const bool value)
  {
   return value ? "1" : "0";
  }

string DoubleText(const double value,const bool present,const int digits)
  {
   if(!present)
      return "";
   const int safe_digits=(int)MathMin(12,MathMax(0,digits));
   return DoubleToString(value,safe_digits);
  }

bool WriteHeader(const int handle)
  {
   return FileWrite(handle,
                    "value_id","event_id","server_time","period_time","revision",
                    "country_id","country_code","country_name","currency",
                    "event_type","sector","frequency","time_mode","importance",
                    "unit","multiplier","digits","event_code","event_name","source_url",
                    "has_actual","actual","has_forecast","forecast","has_previous","previous",
                    "has_revised_previous","revised_previous","impact_type")>0;
  }

void OnStart()
  {
   if(InpFromServerTime>=InpToServerTime || InpChunkDays<1)
     {
      Print("V12 calendar export: invalid date range or chunk size");
      return;
     }

   const int handle=FileOpen(InpOutputFile,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(handle==INVALID_HANDLE)
     {
      PrintFormat("V12 calendar export: FileOpen failed error=%d",GetLastError());
      return;
     }
   if(!WriteHeader(handle))
     {
      PrintFormat("V12 calendar export: header write failed error=%d",GetLastError());
      FileClose(handle);
      return;
     }

   long total_rows=0;
   datetime chunk_from=InpFromServerTime;
   while(chunk_from<InpToServerTime && !IsStopped())
     {
      datetime chunk_to=chunk_from+(datetime)(InpChunkDays*86400);
      if(chunk_to>InpToServerTime)
         chunk_to=InpToServerTime;

      MqlCalendarValue values[];
      int count=-1;
      for(int attempt=0; attempt<InpRetries && !IsStopped(); attempt++)
        {
         ResetLastError();
         count=CalendarValueHistory(values,chunk_from,chunk_to,NULL,NULL);
         if(count>=0)
            break;
         const int error=GetLastError();
         PrintFormat("V12 calendar export: retry from=%s to=%s attempt=%d error=%d",
                     TimeToString(chunk_from,TIME_DATE|TIME_MINUTES),
                     TimeToString(chunk_to,TIME_DATE|TIME_MINUTES),attempt+1,error);
         Sleep(1000*(attempt+1));
        }
      if(count<0)
        {
         PrintFormat("V12 calendar export: aborting failed chunk from=%s to=%s error=%d",
                     TimeToString(chunk_from,TIME_DATE|TIME_MINUTES),
                     TimeToString(chunk_to,TIME_DATE|TIME_MINUTES),GetLastError());
         FileClose(handle);
         return;
        }

      for(int i=0;i<count;i++)
        {
         MqlCalendarEvent event;
         MqlCalendarCountry country;
         ResetLastError();
         if(!CalendarEventById(values[i].event_id,event))
           {
            PrintFormat("V12 calendar export: CalendarEventById failed event=%I64u error=%d",
                        values[i].event_id,GetLastError());
            continue;
           }
         ResetLastError();
         if(!CalendarCountryById(event.country_id,country))
           {
            PrintFormat("V12 calendar export: CalendarCountryById failed country=%I64u error=%d",
                        event.country_id,GetLastError());
            continue;
           }

         FileWrite(handle,
                   (string)values[i].id,
                   (string)values[i].event_id,
                   TimeToString(values[i].time,TIME_DATE|TIME_SECONDS),
                   TimeToString(values[i].period,TIME_DATE|TIME_SECONDS),
                   IntegerToString(values[i].revision),
                   (string)event.country_id,
                   CsvEscape(country.code),CsvEscape(country.name),CsvEscape(country.currency),
                   EnumToString(event.type),EnumToString(event.sector),EnumToString(event.frequency),
                   EnumToString(event.time_mode),EnumToString(event.importance),EnumToString(event.unit),
                   EnumToString(event.multiplier),IntegerToString((int)event.digits),
                   CsvEscape(event.event_code),CsvEscape(event.name),CsvEscape(event.source_url),
                   BoolText(values[i].HasActualValue()),
                   DoubleText(values[i].GetActualValue(),values[i].HasActualValue(),event.digits),
                   BoolText(values[i].HasForecastValue()),
                   DoubleText(values[i].GetForecastValue(),values[i].HasForecastValue(),event.digits),
                   BoolText(values[i].HasPreviousValue()),
                   DoubleText(values[i].GetPreviousValue(),values[i].HasPreviousValue(),event.digits),
                   BoolText(values[i].HasRevisedValue()),
                   DoubleText(values[i].GetRevisedValue(),values[i].HasRevisedValue(),event.digits),
                   EnumToString(values[i].impact_type));
         total_rows++;
        }
      FileFlush(handle);
      PrintFormat("V12 calendar export: completed from=%s to=%s rows=%d total=%I64d",
                  TimeToString(chunk_from,TIME_DATE|TIME_MINUTES),
                  TimeToString(chunk_to,TIME_DATE|TIME_MINUTES),count,total_rows);
      chunk_from=chunk_to;
     }

   FileClose(handle);
   PrintFormat("V12 calendar export: COMPLETE file=%s rows=%I64d server=%s build=%d trade_server=%s",
               InpOutputFile,total_rows,AccountInfoString(ACCOUNT_SERVER),
               (int)TerminalInfoInteger(TERMINAL_BUILD),
               TimeToString(TimeTradeServer(),TIME_DATE|TIME_SECONDS));
  }
