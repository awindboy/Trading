// Deterministic execution fault injection against the actual EA functions.
// No broker trade API is called. Run in Strategy Tester, not on a live chart.
#property strict
#define V13_EXECUTION_TEST

double volumes[16];
string comments[16];
int sides[16];
int selected=-1, sends=0, failures=0;
uint next_code=TRADE_RETCODE_DONE;

int FakeTotal() { int n=0; for(int i=0;i<16;i++) if(volumes[i]>0) n++; return n; }
ulong FakeTicket(int index)
  {
   int n=0;
   for(int i=0;i<16;i++) if(volumes[i]>0)
     { if(n++==index) { selected=i; return (ulong)i+1; } }
   return 0;
  }
bool FakeSelect(ulong ticket)
  { selected=(int)ticket-1; return selected>=0 && selected<16 && volumes[selected]>0; }
string FakeString(ENUM_POSITION_PROPERTY_STRING key)
  { return key==POSITION_SYMBOL ? _Symbol : comments[selected]; }
long FakeInteger(ENUM_POSITION_PROPERTY_INTEGER key)
  { return key==POSITION_MAGIC ? 1300260926 : sides[selected]; }
double FakeDouble(ENUM_POSITION_PROPERTY_DOUBLE key)
  { return key==POSITION_VOLUME ? volumes[selected] : 100.; }

class CTrade
  {
public:
   uint code;
   double filled;
   void SetExpertMagicNumber(long x) {}
   void SetDeviationInPoints(int x) {}
   bool SetTypeFillingBySymbol(string x) { return true; }
   void SetAsyncMode(bool x) {}
   uint ResultRetcode() { return code; }
   string ResultRetcodeDescription() { return "FAULT_INJECTION"; }
   ulong ResultDeal() { return 123; }
   double ResultPrice() { return 100.; }
   double ResultVolume() { return filled; }
   bool Send(double volume,string comment,int direction)
     {
      sends++; code=next_code; next_code=TRADE_RETCODE_DONE; filled=0;
      if(code==TRADE_RETCODE_DONE || code==TRADE_RETCODE_DONE_PARTIAL)
        {
         filled=code==TRADE_RETCODE_DONE ? volume : volume/2;
         for(int i=0;i<16;i++) if(volumes[i]==0)
           { volumes[i]=filled; comments[i]=comment; sides[i]=direction; break; }
        }
      return code==TRADE_RETCODE_DONE || code==TRADE_RETCODE_DONE_PARTIAL;
     }
   bool Buy(double v,string s,double p,double sl,double tp,string c) { return Send(v,c,0); }
   bool Sell(double v,string s,double p,double sl,double tp,string c) { return Send(v,c,1); }
   bool PositionClose(ulong ticket,ulong deviation)
     {
      sends++; code=next_code; next_code=TRADE_RETCODE_DONE;
      if(!FakeSelect(ticket)) { code=TRADE_RETCODE_POSITION_CLOSED; return false; }
      if(code==TRADE_RETCODE_DONE) volumes[selected]=0;
      if(code==TRADE_RETCODE_DONE_PARTIAL) volumes[selected]/=2;
      return code==TRADE_RETCODE_DONE || code==TRADE_RETCODE_DONE_PARTIAL;
     }
  };

#define PositionsTotal FakeTotal
#define PositionGetTicket FakeTicket
#define PositionSelectByTicket FakeSelect
#define PositionGetString FakeString
#define PositionGetInteger FakeInteger
#define PositionGetDouble FakeDouble
#define OnInit SubjectOnInit
#define OnTick SubjectOnTick
#define OnDeinit SubjectOnDeinit
#include "../experts/V13HAOnlyMax10EA.mq5"
#undef OnInit
#undef OnTick
#undef OnDeinit

void Check(bool condition,string name)
  {
   if(!condition) failures++;
   PrintFormat("V13_TEST|%s|%s",condition ? "PASS" : "FAIL",name);
  }
void Reset()
  {
   ArrayInitialize(volumes,0); sends=0; next_code=TRADE_RETCODE_DONE;
   g_pending_entry=false; g_pending_close=false; g_halted=false;
   g_active_journey=false; g_children=0; g_journey_id=0; g_journey_direction=0;
   g_last_ha_open=100; g_last_ha_close=100; g_last_ha_color=1;
   g_signal_time=D'2024.01.02 04:00'; g_execution_bar=D'2024.01.02 08:00';
   g_target_color=1; ResetRetry();
  }
