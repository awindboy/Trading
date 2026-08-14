//+------------------------------------------------------------------+
//| TradeJournalExporterEA.mq5                                       |
//| Exports MT5 position lifecycle events for the local web journal. |
//+------------------------------------------------------------------+
#property strict
#property version   "1.10"
#property description "Writes position open/update/close events to MQL5/Files/trading_journal/events.jsonl and events.csv"

#define EA_VERSION "1.10"
#define EA_FEATURES "jsonl,csv,screenshot,heartbeat,sl_tp_updates"

input string          InpExportDir = "trading_journal";
input int             InpScanSeconds = 1;
input bool            InpTakeScreenshots = true;
input bool            InpAutoScreenshotTimeframe = true;
input ENUM_TIMEFRAMES InpScreenshotTimeframe = PERIOD_M5;
input string          InpScreenshotTemplate = ""; // 罹≪퀜??李⑦듃 ?쒗뵆由?.tpl, 鍮꾩슦硫?誘몄쟻??
input int             InpScreenshotWidth = 1600;
input int             InpScreenshotHeight = 900;
input int             InpChartScale = 2;
input bool            InpCleanScreenshotChart = true;
input bool            InpDrawTradeGuides = true;
input int             InpPositionBoxTransparency = 80;
input bool            InpScreenshotOpenEvents = false;
input bool            InpScreenshotUpdateEvents = false;
input bool            InpScreenshotCloseEvents = true;
input int             InpShotM1MaxMinutes = 90; // M1 罹≪퀜 理쒕? 蹂댁쑀?쒓컙(遺?
input int             InpShotM5MaxMinutes = 480; // M5 罹≪퀜 理쒕? 蹂댁쑀?쒓컙(遺?
input int             InpShotM15MaxMinutes = 1440; // M15 罹≪퀜 理쒕? 蹂댁쑀?쒓컙(遺?
input int             InpShotH1MaxMinutes = 7200; // H1 罹≪퀜 理쒕? 蹂댁쑀?쒓컙(遺?
input int             InpHeartbeatSeconds = 30;

struct TrackedPosition
{
   ulong    ticket;
   long     identifier;
   string   symbol;
   string   direction;
   double   volume;
   double   entry_price;
   double   stop_loss;
   double   take_profit;
   double   profit;
   double   swap_value;
   datetime open_time;
   string   comment;
   bool     seen;
};

TrackedPosition g_positions[];
int g_sequence = 0;
long g_screenshot_chart_id = 0;
bool g_is_scanning = false;
string g_instance_lock_name = "";
bool g_has_instance_lock = false;

string JsonEscape(const string value)
{
   string result = value;
   StringReplace(result, "\\", "\\\\");
   StringReplace(result, "\"", "\\\"");
   StringReplace(result, "\r", "\\r");
   StringReplace(result, "\n", "\\n");
   StringReplace(result, "\t", "\\t");
   return result;
}

string JsonString(const string key, const string value)
{
   return "\"" + key + "\":\"" + JsonEscape(value) + "\"";
}

string CsvEscape(const string value)
{
   string result = value;
   StringReplace(result, "\"", "\"\"");
   return "\"" + result + "\"";
}

string CsvNumber(const double value, const int digits = 8)
{
   return DoubleToString(value, digits);
}

string JsonNumber(const string key, const double value, const int digits = 8)
{
   return "\"" + key + "\":" + DoubleToString(value, digits);
}

string JsonLong(const string key, const long value)
{
   return "\"" + key + "\":" + IntegerToString(value);
}

string TimeText(const datetime value)
{
   if(value <= 0)
      return "";
   return TimeToString(value, TIME_DATE | TIME_SECONDS);
}

string DirectionFromType(const long position_type)
{
   return position_type == POSITION_TYPE_BUY ? "long" : "short";
}

int FindTrackedByIdentifier(const long identifier)
{
   for(int index = 0; index < ArraySize(g_positions); index++)
   {
      if(g_positions[index].identifier == identifier)
         return index;
   }
   return -1;
}

