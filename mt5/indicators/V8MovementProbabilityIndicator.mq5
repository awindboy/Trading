//+------------------------------------------------------------------+
//| V8MovementProbabilityIndicator.mq5                               |
//| GOLD +/-10.0 movement probability shadow indicator              |
//| Research lineage: V8 movement-probability walk-forward models   |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "V8 shadow indicator: P(|price move| >= 10.0) within 15/30/60m. Direction is NOT estimated."
#property indicator_separate_window
#property indicator_buffers 3
#property indicator_plots   3
#property indicator_minimum 0.0
#property indicator_maximum 100.0

#property indicator_label1  "10p <= 15m"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrLimeGreen
#property indicator_width1  2
#property indicator_label2  "10p <= 30m"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrDeepSkyBlue
#property indicator_width2  2
#property indicator_label3  "10p <= 60m"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrOrange
#property indicator_width3  2

input group "Probability Lines"
input color InpColor15m = clrLimeGreen;       // 15분 확률선 색상
input color InpColor30m = clrDeepSkyBlue;     // 30분 확률선 색상
input color InpColor60m = clrOrange;          // 60분 확률선 색상
input int   InpLineWidth = 2;                 // 확률선 두께
input double InpBarrierPrice = 10.0;          // 연구 기준: GOLD 가격축 10.0 (모델 재학습 없이는 변경 금지)

input group "Event Triangles"
input bool  InpShowM5MA20Contact = true;      // M5 SMA20 contact-start 표시
input bool  InpShowM5UpperBB = true;          // M5 BB20 upper contact-start 표시
input bool  InpShowM5LowerBB = true;          // M5 BB20 lower contact-start 표시
input bool  InpShowH1DoubleB = true;           // H1 Double-B 표시
input color InpColorM5MA20 = clrGold;          // M5 MA20 이벤트 색상
input color InpColorM5UpperBB = clrTomato;     // M5 상단 BB 이벤트 색상
input color InpColorM5LowerBB = clrDodgerBlue; // M5 하단 BB 이벤트 색상
input color InpColorH1DoubleB = clrMagenta;    // H1 Double-B 색상
input int   InpTriangleSize = 2;               // 삼각형 크기
input double InpMarkerOffsetFactor = 0.30;      // 캔들 range 대비 마커 간격
input int   InpMinMarkerOffsetPoints = 40;     // 최소 마커 간격(points)

input group "History / Safety"
input int  InpHistoryDays = 1000;              // 과거 표시 일수
input bool InpAllow2026ModelAfter2026 = false;  // 2027+에서 2026 모델 계속 사용 (기본 OFF)
input bool InpShowStatusComment = true;         // 상태 코멘트 표시

//--- probability buffers (0..100)
double Prob15Buffer[];
double Prob30Buffer[];
double Prob60Buffer[];

string V8MP_PREFIX = "V8MP_EVT_";
bool g_ready = false;
datetime g_last_chart_bar = 0;
int g_last_rates_total = 0;

// Research features are defined on consecutive available M1 rows.
const int V8MP_WINS[8] = {5,15,30,60,120,240,480,1440};

