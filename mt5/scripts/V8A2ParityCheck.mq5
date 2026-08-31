//+------------------------------------------------------------------+
//| V8A2ParityCheck.mq5                                              |
//| Reference generated from audited Python survival model pack      |
//+------------------------------------------------------------------+
#property strict
#property script_show_inputs

input string InpIndicatorName = "V8MovementProbabilityA2ReliabilityIndicator";
input double InpToleranceProbabilityPct = 1e-5;
input double InpToleranceRankPct = 1e-6;

#define NREF 18

string REF_SOURCE[NREF] =
{
   "2024.01.03 02:05",
   "2024.03.14 14:40",
   "2024.05.28 08:30",
   "2024.08.07 12:50",
   "2024.10.17 11:20",
   "2024.12.31 19:50",
   "2025.01.03 09:00",
   "2025.03.17 03:10",
   "2025.05.28 19:35",
   "2025.08.07 17:55",
   "2025.10.17 14:30",
   "2025.12.31 19:40",
   "2026.01.05 09:25",
   "2026.02.19 16:00",
   "2026.04.09 06:10",
   "2026.05.25 18:35",
   "2026.07.10 23:50",
   "2026.08.28 23:45"
};
double REF_P15[NREF] = {
   0.0103342571472027,
   4.60883972616022,
   0.462070198644476,
   0.223847444691307,
   0.0575201982979872,
   0.0214415552451149,
   0.433157817139011,
   0.532096477332684,
   1.08016625621209,
   3.54397148776442,
   88.8599818523668,
   15.7399387647977,
   12.2317141574458,
   32.9659247153426,
   17.3993617115677,
   5.33087974452187,
   3.11352724436423,
   11.6923468587545
};
double REF_P30[NREF] = {
   0.0382597301117878,
   15.9321572008015,
   1.27054885301896,
   1.39112067856139,
   0.601142520200256,
   0.379070296754434,
   1.30901090419304,
   6.04006780085791,
   3.85352057521502,
   17.8661523703621,
   98.2556732538481,
   39.4179382936278,
   28.3375778527775,
   67.8028256263146,
   38.8774488393828,
   12.7008450776021,
   10.2474554568276,
   22.9277509087641
};
double REF_P60[NREF] = {
   0.228959880313891,
   37.2416938238765,
   4.95614637257071,
   5.82292923881023,
   2.27148367938634,
   1.83692649198229,
   5.54574826718794,
   15.0345508980068,
   8.53761046788612,
   34.2201479588542,
   99.9761697852018,
   77.3528918950758,
   52.2121516566095,
   89.3966660732591,
   67.6207025345622,
   37.9366409957878,
   19.2219063504107,
   40.0108998434199
};
double REF_R15[NREF] = {
   11.4583333333333,
   97.5694444444444,
   81.5972222222222,
   43.4027777777778,
   43.4027777777778,
   25.6944444444444,
   77.7777777777778,
   67.7083333333333,
   54.5138888888889,
   87.8472222222222,
   88.1944444444444,
   23.9583333333333,
   36.1111111111111,
   82.6388888888889,
   5.20833333333333,
   50.6944444444444,
   35.7638888888889,
   51.7361111111111
};
double REF_R30[NREF] = {
   7.29166666666667,
   98.2638888888889,
   70.4861111111111,
   15.9722222222222,
   35.7638888888889,
   31.25,
   66.6666666666667,
   84.0277777777778,
   45.8333333333333,
   92.7083333333333,
   85.0694444444444,
   21.875,
   37.1527777777778,
   90.625,
   4.86111111111111,
   38.5416666666667,
   35.4166666666667,
   39.9305555555556
};
double REF_R60[NREF] = {
   7.63888888888889,
   98.9583333333333,
   70.4861111111111,
   21.1805555555556,
   42.7083333333333,
   40.9722222222222,
   67.0138888888889,
   79.1666666666667,
   33.6805555555556,
   90.2777777777778,
   86.1111111111111,
   21.1805555555556,
   37.5,
   89.2361111111111,
   4.51388888888889,
   51.0416666666667,
   16.6666666666667,
   28.125
};
double REF_RC[NREF] = {
   7.29166666666667,
   97.5694444444444,
   70.4861111111111,
   15.9722222222222,
   35.7638888888889,
   25.6944444444444,
   66.6666666666667,
   67.7083333333333,
   33.6805555555556,
   87.8472222222222,
   85.0694444444444,
   21.1805555555556,
   36.1111111111111,
   82.6388888888889,
   4.51388888888889,
   38.5416666666667,
   16.6666666666667,
   28.125
};

