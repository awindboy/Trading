//+------------------------------------------------------------------+
//| V11WaveCandle.mq5                                                |
//| V11 Wave Candle: smoothed M5 settlement-density H4 contour       |
//| Research visualization only / no trade authority                 |
//+------------------------------------------------------------------+
#property strict
#property version   "1.510"
#property description "V11 Wave Candle research indicator. Attach to GOLD# H4."
#property description "Selectable FAST/STD/SLOW HA or raw H4 shell with completed-M5 settlement contour."
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

#include <Canvas\Canvas.mqh>

enum ENUM_V11_CANDLE_MODE
  {
   V11_CANDLE_FAST_HA = 0,
   V11_CANDLE_STD_HA  = 1,
   V11_CANDLE_SLOW_HA = 2,
   V11_CANDLE_RAW     = 3
  };

input group "V11 Wave Candle"
input ENUM_V11_CANDLE_MODE InpCandleMode = V11_CANDLE_FAST_HA;
input int   InpBarsToCache       = 1000; // Recent H4 slots retained (1..5000)
input bool  InpIncludeFormingH4  = true; // Uses completed M5 only inside the forming H4
input bool  InpHideNativeCandles = true;

input group "Wave visibility"
input bool  InpShowWaveContour   = true;
input bool  InpShowCandleShell   = true;  // Selected candle wick plus open/close ticks
input bool  InpShowOHCLLines     = true;  // Selected candle Open/High/Close/Low levels
input int   InpContourSteps      = 48;    // Screen-space KDE contour (24..96)

input group "Colors"
input color InpBullColor         = clrDeepSkyBlue;
input color InpBearColor         = clrOrange;
input color InpOHCLColor         = clrWhite;
input color InpFormingColor      = clrKhaki;

string   PREFIX="V11WC_";
string   LEGACY_PREFIX="V11WC_";
string   PREVIOUS_PREFIX="V11WC03_";
datetime g_last_closed_m5=0;
int      g_last_rates_total=0;
int      g_wave_slots=0;
int      g_m5_closes=0;
int      g_cached_slots=0;
int      g_cached_m5_closes=0;
int      g_canvas_width=0;
int      g_canvas_height=0;
int      g_chart_x_origin=0;
int      g_chart_y_origin=0;
bool     g_canvas_ready=false;
bool     g_rebuilding=false;
CCanvas  g_canvas;
bool     g_chart_saved=false;
long     g_old_chart_up=0;
long     g_old_chart_down=0;
long     g_old_candle_bull=0;
long     g_old_candle_bear=0;
long     g_old_chart_line=0;

struct WaveCacheBar
  {
   datetime time;
   double   raw_high;
   double   raw_low;
   double   candle_open;
   double   candle_high;
   double   candle_low;
   double   candle_close;
   double   efficiency;
   double   settlement;
   int      m5_count;
   bool     forming;
   bool     ready;
  };

WaveCacheBar g_wave_cache[];
double       g_density_cache[];
int          g_cache_steps=0;
bool         g_cache_ready=false;

// V10 HA formulas:
// FAST: HC=(O+H+L+2C)/5, HO_t=.25*HO_(t-1)+.75*HC_(t-1)
// STD : HC=(O+H+L+C)/4,  HO_t=.50*HO_(t-1)+.50*HC_(t-1)
// SLOW: HC=(O+H+L+2C)/5, HO_t=.75*HO_(t-1)+.25*HC_(t-1)

void SaveAndApplyChartStyle()
  {
   if(g_chart_saved)
      return;
   g_old_chart_up=ChartGetInteger(0,CHART_COLOR_CHART_UP);
   g_old_chart_down=ChartGetInteger(0,CHART_COLOR_CHART_DOWN);
   g_old_candle_bull=ChartGetInteger(0,CHART_COLOR_CANDLE_BULL);
   g_old_candle_bear=ChartGetInteger(0,CHART_COLOR_CANDLE_BEAR);
   g_old_chart_line=ChartGetInteger(0,CHART_COLOR_CHART_LINE);
   g_chart_saved=true;

   if(!InpHideNativeCandles)
      return;
   color background=(color)ChartGetInteger(0,CHART_COLOR_BACKGROUND);
   ChartSetInteger(0,CHART_COLOR_CHART_UP,background);
   ChartSetInteger(0,CHART_COLOR_CHART_DOWN,background);
   ChartSetInteger(0,CHART_COLOR_CANDLE_BULL,background);
   ChartSetInteger(0,CHART_COLOR_CANDLE_BEAR,background);
   ChartSetInteger(0,CHART_COLOR_CHART_LINE,background);
  }

