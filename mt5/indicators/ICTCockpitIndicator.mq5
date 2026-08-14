//+------------------------------------------------------------------+
//| ICTCockpitIndicator.mq5                                          |
//| MT5 port of the Personal ICT Cockpit TradingView indicator.       |
//+------------------------------------------------------------------+
#property strict
#property indicator_chart_window
#property indicator_plots 0
#property version "1.00"
#property description "Marks BSL/SSL, sweeps, BOS/CHoCH, FVG/OB, PD range, and strict ICT setup guides."

enum ICT_MARKET_PRESET
{
   ICT_PRESET_AUTO = 0,
   ICT_PRESET_XAU_FX_CFD = 1,
   ICT_PRESET_CRYPTO = 2,
   ICT_PRESET_INDEX = 3,
   ICT_PRESET_STOCKS = 4,
   ICT_PRESET_MANUAL = 5
};

enum ICT_BUFFER_MODE
{
   ICT_BUFFER_ATR = 0,
   ICT_BUFFER_TICKS = 1
};

input group "Structure"
input int InpSwingPivotLength = 5; // 스윙 피벗 길이
input int InpSweepValidBars = 20; // 스윕 유효 캔들 수
input int InpMaxBarsToScan = 800; // 분석할 최대 캔들 수

input group "Instrument Adaptation"
input ICT_MARKET_PRESET InpMarketPreset = ICT_PRESET_AUTO; // 종목 프리셋
input ICT_BUFFER_MODE InpSLBufferMode = ICT_BUFFER_ATR; // SL 버퍼 방식
input int InpAtrLength = 14; // ATR 길이
input double InpSLBufferAtrMultiple = 0.04; // ATR SL 버퍼 배수

input group "Display"
input bool InpShowLearningObjects = true; // 학습용 구조물 표시
input bool InpShowSetupLabels = true; // 셋업 라벨 표시
input bool InpShowTradeGuides = true; // 진입/SL/TP 가이드 표시
input bool InpShowBosChochLines = true; // BOS/CHoCH 점선 표시
input bool InpShowLiquidityLines = true; // BSL/SSL 유동성 라인 표시
input int InpMaxStructureMarks = 60; // 구조 표시 최대 개수
input int InpTextFontSize = 8; // 전체 텍스트 크기

input group "PD Array"
input bool InpShowPdArray = true; // 프리미엄/디스카운트 표시
input bool InpUsePdFilter = true; // PD 필터 사용

input group "FVG / OB"
input bool InpShowFvgZones = true; // FVG 영역 표시
input bool InpShowObZones = true; // OB 영역 표시
input bool InpDeleteMitigatedZones = false; // 해소된 영역 삭제
input int InpMaxZonesPerType = 35; // 종류별 최대 영역 수
input int InpObSearchCandles = 15; // OB 탐색 캔들 수
input int InpTpLiquidityLookback = 120; // TP 유동성 탐색 캔들 수
input int InpSLBufferTicks = 2; // 틱 SL 버퍼
input int InpActiveFvgOpacityPercent = 84; // 활성 FVG 투명도
input int InpMitigatedFvgOpacityPercent = 92; // 해소 FVG 투명도
input int InpActiveObOpacityPercent = 78; // 활성 OB 투명도
input int InpMitigatedObOpacityPercent = 92; // 해소 OB 투명도

input group "Optional HTF Bias"
input bool InpUseHtfEmaBias = false; // HTF EMA 보조 필터
input ENUM_TIMEFRAMES InpHtfTimeframe = PERIOD_H1; // HTF EMA 시간프레임
input int InpHtfEmaLength = 50; // HTF EMA 길이

input group "Visual"
input color InpBullColor = clrLimeGreen; // 상승 구조 색상
input color InpBearColor = clrTomato; // 하락 구조 색상
input color InpBullFvgColor = clrMediumSeaGreen; // 상승 FVG 채움
input color InpBullFvgBorderColor = clrLimeGreen; // 상승 FVG 테두리
input color InpBearFvgColor = clrLightCoral; // 하락 FVG 채움
input color InpBearFvgBorderColor = clrTomato; // 하락 FVG 테두리
input color InpMitigatedFvgColor = clrDimGray; // 해소 FVG 채움
input color InpMitigatedFvgBorderColor = clrGray; // 해소 FVG 테두리
input color InpBullObColor = clrSeaGreen; // 상승 OB 채움
input color InpBullObBorderColor = clrGreen; // 상승 OB 테두리
input color InpBearObColor = clrIndianRed; // 하락 OB 채움
input color InpBearObBorderColor = clrFireBrick; // 하락 OB 테두리
input color InpMitigatedObColor = clrDimGray; // 해소 OB 채움
input color InpMitigatedObBorderColor = clrGray; // 해소 OB 테두리
input color InpNeutralColor = clrSilver; // 중립 색상

