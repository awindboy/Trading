//+------------------------------------------------------------------+
//| MentorDeterministicV6EA.mq5                                      |
//| V6-003E role-conditioned research EA R0                           |
//|                                                                  |
//| RESEARCH ONLY. STRATEGY TESTER ONLY.                              |
//| No production authority.                                         |
//|                                                                  |
//| Frozen research control reproduced here:                         |
//| H  = DIRECT + D24 aligned + MENV HIGH_HIGH                       |
//| L1 = DIRECT + D14=D24=local, excluding H-authorized parent       |
//| L2 = ONE_RENEG + D24 aligned                                     |
//|                                                                  |
//| Source substrate:                                                 |
//| M15 DC(k=2, prior SMA ATR14) -> persistent first consumption      |
//| -> atomic same-M1 penetration + close recovery                    |
//| -> pre-sweep M5 owner opposite reaction                          |
//| -> sweep extreme intact                                          |
//| -> first completed M5 BOS-owner transition toward reaction       |
//|                                                                  |
//| R0 purpose: event/routing parity + tester economics.              |
//| H pending is virtual-on-touch to permit fill-time exposure check. |
//+------------------------------------------------------------------+
#property strict
#property version   "001.000"
#property description "V6-003E role-conditioned research EA R0.3; sweep-time prior parity"

#include <Trade/Trade.mqh>

#define V6_BUILD                 "V6_003E_ROLE_CORE_R0_3"
#define V6_DC_K                  2.0
#define V6_ATR_N                 14
#define V6_MENV_MIN_PRIOR        20
#define V6_L_MAX_ACTIVE_M1       240
#define V6_EPS                   1e-12
#define V6_INVALID_DOUBLE        DBL_MAX

enum V6Module
  {
   V6_MOD_NONE=0,
   V6_MOD_H,
   V6_MOD_L1,
   V6_MOD_L2
  };

enum V6PendingState
  {
   V6_PENDING_NONE=0,
   V6_PENDING_ARMED,
   V6_PENDING_FILLED,
   V6_PENDING_TERMINAL,
   V6_PENDING_BLOCKED
  };

//--- tester/execution inputs
input long   InpMagicNumber          = 26082960;
input bool   InpExecuteTrades        = true;
input double InpRiskMoney            = 100.0;
input bool   InpEnsureHPartialSteps  = true;
input int    InpDeviationPoints      = 30;

//--- diagnostics
input bool   InpWriteEventCsv        = true;
input bool   InpVerboseLog           = false;
input string InpEventCsvFile         = "mentor_v6_role_core_r0_events.csv";

// Parity-only research boundary.
// 0 = no mid-test reset. The test start itself always starts H1/D1 feature warm-up from zero.
// For the frozen GOLD22 -> GOLD2325 reproduction run, set 2023.01.03 01:00.
// This resets ONLY D14/D24/D1-ATR feature warm-up; MENV prior history is intentionally retained.
input datetime InpParityFeatureResetAt = 0;

struct V6LiquidityLevel
  {
   long     id;
   int      type;              // +1 H, -1 L
   double   price;
   datetime pivot_time;
   datetime available_at;
   bool     active;
  };

struct V6Reaction
  {
   long     id;
   datetime sweep_time;        // M1 bar open timestamp
   int      dir;               // +1 long reaction, -1 short reaction
   double   liq_price;
   datetime liq_pivot_time;
   datetime liq_available_at;
   long     liq_id;
   int      n_levels;
   double   sweep_extreme;
   int      pre_m5_owner;
   int      m1_owner_at_sweep;
   int      prior_d14;          // frozen completed-H1 prior sampled at sweep_time
   int      prior_d24;          // frozen completed-H1 prior sampled at sweep_time
   int      prior_d24_age;      // shadow-only age sampled at sweep_time
   int      m1_change_count;
   int      m1_seq_state;      // 0 none, 1 event, 2 event->opp, 3 event->opp->event
   bool     m1_seq_invalid;
   bool     invalidated;
   bool     triggered;
  };

struct V6HPending
  {
   long     event_id;
   V6PendingState state;
   int      dir;
   datetime sweep_time;
   datetime trigger_time;
   double   liq_price;
   double   sweep_extreme;
   double   broken_level;
   double   trigger_close;
   double   trigger_spread;
   double   parent_entry;
   double   parent_sl;
   double   parent_risk;
   double   limit_entry;
   double   planned_sl;
   double   planned_risk;
   double   scale;
   double   acceptance;
   double   med_scale;
   double   med_accept;
   int      d24_age;
  };

struct V6LiveTrade
  {
   bool     active;
   ulong    ticket;
   long     event_id;
   V6Module module;
   int      dir;
   datetime sweep_time;
   datetime trigger_time;
   datetime fill_time;
   double   entry;
   double   initial_sl;
   double   risk;
   double   initial_volume;
   bool     h_stage3;
   int      active_m1_bars;
  };

CTrade g_trade;

V6LiquidityLevel g_levels[];
V6Reaction       g_reactions[];
V6HPending       g_hpending[];
V6LiveTrade      g_trades[];

double g_menv_scale_hist[];
double g_menv_accept_hist[];

long g_next_level_id=1;
long g_next_event_id=1;

//--- M15 directional-change state
int      g_dc_mode=0;
bool     g_dc_seeded=false;
double   g_dc_high=-DBL_MAX;
double   g_dc_low= DBL_MAX;
datetime g_dc_high_time=0;
datetime g_dc_low_time=0;

//--- M1/M5 BOS-owner state
int    g_m1_owner=0;
double g_m1_high_level=0.0;
double g_m1_low_level=0.0;
bool   g_m1_has_high=false;
bool   g_m1_has_low=false;

int    g_m5_owner=0;
double g_m5_high_level=0.0;
double g_m5_low_level=0.0;
bool   g_m5_has_high=false;
bool   g_m5_has_low=false;

//--- H1 direction state
int g_d14=0;
int g_d24=0;
int g_d24_age=0;

//--- completed D1 SMA ATR14
double g_d1_atr=0.0;
bool   g_d1_atr_valid=false;

//--- bar clocks
datetime g_last_m1_open=0;
datetime g_last_m5_open=0;
datetime g_last_m15_open=0;
datetime g_last_h1_open=0;
datetime g_last_d1_open=0;

// Feature availability must be causal relative to the accepted raw-data segment,
// not to whatever older bars happen to exist in the MT5 history cache.
int  g_h1_completed_since_feature_start=0;
int  g_d1_completed_since_feature_start=0;
bool g_parity_feature_reset_applied=false;

int g_csv=INVALID_HANDLE;

