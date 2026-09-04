#include <bits/stdc++.h>
using namespace std;
struct Event{long long t;double S,o;int d;string ts;};
struct B{bool done=0,cens=0,deep=0,dec5=0;int fills=0;double f[3]={};long long ft[3]={},deep_t=0;double deep_mtm=0;double xmin=1e9,xmax=-1e9,x1=NAN,x3=NAN,x5=NAN;};
struct A{bool active=0,done=0,cens=0;double total=0;int cat=0;double flip_entry=0;bool prog=0;};
static inline int d2(const char*p){return(p[0]-48)*10+p[1]-48;}static inline int d3(const char*p){return(p[0]-48)*100+(p[1]-48)*10+p[2]-48;}static inline int dbm(int m){static int a[]={0,0,31,60,91,121,152,182,213,244,274,305,335};return a[m];}
static inline long long tms(const string&s){int mo=d2(s.data()+5),d=d2(s.data()+8),H=d2(s.data()+11),M=d2(s.data()+14),se=d2(s.data()+17),ms=d3(s.data()+20);return((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+se)*1000+ms;}static inline long long ims(const string&s){int mo=d2(s.data()+5),d=d2(s.data()+8),H=d2(s.data()+11),M=d2(s.data()+14),se=d2(s.data()+17);return((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+se)*1000;}
static inline double fld(const char*&p){if(*p=='\t'){++p;return NAN;}char*e;double v=strtod(p,&e);p=e;if(*p=='\t')++p;return v;}static inline void qparse(const string&s,double&b,double&a){const char*p=s.c_str()+24;double x=fld(p),y=fld(p);if(isfinite(x))b=x;if(isfinite(y))a=y;}
static vector<string> csv(const string&s){vector<string>v;size_t q=0;for(size_t i=0;i<=s.size();i++)if(i==s.size()||s[i]==','){v.push_back(s.substr(q,i-q));q=i+1;}return v;}static inline bool m1between(const vector<long long>&v,long long a,long long b){auto it=upper_bound(v.begin(),v.end(),a);return it!=v.end()&&*it<b;}
static inline double bp(const B&q,int d,double px,double w0=1,double w1=1,double w2=1){return w0*d*(px-q.f[0])+w1*d*(px-q.f[1])+w2*d*(px-q.f[2]);}
int main(){vector<Event>ev;{ifstream f("/mnt/data/fresh648_events.csv");string l;getline(f,l);while(getline(f,l)){auto a=csv(l);ev.push_back({ims(a[0]),stod(a[2]),stod(a[3]),stoi(a[4]),a[0]});}}vector<long long>m1;{ifstream f("/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv");string l;getline(f,l);while(getline(f,l)){if(l.size()<20||l.compare(0,4,"2024"))continue;int mo=d2(l.data()+5),d=d2(l.data()+8),H=d2(l.data()+11),M=d2(l.data()+14),s=d2(l.data()+17);m1.push_back(((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+s)*1000);}}
 vector<B>b(ev.size()); const int NA=5; const char*nm[NA]={"HOLD5","REDUCE_LATEST5","REDUCE_HALF5","EXIT5","FLIP5"};vector<array<A,NA>>ac(ev.size());size_t next=0;vector<int>active;double bid=NAN,ask=NAN;long long prev=-1;
 vector<string>fs;for(auto&p:filesystem::directory_iterator("/mnt/data/ticks2024"))fs.push_back(p.path().string());sort(fs.begin(),fs.end());
 auto spawn=[&](int i,double bid,double ask){auto&q=b[i];int d=ev[i].d;double ex=d>0?bid:ask;q.dec5=true;q.x5=d*(ex-ev[i].o)/ev[i].S;for(int k=0;k<NA;k++)ac[i][k].active=true;ac[i][3].done=true;ac[i][3].total=bp(q,d,ex);ac[i][3].cat=3;ac[i][4].flip_entry=ex;};
 for(auto&fn:fs){ifstream f(fn);string l;getline(f,l);while(getline(f,l)){if(l.size()<25)continue;long long t=tms(l);qparse(l,bid,ask);if(!isfinite(bid)||!isfinite(ask))continue;if(prev>=0&&t-prev>120000&&m1between(m1,prev,t)){for(int i:active){b[i].done=b[i].cens=true;if(b[i].dec5)for(int k=0;k<NA;k++)if(!ac[i][k].done)ac[i][k].done=ac[i][k].cens=true;}active.clear();}
  while(next<ev.size()&&ev[next].t<=t){int i=next++;if(m1between(m1,ev[i].t,t))b[i].done=b[i].cens=true;else{b[i].fills=1;b[i].f[0]=ev[i].d>0?ask:bid;b[i].ft[0]=t;active.push_back(i);}}
  size_t wr=0;for(int i:active){auto&E=ev[i];auto&q=b[i];int d=E.d;double ex=d>0?bid:ask,ad=d>0?ask:bid;double xe=d*(ex-E.o)/E.S,xa=d*(ad-E.o)/E.S;
   if(!q.deep&&!q.done){if(xe<=-1.2){q.done=true;}else{while(q.fills<3){double lev=-.4*q.fills;if(xa<=lev){q.f[q.fills]=ad;q.ft[q.fills]=t;q.fills++;if(q.fills==3){q.deep=true;q.deep_t=t;q.deep_mtm=bp(q,d,ex);q.xmin=q.xmax=xe;break;}}else break;}if(!q.deep){if(q.fills>=2){double be=(q.f[0]+q.f[1])/2;if((d>0&&bid>=be)||(d<0&&ask<=be))q.done=true;}else if(xe>=1)q.done=true;}}}
   if(q.deep&&!q.done){long long dt=t-q.deep_t;if(!q.dec5){q.xmin=min(q.xmin,xe);q.xmax=max(q.xmax,xe);if(!isfinite(q.x1)&&dt>=60000)q.x1=xe;if(!isfinite(q.x3)&&dt>=180000)q.x3=xe;}
     // Before 5m decision, resolve HOLD normally if BE/hard hit first.
     if(!q.dec5){double be3=(q.f[0]+q.f[1]+q.f[2])/3;if(xe<=-1.2||((d>0&&bid>=be3)||(d<0&&ask<=be3))){q.done=true;}else if(dt>=300000){spawn(i,bid,ask);}}
     if(q.dec5){
       auto&h=ac[i][0];if(!h.done){double be3=(q.f[0]+q.f[1]+q.f[2])/3;if(xe<=-1.2){h.total=bp(q,d,ex);h.done=true;h.cat=4;}else if((d>0&&bid>=be3)||(d<0&&ask<=be3)){h.total=bp(q,d,ex);h.done=true;h.cat=2;}}
       auto&r=ac[i][1];if(!r.done){double ex5=d>0?(q.x5*E.S/d+E.o): (q.x5*E.S/d+E.o); // not used; reconstruct decision executable from x5
         double px5=E.o+d*q.x5*E.S;double realized=d*(px5-q.f[2]);double be2=(q.f[0]+q.f[1])/2;if(xe<=-1.2){r.total=realized+d*(ex-q.f[0])+d*(ex-q.f[1]);r.done=true;r.cat=4;}else if((d>0&&bid>=be2)||(d<0&&ask<=be2)){r.total=realized+d*(ex-q.f[0])+d*(ex-q.f[1]);r.done=true;r.cat=2;}}
       auto&rh=ac[i][2];if(!rh.done){double px5=E.o+d*q.x5*E.S;double real=.5*bp(q,d,px5),be3=(q.f[0]+q.f[1]+q.f[2])/3;if(xe<=-1.2){rh.total=real+.5*bp(q,d,ex);rh.done=true;rh.cat=4;}else if((d>0&&bid>=be3)||(d<0&&ask<=be3)){rh.total=real+.5*bp(q,d,ex);rh.done=true;rh.cat=2;}}
       auto&fl=ac[i][4];if(!fl.done){int fd=-d;double fex=fd>0?bid:ask;double fx=fd*(fex-fl.flip_entry)/E.S;if(!fl.prog&&fx>=1)fl.prog=true;bool stop=fx<=-.4||(fl.prog&&fx<=0);if(fx>=1.5){fl.total=bp(q,d,E.o+d*q.x5*E.S)+fd*(fex-fl.flip_entry);fl.done=true;fl.cat=5;}else if(stop){fl.total=bp(q,d,E.o+d*q.x5*E.S)+fd*(fex-fl.flip_entry);fl.done=true;fl.cat=6;}}
       bool all=1;for(int k=0;k<NA;k++)if(!ac[i][k].done)all=0;if(all)q.done=true;
     }
   }
   if(!q.done)active[wr++]=i;
  }active.resize(wr);prev=t;
 }}
 for(size_t i=0;i<ev.size();i++){if(!b[i].done)b[i].done=b[i].cens=true;if(b[i].dec5)for(int k=0;k<NA;k++)if(!ac[i][k].done)ac[i][k].done=ac[i][k].cens=true;}
 ofstream o("/mnt/data/deep5_detail.csv");o<<"event,decision,S,dir,elapsed_to_deep_min,fill23_min,x1,x3,x5,xmin5,xmax5,action,censored,cat,total_pnl\n";int nd=0,n5=0;for(size_t i=0;i<ev.size();i++)if(b[i].deep){nd++;if(b[i].dec5){n5++;for(int k=0;k<NA;k++){auto&a=ac[i][k];o<<i<<","<<ev[i].ts<<","<<ev[i].S<<","<<ev[i].d<<","<<(b[i].deep_t-ev[i].t)/60000.0<<","<<(b[i].ft[2]-b[i].ft[1])/60000.0<<","<<b[i].x1<<","<<b[i].x3<<","<<b[i].x5<<","<<b[i].xmin<<","<<b[i].xmax<<","<<nm[k]<<","<<a.cens<<","<<a.cat<<","<<a.total<<"\n";}}}
 cerr<<"deep="<<nd<<" decision5="<<n5<<"\n";
}