struct IctZone
{
   string name;
   string kind;
   bool is_bull;
   bool active;
   int left_shift;
   int right_shift;
   double top;
   double bottom;
};

struct LatestZone
{
   bool active;
   int shift;
   double top;
   double bottom;
};

struct LatestGuide
{
   bool active;
   bool is_bull;
   int shift;
   double entry_top;
   double entry_bottom;
   double sl;
   double tp;
};

string PREFIX = "ICTC_";
int g_sequence = 0;
int g_htf_ema_handle = INVALID_HANDLE;

int ActiveSwingLen()
{
   if(InpMarketPreset == ICT_PRESET_MANUAL)
      return MathMax(2, InpSwingPivotLength);
   if(InpMarketPreset == ICT_PRESET_CRYPTO)
      return 7;
   if(InpMarketPreset == ICT_PRESET_INDEX || InpMarketPreset == ICT_PRESET_STOCKS)
      return 6;
   return 5;
}

int ActiveSweepWindow()
{
   if(InpMarketPreset == ICT_PRESET_MANUAL)
      return MathMax(1, InpSweepValidBars);
   if(InpMarketPreset == ICT_PRESET_CRYPTO)
      return 30;
   if(InpMarketPreset == ICT_PRESET_INDEX)
      return 24;
   if(InpMarketPreset == ICT_PRESET_STOCKS)
      return 25;
   return 20;
}

int ActiveObLookback()
{
   if(InpMarketPreset == ICT_PRESET_MANUAL)
      return MathMax(3, InpObSearchCandles);
   if(InpMarketPreset == ICT_PRESET_CRYPTO || InpMarketPreset == ICT_PRESET_STOCKS)
      return 20;
   if(InpMarketPreset == ICT_PRESET_INDEX)
      return 18;
   return 15;
}

int ActiveTargetLookback()
{
   if(InpMarketPreset == ICT_PRESET_MANUAL)
      return MathMax(20, InpTpLiquidityLookback);
   if(InpMarketPreset == ICT_PRESET_CRYPTO)
      return 160;
   if(InpMarketPreset == ICT_PRESET_STOCKS)
      return 150;
   if(InpMarketPreset == ICT_PRESET_INDEX)
      return 140;
   return 120;
}

string NextName(const string suffix)
{
   g_sequence++;
   return PREFIX + suffix + "_" + IntegerToString(g_sequence);
}

void DeleteObjectsByPrefix()
{
   for(int index = ObjectsTotal(0, 0, -1) - 1; index >= 0; index--)
   {
      string name = ObjectName(0, index, 0, -1);
      if(StringFind(name, PREFIX) == 0)
         ObjectDelete(0, name);
   }
   g_sequence = 0;
}

void SetObjectCommon(const string name, const color line_color, const bool back = false)
{
   ObjectSetInteger(0, name, OBJPROP_COLOR, line_color);
   ObjectSetInteger(0, name, OBJPROP_BACK, back);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
}

void DrawLineObject(const string suffix, const datetime left_time, const double left_price, const datetime right_time, const double right_price, const color line_color, const ENUM_LINE_STYLE style, const int width)
{
   string name = NextName(suffix);
   if(!ObjectCreate(0, name, OBJ_TREND, 0, left_time, left_price, right_time, right_price))
      return;
   SetObjectCommon(name, line_color);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, name, OBJPROP_STYLE, style);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, width);
}

void DrawSegment(const string suffix, const datetime left_time, const double price, const datetime right_time, const color line_color, const ENUM_LINE_STYLE style, const int width)
{
   DrawLineObject(suffix, left_time, price, right_time, price, line_color, style, width);
}

datetime MidTime(const datetime left_time, const datetime right_time)
{
   return (datetime)(((long)left_time + (long)right_time) / 2);
}

double TextOffset()
{
   double max_price = 0.0;
   double min_price = 0.0;
   if(ChartGetDouble(0, CHART_PRICE_MAX, 0, max_price) && ChartGetDouble(0, CHART_PRICE_MIN, 0, min_price) && max_price > min_price)
      return MathMax(_Point * 20.0, (max_price - min_price) * 0.008);
   return _Point * 20.0;
}

double LineTextPrice(const double price, const bool is_bull)
{
   return is_bull ? price + TextOffset() : price - TextOffset();
}