//--- counters
long g_count_source=0;
long g_count_recovery=0;
long g_count_trigger=0;
long g_count_direct=0;
long g_count_one_reneg=0;
long g_count_h_auth=0;
long g_count_l1=0;
long g_count_l2=0;
long g_count_fills=0;

//+------------------------------------------------------------------+
//| Utility                                                          |
//+------------------------------------------------------------------+
string ModuleName(V6Module m)
  {
   if(m==V6_MOD_H)  return "H";
   if(m==V6_MOD_L1) return "L1";
   if(m==V6_MOD_L2) return "L2";
   return "NONE";
  }

string PendingName(V6PendingState s)
  {
   if(s==V6_PENDING_ARMED)    return "ARMED";
   if(s==V6_PENDING_FILLED)   return "FILLED";
   if(s==V6_PENDING_TERMINAL) return "TERMINAL";
   if(s==V6_PENDING_BLOCKED)  return "BLOCKED";
   return "NONE";
  }

int SignD(const double x)
  {
   if(x>0.0) return 1;
   if(x<0.0) return -1;
   return 0;
  }

double BidNow()
  {
   return SymbolInfoDouble(_Symbol,SYMBOL_BID);
  }

double AskNow()
  {
   return SymbolInfoDouble(_Symbol,SYMBOL_ASK);
  }

double SpreadNow()
  {
   double b=BidNow(),a=AskNow();
   if(a<=0 || b<=0) return 0.0;
   return a-b;
  }

double NormPrice(double p)
  {
   int d=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   return NormalizeDouble(p,d);
  }

bool GetRate(ENUM_TIMEFRAMES tf,int shift,MqlRates &r)
  {
   MqlRates x[1];
   if(CopyRates(_Symbol,tf,shift,1,x)!=1) return false;
   r=x[0];
   return true;
  }

double TrueRangeAt(ENUM_TIMEFRAMES tf,int shift)
  {
   MqlRates a,b;
   if(!GetRate(tf,shift,a) || !GetRate(tf,shift+1,b)) return V6_INVALID_DOUBLE;
   double x1=a.high-a.low;
   double x2=MathAbs(a.high-b.close);
   double x3=MathAbs(a.low-b.close);
   return MathMax(x1,MathMax(x2,x3));
  }

// start_shift=1 includes most recently completed bar.
// M15 DC intentionally requests start_shift=2 so the current DC bar uses PRIOR ATR.
double SmaAtr(ENUM_TIMEFRAMES tf,int start_shift,int n)
  {
   double s=0.0;
   for(int k=0;k<n;k++)
     {
      double tr=TrueRangeAt(tf,start_shift+k);
      if(tr==V6_INVALID_DOUBLE || !MathIsValidNumber(tr)) return V6_INVALID_DOUBLE;
      s+=tr;
     }
   return s/(double)n;
  }

double MedianArray(const double &src[])
  {
   int n=ArraySize(src);
   if(n<=0) return V6_INVALID_DOUBLE;
   double a[];
   ArrayResize(a,n);
   for(int i=0;i<n;i++) a[i]=src[i];
   ArraySort(a);
   if((n%2)==1) return a[n/2];
   return 0.5*(a[n/2-1]+a[n/2]);
  }

void AppendDouble(double &a[],double v)
  {
   int n=ArraySize(a);
   ArrayResize(a,n+1);
   a[n]=v;
  }

void CsvWrite(string event_type,long event_id,V6Module module,int dir,
              datetime sweep_time,datetime trigger_time,
              double liq_price,double sweep_extreme,double broken_level,
              double scale,double acceptance,double med_scale,double med_accept,
              double planned_entry,double actual_entry,double sl,double risk,
              double volume,ulong ticket,string note)
  {
   if(g_csv==INVALID_HANDLE) return;
   FileWrite(g_csv,
             TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),
             V6_BUILD,_Symbol,event_type,(string)event_id,ModuleName(module),(string)dir,
             sweep_time==0?"":TimeToString(sweep_time,TIME_DATE|TIME_SECONDS),
             trigger_time==0?"":TimeToString(trigger_time,TIME_DATE|TIME_SECONDS),
             DoubleToString(liq_price,_Digits),
             DoubleToString(sweep_extreme,_Digits),
             DoubleToString(broken_level,_Digits),
             (string)g_d14,(string)g_d24,(string)g_d24_age,
             (string)ArraySize(g_menv_scale_hist),
             DoubleToString(scale,8),DoubleToString(acceptance,8),
             DoubleToString(med_scale,8),DoubleToString(med_accept,8),
             DoubleToString(planned_entry,_Digits),DoubleToString(actual_entry,_Digits),
             DoubleToString(sl,_Digits),DoubleToString(risk,_Digits),
             DoubleToString(volume,8),(string)ticket,note);
   FileFlush(g_csv);
  }

void LogV(string s)
  {
   if(InpVerboseLog) Print("[V6] ",s);
  }

void ResetFeatureWarmupState(string reason)
  {
   g_d14=0;
   g_d24=0;
   g_d24_age=0;
   g_d1_atr=0.0;
   g_d1_atr_valid=false;
   g_h1_completed_since_feature_start=0;
   g_d1_completed_since_feature_start=0;

   CsvWrite("FEATURE_RESET",0,V6_MOD_NONE,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            reason);
  }

void MaybeApplyParityFeatureReset(datetime current_m1_open)
  {
   if(g_parity_feature_reset_applied) return;
   if(InpParityFeatureResetAt<=0) return;
   if(current_m1_open<InpParityFeatureResetAt) return;

   g_parity_feature_reset_applied=true;
   ResetFeatureWarmupState(
      StringFormat("parity_feature_reset_at=%s",
                   TimeToString(InpParityFeatureResetAt,TIME_DATE|TIME_MINUTES)));
  }

//+------------------------------------------------------------------+
//| Position/exposure helpers                                        |
//+------------------------------------------------------------------+
bool TicketExists(ulong ticket)
  {
   if(ticket==0) return false;
   return PositionSelectByTicket(ticket);
  }

bool HasOppositeExposure(int dir)
  {
   // Include live EA positions.
   for(int i=0;i<ArraySize(g_trades);i++)
     {
      if(!g_trades[i].active) continue;
      if(g_trades[i].dir==-dir && TicketExists(g_trades[i].ticket))
         return true;
     }
   return false;
  }

double NormalizeVolumeFloor(double v)
  {
   double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double vmax=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(step<=0) step=vmin;
   v=MathMin(v,vmax);
   double k=MathFloor((v+1e-12)/step);
   v=k*step;
   if(v<vmin) v=vmin;
   int vd=2;
   if(step<0.01) vd=3;
   if(step<0.001) vd=4;
   return NormalizeDouble(v,vd);
  }

