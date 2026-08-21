#!/usr/bin/env python3
"""Apply D-149 SP/EM Research V2.

Target: awindboy/Trading exact HEAD b3068c0b445005fe455405ed18fb1f82198231df.
Fail-closed and idempotent. Existing D-149 V1 remains available as a control;
V2 adds SMART_PARTIAL_V2 and ENTRY_SURVIVAL_QUARANTINE_V2.
"""
from __future__ import annotations
from pathlib import Path
import locale
import os
import shutil
import subprocess
import sys

EXPECTED_HEAD = "b3068c0b445005fe455405ed18fb1f82198231df"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

EA = "mt5/experts/MentorDeterministicV1EA.mq5"
EDGE = "mt5/experts/EdgeAuditV1.mqh"
HANDOFF = "docs/ea/HANDOFF.md"
STATE = "docs/ea/STRATEGY_RESEARCH_STATE.md"
BACKLOG = "docs/ea/BACKLOG.md"
DECISIONS = "docs/ea/DECISIONS.md"
TEST_RESULTS = "docs/ea/TEST_RESULTS.md"
D149 = "docs/ea/D149_SP_EM_RESEARCH_V1.md"

TRANSFORMED = [EA, HANDOFF, STATE, BACKLOG, DECISIONS, TEST_RESULTS, D149]
VERIFY_ONLY = [EDGE, "AGENTS.md", "docs/ea/EA_SPEC.md"]
EXPECTED_BLOBS = {
    EA: "362f23a3ae86491c3060864d6250198f08e5760f",
    EDGE: "52f785c22a41295a4b58d8d6f8d79056e6c0c693",
    HANDOFF: "4cd6625217ec27a482e1c050ba1eab3a13832e26",
    STATE: "6c645a462d4f227a0430b76e4a1e22576420a2bd",
    BACKLOG: "62189f9dabd36b6c4bfdb89e15bf497a76c2b97c",
    DECISIONS: "6edce4e1a453fcf4c71a1eb561a2d3b7a0e7e5eb",
    TEST_RESULTS: "490f0f9e856291c24799396c9e584e528f3ec5ec",
    D149: "d812f2dbece6ded7b809fa09784d123c7a1967c1",
    "AGENTS.md": "9dcad4894cd7a995d41dba831b9eb2491feedbaf",
    "docs/ea/EA_SPEC.md": "ee550ae198f7b98f759526dce06dda9a86da95c5",
}

NEW_FILES = {
    "docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md": PACKAGE_ROOT / "payload/docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md",
    "tools/summarize_d149_sp_em_v2.py": PACKAGE_ROOT / "payload/tools/summarize_d149_sp_em_v2.py",
}


def decode_process_output(data: bytes) -> str:
    encodings = ["utf-8-sig", "utf-8", sys.getfilesystemencoding(), locale.getpreferredencoding(False)]
    seen = set()
    for enc in encodings:
        if not enc or enc.lower() in seen:
            continue
        seen.add(enc.lower())
        try:
            return data.decode(enc).strip()
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace").strip()


def find_git_executable() -> str:
    found = shutil.which("git")
    if found:
        return found
    if os.name == "nt":
        candidates = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git/cmd/git.exe",
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git/bin/git.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Git/cmd/git.exe",
        ]
        for p in candidates:
            if str(p) and p.exists():
                return str(p)
    raise RuntimeError("git executable not found")


GIT = find_git_executable()


def run(cwd: Path, *args: str) -> str:
    argv = [GIT if args and args[0] == "git" else args[0], *args[1:]]
    p = subprocess.run(argv, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(argv)} :: {decode_process_output(p.stderr or p.stdout)}")
    return decode_process_output(p.stdout)


def locate_repo() -> Path:
    candidates = [Path.cwd(), Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    seen = set()
    for c in candidates:
        try:
            c = c.resolve()
        except Exception:
            continue
        if c in seen or not c.exists():
            continue
        seen.add(c)
        try:
            root = Path(run(c, "git", "rev-parse", "--show-toplevel")).resolve()
            if (root / EA).exists() and (root / "AGENTS.md").exists():
                return root
        except Exception:
            pass
    raise RuntimeError("Trading Git repository not found")


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def read_file(path: Path) -> str:
    return normalize(path.read_text(encoding="utf-8-sig"))


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalize(text), encoding="utf-8", newline="\n")


def head_text(repo: Path, rel: str) -> str:
    p = subprocess.run([GIT, "show", f"HEAD:{rel}"], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"Unable to read HEAD:{rel}: {decode_process_output(p.stderr or p.stdout)}")
    return normalize(p.stdout.decode("utf-8-sig"))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {n}")
    return text.replace(old, new, 1)


def append_once(text: str, marker: str, block: str) -> str:
    if marker in text:
        return text
    return normalize(text).rstrip() + "\n\n" + block.strip() + "\n"


EMV2_STRUCT = r'''
struct V1EMShadowProbe
  {
   bool              active;
   int               scenario_index;
   string            scenario_id;
   int               direction;
   ENUM_TIMEFRAMES   map_tf;
   string            owner_id;
   string            root_zone_id;
   double            entry_price;
   double            original_sl;
   double            one_r_price;
   double            risk_price;
   bool              filled;
   datetime          armed_at;
   datetime          filled_at;
  };

'''

V2_SCENARIO_FIELDS = r'''
   // D-149 V2 Entry-survival bookkeeping. Research toggle only.
   bool              em_v2_one_r_reached;
   datetime          em_v2_one_r_reached_at;
   double            sp_v2_last_cost_be_target;
'''

V2_GLOBALS = r'''

V1EMShadowProbe g_d149_em_v2_shadow;
int      g_d149_em_v2_global_failures=0;
bool     g_d149_em_v2_quarantine=false;
datetime g_d149_em_v2_quarantine_started_at=0;
long g_d149_em_v2_entry_failures=0;
long g_d149_em_v2_one_r_successes=0;
long g_d149_em_v2_quarantine_entries=0;
long g_d149_em_v2_quarantine_releases=0;
long g_d149_em_v2_blocks_quarantine=0;
long g_d149_em_v2_blocks_no_refresh=0;
long g_d149_em_v2_shadow_armed=0;
long g_d149_em_v2_shadow_filled=0;
long g_d149_em_v2_shadow_success=0;
long g_d149_em_v2_shadow_failure=0;
long g_d149_em_v2_shadow_canceled=0;
long g_d149_em_v2_shadow_censored=0;
long g_d149_sp_v2_protected_partials=0;
long g_d149_sp_v2_strong_partials=0;
long g_d149_sp_v2_full_close_fallbacks=0;
long g_d149_sp_v2_cost_be_moves=0;
long g_d149_sp_v2_cost_be_refreshes=0;
long g_d149_sp_v2_cost_be_unavailable=0;
'''