// AUTO-GENERATED FROM WALK-FORWARD PYTHON LOGISTIC MODELS. DO NOT EDIT COEFFICIENTS BY HAND.
#define V8MP_FEATURE_COUNT 53
#define V8MP_MODEL_COUNT 9
double V8MP_INTERCEPT[V8MP_MODEL_COUNT] = {
   -20.825450906278597,
   -17.114964662249299,
   -14.773395861350913,
   -15.186231772080944,
   -12.20831813317508,
   -11.172286849183131,
   -14.308390550701425,
   -13.437995291020201,
   -13.381964497675066
};
double V8MP_COEF[V8MP_MODEL_COUNT][V8MP_FEATURE_COUNT] = {
   { // 2024 / 15m
      -0.65045207412490924, 2.0031132908111053, -0.328803325269721, 1.3218056304471169, -0.73943152938222878, 0.27990845354500959,
      0.83386150073991627, 0.3253323612005331, -0.26843232105037462, -0.49128698000117477, -0.088008873523713282, 1.4150464917158374,
      -0.31666854171292863, 0.092730498632055999, 0.17242577771009523, -0.21395877114589945, 0.42908205599863125, -0.26206472668020758,
      -0.54792444653160932, -0.09365738656772446, 0.22496289542565229, -0.59664580012920287, 0.21203301749078954, -0.90645659347575269,
      -0.93757266973642184, -0.16310446648763829, 0.28051140237340205, -0.1398723461167421, -0.026201603009980222, 0.19938196786706941,
      -0.41243700482490003, 0.77875499357238942, -0.23584163232691202, 0.68385708637153075, 0.96079033437326122, -0.25423479844769148,
      -1.6155852507085418, 0.30115663698554868, 1.1296902585771971, 1.6888241391747443, 1.0437730720520051, 0.66541783817583855,
      -0.2921384893010493, -0.0013136092855242758, 0.20811647921066923, -0.15027826196234137, -0.0010008826246159595, 0.17521784569972412,
      -0.15173312153844976, 0.19456376140259476, -0.011868185661795261, 0.44383975220849797, 0.0091263381753438969
   },
   { // 2024 / 30m
      -0.46969533801631086, 1.3335710668458851, 0.082100299960921261, 0.85186533083556093, -0.91432457690637126, 0.45331536625099333,
      1.3709909604417889, -0.12161226602891934, -0.51169040067991922, -0.37659985369692994, -0.0089397032154195089, 0.83079065995494283,
      -0.2173775086022344, -0.39133599850935191, 0.1475985163586564, -0.3001702425835191, 2.1691514154054126, 0.023215357619771712,
      -0.85556149872400689, 0.44015759301476459, 0.33364677404038884, -0.85583033766680205, -0.10930219717110831, -1.0477946337293063,
      -0.60573389271949718, -0.066665632789276952, 0.1624822554925234, -0.09540246546218209, -0.6614009245683542, 0.52498469493084898,
      -0.41917660992957217, 0.32932784158938477, 0.011614337168525201, 0.27832643746880059, 1.2388053441816116, 0.027621730340340836,
      -2.6961058510330234, 0.01755641193726859, 1.4477840480444308, 2.196227910300331, 0.57702309147609299, 0.13443862396672254,
      0.10436696901421441, 0.28349636514580862, 0.036667074860811916, -0.16292567025676558, 0.061047891032007501, 0.11477737050125542,
      -0.10509725180587236, 0.082973945571868254, 0.011322224193370728, 0.44631616583532246, -0.11932590510678941
   },
   { // 2024 / 60m
      -0.55295593357644646, 1.0841623711835866, -0.04066042667730619, 0.86278272116513166, -0.97055943300652447, 0.46710456394890693,
      0.98560878925312434, -0.032300837978183033, -0.057571368585346547, -0.43391945778355451, -0.042113085624058418, 1.3751657691756556,
      -0.18133619289523192, -0.79032229656305109, 0.19848968190429062, -0.41820792288872799, 3.6666126156111267, -0.03337121307342019,
      -0.74203142680603551, 0.37023964861730657, 0.39818919268246517, -3.275964612103353, -0.047528487591689067, -0.58272292067092424,
      -0.081412121496450954, -0.025832477217507817, 1.0986150327406086, -0.18864873350143982, -1.2925163957321371, 0.96095756982517078,
      -0.58403866731993714, -0.13957071584900838, 0.07410234950387995, 0.16472362773737739, 1.3577807345558455, 0.37574582528677747,
      -1.5367208436493065, 0.028094755165707877, 0.3846379332574606, 1.551760585433466, 1.1874107028685936, -0.77403122345614728,
      0.11001913103327556, 0.4603383639077186, 0.027759352963861231, -0.31050043007040057, 0.053571933451338656, -0.017233189339265275,
      0.079525972832813083, 0.11563422130746916, -0.11678917020109383, 0.35312357238516073, -0.06545891705140236
   },
   { // 2025 / 15m
      -0.71912402827139343, 1.6956237707037827, -0.031012432362443158, 0.69803429953982421, -0.34548336631641491, 0.46141380137421384,
      0.84421568503666888, 0.078150319875004232, -0.24189374431813448, -1.0844434993401655, -0.098198538084808121, 1.9427857169678957,
      -0.3149158839994865, 0.49166616166225979, 0.18151584145038258, -0.3561245804832609, 0.086665839401373249, -0.12036495784713089,
      0.13338986711833659, 0.36721329228224692, 0.26810067799266402, -0.91152044877336402, 0.13356037398997991, -0.42941840687206972,
      -0.37951772374220877, -0.0056387675164292867, -0.59809068316475122, -0.22316771640514993, 0.019073278379803445, 0.084979391536917873,
      -0.50230760189404611, 0.40274747852996051, -0.16091036360311642, 0.7090177600450015, 1.1316121334339031, 0.34070485109054272,
      -1.3338005710371876, 0.16126256912562525, 0.26311896365014914, 0.75495206756009281, 0.72189183119522748, 0.73490566818440384,
      -0.29938371777983797, 0.20319447693675369, 0.23295224776634199, 0.061838801166501887, -0.17522343344965088, -0.16254453556197609,
      -0.032664695125247126, 0.11499541693509305, 0.054025255518895102, 0.18691072345553814, 0.023424348876271296
   },
   { // 2025 / 30m
      -0.50661605051658964, 1.2630348547439301, 0.15280273055582475, 0.49089558252672288, -0.69861161254136361, 0.40591598732262313,
      1.4779313413661552, -0.13438330639301899, -0.25592836464594454, -0.70233140382510473, 0.023543955470205869, 1.1456097175566653,
      -0.15952384443449241, -0.23285789331306986, 0.12149385678036527, -0.36134236162486771, 1.6231152608266812, 0.02114052790108752,
      -0.30823066844545988, 0.77612890772346133, 0.27288400538346042, -1.0620123761989677, -0.08489692496394248, -0.64780141547127168,
      -0.056683757692200402, 0.11484824956051834, -0.43954644567015705, -0.09563328971753754, -0.62639520604717569, 0.19179098239994449,
      -0.49118545450395701, 0.0076376856528572335, -0.04207373940570501, 0.49571666773929696, 1.5603762076885519, 0.49241179896131343,
      -1.9638060065981608, -0.080547292636092976, 0.050792211425552833, 1.2882856009299926, 0.34212279680686458, 0.34981212028467629,
      -0.017043778982351758, 0.37080019696641603, 0.12688572077075994, -0.049350709352825484, -0.0099326457601120292, -0.19920327519329112,
      -0.045093461518087581, 0.092499884731218604, 0.073438721796033543, 0.096613049736969075, -0.03100930395570527
   },
   { // 2025 / 60m
      -0.58111054579825128, 1.0866839946237252, -0.034950582868122838, 0.61181917024305943, -0.8933234860626299, 0.43282265189994018,
      1.0595268923280088, -0.095352420909611962, 0.028524106967222414, -0.50454760047782476, 0.058059519512598648, 1.4228413431560722,
      -0.11516679094477342, -0.57449194087102018, 0.34551574944500024, -0.47859366033089701, 2.8742511782501374, -0.072424963700971234,
      -0.41014730947592992, 0.78412970394411874, 0.37890668370285802, -3.0244629644196692, -0.092659357080958626, -0.2251293335712761,
      -0.0064486729049574457, 0.17730930466058631, 0.68479916268701413, -0.094334679139842795, -1.227417060103394, 0.083257705857739103,
      -0.69850291399208519, 0.0065727505916625007, -0.077667346555806635, 0.53539867367793381, 1.5959118251556468, 0.69900938371326971,
      -1.2148085083584346, -0.059520250418675487, -0.7734817933315189, 1.2244354319663131, 0.61768385179553975, -0.29090839650679223,
      0.11215970322538601, 0.55747282526656916, 0.12161979832518449, -0.29899932745177049, 0.062653483426212866, -0.26898774556380389,
      0.0089068398578836389, 0.18522846487166411, 0.0099242194891278751, 0.12432379921224147, -0.0546871201050175
   },
   { // 2026 / 15m
      -0.33478826157374753, 1.443212807630984, -0.056962334915186173, 0.64506557387677355, -0.50134967969065392, 0.20082224187489231,
      0.39495100252478721, 0.082492073384854897, -0.13740882610941341, -0.61698093418247613, 0.22914642011088471, 1.7077267519718069,
      -0.066590420947323134, -0.1457960630466493, 0.0023905131288568561, -0.17603283268951428, 0.45984545538945804, -0.073439134930201447,
      -0.39070450616620755, 0.17302305376511087, 0.11514115935696645, 0.47706424667515107, 0.0096445938093927125, -0.67973653075773877,
      -0.089627545930954927, 0.28844002859980333, -1.3173087909314827, -0.017289494861745747, -0.35661446224461246, 0.26470260568960302,
      -0.29041980940207474, 0.14779587647675174, -0.066455050665083865, 0.48080896789076749, 0.99578953075737908, 0.18692637882523558,
      -1.1933449008247234, 0.024252859001582024, 0.50202174443625058, 0.74328214702342288, -0.33965146355835896, 0.91825841052292023,
      -0.080367250034439092, 0.077554653797913986, 0.11924696651476718, 0.096094402198986781, 0.13800858660161242, -0.28579346323758431,
      -0.080352742517130205, 0.22732193872694131, -0.0040695305016242517, 0.00020703717747731686, -0.015100991742075994
   },
   { // 2026 / 30m
      -0.34814621778030108, 1.0729187900103707, 0.10031866034610179, 0.653335478096708, -0.72517432467237597, 0.22707648541566799,
      1.275631425399572, -0.082500973796112029, -0.33836680006281089, -0.50804203198597941, 0.27871984997200949, 0.82362503697566791,
      -0.1227304246667146, -0.0090896422991458264, -0.086345331368981412, -0.22724215776437323, 1.3582583518000124, 0.018619627288516991,
      -0.47518855749754629, 0.46179596120565425, 0.14748654413812667, 0.54451853766120328, -0.084173533754502511, -1.4915312587173704,
      0.27443624179742321, 0.34897003086794792, -1.6416599091896944, -0.07713644836083991, -0.84195861246447834, 0.68744603791738068,
      -0.31158289595003763, 0.19211916554609665, 0.016578760694421834, -0.0011108043197559617, 1.2496203855707833, 0.19134158463838843,
      -1.4029173796453727, -0.06144150243301176, 0.68772430015657404, 1.1627142322143784, -0.31131580596961933, 0.62849893045526983,
      0.032578909201369396, 0.19651932149087631, 0.10700550394726419, 0.040591212858966365, 0.073653286217745542, -0.34161483644778373,
      -0.046366658761573303, 0.14884967848360237, 0.0015015485701901654, 0.074573701009828269, -0.055496079177650821
   },
   { // 2026 / 60m
      -0.50428288477116745, 0.89562153231589614, 0.018716454902989583, 0.56261612773020808, -0.69163710711262372, 0.30188018709596415,
      0.9098294265205279, -0.057080007987765115, 0.084763828042927369, -0.48999868375616334, 0.27774054115431496, 1.2574044825269828,
      -0.15787147550442615, -0.38558382411534248, 0.033808226210767588, -0.3864062381627173, 2.1321076363733269, -0.015510173090445136,
      -0.42447418827704508, 0.92182137534756148, 0.26360976613894921, -1.1403535122946504, -0.079037503643848442, -1.392038134016474,
      0.30268467660342041, 0.3534452237200208, -0.97009400690684811, -0.14965313760922602, -1.2951519849451971, 1.0073278603422136,
      -0.48272859981946137, 0.12688178532966504, 0.0032514401318348325, 0.20801769730748718, 1.0836128045676827, 0.34052251294043645,
      -0.79391108803372545, -0.068737212041758242, 0.43755225626768612, 0.95386682786125676, -0.12110491753177467, 0.3189375125814205,
      0.049015363822039693, 0.43478511649595553, 0.074321044979981321, -0.21187688919016548, 0.11003629739046901, -0.35871949871756059,
      0.053680196194323446, 0.1455677374986678, -0.03092107943116261, 0.13556257044804285, -0.038340183788612189
   }
};