double RiskVolume(int dir,double entry,double sl,V6Module module)
  {
   double one=0.0;
   ENUM_ORDER_TYPE typ=(dir==1?ORDER_TYPE_BUY:ORDER_TYPE_SELL);
   if(!OrderCalcProfit(typ,_Symbol,1.0,entry,sl,one) || MathAbs(one)<V6_EPS)
      return SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double v=InpRiskMoney/MathAbs(one);
   v=NormalizeVolumeFloor(v);

   if(module==V6_MOD_H && InpEnsureHPartialSteps)
     {
      double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
      double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
      if(step<=0) step=vmin;
      double need=4.0*step;
      if(v<need) v=NormalizeVolumeFloor(need);
     }
   return v;
  }

ulong FindNewestMagicPosition(int dir)
  {
   ulong best=0;
   long best_time=0;
   for(int i=0;i<PositionsTotal();i++)
     {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpMagicNumber) continue;
      long typ=PositionGetInteger(POSITION_TYPE);
      int d=(typ==POSITION_TYPE_BUY?1:-1);
      if(d!=dir) continue;
      long tm=PositionGetInteger(POSITION_TIME_MSC);
      if(tm>=best_time){best_time=tm;best=ticket;}
     }
   return best;
  }

bool OpenTrade(V6Module module,long event_id,int dir,
               datetime sweep_time,datetime trigger_time,
               double planned_entry,double sl,double risk_hint,
               double liq_price,double sweep_extreme,double broken_level,
               double scale,double acceptance,double med_scale,double med_accept)
  {
   if(!InpExecuteTrades)
     {
      CsvWrite("SHADOW_FILL",event_id,module,dir,sweep_time,trigger_time,liq_price,
               sweep_extreme,broken_level,scale,acceptance,med_scale,med_accept,
               planned_entry,0,sl,risk_hint,0,0,"execution_disabled");
      return true;
     }

   if(HasOppositeExposure(dir))
     {
      CsvWrite("EXPOSURE_BLOCK",event_id,module,dir,sweep_time,trigger_time,liq_price,
               sweep_extreme,broken_level,scale,acceptance,med_scale,med_accept,
               planned_entry,0,sl,risk_hint,0,0,"opposite_live_position");
      return false;
     }

   double expected=(dir==1?AskNow():BidNow());
   if(expected<=0) return false;
   double vol=RiskVolume(dir,expected,sl,module);
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   string c=StringFormat("V6_%s_E%I64d",ModuleName(module),event_id);

   bool ok=false;
   if(dir==1) ok=g_trade.Buy(vol,_Symbol,0.0,NormPrice(sl),0.0,c);
   else       ok=g_trade.Sell(vol,_Symbol,0.0,NormPrice(sl),0.0,c);

   if(!ok)
     {
      CsvWrite("ORDER_FAIL",event_id,module,dir,sweep_time,trigger_time,liq_price,
               sweep_extreme,broken_level,scale,acceptance,med_scale,med_accept,
               planned_entry,0,sl,risk_hint,vol,0,
               StringFormat("ret=%u %s",g_trade.ResultRetcode(),g_trade.ResultRetcodeDescription()));
      return false;
     }

   ulong ticket=FindNewestMagicPosition(dir);
   double actual=expected;
   if(ticket>0 && PositionSelectByTicket(ticket))
     {
      actual=PositionGetDouble(POSITION_PRICE_OPEN);
      vol=PositionGetDouble(POSITION_VOLUME);
     }
   double rr=MathAbs(actual-sl);
   if(rr<=V6_EPS) rr=risk_hint;

   int n=ArraySize(g_trades);
   ArrayResize(g_trades,n+1);
   g_trades[n].active=true;
   g_trades[n].ticket=ticket;
   g_trades[n].event_id=event_id;
   g_trades[n].module=module;
   g_trades[n].dir=dir;
   g_trades[n].sweep_time=sweep_time;
   g_trades[n].trigger_time=trigger_time;
   g_trades[n].fill_time=TimeCurrent();
   g_trades[n].entry=actual;
   g_trades[n].initial_sl=sl;
   g_trades[n].risk=rr;
   g_trades[n].initial_volume=vol;
   g_trades[n].h_stage3=false;
   g_trades[n].active_m1_bars=0;

   g_count_fills++;
   CsvWrite("FILL",event_id,module,dir,sweep_time,trigger_time,liq_price,
            sweep_extreme,broken_level,scale,acceptance,med_scale,med_accept,
            planned_entry,actual,sl,rr,vol,ticket,"");
   return true;
  }

//+------------------------------------------------------------------+
//| Pivot / BOS owner helpers                                        |
//+------------------------------------------------------------------+
bool ConfirmPivot(ENUM_TIMEFRAMES tf,bool high_pivot,double &price)
  {
   // chronological target: candidate=shift3; older shifts 4,5; newer shifts2,1.
   // Copy individually to avoid series-order ambiguity.
   MqlRates s1,s2,s3,s4,s5;
   if(!GetRate(tf,1,s1)||!GetRate(tf,2,s2)||!GetRate(tf,3,s3)||
      !GetRate(tf,4,s4)||!GetRate(tf,5,s5)) return false;
   if(high_pivot)
     {
      if(s3.high>s4.high && s3.high>s5.high && s3.high>=s2.high && s3.high>=s1.high)
        { price=s3.high; return true; }
     }
   else
     {
      if(s3.low<s4.low && s3.low<s5.low && s3.low<=s2.low && s3.low<=s1.low)
        { price=s3.low; return true; }
     }
   return false;
  }

int ProcessOwnerClose(ENUM_TIMEFRAMES tf,
                      int &owner,double &high_level,double &low_level,
                      bool &has_high,bool &has_low,
                      double &broken_level)
  {
   double p=0.0;
   if(ConfirmPivot(tf,true,p)){high_level=p;has_high=true;}
   if(ConfirmPivot(tf,false,p)){low_level=p;has_low=true;}

   MqlRates b;
   if(!GetRate(tf,1,b)) return 0;
   int old=owner,newv=owner;
   if(has_high && b.close>high_level) newv=1;
   if(has_low  && b.close<low_level)  newv=-1;
   if(newv!=old)
     {
      owner=newv;
      broken_level=(newv==1?high_level:low_level);
      return newv;
     }
   owner=newv;
   return 0;
  }

//+------------------------------------------------------------------+
//| M15 DC source                                                    |
//+------------------------------------------------------------------+
void AddLiquidityLevel(int type,double price,datetime pivot_time,datetime available_at)
  {
   int n=ArraySize(g_levels);
   ArrayResize(g_levels,n+1);
   g_levels[n].id=g_next_level_id++;
   g_levels[n].type=type;
   g_levels[n].price=price;
   g_levels[n].pivot_time=pivot_time;
   g_levels[n].available_at=available_at;
   g_levels[n].active=true;
   g_count_source++;
   CsvWrite("SOURCE_ADD",g_levels[n].id,V6_MOD_NONE,0,0,0,price,0,0,
            0,0,0,0,0,0,0,0,0,0,"M15_DC_K2");
  }