bool LoadPositionByIndex(const int index, TrackedPosition &position)
{
   ulong ticket = PositionGetTicket(index);
   if(ticket == 0)
      return false;

   long position_type = PositionGetInteger(POSITION_TYPE);
   position.ticket = ticket;
   position.identifier = PositionGetInteger(POSITION_IDENTIFIER);
   position.symbol = PositionGetString(POSITION_SYMBOL);
   position.direction = DirectionFromType(position_type);
   position.volume = PositionGetDouble(POSITION_VOLUME);
   position.entry_price = PositionGetDouble(POSITION_PRICE_OPEN);
   position.stop_loss = PositionGetDouble(POSITION_SL);
   position.take_profit = PositionGetDouble(POSITION_TP);
   position.profit = PositionGetDouble(POSITION_PROFIT);
   position.swap_value = PositionGetDouble(POSITION_SWAP);
   position.open_time = (datetime)PositionGetInteger(POSITION_TIME);
   position.comment = PositionGetString(POSITION_COMMENT);
   position.seen = true;
   return true;
}

bool SamePrice(const double left, const double right)
{
   return MathAbs(left - right) < 0.00000001;
}

bool SignificantUpdate(const TrackedPosition &previous, const TrackedPosition &current)
{
   if(!SamePrice(previous.stop_loss, current.stop_loss))
      return true;
   if(!SamePrice(previous.take_profit, current.take_profit))
      return true;
   if(!SamePrice(previous.volume, current.volume))
      return true;
   return false;
}

void EnsureFolders()
{
   FolderCreate(InpExportDir);
   FolderCreate(InpExportDir + "\\screenshots");
}

string ScreenshotFileName(const string event_type, const TrackedPosition &position)
{
   string stamp = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
   StringReplace(stamp, ".", "");
   StringReplace(stamp, ":", "");
   StringReplace(stamp, " ", "_");
   return "screenshots\\" + position.symbol + "_" + IntegerToString(position.identifier) + "_" + event_type + "_" + stamp + ".png";
}

ENUM_TIMEFRAMES ScreenshotPeriod(const string event_type, const TrackedPosition &position, const datetime reference_time = 0)
{
   if(!InpAutoScreenshotTimeframe)
      return InpScreenshotTimeframe;

   if(event_type != "close" || position.open_time <= 0)
      return PERIOD_M1;

   datetime end_time = reference_time > 0 ? reference_time : TimeCurrent();
   int minutes = MathMax(0, (int)((end_time - position.open_time) / 60));
   if(minutes <= MathMax(1, InpShotM1MaxMinutes))
      return PERIOD_M1;
   if(minutes <= MathMax(InpShotM1MaxMinutes + 1, InpShotM5MaxMinutes))
      return PERIOD_M5;
   if(minutes <= MathMax(InpShotM5MaxMinutes + 1, InpShotM15MaxMinutes))
      return PERIOD_M15;
   if(minutes <= MathMax(InpShotM15MaxMinutes + 1, InpShotH1MaxMinutes))
      return PERIOD_H1;
   return PERIOD_H4;
}

int PeriodSecondsSafe(const ENUM_TIMEFRAMES period)
{
   int seconds = PeriodSeconds(period);
   if(seconds <= 0)
      return 60;
   return seconds;
}

int ScreenshotBarsBack(const string event_type, const TrackedPosition &position, const ENUM_TIMEFRAMES period, const datetime reference_time = 0)
{
   if(event_type != "close" || position.open_time <= 0)
      return 0;

   datetime end_time = reference_time > 0 ? reference_time : TimeCurrent();
   int duration = (int)(end_time - position.open_time);
   int bars = duration / PeriodSecondsSafe(period);
   return (int)MathMax(0, MathMin(500, bars + 20));
}

void ApplyScreenshotTemplate(const long chart_id)
{
   if(chart_id == ChartID() || StringLen(InpScreenshotTemplate) <= 0)
      return;

   ResetLastError();
   if(!ChartApplyTemplate(chart_id, InpScreenshotTemplate))
      Print("TradeJournalExporterEA: ChartApplyTemplate failed: ", GetLastError(), " template=", InpScreenshotTemplate);
   Sleep(800);
}