void RestoreChartStyle()
  {
   if(!g_chart_saved || !InpHideNativeCandles)
      return;
   ChartSetInteger(0,CHART_COLOR_CHART_UP,g_old_chart_up);
   ChartSetInteger(0,CHART_COLOR_CHART_DOWN,g_old_chart_down);
   ChartSetInteger(0,CHART_COLOR_CANDLE_BULL,g_old_candle_bull);
   ChartSetInteger(0,CHART_COLOR_CANDLE_BEAR,g_old_candle_bear);
   ChartSetInteger(0,CHART_COLOR_CHART_LINE,g_old_chart_line);
  }

string CandleModeName()
  {
   if(InpCandleMode==V11_CANDLE_FAST_HA) return "FAST HA";
   if(InpCandleMode==V11_CANDLE_STD_HA)  return "STD HA";
   if(InpCandleMode==V11_CANDLE_SLOW_HA) return "SLOW HA";
   return "RAW OHLC";
  }

void HAFormulaParams(double &close_weight,double &open_alpha)
  {
   if(InpCandleMode==V11_CANDLE_FAST_HA)
     {
      close_weight=2.0;
      open_alpha=0.25;
     }
   else if(InpCandleMode==V11_CANDLE_STD_HA)
     {
      close_weight=1.0;
      open_alpha=0.50;
     }
   else
     {
      close_weight=2.0;
      open_alpha=0.75;
     }
  }

bool EnsureCanvas()
  {
   int width=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS,0);
   int height=(int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS,0);
   if(width<=0 || height<=0)
      return false;

   if(g_canvas_ready)
     {
      if(width==g_canvas_width && height==g_canvas_height)
         return true;
      if(g_canvas.Resize(width,height))
        {
         g_canvas_width=width;
         g_canvas_height=height;
         return true;
        }
      g_canvas.Destroy();
      g_canvas_ready=false;
     }

   string canvas_name=PREFIX+"canvas";
   if(!g_canvas.CreateBitmapLabel(0,0,canvas_name,0,0,width,height,
                                  COLOR_FORMAT_ARGB_NORMALIZE))
      return false;
   g_canvas_ready=true;
   g_canvas_width=width;
   g_canvas_height=height;
   ObjectSetInteger(0,canvas_name,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,canvas_name,OBJPROP_ANCHOR,ANCHOR_LEFT_UPPER);
   ObjectSetInteger(0,canvas_name,OBJPROP_BACK,false);
   ObjectSetInteger(0,canvas_name,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,canvas_name,OBJPROP_SELECTED,false);
   ObjectSetInteger(0,canvas_name,OBJPROP_HIDDEN,true);
   ObjectSetInteger(0,canvas_name,OBJPROP_ZORDER,0);
   return true;
  }