void ProcessM15Close(datetime boundary_time)
  {
   MqlRates b;
   if(!GetRate(PERIOD_M15,1,b)) return;
   double atr=SmaAtr(PERIOD_M15,2,V6_ATR_N); // prior ATR only
   if(atr==V6_INVALID_DOUBLE || !MathIsValidNumber(atr) || atr<=0) return;

   if(!g_dc_seeded)
     {
      g_dc_high=b.high; g_dc_low=b.low;
      g_dc_high_time=b.time; g_dc_low_time=b.time;
      g_dc_seeded=true;
      return;
     }

   if(g_dc_mode==0)
     {
      if(b.high>g_dc_high){g_dc_high=b.high;g_dc_high_time=b.time;}
      if(b.low <g_dc_low ){g_dc_low =b.low; g_dc_low_time =b.time;}

      if(g_dc_high-b.close>=V6_DC_K*atr && g_dc_high_time<b.time)
        {
         AddLiquidityLevel(+1,g_dc_high,g_dc_high_time,boundary_time);
         g_dc_mode=-1;
         g_dc_low=b.low;g_dc_low_time=b.time;
        }
      else if(b.close-g_dc_low>=V6_DC_K*atr && g_dc_low_time<b.time)
        {
         AddLiquidityLevel(-1,g_dc_low,g_dc_low_time,boundary_time);
         g_dc_mode=1;
         g_dc_high=b.high;g_dc_high_time=b.time;
        }
     }
   else if(g_dc_mode==1)
     {
      if(b.high>g_dc_high){g_dc_high=b.high;g_dc_high_time=b.time;}
      if(g_dc_high-b.close>=V6_DC_K*atr && g_dc_high_time<b.time)
        {
         AddLiquidityLevel(+1,g_dc_high,g_dc_high_time,boundary_time);
         g_dc_mode=-1;
         g_dc_low=b.low;g_dc_low_time=b.time;
        }
     }
   else
     {
      if(b.low<g_dc_low){g_dc_low=b.low;g_dc_low_time=b.time;}
      if(b.close-g_dc_low>=V6_DC_K*atr && g_dc_low_time<b.time)
        {
         AddLiquidityLevel(-1,g_dc_low,g_dc_low_time,boundary_time);
         g_dc_mode=1;
         g_dc_high=b.high;g_dc_high_time=b.time;
        }
     }
  }

//+------------------------------------------------------------------+
//| Reaction / M1 path                                               |
//+------------------------------------------------------------------+
void AddReaction(datetime sweep_time,int dir,double liq_price,datetime liq_pivot,
                 datetime liq_available,long liq_id,int n_levels,double extreme)
  {
   int n=ArraySize(g_reactions);
   ArrayResize(g_reactions,n+1);
   g_reactions[n].id=g_next_event_id++;
   g_reactions[n].sweep_time=sweep_time;
   g_reactions[n].dir=dir;
   g_reactions[n].liq_price=liq_price;
   g_reactions[n].liq_pivot_time=liq_pivot;
   g_reactions[n].liq_available_at=liq_available;
   g_reactions[n].liq_id=liq_id;
   g_reactions[n].n_levels=n_levels;
   g_reactions[n].sweep_extreme=extreme;
   g_reactions[n].pre_m5_owner=g_m5_owner;
   g_reactions[n].m1_owner_at_sweep=g_m1_owner;

   // V6-003B/C and V6-003D causal contract:
   // directional prior is sampled at sweep_time from already-completed HTF bars.
   // Never let H1 bars completed between sweep and later M5 trigger change authority.
   g_reactions[n].prior_d14=g_d14;
   g_reactions[n].prior_d24=g_d24;
   g_reactions[n].prior_d24_age=g_d24_age;

   g_reactions[n].m1_change_count=0;
   g_reactions[n].m1_seq_state=0;
   g_reactions[n].m1_seq_invalid=false;
   g_reactions[n].invalidated=(g_m5_owner!=-dir);
   g_reactions[n].triggered=false;

   if(!g_reactions[n].invalidated) g_count_recovery++;
   CsvWrite(g_reactions[n].invalidated?"RECOVERY_REJECT_PRE_M5":"RECOVERY",
            g_reactions[n].id,V6_MOD_NONE,dir,sweep_time,0,liq_price,extreme,0,
            0,0,0,0,0,0,0,0,0,0,
            StringFormat("levels=%d preM5=%d preM1=%d priorD14=%d priorD24=%d priorAge=%d",
                         n_levels,g_m5_owner,g_m1_owner,
                         g_reactions[n].prior_d14,g_reactions[n].prior_d24,g_reactions[n].prior_d24_age));
  }

void ProcessClosedM1ForSweeps()
  {
   MqlRates b;
   if(!GetRate(PERIOD_M1,1,b)) return;

   // Existing reaction extremes are protected strictly AFTER their sweep bar.
   for(int j=0;j<ArraySize(g_reactions);j++)
     {
      if(g_reactions[j].invalidated || g_reactions[j].triggered) continue;
      if(b.time<=g_reactions[j].sweep_time) continue;
      if(g_reactions[j].dir==1 && b.low<g_reactions[j].sweep_extreme)
        {
         g_reactions[j].invalidated=true;
         CsvWrite("REACTION_INVALIDATE",g_reactions[j].id,V6_MOD_NONE,g_reactions[j].dir,
                  g_reactions[j].sweep_time,0,g_reactions[j].liq_price,
                  g_reactions[j].sweep_extreme,0,0,0,0,0,0,0,0,0,0,0,"sweep_extreme_broken");
        }
      if(g_reactions[j].dir==-1 && b.high>g_reactions[j].sweep_extreme)
        {
         g_reactions[j].invalidated=true;
         CsvWrite("REACTION_INVALIDATE",g_reactions[j].id,V6_MOD_NONE,g_reactions[j].dir,
                  g_reactions[j].sweep_time,0,g_reactions[j].liq_price,
                  g_reactions[j].sweep_extreme,0,0,0,0,0,0,0,0,0,0,0,"sweep_extreme_broken");
        }
     }

   // Consume every level on first penetration. Recovered levels on the same M1
   // and direction are deduped to the same representative rule as Python:
   // long => highest swept low-level; short => lowest swept high-level.
   bool hasLong=false,hasShort=false;
   double longPrice=-DBL_MAX,shortPrice=DBL_MAX;
   int longN=0,shortN=0;
   datetime longPivot=0,longAvail=0,shortPivot=0,shortAvail=0;
   long longId=0,shortId=0;

   for(int i=0;i<ArraySize(g_levels);i++)
     {
      if(!g_levels[i].active) continue;
      if(g_levels[i].available_at>b.time) continue;

      if(g_levels[i].type==+1 && b.high>g_levels[i].price)
        {
         g_levels[i].active=false;
         if(b.close<g_levels[i].price)
           {
            shortN++;
            if(g_levels[i].price<shortPrice)
              {
               hasShort=true;shortPrice=g_levels[i].price;
               shortPivot=g_levels[i].pivot_time;shortAvail=g_levels[i].available_at;shortId=g_levels[i].id;
              }
           }
        }
      else if(g_levels[i].type==-1 && b.low<g_levels[i].price)
        {
         g_levels[i].active=false;
         if(b.close>g_levels[i].price)
           {
            longN++;
            if(g_levels[i].price>longPrice)
              {
               hasLong=true;longPrice=g_levels[i].price;
               longPivot=g_levels[i].pivot_time;longAvail=g_levels[i].available_at;longId=g_levels[i].id;
              }
           }
        }
     }

   if(hasLong)  AddReaction(b.time,+1,longPrice,longPivot,longAvail,longId,longN,b.low);
   if(hasShort) AddReaction(b.time,-1,shortPrice,shortPivot,shortAvail,shortId,shortN,b.high);
  }