//+------------------------------------------------------------------+
//| Utility                                                          |
//+------------------------------------------------------------------+
double SafeLog1p(const double x)
{
   return MathLog(1.0 + MathMax(0.0, x));
}

double SigmoidClipped(double z)
{
   if(z > 40.0) z = 40.0;
   if(z < -40.0) z = -40.0;
   return 1.0 / (1.0 + MathExp(-z));
}

int ModelBaseForYear(const int year)
{
   if(year == 2024) return 0;
   if(year == 2025) return 3;
   if(year == 2026) return 6;
   if(year > 2026 && InpAllow2026ModelAfter2026) return 6;
   return -1;
}

double PredictProbability(const int year,const int horizon_slot,const double &features[])
{
   int base = ModelBaseForYear(year);
   if(base < 0 || horizon_slot < 0 || horizon_slot > 2)
      return EMPTY_VALUE;
   int model = base + horizon_slot;
   double z = V8MP_INTERCEPT[model];
   for(int j=0;j<V8MP_FEATURE_COUNT;j++)
      z += V8MP_COEF[model][j] * features[j];
   return SigmoidClipped(z);
}

int YearOf(const datetime t)
{
   MqlDateTime dt;
   if(!TimeToStruct(t,dt)) return 0;
   return dt.year;
}