bool BuildWaveCache()
  {
   g_cache_ready=false;
   g_cached_slots=0;
   g_cached_m5_closes=0;
   if(_Period!=PERIOD_H4)
      return false;

   int total=Bars(_Symbol,PERIOD_H4);
   if(total<3)
      return false;
   MqlRates h4[];
   int copied=CopyRates(_Symbol,PERIOD_H4,0,total,h4);
   if(copied<3)
      return false;
   ArraySetAsSeries(h4,false);

   // HA state is calculated chronologically over all available H4 history so
   // the cached window does not create a synthetic HA restart boundary.
   double candle_open[],candle_high[],candle_low[],candle_close[];
   ArrayResize(candle_open,copied);
   ArrayResize(candle_high,copied);
   ArrayResize(candle_low,copied);
   ArrayResize(candle_close,copied);
   double close_weight=2.0;
   double open_alpha=0.25;
   HAFormulaParams(close_weight,open_alpha);
   for(int i=0;i<copied;i++)
     {
      if(InpCandleMode==V11_CANDLE_RAW)
        {
         candle_open[i]=h4[i].open;
         candle_high[i]=h4[i].high;
         candle_low[i]=h4[i].low;
         candle_close[i]=h4[i].close;
        }
      else
        {
         candle_close[i]=(h4[i].open+h4[i].high+h4[i].low+
                          close_weight*h4[i].close)/(3.0+close_weight);
         if(i==0)
            candle_open[i]=0.5*(h4[i].open+h4[i].close);
         else
            candle_open[i]=open_alpha*candle_open[i-1]+
                           (1.0-open_alpha)*candle_close[i-1];
         candle_high[i]=MathMax(h4[i].high,MathMax(candle_open[i],candle_close[i]));
         candle_low[i]=MathMin(h4[i].low,MathMin(candle_open[i],candle_close[i]));
        }
     }

   int bars_to_cache=(int)MathMax(1,MathMin(5000,InpBarsToCache));
   int first=MathMax(0,copied-bars_to_cache);
   int cache_count=copied-first;
   g_cache_steps=(int)MathMax(24,MathMin(96,InpContourSteps));
   ArrayResize(g_wave_cache,cache_count);
   ArrayResize(g_density_cache,cache_count*(g_cache_steps+1));
   ArrayInitialize(g_density_cache,0.0);

   // One chronological M5 read supplies the entire retained history. Screen
   // movement never executes this read or recalculates the KDE.
   MqlRates m5[];
   int m5_copied=CopyRates(_Symbol,PERIOD_M5,h4[first].time,TimeCurrent(),m5);
   if(m5_copied<=0)
      return false;
   ArraySetAsSeries(m5,false);
   datetime now=TimeCurrent();
   datetime current_h4=iTime(_Symbol,PERIOD_H4,0);
   int cursor=0;

   for(int cache_index=0;cache_index<cache_count;cache_index++)
     {
      int i=first+cache_index;
      WaveCacheBar bar;
      bar.time=h4[i].time;
      bar.raw_high=h4[i].high;
      bar.raw_low=h4[i].low;
      bar.candle_open=candle_open[i];
      bar.candle_high=candle_high[i];
      bar.candle_low=candle_low[i];
      bar.candle_close=candle_close[i];
      bar.efficiency=0.0;
      bar.settlement=0.0;
      bar.m5_count=0;
      bar.forming=(h4[i].time==current_h4);
      bar.ready=false;

      datetime slot_end=h4[i].time+PeriodSeconds(PERIOD_H4);
      while(cursor<m5_copied && m5[cursor].time<h4[i].time)
         cursor++;
      int begin=cursor;
      while(cursor<m5_copied && m5[cursor].time<slot_end &&
            m5[cursor].time+PeriodSeconds(PERIOD_M5)<=now)
         cursor++;
      int finish=cursor;
      int n=finish-begin;
      if(n<=0)
        {
         g_wave_cache[cache_index]=bar;
         continue;
        }

      int direction=(bar.candle_close>=bar.candle_open ? 1 : -1);
      double path_distance=0.0;
      double previous=bar.candle_open;
      double mean=0.0;
      int favorable_settles=0;
      for(int j=begin;j<finish;j++)
        {
         double settle=m5[j].close;
         path_distance+=MathAbs(settle-previous);
         if(direction*(settle-bar.candle_open)>=0.0)
            favorable_settles++;
         previous=settle;
         mean+=settle;
        }
      mean/=(double)n;
      double variance=0.0;
      for(int j=begin;j<finish;j++)
         variance+=(m5[j].close-mean)*(m5[j].close-mean);
      variance/=(double)n;

      bar.efficiency=(path_distance>0.0 ?
                      MathAbs(m5[finish-1].close-bar.candle_open)/path_distance : 0.0);
      bar.efficiency=MathMax(0.0,MathMin(1.0,bar.efficiency));
      bar.settlement=(double)favorable_settles/(double)n;
      bar.m5_count=n;
      double span=bar.raw_high-bar.raw_low;
      if(span>0.0)
        {
         double standard_deviation=MathSqrt(variance);
         double bandwidth=MathMax(span/48.0,
                                  MathMax(standard_deviation*0.10,2.0*_Point));
         double max_density=0.0;
         int density_offset=cache_index*(g_cache_steps+1);
         for(int level=0;level<=g_cache_steps;level++)
           {
            double price=bar.raw_low+span*(double)level/(double)g_cache_steps;
            double density=0.0;
            for(int j=begin;j<finish;j++)
              {
               double z=(price-m5[j].close)/bandwidth;
               density+=MathExp(-0.5*z*z);
              }
            density/=(double)n;
            g_density_cache[density_offset+level]=density;
            max_density=MathMax(max_density,density);
           }
         if(max_density>0.0)
           {
            for(int level=0;level<=g_cache_steps;level++)
               g_density_cache[density_offset+level]=
                  MathPow(MathMax(0.0,g_density_cache[density_offset+level]/max_density),1.35);
            bar.ready=true;
           }
        }
      g_wave_cache[cache_index]=bar;
      if(bar.ready)
        {
         g_cached_slots++;
         g_cached_m5_closes+=n;
        }
     }
   g_cache_ready=true;
   PrintFormat("V11 v0.5.1 %s numeric cache built: slots=%d M5=%d retained=%d",
               CandleModeName(),g_cached_slots,g_cached_m5_closes,cache_count);
   return true;
  }