int TextFontSize()
{
   return MathMax(6, MathMin(18, InpTextFontSize));
}

void DrawText(const string suffix, const datetime time_value, const double price, const string text, const color text_color, const int font_size = 8, const ENUM_ANCHOR_POINT anchor = ANCHOR_LEFT)
{
   string name = NextName(suffix);
   if(!ObjectCreate(0, name, OBJ_TEXT, 0, time_value, price))
      return;
   SetObjectCommon(name, text_color);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, TextFontSize());
   ObjectSetInteger(0, name, OBJPROP_ANCHOR, anchor);
}

void DrawLineText(const string suffix, const datetime left_time, const datetime right_time, const double price, const string text, const color text_color, const bool is_bull)
{
   DrawText(suffix, MidTime(left_time, right_time), LineTextPrice(price, is_bull), text, text_color, 8, ANCHOR_CENTER);
}

int ColorRed(const color value)
{
   return (int)(value & 0x0000FF);
}

int ColorGreen(const color value)
{
   return (int)((value >> 8) & 0x0000FF);
}

int ColorBlue(const color value)
{
   return (int)((value >> 16) & 0x0000FF);
}

color MakeRgb(const int red, const int green, const int blue)
{
   int r = MathMax(0, MathMin(255, red));
   int g = MathMax(0, MathMin(255, green));
   int b = MathMax(0, MathMin(255, blue));
   return (color)(r | (g << 8) | (b << 16));
}

color ChartBackgroundColor()
{
   long background = 0;
   if(ChartGetInteger(0, CHART_COLOR_BACKGROUND, 0, background))
      return (color)background;
   return clrBlack;
}

color OpacityColor(const color base_color, const int opacity_percent)
{
   int opacity = MathMax(0, MathMin(100, opacity_percent));
   color background = ChartBackgroundColor();
   double visible = (100.0 - opacity) / 100.0;
   int red = (int)MathRound(ColorRed(base_color) * visible + ColorRed(background) * (1.0 - visible));
   int green = (int)MathRound(ColorGreen(base_color) * visible + ColorGreen(background) * (1.0 - visible));
   int blue = (int)MathRound(ColorBlue(base_color) * visible + ColorBlue(background) * (1.0 - visible));
   return MakeRgb(red, green, blue);
}

void DrawZoneBorder(const string suffix, const datetime left_time, const double top, const datetime right_time, const double bottom, const color border_color)
{
   DrawLineObject(suffix + "_border_top", left_time, top, right_time, top, border_color, STYLE_SOLID, 1);
   DrawLineObject(suffix + "_border_bottom", left_time, bottom, right_time, bottom, border_color, STYLE_SOLID, 1);
   DrawLineObject(suffix + "_border_left", left_time, top, left_time, bottom, border_color, STYLE_SOLID, 1);
   DrawLineObject(suffix + "_border_right", right_time, top, right_time, bottom, border_color, STYLE_SOLID, 1);
}

void DrawRectangle(const string suffix, const datetime left_time, const double top, const datetime right_time, const double bottom, const color fill_color, const color border_color, const int opacity_percent, const string label)
{
   if(top <= bottom)
      return;

   string name = NextName(suffix);
   if(!ObjectCreate(0, name, OBJ_RECTANGLE, 0, left_time, top, right_time, bottom))
      return;
   SetObjectCommon(name, OpacityColor(fill_color, opacity_percent), true);
   ObjectSetInteger(0, name, OBJPROP_FILL, true);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);

   DrawZoneBorder(suffix, left_time, top, right_time, bottom, border_color);
   DrawText(suffix + "_label", MidTime(left_time, right_time), (top + bottom) / 2.0, label, border_color, 7, ANCHOR_CENTER);
}

void DrawArrowText(const string suffix, const datetime time_value, const double price, const string text, const color text_color)
{
   DrawText(suffix, time_value, price, text, text_color, 8);
}

void DrawSweepText(const string suffix, const datetime time_value, const double candle_high, const double candle_low, const string text, const color text_color, const bool is_buy_side)
{
   double sweep_price = is_buy_side ? candle_high + TextOffset() * 1.2 : candle_low - TextOffset() * 1.2;
   DrawText(suffix, time_value, sweep_price, text, text_color, 8, ANCHOR_CENTER);
}

bool IsPivotHigh(const int shift, const int pivot_len, const double &high[], const int rates_total)
{
   if(shift - pivot_len < 0 || shift + pivot_len >= rates_total)
      return false;
   double value = high[shift];
   for(int offset = 1; offset <= pivot_len; offset++)
   {
      if(high[shift - offset] >= value || high[shift + offset] >= value)
         return false;
   }
   return true;
}