void DeleteScreenshotObjects(const long chart_id)
{
   int total = ObjectsTotal(chart_id, 0, -1);
   for(int index = total - 1; index >= 0; index--)
   {
      string name = ObjectName(chart_id, index, 0, -1);
      if(StringFind(name, "TJ_") == 0)
         ObjectDelete(chart_id, name);
   }
}

void ClearScreenshotIndicators(const long chart_id)
{
   if(!InpCleanScreenshotChart)
      return;

   long windows = ChartGetInteger(chart_id, CHART_WINDOWS_TOTAL);
   for(int window = (int)windows - 1; window >= 0; window--)
   {
      for(int index = ChartIndicatorsTotal(chart_id, window) - 1; index >= 0; index--)
      {
         string indicator_name = ChartIndicatorName(chart_id, window, index);
         if(StringLen(indicator_name) > 0)
            ChartIndicatorDelete(chart_id, window, indicator_name);
      }
   }
}

void SetTradeLine(const long chart_id, const string suffix, const double price, const color line_color, const ENUM_LINE_STYLE style)
{
   if(price <= 0.0)
      return;

   string name = "TJ_" + suffix;
   ObjectDelete(chart_id, name);
   ObjectCreate(chart_id, name, OBJ_HLINE, 0, 0, price);
   ObjectSetInteger(chart_id, name, OBJPROP_COLOR, line_color);
   ObjectSetInteger(chart_id, name, OBJPROP_STYLE, style);
   ObjectSetInteger(chart_id, name, OBJPROP_WIDTH, 2);
   ObjectSetInteger(chart_id, name, OBJPROP_BACK, false);
   ObjectSetString(chart_id, name, OBJPROP_TEXT, suffix);
}

void SetTradeRectangle(const long chart_id, const string suffix, const datetime left_time, const datetime right_time, const double price_a, const double price_b, const color fill_color)
{
   if(left_time <= 0 || right_time <= left_time || price_a <= 0.0 || price_b <= 0.0)
      return;

   int transparency = (int)MathMax(0, MathMin(100, InpPositionBoxTransparency));
   uchar alpha = (uchar)MathMax(0, MathMin(255, 255 - (int)MathRound(255.0 * transparency / 100.0)));
   color box_color = (color)ColorToARGB(fill_color, alpha);
   string name = "TJ_" + suffix + "_BOX";
   ObjectDelete(chart_id, name);
   ObjectCreate(chart_id, name, OBJ_RECTANGLE, 0, left_time, price_a, right_time, price_b);
   ObjectSetInteger(chart_id, name, OBJPROP_COLOR, box_color);
   ObjectSetInteger(chart_id, name, OBJPROP_FILL, true);
   ObjectSetInteger(chart_id, name, OBJPROP_BACK, true);
   ObjectSetInteger(chart_id, name, OBJPROP_WIDTH, 1);
}

void SetTradeText(const long chart_id, const string suffix, const datetime time_value, const double price, const string text, const color text_color)
{
   if(time_value <= 0 || price <= 0.0)
      return;

   string name = "TJ_" + suffix + "_TEXT";
   ObjectDelete(chart_id, name);
   ObjectCreate(chart_id, name, OBJ_TEXT, 0, time_value, price);
   ObjectSetString(chart_id, name, OBJPROP_TEXT, text);
   ObjectSetInteger(chart_id, name, OBJPROP_COLOR, text_color);
   ObjectSetInteger(chart_id, name, OBJPROP_FONTSIZE, 10);
   ObjectSetInteger(chart_id, name, OBJPROP_ANCHOR, ANCHOR_CENTER);
   ObjectSetInteger(chart_id, name, OBJPROP_BACK, false);
}