void DeleteEventObjects()
{
   for(int i=ObjectsTotal(0,0,-1)-1;i>=0;i--)
   {
      string name=ObjectName(0,i,0,-1);
      if(StringFind(name,V8MP_PREFIX)==0)
         ObjectDelete(0,name);
   }
}

string ProbText(const double p)
{
   if(p==EMPTY_VALUE || !MathIsValidNumber(p)) return "N/A";
   return DoubleToString(p,1) + "%";
}

void DrawTriangle(const string suffix,
                  const datetime source_time,
                  const double high_price,
                  const double low_price,
                  const bool above,
                  const color clr,
                  const int stack,
                  const string tooltip)
{
   string name=V8MP_PREFIX+suffix+"_"+IntegerToString((long)source_time);
   if(ObjectFind(0,name)>=0) return;

   double candle_range=MathMax(0.0,high_price-low_price);
   double base_offset=MathMax(_Point*MathMax(1,InpMinMarkerOffsetPoints),candle_range*MathMax(0.0,InpMarkerOffsetFactor));
   double offset=base_offset*(1.0+0.65*stack);
   double price=above ? high_price+offset : low_price-offset;
   int code=above ? 218 : 217; // Wingdings down/up triangular arrow glyphs

   if(!ObjectCreate(0,name,OBJ_ARROW,0,source_time,price)) return;
   ObjectSetInteger(0,name,OBJPROP_ARROWCODE,code);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_WIDTH,MathMax(1,MathMin(5,InpTriangleSize)));
   ObjectSetInteger(0,name,OBJPROP_ANCHOR,above ? ANCHOR_BOTTOM : ANCHOR_TOP);
   ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
   ObjectSetInteger(0,name,OBJPROP_BACK,false);
   ObjectSetString(0,name,OBJPROP_TOOLTIP,tooltip);
}

//+------------------------------------------------------------------+
//| M1 feature engine                                                |
//+------------------------------------------------------------------+
int FindLastRateBefore(const MqlRates &rates[],const datetime t)
{
   int n=ArraySize(rates);
   int lo=0,hi=n-1,ans=-1;
   while(lo<=hi)
   {
      int mid=(lo+hi)/2;
      if(rates[mid].time < t)
      {
         ans=mid;
         lo=mid+1;
      }
      else hi=mid-1;
   }
   return ans;
}

void ComputeRollingHL(const MqlRates &rates[],const int window,double &out[])
{
   int n=ArraySize(rates);
   ArrayResize(out,n);
   ArrayInitialize(out,EMPTY_VALUE);
   if(n<=0 || window<=0) return;

   int qmax[],qmin[];
   int cap=window+2;
   ArrayResize(qmax,cap);
   ArrayResize(qmin,cap);
   int hmax=0,cmax=0,hmin=0,cmin=0;

   for(int i=0;i<n;i++)
   {
      while(cmax>0)
      {
         int back=(hmax+cmax-1)%cap;
         if(rates[qmax[back]].high > rates[i].high) break;
         cmax--;
      }
      qmax[(hmax+cmax)%cap]=i;
      cmax++;
      while(cmax>0 && qmax[hmax] <= i-window)
      {
         hmax=(hmax+1)%cap;
         cmax--;
      }

      while(cmin>0)
      {
         int back=(hmin+cmin-1)%cap;
         if(rates[qmin[back]].low < rates[i].low) break;
         cmin--;
      }
      qmin[(hmin+cmin)%cap]=i;
      cmin++;
      while(cmin>0 && qmin[hmin] <= i-window)
      {
         hmin=(hmin+1)%cap;
         cmin--;
      }

      if(i>=window-1 && cmax>0 && cmin>0)
         out[i]=rates[qmax[hmax]].high-rates[qmin[hmin]].low;
   }
}

double PrefixWindow(const double &prefix[],const int pos,const int window)
{
   int left=pos+1-window;
   if(left<0) return EMPTY_VALUE;
   return prefix[pos+1]-prefix[left];
}