EMV2_HELPERS = r'''
//+------------------------------------------------------------------+
//| D-149 EM V2 -- entry-survival quarantine / shadow requalification|
//+------------------------------------------------------------------+
bool D149EMV2Mode()
  {
   return InpEpisodeManagementMode==V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2;
  }

bool D149EMV2OriginalMapAuthorityAlive(const V1EMShadowProbe &p)
  {
   int index=-1;
   if(p.map_tf==PERIOD_H1) index=1;
   else if(p.map_tf==PERIOD_M30) index=2;
   if(index<0 || p.owner_id=="") return false;
   return (g_structure[index].owner_id==p.owner_id &&
           TrendDirection(g_structure[index].trend)==p.direction);
  }

bool D149EMV2RootAlive(const V1EMShadowProbe &p)
  {
   if(p.root_zone_id=="") return false;
   int index=FindActiveSourceById(p.root_zone_id);
   return (index>=0 && g_sources[index].kind==V1_SOURCE_ROOT);
  }

void D149EMV2ClearShadow()
  {
   g_d149_em_v2_shadow.active=false;
   g_d149_em_v2_shadow.scenario_index=-1;
   g_d149_em_v2_shadow.scenario_id="";
   g_d149_em_v2_shadow.direction=0;
   g_d149_em_v2_shadow.map_tf=PERIOD_CURRENT;
   g_d149_em_v2_shadow.owner_id="";
   g_d149_em_v2_shadow.root_zone_id="";
   g_d149_em_v2_shadow.entry_price=0.0;
   g_d149_em_v2_shadow.original_sl=0.0;
   g_d149_em_v2_shadow.one_r_price=0.0;
   g_d149_em_v2_shadow.risk_price=0.0;
   g_d149_em_v2_shadow.filled=false;
   g_d149_em_v2_shadow.armed_at=0;
   g_d149_em_v2_shadow.filled_at=0;
  }

void D149EMV2ReleaseQuarantine(const datetime observed_at,const string reason)
  {
   if(!g_d149_em_v2_quarantine) return;
   g_d149_em_v2_quarantine=false;
   g_d149_em_v2_global_failures=0;
   g_d149_em_v2_quarantine_releases++;
   LogLine("D149_EM_V2_QUARANTINE_RELEASED","M1",observed_at,"",
           StringFormat("reason=%s release_requires_causal_plus_1r=true",reason));
   if(g_d149_em_v2_shadow.active)
     {
      LogLine("D149_EM_V2_SHADOW_SUPERSEDED","M1",observed_at,g_d149_em_v2_shadow.scenario_id,
              StringFormat("scenario_id=%s reason=%s",g_d149_em_v2_shadow.scenario_id,reason));
      D149EMV2ClearShadow();
     }
  }

void D149EMV2EnterQuarantine(const datetime observed_at,const string trigger_scenario_id)
  {
   if(g_d149_em_v2_quarantine) return;
   g_d149_em_v2_quarantine=true;
   g_d149_em_v2_quarantine_started_at=observed_at;
   g_d149_em_v2_quarantine_entries++;
   LogLine("D149_EM_V2_QUARANTINE_ENTERED","M1",observed_at,trigger_scenario_id,
           StringFormat("trigger_scenario_id=%s consecutive_entry_failures=%d trigger=SL_BEFORE_PLUS_1R existing_filled_or_pending_not_force_canceled=true",
                        trigger_scenario_id,g_d149_em_v2_global_failures));
  }

bool D149EMV2EpisodeRefreshAvailable(const int scenario_index,string &refresh_reason,datetime &refresh_at)
  {
   refresh_reason="NONE";
   refresh_at=0;
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios)) return false;
   int e=D149EMFindEpisode(g_scenarios[scenario_index].active_map_tf,
                          g_scenarios[scenario_index].owner_id,
                          g_scenarios[scenario_index].direction);
   if(e<0 || g_d149_em_episodes[e].consecutive_losses<=0) return true;
   refresh_at=D149EMLatestRefreshForScenario(scenario_index,refresh_reason);
   return (refresh_at>g_d149_em_episodes[e].last_loss_at &&
           refresh_at>g_d149_em_episodes[e].last_refresh_consumed_at);
  }

void D149EMV2ConsumeEpisodeRefresh(const int scenario_index,const datetime refresh_at)
  {
   if(refresh_at<=0 || scenario_index<0 || scenario_index>=ArraySize(g_scenarios)) return;
   int e=D149EMGetOrCreateEpisode(g_scenarios[scenario_index].active_map_tf,
                                 g_scenarios[scenario_index].owner_id,
                                 g_scenarios[scenario_index].direction);
   if(e<0) return;
   if(refresh_at>g_d149_em_episodes[e].last_refresh_consumed_at)
      g_d149_em_episodes[e].last_refresh_consumed_at=refresh_at;
  }

bool D149EMV2ArmShadow(const int scenario_index,const datetime available_at,const datetime refresh_at,const string refresh_reason)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) || g_d149_em_v2_shadow.active)
      return false;
   double risk=MathAbs(g_scenarios[scenario_index].strategy_entry_price-g_scenarios[scenario_index].normalized_sl);
   if(risk<=0.0) return false;

   D149EMV2ClearShadow();
   g_d149_em_v2_shadow.active=true;
   g_d149_em_v2_shadow.scenario_index=scenario_index;
   g_d149_em_v2_shadow.scenario_id=g_scenarios[scenario_index].id;
   g_d149_em_v2_shadow.direction=g_scenarios[scenario_index].direction;
   g_d149_em_v2_shadow.map_tf=g_scenarios[scenario_index].active_map_tf;
   g_d149_em_v2_shadow.owner_id=g_scenarios[scenario_index].owner_id;
   g_d149_em_v2_shadow.root_zone_id=g_scenarios[scenario_index].root_zone_id;
   g_d149_em_v2_shadow.entry_price=g_scenarios[scenario_index].strategy_entry_price;
   g_d149_em_v2_shadow.original_sl=g_scenarios[scenario_index].normalized_sl;
   g_d149_em_v2_shadow.risk_price=risk;
   g_d149_em_v2_shadow.one_r_price=g_d149_em_v2_shadow.entry_price+(double)g_d149_em_v2_shadow.direction*risk;
   g_d149_em_v2_shadow.filled=false;
   g_d149_em_v2_shadow.armed_at=available_at;
   g_d149_em_v2_shadow.filled_at=0;
   D149EMV2ConsumeEpisodeRefresh(scenario_index,refresh_at);
   g_d149_em_v2_shadow_armed++;
   LogLine("D149_EM_V2_SHADOW_ARMED","M1",available_at,g_d149_em_v2_shadow.scenario_id,
           StringFormat("scenario_id=%s direction=%s map_tf=%s owner_id=%s root_id=%s entry=%.10f sl=%.10f one_r=%.10f refresh_at=%s refresh_reason=%s strategy_entry_used_as_shadow_fill_anchor=true no_broker_order=true",
                        g_d149_em_v2_shadow.scenario_id,DirectionName(g_d149_em_v2_shadow.direction),TfName(g_d149_em_v2_shadow.map_tf),
                        g_d149_em_v2_shadow.owner_id,g_d149_em_v2_shadow.root_zone_id,
                        g_d149_em_v2_shadow.entry_price,g_d149_em_v2_shadow.original_sl,g_d149_em_v2_shadow.one_r_price,
                        refresh_at>0 ? TimeToString(refresh_at,TIME_DATE|TIME_SECONDS) : "NA",refresh_reason));
   return true;
  }

bool D149EMV2AuthorizeOpportunity(const int scenario_index,const datetime available_at,string &block_reason)
  {
   block_reason="";
   if(!D149EMV2Mode() || scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION)
      return true;

   if(g_scenarios[scenario_index].owner_id=="" ||
      (g_scenarios[scenario_index].active_map_tf!=PERIOD_H1 && g_scenarios[scenario_index].active_map_tf!=PERIOD_M30))
     {
      block_reason="EMV2_EPISODE_ID_UNAVAILABLE";
      return false;
     }

   string refresh_reason="NONE";
   datetime refresh_at=0;
   if(!D149EMV2EpisodeRefreshAvailable(scenario_index,refresh_reason,refresh_at))
     {
      block_reason="EMV2_FIRST_ENTRY_FAILURE_REQUIRES_NEW_MAP_DELIVERY";
      g_d149_em_v2_blocks_no_refresh++;
      return false;
     }

   if(g_d149_em_v2_quarantine)
     {
      g_d149_em_v2_blocks_quarantine++;
      if(g_d149_em_v2_shadow.active)
        {
         block_reason="EMV2_QUARANTINE_WAITING_SHADOW";
         return false;
        }
      if(D149EMV2ArmShadow(scenario_index,available_at,refresh_at,refresh_reason))
        {
         block_reason="EMV2_QUARANTINE_SHADOW_ARMED";
         return false;
        }
      block_reason="EMV2_QUARANTINE_SHADOW_ARM_FAILED";
      return false;
     }
   return true;
  }

void D149EMV2OnOpportunitySubmitted(const int scenario_index,const datetime available_at)
  {
   if(!D149EMV2Mode() || scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION)
      return;
   string refresh_reason="NONE";
   datetime refresh_at=0;
   if(D149EMV2EpisodeRefreshAvailable(scenario_index,refresh_reason,refresh_at) && refresh_at>0)
     {
      D149EMV2ConsumeEpisodeRefresh(scenario_index,refresh_at);
      g_d149_em_refresh_retries++;
      LogLine("D149_EM_V2_REFRESH_RETRY","M1",available_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s refresh_at=%s refresh_reason=%s",g_scenarios[scenario_index].id,
                           TimeToString(refresh_at,TIME_DATE|TIME_SECONDS),refresh_reason));
     }
  }

void D149EMV2TrackFilledEntrySurvival(const int scenario_index,const MqlTick &tick)
  {
   if(!D149EMV2Mode() || scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION ||
      g_scenarios[scenario_index].strategy_state!=V1_STRATEGY_FILLED ||
      g_scenarios[scenario_index].em_v2_one_r_reached)
      return;
   double risk=g_scenarios[scenario_index].exit_initial_risk_price;
   if(risk<=0.0) risk=MathAbs(g_scenarios[scenario_index].fill_price-g_scenarios[scenario_index].normalized_sl);
   if(risk<=0.0) return;
   double px=(g_scenarios[scenario_index].direction>0 ? tick.bid : tick.ask);
   double favorable_r=(double)g_scenarios[scenario_index].direction*(px-g_scenarios[scenario_index].fill_price)/risk;
   if(favorable_r<1.0-1.0e-10) return;

   g_scenarios[scenario_index].em_v2_one_r_reached=true;
   g_scenarios[scenario_index].em_v2_one_r_reached_at=(datetime)tick.time;
   g_d149_em_v2_one_r_successes++;
   g_d149_em_v2_global_failures=0;

   int e=D149EMFindEpisode(g_scenarios[scenario_index].active_map_tf,
                          g_scenarios[scenario_index].owner_id,
                          g_scenarios[scenario_index].direction);
   if(e>=0)
     {
      g_d149_em_episodes[e].consecutive_losses=0;
      g_d149_em_episodes[e].hard_locked=false;
     }
   LogLine("D149_EM_V2_REAL_PLUS_1R","M1",(datetime)tick.time,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s favorable_r=%.10f entry_survival_success=true global_failure_streak_reset=true",
                        g_scenarios[scenario_index].id,favorable_r));
   if(g_d149_em_v2_quarantine)
      D149EMV2ReleaseQuarantine((datetime)tick.time,"PREEXISTING_REAL_TRADE_PLUS_1R");
  }

void D149EMV2OnPositionClosed(const int scenario_index,const datetime exit_at,const double realized_net_money,const long exit_reason)
  {
   if(!D149EMV2Mode() || scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION ||
      g_scenarios[scenario_index].execution_divergence)
      return;

   // A server-side structural TP can close the position before the next OnTick
   // iteration records the +1R barrier. Recover that causal success from the
   // terminal deal itself, but only when the actual Fill-based price R is >=1.
   if(!g_scenarios[scenario_index].em_v2_one_r_reached && exit_reason==DEAL_REASON_TP)
     {
      double risk=g_scenarios[scenario_index].exit_initial_risk_price;
      if(risk<=0.0) risk=MathAbs(g_scenarios[scenario_index].fill_price-g_scenarios[scenario_index].normalized_sl);
      if(risk>0.0)
        {
         double favorable_r=(double)g_scenarios[scenario_index].direction*
                            (g_scenarios[scenario_index].exit_price-g_scenarios[scenario_index].fill_price)/risk;
         if(favorable_r>=1.0-1.0e-10)
           {
            g_scenarios[scenario_index].em_v2_one_r_reached=true;
            g_scenarios[scenario_index].em_v2_one_r_reached_at=exit_at;
            g_d149_em_v2_one_r_successes++;
            g_d149_em_v2_global_failures=0;
            int success_episode=D149EMFindEpisode(g_scenarios[scenario_index].active_map_tf,
                                                  g_scenarios[scenario_index].owner_id,
                                                  g_scenarios[scenario_index].direction);
            if(success_episode>=0)
              {
               g_d149_em_episodes[success_episode].consecutive_losses=0;
               g_d149_em_episodes[success_episode].hard_locked=false;
              }
            LogLine("D149_EM_V2_REAL_PLUS_1R","M1",exit_at,g_scenarios[scenario_index].id,
                    StringFormat("scenario_id=%s favorable_r=%.10f entry_survival_success=true observed_at_terminal_tp=true global_failure_streak_reset=true",
                                 g_scenarios[scenario_index].id,favorable_r));
            if(g_d149_em_v2_quarantine)
               D149EMV2ReleaseQuarantine(exit_at,"PREEXISTING_REAL_TRADE_TP_PLUS_1R");
           }
        }
     }

   bool genuine_failure=(exit_reason==DEAL_REASON_SL && !g_scenarios[scenario_index].em_v2_one_r_reached);
   if(!genuine_failure)
     {
      LogLine("D149_EM_V2_RESULT","M1",exit_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s exit_reason=%I64d one_r_reached=%s genuine_entry_failure=false realized_net_money=%.8f",
                           g_scenarios[scenario_index].id,exit_reason,
                           g_scenarios[scenario_index].em_v2_one_r_reached ? "true" : "false",realized_net_money));
      return;
     }

   int e=D149EMGetOrCreateEpisode(g_scenarios[scenario_index].active_map_tf,
                                 g_scenarios[scenario_index].owner_id,
                                 g_scenarios[scenario_index].direction);
   if(e>=0)
     {
      g_d149_em_episodes[e].consecutive_losses++;
      g_d149_em_episodes[e].last_loss_at=exit_at;
      g_d149_em_episodes[e].losses++;
     }
   g_d149_em_v2_entry_failures++;
   g_d149_em_v2_global_failures++;
   LogLine("D149_EM_V2_ENTRY_FAILURE","M1",exit_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s owner_id=%s map_tf=%s direction=%s exit_reason=SL one_r_reached=false episode_failures=%d global_consecutive_entry_failures=%d realized_net_money=%.8f",
                        g_scenarios[scenario_index].id,g_scenarios[scenario_index].owner_id,
                        TfName(g_scenarios[scenario_index].active_map_tf),DirectionName(g_scenarios[scenario_index].direction),
                        e>=0 ? g_d149_em_episodes[e].consecutive_losses : -1,g_d149_em_v2_global_failures,realized_net_money));
   if(g_d149_em_v2_global_failures>=2)
      D149EMV2EnterQuarantine(exit_at,g_scenarios[scenario_index].id);
  }

void D149EMV2ProcessShadowProbe(const MqlTick &tick)
  {
   if(!D149EMV2Mode() || !g_d149_em_v2_shadow.active) return;
   const datetime observed_at=(datetime)tick.time;
   int i=g_d149_em_v2_shadow.scenario_index;
   if(i<0 || i>=ArraySize(g_scenarios))
     {
      g_d149_em_v2_shadow_canceled++;
      LogLine("D149_EM_V2_SHADOW_CANCELED","M1",observed_at,g_d149_em_v2_shadow.scenario_id,"reason=SCENARIO_INDEX_INVALID");
      D149EMV2ClearShadow();
      return;
     }

   if(!g_d149_em_v2_shadow.filled)
     {
      string cancel_reason="";
      if(FinalObjectiveConsumed(g_scenarios[i]) || ObjectiveDeliveredAtTick(g_scenarios[i],tick))
         cancel_reason="OBJECTIVE_DELIVERED";
      else if(!D149EMV2RootAlive(g_d149_em_v2_shadow))
         cancel_reason="ROOT_INVALIDATED";
      else if(!D149EMV2OriginalMapAuthorityAlive(g_d149_em_v2_shadow))
         cancel_reason="DIRECTION_AUTHORITY_LOST";

      if(cancel_reason!="")
        {
         g_d149_em_v2_shadow_canceled++;
         LogLine("D149_EM_V2_SHADOW_CANCELED","M1",observed_at,g_d149_em_v2_shadow.scenario_id,
                 StringFormat("scenario_id=%s reason=%s before_fill=true quarantine_remains=true",
                              g_d149_em_v2_shadow.scenario_id,cancel_reason));
         D149EMV2ClearShadow();
         return;
        }

      bool would_fill=(g_d149_em_v2_shadow.direction>0 ? tick.ask<=g_d149_em_v2_shadow.entry_price : tick.bid>=g_d149_em_v2_shadow.entry_price);
      if(!would_fill) return;
      g_d149_em_v2_shadow.filled=true;
      g_d149_em_v2_shadow.filled_at=observed_at;
      g_d149_em_v2_shadow_filled++;
      LogLine("D149_EM_V2_SHADOW_FILLED","M1",observed_at,g_d149_em_v2_shadow.scenario_id,
              StringFormat("scenario_id=%s shadow_fill=%.10f actual_tick_bid=%.10f actual_tick_ask=%.10f no_broker_order=true",
                           g_d149_em_v2_shadow.scenario_id,g_d149_em_v2_shadow.entry_price,tick.bid,tick.ask));
     }

   double exit_side=(g_d149_em_v2_shadow.direction>0 ? tick.bid : tick.ask);
   bool one_r=(g_d149_em_v2_shadow.direction>0 ? exit_side>=g_d149_em_v2_shadow.one_r_price : exit_side<=g_d149_em_v2_shadow.one_r_price);
   bool sl=(g_d149_em_v2_shadow.direction>0 ? exit_side<=g_d149_em_v2_shadow.original_sl : exit_side>=g_d149_em_v2_shadow.original_sl);
   if(one_r)
     {
      g_d149_em_v2_shadow_success++;
      string sid=g_d149_em_v2_shadow.scenario_id;
      LogLine("D149_EM_V2_SHADOW_PLUS_1R","M1",observed_at,sid,
              StringFormat("scenario_id=%s terminal=REQUALIFY exit_side=%.10f one_r=%.10f quarantine_release=true",
                           sid,exit_side,g_d149_em_v2_shadow.one_r_price));
      D149EMV2ClearShadow();
      D149EMV2ReleaseQuarantine(observed_at,"SHADOW_SETUP_PLUS_1R");
      return;
     }
   if(sl)
     {
      g_d149_em_v2_shadow_failure++;
      LogLine("D149_EM_V2_SHADOW_SL","M1",observed_at,g_d149_em_v2_shadow.scenario_id,
              StringFormat("scenario_id=%s terminal=SHADOW_FAILURE exit_side=%.10f sl=%.10f quarantine_remains=true",
                           g_d149_em_v2_shadow.scenario_id,exit_side,g_d149_em_v2_shadow.original_sl));
      D149EMV2ClearShadow();
     }
  }

void D149EMV2OnTesterEnd(const datetime observed_at)
  {
   if(!D149EMV2Mode() || !g_d149_em_v2_shadow.active) return;
   g_d149_em_v2_shadow_censored++;
   LogLine("D149_EM_V2_SHADOW_CENSORED","M1",observed_at,g_d149_em_v2_shadow.scenario_id,
           StringFormat("scenario_id=%s filled=%s quarantine_remains=true tester_end=true",
                        g_d149_em_v2_shadow.scenario_id,g_d149_em_v2_shadow.filled ? "true" : "false"));
   D149EMV2ClearShadow();
  }

'''