void DrawTradeGuides(const long chart_id, const string event_type, const TrackedPosition &position, const double close_price = 0.0, const datetime close_time = 0)
{
   DeleteScreenshotObjects(chart_id);
   if(!InpDrawTradeGuides || event_type != "close")
      return;

   datetime exit_time = close_time > 0 ? close_time : TimeCurrent();
   int min_span = MathMax(PeriodSecondsSafe((ENUM_TIMEFRAMES)ChartPeriod(chart_id)) * 16, 60);
   datetime right_time = MathMax(exit_time, position.open_time + min_span);
   datetime label_time = position.open_time + (right_time - position.open_time) / 2;

   double entry = position.entry_price;
   double sl = position.stop_loss;
   double tp = position.take_profit;
   double risk = MathAbs(entry - sl);
   double reward = MathAbs(tp - entry);
   double rr = risk > 0.0 && reward > 0.0 ? reward / risk : 0.0;

   SetTradeRectangle(chart_id, "RISK", position.open_time, right_time, entry, sl, clrFireBrick);
   SetTradeRectangle(chart_id, "REWARD", position.open_time, right_time, entry, tp, clrSeaGreen);

   SetTradeText(chart_id, "SL_LABEL", label_time, sl, "SL " + DoubleToString(sl, _Digits) + " | Risk " + DoubleToString(risk, _Digits), clrWhite);
   SetTradeText(chart_id, "TP_LABEL", label_time, tp, "TP " + DoubleToString(tp, _Digits) + " | RR " + DoubleToString(rr, 2), clrWhite);
}

bool ChartStillOpen(const long chart_id)
{
   for(long current = ChartFirst(); current >= 0; current = ChartNext(current))
   {
      if(current == chart_id)
         return true;
   }
   return false;
}

long ScreenshotChart(const string symbol, const ENUM_TIMEFRAMES period)
{
   ResetLastError();
   g_screenshot_chart_id = ChartOpen(symbol, period);
   if(g_screenshot_chart_id == 0)
   {
      Print("TradeJournalExporterEA: ChartOpen failed: ", GetLastError(), " symbol=", symbol);
      return ChartID();
   }

   Sleep(500);
   return g_screenshot_chart_id;
}

void CloseScreenshotChart()
{
   if(g_screenshot_chart_id > 0 && g_screenshot_chart_id != ChartID() && ChartStillOpen(g_screenshot_chart_id))
      ChartClose(g_screenshot_chart_id);
   g_screenshot_chart_id = 0;
}

bool AcquireInstanceLock()
{
   g_instance_lock_name = "TradeJournalExporterEA:" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
   if(GlobalVariableCheck(g_instance_lock_name))
   {
      long owner_chart = (long)GlobalVariableGet(g_instance_lock_name);
      if(owner_chart > 0 && owner_chart != ChartID() && ChartStillOpen(owner_chart))
      {
         Print("TradeJournalExporterEA: another instance is already running on chart ", owner_chart, ". Remove duplicate EA instances.");
         return false;
      }
   }

   GlobalVariableSet(g_instance_lock_name, (double)ChartID());
   g_has_instance_lock = true;
   return true;
}

void ReleaseInstanceLock()
{
   if(!g_has_instance_lock || StringLen(g_instance_lock_name) <= 0)
      return;

   if(GlobalVariableCheck(g_instance_lock_name) && (long)GlobalVariableGet(g_instance_lock_name) == ChartID())
      GlobalVariableDel(g_instance_lock_name);
   g_has_instance_lock = false;
}

string CaptureScreenshot(const string event_type, const TrackedPosition &position, const double close_price = 0.0, const datetime close_time = 0)
{
   if(!InpTakeScreenshots)
      return "";
   if(event_type == "open" && !InpScreenshotOpenEvents)
      return "";
   if(event_type == "update" && !InpScreenshotUpdateEvents)
      return "";
   if(event_type == "close" && !InpScreenshotCloseEvents)
      return "";

   string relative_path = ScreenshotFileName(event_type, position);
   ENUM_TIMEFRAMES screenshot_period = ScreenshotPeriod(event_type, position, close_time);
   long chart_id = ScreenshotChart(position.symbol, screenshot_period);

   ApplyScreenshotTemplate(chart_id);
   ClearScreenshotIndicators(chart_id);
   DrawTradeGuides(chart_id, event_type, position, close_price, close_time);
   ChartSetInteger(chart_id, CHART_AUTOSCROLL, false);
   ChartSetInteger(chart_id, CHART_SHIFT, true);
   ChartSetInteger(chart_id, CHART_SCALE, InpChartScale);
   ChartNavigate(chart_id, CHART_END, 0);
   int bars_back = ScreenshotBarsBack(event_type, position, screenshot_period, close_time);
   if(bars_back > 0)
      ChartNavigate(chart_id, CHART_CURRENT_POS, -bars_back);
   ChartRedraw(chart_id);
   Sleep(500);

   bool ok = ChartScreenShot(chart_id, InpExportDir + "\\" + relative_path, InpScreenshotWidth, InpScreenshotHeight, ALIGN_RIGHT);
   if(chart_id != ChartID())
      ChartClose(chart_id);
   g_screenshot_chart_id = 0;

   if(!ok)
   {
      Print("TradeJournalExporterEA: ChartScreenShot failed: ", GetLastError(), " path=", relative_path);
      return "";
   }
   return relative_path;
}