bool BuildHistoricalFeatureCaches(const MqlRates &m1[],
                                  double &psq[],double &prange[],double &pabs[],double &pbody[],
                                  double &hl5[],double &hl15[],double &hl30[],double &hl60[],
                                  double &hl120[],double &hl240[],double &hl480[],double &hl1440[])
{
   int n=ArraySize(m1);
   if(n<1442) return false;
   ArrayResize(psq,n+1); ArrayResize(prange,n+1); ArrayResize(pabs,n+1); ArrayResize(pbody,n+1);
   psq[0]=0.0; prange[0]=0.0; pabs[0]=0.0; pbody[0]=0.0;
   for(int i=0;i<n;i++)
   {
      double dp=(i>0 ? m1[i].close-m1[i-1].close : 0.0);
      double rng=m1[i].high-m1[i].low;
      double body=MathAbs(m1[i].close-m1[i].open);
      psq[i+1]=psq[i]+dp*dp;
      prange[i+1]=prange[i]+rng;
      pabs[i+1]=pabs[i]+MathAbs(dp);
      pbody[i+1]=pbody[i]+body;
   }
   ComputeRollingHL(m1,5,hl5);
   ComputeRollingHL(m1,15,hl15);
   ComputeRollingHL(m1,30,hl30);
   ComputeRollingHL(m1,60,hl60);
   ComputeRollingHL(m1,120,hl120);
   ComputeRollingHL(m1,240,hl240);
   ComputeRollingHL(m1,480,hl480);
   ComputeRollingHL(m1,1440,hl1440);
   return true;
}

double HLAt(const int wi,const int pos,
            const double &hl5[],const double &hl15[],const double &hl30[],const double &hl60[],
            const double &hl120[],const double &hl240[],const double &hl480[],const double &hl1440[])
{
   if(wi==0) return hl5[pos];
   if(wi==1) return hl15[pos];
   if(wi==2) return hl30[pos];
   if(wi==3) return hl60[pos];
   if(wi==4) return hl120[pos];
   if(wi==5) return hl240[pos];
   if(wi==6) return hl480[pos];
   return hl1440[pos];
}

bool BuildFeaturesCached(const MqlRates &m1[],const int pos,
                         const double &psq[],const double &prange[],const double &pabs[],const double &pbody[],
                         const double &hl5[],const double &hl15[],const double &hl30[],const double &hl60[],
                         const double &hl120[],const double &hl240[],const double &hl480[],const double &hl1440[],
                         double &f[])
{
   if(pos<1440 || pos>=ArraySize(m1)) return false;
   ArrayResize(f,V8MP_FEATURE_COUNT);
   double logrv[8],loghl[8];
   int k=0;
   for(int wi=0;wi<8;wi++)
   {
      int w=V8MP_WINS[wi];
      double rv=PrefixWindow(psq,pos,w);
      double rsum=PrefixWindow(prange,pos,w);
      double asum=PrefixWindow(pabs,pos,w);
      double bsum=PrefixWindow(pbody,pos,w);
      double hlt=HLAt(wi,pos,hl5,hl15,hl30,hl60,hl120,hl240,hl480,hl1440);
      if(rv==EMPTY_VALUE || hlt==EMPTY_VALUE) return false;
      logrv[wi]=SafeLog1p(rv);
      loghl[wi]=SafeLog1p(hlt);
      f[k++]=logrv[wi];
      f[k++]=SafeLog1p(rsum);
      f[k++]=loghl[wi];
      f[k++]=SafeLog1p(asum);
      f[k++]=SafeLog1p(bsum);
   }
   double rng=m1[pos].high-m1[pos].low;
   double dp=m1[pos].close-m1[pos-1].close;
   double tr=MathMax(rng,MathMax(MathAbs(m1[pos].high-m1[pos-1].close),MathAbs(m1[pos].low-m1[pos-1].close)));
   f[k++]=SafeLog1p(rng);
   f[k++]=SafeLog1p(tr);
   f[k++]=SafeLog1p(MathAbs(dp));
   f[k++]=logrv[0]-logrv[3]; f[k++]=loghl[0]-loghl[3];
   f[k++]=logrv[1]-logrv[4]; f[k++]=loghl[1]-loghl[4];
   f[k++]=logrv[2]-logrv[5]; f[k++]=loghl[2]-loghl[5];
   f[k++]=logrv[3]-logrv[6]; f[k++]=loghl[3]-loghl[6];
   f[k++]=logrv[4]-logrv[7]; f[k++]=loghl[4]-loghl[7];
   return (k==V8MP_FEATURE_COUNT);
}