void Bar(double price,int hour)
  {
   MqlRates b={}; b.time=D'2024.01.02 00:00'+hour*3600;
   b.open=price; b.high=price+1; b.low=price-1; b.close=price;
   ObserveCompletedH4(b,b.time+14400);
  }
void Seed(int children)
  {
   StartJourney(1,g_signal_time,g_execution_bar);
   for(int i=0;i<children;i++) { g_pending_entry=true; ServiceExecution(); }
  }
int OnInit()
  {
   Reset(); next_code=TRADE_RETCODE_MARKET_CLOSED; Seed(1);
   Check(!g_halted && g_pending_entry && g_children==0 && sends==1,"closed market queues first entry");
   ServiceExecution(); Check(sends==1,"retry throttled, no tick spam");
   g_next_attempt=0; ServiceExecution(); ServiceExecution();
   Check(g_children==1 && FakeTotal()==1 && sends==2,"reopen gives exactly one child");

   next_code=TRADE_RETCODE_PRICE_CHANGED; g_pending_entry=true; ServiceExecution();
   Check(!g_halted && g_children==1,"same-color transient failure survives");
   g_next_attempt=0; ServiceExecution(); Check(g_children==2 && FakeTotal()==2,"same-color retry increments once");

   Reset(); Seed(3); Bar(90,8); next_code=TRADE_RETCODE_MARKET_CLOSED;
   ServiceExecution(); Check(g_pending_close && !g_halted && FakeTotal()==3,"close failure queues, no reversal");
   // Simulate one ticket already closed before the remaining close fails.
   volumes[0]=0; g_next_attempt=0; ServiceExecution();
   Check(!g_halted && !g_pending_close && g_children==1 && FakeTotal()==1 && g_journey_direction==-1,"resume remaining close then reverse");

   Reset(); Seed(1); Bar(90,8); next_code=TRADE_RETCODE_DONE_PARTIAL;
   ServiceExecution(); Check(!g_halted && g_pending_close && FakeTotal()==1,"partial close keeps remainder pending");
   g_next_attempt=0; ServiceExecution(); Check(g_children==1 && g_journey_direction==-1 && !g_pending_close,"remainder closes before reversal");

   Reset(); next_code=TRADE_RETCODE_MARKET_CLOSED; Seed(1);
   Bar(110,8); g_next_attempt=0; ServiceExecution();
   Check(g_children==1 && sends==2,"expired same-color entry not backfilled");

   Reset(); next_code=TRADE_RETCODE_MARKET_CLOSED; Seed(1);
   Bar(90,8); g_next_attempt=0; ServiceExecution();
   Check(g_children==1 && g_journey_direction==-1 && FakeTotal()==1,"stale pending direction never opens");

   Reset(); Seed(1); Bar(90,8); next_code=TRADE_RETCODE_MARKET_CLOSED; ServiceExecution();
   Bar(110,12); g_next_attempt=0; ServiceExecution();
   Check(g_journey_direction==1 && g_journey_id==2 && g_children==1,"latched close then latest direction, not stale reverse");

   Reset(); Seed(10); Bar(110,8); ServiceExecution();
   Check(g_children==10 && sends==10 && FakeTotal()==10,"max ten preserved");

   Reset(); next_code=TRADE_RETCODE_TIMEOUT; Seed(1); g_next_attempt=0; ServiceExecution();
   Check(g_halted && sends==1,"ambiguous timeout is not blindly resent");
   Reset(); next_code=TRADE_RETCODE_NO_MONEY; Seed(1);
   Check(g_halted && sends==1,"invalid economics stops explicitly");
   Reset(); next_code=TRADE_RETCODE_DONE_PARTIAL; Seed(1); ServiceExecution();
   Check(g_halted && sends==1 && FakeTotal()==1,"partial entry never duplicated or counted as full");
   Reset(); Bar(110,4); Bar(90,8); Bar(110,12); ServiceExecution();
   Check(sends==1 && FakeTotal()==1 && g_journey_direction==1,"history catchup cannot batch entries");
   PrintFormat("V13_TEST_SUMMARY|failures=%d|broker_orders=0",failures);
   return failures==0 ? INIT_SUCCEEDED : INIT_FAILED;
  }
void OnTick() { TesterStop(); }
