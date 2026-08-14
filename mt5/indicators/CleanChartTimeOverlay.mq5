//+------------------------------------------------------------------+
//| CleanChartTimeOverlay.mq5                                        |
//| Removes leftover multi-timeframe/server-time text objects.        |
//+------------------------------------------------------------------+
#property strict
#property script_show_inputs

input bool InpDeleteOnlyTimeOverlay = true; // true: time overlay text only, false: all text/label objects

bool LooksLikeTimeOverlay(const string name, const string text)
{
   string merged = name + " " + text;
   StringToLower(merged);

   if(StringFind(merged, "market closed") >= 0)
      return true;
   if(StringFind(merged, "server time") >= 0)
      return true;
   if(StringFind(merged, "d1:") >= 0 || StringFind(merged, "h4:") >= 0 || StringFind(merged, "h1:") >= 0)
      return true;
   if(StringFind(merged, "m15:") >= 0 || StringFind(merged, "m5:") >= 0 || StringFind(merged, "m1:") >= 0)
      return true;
   if(LooksLikeClockLabel(text) || LooksLikeClockLabel(name))
      return true;

   return false;
}

bool IsDigitChar(const int code)
{
   return code >= '0' && code <= '9';
}

bool LooksLikeClockLabel(string value)
{
   StringTrimLeft(value);
   StringTrimRight(value);

   int length = StringLen(value);
   if(length < 4 || length > 8)
      return false;

   int colon = StringFind(value, ":");
   if(colon < 1 || colon > 2)
      return false;

   int minute_start = colon + 1;
   if(minute_start + 1 >= length)
      return false;

   for(int index = 0; index < colon; index++)
   {
      if(!IsDigitChar(StringGetCharacter(value, index)))
         return false;
   }

   if(!IsDigitChar(StringGetCharacter(value, minute_start)) || !IsDigitChar(StringGetCharacter(value, minute_start + 1)))
      return false;

   for(int index = minute_start + 2; index < length; index++)
   {
      int code = StringGetCharacter(value, index);
      if(code != ' ' && code != 'A' && code != 'P' && code != 'M' && code != 'a' && code != 'p' && code != 'm')
         return false;
   }

   return true;
}

void OnStart()
{
   int deleted = 0;
   for(int index = ObjectsTotal(0, 0, -1) - 1; index >= 0; index--)
   {
      string name = ObjectName(0, index, 0, -1);
      if(name == "")
         continue;

      ENUM_OBJECT type = (ENUM_OBJECT)ObjectGetInteger(0, name, OBJPROP_TYPE);
      if(type != OBJ_LABEL && type != OBJ_TEXT)
         continue;

      string text = ObjectGetString(0, name, OBJPROP_TEXT);
      if(InpDeleteOnlyTimeOverlay && !LooksLikeTimeOverlay(name, text))
         continue;

      if(ObjectDelete(0, name))
         deleted++;
   }

   ChartRedraw(0);
   PrintFormat("CleanChartTimeOverlay: deleted %d leftover object(s).", deleted);
}