bool DrawCachedWaveSlot(const int cache_index)
  {
   WaveCacheBar bar=g_wave_cache[cache_index];
   if(!bar.ready || (bar.forming && !InpIncludeFormingH4))
      return false;

   int h4_seconds=PeriodSeconds(PERIOD_H4);
   datetime center=bar.time+h4_seconds/2;
   double reference_price=0.5*(bar.raw_high+bar.raw_low);
   int center_x=0,next_x=0,ignored_y=0;
   if(!ChartTimePriceToXY(0,0,center,reference_price,center_x,ignored_y) ||
      !ChartTimePriceToXY(0,0,center+h4_seconds,reference_price,next_x,ignored_y))
      return false;
   center_x-=g_chart_x_origin;
   next_x-=g_chart_x_origin;
   int slot_pixels=MathMax(12,(int)MathAbs(next_x-center_x));
   if(center_x+slot_pixels<0 || center_x-slot_pixels>g_canvas_width)
      return false;

   int direction=(bar.candle_close>=bar.candle_open ? 1 : -1);
   color base=(direction>0 ? InpBullColor : InpBearColor);
   color shell_border=(bar.forming ? InpFormingColor : base);
   int max_half_pixels=(int)MathMax(6.0,0.46*(double)slot_pixels*
                                    (0.72+0.28*bar.efficiency));

   if(InpShowWaveContour && bar.raw_high>bar.raw_low)
     {
      int point_count=2*(g_cache_steps+1);
      int contour_x[],contour_y[];
      ArrayResize(contour_x,point_count);
      ArrayResize(contour_y,point_count);
      bool mapped=true;
      double span=bar.raw_high-bar.raw_low;
      int density_offset=cache_index*(g_cache_steps+1);
      for(int level=0;level<=g_cache_steps;level++)
        {
         double price=bar.raw_low+span*(double)level/(double)g_cache_steps;
         int py=0,ignored_x=0;
         if(!ChartTimePriceToXY(0,0,center,price,ignored_x,py))
           {
            mapped=false;
            break;
           }
         py-=g_chart_y_origin;
         int half=(int)MathMax(1.0,g_density_cache[density_offset+level]*
                                    (double)max_half_pixels);
         contour_x[level]=center_x-half;
         contour_y[level]=py;
         int mirror=point_count-1-level;
         contour_x[mirror]=center_x+half;
         contour_y[mirror]=py;
        }
      if(mapped)
        {
         uchar fill_alpha=(uchar)MathRound(78.0+82.0*bar.settlement);
         g_canvas.FillPolygon(contour_x,contour_y,ColorToARGB(base,fill_alpha));
         g_canvas.PolygonAA(contour_x,contour_y,ColorToARGB(shell_border,235));
        }
     }

   if(InpShowCandleShell)
     {
      int wick_top=0,wick_bottom=0,open_y=0,close_y=0,ignored_x=0;
      if(ChartTimePriceToXY(0,0,center,bar.candle_high,ignored_x,wick_top) &&
         ChartTimePriceToXY(0,0,center,bar.candle_low,ignored_x,wick_bottom) &&
         ChartTimePriceToXY(0,0,center,bar.candle_open,ignored_x,open_y) &&
         ChartTimePriceToXY(0,0,center,bar.candle_close,ignored_x,close_y))
        {
         wick_top-=g_chart_y_origin;
         wick_bottom-=g_chart_y_origin;
         open_y-=g_chart_y_origin;
         close_y-=g_chart_y_origin;
         uint shell_color=ColorToARGB(shell_border,255);
         int tick=(int)MathMax(3.0,0.23*(double)slot_pixels);
         g_canvas.LineAA(center_x,wick_top,center_x,wick_bottom,shell_color);
         g_canvas.LineAA(center_x-tick,open_y,center_x,open_y,shell_color);
         g_canvas.LineAA(center_x,close_y,center_x+tick,close_y,shell_color);
        }
     }

   if(InpShowOHCLLines)
     {
      double levels[4]={bar.candle_open,bar.candle_high,
                        bar.candle_close,bar.candle_low};
      int level_half=(int)MathMax(4.0,0.38*(double)slot_pixels);
      uint level_color=ColorToARGB(InpOHCLColor,205);
      for(int level=0;level<4;level++)
        {
         int line_x=0,line_y=0;
         if(ChartTimePriceToXY(0,0,center,levels[level],line_x,line_y))
           {
            line_y-=g_chart_y_origin;
            g_canvas.LineAA(center_x-level_half,line_y,
                            center_x+level_half,line_y,level_color);
           }
        }
     }
   g_wave_slots++;
   g_m5_closes+=bar.m5_count;
   return true;
  }

