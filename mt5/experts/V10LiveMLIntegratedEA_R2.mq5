//+------------------------------------------------------------------+
//| V10LiveMLIntegratedEA_R2.mq5                                    |
//| Fully chart-native V10 research EA with embedded ML inference.   |
//|                                                                  |
//| No signal ledger. No future label. No Python runtime dependency. |
//| ML coefficients/preprocessing are embedded in                    |
//| V10LiveMLModelsR2.mqh.                                           |
//|                                                                  |
//| RESEARCH / TESTER / FORWARD-DEMO ONLY. NO PRODUCTION AUTHORITY.  |
//+------------------------------------------------------------------+
#property strict
#property version   "2.000"
#property description "V10 R2: chart-native H4 HA + embedded walk-forward ML + regime/neutral + prev-STD HA SL + money-risk sizing."

#include <Trade/Trade.mqh>
#include <V10LiveMLModelsR2.mqh>

#define V10R2_BUILD "V10_LIVE_ML_R2_20260917"
#define V10R2_H4_HISTORY 720
#define V10R2_LTF_HISTORY 720
#define V10R2_EPS 1e-12

enum V10RegimeMode
  {
   V10_REGIME_OFF=0,
   V10_REGIME_NEUTRAL_4H=1,
   V10_REGIME_NEUTRAL_12H=2
  };

enum V10ModelMode
  {
   V10_MODEL_AUTO=0,        // tester: causal walk-forward; live: latest model
   V10_MODEL_WALK_FORWARD=1,
   V10_MODEL_LATEST=2
  };

input group "Execution"
input long           InpMagicNumber            = 26101720;
input bool           InpExecuteTrades          = true;
input bool           InpRequireHedging         = true;
input int            InpDeviationPoints        = 30;

input group "Embedded ML"
input V10MLPolicy    InpPolicy                 = V10_POLICY_RUNWAY_PERSIST;
input V10ModelMode   InpModelMode              = V10_MODEL_AUTO;
input bool           InpUseK1ShockVeto         = true;

input group "Regime / reverse admission"
input V10RegimeMode  InpRegimeMode             = V10_REGIME_NEUTRAL_4H;

input group "Money risk"
input double         InpRiskUnitPctEquity       = 0.25;  // 1 risk unit = this % of current equity
input double         InpMidTierRiskUnits        = 1.0;
input double         InpTopTierRiskUnits        = 3.0;
input double         InpCampaignRiskCapUnits    = 8.0;
input bool           InpPartialRemainingBudget = true;

input group "Diagnostics"
input bool           InpWriteCsv               = true;
input bool           InpVerboseLog             = false;
input string         InpCsvFile                = "V10_LiveML_R2_events.csv";

CTrade g_trade;
datetime g_last_h4_open=0;
int      g_run_dir=0;
bool     g_run_admitted=false;
bool     g_exit_pending=false;
int      g_exit_old_dir=0;
int      g_csv=INVALID_HANDLE;
long     g_decisions=0;
long     g_entries=0;

//+------------------------------------------------------------------+
//| Utilities                                                        |
//+------------------------------------------------------------------+
void VLog(string s){ if(InpVerboseLog) Print("[V10R2] ",s); }

double BidNow(){ return SymbolInfoDouble(_Symbol,SYMBOL_BID); }
double AskNow(){ return SymbolInfoDouble(_Symbol,SYMBOL_ASK); }
double NormPrice(double p){ return NormalizeDouble(p,(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS)); }

string DirName(int d){ return d>0?"LONG":(d<0?"SHORT":"NONE"); }
string EraName(V10MLEra e)
  {
   if(e==V10_ERA_2023) return "2023";
   if(e==V10_ERA_2024) return "2024";
   if(e==V10_ERA_2025) return "2025";
   if(e==V10_ERA_2026) return "2026";
   return "FUTURE";
  }

