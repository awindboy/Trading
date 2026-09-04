#include <bits/stdc++.h>
using namespace std;
struct Event{long long t;double S,origin;int dir;string ts;};
struct Base{bool done=false,cens=false,deep=false;int fills=0;double fill[3]={};double pnl=0;long long deep_t=0;double deep_bid=0,deep_ask=0,deep_mtm=0;};
struct Act{bool active=false,done=false,cens=false;double pnl=0,qdeep=0;int cat=0;double flip_entry=0;bool flip_prog=false;};
static inline int d2(const char*p){return (p[0]-48)*10+p[1]-48;} static inline int d3(const char*p){return (p[0]-48)*100+(p[1]-48)*10+p[2]-48;}
static inline int dbm(int m){static int a[]={0,0,31,60,91,121,152,182,213,244,274,305,335};return a[m];}
static inline long long tms(const string&s){int mo=d2(s.data()+5),d=d2(s.data()+8),H=d2(s.data()+11),M=d2(s.data()+14),se=d2(s.data()+17),ms=d3(s.data()+20);return ((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+se)*1000+ms;}
static inline long long ims(const string&s){int mo=d2(s.data()+5),d=d2(s.data()+8),H=d2(s.data()+11),M=d2(s.data()+14),se=d2(s.data()+17);return ((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+se)*1000;}
static inline double fld(const char*&p){if(*p=='\t'){++p;return NAN;}char*e;double v=strtod(p,&e);p=e;if(*p=='\t')++p;return v;} static inline void quote(const string&s,double&b,double&a){const char*p=s.c_str()+24;double x=fld(p),y=fld(p);if(isfinite(x))b=x;if(isfinite(y))a=y;}
static vector<string> csv(const string&s){vector<string>v;size_t q=0;for(size_t i=0;i<=s.size();i++)if(i==s.size()||s[i]==','){v.push_back(s.substr(q,i-q));q=i+1;}return v;}
static inline bool m1between(const vector<long long>&v,long long a,long long b){auto it=upper_bound(v.begin(),v.end(),a);return it!=v.end()&&*it<b;}
static inline double basketpnl(const Base&q,int dir,double px,double w0=1,double w1=1,double w2=1){double z=0;if(q.fills>0)z+=w0*dir*(px-q.fill[0]);if(q.fills>1)z+=w1*dir*(px-q.fill[1]);if(q.fills>2)z+=w2*dir*(px-q.fill[2]);return z;}
int main(){
 vector<Event>ev;{ifstream f("/mnt/data/fresh648_events.csv");string l;getline(f,l);while(getline(f,l)){auto a=csv(l);ev.push_back({ims(a[0]),stod(a[2]),stod(a[3]),stoi(a[4]),a[0]});}}
 vector<long long>m1;{ifstream f("/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv");string l;getline(f,l);while(getline(f,l)){if(l.size()<20||l.compare(0,4,"2024"))continue;int mo=d2(l.data()+5),d=d2(l.data()+8),H=d2(l.data()+11),M=d2(l.data()+14),s=d2(l.data()+17);m1.push_back(((long long)(dbm(mo)+d-1)*86400+H*3600+M*60+s)*1000);}}
 vector<Base>b(ev.size()); const int NA=5; // HOLD, REDUCE_LATEST, REDUCE_HALF, EXIT, FLIP
 const char*an[NA]={"HOLD","REDUCE_LATEST","REDUCE_HALF_ALL","EXIT","FLIP"}; vector<array<Act,NA>>A(ev.size());
 size_t next=0;vector<int>active;double bid=NAN,ask=NAN;long long prev=-1,lines=0;
 vector<string>files;for(auto&p:filesystem::directory_iterator("/mnt/data/ticks2024"))files.push_back(p.path().string());sort(files.begin(),files.end());
 auto startacts=[&](int ei,long long t,double bid,double ask){auto&q=b[ei];q.deep=true;q.deep_t=t;q.deep_bid=bid;q.deep_ask=ask;int d=ev[ei].dir;double ex=d>0?bid:ask;q.deep_mtm=basketpnl(q,d,ex);for(int k=0;k<NA;k++){A[ei][k].active=true;A[ei][k].qdeep=q.deep_mtm;} // qdeep stores current MTM for later delta
   A[ei][3].done=true;A[ei][3].pnl=q.deep_mtm;A[ei][3].cat=3; // EXIT total pnl
   A[ei][4].flip_entry=ex; // opposite new order executes at same side used to close original basket
 };
 for(auto&fn:files){ifstream f(fn);string l;getline(f,l);while(getline(f,l)){++lines;if(l.size()<25)continue;long long t=tms(l);quote(l,bid,ask);if(!isfinite(bid)||!isfinite(ask))continue;
   if(prev>=0&&t-prev>120000&&m1between(m1,prev,t)){for(int ei:active){if(!b[ei].done){b[ei].done=b[ei].cens=true;}if(b[ei].deep)for(int k=0;k<NA;k++)if(A[ei][k].active&&!A[ei][k].done){A[ei][k].done=A[ei][k].cens=true;}}active.clear();}
   while(next<ev.size()&&ev[next].t<=t){int ei=(int)next;bool gap=m1between(m1,ev[ei].t,t);if(gap)b[ei].done=b[ei].cens=true;else{b[ei].fills=1;b[ei].fill[0]=ev[ei].dir>0?ask:bid;active.push_back(ei);}++next;}
   size_t wr=0;for(int ei:active){auto&E=ev[ei];auto&q=b[ei];int d=E.dir;double ex=d>0?bid:ask,ad=d>0?ask:bid;double xe=d*(ex-E.origin)/E.S,xa=d*(ad-E.origin)/E.S;
     // If not deep yet, run fixed control to third fill or completion.
     if(!q.deep&&!q.done){if(xe<=-1.2){q.pnl=basketpnl(q,d,ex);q.done=true;}else{while(q.fills<3){double lev=-.4*q.fills;if(xa<=lev){q.fill[q.fills]=ad;q.fills++;if(q.fills==3){startacts(ei,t,bid,ask);break;}}else break;}if(!q.deep){if(q.fills>=2){double be=(q.fill[0]+q.fill[1])/2.0;if((d>0&&bid>=be)||(d<0&&ask<=be)){q.pnl=basketpnl(q,d,ex);q.done=true;}}else if(xe>=1.0){q.pnl=basketpnl(q,d,ex);q.done=true;}}}}
     if(q.deep){
       // HOLD: full 1:1:1 to original weighted BE or hard -1.2S
       auto &h=A[ei][0]; if(!h.done){double be=(q.fill[0]+q.fill[1]+q.fill[2])/3.0;if(xe<=-1.2){h.pnl=basketpnl(q,d,ex);h.done=true;h.cat=4;}else if((d>0&&bid>=be)||(d<0&&ask<=be)){h.pnl=basketpnl(q,d,ex);h.done=true;h.cat=2;}}
       // REDUCE_LATEST: realize third leg now at deep quote, keep first 2, rescue at their BE, hard same boundary
       auto &r=A[ei][1]; if(!r.done){double deep_ex=d>0?q.deep_bid:q.deep_ask;double realized=d*(deep_ex-q.fill[2]);double be2=(q.fill[0]+q.fill[1])/2.0;if(xe<=-1.2){r.pnl=realized+d*(ex-q.fill[0])+d*(ex-q.fill[1]);r.done=true;r.cat=4;}else if((d>0&&bid>=be2)||(d<0&&ask<=be2)){r.pnl=realized+d*(ex-q.fill[0])+d*(ex-q.fill[1]);r.done=true;r.cat=2;}}
       // REDUCE_HALF_ALL: realize half all at deep quote, retain half all, same BE/hard
       auto &rh=A[ei][2]; if(!rh.done){double deep_ex=d>0?q.deep_bid:q.deep_ask;double real=.5*basketpnl(q,d,deep_ex);double be3=(q.fill[0]+q.fill[1]+q.fill[2])/3.0;if(xe<=-1.2){rh.pnl=real+.5*basketpnl(q,d,ex);rh.done=true;rh.cat=4;}else if((d>0&&bid>=be3)||(d<0&&ask<=be3)){rh.pnl=real+.5*basketpnl(q,d,ex);rh.done=true;rh.cat=2;}}
       // FLIP: close initial basket at deep; opposite 1 unit, TP +1.5S / SL -0.4S; after +1S protect at flip entry
       auto &fl=A[ei][4]; if(!fl.done){int fd=-d;double fex=fd>0?bid:ask;double fx=fd*(fex-fl.flip_entry)/E.S; if(!fl.flip_prog&&fx>=1.0)fl.flip_prog=true;bool stop=(fx<=-.4)||(fl.flip_prog&&fx<=0.0);if(fx>=1.5){fl.pnl=q.deep_mtm+fd*(fex-fl.flip_entry);fl.done=true;fl.cat=5;}else if(stop){fl.pnl=q.deep_mtm+fd*(fex-fl.flip_entry);fl.done=true;fl.cat=6;}}
       bool alld=true;for(int k=0;k<NA;k++)if(!A[ei][k].done)alld=false;if(alld)q.done=true;
     }
     if(!q.done)active[wr++]=ei;
   }active.resize(wr);prev=t;
 }}
 for(size_t i=0;i<ev.size();i++){if(!b[i].done)b[i].done=b[i].cens=true;if(b[i].deep)for(int k=0;k<NA;k++)if(!A[i][k].done)A[i][k].done=A[i][k].cens=true;}
 ofstream fo("/mnt/data/deep_actions_detail.csv");fo<<"event,decision,S,dir,deep_t,deep_mtm,action,censored,cat,total_pnl,q_from_deep\n";int ndeep=0;for(size_t i=0;i<ev.size();i++)if(b[i].deep){ndeep++;for(int k=0;k<NA;k++){auto&a=A[i][k];double q=a.pnl-b[i].deep_mtm;fo<<i<<","<<ev[i].ts<<","<<ev[i].S<<","<<ev[i].dir<<","<<b[i].deep_t<<","<<b[i].deep_mtm<<","<<an[k]<<","<<a.cens<<","<<a.cat<<","<<a.pnl<<","<<q<<"\n";}}
 cerr<<"lines="<<lines<<" deep="<<ndeep<<"\n";
 for(int k=0;k<NA;k++){int n=0,cen=0;double s=0,sq=0;for(size_t i=0;i<ev.size();i++)if(b[i].deep){auto&a=A[i][k];if(a.cens){cen++;continue;}n++;s+=a.pnl;sq+=a.pnl-b[i].deep_mtm;}cout<<an[k]<<",N="<<n<<",cens="<<cen<<",mean_total="<<(n?s/n:0)<<",mean_Q="<<(n?sq/n:0)<<"\n";}
}
