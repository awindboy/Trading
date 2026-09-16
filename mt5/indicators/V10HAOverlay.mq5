//+------------------------------------------------------------------+
//| V10HAOverlay.mq5                                                 |
//| V10 FAST / STD / SLOW Heikin-Ashi overlay                        |
//| Research visualization only                                      |
//+------------------------------------------------------------------+
#property strict
#property version   "1.000"
#property description "V10 FAST/STD/SLOW Heikin-Ashi overlay. Use on H4 for current V10 research semantics."
#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1

#property indicator_label1  "V10 HA"
#property indicator_type1   DRAW_COLOR_CANDLES
#property indicator_color1  clrDodgerBlue,clrTomato
#property indicator_width1  1

// V10 formulas:
// FAST: HC=(O+H+L+2C)/5, HO_t=.25*HO_(t-1)+.75*HC_(t-1)
// STD : HC=(O+H+L+C)/4,  HO_t=.50*HO_(t-1)+.50*HC_(t-1)
// SLOW: HC=(O+H+L+2C)/5, HO_t=.75*HO_(t-1)+.25*HC_(t-1)
enum ENUM_V10_HA_MODE
  {
   V10_HA_FAST = 0,
   V10_HA_STD  = 1,
   V10_HA_SLOW = 2
  };

input group "V10 HA"
input ENUM_V10_HA_MODE InpHAMode = V10_HA_FAST;
input int               InpMaxDrawBars = 10000; // 0 = all available bars

input group "Display"
input color InpBullColor = clrDodgerBlue;
input color InpBearColor = clrTomato;
input int   InpCandleWidth = 1;

//--- DRAW_COLOR_CANDLES buffers: O/H/L/C/color-index
double HAOpenBuffer[];
double HAHighBuffer[];
double HALowBuffer[];
double HACloseBuffer[];
double HAColorBuffer[];

string ModeName()
  {
   if(InpHAMode==V10_HA_FAST) return "FAST w2/a0.25";
   if(InpHAMode==V10_HA_STD)  return "STD w1/a0.50";
   return "SLOW w2/a0.75";
  }

void FormulaParams(double &w,double &alpha)
  {
   if(InpHAMode==V10_HA_FAST)
     {
      w=2.0;
      alpha=0.25;
     }
   else if(InpHAMode==V10_HA_STD)
     {
      w=1.0;
      alpha=0.50;
     }
   else
     {
      w=2.0;
      alpha=0.75;
     }
  }

int OnInit()
  {
   SetIndexBuffer(0,HAOpenBuffer,INDICATOR_DATA);
   SetIndexBuffer(1,HAHighBuffer,INDICATOR_DATA);
   SetIndexBuffer(2,HALowBuffer,INDICATOR_DATA);
   SetIndexBuffer(3,HACloseBuffer,INDICATOR_DATA);
   SetIndexBuffer(4,HAColorBuffer,INDICATOR_COLOR_INDEX);

   ArraySetAsSeries(HAOpenBuffer,false);
   ArraySetAsSeries(HAHighBuffer,false);
   ArraySetAsSeries(HALowBuffer,false);
   ArraySetAsSeries(HACloseBuffer,false);
   ArraySetAsSeries(HAColorBuffer,false);

   PlotIndexSetInteger(0,PLOT_COLOR_INDEXES,2);
   PlotIndexSetInteger(0,PLOT_LINE_COLOR,0,InpBullColor);
   PlotIndexSetInteger(0,PLOT_LINE_COLOR,1,InpBearColor);
   PlotIndexSetInteger(0,PLOT_LINE_WIDTH,InpCandleWidth);
   PlotIndexSetDouble(0,PLOT_EMPTY_VALUE,EMPTY_VALUE);
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,1);

   IndicatorSetString(INDICATOR_SHORTNAME,"V10 HA Overlay - "+ModeName());
   IndicatorSetInteger(INDICATOR_DIGITS,_Digits);
   return(INIT_SUCCEEDED);
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
   if(rates_total<2)
      return 0;

   MqlRates rates[];
   int copied=CopyRates(_Symbol,_Period,0,rates_total,rates);
   if(copied<2)
      return prev_calculated;

   ArraySetAsSeries(rates,false);

   double w=2.0,alpha=0.25;
   FormulaParams(w,alpha);

   int first_draw=0;
   if(InpMaxDrawBars>0 && copied>InpMaxDrawBars)
      first_draw=copied-InpMaxDrawBars;

   // Clear any buffer area that is older than the requested visible range.
   for(int i=0;i<first_draw && i<rates_total;i++)
     {
      HAOpenBuffer[i]=EMPTY_VALUE;
      HAHighBuffer[i]=EMPTY_VALUE;
      HALowBuffer[i]=EMPTY_VALUE;
      HACloseBuffer[i]=EMPTY_VALUE;
      HAColorBuffer[i]=0.0;
     }

   double prev_ha_open=0.0;
   double prev_ha_close=0.0;

   // Recompute chronologically so the recursive HA open is deterministic.
   for(int i=0;i<copied;i++)
     {
      double hc=(rates[i].open+rates[i].high+rates[i].low+w*rates[i].close)/(3.0+w);
      double ho;
      if(i==0)
         ho=0.5*(rates[i].open+rates[i].close);
      else
         ho=alpha*prev_ha_open+(1.0-alpha)*prev_ha_close;

      double hh=MathMax(rates[i].high,MathMax(ho,hc));
      double hl=MathMin(rates[i].low, MathMin(ho,hc));

      if(i>=first_draw)
        {
         HAOpenBuffer[i]=ho;
         HAHighBuffer[i]=hh;
         HALowBuffer[i]=hl;
         HACloseBuffer[i]=hc;
         HAColorBuffer[i]=(hc>=ho ? 0.0 : 1.0);
        }

      prev_ha_open=ho;
      prev_ha_close=hc;
     }

   return rates_total;
  }
//+------------------------------------------------------------------+