void CsvHeader()
  {
   if(g_csv==INVALID_HANDLE) return;
   FileWrite(g_csv,"event_time","decision_time","event","dir","k","era","admitted","chop","confirm",
             "p_runway","p_win","p_persist","p_severe","p_stop","p_shock","score","q50","q75","shock_q95",
             "tier","stop","stop_dist_atr","campaign_units_before","desired_units","allocated_units","volume","note");
   FileFlush(g_csv);
  }

void CsvEvent(string event_name,datetime decision,int dir,int k,V10MLEra era,bool admitted,bool chop,bool confirm,
              double pr,double pw,double pp,double psev,double pst,double psh,double score,double q50,double q75,double sq95,
              int tier,double stop,double stopdist,double before,double desired,double allocated,double volume,string note)
  {
   if(g_csv==INVALID_HANDLE) return;
   FileWrite(g_csv,
      TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),
      decision==0?"":TimeToString(decision,TIME_DATE|TIME_SECONDS),event_name,DirName(dir),k,EraName(era),
      (int)admitted,(int)chop,(int)confirm,
      DoubleToString(pr,8),DoubleToString(pw,8),DoubleToString(pp,8),DoubleToString(psev,8),DoubleToString(pst,8),DoubleToString(psh,8),
      DoubleToString(score,10),DoubleToString(q50,10),DoubleToString(q75,10),DoubleToString(sq95,10),tier,
      stop==0?"":DoubleToString(stop,_Digits),DoubleToString(stopdist,8),DoubleToString(before,4),DoubleToString(desired,4),DoubleToString(allocated,4),DoubleToString(volume,4),note);
   FileFlush(g_csv);
  }

double Median(double &a[])
  {
   int n=ArraySize(a); if(n<=0) return 0.0;
   double b[]; ArrayResize(b,n);
   for(int i=0;i<n;i++) b[i]=a[i];
   ArraySort(b);
   if((n%2)==1) return b[n/2];
   return 0.5*(b[n/2-1]+b[n/2]);
  }

//+------------------------------------------------------------------+
//| HA / indicator reconstruction in chronological array order       |
//+------------------------------------------------------------------+
int BuildHA(ENUM_TIMEFRAMES tf,int want,double w,double alpha,
            MqlRates &r[],double &hao[],double &hac[],double &hah[],double &hal[],int &dir[])
  {
   ArrayResize(r,want); ArraySetAsSeries(r,false);
   int n=CopyRates(_Symbol,tf,0,want,r);
   if(n<=0) return 0;
   ArrayResize(r,n); ArrayResize(hao,n);ArrayResize(hac,n);ArrayResize(hah,n);ArrayResize(hal,n);ArrayResize(dir,n);
   for(int i=0;i<n;i++)
     {
      hac[i]=(r[i].open+r[i].high+r[i].low+w*r[i].close)/(3.0+w);
      if(i==0) hao[i]=0.5*(r[i].open+r[i].close);
      else     hao[i]=alpha*hao[i-1]+(1.0-alpha)*hac[i-1];
      hah[i]=MathMax(r[i].high,MathMax(hao[i],hac[i]));
      hal[i]=MathMin(r[i].low, MathMin(hao[i],hac[i]));
      dir[i]=(hac[i]>=hao[i]?1:-1);
     }
   return n;
  }

void CalcATR(const MqlRates &r[],int nbar,int period,double &out[])
  {
   int n=ArraySize(r); ArrayResize(out,n); ArrayInitialize(out,EMPTY_VALUE);
   if(n<=period) return;
   double tr[];ArrayResize(tr,n);
   tr[0]=r[0].high-r[0].low;
   for(int i=1;i<n;i++)
     tr[i]=MathMax(r[i].high-r[i].low,MathMax(MathAbs(r[i].high-r[i-1].close),MathAbs(r[i].low-r[i-1].close)));
   double a=0.0;for(int i=0;i<period;i++)a+=tr[i];a/=period;out[period-1]=a;
   for(int i=period;i<n;i++){a=(a*(period-1)+tr[i])/period;out[i]=a;}
  }