void AppendJsonLine(const string line)
{
   EnsureFolders();
   string file_name = InpExportDir + "\\events.jsonl";
   int handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI);
   if(handle == INVALID_HANDLE)
   {
      Print("TradeJournalExporterEA: FileOpen failed: ", GetLastError());
      return;
   }

   FileSeek(handle, 0, SEEK_END);
   FileWriteString(handle, line + "\n");
   FileFlush(handle);
   FileClose(handle);
}

string CsvHeader()
{
   return "schema,event,eventId,time,accountLogin,server,chartSymbol,positionsTotal,ticket,positionId,symbol,direction,volume,entryPrice,stopLoss,takeProfit,floatingProfit,swap,openTime,comment,screenshot,closeDeal,closeTime,closePrice,closeVolume,profit,commission,closeSwap,fee";
}

void AppendCsvLine(const string line)
{
   EnsureFolders();
   string file_name = InpExportDir + "\\events.csv";
   int handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI);
   if(handle == INVALID_HANDLE)
   {
      Print("TradeJournalExporterEA: CSV FileOpen failed: ", GetLastError());
      return;
   }

   if(FileSize(handle) == 0)
      FileWriteString(handle, CsvHeader() + "\n");

   FileSeek(handle, 0, SEEK_END);
   FileWriteString(handle, line + "\n");
   FileFlush(handle);
   FileClose(handle);
}

string StatusCsvLine(const string event_type, const string event_id)
{
   string line = "";
   line += CsvEscape("trade-journal-ea-v1") + ",";
   line += CsvEscape(event_type) + ",";
   line += CsvEscape(event_id) + ",";
   line += CsvEscape(TimeText(TimeCurrent())) + ",";
   line += IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + ",";
   line += CsvEscape(AccountInfoString(ACCOUNT_SERVER)) + ",";
   line += CsvEscape(Symbol()) + ",";
   line += IntegerToString(PositionsTotal()) + ",";
   line += "0,0,,,0,0,0,0,0,0,,,,0,,0,0,0,0,0,0";
   return line;
}

string TradeCsvLine(const string event_type,
                    const string event_id,
                    const TrackedPosition &position,
                    const string screenshot,
                    const ulong close_deal = 0,
                    const datetime close_time = 0,
                    const double close_price = 0.0,
                    const double close_volume = 0.0,
                    const double profit = 0.0,
                    const double commission = 0.0,
                    const double close_swap = 0.0,
                    const double fee = 0.0)
{
   string line = "";
   line += CsvEscape("trade-journal-ea-v1") + ",";
   line += CsvEscape(event_type) + ",";
   line += CsvEscape(event_id) + ",";
   line += CsvEscape(TimeText(TimeCurrent())) + ",";
   line += IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + ",";
   line += CsvEscape(AccountInfoString(ACCOUNT_SERVER)) + ",";
   line += ",";
   line += "0,";
   line += IntegerToString((long)position.ticket) + ",";
   line += IntegerToString(position.identifier) + ",";
   line += CsvEscape(position.symbol) + ",";
   line += CsvEscape(position.direction) + ",";
   line += CsvNumber(position.volume) + ",";
   line += CsvNumber(position.entry_price) + ",";
   line += CsvNumber(position.stop_loss) + ",";
   line += CsvNumber(position.take_profit) + ",";
   line += CsvNumber(position.profit) + ",";
   line += CsvNumber(position.swap_value) + ",";
   line += CsvEscape(TimeText(position.open_time)) + ",";
   line += CsvEscape(position.comment) + ",";
   line += CsvEscape(screenshot) + ",";
   line += IntegerToString((long)close_deal) + ",";
   line += CsvEscape(TimeText(close_time)) + ",";
   line += CsvNumber(close_price) + ",";
   line += CsvNumber(close_volume) + ",";
   line += CsvNumber(profit) + ",";
   line += CsvNumber(commission) + ",";
   line += CsvNumber(close_swap) + ",";
   line += CsvNumber(fee);
   return line;
}

