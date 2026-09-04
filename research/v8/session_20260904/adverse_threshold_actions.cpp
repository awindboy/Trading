#include <bits/stdc++.h>
using namespace std;
struct E{long long t;double S,o;int d;}; struct B{bool done=0,cens=0,deep=0;int n=0;double f[3]={};double final=0;};
struct A{bool trig=0,done=0,cens=0,prog=0;double total=0,px=0;int cat=0;};
static inline int d2(const char*p){return(p[0]-48)*10+p[1]-48;}static inline int d3(const char*p){return(p[0]-48)*100+(p[1]-48)*10+p[2]-48;}static inline int dbm(int m){static int a[]={0,0,31,60,91,121,152,182,213,244,274,305,335};return a[m];}
static inline long long tms(const string&s){int mo=d2(s.data()+5),d=d2(s.data()+8),H=d2(s.data()+11),M=d2(s.data()+14),se=d2(s.data()+17),ms=d3(s.data()+20);return((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+se)*1000+ms;}static inline long long ims(const string&s){int mo=d2(s.data()+5),d=d2(s.data()+8),H=d2(s.data()+11),M=d2(s.data()+14),se=d2(s.data()+17);return((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+se)*1000;}
static inline double fld(const char*&p){if(*p=='\t'){++p;return NAN;}char*e;double v=strtod(p,&e);p=e;if(*p=='\t')++p;return v;}static inline void qp(const string&s,double&b,double&a){const char*p=s.c_str()+24;double x=fld(p),y=fld(p);if(isfinite(x))b=x;if(isfinite(y))a=y;}static vector<string>csv(const string&s){vector<string>v;size_t q=0;for(size_t i=0;i<=s.size();i++)if(i==s.size()||s[i]==','){v.push_back(s.substr(q,i-q));q=i+1;}return v;}static inline bool mb(const vector<long long>&v,long long a,long long b){auto it=upper_bound(v.begin(),v.end(),a);return it!=v.end()&&*it<b;}
static inline double pnl(const B&q,int d,double px,double a=1,double b=1,double c=1){return a*d*(px-q.f[0])+b*d*(px-q.f[1])+c*d*(px-q.f[2]);}
int main(){vector<E>ev;{ifstream f("/mnt/data/fresh648_events.csv");string l;getline(f,l);while(getline(f,l)){auto a=csv(l);ev.push_back({ims(a[0]),stod(a[2]),stod(a[3]),stoi(a[4])});}}vector<long long>m1;{ifstream f("/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv");string l;getline(f,l);while(getline(f,l)){if(l.size()<20||l.compare(0,4,"2024"))continue;int mo=d2(l.data()+5),d=d2(l.data()+8),H=d2(l.data()+11),M=d2(l.data()+14),s=d2(l.data()+17);m1.push_back(((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+s)*1000);}}
 const int NT=3,NA=4;double th[NT]={-.9,-1.0,-1.1};const char*an[NA]={"EXIT","REDUCE_LATEST","REDUCE_HALF","FLIP"};vector<B>b(ev.size());vector<array<array<A,NA>,NT>>A(ev.size());size_t next=0;vector<int>act;double bid=NAN,ask=NAN;long long prev=-1;
 vector<string>fs;for(auto&p:filesystem::directory_iterator("/mnt/data/ticks2024"))fs.push_back(p.path().string());sort(fs.begin(),fs.end());
 for(auto&fn:fs){ifstream f(fn);string l;getline(f,l);while(getline(f,l)){if(l.size()<25)continue;long long tm=tms(l);qp(l,bid,ask);if(!isfinite(bid)||!isfinite(ask))continue;if(prev>=0&&tm-prev>120000&&mb(m1,prev,tm)){for(int i:act){if(!b[i].done)b[i].done=b[i].cens=true;for(int j=0;j<NT;j++)for(int k=0;k<NA;k++)if(A[i][j][k].trig&&!A[i][j][k].done)A[i][j][k].done=A[i][j][k].cens=true;}act.clear();}
 while(next<ev.size()&&ev[next].t<=tm){int i=next++;if(mb(m1,ev[i].t,tm))b[i].done=b[i].cens=true;else{b[i].n=1;b[i].f[0]=ev[i].d>0?ask:bid;act.push_back(i);}}
 size_t wr=0;for(int i:act){auto&E=ev[i];auto&q=b[i];int d=E.d;double ex=d>0?bid:ask,ad=d>0?ask:bid,xe=d*(ex-E.o)/E.S,xa=d*(ad-E.o)/E.S;
  if(!q.deep&&!q.done){if(xe<=-1.2){q.final=(q.n==1?d*(ex-q.f[0]):d*(ex-q.f[0])+d*(ex-q.f[1]));q.done=true;}else{while(q.n<3){double lv=-.4*q.n;if(xa<=lv){q.f[q.n]=ad;q.n++;if(q.n==3){q.deep=true;break;}}else break;}if(!q.deep){if(q.n>=2){double be=(q.f[0]+q.f[1])/2;if((d>0&&bid>=be)||(d<0&&ask<=be)){q.final=d*(ex-q.f[0])+d*(ex-q.f[1]);q.done=true;}}else if(xe>=1){q.final=d*(ex-q.f[0]);q.done=true;}}}}
  if(q.deep){
   // trigger each adverse threshold if not yet triggered
   for(int j=0;j<NT;j++)if(xe<=th[j]&&!A[i][j][0].trig){double cur=pnl(q,d,ex);for(int k=0;k<NA;k++)A[i][j][k].trig=true;A[i][j][0].done=true;A[i][j][0].total=cur;A[i][j][0].cat=3;A[i][j][3].px=ex;}
   // baseline HOLD final
   if(!q.done){double be=(q.f[0]+q.f[1]+q.f[2])/3;if(xe<=-1.2){q.final=pnl(q,d,ex);q.done=true;}else if((d>0&&bid>=be)||(d<0&&ask<=be)){q.final=pnl(q,d,ex);q.done=true;}}
   // action simulations after trigger
   for(int j=0;j<NT;j++)if(A[i][j][0].trig){
    double pxtr=E.o+d*th[j]*E.S; // only for approximate realized? use stored EXIT total to reconstruct exact trigger MTM
    double trig_mtm=A[i][j][0].total; // exact executable
    auto&r=A[i][j][1];if(!r.done){double third_real=trig_mtm - (d*(A[i][j][3].px-q.f[0])+d*(A[i][j][3].px-q.f[1]));double be2=(q.f[0]+q.f[1])/2;if(xe<=-1.2){r.total=third_real+d*(ex-q.f[0])+d*(ex-q.f[1]);r.done=true;r.cat=4;}else if((d>0&&bid>=be2)||(d<0&&ask<=be2)){r.total=third_real+d*(ex-q.f[0])+d*(ex-q.f[1]);r.done=true;r.cat=2;}}
    auto&rh=A[i][j][2];if(!rh.done){double be3=(q.f[0]+q.f[1]+q.f[2])/3;if(xe<=-1.2){rh.total=.5*trig_mtm+.5*pnl(q,d,ex);rh.done=true;rh.cat=4;}else if((d>0&&bid>=be3)||(d<0&&ask<=be3)){rh.total=.5*trig_mtm+.5*pnl(q,d,ex);rh.done=true;rh.cat=2;}}
    auto&fl=A[i][j][3];if(!fl.done){int fd=-d;double fex=fd>0?bid:ask,fx=fd*(fex-fl.px)/E.S;if(!fl.prog&&fx>=1)fl.prog=true;bool stop=fx<=-.4||(fl.prog&&fx<=0);if(fx>=1.5){fl.total=trig_mtm+fd*(fex-fl.px);fl.done=true;fl.cat=5;}else if(stop){fl.total=trig_mtm+fd*(fex-fl.px);fl.done=true;fl.cat=6;}}
   }
  }
  bool alive=!q.done;for(int j=0;j<NT;j++)for(int k=0;k<NA;k++)if(A[i][j][k].trig&&!A[i][j][k].done)alive=true;if(alive)act[wr++]=i;
 }act.resize(wr);prev=tm;
 }}
 for(size_t i=0;i<ev.size();i++){if(!b[i].done)b[i].done=b[i].cens=true;for(int j=0;j<NT;j++)for(int k=0;k<NA;k++)if(A[i][j][k].trig&&!A[i][j][k].done)A[i][j][k].done=A[i][j][k].cens=true;}
 ofstream o("/mnt/data/threshold_actions.csv");o<<"event,threshold,action,hold_censored,action_censored,hold_total,action_total,delta\n";for(size_t i=0;i<ev.size();i++)for(int j=0;j<NT;j++)if(A[i][j][0].trig)for(int k=0;k<NA;k++){auto&a=A[i][j][k];o<<i<<","<<th[j]<<","<<an[k]<<","<<b[i].cens<<","<<a.cens<<","<<b[i].final<<","<<a.total<<","<<a.total-b[i].final<<"\n";}
}