void CalcEMA(const MqlRates &r[],int period,double &out[])
  {
   int n=ArraySize(r);ArrayResize(out,n);if(n<=0)return;
   double a=2.0/(period+1.0);out[0]=r[0].close;
   for(int i=1;i<n;i++)out[i]=a*r[i].close+(1.0-a)*out[i-1];
  }

void CalcADX(const MqlRates &r[],int period,double &adx[],double &pdi[],double &mdi[])
  {
   int n=ArraySize(r);ArrayResize(adx,n);ArrayResize(pdi,n);ArrayResize(mdi,n);
   ArrayInitialize(adx,EMPTY_VALUE);ArrayInitialize(pdi,EMPTY_VALUE);ArrayInitialize(mdi,EMPTY_VALUE);
   if(n<=2*period+2)return;
   double tr[],pdm[],mdm[],atrS[],sp[],sm[],dx[];
   ArrayResize(tr,n);ArrayResize(pdm,n);ArrayResize(mdm,n);ArrayResize(atrS,n);ArrayResize(sp,n);ArrayResize(sm,n);ArrayResize(dx,n);
   ArrayInitialize(atrS,EMPTY_VALUE);ArrayInitialize(sp,EMPTY_VALUE);ArrayInitialize(sm,EMPTY_VALUE);ArrayInitialize(dx,EMPTY_VALUE);
   tr[0]=r[0].high-r[0].low;pdm[0]=0;mdm[0]=0;
   for(int i=1;i<n;i++)
     {
      tr[i]=MathMax(r[i].high-r[i].low,MathMax(MathAbs(r[i].high-r[i-1].close),MathAbs(r[i].low-r[i-1].close)));
      double up=r[i].high-r[i-1].high, dn=r[i-1].low-r[i].low;
      pdm[i]=(up>dn && up>0?up:0); mdm[i]=(dn>up && dn>0?dn:0);
     }
   double at=0,ps=0,ms=0;for(int i=1;i<=period;i++){at+=tr[i];ps+=pdm[i];ms+=mdm[i];}
   atrS[period]=at;sp[period]=ps;sm[period]=ms;
   for(int i=period+1;i<n;i++)
     { atrS[i]=atrS[i-1]-atrS[i-1]/period+tr[i]; sp[i]=sp[i-1]-sp[i-1]/period+pdm[i]; sm[i]=sm[i-1]-sm[i-1]/period+mdm[i]; }
   for(int i=period;i<n;i++)
     {
      if(atrS[i]<=0)continue;
      pdi[i]=100.0*sp[i]/atrS[i]; mdi[i]=100.0*sm[i]/atrS[i];
      double den=pdi[i]+mdi[i]; if(den>V10R2_EPS) dx[i]=100.0*MathAbs(pdi[i]-mdi[i])/den;
     }
   int start=2*period; double sum=0;int cnt=0;
   for(int i=period+1;i<=start;i++){if(dx[i]!=EMPTY_VALUE){sum+=dx[i];cnt++;}}
   if(cnt<=0)return; adx[start]=sum/cnt;
   for(int i=start+1;i<n;i++) if(dx[i]!=EMPTY_VALUE) adx[i]=(adx[i-1]*(period-1)+dx[i])/period;
  }

double PathEffAt(const MqlRates &r[],int idx,int w)
  {
   if(idx-w+1<0)return EMPTY_VALUE;
   double den=0;for(int i=idx-w+2;i<=idx;i++)den+=MathAbs(r[i].close-r[i-1].close);
   if(den<=V10R2_EPS)return 0.0;
   return MathAbs(r[idx].close-r[idx-w+1].close)/den;
  }

