#include <bits/stdc++.h>
using namespace std;
struct E{long long t;double S;int d;string ts;}; struct St{bool entered=0,done=0,cens=0;double ep=0,pnl=0;int cat=0;long long endt=0;};
static inline int d2(const char*p){return (p[0]-'0')*10+p[1]-'0';} static inline int d3(const char*p){return (p[0]-'0')*100+(p[1]-'0')*10+p[2]-'0';}
static inline int dbm(int m){static int a[]={0,0,31,60,91,121,152,182,213,244,274,305,335};return a[m];}
static long long tms_tick(const string&s){int mo=d2(s.data()+5),da=d2(s.data()+8),H=d2(s.data()+11),M=d2(s.data()+14),S=d2(s.data()+17),ms=d3(s.data()+20);return ((long long)(dbm(mo)+da-1)*86400+H*3600+M*60+S)*1000+ms;}
static long long tms_iso(const string&s){int mo=d2(s.data()+5),da=d2(s.data()+8),H=d2(s.data()+11),M=d2(s.data()+14),S=d2(s.data()+17);return ((long long)(dbm(mo)+da-1)*86400+H*3600+M*60+S)*1000;}
static inline double fd(const char*&p){if(*p=='\t'){++p;return NAN;}char*e;double v=strtod(p,&e);p=e;if(*p=='\t')++p;return v;} static inline void pq(const string&s,double&b,double&a){const char*p=s.c_str()+24;double x=fd(p),y=fd(p);if(isfinite(x))b=x;if(isfinite(y))a=y;}
static vector<string> csv(const string&s){vector<string>v;size_t st=0;for(size_t i=0;i<=s.size();++i)if(i==s.size()||s[i]==','){v.push_back(s.substr(st,i-st));st=i+1;}return v;}
static inline bool m1between(const vector<long long>&v,long long a,long long b){auto it=upper_bound(v.begin(),v.end(),a);return it!=v.end()&&*it<b;}
int main(int ac,char**av){double tp=ac>1?stod(av[1]):.75, sl=ac>2?stod(av[2]):.40; long long horizon=(ac>3?stoll(av[3]):60)*60000LL;
 vector<E> e;{ifstream f("/mnt/data/cluster4_2024_events.csv");string l;getline(f,l);while(getline(f,l)){auto a=csv(l);if(a.size()<4)continue;e.push_back({tms_iso(a[0]),stod(a[1]),stoi(a[3]),a[0]});}} sort(e.begin(),e.end(),[](auto&a,auto&b){return a.t<b.t;});
 vector<long long> m1;{ifstream f("/mnt/data/GOLD#_M1_202201030100_202608282357(5).csv");string l;getline(f,l);while(getline(f,l)){if(l.size()<20||l.compare(0,4,"2024"))continue;int mo=d2(l.data()+5),da=d2(l.data()+8),H=d2(l.data()+11),M=d2(l.data()+14),S=d2(l.data()+17);m1.push_back(((long long)(dbm(mo)+da-1)*86400+H*3600+M*60+S)*1000);}}
 vector<St>s(e.size());vector<int>active;size_t next=0;double bid=NAN,ask=NAN;long long prev=-1;vector<string>files;for(auto&p:filesystem::directory_iterator("/mnt/data/ticks2024"))files.push_back(p.path().string());sort(files.begin(),files.end());
 for(auto&fn:files){ifstream f(fn);string l;getline(f,l);while(getline(f,l)){if(l.size()<25)continue;long long t=tms_tick(l);pq(l,bid,ask);if(!isfinite(bid)||!isfinite(ask))continue;
   if(prev>=0&&t-prev>120000&&m1between(m1,prev,t)){for(int i:active)if(!s[i].done){s[i].done=s[i].cens=1;s[i].cat=4;s[i].endt=prev;}active.clear();}
   while(next<e.size()&&e[next].t<=t){bool gap=m1between(m1,e[next].t,t);if(gap){s[next].done=s[next].cens=1;s[next].cat=4;}else{s[next].entered=1;s[next].ep=e[next].d>0?ask:bid;active.push_back(next);}next++;}
   size_t w=0;for(int id:active){auto&q=s[id];if(q.done)continue;auto&E=e[id];double ex=E.d>0?bid:ask;double x=E.d*(ex-q.ep)/E.S;
      if(x>=tp){q.done=1;q.cat=1;q.pnl=E.d*(ex-q.ep);q.endt=t;continue;} if(x<=-sl){q.done=1;q.cat=2;q.pnl=E.d*(ex-q.ep);q.endt=t;continue;} if(t-E.t>=horizon){q.done=1;q.cens=1;q.cat=3;q.endt=t;continue;} active[w++]=id;} active.resize(w);prev=t;
 }}
 for(auto&q:s)if(!q.done){q.done=q.cens=1;q.cat=4;}
 int win=0,loss=0,cen=0;double pos=0,neg=0,sum=0,worst=0;for(auto&q:s){if(q.cens){cen++;continue;}sum+=q.pnl;if(q.pnl>0){win++;pos+=q.pnl;}else if(q.pnl<0){loss++;neg+=q.pnl;}worst=min(worst,q.pnl);}int comp=win+loss;cout<<"N,"<<e.size()<<"\ncompleted,"<<comp<<"\ncensored,"<<cen<<"\nwin,"<<win<<"\nloss,"<<loss<<"\nWR,"<<(comp?double(win)/comp:NAN)<<"\nmean_dollar,"<<(comp?sum/comp:NAN)<<"\ntotal_dollar,"<<sum<<"\nPF,"<<(neg<0?pos/-neg:NAN)<<"\navg_win,"<<(win?pos/win:0)<<"\navg_loss,"<<(loss?neg/loss:0)<<"\nworst,"<<worst<<"\n";
 ofstream o("/mnt/data/cluster4_tick_detail.csv");o<<"decision,S,dir,entry,cat,pnl,censored,end_ms\n";for(size_t i=0;i<e.size();i++)o<<e[i].ts<<","<<e[i].S<<","<<e[i].d<<","<<s[i].ep<<","<<s[i].cat<<","<<s[i].pnl<<","<<s[i].cens<<","<<s[i].endt<<"\n";
}