void UpdateReactionM1PathOnOwnerChange(int new_owner)
  {
   if(new_owner==0) return;
   for(int j=0;j<ArraySize(g_reactions);j++)
     {
      if(g_reactions[j].invalidated || g_reactions[j].triggered) continue;

      g_reactions[j].m1_change_count++;
      int d=g_reactions[j].dir;
      int c=g_reactions[j].m1_change_count;

      if(c==1 && new_owner==d && !g_reactions[j].m1_seq_invalid)
         g_reactions[j].m1_seq_state=1;
      else if(c==2 && g_reactions[j].m1_seq_state==1 && new_owner==-d && !g_reactions[j].m1_seq_invalid)
         g_reactions[j].m1_seq_state=2;
      else if(c==3 && g_reactions[j].m1_seq_state==2 && new_owner==d && !g_reactions[j].m1_seq_invalid)
         g_reactions[j].m1_seq_state=3;
      else
         g_reactions[j].m1_seq_invalid=true;
     }
  }

void ProcessM1OwnerClose()
  {
   double broken=0.0;
   int changed=ProcessOwnerClose(PERIOD_M1,g_m1_owner,g_m1_high_level,g_m1_low_level,
                                 g_m1_has_high,g_m1_has_low,broken);
   if(changed!=0) UpdateReactionM1PathOnOwnerChange(changed);
  }

//+------------------------------------------------------------------+
//| Direction / D1 state                                             |
//+------------------------------------------------------------------+
void ProcessH1Close()
  {
   MqlRates cur,b14,b24;
   if(!GetRate(PERIOD_H1,1,cur)) return;

   // The just-completed H1 belongs to the current accepted-data segment.
   // Pre-segment MT5 cache bars are not allowed to make D14/D24 available early.
   g_h1_completed_since_feature_start++;

   g_d14=0;
   if(g_h1_completed_since_feature_start>=15 && GetRate(PERIOD_H1,15,b14))
      g_d14=SignD(cur.close-b14.close); // latest completed vs 14 completed H1 bars earlier

   if(g_h1_completed_since_feature_start<25)
     {
      g_d24=0;
      g_d24_age=0;
      return;
     }

   if(!GetRate(PERIOD_H1,25,b24))
     {
      g_d24=0;
      g_d24_age=0;
      return;
     }

   int nd24=SignD(cur.close-b24.close); // latest completed vs 24 completed H1 bars earlier
   if(nd24==0)
     {
      g_d24=0;
      g_d24_age=0;
     }
   else if(nd24==g_d24)
     {
      g_d24_age++;
     }
   else
     {
      g_d24=nd24;
      g_d24_age=1;
     }
  }

void ProcessD1Close()
  {
   // Offline V6 D1 ATR is unavailable until 14 completed D1 bars exist
   // inside the accepted raw-data segment. Never borrow older tester-cache days.
   g_d1_completed_since_feature_start++;
   g_d1_atr_valid=false;

   if(g_d1_completed_since_feature_start<V6_ATR_N) return;

   double a=SmaAtr(PERIOD_D1,1,V6_ATR_N);
   if(a!=V6_INVALID_DOUBLE && MathIsValidNumber(a) && a>0)
     {
      g_d1_atr=a;
      g_d1_atr_valid=true;
     }
  }

//+------------------------------------------------------------------+
//| Trigger geometry / routing                                       |
//+------------------------------------------------------------------+
bool IsDirect(const V6Reaction &r)
  {
   return (r.m1_owner_at_sweep==-r.dir &&
           !r.m1_seq_invalid &&
           r.m1_change_count==1 &&
           r.m1_seq_state==1 &&
           g_m1_owner==r.dir);
  }

bool IsOneReneg(const V6Reaction &r)
  {
   return (r.m1_owner_at_sweep==-r.dir &&
           !r.m1_seq_invalid &&
           r.m1_change_count==3 &&
           r.m1_seq_state==3 &&
           g_m1_owner==r.dir);
  }

void AddHPending(long event_id,int dir,datetime sweep_time,datetime trigger_time,
                 double liq_price,double extreme,double broken,double trigger_close,
                 double spread,double parent_entry,double parent_sl,double parent_risk,
                 double limit_entry,double planned_sl,double planned_risk,
                 double scale,double acceptance,double med_scale,double med_accept,
                 int prior_d24_age)
  {
   int n=ArraySize(g_hpending);
   ArrayResize(g_hpending,n+1);
   g_hpending[n].event_id=event_id;
   g_hpending[n].state=V6_PENDING_ARMED;
   g_hpending[n].dir=dir;
   g_hpending[n].sweep_time=sweep_time;
   g_hpending[n].trigger_time=trigger_time;
   g_hpending[n].liq_price=liq_price;
   g_hpending[n].sweep_extreme=extreme;
   g_hpending[n].broken_level=broken;
   g_hpending[n].trigger_close=trigger_close;
   g_hpending[n].trigger_spread=spread;
   g_hpending[n].parent_entry=parent_entry;
   g_hpending[n].parent_sl=parent_sl;
   g_hpending[n].parent_risk=parent_risk;
   g_hpending[n].limit_entry=limit_entry;
   g_hpending[n].planned_sl=planned_sl;
   g_hpending[n].planned_risk=planned_risk;
   g_hpending[n].scale=scale;
   g_hpending[n].acceptance=acceptance;
   g_hpending[n].med_scale=med_scale;
   g_hpending[n].med_accept=med_accept;
   g_hpending[n].d24_age=prior_d24_age;

   CsvWrite("H_PENDING_ARM",event_id,V6_MOD_H,dir,sweep_time,trigger_time,liq_price,
            extreme,broken,scale,acceptance,med_scale,med_accept,limit_entry,0,
            planned_sl,planned_risk,0,0,"virtual_pending_R0");
  }