SPV2_HELPERS = r'''
//+------------------------------------------------------------------+
//| D-149 SP V2 -- protected default + cost-adjusted +2R lock       |
//+------------------------------------------------------------------+
bool D149SPV2ExpectedGross(const int direction,const double volume,const double open_price,const double close_price,double &money)
  {
   money=0.0;
   if(volume<=0.0) return false;
   ENUM_ORDER_TYPE type=(direction>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   ResetLastError();
   return OrderCalcProfit(type,_Symbol,volume,open_price,close_price,money);
  }

double D149SPV2KnownCash(const int scenario_index,const ulong position_ticket)
  {
   double cash=0.0;
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios)) return cash;
   ulong position_id=g_scenarios[scenario_index].broker_position_id;
   if(position_id>0)
     {
      datetime from=(g_scenarios[scenario_index].fill_at>86400 ? g_scenarios[scenario_index].fill_at-86400 : 0);
      if(HistorySelect(from,TimeCurrent()+60))
        {
         for(int i=0;i<HistoryDealsTotal();i++)
           {
            ulong deal=HistoryDealGetTicket(i);
            if(deal==0 || HistoryDealGetString(deal,DEAL_SYMBOL)!=_Symbol ||
               (long)HistoryDealGetInteger(deal,DEAL_MAGIC)!=InpMagicNumber ||
               (ulong)HistoryDealGetInteger(deal,DEAL_POSITION_ID)!=position_id)
               continue;
            cash+=HistoryDealGetDouble(deal,DEAL_PROFIT);
            cash+=HistoryDealGetDouble(deal,DEAL_COMMISSION);
            cash+=HistoryDealGetDouble(deal,DEAL_SWAP);
            cash+=HistoryDealGetDouble(deal,DEAL_FEE);
           }
        }
     }
   if(PositionSelectByTicket(position_ticket))
      cash+=PositionGetDouble(POSITION_SWAP);
   return cash;
  }

bool D149SPV2ChooseDefaultCloseVolume(const int scenario_index,
                                      const ulong position_ticket,
                                      const double current_volume,
                                      const double market_price,
                                      double &close_volume,
                                      double &expected_lock_money,
                                      double &expected_lock_r)
  {
   close_volume=0.0;
   expected_lock_money=0.0;
   expected_lock_r=0.0;
   double min_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double eps=MathMax(1.0e-10,step*1.0e-6);
   double risk_money=g_scenarios[scenario_index].actual_fill_risk_money;
   if(risk_money<=0.0) risk_money=g_scenarios[scenario_index].planned_risk_money;
   if(min_volume<=0.0 || step<=0.0 || risk_money<=0.0) return false;
   double known_cash=D149SPV2KnownCash(scenario_index,position_ticket);
   double required_lock=V1_D149_SP_V2_DEFAULT_LOCK_BUFFER_R*risk_money;

   int max_steps=(int)MathFloor((current_volume-min_volume+eps)/step);
   if(max_steps<=0) return false;
   for(int k=1;k<=max_steps;k++)
     {
      double candidate=D147NormalizeVolumeDown((double)k*step);
      double remaining=current_volume-candidate;
      if(candidate<min_volume-eps || remaining<min_volume-eps) continue;
      double now_profit=0.0,sl_profit=0.0;
      if(!D149SPV2ExpectedGross(g_scenarios[scenario_index].direction,candidate,
                                g_scenarios[scenario_index].fill_price,market_price,now_profit))
         continue;
      if(!D149SPV2ExpectedGross(g_scenarios[scenario_index].direction,remaining,
                                g_scenarios[scenario_index].fill_price,g_scenarios[scenario_index].normalized_sl,sl_profit))
         continue;
      double terminal_estimate=known_cash+now_profit+sl_profit;
      if(terminal_estimate+1.0e-8>=required_lock)
        {
         close_volume=candidate;
         expected_lock_money=terminal_estimate;
         expected_lock_r=terminal_estimate/risk_money;
         return true;
        }
     }
   return false;
  }

bool D149SPV2RequestClose(const int scenario_index,
                          const MqlTick &tick,
                          const ulong position_ticket,
                          const double current_volume,
                          const double close_volume,
                          const string action_name,
                          const double expected_lock_money,
                          const double expected_lock_r)
  {
   if(close_volume<=0.0 || current_volume<=0.0) return false;
   datetime observed_at=(datetime)tick.time;
   if(g_scenarios[scenario_index].exit_last_action_attempt_at==observed_at &&
      g_scenarios[scenario_index].exit_last_action_attempt_step==301)
      return false;
   g_scenarios[scenario_index].exit_last_action_attempt_at=observed_at;
   g_scenarios[scenario_index].exit_last_action_attempt_step=301;

   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action=TRADE_ACTION_DEAL;
   request.magic=(ulong)InpMagicNumber;
   request.symbol=_Symbol;
   request.position=position_ticket;
   request.volume=close_volume;
   request.type=(g_scenarios[scenario_index].direction>0 ? ORDER_TYPE_SELL : ORDER_TYPE_BUY);
   double market_reference_price=(g_scenarios[scenario_index].direction>0 ? tick.bid : tick.ask);
   long execution_mode=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_EXEMODE);
   request.price=(execution_mode==SYMBOL_TRADE_EXECUTION_MARKET ? 0.0 : market_reference_price);
   request.type_filling=D147MarketFillingMode();
   request.deviation=0;
   request.comment=StringFormat("D149SP2-%d",scenario_index);

   ResetLastError();
   bool call_ok=OrderSend(request,result);
   bool accepted=(call_ok && IsAcceptableTradeRetcode(result.retcode));
   if(!accepted)
     {
      g_d149_sp_action_rejections++;
      LogLine("D149_SP_V2_CLOSE_REJECTED","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s action=%s state=%s close_volume=%.8f current_volume=%.8f call_ok=%s retcode=%u comment=%s last_error=%d retry=true",
                           g_scenarios[scenario_index].id,action_name,SmartPartialStateName(g_scenarios[scenario_index].sp_state),
                           close_volume,current_volume,call_ok ? "true" : "false",result.retcode,result.comment,GetLastError()));
      return false;
     }

   g_scenarios[scenario_index].sp_partial_done=true;
   g_scenarios[scenario_index].exit_partial_count++;
   g_d149_sp_partials++;
   LogLine("D149_SP_V2_CLOSE_ACCEPTED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s action=%s state=%s requested_volume=%.8f pre_close_volume=%.8f expected_remaining=%.8f execution_price=%.10f expected_lock_money=%.8f expected_lock_r=%.8f original_sl=%.10f structural_tp=%.10f retcode=%u deal=%I64u order=%I64u",
                        g_scenarios[scenario_index].id,action_name,SmartPartialStateName(g_scenarios[scenario_index].sp_state),
                        close_volume,current_volume,MathMax(0.0,current_volume-close_volume),
                        (result.price>0.0 ? result.price : market_reference_price),expected_lock_money,expected_lock_r,
                        g_scenarios[scenario_index].normalized_sl,g_scenarios[scenario_index].final_objective_price,
                        result.retcode,result.deal,result.order));
   return true;
  }

bool D149SPV2RequestFirstProfit(const int scenario_index,const MqlTick &tick,const ulong position_ticket,const double current_volume)
  {
   double min_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double eps=MathMax(1.0e-10,step*1.0e-6);
   double market_price=(g_scenarios[scenario_index].direction>0 ? tick.bid : tick.ask);

   if(g_scenarios[scenario_index].sp_state==V1_SP_STATE_STRONG_RUNNER)
     {
      double close_volume=D147NormalizeVolumeDown(current_volume*V1_D149_SP_STRONG_PARTIAL_FRACTION);
      double remaining=current_volume-close_volume;
      if(close_volume<min_volume-eps || remaining<min_volume-eps || close_volume<=0.0)
        {
         g_scenarios[scenario_index].sp_partial_done=true;
         g_d149_sp_partial_infeasible++;
         LogLine("D149_SP_V2_STRONG_PARTIAL_INFEASIBLE","M1",(datetime)tick.time,g_scenarios[scenario_index].id,
                 StringFormat("scenario_id=%s current_volume=%.8f target_fraction=%.8f normalized_close=%.8f remaining=%.8f action=KEEP_FULL_RUNNER no_full_close_fallback=true",
                              g_scenarios[scenario_index].id,current_volume,V1_D149_SP_STRONG_PARTIAL_FRACTION,close_volume,remaining));
         return false;
        }
      if(D149SPV2RequestClose(scenario_index,tick,position_ticket,current_volume,close_volume,"STRONG_25_PERCENT",0.0,0.0))
        {
         g_d149_sp_v2_strong_partials++;
         return true;
        }
      return false;
     }

   double close_volume=0.0,lock_money=0.0,lock_r=0.0;
   if(D149SPV2ChooseDefaultCloseVolume(scenario_index,position_ticket,current_volume,market_price,close_volume,lock_money,lock_r))
     {
      if(D149SPV2RequestClose(scenario_index,tick,position_ticket,current_volume,close_volume,"DEFAULT_PROTECTED_PARTIAL",lock_money,lock_r))
        {
         g_d149_sp_v2_protected_partials++;
         return true;
        }
      return false;
     }

   // Broker volume granularity can make any true partial impossible. DEFAULT
   // is not the strong-runner state, so use a +1R full-close fallback instead
   // of leaving an unprotected tiny remainder. This is explicit and logged.
   if(current_volume>=min_volume-eps)
     {
      double gross=0.0;
      D149SPV2ExpectedGross(g_scenarios[scenario_index].direction,current_volume,
                            g_scenarios[scenario_index].fill_price,market_price,gross);
      double risk_money=g_scenarios[scenario_index].actual_fill_risk_money;
      if(risk_money<=0.0) risk_money=g_scenarios[scenario_index].planned_risk_money;
      double known_cash=D149SPV2KnownCash(scenario_index,position_ticket);
      double estimate=known_cash+gross;
      double estimate_r=(risk_money>0.0 ? estimate/risk_money : 0.0);
      if(D149SPV2RequestClose(scenario_index,tick,position_ticket,current_volume,current_volume,"DEFAULT_FULL_CLOSE_VOLUME_FALLBACK",estimate,estimate_r))
        {
         g_d149_sp_v2_full_close_fallbacks++;
         return true;
        }
     }
   return false;
  }

bool D149SPV2CostAdjustedTarget(const int scenario_index,
                                const MqlTick &tick,
                                const ulong position_ticket,
                                const double current_volume,
                                double &target_sl,
                                double &known_cash,
                                double &required_remaining_profit)
  {
   target_sl=0.0;
   known_cash=D149SPV2KnownCash(scenario_index,position_ticket);
   required_remaining_profit=0.0;
   double risk_money=g_scenarios[scenario_index].actual_fill_risk_money;
   if(risk_money<=0.0) risk_money=g_scenarios[scenario_index].planned_risk_money;
   if(risk_money<=0.0 || current_volume<=0.0) return false;
   double desired_floor=V1_D149_SP_V2_COST_BE_BUFFER_R*risk_money;
   required_remaining_profit=MathMax(0.0,desired_floor-known_cash);
   double fill=g_scenarios[scenario_index].fill_price;
   double px=(g_scenarios[scenario_index].direction>0 ? tick.bid : tick.ask);
   double fill_tick=(g_scenarios[scenario_index].direction>0 ? NormalizePriceCeilToTick(fill) : NormalizePriceFloorToTick(fill));
   target_sl=fill_tick;
   if(required_remaining_profit<=0.0) return true;

   double max_profit=0.0;
   if(!D149SPV2ExpectedGross(g_scenarios[scenario_index].direction,current_volume,fill,px,max_profit) ||
      max_profit+1.0e-8<required_remaining_profit)
      return false;

   double lo=fill,hi=px;
   if(g_scenarios[scenario_index].direction<0)
     {
      lo=px;
      hi=fill;
     }
   for(int iter=0;iter<48;iter++)
     {
      double mid=(lo+hi)*0.5;
      double p=0.0;
      if(!D149SPV2ExpectedGross(g_scenarios[scenario_index].direction,current_volume,fill,mid,p)) return false;
      if(g_scenarios[scenario_index].direction>0)
        {
         if(p>=required_remaining_profit) hi=mid;
         else lo=mid;
        }
      else
        {
         if(p>=required_remaining_profit) lo=mid;
         else hi=mid;
        }
     }
   double raw=(g_scenarios[scenario_index].direction>0 ? hi : lo);
   target_sl=(g_scenarios[scenario_index].direction>0 ? NormalizePriceCeilToTick(raw) : NormalizePriceFloorToTick(raw));
   if(g_scenarios[scenario_index].direction>0) target_sl=MathMax(target_sl,fill_tick);
   else target_sl=MathMin(target_sl,fill_tick);
   return true;
  }

bool D149SPV2MaintainCostAdjustedBE(const int scenario_index,
                                    const MqlTick &tick,
                                    const ulong position_ticket,
                                    const double current_volume,
                                    const double current_sl,
                                    const double current_tp)
  {
   double target_sl=0.0,known_cash=0.0,required_profit=0.0;
   if(!D149SPV2CostAdjustedTarget(scenario_index,tick,position_ticket,current_volume,target_sl,known_cash,required_profit))
     {
      g_d149_sp_v2_cost_be_unavailable++;
      return false;
     }
   double eps=LiquidityTickSize()*0.5;
   bool already=(g_scenarios[scenario_index].direction>0 ? (current_sl>0.0 && current_sl>=target_sl-eps) : (current_sl>0.0 && current_sl<=target_sl+eps));
   if(already)
     {
      g_scenarios[scenario_index].sp_be_done=true;
      if(g_scenarios[scenario_index].sp_v2_last_cost_be_target==0.0 ||
         (g_scenarios[scenario_index].direction>0 && target_sl>g_scenarios[scenario_index].sp_v2_last_cost_be_target+eps) ||
         (g_scenarios[scenario_index].direction<0 && target_sl<g_scenarios[scenario_index].sp_v2_last_cost_be_target-eps))
        {
         g_scenarios[scenario_index].sp_v2_last_cost_be_target=target_sl;
         LogLine("D149_SP_V2_COST_BE_ALREADY_PROTECTED","M1",(datetime)tick.time,g_scenarios[scenario_index].id,
                 StringFormat("scenario_id=%s current_sl=%.10f required_target=%.10f known_cash=%.8f required_remaining_profit=%.8f",
                              g_scenarios[scenario_index].id,current_sl,target_sl,known_cash,required_profit));
        }
      // Already protected is not an action. Return false so the same tick may
      // still execute the one-time +1R partial if a gap/jump reached +2R first.
      return false;
     }
   if(!D147TrailingTargetLegal(g_scenarios[scenario_index].direction,tick,target_sl)) return false;

   datetime observed_at=(datetime)tick.time;
   if(g_scenarios[scenario_index].exit_last_action_attempt_at==observed_at &&
      g_scenarios[scenario_index].exit_last_action_attempt_step==302)
      return false;
   g_scenarios[scenario_index].exit_last_action_attempt_at=observed_at;
   g_scenarios[scenario_index].exit_last_action_attempt_step=302;

   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action=TRADE_ACTION_SLTP;
   request.magic=(ulong)InpMagicNumber;
   request.symbol=_Symbol;
   request.position=position_ticket;
   request.sl=target_sl;
   request.tp=current_tp;
   ResetLastError();
   bool call_ok=OrderSend(request,result);
   bool accepted=(call_ok && (IsAcceptableTradeRetcode(result.retcode) || result.retcode==TRADE_RETCODE_NO_CHANGES));
   if(!accepted)
     {
      g_d149_sp_action_rejections++;
      LogLine("D149_SP_V2_COST_BE_REJECTED","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s position_ticket=%I64u target_sl=%.10f current_sl=%.10f known_cash=%.8f required_remaining_profit=%.8f call_ok=%s retcode=%u comment=%s last_error=%d retry=true",
                           g_scenarios[scenario_index].id,position_ticket,target_sl,current_sl,known_cash,required_profit,
                           call_ok ? "true" : "false",result.retcode,result.comment,GetLastError()));
      return false;
     }

   bool refresh=g_scenarios[scenario_index].sp_be_done;
   g_scenarios[scenario_index].sp_be_done=true;
   g_scenarios[scenario_index].sp_v2_last_cost_be_target=target_sl;
   g_scenarios[scenario_index].exit_dynamic_sl=target_sl;
   g_d149_sp_v2_cost_be_moves++;
   if(refresh) g_d149_sp_v2_cost_be_refreshes++;
   LogLine("D149_SP_V2_COST_BE_MOVED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s trigger=PLUS_2R_OR_LATER old_sl=%.10f new_sl=%.10f fill=%.10f known_cash=%.8f required_remaining_profit=%.8f cost_buffer_r=%.8f dynamic_forward_only=true structural_tp=%.10f retcode=%u comment=%s",
                        g_scenarios[scenario_index].id,current_sl,target_sl,g_scenarios[scenario_index].fill_price,
                        known_cash,required_profit,V1_D149_SP_V2_COST_BE_BUFFER_R,current_tp,result.retcode,result.comment));
   return true;
  }

void D149SPV2ManageFilledPosition(const int scenario_index,const MqlTick &tick)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].strategy_state!=V1_STRATEGY_FILLED ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION ||
      g_scenarios[scenario_index].exit_initial_risk_price<=0.0)
      return;

   ulong position_ticket=0;
   double open_price=0.0,volume=0.0,current_sl=0.0,current_tp=0.0;
   if(!D147GetManagedPositionState(scenario_index,position_ticket,open_price,volume,current_sl,current_tp)) return;
   double px=(g_scenarios[scenario_index].direction>0 ? tick.bid : tick.ask);
   double favorable_r=(double)g_scenarios[scenario_index].direction*(px-g_scenarios[scenario_index].fill_price)/g_scenarios[scenario_index].exit_initial_risk_price;
   int reached_step=(int)MathFloor(favorable_r+1.0e-10);
   if(reached_step>g_scenarios[scenario_index].exit_highest_r_step_seen)
      g_scenarios[scenario_index].exit_highest_r_step_seen=reached_step;

   if(g_scenarios[scenario_index].exit_highest_r_step_seen>=1 && !g_scenarios[scenario_index].sp_state_frozen)
      D149SPFreezeStateAtOneR(scenario_index,(datetime)tick.time);

   // Once +2R has existed, continuously maintain a forward-only cost-adjusted
   // break-even floor. It can advance for accumulated carry but never retreat.
   if(g_scenarios[scenario_index].exit_highest_r_step_seen>=2)
     {
      if(D149SPV2MaintainCostAdjustedBE(scenario_index,tick,position_ticket,volume,current_sl,current_tp))
         return;
     }

   if(g_scenarios[scenario_index].exit_highest_r_step_seen>=1 &&
      !g_scenarios[scenario_index].sp_partial_done &&
      !g_scenarios[scenario_index].exit_partial_disabled)
      D149SPV2RequestFirstProfit(scenario_index,tick,position_ticket,volume);
  }

'''