bool IsPivotLow(const int shift, const int pivot_len, const double &low[], const int rates_total)
{
   if(shift - pivot_len < 0 || shift + pivot_len >= rates_total)
      return false;
   double value = low[shift];
   for(int offset = 1; offset <= pivot_len; offset++)
   {
      if(low[shift - offset] <= value || low[shift + offset] <= value)
         return false;
   }
   return true;
}

double SimpleAtr(const int shift, const int atr_len, const double &high[], const double &low[], const double &close[], const int rates_total)
{
   int count = 0;
   double total = 0.0;
   for(int index = shift; index < MathMin(rates_total - 1, shift + atr_len); index++)
   {
      double previous_close = close[index + 1];
      double tr = MathMax(high[index] - low[index], MathMax(MathAbs(high[index] - previous_close), MathAbs(low[index] - previous_close)));
      total += tr;
      count++;
   }
   if(count <= 0)
      return 0.0;
   return total / count;
}

double HtfEmaAt(const datetime bar_time)
{
   if(!InpUseHtfEmaBias || g_htf_ema_handle == INVALID_HANDLE)
      return 0.0;

   double buffer[];
   ArraySetAsSeries(buffer, true);
   int copied = CopyBuffer(g_htf_ema_handle, 0, bar_time, 1, buffer);
   if(copied <= 0)
      return 0.0;
   return buffer[0];
}

bool FindBullOb(const int shift, const int lookback, const double &open[], const double &high[], const double &low[], const double &close[], const int rates_total, int &left_shift, double &top, double &bottom)
{
   for(int offset = 1; offset <= lookback && shift + offset < rates_total; offset++)
   {
      int candidate = shift + offset;
      if(close[candidate] < open[candidate])
      {
         left_shift = candidate;
         top = high[candidate];
         bottom = low[candidate];
         return true;
      }
   }
   return false;
}

bool FindBearOb(const int shift, const int lookback, const double &open[], const double &high[], const double &low[], const double &close[], const int rates_total, int &left_shift, double &top, double &bottom)
{
   for(int offset = 1; offset <= lookback && shift + offset < rates_total; offset++)
   {
      int candidate = shift + offset;
      if(close[candidate] > open[candidate])
      {
         left_shift = candidate;
         top = high[candidate];
         bottom = low[candidate];
         return true;
      }
   }
   return false;
}

void AddZone(IctZone &zones[], int &count, const int limit, const string kind, const bool is_bull, const int left_shift, const int current_shift, const double top, const double bottom)
{
   if(top <= bottom)
      return;

   if(count >= limit)
   {
      for(int index = 1; index < count; index++)
         zones[index - 1] = zones[index];
      count = limit - 1;
   }

   IctZone zone;
   zone.name = kind;
   zone.kind = kind;
   zone.is_bull = is_bull;
   zone.active = true;
   zone.left_shift = left_shift;
   zone.right_shift = current_shift;
   zone.top = top;
   zone.bottom = bottom;
   zones[count] = zone;
   count++;
}

void UpdateZones(IctZone &zones[], int &count, const int shift, const double bar_high, const double bar_low)
{
   for(int index = 0; index < count; index++)
   {
      if(!zones[index].active)
         continue;

      zones[index].right_shift = shift;
      bool mitigated = zones[index].is_bull ? (bar_low <= zones[index].bottom) : (bar_high >= zones[index].top);
      if(mitigated)
      {
         if(InpDeleteMitigatedZones)
         {
            for(int move = index + 1; move < count; move++)
               zones[move - 1] = zones[move];
            count--;
            index--;
         }
         else
         {
            zones[index].active = false;
            zones[index].right_shift = shift;
         }
      }
   }
}

double HighestBefore(const int shift, const int lookback, const double &high[], const int rates_total)
{
   double result = 0.0;
   bool has_value = false;
   for(int offset = 1; offset <= lookback && shift + offset < rates_total; offset++)
   {
      double value = high[shift + offset];
      if(!has_value || value > result)
      {
         result = value;
         has_value = true;
      }
   }
   return has_value ? result : 0.0;
}

double LowestBefore(const int shift, const int lookback, const double &low[], const int rates_total)
{
   double result = 0.0;
   bool has_value = false;
   for(int offset = 1; offset <= lookback && shift + offset < rates_total; offset++)
   {
      double value = low[shift + offset];
      if(!has_value || value < result)
      {
         result = value;
         has_value = true;
      }
   }
   return has_value ? result : 0.0;
}