void RouteTriggeredReaction(int j,datetime trigger_time,double trigger_close,double broken_level)
  {
   V6Reaction r=g_reactions[j];
   bool direct=IsDirect(r);
   bool one=IsOneReneg(r);

   if(direct) g_count_direct++;
   if(one)    g_count_one_reneg++;

   if(!direct && !one)
     {
      CsvWrite("TRIGGER_NO_PATH",r.id,V6_MOD_NONE,r.dir,r.sweep_time,trigger_time,
               r.liq_price,r.sweep_extreme,broken_level,0,0,0,0,0,0,0,0,0,0,
               StringFormat("m1start=%d changes=%d seq=%d invalid=%d",
                            r.m1_owner_at_sweep,r.m1_change_count,r.m1_seq_state,(int)r.m1_seq_invalid));
      return;
     }

   double spread=SpreadNow();
   double parent_entry=(r.dir==1?trigger_close+spread:trigger_close);
   double parent_sl=(r.dir==1?r.sweep_extreme:r.sweep_extreme+spread);
   double parent_risk=MathAbs(parent_entry-parent_sl);

   // H 50% pullback geometry uses chart midpoint of trigger-close to broken M5 level.
   double chart_limit=trigger_close-r.dir*0.5*MathAbs(trigger_close-broken_level);
   double limit_entry=(r.dir==1?chart_limit+spread:chart_limit);
   double planned_sl=parent_sl;
   double planned_risk=MathAbs(limit_entry-planned_sl);
   bool improved=(r.dir==1?limit_entry<parent_entry:limit_entry>parent_entry);
   bool geom=(parent_risk>V6_EPS && planned_risk>V6_EPS && improved);

   double scale=V6_INVALID_DOUBLE,accept=V6_INVALID_DOUBLE,meds=V6_INVALID_DOUBLE,meda=V6_INVALID_DOUBLE;
   bool menv_valid=false,hh=false;
   if(direct && geom && g_d1_atr_valid && g_d1_atr>0)
     {
      double acceptance_margin=(trigger_close-broken_level)*r.dir;
      scale=planned_risk/g_d1_atr;
      accept=acceptance_margin/g_d1_atr;
      int prior=ArraySize(g_menv_scale_hist);
      if(prior>=V6_MENV_MIN_PRIOR)
        {
         meds=MedianArray(g_menv_scale_hist);
         meda=MedianArray(g_menv_accept_hist);
         menv_valid=true;
         hh=(scale>meds && accept>meda);
        }

      // Current opportunity enters history only AFTER its state is classified.
      AppendDouble(g_menv_scale_hist,scale);
      AppendDouble(g_menv_accept_hist,accept);
     }

   int pd14=r.prior_d14;
   int pd24=r.prior_d24;
   int page=r.prior_d24_age;

   if(pd14!=g_d14 || pd24!=g_d24)
     {
      CsvWrite("PRIOR_DRIFT",r.id,V6_MOD_NONE,r.dir,r.sweep_time,trigger_time,r.liq_price,
               r.sweep_extreme,broken_level,scale,accept,meds,meda,limit_entry,0,
               planned_sl,planned_risk,0,0,
               StringFormat("sweepD14=%d sweepD24=%d triggerD14=%d triggerD24=%d",
                            pd14,pd24,g_d14,g_d24));
     }

   bool h_auth=(direct && geom && menv_valid && hh && pd24==r.dir);

   CsvWrite("ROUTE_STATE",r.id,V6_MOD_NONE,r.dir,r.sweep_time,trigger_time,r.liq_price,
            r.sweep_extreme,broken_level,scale,accept,meds,meda,limit_entry,0,
            planned_sl,planned_risk,0,0,
            StringFormat("path=%s priorD14=%d priorD24=%d priorAge=%d triggerD14=%d triggerD24=%d triggerAge=%d menv=%s Hauth=%d",
                         direct?"DIRECT":"ONE_RENEG",pd14,pd24,page,g_d14,g_d24,g_d24_age,
                         menv_valid?(hh?"HH":"NOT_HH"):"WARMUP",(int)h_auth));

   if(h_auth)
     {
      g_count_h_auth++;
      AddHPending(r.id,r.dir,r.sweep_time,trigger_time,r.liq_price,r.sweep_extreme,
                  broken_level,trigger_close,spread,parent_entry,parent_sl,parent_risk,
                  limit_entry,planned_sl,planned_risk,scale,accept,meds,meda,page);
      return; // causal H priority: L1 cannot resurrect later if H does not fill.
     }

   if(direct && pd14==r.dir && pd24==r.dir)
     {
      g_count_l1++;
      OpenTrade(V6_MOD_L1,r.id,r.dir,r.sweep_time,trigger_time,
                (r.dir==1?AskNow():BidNow()),parent_sl,parent_risk,
                r.liq_price,r.sweep_extreme,broken_level,scale,accept,meds,meda);
      return;
     }

   if(one && pd24==r.dir)
     {
      g_count_l2++;
      OpenTrade(V6_MOD_L2,r.id,r.dir,r.sweep_time,trigger_time,
                (r.dir==1?AskNow():BidNow()),parent_sl,parent_risk,
                r.liq_price,r.sweep_extreme,broken_level,scale,accept,meds,meda);
      return;
     }

   CsvWrite("ROUTE_NO_TRADE",r.id,V6_MOD_NONE,r.dir,r.sweep_time,trigger_time,
            r.liq_price,r.sweep_extreme,broken_level,scale,accept,meds,meda,
            limit_entry,0,planned_sl,planned_risk,0,0,"frozen_core_no_authority");
  }

void ProcessM5Close(datetime boundary_time)
  {
   double broken=0.0;
   int changed=ProcessOwnerClose(PERIOD_M5,g_m5_owner,g_m5_high_level,g_m5_low_level,
                                 g_m5_has_high,g_m5_has_low,broken);
   if(changed==0) return;

   MqlRates b;
   if(!GetRate(PERIOD_M5,1,b)) return;

   for(int j=0;j<ArraySize(g_reactions);j++)
     {
      if(g_reactions[j].invalidated || g_reactions[j].triggered) continue;
      if(g_reactions[j].pre_m5_owner!=-g_reactions[j].dir) continue;
      if(changed!=g_reactions[j].dir) continue;
      if(boundary_time<=g_reactions[j].sweep_time) continue;

      g_reactions[j].triggered=true;
      g_count_trigger++;
      CsvWrite("M5_TRIGGER",g_reactions[j].id,V6_MOD_NONE,g_reactions[j].dir,
               g_reactions[j].sweep_time,boundary_time,g_reactions[j].liq_price,
               g_reactions[j].sweep_extreme,broken,0,0,0,0,0,0,0,0,0,0,
               StringFormat("m1changes=%d seq=%d",g_reactions[j].m1_change_count,g_reactions[j].m1_seq_state));
      RouteTriggeredReaction(j,boundary_time,b.close,broken);
     }
  }

