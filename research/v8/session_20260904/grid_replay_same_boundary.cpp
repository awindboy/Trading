#include <bits/stdc++.h>
using namespace std;
struct Event{ long long t; double S, origin; int dir; string ts;};
struct State{ bool started=false, done=false, cens=false, progressed=false; uint8_t fills=0; double fill[3]={0,0,0}; double pnl=0; long long endt=0; uint8_t cat=0;};
struct Schedule{const char*name; double w[3];};
static inline int dig2(const char*p){return (p[0]-'0')*10+(p[1]-'0');}
static inline int dig3(const char*p){return (p[0]-'0')*100+(p[1]-'0')*10+(p[2]-'0');}
static inline int days_before_month(int m){static int a[]={0,0,31,60,91,121,152,182,213,244,274,305,335};return a[m];}
static inline long long tick_ms(const string&s){ // YYYY.MM.DD\tHH:MM:SS.mmm
 int mo=dig2(s.data()+5), d=dig2(s.data()+8), H=dig2(s.data()+11), M=dig2(s.data()+14), sec=dig2(s.data()+17), ms=dig3(s.data()+20);
 int doy=days_before_month(mo)+d-1; return ((long long)doy*86400+H*3600+M*60+sec)*1000+ms;
}
static inline long long iso_ms(const string&s){int mo=dig2(s.data()+5),d=dig2(s.data()+8),H=dig2(s.data()+11),M=dig2(s.data()+14),sec=dig2(s.data()+17);int doy=days_before_month(mo)+d-1;return ((long long)doy*86400+H*3600+M*60+sec)*1000;}
static inline double field_double(const char*&p){ if(*p=='\t'){++p;return NAN;} char*e=nullptr; double v=strtod(p,&e); p=e; if(*p=='\t')++p; return v; }
static inline void parse_quote(const string&s,double &b,double&a){const char*p=s.c_str()+24; double x=field_double(p), y=field_double(p); if(isfinite(x))b=x;if(isfinite(y))a=y;}
static vector<string> splitcsv(const string&s){vector<string>v; size_t st=0; for(size_t i=0;i<=s.size();i++)if(i==s.size()||s[i]==','){v.emplace_back(s.substr(st,i-st));st=i+1;}return v;}
static inline bool m1_between(const vector<long long>&m1,long long a,long long b){auto it=upper_bound(m1.begin(),m1.end(),a);return it!=m1.end()&&*it<b;}
static inline double be(const State&q,const Schedule&S){double n=0,d=0;for(int i=0;i<q.fills;i++){n+=S.w[i]*q.fill[i];d+=S.w[i];}return n/d;}
static inline double pnl(const State&q,const Schedule&S,int dir,double px){double z=0;for(int i=0;i<q.fills;i++)z+=S.w[i]*dir*(px-q.fill[i]);return z;}
int main(int argc,char**argv){
 string refmode=argc>1?argv[1]:"origin", addfill=argc>2?argv[2]:"quote"; double targetS=argc>3?stod(argv[3]):1.0; string protect=argc>4?argv[4]:"none"; int schedmode=argc>5?stoi(argv[5]):0; string gapmode=argc>6?argv[6]:"censor";
 vector<Event> ev; {ifstream f("/mnt/data/fresh648_events.csv");string l;getline(f,l);while(getline(f,l)){auto a=splitcsv(l);if(a.size()<7)continue;ev.push_back({iso_ms(a[0]),stod(a[2]),stod(a[3]),stoi(a[4]),a[0]});}}
 vector<long long> m1t; {ifstream f("/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv");string l;getline(f,l);while(getline(f,l)){if(l.size()<20||l.compare(0,4,"2024")!=0)continue; // YYYY.MM.DD tab HH:MM:SS no ms
 int mo=dig2(l.data()+5),d=dig2(l.data()+8),H=dig2(l.data()+11),M=dig2(l.data()+14),sec=dig2(l.data()+17);int doy=days_before_month(mo)+d-1;m1t.push_back(((long long)doy*86400+H*3600+M*60+sec)*1000);}}
 vector<Schedule> all={{{"1_1_1"},{1,1,1}},{{"1_.5_.25"},{1,.5,.25}},{{"1_.5_.5"},{1,.5,.5}},{{"1_.25_.25"},{1,.25,.25}},{{"1_2_4"},{1,2,4}}};
 vector<Schedule> sc; if(schedmode==1)sc.push_back(all[0]);else sc=all;
 vector<vector<State>> st(sc.size(),vector<State>(ev.size())); size_t next=0; vector<int> active; double bid=NAN,ask=NAN; long long prevt=-1; long long lines=0;
 vector<string> files;for(auto&p:filesystem::directory_iterator("/mnt/data/ticks2024"))files.push_back(p.path().string());sort(files.begin(),files.end());
 for(auto&fn:files){ifstream f(fn); string l;getline(f,l); while(getline(f,l)){++lines;if(l.size()<25)continue;long long t=tick_ms(l);parse_quote(l,bid,ask);if(!isfinite(bid)||!isfinite(ask))continue;
  if(gapmode=="censor"&&prevt>=0&&t-prevt>120000&&m1_between(m1t,prevt,t)){for(int ei:active)for(size_t si=0;si<sc.size();si++){auto&q=st[si][ei];if(!q.done){q.done=q.cens=true;q.cat=5;q.endt=prevt;}}active.clear();}
  while(next<ev.size()&&ev[next].t<=t){int ei=(int)next;bool gap=(gapmode=="censor")&&m1_between(m1t,ev[ei].t,t);for(size_t si=0;si<sc.size();si++){auto&q=st[si][ei];if(gap){q.done=q.cens=true;q.cat=5;}else{q.started=true;q.fills=1;q.fill[0]=ev[ei].dir>0?ask:bid;}}if(!gap)active.push_back(ei);++next;}
  size_t wr=0;for(size_t ai=0;ai<active.size();ai++){int ei=active[ai];bool alive=false;auto&E=ev[ei];for(size_t si=0;si<sc.size();si++){auto&q=st[si][ei];if(q.done)continue;auto&S=sc[si];int d=E.dir;double ref=refmode=="fill"?q.fill[0]:E.origin;double ex=d>0?bid:ask, ad=d>0?ask:bid;double xe=d*(ex-ref)/E.S, xa=d*(ad-ref)/E.S;
    if(xe<=-1.2){q.pnl=pnl(q,S,d,ex);q.done=true;q.cat=4;q.endt=t;continue;}
    while(q.fills<3){double lev=-.4*q.fills;if(xa<=lev){q.fill[q.fills]=(addfill=="level"?ref+d*lev*E.S:ad);q.fills++;}else break;}
    if(q.fills>=2){double b=be(q,S);if((d>0&&bid>=b)||(d<0&&ask<=b)){q.pnl=pnl(q,S,d,ex);q.done=true;q.cat=2;q.endt=t;continue;}}
    else {if(!q.progressed&&xe>=1.0)q.progressed=true;if(targetS<=1.0000001&&xe>=1.0){q.pnl=pnl(q,S,d,ex);q.done=true;q.cat=1;q.endt=t;continue;}if(targetS>1.0){if(xe>=targetS){q.pnl=pnl(q,S,d,ex);q.done=true;q.cat=1;q.endt=t;continue;}if(q.progressed&&protect!="none"){double pr=(protect=="half"?ref+d*.5*E.S:q.fill[0]);if((d>0&&bid<=pr)||(d<0&&ask>=pr)){q.pnl=pnl(q,S,d,ex);q.done=true;q.cat=3;q.endt=t;continue;}}}}
    alive=true;
   } if(alive)active[wr++]=ei;}active.resize(wr);prevt=t;
 }}
 for(size_t ei=0;ei<ev.size();ei++)for(size_t si=0;si<sc.size();si++){auto&q=st[si][ei];if(!q.done){q.done=q.cens=true;q.cat=5;}}
 cerr<<"lines="<<lines<<" events="<<ev.size()<<"\n";cout<<"PARAM,"<<refmode<<","<<addfill<<","<<targetS<<","<<protect<<"\n";cout<<"schedule,total,completed,censored,tp,be,protected,hard,mean,total_pnl,pf,avg_pos,avg_neg,worst,deep3\n";
 for(size_t si=0;si<sc.size();si++){int cen=0,comp=0,tp=0,br=0,pe=0,hl=0,deep=0,np=0,nn=0;double sum=0,pos=0,neg=0,worst=0;for(size_t ei=0;ei<ev.size();ei++){auto&q=st[si][ei];if(q.cens){cen++;continue;}comp++;sum+=q.pnl;if(q.pnl>0){pos+=q.pnl;np++;}else if(q.pnl<0){neg+=q.pnl;nn++;}worst=min(worst,q.pnl);tp+=q.cat==1;br+=q.cat==2;pe+=q.cat==3;hl+=q.cat==4;deep+=q.fills>=3;}double pf=neg<0?pos/-neg:NAN;cout<<sc[si].name<<","<<ev.size()<<","<<comp<<","<<cen<<","<<tp<<","<<br<<","<<pe<<","<<hl<<","<<sum/comp<<","<<sum<<","<<pf<<","<<(np?pos/np:0)<<","<<(nn?neg/nn:0)<<","<<worst<<","<<deep<<"\n";}
 ofstream fo("/mnt/data/grid_detail_fast.csv");fo<<"event,decision,S,origin,dir,schedule,cat,pnl,fills,censored,end_ms\n";for(size_t si=0;si<sc.size();si++)for(size_t ei=0;ei<ev.size();ei++){auto&q=st[si][ei];fo<<ei<<","<<ev[ei].ts<<","<<ev[ei].S<<","<<ev[ei].origin<<","<<ev[ei].dir<<","<<sc[si].name<<","<<(int)q.cat<<","<<q.pnl<<","<<(int)q.fills<<","<<q.cens<<","<<q.endt<<"\n";}
}