double PriorPathMedian(const MqlRates &r[],int idx,int w,int lookback)
  {
   double a[];ArrayResize(a,0);
   for(int j=idx-lookback;j<=idx-1;j++)
     {
      double v=PathEffAt(r,j,w);if(v==EMPTY_VALUE)continue;
      int n=ArraySize(a);ArrayResize(a,n+1);a[n]=v;
     }
   if(ArraySize(a)<30)return EMPTY_VALUE;return Median(a);
  }

double PriorMedian(const double &src[],int idx,int lookback)
  {
   double a[];ArrayResize(a,0);
   for(int j=idx-lookback;j<=idx-1;j++)
     if(j>=0 && src[j]!=EMPTY_VALUE && MathIsValidNumber(src[j])){int n=ArraySize(a);ArrayResize(a,n+1);a[n]=src[j];}
   if(ArraySize(a)<30)return EMPTY_VALUE;return Median(a);
  }

bool LTFCompact(ENUM_TIMEFRAMES tf,double w,double alpha,datetime h4open,datetime decision,double scale,int pdir,
                double &aligned,double &streak,double &body_sum_atr,double &body_rng,double &opp_wick)
  {
   MqlRates r[];double ho[],hc[],hh[],hl[];int hd[];
   int n=BuildHA(tf,V10R2_LTF_HISTORY,w,alpha,r,ho,hc,hh,hl,hd);if(n<20)return false;
   int ids[];ArrayResize(ids,0);
   for(int i=0;i<n;i++) if(r[i].time>=h4open && r[i].time<decision){int z=ArraySize(ids);ArrayResize(ids,z+1);ids[z]=i;}
   int m=ArraySize(ids);if(m<=0)return false;
   int ac=0;double bs=0,br=0,ow=0;
   for(int z=0;z<m;z++)
     {
      int i=ids[z];int sg=pdir*hd[i];if(sg>0)ac++;
      double body=pdir*(hc[i]-ho[i]);double range=MathMax(hh[i]-hl[i],V10R2_EPS);bs+=body;br+=body/range;
      double wick=(pdir>0?MathMax(0.0,MathMin(ho[i],hc[i])-hl[i]):MathMax(0.0,hh[i]-MathMax(ho[i],hc[i])));
      ow+=wick/range;
     }
   aligned=(double)ac/m;body_sum_atr=bs/MathMax(scale,V10R2_EPS);body_rng=br/m;opp_wick=ow/m;
   int last=ids[m-1];int lastsg=pdir*hd[last];int cur=0;
   for(int z=m-1;z>=0;z--){int sg=pdir*hd[ids[z]];if(sg==lastsg)cur++;else break;}
   streak=(lastsg>0?cur:-cur);
   return true;
  }