bool RenderWaveCandles()
  {
   if(g_rebuilding)
      return false;
   g_rebuilding=true;
   g_wave_slots=0;
   g_m5_closes=0;
   if(_Period!=PERIOD_H4)
     {
      Comment("V11 Wave Candle: attach to an H4 chart. No trade authority.");
      g_rebuilding=false;
      return false;
     }
   if(!g_cache_ready || !EnsureCanvas())
     {
      Comment("V11 Wave Candle: cache/canvas unavailable. Error="+(string)GetLastError());
      g_rebuilding=false;
      return false;
     }
   Comment("");

   // Reproject cached values to the current chart coordinates. The canvas
   // object stays alive; only its in-memory pixels are replaced atomically.
   int first_visible=(int)ChartGetInteger(0,CHART_FIRST_VISIBLE_BAR,0);
   datetime first_time=iTime(_Symbol,PERIOD_H4,first_visible)+PeriodSeconds(PERIOD_H4)/2;
   datetime current_center=iTime(_Symbol,PERIOD_H4,0)+PeriodSeconds(PERIOD_H4)/2;
   double price_max=ChartGetDouble(0,CHART_PRICE_MAX,0);
   double price_mid=0.5*(price_max+ChartGetDouble(0,CHART_PRICE_MIN,0));
   int ignored=0;
   g_chart_x_origin=0;
   g_chart_y_origin=0;
   ChartTimePriceToXY(0,0,first_time,price_mid,g_chart_x_origin,ignored);
   ChartTimePriceToXY(0,0,current_center,price_max,ignored,g_chart_y_origin);

   g_canvas.Erase(ColorToARGB(clrNONE,0));
   int cache_count=ArraySize(g_wave_cache);
   for(int i=0;i<cache_count;i++)
      DrawCachedWaveSlot(i);
   g_canvas.Update(false);
   ChartRedraw();
   g_rebuilding=false;
   return true;
  }

bool RebuildWaveCandles()
  {
   if(!BuildWaveCache())
      return false;
   return RenderWaveCandles();
  }

int OnInit()
  {
   PREFIX="V11WC05_"+(string)ChartID()+"_";
   LEGACY_PREFIX="V11WC_"+(string)ChartID()+"_";
   PREVIOUS_PREFIX="V11WC03_"+(string)ChartID()+"_";
   ObjectsDeleteAll(0,LEGACY_PREFIX);
   ObjectsDeleteAll(0,PREVIOUS_PREFIX);
   IndicatorSetString(INDICATOR_SHORTNAME,
                      "V11 Wave Candle v0.5.1 ["+CandleModeName()+"]");
   SaveAndApplyChartStyle();
   g_last_closed_m5=iTime(_Symbol,PERIOD_M5,1);
   RebuildWaveCandles();
   g_last_rates_total=Bars(_Symbol,PERIOD_H4);
   EventSetTimer(2);
   Print("V11 Wave Candle v0.5.1 initialized: "+CandleModeName()+
         " cached canvas KDE.");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   if(g_canvas_ready)
     {
      g_canvas.Destroy();
      g_canvas_ready=false;
     }
   ObjectsDeleteAll(0,PREFIX);
   RestoreChartStyle();
   Comment("");
   ChartRedraw();
  }

void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
  {
   if(id==CHARTEVENT_CHART_CHANGE)
      RenderWaveCandles();
  }

void OnTimer()
  {
   // Keep stale object renderers off the chart until duplicate old indicator
   // instances are removed by the user.
   int deleted=ObjectsDeleteAll(0,LEGACY_PREFIX);
   deleted+=ObjectsDeleteAll(0,PREVIOUS_PREFIX);
   if(deleted>0)
      ChartRedraw();
  }

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
  {
   datetime last_closed_m5=iTime(_Symbol,PERIOD_M5,1);
   if(prev_calculated==0 || !g_cache_ready ||
      last_closed_m5!=g_last_closed_m5 || rates_total!=g_last_rates_total)
     {
      g_last_closed_m5=last_closed_m5;
      g_last_rates_total=rates_total;
      RebuildWaveCandles();
     }
   return rates_total;
  }
//+------------------------------------------------------------------+