bool BuildFeaturesDirect(const datetime decision_time,double &f[])
{
   MqlRates m1[];
   datetime from=decision_time-(datetime)(30*86400);
   datetime to=decision_time-1;
   int copied=CopyRates(_Symbol,PERIOD_M1,from,to,m1);
   if(copied<1442) return false;
   int pos=ArraySize(m1)-1;
   if(m1[pos].time>=decision_time) pos--;
   if(pos<1440) return false;

   ArrayResize(f,V8MP_FEATURE_COUNT);
   double logrv[8],loghl[8];
   int k=0;
   for(int wi=0;wi<8;wi++)
   {
      int w=V8MP_WINS[wi];
      int first=pos-w+1;
      if(first<1) return false;
      double rv=0.0,rsum=0.0,asum=0.0,bsum=0.0;
      double maxh=-DBL_MAX,minl=DBL_MAX;
      for(int i=first;i<=pos;i++)
      {
         double dp=m1[i].close-m1[i-1].close;
         double rng=m1[i].high-m1[i].low;
         rv+=dp*dp;
         rsum+=rng;
         asum+=MathAbs(dp);
         bsum+=MathAbs(m1[i].close-m1[i].open);
         if(m1[i].high>maxh) maxh=m1[i].high;
         if(m1[i].low<minl) minl=m1[i].low;
      }
      logrv[wi]=SafeLog1p(rv);
      loghl[wi]=SafeLog1p(maxh-minl);
      f[k++]=logrv[wi];
      f[k++]=SafeLog1p(rsum);
      f[k++]=loghl[wi];
      f[k++]=SafeLog1p(asum);
      f[k++]=SafeLog1p(bsum);
   }
   double rng=m1[pos].high-m1[pos].low;
   double dp=m1[pos].close-m1[pos-1].close;
   double tr=MathMax(rng,MathMax(MathAbs(m1[pos].high-m1[pos-1].close),MathAbs(m1[pos].low-m1[pos-1].close)));
   f[k++]=SafeLog1p(rng);
   f[k++]=SafeLog1p(tr);
   f[k++]=SafeLog1p(MathAbs(dp));
   f[k++]=logrv[0]-logrv[3]; f[k++]=loghl[0]-loghl[3];
   f[k++]=logrv[1]-logrv[4]; f[k++]=loghl[1]-loghl[4];
   f[k++]=logrv[2]-logrv[5]; f[k++]=loghl[2]-loghl[5];
   f[k++]=logrv[3]-logrv[6]; f[k++]=loghl[3]-loghl[6];
   f[k++]=logrv[4]-logrv[7]; f[k++]=loghl[4]-loghl[7];
   return (k==V8MP_FEATURE_COUNT);
}

//+------------------------------------------------------------------+
//| Probability history                                              |
//+------------------------------------------------------------------+
bool RebuildProbabilityHistory(const int rates_total,const datetime &time[])
{
   ArrayInitialize(Prob15Buffer,EMPTY_VALUE);
   ArrayInitialize(Prob30Buffer,EMPTY_VALUE);
   ArrayInitialize(Prob60Buffer,EMPTY_VALUE);

   datetime cutoff=TimeCurrent()-(datetime)(MathMax(30,InpHistoryDays)*86400);
   int max_shift=rates_total-1;
   while(max_shift>1 && time[max_shift]<cutoff) max_shift--;
   // max_shift is now the first bar inside cutoff (or close to it); include its older neighbor if possible.
   max_shift=MathMin(rates_total-1,max_shift+1);
   datetime oldest=time[max_shift]-(datetime)(30*86400);

   MqlRates m1[];
   int copied=CopyRates(_Symbol,PERIOD_M1,oldest,TimeCurrent(),m1);
   if(copied<1442)
   {
      Print("V8MP: insufficient M1 history: ",copied);
      return false;
   }

   double psq[],prange[],pabs[],pbody[];
   double hl5[],hl15[],hl30[],hl60[],hl120[],hl240[],hl480[],hl1440[];
   if(!BuildHistoricalFeatureCaches(m1,psq,prange,pabs,pbody,hl5,hl15,hl30,hl60,hl120,hl240,hl480,hl1440))
      return false;

   double f[];
   for(int shift=max_shift;shift>=1;shift--)
   {
      if(time[shift]<cutoff) continue;
      datetime decision=time[shift]+PeriodSeconds(PERIOD_M5);
      int pos=FindLastRateBefore(m1,decision);
      if(!BuildFeaturesCached(m1,pos,psq,prange,pabs,pbody,hl5,hl15,hl30,hl60,hl120,hl240,hl480,hl1440,f))
         continue;
      int year=YearOf(decision);
      double p15=PredictProbability(year,0,f);
      double p30=PredictProbability(year,1,f);
      double p60=PredictProbability(year,2,f);
      if(p15!=EMPTY_VALUE) Prob15Buffer[shift]=100.0*p15;
      if(p30!=EMPTY_VALUE) Prob30Buffer[shift]=100.0*p30;
      if(p60!=EMPTY_VALUE) Prob60Buffer[shift]=100.0*p60;
   }
   Prob15Buffer[0]=EMPTY_VALUE;
   Prob30Buffer[0]=EMPTY_VALUE;
   Prob60Buffer[0]=EMPTY_VALUE;
   return true;
}

void UpdateLatestClosedBar(const datetime &time[])
{
   Prob15Buffer[0]=EMPTY_VALUE;
   Prob30Buffer[0]=EMPTY_VALUE;
   Prob60Buffer[0]=EMPTY_VALUE;
   if(ArraySize(time)<2) return;
   datetime decision=time[1]+PeriodSeconds(PERIOD_M5);
   double f[];
   if(!BuildFeaturesDirect(decision,f)) return;
   int year=YearOf(decision);
   double p15=PredictProbability(year,0,f);
   double p30=PredictProbability(year,1,f);
   double p60=PredictProbability(year,2,f);
   if(p15!=EMPTY_VALUE) Prob15Buffer[1]=100.0*p15;
   if(p30!=EMPTY_VALUE) Prob30Buffer[1]=100.0*p30;
   if(p60!=EMPTY_VALUE) Prob60Buffer[1]=100.0*p60;
}

//+------------------------------------------------------------------+
//| Event detection                                                  |
//+------------------------------------------------------------------+
bool BBSeries(const double &close[],const int rates_total,const int shift,const int period,const double mult,
              double &mid,double &upper,double &lower)
{
   if(shift<0 || shift+period>rates_total) return false;
   double sum=0.0;
   for(int k=0;k<period;k++) sum+=close[shift+k];
   mid=sum/period;
   double var=0.0;
   for(int k=0;k<period;k++)
   {
      double d=close[shift+k]-mid;
      var+=d*d;
   }
   double sd=MathSqrt(var/period);
   upper=mid+mult*sd;
   lower=mid-mult*sd;
   return true;
}