//+------------------------------------------------------------------+
//| Build exact live feature vector                                  |
//+------------------------------------------------------------------+
bool BuildFeatures(datetime decision,double &x[],int &pdir,int &run_k,double &stop,double &stop_dist_atr,
                   bool &chop,bool &confirm)
  {
   MqlRates r[];double fho[],fhc[],fhh[],fhl[];int fd[];
   int n=BuildHA(PERIOD_H4,V10R2_H4_HISTORY,2.0,0.25,r,fho,fhc,fhh,fhl,fd);if(n<250)return false;
   double sho[],shc[],shh[],shl[];int sd[];MqlRates dummy[];
   if(BuildHA(PERIOD_H4,V10R2_H4_HISTORY,1.0,0.50,dummy,sho,shc,shh,shl,sd)!=n)return false;
   double slo[],slc[],slh[],sll[];int sld[];MqlRates dummy2[];
   if(BuildHA(PERIOD_H4,V10R2_H4_HISTORY,2.0,0.75,dummy2,slo,slc,slh,sll,sld)!=n)return false;
   int idx=n-2; if(idx<200)return false; // n-1 is current forming H4
   if(r[n-1].time!=decision){VLog("H4 decision clock mismatch");return false;}
   pdir=fd[idx];run_k=1;for(int j=idx-1;j>=0 && fd[j]==pdir;j--)run_k++;
   stop=(pdir>0?shl[idx-1]:shh[idx-1]);
   double entry=BidNow(); // model feature uses chart/Bid price, matching OHLC training substrate
   if(entry<=0)return false;
   if((pdir>0 && stop>=entry)||(pdir<0 && stop<=entry))return false;

   double atr[];CalcATR(r,n,180,atr);double scale=atr[idx-1];if(scale==EMPTY_VALUE || !MathIsValidNumber(scale)||scale<=0)return false;
   stop_dist_atr=MathAbs(entry-stop)/scale;
   double adx14[],pdi14[],mdi14[],adx28[],pdi28[],mdi28[];CalcADX(r,14,adx14,pdi14,mdi14);CalcADX(r,28,adx28,pdi28,mdi28);
   double adxmed=PriorMedian(adx28,idx,180);if(adxmed==EMPTY_VALUE||adxmed<=0)return false;
   double pe4=PathEffAt(r,idx,4),pe12=PathEffAt(r,idx,12),pm4=PriorPathMedian(r,idx,4,180),pm12=PriorPathMedian(r,idx,12,180);
   if(pe4==EMPTY_VALUE||pe12==EMPTY_VALUE||pm4==EMPTY_VALUE||pm12==EMPTY_VALUE||pm4<=0||pm12<=0)return false;
   double e8[],e21[];CalcEMA(r,8,e8);CalcEMA(r,21,e21);
   double fr=0;int trans=0;for(int j=idx-6;j<=idx;j++)if(j>0 && fd[j]!=fd[j-1])trans++;fr=trans/7.0;

   ArrayResize(x,V10ML_FEATURES);ArrayInitialize(x,0.0);
   x[0]=run_k;
   x[1]=stop_dist_atr;
   x[2]=pdir*(fhc[idx]-fho[idx])/MathMax(fhh[idx]-fhl[idx],V10R2_EPS);
   x[3]=(sd[idx]==pdir?1.0:0.0);
   x[4]=pdir*(shc[idx]-sho[idx])/MathMax(shh[idx]-shl[idx],V10R2_EPS);
   x[5]=(sld[idx]==pdir?1.0:0.0);
   x[6]=adx28[idx]/adxmed;
   x[7]=pdir*(pdi14[idx]-mdi14[idx])/100.0;
   x[8]=pdir*(e8[idx]-e21[idx])/scale;
   x[9]=pe4/pm4;
   x[10]=pe12/pm12;
   x[11]=fr;

   double a,s,b,rng,ow;
   if(!LTFCompact(PERIOD_M15,2.0,0.25,r[idx].time,decision,scale,pdir,a,s,b,rng,ow))return false;
   x[12]=a;x[13]=s;x[14]=b;x[15]=rng;x[16]=ow;
   if(!LTFCompact(PERIOD_M30,2.0,0.25,r[idx].time,decision,scale,pdir,a,s,b,rng,ow))return false;
   x[17]=a;x[18]=s;x[19]=b;x[20]=rng;x[21]=ow;
   if(!LTFCompact(PERIOD_H1,1.0,0.50,r[idx].time,decision,scale,pdir,a,s,b,rng,ow))return false;
   x[22]=a;x[23]=s;x[24]=b;x[25]=rng;x[26]=ow;

   bool weak_adx=(x[6]<1.0);bool weak_eff=(InpRegimeMode==V10_REGIME_NEUTRAL_12H?x[10]<1.0:x[9]<1.0);
   chop=(InpRegimeMode!=V10_REGIME_OFF && weak_adx && weak_eff);
   confirm=(x[7]>0.0 || x[8]>0.0);
   return true;
  }

V10MLEra SelectEra(datetime decision)
  {
   if(InpModelMode==V10_MODEL_LATEST)return V10_ERA_FUTURE;
   if(InpModelMode==V10_MODEL_WALK_FORWARD)return V10MLEraForTime(decision);
   if((bool)MQLInfoInteger(MQL_TESTER))return V10MLEraForTime(decision);
   return V10_ERA_FUTURE;
  }