//+------------------------------------------------------------------+
//| Pending fill / live management                                   |
//+------------------------------------------------------------------+
void ManageHPending()
  {
   double bid=BidNow(),ask=AskNow();
   if(bid<=0 || ask<=0) return;

   for(int i=0;i<ArraySize(g_hpending);i++)
     {
      if(g_hpending[i].state!=V6_PENDING_ARMED) continue;
      V6HPending p=g_hpending[i];

      bool terminal=false,fill=false;
      if(p.dir==1)
        {
         double tp_parent=p.parent_entry+p.parent_risk;
         terminal=(bid<=p.parent_sl || bid>=tp_parent);
         fill=(ask<=p.limit_entry);
        }
      else
        {
         double tp_parent=p.parent_entry-p.parent_risk;
         terminal=(ask>=p.parent_sl || ask<=tp_parent);
         fill=(bid>=p.limit_entry);
        }

      // Frozen offline parent check evaluates terminal before pending fill.
      if(terminal)
        {
         g_hpending[i].state=V6_PENDING_TERMINAL;
         CsvWrite("H_PENDING_TERMINAL",p.event_id,V6_MOD_H,p.dir,p.sweep_time,p.trigger_time,
                  p.liq_price,p.sweep_extreme,p.broken_level,p.scale,p.acceptance,p.med_scale,p.med_accept,
                  p.limit_entry,0,p.planned_sl,p.planned_risk,0,0,"parent_terminal_before_fill");
         continue;
        }

      if(fill)
        {
         if(HasOppositeExposure(p.dir))
           {
            g_hpending[i].state=V6_PENDING_BLOCKED;
            CsvWrite("H_PENDING_BLOCK",p.event_id,V6_MOD_H,p.dir,p.sweep_time,p.trigger_time,
                     p.liq_price,p.sweep_extreme,p.broken_level,p.scale,p.acceptance,p.med_scale,p.med_accept,
                     p.limit_entry,0,p.planned_sl,p.planned_risk,0,0,"opposite_exposure_at_touch");
            continue;
           }
         bool ok=OpenTrade(V6_MOD_H,p.event_id,p.dir,p.sweep_time,p.trigger_time,p.limit_entry,
                           p.planned_sl,p.planned_risk,p.liq_price,p.sweep_extreme,p.broken_level,
                           p.scale,p.acceptance,p.med_scale,p.med_accept);
         g_hpending[i].state=(ok?V6_PENDING_FILLED:V6_PENDING_BLOCKED);
        }
     }
  }

double ExitSidePrice(int dir)
  {
   return dir==1?BidNow():AskNow();
  }

double ApproxTradeR(const V6LiveTrade &t,double exit_price)
  {
   if(t.risk<=V6_EPS) return 0.0;
   return (exit_price-t.entry)*t.dir/t.risk;
  }

void MarkClosed(int idx,string reason,double px)
  {
   if(idx<0 || idx>=ArraySize(g_trades) || !g_trades[idx].active) return;
   V6LiveTrade t=g_trades[idx];
   double r=ApproxTradeR(t,px);
   double composite=r;
   if(t.module==V6_MOD_H && t.h_stage3)
      composite=0.75 + 0.75*r; // 25% realized at +3R; residual is 75%.
   CsvWrite("EXIT",t.event_id,t.module,t.dir,t.sweep_time,t.trigger_time,0,0,0,
            0,0,0,0,t.entry,px,t.initial_sl,t.risk,t.initial_volume,t.ticket,
            StringFormat("%s rawR=%.6f compositeR=%.6f bars=%d",reason,r,composite,t.active_m1_bars));
   g_trades[idx].active=false;
  }

void ReconcileClosedPositions()
  {
   for(int i=0;i<ArraySize(g_trades);i++)
     {
      if(!g_trades[i].active) continue;
      if(TicketExists(g_trades[i].ticket)) continue;

      double px=ExitSidePrice(g_trades[i].dir);
      string reason="broker_or_external_close";
      // Best-effort recover latest exit deal for this position id/ticket.
      if(HistorySelect(g_trades[i].fill_time-60,TimeCurrent()+60))
        {
         for(int d=HistoryDealsTotal()-1;d>=0;d--)
           {
            ulong deal=HistoryDealGetTicket(d);
            if(deal==0) continue;
            if(HistoryDealGetString(deal,DEAL_SYMBOL)!=_Symbol) continue;
            if((long)HistoryDealGetInteger(deal,DEAL_MAGIC)!=InpMagicNumber) continue;
            long entry=HistoryDealGetInteger(deal,DEAL_ENTRY);
            if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY) continue;
            px=HistoryDealGetDouble(deal,DEAL_PRICE);
            long why=HistoryDealGetInteger(deal,DEAL_REASON);
            if(why==DEAL_REASON_SL) reason="SL";
            else if(why==DEAL_REASON_TP) reason="TP";
            else reason="DEAL_OUT";
            break;
           }
        }
      MarkClosed(i,reason,px);
     }
  }

void ManageLiveTrades()
  {
   ReconcileClosedPositions();

   double bid=BidNow(),ask=AskNow();
   if(bid<=0 || ask<=0) return;

   for(int i=0;i<ArraySize(g_trades);i++)
     {
      if(!g_trades[i].active || !TicketExists(g_trades[i].ticket)) continue;
      V6LiveTrade t=g_trades[i];
      double px=(t.dir==1?bid:ask);
      double r=(px-t.entry)*t.dir/t.risk;

      if(t.module==V6_MOD_L1 || t.module==V6_MOD_L2)
        {
         if(r>=1.0)
           {
            if(g_trade.PositionClose(t.ticket,InpDeviationPoints))
               MarkClosed(i,"L_TP1",px);
           }
        }
      else if(t.module==V6_MOD_H)
        {
         if(!t.h_stage3 && r>=3.0)
           {
            double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
            double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
            if(step<=0) step=vmin;
            double cur=PositionGetDouble(POSITION_VOLUME);
            double cv=NormalizeVolumeFloor(0.25*t.initial_volume);
            if(cv>=cur) cv=NormalizeVolumeFloor(cur*0.25);

            bool partial_ok=false;
            if(cv>=vmin && cv<cur)
               partial_ok=g_trade.PositionClosePartial(t.ticket,cv,InpDeviationPoints);

            // Move residual to BE even if volume rounding prevented exact 25%;
            // diagnostic records any execution deviation.
            bool mod_ok=g_trade.PositionModify(t.ticket,NormPrice(t.entry),0.0);
            g_trades[i].h_stage3=true;
            CsvWrite("H_STAGE3",t.event_id,V6_MOD_H,t.dir,t.sweep_time,t.trigger_time,0,0,0,
                     0,0,0,0,t.entry,px,t.initial_sl,t.risk,cv,t.ticket,
                     StringFormat("partial=%d modifyBE=%d curvol=%.8f",partial_ok,mod_ok,cur));
           }
         else if(t.h_stage3 && r>=5.0)
           {
            if(g_trade.PositionClose(t.ticket,InpDeviationPoints))
               MarkClosed(i,"H_TP5",px);
           }
        }
     }
  }