HANDOFF_APPEND = r'''
## D-149 V1 result -> V2 revision — 2026-08-21

The GOLD 2025 A/B/C/D research ledgers are now locally validated for the three supplied research variants. Detailed evidence and the pre-registered V2 fix are frozen in:

`docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md`

Key continuation results:

```text
ORIGINAL control: 51 trades / WR 27.45% / avg winner 3.827R / expectancy +0.254R / DD 19.53R / streak 11
SP V1:            51 trades / WR 43.14% / avg winner 1.880R / expectancy +0.315R / DD 11.05R / streak 6
EM V1:            29 trades / WR 27.59% / avg winner 4.842R / expectancy +0.563R / DD 15.13R / streak 14
SP+EM V1:         30 trades / WR 43.33% / avg winner 2.256R / expectancy +0.538R / DD 8.29R / streak 7
```

Interpretation:

- SP V1 is **PROMISING**. The pre-registered strong state separated +2R continuation on GOLD 2025: continuation `STRONG_RUNNER 9/11 = 81.8%` vs `DEFAULT 4/19 = 21.1%`.
- EM V1 is **DEMOTED**. Same-episode concurrency blocking removed many trades without shortening the longest loss streak; EM-only streak worsened to 14.
- The useful EM V1 component is the post-failure fresh-delivery requirement. Concurrent exposure blocking is removed from V2.
- D-148 clean GOLD 2023-2025 remains the Entry-side causal basis: 167 continuation fills, 78 SL-first, 27/78 recovered +1R before map-support loss, including 18 local-source-failure recoveries and 9 same-Root recoveries.

Current build after this package: `1.96R1L12 / SP_EM_RESEARCH_V2`.

V2 adds controls without deleting V1:

```text
V1_EXIT_SMART_PARTIAL_V2
V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2
```

SP V2:
- only EXTERNAL_CONTINUATION is managed;
- strong state remains the same D145/D146 structural rule and keeps the 25% partial;
- DEFAULT chooses the minimum broker-valid +1R close volume whose modeled original-SL fallback retains a small positive gross/cost buffer;
- if a true DEFAULT partial is impossible because of volume granularity, a logged +1R full-close fallback is allowed;
- after +2R the remainder receives a forward-only, current-known-cost-adjusted BE floor, recalculated as carry accumulates;
- structural TP remains frozen.

EM V2:
- no same-episode concurrency block;
- a same episode still needs fresh same-direction map delivery after a genuine Entry failure;
- only `SL before +1R` counts as an EM failure; +1R-then-giveback is an exit problem and does not count;
- two consecutive genuine Entry failures enter global quarantine;
- during quarantine real submissions are blocked and one eligible setup at a time is shadowed with its frozen Entry/SL geometry;
- quarantine ends only after a shadow +1R success or an already-open real trade reaches +1R;
- the successful shadow setup itself remains untraded; the next setup is the first eligible real trade.

V2 is research only. ORIGINAL + EM_OFF remains baseline authority. 2021 remains untouched.
'''