void TooltipFromShift(const string event_name,const int shift,string &tooltip)
{
   tooltip=event_name+"\n";
   if(shift>=0 && shift<ArraySize(Prob15Buffer))
   {
      tooltip+="10p <=15m: "+ProbText(Prob15Buffer[shift])+"\n";
      tooltip+="10p <=30m: "+ProbText(Prob30Buffer[shift])+"\n";
      tooltip+="10p <=60m: "+ProbText(Prob60Buffer[shift])+"\n";
   }
   tooltip+="Direction: NOT ESTIMATED";
}

void DrawOneM5EventBar(const int rates_total,const datetime &time[],const double &high[],const double &low[],const double &close[],const int shift)
{
   if(shift<1 || shift+21>=rates_total) return;
   double mid,u,l,pmid,pu,pl;
   if(!BBSeries(close,rates_total,shift,20,2.0,mid,u,l)) return;
   if(!BBSeries(close,rates_total,shift+1,20,2.0,pmid,pu,pl)) return;

   bool tm=(low[shift]<=mid && high[shift]>=mid);
   bool tu=(high[shift]>=u);
   bool tl=(low[shift]<=l);
   bool ptm=(low[shift+1]<=pmid && high[shift+1]>=pmid);
   bool ptu=(high[shift+1]>=pu);
   bool ptl=(low[shift+1]<=pl);

   int above_stack=0,below_stack=0;
   string tip;
   if(InpShowM5UpperBB && tu && !ptu)
   {
      TooltipFromShift("M5 BB20 UPPER CONTACT START",shift,tip);
      DrawTriangle("M5U",time[shift],high[shift],low[shift],true,InpColorM5UpperBB,above_stack++,tip);
   }
   if(InpShowM5LowerBB && tl && !ptl)
   {
      TooltipFromShift("M5 BB20 LOWER CONTACT START",shift,tip);
      DrawTriangle("M5L",time[shift],high[shift],low[shift],false,InpColorM5LowerBB,below_stack++,tip);
   }
   if(InpShowM5MA20Contact && tm && !ptm)
   {
      bool above=(close[shift]<mid); // placement only; NOT a directional label
      TooltipFromShift("M5 SMA20 CONTACT START",shift,tip);
      if(above)
         DrawTriangle("M5MA",time[shift],high[shift],low[shift],true,InpColorM5MA20,above_stack++,tip);
      else
         DrawTriangle("M5MA",time[shift],high[shift],low[shift],false,InpColorM5MA20,below_stack++,tip);
   }
}

bool H1BandsAt(const MqlRates &h1[],const int i,double &u20,double &l20,double &u4,double &l4)
{
   if(i<19 || i<3) return false;
   double mean20=0.0;
   for(int k=i-19;k<=i;k++) mean20+=h1[k].close;
   mean20/=20.0;
   double var20=0.0;
   for(int k=i-19;k<=i;k++) { double d=h1[k].close-mean20; var20+=d*d; }
   double sd20=MathSqrt(var20/20.0);
   u20=mean20+2.0*sd20; l20=mean20-2.0*sd20;

   double mean4=0.0;
   for(int k=i-3;k<=i;k++) mean4+=h1[k].open;
   mean4/=4.0;
   double var4=0.0;
   for(int k=i-3;k<=i;k++) { double d=h1[k].open-mean4; var4+=d*d; }
   double sd4=MathSqrt(var4/4.0);
   u4=mean4+4.0*sd4; l4=mean4-4.0*sd4;
   return true;
}

int ProbabilityShiftForDecision(const datetime decision)
{
   datetime source_m5=decision-PeriodSeconds(PERIOD_M5);
   return iBarShift(_Symbol,PERIOD_M5,source_m5,true);
}

void DrawH1DBFromRates(const MqlRates &h1[],const int i)
{
   double u20,l20,u4,l4;
   if(!H1BandsAt(h1,i,u20,l20,u4,l4)) return;
   bool upper=(h1[i].high>=u20 && h1[i].high>=u4);
   bool lower=(h1[i].low<=l20 && h1[i].low<=l4);
   if(!upper && !lower) return;
   datetime decision=h1[i].time+PeriodSeconds(PERIOD_H1);
   int pshift=ProbabilityShiftForDecision(decision);
   string tip;
   TooltipFromShift("H1 DOUBLE-B CONFIRMED",pshift,tip);
   if(upper)
      DrawTriangle("H1DBU",h1[i].time,h1[i].high,h1[i].low,true,InpColorH1DoubleB,0,tip+"\nSide: UPPER");
   if(lower)
      DrawTriangle("H1DBL",h1[i].time,h1[i].high,h1[i].low,false,InpColorH1DoubleB,0,tip+"\nSide: LOWER");
}