int OnInit()
{
   if(InpUseHtfEmaBias)
      g_htf_ema_handle = iMA(_Symbol, InpHtfTimeframe, MathMax(5, InpHtfEmaLength), 0, MODE_EMA, PRICE_CLOSE);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   DeleteObjectsByPrefix();
   if(g_htf_ema_handle != INVALID_HANDLE)
      IndicatorRelease(g_htf_ema_handle);
}

int OnCalculate(
   const int rates_total,
   const int prev_calculated,
   const datetime &time[],
   const double &open[],
   const double &high[],
   const double &low[],
   const double &close[],
   const long &tick_volume[],
   const long &volume[],
   const int &spread[]
)
{
   ArraySetAsSeries(time, true);
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);

   int pivot_len = ActiveSwingLen();
   int ob_lookback = ActiveObLookback();
   int target_lookback = ActiveTargetLookback();
   int sweep_window = ActiveSweepWindow();
   int safety_bars = MathMax(MathMax(pivot_len * 2 + 2, ob_lookback + 2), target_lookback + 2);

   if(rates_total <= safety_bars + 5)
      return rates_total;

   DeleteObjectsByPrefix();

   int start_shift = MathMin(InpMaxBarsToScan, rates_total - safety_bars - 1);
   start_shift = MathMax(start_shift, 1);

   double last_swing_high = 0.0;
   double last_swing_low = 0.0;
   int last_swing_high_shift = -1;
   int last_swing_low_shift = -1;
   bool has_swing_high = false;
   bool has_swing_low = false;
   int trend = 0;
   int last_bsl_sweep_shift = -1;
   int last_ssl_sweep_shift = -1;
   double last_bsl_sweep_price = 0.0;
   double last_ssl_sweep_price = 0.0;

   LatestZone bull_fvg;
   LatestZone bear_fvg;
   LatestZone bull_ob;
   LatestZone bear_ob;
   bull_fvg.active = false;
   bear_fvg.active = false;
   bull_ob.active = false;
   bear_ob.active = false;

   LatestGuide latest_guide;
   latest_guide.active = false;

   IctZone bull_fvgs[];
   IctZone bear_fvgs[];
   IctZone bull_obs[];
   IctZone bear_obs[];
   ArrayResize(bull_fvgs, MathMax(1, InpMaxZonesPerType));
   ArrayResize(bear_fvgs, MathMax(1, InpMaxZonesPerType));
   ArrayResize(bull_obs, MathMax(1, InpMaxZonesPerType));
   ArrayResize(bear_obs, MathMax(1, InpMaxZonesPerType));
   int bull_fvg_count = 0;
   int bear_fvg_count = 0;
   int bull_ob_count = 0;
   int bear_ob_count = 0;
   int structure_count = 0;
   int last_bull_structure_pivot_shift = -1;
   int last_bear_structure_pivot_shift = -1;

   for(int shift = start_shift; shift >= 0; shift--)
   {
      int pivot_shift = shift + pivot_len;
      if(IsPivotHigh(pivot_shift, pivot_len, high, rates_total))
      {
         last_swing_high = high[pivot_shift];
         last_swing_high_shift = pivot_shift;
         has_swing_high = true;
      }

      if(IsPivotLow(pivot_shift, pivot_len, low, rates_total))
      {
         last_swing_low = low[pivot_shift];
         last_swing_low_shift = pivot_shift;
         has_swing_low = true;
      }

      bool external_ok = has_swing_high && has_swing_low && last_swing_high > last_swing_low;
      double eq = external_ok ? (last_swing_high + last_swing_low) / 2.0 : 0.0;
      bool in_discount = external_ok && close[shift] <= eq;
      bool in_premium = external_ok && close[shift] >= eq;

      bool buy_side_sweep = has_swing_high && high[shift] > last_swing_high && close[shift] < last_swing_high;
      bool sell_side_sweep = has_swing_low && low[shift] < last_swing_low && close[shift] > last_swing_low;

      if(buy_side_sweep)
      {
         last_bsl_sweep_shift = shift;
         last_bsl_sweep_price = high[shift];
         if(InpShowLearningObjects)
            DrawSweepText("bsl_sweep", time[shift], high[shift], low[shift], "BS", InpBearColor, true);
      }

      if(sell_side_sweep)
      {
         last_ssl_sweep_shift = shift;
         last_ssl_sweep_price = low[shift];
         if(InpShowLearningObjects)
            DrawSweepText("ssl_sweep", time[shift], high[shift], low[shift], "SS", InpBullColor, false);
      }

      bool recent_bsl_sweep = last_bsl_sweep_shift >= 0 && (last_bsl_sweep_shift - shift) <= sweep_window;
      bool recent_ssl_sweep = last_ssl_sweep_shift >= 0 && (last_ssl_sweep_shift - shift) <= sweep_window;
      bool bullish_break = has_swing_high && shift + 1 < rates_total && close[shift] > last_swing_high && close[shift + 1] <= last_swing_high;
      bool bearish_break = has_swing_low && shift + 1 < rates_total && close[shift] < last_swing_low && close[shift + 1] >= last_swing_low;

      if(bullish_break)
      {
         string break_name = trend == -1 ? "CHoCH" : "BOS";
         bool fresh_structure = last_swing_high_shift != last_bull_structure_pivot_shift;
         if(fresh_structure && InpShowLearningObjects && InpShowBosChochLines && structure_count < InpMaxStructureMarks)
         {
            DrawSegment("structure", time[last_swing_high_shift], last_swing_high, time[shift], InpBullColor, STYLE_DOT, 2);
            DrawLineText("structure_text", time[last_swing_high_shift], time[shift], last_swing_high, break_name, InpBullColor, true);
            last_bull_structure_pivot_shift = last_swing_high_shift;
            structure_count++;
         }
         trend = 1;
      }

      if(bearish_break)
      {
         string break_name = trend == 1 ? "CHoCH" : "BOS";
         bool fresh_structure = last_swing_low_shift != last_bear_structure_pivot_shift;
         if(fresh_structure && InpShowLearningObjects && InpShowBosChochLines && structure_count < InpMaxStructureMarks)
         {
            DrawSegment("structure", time[last_swing_low_shift], last_swing_low, time[shift], InpBearColor, STYLE_DOT, 2);
            DrawLineText("structure_text", time[last_swing_low_shift], time[shift], last_swing_low, break_name, InpBearColor, false);
            last_bear_structure_pivot_shift = last_swing_low_shift;
            structure_count++;
         }
         trend = -1;
      }

      bool is_bull_fvg = shift + 2 < rates_total && low[shift] > high[shift + 2];
      bool is_bear_fvg = shift + 2 < rates_total && high[shift] < low[shift + 2];

      if(is_bull_fvg)
      {
         bull_fvg.active = true;
         bull_fvg.shift = shift;
         bull_fvg.top = low[shift];
         bull_fvg.bottom = high[shift + 2];
         AddZone(bull_fvgs, bull_fvg_count, MathMax(1, InpMaxZonesPerType), "Bull FVG", true, shift + 2, shift, bull_fvg.top, bull_fvg.bottom);
      }

      if(is_bear_fvg)
      {
         bear_fvg.active = true;
         bear_fvg.shift = shift;
         bear_fvg.top = low[shift + 2];
         bear_fvg.bottom = high[shift];
         AddZone(bear_fvgs, bear_fvg_count, MathMax(1, InpMaxZonesPerType), "Bear FVG", false, shift + 2, shift, bear_fvg.top, bear_fvg.bottom);
      }

      if(bullish_break)
      {
         int ob_shift = -1;
         double ob_top = 0.0;
         double ob_bottom = 0.0;
         if(FindBullOb(shift, ob_lookback, open, high, low, close, rates_total, ob_shift, ob_top, ob_bottom))
         {
            bull_ob.active = true;
            bull_ob.shift = ob_shift;
            bull_ob.top = ob_top;
            bull_ob.bottom = ob_bottom;
            AddZone(bull_obs, bull_ob_count, MathMax(1, InpMaxZonesPerType), "Bull OB", true, ob_shift, shift, ob_top, ob_bottom);
         }
      }

      if(bearish_break)
      {
         int ob_shift = -1;
         double ob_top = 0.0;
         double ob_bottom = 0.0;
         if(FindBearOb(shift, ob_lookback, open, high, low, close, rates_total, ob_shift, ob_top, ob_bottom))
         {
            bear_ob.active = true;
            bear_ob.shift = ob_shift;
            bear_ob.top = ob_top;
            bear_ob.bottom = ob_bottom;
            AddZone(bear_obs, bear_ob_count, MathMax(1, InpMaxZonesPerType), "Bear OB", false, ob_shift, shift, ob_top, ob_bottom);
         }
      }

      UpdateZones(bull_fvgs, bull_fvg_count, shift, high[shift], low[shift]);
      UpdateZones(bear_fvgs, bear_fvg_count, shift, high[shift], low[shift]);
      UpdateZones(bull_obs, bull_ob_count, shift, high[shift], low[shift]);
      UpdateZones(bear_obs, bear_ob_count, shift, high[shift], low[shift]);

      if(bull_fvg.active && low[shift] <= bull_fvg.bottom)
         bull_fvg.active = false;
      if(bear_fvg.active && high[shift] >= bear_fvg.top)
         bear_fvg.active = false;
      if(bull_ob.active && low[shift] <= bull_ob.bottom)
         bull_ob.active = false;
      if(bear_ob.active && high[shift] >= bear_ob.top)
         bear_ob.active = false;

      double htf_ema = HtfEmaAt(time[shift]);
      bool htf_bull_ok = !InpUseHtfEmaBias || htf_ema <= 0.0 || close[shift] >= htf_ema;
      bool htf_bear_ok = !InpUseHtfEmaBias || htf_ema <= 0.0 || close[shift] <= htf_ema;
      bool pd_bull_ok = !InpUsePdFilter || !external_ok || in_discount;
      bool pd_bear_ok = !InpUsePdFilter || !external_ok || in_premium;

      bool bull_fvg_fresh = bull_fvg.active && last_ssl_sweep_shift >= 0 && bull_fvg.shift <= last_ssl_sweep_shift;
      bool bull_ob_fresh = bull_ob.active && last_ssl_sweep_shift >= 0 && bull_ob.shift <= last_ssl_sweep_shift;
      bool bear_fvg_fresh = bear_fvg.active && last_bsl_sweep_shift >= 0 && bear_fvg.shift <= last_bsl_sweep_shift;
      bool bear_ob_fresh = bear_ob.active && last_bsl_sweep_shift >= 0 && bear_ob.shift <= last_bsl_sweep_shift;

      bool has_fresh_bull_zone = bull_fvg_fresh || bull_ob_fresh;
      bool has_fresh_bear_zone = bear_fvg_fresh || bear_ob_fresh;
      bool bull_setup = bullish_break && recent_ssl_sweep && pd_bull_ok && htf_bull_ok && has_fresh_bull_zone;
      bool bear_setup = bearish_break && recent_bsl_sweep && pd_bear_ok && htf_bear_ok && has_fresh_bear_zone;

      if(bull_setup || bear_setup)
      {
         bool use_bull_ob = bull_ob_fresh && (!bull_fvg_fresh || bull_ob.shift <= bull_fvg.shift);
         bool use_bear_ob = bear_ob_fresh && (!bear_fvg_fresh || bear_ob.shift <= bear_fvg.shift);
         double entry_top = bull_setup ? (use_bull_ob ? bull_ob.top : bull_fvg.top) : (use_bear_ob ? bear_ob.top : bear_fvg.top);
         double entry_bottom = bull_setup ? (use_bull_ob ? bull_ob.bottom : bull_fvg.bottom) : (use_bear_ob ? bear_ob.bottom : bear_fvg.bottom);
         double sl_buffer = InpSLBufferMode == ICT_BUFFER_ATR ? SimpleAtr(shift, MathMax(1, InpAtrLength), high, low, close, rates_total) * InpSLBufferAtrMultiple : _Point * InpSLBufferTicks;
         double sl_price = bull_setup ? last_ssl_sweep_price - sl_buffer : last_bsl_sweep_price + sl_buffer;
         double tp_price = bull_setup ? HighestBefore(shift, target_lookback, high, rates_total) : LowestBefore(shift, target_lookback, low, rates_total);

         if(InpShowSetupLabels)
         {
            string setup_text = bull_setup ? "L Setup" : "S Setup";
            DrawText("setup", time[shift], bull_setup ? low[shift] : high[shift], setup_text, bull_setup ? InpBullColor : InpBearColor, 9);
         }

         if(entry_top > entry_bottom && sl_price > 0.0 && tp_price > 0.0)
         {
            latest_guide.active = true;
            latest_guide.is_bull = bull_setup;
            latest_guide.shift = shift;
            latest_guide.entry_top = entry_top;
            latest_guide.entry_bottom = entry_bottom;
            latest_guide.sl = sl_price;
            latest_guide.tp = tp_price;
         }
      }
   }

   datetime current_time = time[0];

   if(InpShowLearningObjects && InpShowLiquidityLines)
   {
      if(has_swing_high)
      {
         DrawSegment("bsl", time[last_swing_high_shift], last_swing_high, current_time, InpBearColor, STYLE_DASH, 1);
         DrawLineText("bsl_text", time[last_swing_high_shift], current_time, last_swing_high, "BSL", InpBearColor, true);
      }
      if(has_swing_low)
      {
         DrawSegment("ssl", time[last_swing_low_shift], last_swing_low, current_time, InpBullColor, STYLE_DASH, 1);
         DrawLineText("ssl_text", time[last_swing_low_shift], current_time, last_swing_low, "SSL", InpBullColor, false);
      }
   }

   if(InpShowLearningObjects && InpShowPdArray && has_swing_high && has_swing_low && last_swing_high > last_swing_low)
   {
      double eq = (last_swing_high + last_swing_low) / 2.0;
      datetime left_time = time[MathMax(last_swing_high_shift, last_swing_low_shift)];
      DrawSegment("pd_high", left_time, last_swing_high, current_time, InpBearColor, STYLE_DOT, 1);
      DrawSegment("pd_low", left_time, last_swing_low, current_time, InpBullColor, STYLE_DOT, 1);
      DrawSegment("pd_eq", left_time, eq, current_time, InpNeutralColor, STYLE_DOT, 1);
      DrawText("pd_eq_text", current_time, eq, "EQ", InpNeutralColor);
   }

   if(InpShowLearningObjects && InpShowFvgZones)
   {
      for(int index = 0; index < bull_fvg_count; index++)
      {
         color fill_color = bull_fvgs[index].active ? InpBullFvgColor : InpMitigatedFvgColor;
         color border_color = bull_fvgs[index].active ? InpBullFvgBorderColor : InpMitigatedFvgBorderColor;
         int opacity = bull_fvgs[index].active ? InpActiveFvgOpacityPercent : InpMitigatedFvgOpacityPercent;
         DrawRectangle("bull_fvg", time[bull_fvgs[index].left_shift], bull_fvgs[index].top, time[bull_fvgs[index].right_shift], bull_fvgs[index].bottom, fill_color, border_color, opacity, "Bull FVG");
      }
      for(int index = 0; index < bear_fvg_count; index++)
      {
         color fill_color = bear_fvgs[index].active ? InpBearFvgColor : InpMitigatedFvgColor;
         color border_color = bear_fvgs[index].active ? InpBearFvgBorderColor : InpMitigatedFvgBorderColor;
         int opacity = bear_fvgs[index].active ? InpActiveFvgOpacityPercent : InpMitigatedFvgOpacityPercent;
         DrawRectangle("bear_fvg", time[bear_fvgs[index].left_shift], bear_fvgs[index].top, time[bear_fvgs[index].right_shift], bear_fvgs[index].bottom, fill_color, border_color, opacity, "Bear FVG");
      }
   }

   if(InpShowLearningObjects && InpShowObZones)
   {
      for(int index = 0; index < bull_ob_count; index++)
      {
         color fill_color = bull_obs[index].active ? InpBullObColor : InpMitigatedObColor;
         color border_color = bull_obs[index].active ? InpBullObBorderColor : InpMitigatedObBorderColor;
         int opacity = bull_obs[index].active ? InpActiveObOpacityPercent : InpMitigatedObOpacityPercent;
         DrawRectangle("bull_ob", time[bull_obs[index].left_shift], bull_obs[index].top, time[bull_obs[index].right_shift], bull_obs[index].bottom, fill_color, border_color, opacity, "Bull OB");
      }
      for(int index = 0; index < bear_ob_count; index++)
      {
         color fill_color = bear_obs[index].active ? InpBearObColor : InpMitigatedObColor;
         color border_color = bear_obs[index].active ? InpBearObBorderColor : InpMitigatedObBorderColor;
         int opacity = bear_obs[index].active ? InpActiveObOpacityPercent : InpMitigatedObOpacityPercent;
         DrawRectangle("bear_ob", time[bear_obs[index].left_shift], bear_obs[index].top, time[bear_obs[index].right_shift], bear_obs[index].bottom, fill_color, border_color, opacity, "Bear OB");
      }
   }

   if(InpShowTradeGuides && latest_guide.active)
   {
      color guide_color = latest_guide.is_bull ? InpBullColor : InpBearColor;
      DrawSegment("guide_entry_top", time[latest_guide.shift], latest_guide.entry_top, current_time, guide_color, STYLE_SOLID, 2);
      DrawSegment("guide_entry_bottom", time[latest_guide.shift], latest_guide.entry_bottom, current_time, guide_color, STYLE_SOLID, 1);
      DrawSegment("guide_sl", time[latest_guide.shift], latest_guide.sl, current_time, InpBearColor, STYLE_DASH, 2);
      DrawSegment("guide_tp", time[latest_guide.shift], latest_guide.tp, current_time, InpBullColor, STYLE_DASH, 2);
      DrawText("guide_text", time[latest_guide.shift], latest_guide.entry_top, latest_guide.is_bull ? "L Guide" : "S Guide", guide_color, 8);
   }

   return rates_total;
}