void CountActiveM1BarsAndTimeCaps()
  {
   for(int i=0;i<ArraySize(g_trades);i++)
     {
      if(!g_trades[i].active || !TicketExists(g_trades[i].ticket)) continue;
      if(g_trades[i].module!=V6_MOD_L1 && g_trades[i].module!=V6_MOD_L2) continue;
      if(TimeCurrent()<=g_trades[i].fill_time) continue;
      g_trades[i].active_m1_bars++;
      if(g_trades[i].active_m1_bars>=V6_L_MAX_ACTIVE_M1)
        {
         double px=ExitSidePrice(g_trades[i].dir);
         if(g_trade.PositionClose(g_trades[i].ticket,InpDeviationPoints))
            MarkClosed(i,"L_4_ACTIVE_H_CAP",px);
        }
     }
  }

//+------------------------------------------------------------------+
//| Initialization                                                   |
//+------------------------------------------------------------------+
bool IsTester()
  {
   return (bool)MQLInfoInteger(MQL_TESTER);
  }

int OnInit()
  {
   if(!IsTester())
     {
      Print("V6 research EA hard-blocked: Strategy Tester only.");
      return INIT_FAILED;
     }

   if(InpExecuteTrades)
     {
      long mm=AccountInfoInteger(ACCOUNT_MARGIN_MODE);
      if(mm!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
        {
         Print("V6 R0 requires hedging mode for independent same-direction positions. Set InpExecuteTrades=false for shadow-only.");
         return INIT_FAILED;
        }
     }

   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);

   if(InpWriteEventCsv)
     {
      g_csv=FileOpen(InpEventCsvFile,FILE_WRITE|FILE_CSV|FILE_ANSI,',');
      if(g_csv==INVALID_HANDLE)
        {
         Print("Failed to open V6 event CSV: ",GetLastError());
         return INIT_FAILED;
        }
      FileWrite(g_csv,
         "logged_at","build","symbol","event_type","event_id","module","dir",
         "sweep_time","trigger_time","liq_price","sweep_extreme","broken_m5_level",
         "d14","d24","d24_age","menv_prior_n","scale","acceptance","median_scale","median_acceptance",
         "planned_entry","actual_entry","sl","risk","volume","ticket","note");
      FileFlush(g_csv);
     }

   g_last_m1_open=iTime(_Symbol,PERIOD_M1,0);
   g_last_m5_open=iTime(_Symbol,PERIOD_M5,0);
   g_last_m15_open=iTime(_Symbol,PERIOD_M15,0);
   g_last_h1_open=iTime(_Symbol,PERIOD_H1,0);
   g_last_d1_open=iTime(_Symbol,PERIOD_D1,0);

   // R0.2 parity correction:
   // D14/D24/D1-ATR start unavailable and warm up only from bars completed
   // after the Strategy Tester start. Older broker-cache bars have no authority.
   ResetFeatureWarmupState("tester_start_feature_warmup");

   CsvWrite("INIT",0,V6_MOD_NONE,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            StringFormat("tester=1 execute=%d magic=%I64d parity_feature_reset=%s",
                         (int)InpExecuteTrades,InpMagicNumber,
                         InpParityFeatureResetAt>0?
                           TimeToString(InpParityFeatureResetAt,TIME_DATE|TIME_MINUTES):
                           "NONE"));
   Print("Initialized ",V6_BUILD," on ",_Symbol,
         ". Run full history with warmup; production authority NONE.");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   string s=StringFormat("source=%I64d recovery=%I64d trigger=%I64d direct=%I64d one_reneg=%I64d H=%I64d L1=%I64d L2=%I64d fills=%I64d",
                         g_count_source,g_count_recovery,g_count_trigger,g_count_direct,g_count_one_reneg,
                         g_count_h_auth,g_count_l1,g_count_l2,g_count_fills);
   Print("V6 R0 summary: ",s);
   CsvWrite("SUMMARY",0,V6_MOD_NONE,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,s);
   if(g_csv!=INVALID_HANDLE){FileClose(g_csv);g_csv=INVALID_HANDLE;}
  }

//+------------------------------------------------------------------+
//| Main tick                                                        |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Tick-level execution/exit first. Newly armed H pending later in this tick
   // cannot fill until the next incoming tick, matching "strictly after trigger".
   ManageLiveTrades();
   ManageHPending();

   datetime m1=iTime(_Symbol,PERIOD_M1,0);
   if(m1==0 || m1==g_last_m1_open) return;

   // If the historical research dataset had a segment boundary here, reset feature
   // availability before routing any event at/after that boundary. MENV history stays intact.
   MaybeApplyParityFeatureReset(m1);

   // A new M1 bar means the previous one is now causally complete.
   CountActiveM1BarsAndTimeCaps();
   ProcessClosedM1ForSweeps();
   ProcessM1OwnerClose();

   datetime d1=iTime(_Symbol,PERIOD_D1,0);
   if(d1!=0 && d1!=g_last_d1_open)
     {
      g_last_d1_open=d1;
      ProcessD1Close();
     }

   datetime h1=iTime(_Symbol,PERIOD_H1,0);
   if(h1!=0 && h1!=g_last_h1_open)
     {
      g_last_h1_open=h1;
      ProcessH1Close();
     }

   datetime m15=iTime(_Symbol,PERIOD_M15,0);
   if(m15!=0 && m15!=g_last_m15_open)
     {
      g_last_m15_open=m15;
      ProcessM15Close(m1);
     }

   datetime m5=iTime(_Symbol,PERIOD_M5,0);
   if(m5!=0 && m5!=g_last_m5_open)
     {
      g_last_m5_open=m5;
      ProcessM5Close(m1);
     }

   g_last_m1_open=m1;
  }
//+------------------------------------------------------------------+