double PolicyScore(V10MLPolicy p,int k,double pr,double pw,double pp,double psev)
  {
   if(p==V10_POLICY_RUNWAY)return pr;
   double pers=(k>=2?pp:1.0);
   if(p==V10_POLICY_RUNWAY_PERSIST)return pr*pers;
   if(p==V10_POLICY_RUNWAY_WIN_PERSIST)return pr*pw*pers;
   return pr*(1.0-psev)*pers;
  }

//+------------------------------------------------------------------+
//| Exposure / risk                                                  |
//+------------------------------------------------------------------+
bool IsMagicPosition(ulong ticket)
  {
   if(ticket==0||!PositionSelectByTicket(ticket))return false;
   return PositionGetString(POSITION_SYMBOL)==_Symbol && (long)PositionGetInteger(POSITION_MAGIC)==InpMagicNumber;
  }

int PositionDir(ulong ticket)
  {
   if(!PositionSelectByTicket(ticket))return 0;
   return PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY?1:-1;
  }

double CommentUnits(string c)
  {
   int p=StringFind(c,"_U");if(p<0)return 0.0;
   return StringToDouble(StringSubstr(c,p+2));
  }

double CurrentCommittedUnits()
  {
   double s=0;
   for(int i=0;i<PositionsTotal();i++)
     {
      ulong t=PositionGetTicket(i);if(!IsMagicPosition(t))continue;
      s+=CommentUnits(PositionGetString(POSITION_COMMENT));
     }
   return s;
  }

bool HasDirection(int dir)
  {
   for(int i=0;i<PositionsTotal();i++){ulong t=PositionGetTicket(i);if(IsMagicPosition(t)&&PositionDir(t)==dir)return true;}
   return false;
  }

bool CloseDirection(int dir)
  {
   bool all=true;g_trade.SetExpertMagicNumber(InpMagicNumber);g_trade.SetDeviationInPoints(InpDeviationPoints);
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      ulong t=PositionGetTicket(i);if(!IsMagicPosition(t)||PositionDir(t)!=dir)continue;
      if(!g_trade.PositionClose(t,InpDeviationPoints)){all=false;VLog(StringFormat("close failed ticket=%I64u ret=%u %s",t,g_trade.ResultRetcode(),g_trade.ResultRetcodeDescription()));}
     }
   return all && !HasDirection(dir);
  }

void TryPendingExit()
  {
   if(!g_exit_pending)return;
   if(!HasDirection(g_exit_old_dir)){g_exit_pending=false;g_exit_old_dir=0;return;}
   if(CloseDirection(g_exit_old_dir)){g_exit_pending=false;g_exit_old_dir=0;}
  }

double NormalizeVolumeFloor(double v)
  {
   double mn=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN),mx=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX),st=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(st<=0)st=mn;if(v>mx)v=mx;double z=MathFloor((v+1e-12)/st)*st;
   int d=2;if(st<0.01)d=3;if(st<0.001)d=4;return NormalizeDouble(z,d);
  }

bool RiskVolume(int dir,double entry,double sl,double units,double &volume,double &actual_units)
  {
   double unitMoney=AccountInfoDouble(ACCOUNT_EQUITY)*InpRiskUnitPctEquity/100.0;if(unitMoney<=0||units<=0)return false;
   double one=0;ENUM_ORDER_TYPE typ=(dir>0?ORDER_TYPE_BUY:ORDER_TYPE_SELL);
   if(!OrderCalcProfit(typ,_Symbol,1.0,entry,sl,one)||MathAbs(one)<V10R2_EPS)return false;
   double raw=(unitMoney*units)/MathAbs(one);double mn=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   volume=NormalizeVolumeFloor(raw);if(volume+1e-12<mn)return false;
   actual_units=MathAbs(one)*volume/unitMoney;return actual_units>0;
  }