void EmitStatus(const string event_type)
{
   g_sequence++;
   EnsureFolders();
   string event_id = "status:" + event_type + ":" + IntegerToString((long)TimeCurrent()) + ":" + IntegerToString(g_sequence);
   string json = "{";
   json += JsonString("schema", "trade-journal-ea-v1") + ",";
   json += JsonString("eaVersion", EA_VERSION) + ",";
   json += JsonString("features", EA_FEATURES) + ",";
   json += JsonString("event", event_type) + ",";
   json += JsonString("eventId", event_id) + ",";
   json += JsonString("time", TimeText(TimeCurrent())) + ",";
   json += JsonLong("accountLogin", AccountInfoInteger(ACCOUNT_LOGIN)) + ",";
   json += JsonString("server", AccountInfoString(ACCOUNT_SERVER)) + ",";
   json += JsonString("chartSymbol", Symbol()) + ",";
   json += JsonLong("positionsTotal", PositionsTotal());
   json += "}";
   AppendJsonLine(json);
   AppendCsvLine(StatusCsvLine(event_type, event_id));
}

string BaseEventJson(const string event_type, const TrackedPosition &position, const string screenshot, const string event_id)
{
   string json = "{";
   json += JsonString("schema", "trade-journal-ea-v1") + ",";
   json += JsonString("eaVersion", EA_VERSION) + ",";
   json += JsonString("features", EA_FEATURES) + ",";
   json += JsonString("event", event_type) + ",";
   json += JsonString("eventId", event_id) + ",";
   json += JsonString("time", TimeText(TimeCurrent())) + ",";
   json += JsonLong("accountLogin", AccountInfoInteger(ACCOUNT_LOGIN)) + ",";
   json += JsonString("server", AccountInfoString(ACCOUNT_SERVER)) + ",";
   json += JsonLong("ticket", (long)position.ticket) + ",";
   json += JsonLong("positionId", position.identifier) + ",";
   json += JsonString("symbol", position.symbol) + ",";
   json += JsonString("direction", position.direction) + ",";
   json += JsonNumber("volume", position.volume) + ",";
   json += JsonNumber("entryPrice", position.entry_price) + ",";
   json += JsonNumber("stopLoss", position.stop_loss) + ",";
   json += JsonNumber("takeProfit", position.take_profit) + ",";
   json += JsonNumber("floatingProfit", position.profit) + ",";
   json += JsonNumber("swap", position.swap_value) + ",";
   json += JsonString("openTime", TimeText(position.open_time)) + ",";
   json += JsonString("comment", position.comment) + ",";
   json += JsonString("screenshot", screenshot);
   return json;
}

void EmitOpenOrUpdate(const string event_type, const TrackedPosition &position)
{
   g_sequence++;
   string event_id = IntegerToString(position.identifier) + ":" + event_type + ":" + IntegerToString((long)TimeCurrent()) + ":" + IntegerToString(g_sequence);
   string screenshot = CaptureScreenshot(event_type, position);
   string json = BaseEventJson(event_type, position, screenshot, event_id);
   json += "}";
   AppendJsonLine(json);
   AppendCsvLine(TradeCsvLine(event_type, event_id, position, screenshot));
}