STATE_APPEND = r'''
## D-149 V1 solution result and current V2 hypothesis

GOLD 2025 establishes two different solution priorities.

### Smart Partial

SP V1 improved continuation WR, expectancy, drawdown, and streak simultaneously relative to ORIGINAL while preserving materially more winner size than D147 mechanical PARTIAL. This is the first implemented exit architecture in the current chain that improved GOLD 2025 continuation expectancy above ORIGINAL while also reducing drawdown/streak.

The strong-state separator behaved as intended at the stage where it was discovered:

```text
STRONG_RUNNER: +2R 9/11 = 81.8%
DEFAULT:       +2R 4/19 = 21.1%
```

SP V2 therefore does not mine a new runner threshold. It preserves the structural `current M30 external at/beyond original +2R` rule and fixes two execution/economic defects only: DEFAULT terminal protection and cost-adjusted +2R BE.

### Episode Management

EM V1 did not solve the observed loss clusters. It reduced continuation trade count from 51 to 29 while the longest nonpositive streak increased from 11 to 14. Its 20 concurrency blocks corresponded to only 17 baseline fills and removed approximately `-0.259R` total; the useful six no-refresh blocks corresponded to five baseline fills totaling approximately `-3.146R`.

The next hypothesis is therefore global **Entry-survival quarantine**, not owner-level concurrency suppression. EM V2 counts only `SL before +1R`, quarantines after two consecutive such failures, and requires a causally observed shadow +1R setup before new real risk is allowed.

Do not interpret either V2 rule as strategy authority before multi-year and cross-market validation.
'''

BACKLOG_APPEND = r'''
## P0 — D-149 SP/EM V2 controlled revision

V1 result status:

- [x] MetaEditor compile / tester execution successful for supplied D149 research runs.
- [x] GOLD 2025 SP V1 ledger integrity PASS; 51 continuation fills.
- [x] GOLD 2025 EM V1 ledger integrity PASS; 29 continuation fills.
- [x] GOLD 2025 SP+EM V1 ledger integrity PASS; 30 continuation fills.
- [x] SP V1 classified PROMISING: continuation WR 43.14%, avg winner 1.880R, expectancy +0.315R, DD 11.05R, streak 6.
- [x] Confirm SP strong-state +2R separation on continuation: 9/11 vs 4/19.
- [x] EM V1 classified DEMOTED: longest streak 14 despite large trade suppression.
- [x] Remove same-episode concurrency block from V2 design.
- [x] Retain post-genuine-failure fresh map-delivery gate.

SP V2 implementation:

- [x] preserve V1 SMART_PARTIAL as a control and add `V1_EXIT_SMART_PARTIAL_V2`.
- [x] scope SP V2 to EXTERNAL_CONTINUATION only.
- [x] preserve strong-state rule and 25% strong partial; no new runner threshold fit.
- [x] DEFAULT uses a broker-volume-step search for the minimum partial that models a small positive terminal lock if the remainder returns to original SL.
- [x] DEFAULT may full-close at +1R only when broker volume granularity makes any protected partial impossible; explicit diagnostic required.
- [x] +2R uses current-known-cost-adjusted forward-only BE rather than static Fill BE.
- [x] structural TP remains unchanged.

EM V2 implementation:

- [x] preserve EM V1 as a control and add `V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2`.
- [x] remove same-episode concurrent-exposure veto from V2.
- [x] count only exact-tick real `SL before +1R` as genuine Entry failure.
- [x] reset the global failure streak when a real continuation trade reaches +1R.
- [x] enter quarantine after two consecutive genuine Entry failures.
- [x] keep the same-episode fresh-delivery requirement after a genuine failure.
- [x] during quarantine arm at most one no-broker shadow setup at a time.
- [x] shadow pending validation checks objective delivery, original Root validity, and frozen map-owner authority before simulated fill.
- [x] shadow post-fill terminal is +1R vs original SL using executable-side Bid/Ask.
- [x] shadow +1R releases quarantine; shadow SL keeps quarantine.
- [x] do not force-cancel already-open/pending real exposure when quarantine begins in V2.

Validation still required:

- [ ] MetaEditor compile V2 = 0 errors.
- [ ] ORIGINAL + EM_OFF parity against D149 V1 control.
- [ ] GOLD 2025 SP V2 isolated.
- [ ] GOLD 2025 EM V2 isolated.
- [ ] GOLD 2025 SP V2 + EM V2 combined.
- [ ] Compare V1 vs V2 opportunity membership, WR, avg winner, expectancy, DD, streak, quarantine time, shadow validation cost, and winner concentration.
- [ ] If 2025 V2 is coherent, run GOLD 2023 and 2024 without changing constants.
- [ ] Cross-market validation only after GOLD multi-year direction is known.

Do not tune the two-failure quarantine count, 25% strong fraction, or M30 structural strong-state rule from GOLD 2025 after seeing V2 results.
'''

DECISIONS_APPEND = r'''
## D-149B — D149 V1 result classification and V2 architecture freeze

Date: 2026-08-21  
Status: ACTIVE RESEARCH DECISION / NO BASELINE AUTHORITY

### Evidence

GOLD 2025 D149 V1 continuation:

```text
ORIGINAL: 51 / WR 27.45% / avg winner 3.827R / expectancy +0.254R / DD 19.53R / streak 11
SP V1:    51 / WR 43.14% / avg winner 1.880R / expectancy +0.315R / DD 11.05R / streak 6
EM V1:    29 / WR 27.59% / avg winner 4.842R / expectancy +0.563R / DD 15.13R / streak 14
SP+EM V1: 30 / WR 43.33% / avg winner 2.256R / expectancy +0.538R / DD 8.29R / streak 7
```

SP V1 strong continuation state delivered +2R on `9/11`, compared with `4/19` DEFAULT. This validates use of the previously generalized D145/D146 +1R geometry as a runner-management state on this development year, not as an Entry filter.

EM V1 is demoted because it did not shorten the isolated EM loss streak. The same-owner concurrency veto is specifically rejected for V2. Its 20 blocks mapped to 17 baseline fills totaling only about `-0.259R`, while the fresh-delivery gate mapped to five blocked baseline fills totaling about `-3.146R` and remains worth testing.

### Decision

1. Preserve V1 modes as controls.
2. Add `SMART_PARTIAL_V2`, continuation only.
3. Strong runner rule and 25% fraction remain unchanged; no 2025 threshold re-fit.
4. DEFAULT uses minimum broker-valid protected realization rather than a blind 50% fraction. The target is a small positive modeled lock under original-SL fallback, not a fitted return optimum.
5. When DEFAULT cannot be partially realized because the symbol volume step cannot leave a valid remainder, a logged full +1R close is allowed. This is an execution-granularity fallback, not the normal architecture.
6. After +2R, maintain a forward-only cost-adjusted BE floor using current-known realized cash/carry. It may advance with negative carry and never retreat. Frozen structural TP remains.
7. Add `ENTRY_SURVIVAL_QUARANTINE_V2` for EM. A genuine EM failure is only `original SL before +1R`.
8. Two consecutive genuine Entry failures trigger global quarantine. This count is pre-registered from the user's objective of tolerating one/two losses before suppressing the rest; do not optimize it on GOLD 2025.
9. Quarantine is not released by elapsed time, owner change alone, or a score. It requires an eligible shadow setup to reach +1R before its original SL, or an already-open real trade to do so.
10. The validating shadow setup itself is not traded. This intentionally pays one missed winner as a causal requalification cost.
11. EM V2 retains the first-failure fresh same-direction map-delivery gate but removes same-owner concurrency suppression and owner hard-lock as primary controls.
12. Existing pending/filled positions are not force-canceled when quarantine begins in V2; this isolates authorization of new risk from lifecycle cancellation semantics.
13. ORIGINAL + EM_OFF remains baseline. AGENTS/EA_SPEC authority is unchanged. 2021 remains untouched.
'''