bool OpenChild(datetime decision,int dir,int k,int tier,double stop,double stopdist,double desired_units,double before,
               V10MLEra era,bool admitted,bool chop,bool confirm,double pr,double pw,double pp,double psev,double pst,double psh,double score,double q50,double q75,double sq95)
  {
   double remain=InpCampaignRiskCapUnits-before;if(remain<=V10R2_EPS){CsvEvent("RISK_CAP_SKIP",decision,dir,k,era,admitted,chop,confirm,pr,pw,pp,psev,pst,psh,score,q50,q75,sq95,tier,stop,stopdist,before,desired_units,0,0,"no remaining campaign budget");return false;}
   double alloc=desired_units;
   if(alloc>remain)
     {
      if(!InpPartialRemainingBudget){CsvEvent("RISK_CAP_SKIP",decision,dir,k,era,admitted,chop,confirm,pr,pw,pp,psev,pst,psh,score,q50,q75,sq95,tier,stop,stopdist,before,desired_units,0,0,"desired > remaining; skip mode");return false;}
      alloc=remain;
     }
   double entry=(dir>0?AskNow():BidNow()),vol=0,actual_units=0;
   if(entry<=0||!RiskVolume(dir,entry,stop,alloc,vol,actual_units)){CsvEvent("SIZE_SKIP",decision,dir,k,era,admitted,chop,confirm,pr,pw,pp,psev,pst,psh,score,q50,q75,sq95,tier,stop,stopdist,before,desired_units,alloc,0,"cannot honor risk with broker volume step");return false;}
   if(!InpExecuteTrades){CsvEvent("SHADOW_ENTRY",decision,dir,k,era,admitted,chop,confirm,pr,pw,pp,psev,pst,psh,score,q50,q75,sq95,tier,stop,stopdist,before,desired_units,actual_units,vol,"");return true;}
   g_trade.SetExpertMagicNumber(InpMagicNumber);g_trade.SetDeviationInPoints(InpDeviationPoints);
   string comment=StringFormat("V10R2_U%.3f",actual_units);
   bool ok=(dir>0?g_trade.Buy(vol,_Symbol,0,NormPrice(stop),0,comment):g_trade.Sell(vol,_Symbol,0,NormPrice(stop),0,comment));
   if(!ok){CsvEvent("ORDER_FAIL",decision,dir,k,era,admitted,chop,confirm,pr,pw,pp,psev,pst,psh,score,q50,q75,sq95,tier,stop,stopdist,before,desired_units,actual_units,vol,StringFormat("ret=%u %s",g_trade.ResultRetcode(),g_trade.ResultRetcodeDescription()));return false;}
   g_entries++;CsvEvent("ENTRY",decision,dir,k,era,admitted,chop,confirm,pr,pw,pp,psev,pst,psh,score,q50,q75,sq95,tier,stop,stopdist,before,desired_units,actual_units,vol,"");return true;
  }