void RebuildEventMarkers(const int rates_total,const datetime &time[],const double &high[],const double &low[],const double &close[])
{
   DeleteEventObjects();
   datetime cutoff=TimeCurrent()-(datetime)(MathMax(30,InpHistoryDays)*86400);

   // M5 event starts on the source candle. The probability plotted on that same M5 candle is known at its close.
   for(int shift=rates_total-22;shift>=1;shift--)
   {
      if(time[shift]<cutoff) continue;
      DrawOneM5EventBar(rates_total,time,high,low,close,shift);
   }

   if(InpShowH1DoubleB)
   {
      MqlRates h1[];
      datetime from=cutoff-(datetime)(10*86400);
      int n=CopyRates(_Symbol,PERIOD_H1,from,TimeCurrent(),h1);
      if(n>25)
      {
         for(int i=19;i<n;i++)
         {
            datetime decision=h1[i].time+PeriodSeconds(PERIOD_H1);
            if(h1[i].time<cutoff || decision>TimeCurrent()) continue;
            DrawH1DBFromRates(h1,i);
         }
      }
   }
   ChartRedraw(0);
}

void UpdateNewestEventMarkers(const int rates_total,const datetime &time[],const double &high[],const double &low[],const double &close[])
{
   DrawOneM5EventBar(rates_total,time,high,low,close,1);
   if(InpShowH1DoubleB)
   {
      MqlRates h1[];
      int n=CopyRates(_Symbol,PERIOD_H1,0,25,h1);
      if(n>=21)
      {
         // CopyRates physical order is oldest -> newest; newest item is current H1, previous item is last closed.
         int i=n-2;
         if(i>=19)
         {
            datetime decision=h1[i].time+PeriodSeconds(PERIOD_H1);
            if(decision<=TimeCurrent()) DrawH1DBFromRates(h1,i);
         }
      }
   }
   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| Indicator lifecycle                                              |
//+------------------------------------------------------------------+
int OnInit()
{
   if(_Period!=PERIOD_M5)
   {
      Print("V8MP: attach this indicator to a GOLD M5 chart. Current period=",EnumToString((ENUM_TIMEFRAMES)_Period));
      return INIT_PARAMETERS_INCORRECT;
   }
   if(MathAbs(InpBarrierPrice-10.0)>1e-9)
   {
      Print("V8MP: this model was trained for a fixed GOLD price barrier of 10.0. Keep InpBarrierPrice=10.0.");
      return INIT_PARAMETERS_INCORRECT;
   }

   SetIndexBuffer(0,Prob15Buffer,INDICATOR_DATA);
   SetIndexBuffer(1,Prob30Buffer,INDICATOR_DATA);
   SetIndexBuffer(2,Prob60Buffer,INDICATOR_DATA);
   ArraySetAsSeries(Prob15Buffer,true);
   ArraySetAsSeries(Prob30Buffer,true);
   ArraySetAsSeries(Prob60Buffer,true);

   PlotIndexSetInteger(0,PLOT_LINE_COLOR,InpColor15m);
   PlotIndexSetInteger(1,PLOT_LINE_COLOR,InpColor30m);
   PlotIndexSetInteger(2,PLOT_LINE_COLOR,InpColor60m);
   PlotIndexSetInteger(0,PLOT_LINE_WIDTH,MathMax(1,MathMin(5,InpLineWidth)));
   PlotIndexSetInteger(1,PLOT_LINE_WIDTH,MathMax(1,MathMin(5,InpLineWidth)));
   PlotIndexSetInteger(2,PLOT_LINE_WIDTH,MathMax(1,MathMin(5,InpLineWidth)));
   PlotIndexSetDouble(0,PLOT_EMPTY_VALUE,EMPTY_VALUE);
   PlotIndexSetDouble(1,PLOT_EMPTY_VALUE,EMPTY_VALUE);
   PlotIndexSetDouble(2,PLOT_EMPTY_VALUE,EMPTY_VALUE);

   IndicatorSetString(INDICATOR_SHORTNAME,"V8 Movement P(10p) 15/30/60m");
   IndicatorSetInteger(INDICATOR_DIGITS,1);
   DeleteEventObjects();
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   DeleteEventObjects();
   if(InpShowStatusComment) Comment("");
}

int OnCalculate(const int rates_total,const int prev_calculated,
                const datetime &time[],const double &open[],const double &high[],const double &low[],const double &close[],
                const long &tick_volume[],const long &volume[],const int &spread[])
{
   ArraySetAsSeries(time,true);
   ArraySetAsSeries(open,true);
   ArraySetAsSeries(high,true);
   ArraySetAsSeries(low,true);
   ArraySetAsSeries(close,true);

   if(rates_total<50) return 0;

   bool need_full=(!g_ready || prev_calculated==0);
   if(g_ready && time[0]==g_last_chart_bar && rates_total!=g_last_rates_total)
      need_full=true; // deeper history was loaded while current bar stayed the same

   if(need_full)
   {
      bool ok=RebuildProbabilityHistory(rates_total,time);
      if(ok)
      {
         RebuildEventMarkers(rates_total,time,high,low,close);
         g_ready=true;
      }
   }
   else if(time[0]!=g_last_chart_bar)
   {
      UpdateLatestClosedBar(time);
      UpdateNewestEventMarkers(rates_total,time,high,low,close);
   }

   g_last_chart_bar=time[0];
   g_last_rates_total=rates_total;

   if(InpShowStatusComment)
   {
      string s="V8 Movement Probability SHADOW | +/-10.0 GOLD price units | Direction NOT estimated";
      s+="\n15m="+ProbText(Prob15Buffer[1])+"  30m="+ProbText(Prob30Buffer[1])+"  60m="+ProbText(Prob60Buffer[1]);
      s+="\nWalk-forward display: 2024<-2022-23, 2025<-2022-24, 2026<-2022-25";
      Comment(s);
   }
   return rates_total;
}
//+------------------------------------------------------------------+