TEST_APPEND = r'''
## 2026-08-21 — D-149 GOLD 2025 SP / EM V1 result and V2 handoff

User-provided ledgers:

```text
GOLD_SP.csv
GOLD_EM.csv
GOLD_SPEM.csv
```

All three D149 ledgers passed the supplied D149 integrity analyzer and reported:

```text
execution divergence = 0
cancel rejected = 0
unresolved = 0
```

Continuation performance:

| Variant | Trades | Wins | WR | Avg winner | Avg loser | Expectancy | Total | Max DD | Longest nonpositive streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ORIGINAL control | 51 | 14 | 27.45% | +3.827R | -1.099R | +0.254R | +12.934R | 19.53R | 11 |
| SP V1 | 51 | 22 | 43.14% | +1.880R | -0.872R | +0.315R | +16.071R | 11.05R | 6 |
| EM V1 | 29 | 8 | 27.59% | +4.842R | -1.067R | +0.563R | +16.339R | 15.13R | 14 |
| SP+EM V1 | 30 | 13 | 43.33% | +2.256R | -0.775R | +0.538R | +16.149R | 8.29R | 7 |

The EM expectancy numbers are not sufficient for promotion because EM V1 removed a large share of trades and worsened its isolated longest streak. It must be judged by membership and streak behavior, not only expectancy per remaining trade.

### SP V1

Continuation +1R state counts:

```text
STRONG_RUNNER = 11
DEFAULT = 19
```

Observed +2R / BE trigger:

```text
STRONG_RUNNER 9/11 = 81.8%
DEFAULT       4/19 = 21.1%
```

This supports the D145/D146 structural strong-state concept for runner management on GOLD 2025.

SP V1 still exposed two economic defects:

1. Five continuation DEFAULT trades that had reached +1R still finished slightly negative after the 50% partial / remainder outcome and costs/slippage.
2. One STRONG trade reached +2R and moved the remainder to Fill BE but still closed aggregate-negative (`exit profit +22.48`, `swap -32.05`, net `-9.57`, approximately `-0.105R`). Static price BE is therefore not sufficient for the stated no-negative-lock intent under carry.

SP V2 addresses these defects without changing the strong-state threshold.

### EM V1

```text
same-episode concurrent blocks = 20
first-loss/no-refresh blocks = 6
```

Mapping the blocked scenario IDs back to the clean ORIGINAL population:

```text
concurrency blocks -> 17 baseline fills / 5 winners / 12 losers / about -0.259R total
no-refresh blocks  ->  5 baseline fills / 1 winner  /  4 losers / about -3.146R total
```

The concurrency rule therefore removed many opportunities for little net loss avoidance and is rejected for V2. The post-failure fresh-delivery gate remains promising.

The EM-only longest streak was 14, demonstrating that the dominant long loss cluster can cross owner episodes. EM V2 therefore moves the primary risk unit from `same owner episode` to `global consecutive Entry-survival failures` while retaining a local fresh-delivery gate.

### D148 / loss-cluster context retained

Clean GOLD 2023-2025 D148 continuation:

```text
167 fills
89 immediate +1R = 53.3%
78 SL-first = 46.7%
27/78 recovered original +1R before H1/M30 support loss = 34.6%
51/78 lost map support first = 65.4%
18/27 recovery cases invalidated the original Root first
9/27 kept the original Root through recovery
```

Long realized-loss streaks are not a single Entry-failure population: earlier sequence analysis found both repeated structural exposure and +1R giveback inside the streaks. This is why SP and EM remain separate controls.

Classification:

```text
SP V1 = PROMISING / KEEP AS CONTROL
EM V1 = DEMOTED / KEEP AS NEGATIVE CONTROL
SP V2 = IMPLEMENTED / VALIDATION PENDING
EM V2 = IMPLEMENTED / VALIDATION PENDING
baseline authority = UNCHANGED
```
'''

D149_DOC_APPEND = r'''
## 12. GOLD 2025 V1 result — completed 2026-08-21

D149 V1 is no longer validation-pending. The supplied GOLD 2025 SP, EM, and SP+EM ledgers all passed event integrity with zero execution divergence/cancel rejection.

Continuation:

```text
SP V1    51 trades / WR 43.14% / avg winner 1.880R / expectancy +0.315R / DD 11.05R / streak 6
EM V1    29 trades / WR 27.59% / avg winner 4.842R / expectancy +0.563R / DD 15.13R / streak 14
SP+EM V1 30 trades / WR 43.33% / avg winner 2.256R / expectancy +0.538R / DD 8.29R / streak 7
```

The SP structural state separated +2R continuation strongly on this year (`STRONG 9/11`, `DEFAULT 4/19`). SP V1 is therefore retained as a promising control.

EM V1 failed its main purpose. Same-episode concurrency suppression greatly reduced trade count but did not suppress the long loss cluster. EM V1 is retained only as a negative/control variant.

The exact result and V2 contract are in `D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md`.

## 13. V2 revision

Build target: `1.96R1L12 / SP_EM_RESEARCH_V2`.

New modes preserve V1 numeric identities and controls:

```text
V1_EXIT_SMART_PARTIAL_V2
V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2
```

No V2 rule changes PLAN, Root/Sweep/CHoCH/FVG authorization, initial Entry, initial normalized SL, frozen structural TP, or baseline mode.
'''


