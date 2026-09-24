#property script_show_inputs
#property strict

input datetime InpFromServerTime = D'2022.01.01 00:00:00';
input datetime InpToServerTime   = D'2026.09.19 00:00:00';
input string   InpOutputFile     = "V12_PHASE1E_MQL5_CALENDAR_SNAPSHOT.csv";
input int      InpRetries        = 8;
input int      InpConnectionWaitSeconds = 60;
input int      InpWarmupPauseMilliseconds = 3000;

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

bool CalendarArraysMatch(const MqlCalendarValue &left[],const int left_count,
                         const MqlCalendarValue &right[],const int right_count)
  {
   if(left_count!=right_count)
      return false;
   for(int i=0;i<left_count;i++)
     {
      if(left[i].id!=right[i].id ||
         left[i].event_id!=right[i].event_id ||
         left[i].time!=right[i].time ||
         left[i].period!=right[i].period ||
         left[i].revision!=right[i].revision)
         return false;
     }
   return true;
  }

bool WaitForCalendarClock()
  {
   const datetime deadline=TimeLocal()+InpConnectionWaitSeconds;
   while(!IsStopped() && TimeLocal()<=deadline)
     {
      if((bool)TerminalInfoInteger(TERMINAL_CONNECTED) && TimeTradeServer()>0)
        {
         PrintFormat("V12 calendar export: terminal connected server_time=%s trade_server=%s",
                     TimeToString(TimeTradeServer(),TIME_DATE|TIME_SECONDS),
                     AccountInfoString(ACCOUNT_SERVER));
         Sleep(InpWarmupPauseMilliseconds);
         break;
        }
      Sleep(1000);
     }

   if(!(bool)TerminalInfoInteger(TERMINAL_CONNECTED) || TimeTradeServer()<=0)
     {
      PrintFormat("V12 calendar export: terminal/calendar clock unavailable connected=%d server_time=%s",
                  (int)TerminalInfoInteger(TERMINAL_CONNECTED),
                  TimeToString(TimeTradeServer(),TIME_DATE|TIME_SECONDS));
      return false;
     }

   // The first calendar call after terminal startup can be returned in a
   // different time namespace from later calls.  Require two complete,
   // consecutive reads of the same sentinel range to agree before exporting.
   const datetime probe_from=D'2022.01.01 00:00:00';
   const datetime probe_to=D'2022.02.05 00:00:00';
   for(int attempt=0;attempt<InpRetries && !IsStopped();attempt++)
     {
      MqlCalendarValue first[];
      MqlCalendarValue second[];
      ResetLastError();
      const int first_count=CalendarValueHistory(first,probe_from,probe_to,NULL,NULL);
      const int first_error=GetLastError();
      Sleep(1000);
      ResetLastError();
      const int second_count=CalendarValueHistory(second,probe_from,probe_to,NULL,NULL);
      const int second_error=GetLastError();
      if(first_count>=0 && second_count>=0 &&
         CalendarArraysMatch(first,first_count,second,second_count))
        {
         PrintFormat("V12 calendar export: stable calendar clock probe rows=%d attempt=%d",
                     first_count,attempt+1);
         return true;
        }
      PrintFormat("V12 calendar export: unstable calendar clock probe attempt=%d first_rows=%d first_error=%d second_rows=%d second_error=%d",
                  attempt+1,first_count,first_error,second_count,second_error);
      Sleep(1000*(attempt+1));
     }
   return false;
  }

void OnStart()
  {
   if(InpFromServerTime>=InpToServerTime)
     {
      Print("V12 calendar export: invalid date range");
      return;
     }
   if(!WaitForCalendarClock())
     {
      Print("V12 calendar export: calendar clock did not stabilize");
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

   MqlCalendarValue values[];
   int count=-1;
   for(int attempt=0;attempt<InpRetries && !IsStopped();attempt++)
     {
      ResetLastError();
      count=CalendarValueHistory(values,InpFromServerTime,InpToServerTime,NULL,NULL);
      if(count>=0)
         break;
      PrintFormat("V12 calendar export: full-range retry from=%s to=%s attempt=%d error=%d",
                  TimeToString(InpFromServerTime,TIME_DATE|TIME_MINUTES),
                  TimeToString(InpToServerTime,TIME_DATE|TIME_MINUTES),
                  attempt+1,GetLastError());
      Sleep(1000*(attempt+1));
     }
   if(count<0)
     {
      PrintFormat("V12 calendar export: full-range query failed error=%d",GetLastError());
      FileClose(handle);
      return;
     }

   long total_rows=0;
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
   FileClose(handle);
   PrintFormat("V12 calendar export: COMPLETE file=%s rows=%I64d server=%s build=%d trade_server=%s",
               InpOutputFile,total_rows,AccountInfoString(ACCOUNT_SERVER),
               (int)TerminalInfoInteger(TERMINAL_BUILD),
               TimeToString(TimeTradeServer(),TIME_DATE|TIME_SECONDS));
  }