bool ReadOne(const int handle,const int buffer,const int shift,double &v)
{
   double a[1];
   if(CopyBuffer(handle,buffer,shift,1,a)!=1) return false;
   v=a[0];
   return true;
}

void OnStart()
{
   if(_Period!=PERIOD_M5)
      Print("V8-A2 parity: running on non-M5 chart is okay; indicator handle is explicitly M5.");
   int h=iCustom(_Symbol,PERIOD_M5,InpIndicatorName);
   if(h==INVALID_HANDLE)
   {
      Print("V8-A2 parity FAIL: cannot create indicator handle for ",InpIndicatorName," err=",GetLastError());
      return;
   }
   for(int k=0;k<30 && BarsCalculated(h)<=0;k++) Sleep(250);
   if(BarsCalculated(h)<=0)
   {
      Print("V8-A2 parity FAIL: indicator did not calculate. err=",GetLastError());
      IndicatorRelease(h);
      return;
   }

   double maxp=0.0,maxr=0.0;
   int checked=0,failed=0;
   for(int i=0;i<NREF;i++)
   {
      datetime st=StringToTime(REF_SOURCE[i]);
      int shift=iBarShift(_Symbol,PERIOD_M5,st,true);
      if(shift<0)
      {
         Print("MISS ",REF_SOURCE[i]," no exact M5 bar");
         failed++;
         continue;
      }
      double got[7];
      bool ok=true;
      for(int b=0;b<7;b++)
         if(!ReadOne(h,b,shift,got[b])) { ok=false; break; }
      if(!ok)
      {
         Print("MISS ",REF_SOURCE[i]," CopyBuffer failed err=",GetLastError());
         failed++;
         continue;
      }
      double ep=MathMax(MathAbs(got[0]-REF_P15[i]),MathMax(MathAbs(got[1]-REF_P30[i]),MathAbs(got[2]-REF_P60[i])));
      double er=MathMax(MathAbs(got[3]-REF_R15[i]),MathMax(MathAbs(got[4]-REF_R30[i]),MathMax(MathAbs(got[5]-REF_R60[i]),MathAbs(got[6]-REF_RC[i]))));
      if(ep>maxp) maxp=ep;
      if(er>maxr) maxr=er;
      checked++;
      if(ep>InpToleranceProbabilityPct || er>InpToleranceRankPct)
      {
         failed++;
         Print("DIFF ",REF_SOURCE[i]," pErr=",DoubleToString(ep,10)," rErr=",DoubleToString(er,10),
               " gotP=",DoubleToString(got[0],8),"/",DoubleToString(got[1],8),"/",DoubleToString(got[2],8),
               " gotR=",DoubleToString(got[3],8),"/",DoubleToString(got[4],8),"/",DoubleToString(got[5],8));
      }
   }
   Print("V8-A2 PARITY checked=",checked," failed=",failed,
         " maxProbPctDiff=",DoubleToString(maxp,12),
         " maxRankPctDiff=",DoubleToString(maxr,12));
   if(failed==0) Print("V8-A2 PARITY PASS");
   else Print("V8-A2 PARITY FAIL");
   IndicatorRelease(h);
}
//+------------------------------------------------------------------+