def transform_ea(text: str) -> str:
    t=normalize(text)
    t=replace_once(t,
        '#property description "Mentor deterministic V1 EA - D-149 SP + EM research harness"\n',
        '#property description "Mentor deterministic V1 EA - D-149 SP + EM research V2 harness"\n',
        'property description')

    old_exit='''enum V1ExitManagementMode\n  {\n   V1_EXIT_ORIGINAL=0,\n   V1_EXIT_R_STEP_TRAILING,\n   V1_EXIT_R_STEP_PARTIAL,\n   V1_EXIT_SMART_PARTIAL\n  };\n'''
    new_exit='''enum V1ExitManagementMode\n  {\n   V1_EXIT_ORIGINAL=0,\n   V1_EXIT_R_STEP_TRAILING,\n   V1_EXIT_R_STEP_PARTIAL,\n   V1_EXIT_SMART_PARTIAL,\n   V1_EXIT_SMART_PARTIAL_V2\n  };\n'''
    t=replace_once(t,old_exit,new_exit,'exit enum V2')

    old_em='''enum V1EpisodeManagementMode\n  {\n   V1_EM_OFF=0,\n   V1_EM_CAUSAL_EPISODE_V1\n  };\n'''
    new_em='''enum V1EpisodeManagementMode\n  {\n   V1_EM_OFF=0,\n   V1_EM_CAUSAL_EPISODE_V1,\n   V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2\n  };\n'''
    t=replace_once(t,old_em,new_em,'EM enum V2')

    old_params='''// D-149 V1 parameters are frozen research constants, not optimizer inputs.\n#define V1_D149_SP_STRONG_PARTIAL_FRACTION 0.25\n#define V1_D149_SP_DEFAULT_PARTIAL_FRACTION 0.50\n#define V1_D149_SP_STRONG_ROOM_R           1.00\n'''
    new_params=old_params+'''\n// D-149 V2 constants are architecture guards, not optimizer inputs.\n#define V1_D149_SP_V2_DEFAULT_LOCK_BUFFER_R 0.05\n#define V1_D149_SP_V2_COST_BE_BUFFER_R      0.01\n'''
    t=replace_once(t,old_params,new_params,'V2 constants')

    old_struct='''struct V1EMEpisodeState\n  {\n   bool              valid;\n   ENUM_TIMEFRAMES   map_tf;\n   string            owner_id;\n   int               direction;\n   int               consecutive_losses;\n   bool              hard_locked;\n   datetime          last_loss_at;\n   datetime          last_refresh_consumed_at;\n   datetime          last_authorized_at;\n   int               wins;\n   int               losses;\n   int               submitted;\n  };\n\n'''
    t=replace_once(t,old_struct,old_struct+EMV2_STRUCT,'EM V2 shadow struct')

    old_fields='''   bool              sp_partial_done;\n   bool              sp_be_done;\n'''
    t=replace_once(t,old_fields,old_fields+V2_SCENARIO_FIELDS,'V2 scenario fields')

    globals_anchor='''long g_d149_em_hard_locks=0;\n\nstring SmartPartialStateName(const int state)\n'''
    t=replace_once(t,globals_anchor,'long g_d149_em_hard_locks=0;\n'+V2_GLOBALS+'\nstring SmartPartialStateName(const int state)\n','V2 globals')

    t=replace_once(t,
        '      case V1_EXIT_SMART_PARTIAL:  return "SMART_PARTIAL";\n',
        '      case V1_EXIT_SMART_PARTIAL:  return "SMART_PARTIAL";\n      case V1_EXIT_SMART_PARTIAL_V2: return "SMART_PARTIAL_V2";\n',
        'SP V2 mode name')
    t=replace_once(t,
        '   if(mode==V1_EM_CAUSAL_EPISODE_V1) return "CAUSAL_EPISODE_V1";\n   return "OFF";\n',
        '   if(mode==V1_EM_CAUSAL_EPISODE_V1) return "CAUSAL_EPISODE_V1";\n   if(mode==V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2) return "ENTRY_SURVIVAL_QUARANTINE_V2";\n   return "OFF";\n',
        'EM V2 mode name')

    # initialize newly added per-scenario fields both at scenario creation and fill reset
    init_anchor='''   g_scenarios[n].sp_partial_done=false;\n   g_scenarios[n].sp_be_done=false;\n   g_scenarios[n].pending_submitted_at=0;\n'''
    init_new='''   g_scenarios[n].sp_partial_done=false;\n   g_scenarios[n].sp_be_done=false;\n   g_scenarios[n].em_v2_one_r_reached=false;\n   g_scenarios[n].em_v2_one_r_reached_at=0;\n   g_scenarios[n].sp_v2_last_cost_be_target=0.0;\n   g_scenarios[n].pending_submitted_at=0;\n'''
    t=replace_once(t,init_anchor,init_new,'V2 scenario initialization')
    fill_anchor='''   g_scenarios[scenario_index].sp_partial_done=false;\n   g_scenarios[scenario_index].sp_be_done=false;\n'''
    fill_new=fill_anchor+'''   g_scenarios[scenario_index].em_v2_one_r_reached=false;\n   g_scenarios[scenario_index].em_v2_one_r_reached_at=0;\n   g_scenarios[scenario_index].sp_v2_last_cost_be_target=0.0;\n'''
    t=replace_once(t,fill_anchor,fill_new,'V2 fill reset')

    # Structure refresh observation is shared by EM V1 and V2.
    t=replace_once(t,
        '''   if(InpEpisodeManagementMode!=V1_EM_CAUSAL_EPISODE_V1 ||\n      g_execution_epoch_start<=0 || available_at<g_execution_epoch_start ||\n''',
        '''   if((InpEpisodeManagementMode!=V1_EM_CAUSAL_EPISODE_V1 &&\n       InpEpisodeManagementMode!=V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2) ||\n      g_execution_epoch_start<=0 || available_at<g_execution_epoch_start ||\n''',
        'EM structure shared mode')

    # Insert V2 EM helpers immediately before structure logging.
    log_anchor='''void LogStructureEvent(V1StructureState &s,\n                       const int event_type,\n'''
    t=replace_once(t,log_anchor,EMV2_HELPERS+log_anchor,'EM V2 helper insertion')

    # Dispatch V2 through the existing EM gate and submission hook.
    auth_anchor='''bool D149EMAuthorizeOpportunity(const int scenario_index,const datetime available_at,string &block_reason)\n  {\n   block_reason="";\n'''
    auth_new=auth_anchor+'''   if(InpEpisodeManagementMode==V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2)\n      return D149EMV2AuthorizeOpportunity(scenario_index,available_at,block_reason);\n'''
    t=replace_once(t,auth_anchor,auth_new,'EM V2 authorization dispatch')

    submit_anchor='''void D149EMOnOpportunitySubmitted(const int scenario_index,const datetime available_at)\n  {\n'''
    submit_new=submit_anchor+'''   if(InpEpisodeManagementMode==V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2)\n     {\n      D149EMV2OnOpportunitySubmitted(scenario_index,available_at);\n      return;\n     }\n'''
    t=replace_once(t,submit_anchor,submit_new,'EM V2 submit dispatch')

    # Insert SP V2 helpers before the old D147 manager.
    d147_anchor='''void D147ManageFilledPosition(const int scenario_index,const MqlTick &tick)\n'''
    t=replace_once(t,d147_anchor,SPV2_HELPERS+d147_anchor,'SP V2 helper insertion')

    # Dispatch SP V2 while preserving SP V1.
    old_dispatch='''   if(mode==V1_EXIT_SMART_PARTIAL)\n     {\n      D149SPManageFilledPosition(scenario_index,tick);\n      return;\n     }\n   if(g_scenarios[scenario_index].exit_initial_risk_price<=0.0)\n'''
    new_dispatch='''   if(mode==V1_EXIT_SMART_PARTIAL)\n     {\n      D149SPManageFilledPosition(scenario_index,tick);\n      return;\n     }\n   if(mode==V1_EXIT_SMART_PARTIAL_V2)\n     {\n      D149SPV2ManageFilledPosition(scenario_index,tick);\n      return;\n     }\n   if(g_scenarios[scenario_index].exit_initial_risk_price<=0.0)\n'''
    t=replace_once(t,old_dispatch,new_dispatch,'SP V2 dispatch')

    # Aggregate all partial/full-close deals under SP V2 too.
    old_agg='''   if(g_scenarios[scenario_index].exit_management_mode==V1_EXIT_R_STEP_PARTIAL ||\n      g_scenarios[scenario_index].exit_management_mode==V1_EXIT_SMART_PARTIAL)\n'''
    new_agg='''   if(g_scenarios[scenario_index].exit_management_mode==V1_EXIT_R_STEP_PARTIAL ||\n      g_scenarios[scenario_index].exit_management_mode==V1_EXIT_SMART_PARTIAL ||\n      g_scenarios[scenario_index].exit_management_mode==V1_EXIT_SMART_PARTIAL_V2)\n'''
    t=replace_once(t,old_agg,new_agg,'SP V2 aggregate close')

    # Track +1R independently of exit mode before post-fill exit management.
    filled_anchor='''      if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_FILLED)\n        {\n         D147ManageFilledPosition(scenario_index,tick);\n         continue;\n        }\n'''
    filled_new='''      if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_FILLED)\n        {\n         D149EMV2TrackFilledEntrySurvival(scenario_index,tick);\n         D147ManageFilledPosition(scenario_index,tick);\n         continue;\n        }\n'''
    t=replace_once(t,filled_anchor,filled_new,'EM V2 real +1R tracking')

    # Process the no-broker shadow probe every tick, even when no real execution exists.
    manage_anchor='''void ManageIntegratedExecution(const MqlTick &tick)\n  {\n   datetime observed_at=(datetime)tick.time;\n   ReconcileAllManagedExecutions(observed_at,false);\n'''
    manage_new='''void ManageIntegratedExecution(const MqlTick &tick)\n  {\n   datetime observed_at=(datetime)tick.time;\n   D149EMV2ProcessShadowProbe(tick);\n   ReconcileAllManagedExecutions(observed_at,false);\n'''
    t=replace_once(t,manage_anchor,manage_new,'EM V2 shadow tick processing')

    # Route final position close to V2 entry-survival accounting when selected.
    close_anchor='''   D149EMOnPositionClosed(scenario_index,exit_time,realized_net_money);\n   D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);\n'''
    close_new='''   if(InpEpisodeManagementMode==V1_EM_ENTRY_SURVIVAL_QUARANTINE_V2)\n      D149EMV2OnPositionClosed(scenario_index,exit_time,realized_net_money,exit_reason);\n   else\n      D149EMOnPositionClosed(scenario_index,exit_time,realized_net_money);\n   D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);\n'''
    t=replace_once(t,close_anchor,close_new,'EM V2 close dispatch')

    # Build identity.
    t=t.replace('build=1.95R1L11 property_version=1.00 magic=%I64d phase=SP_EM_RESEARCH_V1 strategy_semantics=D134_BASELINE_CONTROL_PLUS_D149_SP_EM_RESEARCH_TOGGLES',
                'build=1.96R1L12 property_version=1.00 magic=%I64d phase=SP_EM_RESEARCH_V2 strategy_semantics=D134_BASELINE_CONTROL_PLUS_D149_SP_EM_V1_V2_RESEARCH_TOGGLES')
    if 'build=1.96R1L12' not in t:
        raise RuntimeError('EA_START build identity replacement failed')

    old_start='''   LogLine("D149_RESEARCH_START","M1",TimeCurrent(),"",\n           StringFormat("exit_mode=%s em_mode=%s sp_strong_fraction=%.8f sp_default_fraction=%.8f sp_strong_room_r=%.8f sp_partial_once_at_1r=true sp_be_at_2r=true structural_tp_retained=true em_scope=EXTERNAL_CONTINUATION em_episode=FROZEN_MAP_OWNER_PLUS_DIRECTION em_first_loss_requires_refresh=true em_second_loss_owner_lock=true d148_audit_allowed_only_on_control=true",\n                        ExitManagementModeName((int)InpExitManagementMode),EpisodeManagementModeName((int)InpEpisodeManagementMode),\n                        V1_D149_SP_STRONG_PARTIAL_FRACTION,V1_D149_SP_DEFAULT_PARTIAL_FRACTION,V1_D149_SP_STRONG_ROOM_R));\n'''
    new_start='''   LogLine("D149_RESEARCH_START","M1",TimeCurrent(),"",\n           StringFormat("exit_mode=%s em_mode=%s build=1.96R1L12 sp_strong_fraction=%.8f sp_v1_default_fraction=%.8f sp_strong_room_r=%.8f sp_v2_default_lock_buffer_r=%.8f sp_v2_cost_be_buffer_r=%.8f sp_v2_continuation_only=true structural_tp_retained=true em_v2_failure=SL_BEFORE_PLUS_1R em_v2_quarantine_after=2 em_v2_release=SHADOW_OR_PREEXISTING_REAL_PLUS_1R em_v2_force_cancel_existing=false d148_audit_allowed_only_on_control=true",\n                        ExitManagementModeName((int)InpExitManagementMode),EpisodeManagementModeName((int)InpEpisodeManagementMode),\n                        V1_D149_SP_STRONG_PARTIAL_FRACTION,V1_D149_SP_DEFAULT_PARTIAL_FRACTION,V1_D149_SP_STRONG_ROOM_R,\n                        V1_D149_SP_V2_DEFAULT_LOCK_BUFFER_R,V1_D149_SP_V2_COST_BE_BUFFER_R));\n'''
    t=replace_once(t,old_start,new_start,'D149 V2 start log')

    old_deinit='''   EdgeAuditDeinit(reason);\n   LogLine("D149_RESEARCH_STOP","M1",TimeCurrent(),"",\n'''
    new_deinit='''   EdgeAuditDeinit(reason);\n   D149EMV2OnTesterEnd(TimeCurrent());\n   LogLine("D149_RESEARCH_STOP","M1",TimeCurrent(),"",\n'''
    t=replace_once(t,old_deinit,new_deinit,'EM V2 tester-end hook')

    old_stop='''           StringFormat("exit_mode=%s em_mode=%s sp_strong_states=%I64d sp_default_states=%I64d sp_partials=%I64d sp_be_moves=%I64d sp_action_rejections=%I64d sp_partial_infeasible=%I64d em_blocks_concurrent=%I64d em_blocks_no_refresh=%I64d em_blocks_hard_lock=%I64d em_refresh_retries=%I64d em_episode_wins=%I64d em_episode_losses=%I64d em_hard_locks=%I64d 2021_untouched=true",\n                        ExitManagementModeName((int)InpExitManagementMode),EpisodeManagementModeName((int)InpEpisodeManagementMode),\n                        g_d149_sp_strong_states,g_d149_sp_default_states,g_d149_sp_partials,g_d149_sp_be_moves,\n                        g_d149_sp_action_rejections,g_d149_sp_partial_infeasible,g_d149_em_blocks_concurrent,\n                        g_d149_em_blocks_no_refresh,g_d149_em_blocks_hard_lock,g_d149_em_refresh_retries,\n                        g_d149_em_episode_wins,g_d149_em_episode_losses,g_d149_em_hard_locks));\n'''
    new_stop='''           StringFormat("exit_mode=%s em_mode=%s sp_strong_states=%I64d sp_default_states=%I64d sp_partials=%I64d sp_be_moves=%I64d sp_action_rejections=%I64d sp_partial_infeasible=%I64d em_blocks_concurrent=%I64d em_blocks_no_refresh=%I64d em_blocks_hard_lock=%I64d em_refresh_retries=%I64d em_episode_wins=%I64d em_episode_losses=%I64d em_hard_locks=%I64d sp_v2_protected_partials=%I64d sp_v2_strong_partials=%I64d sp_v2_full_close_fallbacks=%I64d sp_v2_cost_be_moves=%I64d sp_v2_cost_be_refreshes=%I64d sp_v2_cost_be_unavailable=%I64d em_v2_entry_failures=%I64d em_v2_one_r_successes=%I64d em_v2_quarantine_entries=%I64d em_v2_quarantine_releases=%I64d em_v2_blocks_quarantine=%I64d em_v2_blocks_no_refresh=%I64d em_v2_shadow_armed=%I64d em_v2_shadow_filled=%I64d em_v2_shadow_success=%I64d em_v2_shadow_failure=%I64d em_v2_shadow_canceled=%I64d em_v2_shadow_censored=%I64d em_v2_quarantine_active_at_stop=%s em_v2_global_failures_at_stop=%d 2021_untouched=true",\n                        ExitManagementModeName((int)InpExitManagementMode),EpisodeManagementModeName((int)InpEpisodeManagementMode),\n                        g_d149_sp_strong_states,g_d149_sp_default_states,g_d149_sp_partials,g_d149_sp_be_moves,\n                        g_d149_sp_action_rejections,g_d149_sp_partial_infeasible,g_d149_em_blocks_concurrent,\n                        g_d149_em_blocks_no_refresh,g_d149_em_blocks_hard_lock,g_d149_em_refresh_retries,\n                        g_d149_em_episode_wins,g_d149_em_episode_losses,g_d149_em_hard_locks,\n                        g_d149_sp_v2_protected_partials,g_d149_sp_v2_strong_partials,g_d149_sp_v2_full_close_fallbacks,\n                        g_d149_sp_v2_cost_be_moves,g_d149_sp_v2_cost_be_refreshes,g_d149_sp_v2_cost_be_unavailable,\n                        g_d149_em_v2_entry_failures,g_d149_em_v2_one_r_successes,g_d149_em_v2_quarantine_entries,g_d149_em_v2_quarantine_releases,\n                        g_d149_em_v2_blocks_quarantine,g_d149_em_v2_blocks_no_refresh,g_d149_em_v2_shadow_armed,g_d149_em_v2_shadow_filled,\n                        g_d149_em_v2_shadow_success,g_d149_em_v2_shadow_failure,g_d149_em_v2_shadow_canceled,g_d149_em_v2_shadow_censored,\n                        g_d149_em_v2_quarantine ? "true" : "false",g_d149_em_v2_global_failures));\n'''
    t=replace_once(t,old_stop,new_stop,'D149 V2 stop log')
    return normalize(t)