void EmitClose(const TrackedPosition &position)
{
   datetime from_time = position.open_time - 86400;
   datetime to_time = TimeCurrent() + 60;
   double close_volume = 0.0;
   double weighted_close = 0.0;
   double profit = 0.0;
   double commission = 0.0;
   double swap_value = 0.0;
   double fee = 0.0;
   datetime close_time = TimeCurrent();
   ulong close_deal = 0;

   if(HistorySelect(from_time, to_time))
   {
      int total = HistoryDealsTotal();
      for(int index = 0; index < total; index++)
      {
         ulong deal = HistoryDealGetTicket(index);
         if(deal == 0)
            continue;

         long deal_position_id = HistoryDealGetInteger(deal, DEAL_POSITION_ID);
         if(deal_position_id != position.identifier)
            continue;

         long entry = HistoryDealGetInteger(deal, DEAL_ENTRY);
         if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_INOUT && entry != DEAL_ENTRY_OUT_BY)
            continue;

         double volume = HistoryDealGetDouble(deal, DEAL_VOLUME);
         double price = HistoryDealGetDouble(deal, DEAL_PRICE);
         close_volume += volume;
         weighted_close += price * volume;
         profit += HistoryDealGetDouble(deal, DEAL_PROFIT);
         commission += HistoryDealGetDouble(deal, DEAL_COMMISSION);
         swap_value += HistoryDealGetDouble(deal, DEAL_SWAP);
         fee += HistoryDealGetDouble(deal, DEAL_FEE);
         close_time = (datetime)HistoryDealGetInteger(deal, DEAL_TIME);
         close_deal = deal;
      }
   }

   double close_price = close_volume > 0.0 ? weighted_close / close_volume : 0.0;
   g_sequence++;
   string event_id = IntegerToString(position.identifier) + ":close:" + IntegerToString((long)TimeCurrent()) + ":" + IntegerToString(g_sequence);
   string screenshot = CaptureScreenshot("close", position, close_price, close_time);
   string json = BaseEventJson("close", position, screenshot, event_id);
   json += ",";
   json += JsonLong("closeDeal", (long)close_deal) + ",";
   json += JsonString("closeTime", TimeText(close_time)) + ",";
   json += JsonNumber("closePrice", close_price) + ",";
   json += JsonNumber("closeVolume", close_volume) + ",";
   json += JsonNumber("profit", profit) + ",";
   json += JsonNumber("commission", commission) + ",";
   json += JsonNumber("closeSwap", swap_value) + ",";
   json += JsonNumber("fee", fee);
   json += "}";
   AppendJsonLine(json);
   AppendCsvLine(TradeCsvLine("close", event_id, position, screenshot, close_deal, close_time, close_price, close_volume, profit, commission, swap_value, fee));
}

void ScanPositions()
{
   if(g_is_scanning)
      return;
   g_is_scanning = true;

   for(int index = 0; index < ArraySize(g_positions); index++)
      g_positions[index].seen = false;

   int total = PositionsTotal();
   for(int index = 0; index < total; index++)
   {
      TrackedPosition current;
      if(!LoadPositionByIndex(index, current))
         continue;

      int existing_index = FindTrackedByIdentifier(current.identifier);
      if(existing_index < 0)
      {
         int size = ArraySize(g_positions);
         ArrayResize(g_positions, size + 1);
         g_positions[size] = current;
         EmitOpenOrUpdate("open", current);
      }
      else
      {
         if(SignificantUpdate(g_positions[existing_index], current))
            EmitOpenOrUpdate("update", current);
         g_positions[existing_index] = current;
      }
   }

   for(int index = ArraySize(g_positions) - 1; index >= 0; index--)
   {
      if(g_positions[index].seen)
         continue;

      EmitClose(g_positions[index]);
      ArrayRemove(g_positions, index, 1);
   }

   g_is_scanning = false;
}

int OnInit()
{
   if(!AcquireInstanceLock())
      return INIT_FAILED;

   EnsureFolders();
   EventSetTimer((int)MathMax(1, InpScanSeconds));
   EmitStatus("ea_start");
   ScanPositions();
   Print("TradeJournalExporterEA initialized. Export files: MQL5/Files/", InpExportDir, "/events.jsonl and events.csv");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EmitStatus("ea_stop");
   EventKillTimer();
   CloseScreenshotChart();
   ReleaseInstanceLock();
}

void OnTimer()
{
   static datetime last_heartbeat = 0;
   if(InpHeartbeatSeconds > 0 && TimeCurrent() - last_heartbeat >= InpHeartbeatSeconds)
   {
      EmitStatus("heartbeat");
      last_heartbeat = TimeCurrent();
   }
   ScanPositions();
}

void OnTrade()
{
   ScanPositions();
}

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   ScanPositions();
}