//+------------------------------------------------------------------+
//| H4 decision                                                      |
//+------------------------------------------------------------------+
void ProcessDecision(datetime decision)
  {
   MqlDateTime dt;TimeToStruct(decision,dt);
   if(dt.year<2023 && SelectEra(decision)!=V10_ERA_FUTURE){VLog("walk-forward warmup: no trading before 2023");return;}
   double x[];int dir=0,k=0;double stop=0,stopdist=0;bool chop=false,confirm=false;
   if(!BuildFeatures(decision,x,dir,k,stop,stopdist,chop,confirm)){VLog("feature build failed");return;}
   g_decisions++;

   bool flip=(g_run_dir!=0 && dir!=g_run_dir);
   if(g_run_dir==0 || flip)
     {
      int old=g_run_dir;g_run_dir=dir;g_run_admitted=false;
      if(old!=0 && HasDirection(old)){g_exit_pending=true;g_exit_old_dir=old;TryPendingExit();}
     }
   if(g_exit_pending){VLog("new admission blocked while old campaign EXIT_PENDING");return;}

   if(!g_run_admitted)
     {
      if(InpRegimeMode==V10_REGIME_OFF || !chop || confirm)g_run_admitted=true;
     }

   V10MLEra era=SelectEra(decision);
   double pr=V10MLPredict(era,V10_HEAD_RUNWAY,x);
   double pw=V10MLPredict(era,V10_HEAD_WIN,x);
   double pp=V10MLPredict(era,V10_HEAD_PERSIST,x);
   double psev=V10MLPredict(era,V10_HEAD_SEVERE,x);
   double pst=V10MLPredict(era,V10_HEAD_STOP,x);
   double psh=V10MLPredict(era,V10_HEAD_SHOCK,x);
   double score=PolicyScore(InpPolicy,k,pr,pw,pp,psev);
   double q50=V10ML_Q50[(int)era][(int)InpPolicy],q75=V10ML_Q75[(int)era][(int)InpPolicy],sq95=V10ML_SHOCK_Q95[(int)era];
   int tier=(score<q50?0:(score<q75?1:3));
   if(InpUseK1ShockVeto && k==1 && psh>=sq95)tier=0;
   if(!g_run_admitted)tier=0;

   double before=CurrentCommittedUnits();double desired=(tier==3?InpTopTierRiskUnits:(tier==1?InpMidTierRiskUnits:0));
   CsvEvent("DECISION",decision,dir,k,era,g_run_admitted,chop,confirm,pr,pw,pp,psev,pst,psh,score,q50,q75,sq95,tier,stop,stopdist,before,desired,0,0,flip?"FAST flip":"");
   if(tier<=0)return;
   OpenChild(decision,dir,k,tier,stop,stopdist,desired,before,era,g_run_admitted,chop,confirm,pr,pw,pp,psev,pst,psh,score,q50,q75,sq95);
  }

//+------------------------------------------------------------------+
//| MT5 lifecycle                                                    |
//+------------------------------------------------------------------+
int OnInit()
  {
   if(InpRequireHedging && AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
     {Print("[V10R2] INIT FAILED: hedging account required for independent Child positions/SLs.");return INIT_FAILED;}
   if(InpRiskUnitPctEquity<=0 || InpCampaignRiskCapUnits<=0 || InpMidTierRiskUnits<=0 || InpTopTierRiskUnits<=0)
     {Print("[V10R2] INIT FAILED: invalid risk inputs.");return INIT_PARAMETERS_INCORRECT;}
   g_trade.SetExpertMagicNumber(InpMagicNumber);g_trade.SetDeviationInPoints(InpDeviationPoints);
   if(InpWriteCsv)
     {
      g_csv=FileOpen(InpCsvFile,FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_ANSI,',');
      if(g_csv!=INVALID_HANDLE)CsvHeader();else Print("[V10R2] warning: event CSV open failed; trading continues.");
     }
   g_last_h4_open=iTime(_Symbol,PERIOD_H4,0);
   Print("[V10R2] initialized. build=",V10R2_BUILD," model policy=",(int)InpPolicy," regime=",(int)InpRegimeMode,
         " signal source=LIVE CHART ONLY; embedded signal count=0");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_csv!=INVALID_HANDLE){FileFlush(g_csv);FileClose(g_csv);g_csv=INVALID_HANDLE;}
   Print("[V10R2] deinit decisions=",g_decisions," entries=",g_entries," reason=",reason);
  }

void OnTick()
  {
   if(g_exit_pending){TryPendingExit();if(g_exit_pending)return;}
   datetime h4=iTime(_Symbol,PERIOD_H4,0);if(h4<=0)return;
   if(g_last_h4_open==0){g_last_h4_open=h4;return;}
   if(h4!=g_last_h4_open){g_last_h4_open=h4;ProcessDecision(h4);}
  }