def transform_doc(rel: str, text: str) -> str:
    t=normalize(text)
    if rel==HANDOFF:
        old='''Last updated: 2026-08-21\nRepository base before this handoff package: `e449bc68b9e57bd7bd4170279057fddeb429985d`\nCurrent code/research build: `1.95R1L11 / SP_EM_RESEARCH_V1`\nCurrent research phase: **D-149 SMART PARTIAL + EPISODE MANAGEMENT — IMPLEMENTED / LOCAL VALIDATION PENDING**\nStrategy semantics: **D134 BASELINE CONTROL PRESERVED / D149 SP + EM CONTROLLED RESEARCH TOGGLES**\nStrategy authority: **UNCHANGED; ORIGINAL + EM_OFF IS BASELINE CONTROL**\n2021 status: **KEEP UNTOUCHED**\n'''
        new='''Last updated: 2026-08-21\nRepository base before this handoff package: `b3068c0b445005fe455405ed18fb1f82198231df`\nCurrent code/research build: `1.96R1L12 / SP_EM_RESEARCH_V2`\nCurrent research phase: **D-149 SP + EM V2 — IMPLEMENTED / LOCAL COMPILE + CONTROLLED VALIDATION PENDING**\nStrategy semantics: **D134 BASELINE CONTROL PRESERVED / D149 V1 CONTROLS PRESERVED / V2 RESEARCH TOGGLES ADDED**\nStrategy authority: **UNCHANGED; ORIGINAL + EM_OFF IS BASELINE CONTROL**\n2021 status: **KEEP UNTOUCHED**\n'''
        t=replace_once(t,old,new,'HANDOFF V2 header')
        startup_old='''4. Read `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`.
5. Read `docs/ea/D146_CONTINUATION_STATE_AUDIT.md`.
6. Read `docs/ea/STRATEGY_RESEARCH_STATE.md` and `docs/ea/BACKLOG.md`.
7. Use `DECISIONS.md`, `TEST_RESULTS.md`, `EA_SPEC.md`, and older research docs only as needed.
'''
        startup_new='''4. Read `docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md` for the current solution-research evidence and V2 contract.
5. Read `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md` and `docs/ea/D146_CONTINUATION_STATE_AUDIT.md` for the runner-state evidence behind SP.
6. Read `docs/ea/D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY.md` for the Entry-failure classes constraining EM.
7. Read `docs/ea/STRATEGY_RESEARCH_STATE.md` and `docs/ea/BACKLOG.md`.
8. Use `DECISIONS.md`, `TEST_RESULTS.md`, `EA_SPEC.md`, and older research docs only as needed.
'''
        t=replace_once(t,startup_old,startup_new,'HANDOFF V2 startup order')
        return append_once(t,'## D-149 V1 result -> V2 revision — 2026-08-21',HANDOFF_APPEND)
    if rel==STATE:
        old='''Last updated: 2026-08-21\nRepository base before handoff package: `e449bc68b9e57bd7bd4170279057fddeb429985d`\nCurrent code/research identity: `1.95R1L11 / SP_EM_RESEARCH_V1`\nCurrent research phase: **D-149 SMART PARTIAL + EPISODE MANAGEMENT — IMPLEMENTED / LOCAL VALIDATION PENDING**\nStrategy authority: **UNCHANGED; ORIGINAL + EM_OFF CONTROL PRESERVED**\n2021: **UNTOUCHED**\n'''
        new='''Last updated: 2026-08-21\nRepository base before handoff package: `b3068c0b445005fe455405ed18fb1f82198231df`\nCurrent code/research identity: `1.96R1L12 / SP_EM_RESEARCH_V2`\nCurrent research phase: **D-149 SP + EM V2 — IMPLEMENTED / LOCAL COMPILE + CONTROLLED VALIDATION PENDING**\nStrategy authority: **UNCHANGED; ORIGINAL + EM_OFF CONTROL PRESERVED; V1 MODES RETAINED**\n2021: **UNTOUCHED**\n'''
        t=replace_once(t,old,new,'STATE V2 header')
        return append_once(t,'## D-149 V1 solution result and current V2 hypothesis',STATE_APPEND)
    if rel==BACKLOG:
        old='''Last updated: 2026-08-21\nCurrent phase: **D-149 SMART PARTIAL + EPISODE MANAGEMENT — IMPLEMENTED / LOCAL VALIDATION PENDING**\nStrategy authority: **UNCHANGED; RESEARCH TOGGLES ONLY**\n2021: **KEEP UNTOUCHED**\n'''
        new='''Last updated: 2026-08-21\nCurrent phase: **D-149 SP + EM V2 — IMPLEMENTED / LOCAL COMPILE + CONTROLLED VALIDATION PENDING**\nStrategy authority: **UNCHANGED; V1/V2 RESEARCH TOGGLES ONLY**\n2021: **KEEP UNTOUCHED**\n'''
        t=replace_once(t,old,new,'BACKLOG V2 header')
        return append_once(t,'## P0 — D-149 SP/EM V2 controlled revision',BACKLOG_APPEND)
    if rel==DECISIONS:
        return append_once(t,'## D-149B — D149 V1 result classification and V2 architecture freeze',DECISIONS_APPEND)
    if rel==TEST_RESULTS:
        return append_once(t,'## 2026-08-21 — D-149 GOLD 2025 SP / EM V1 result and V2 handoff',TEST_APPEND)
    if rel==D149:
        header_old='''Date: 2026-08-21  
Status: **IMPLEMENTED / LOCAL VALIDATION PENDING**  
Build: `1.95R1L11 / SP_EM_RESEARCH_V1`  
Baseline strategy authority: **UNCHANGED**  
Baseline control: `V1_EXIT_ORIGINAL + V1_EM_OFF`  
2021: **KEEP UNTOUCHED**
'''
        header_new='''Date: 2026-08-21  
Status: **V1 GOLD 2025 COMPLETED / V1 MODES RETAINED AS CONTROLS / V2 IMPLEMENTED SEPARATELY**  
Build: `1.95R1L11 / SP_EM_RESEARCH_V1`  
Baseline strategy authority: **UNCHANGED**  
Baseline control: `V1_EXIT_ORIGINAL + V1_EM_OFF`  
2021: **KEEP UNTOUCHED**
'''
        t=replace_once(t,header_old,header_new,'D149 V1 result status header')
        return append_once(t,'## 12. GOLD 2025 V1 result — completed 2026-08-21',D149_DOC_APPEND)
    raise RuntimeError(f'No doc transform for {rel}')


def expected_outputs(repo: Path) -> dict[str,str]:
    out={EA:transform_ea(head_text(repo,EA))}
    for rel in [HANDOFF,STATE,BACKLOG,DECISIONS,TEST_RESULTS,D149]:
        out[rel]=transform_doc(rel,head_text(repo,rel))
    return out


def verify_head_blob(repo: Path, rel: str, expected: str) -> None:
    actual=run(repo,'git','rev-parse',f'HEAD:{rel}')
    if actual!=expected:
        raise RuntimeError(f'{rel}: committed blob mismatch expected={expected} actual={actual}')


def main() -> int:
    repo=locate_repo()
    head=run(repo,'git','rev-parse','HEAD')
    if head!=EXPECTED_HEAD:
        raise RuntimeError(f'Wrong Git HEAD. expected={EXPECTED_HEAD} actual={head}')
    for rel,blob in EXPECTED_BLOBS.items():
        verify_head_blob(repo,rel,blob)

    for rel in VERIFY_ONLY:
        path=repo/rel
        if not path.exists() or read_file(path)!=head_text(repo,rel):
            raise RuntimeError(f'{rel}: unexpected local edit; D149 V2 refuses to proceed')

    expected=expected_outputs(repo)
    for rel,new_text in expected.items():
        path=repo/rel
        current=read_file(path)
        base=head_text(repo,rel)
        if current!=base and current!=new_text:
            raise RuntimeError(f'{rel}: unexpected local state; expected exact HEAD or exact V2 output')

    for rel,src in NEW_FILES.items():
        desired=read_file(src)
        dst=repo/rel
        if dst.exists() and read_file(dst)!=desired:
            raise RuntimeError(f'{rel}: existing unknown content; refusing overwrite')

    # Freeze the completed V1 evidence in documentation before changing the EA
    # research implementation, matching the project handoff discipline. The
    # apply remains idempotent if interrupted between writes.
    result_doc="docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md"
    write_file(repo/result_doc,read_file(NEW_FILES[result_doc]))
    for rel in [HANDOFF,STATE,BACKLOG,DECISIONS,TEST_RESULTS,D149]:
        write_file(repo/rel,expected[rel])
    write_file(repo/EA,expected[EA])
    analyzer_rel="tools/summarize_d149_sp_em_v2.py"
    write_file(repo/analyzer_rel,read_file(NEW_FILES[analyzer_rel]))

    print('D-149 SP/EM Research V2 applied successfully.')
    print('Build: 1.96R1L12 / SP_EM_RESEARCH_V2')
    print('Baseline: V1_EXIT_ORIGINAL + V1_EM_OFF')
    print('SP controls: SMART_PARTIAL(V1), SMART_PARTIAL_V2')
    print('EM controls: CAUSAL_EPISODE_V1, ENTRY_SURVIVAL_QUARANTINE_V2')
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        raise SystemExit(1)
