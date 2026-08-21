#!/usr/bin/env python3
"""Apply D-149 Smart Partial + Episode Management research variant.

Target: awindboy/Trading exact HEAD e449bc68b9e57bd7bd4170279057fddeb429985d.
Fail-closed and idempotent. Every transformed file is regenerated from exact
committed HEAD content. Unknown local edits abort.
"""
from __future__ import annotations

from pathlib import Path
import locale
import os
import shutil
import subprocess
import sys

EXPECTED_HEAD = "e449bc68b9e57bd7bd4170279057fddeb429985d"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

EA = "mt5/experts/MentorDeterministicV1EA.mq5"
EDGE = "mt5/experts/EdgeAuditV1.mqh"
HANDOFF = "docs/ea/HANDOFF.md"
STATE = "docs/ea/STRATEGY_RESEARCH_STATE.md"
BACKLOG = "docs/ea/BACKLOG.md"
DECISIONS = "docs/ea/DECISIONS.md"
TEST_RESULTS = "docs/ea/TEST_RESULTS.md"
D147 = "docs/ea/D147_EXIT_ARCHITECTURE_RESEARCH.md"
D148 = "docs/ea/D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY.md"

TRANSFORMED = [EA, HANDOFF, STATE, BACKLOG, DECISIONS, TEST_RESULTS, D147, D148]
VERIFY_ONLY = [EDGE, "AGENTS.md", "docs/ea/EA_SPEC.md"]
EXPECTED_BLOBS = {
    EA: "78c3542173137ff59d578826737e83d851d99adc",
    EDGE: "52f785c22a41295a4b58d8d6f8d79056e6c0c693",
    HANDOFF: "cf302cd2e015d868149a79f554b92895051e4e2c",
    STATE: "293f763c29febec35359e6b51cca3ac40d32398f",
    BACKLOG: "1496193211d8543acb2d083a47f094d0b69f742f",
    DECISIONS: "864f7ae0deba7da917421e920574932831668ca5",
    TEST_RESULTS: "46626210558afaeeaaf44ae03861dd5f66d5a196",
    D147: "bd4eaaa2969be104011751fa83888824ff7afbed",
    D148: "a99bf71724a4c4abe0d9235947954cffd08da130",
}

NEW_FILES = {
    "docs/ea/D149_SP_EM_RESEARCH_V1.md": PACKAGE_ROOT / "payload/docs/ea/D149_SP_EM_RESEARCH_V1.md",
    "tools/summarize_d149_sp_em.py": PACKAGE_ROOT / "payload/tools/summarize_d149_sp_em.py",
    "tools/compare_d149_baseline.py": PACKAGE_ROOT / "payload/tools/compare_d149_baseline.py",
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


D149_ENUMS = r'''
// D-149 Smart Partial state is frozen only at first +1R.
enum V1SmartPartialState
  {
   V1_SP_STATE_UNSET=0,
   V1_SP_STATE_STRONG_RUNNER,
   V1_SP_STATE_DEFAULT
  };

// D-149 Episode Management is an independent Entry/exposure research toggle.
enum V1EpisodeManagementMode
  {
   V1_EM_OFF=0,
   V1_EM_CAUSAL_EPISODE_V1
  };

'''

D149_EM_STRUCT = r'''
struct V1EMEpisodeState
  {
   bool              valid;
   ENUM_TIMEFRAMES   map_tf;
   string            owner_id;
   int               direction;
   int               consecutive_losses;
   bool              hard_locked;
   datetime          last_loss_at;
   datetime          last_refresh_consumed_at;
   datetime          last_authorized_at;
   int               wins;
   int               losses;
   int               submitted;
  };

'''

D149_SCENARIO_FIELDS = r'''

   // D-149 Smart Partial fill-frozen state. No Entry/initial geometry authority.
   bool              sp_state_frozen;
   int               sp_state;
   double            sp_partial_fraction;
   bool              sp_m30_range_available;
   string            sp_m30_owner_id;
   double            sp_m30_protected_price;
   double            sp_m30_external_price;
   double            sp_m30_range_progress;
   double            sp_m30_remaining_to_external_r;
   bool              sp_partial_done;
   bool              sp_be_done;
'''

D149_GLOBALS = r'''

V1EMEpisodeState g_d149_em_episodes[];
datetime g_d149_last_h1_event_at[2];
string   g_d149_last_h1_event_owner[2];
datetime g_d149_last_m30_event_at[2];
string   g_d149_last_m30_event_owner[2];

long g_d149_sp_strong_states=0;
long g_d149_sp_default_states=0;
long g_d149_sp_partials=0;
long g_d149_sp_be_moves=0;
long g_d149_sp_action_rejections=0;
long g_d149_sp_partial_infeasible=0;
long g_d149_em_blocks_concurrent=0;
long g_d149_em_blocks_no_refresh=0;
long g_d149_em_blocks_hard_lock=0;
long g_d149_em_refresh_retries=0;
long g_d149_em_episode_wins=0;
long g_d149_em_episode_losses=0;
long g_d149_em_hard_locks=0;

string SmartPartialStateName(const int state)
  {
   if(state==V1_SP_STATE_STRONG_RUNNER) return "STRONG_RUNNER";
   if(state==V1_SP_STATE_DEFAULT)       return "DEFAULT";
   return "UNSET";
  }

string EpisodeManagementModeName(const int mode)
  {
   if(mode==V1_EM_CAUSAL_EPISODE_V1) return "CAUSAL_EPISODE_V1";
   return "OFF";
  }
'''

D149_EM_HELPERS = r'''
//+------------------------------------------------------------------+
//| D-149 Episode Management -- causal repeated-exposure control     |
//+------------------------------------------------------------------+
int D149DirectionIndex(const int direction)
  {
   return (direction>0 ? 0 : 1);
  }

int D149EMFindEpisode(const ENUM_TIMEFRAMES map_tf,const string owner_id,const int direction)
  {
   for(int i=ArraySize(g_d149_em_episodes)-1;i>=0;i--)
      if(g_d149_em_episodes[i].valid &&
         g_d149_em_episodes[i].map_tf==map_tf &&
         g_d149_em_episodes[i].owner_id==owner_id &&
         g_d149_em_episodes[i].direction==direction)
         return i;
   return -1;
  }

int D149EMGetOrCreateEpisode(const ENUM_TIMEFRAMES map_tf,const string owner_id,const int direction)
  {
   int found=D149EMFindEpisode(map_tf,owner_id,direction);
   if(found>=0) return found;
   int n=ArraySize(g_d149_em_episodes);
   if(ArrayResize(g_d149_em_episodes,n+1,32)<0) return -1;
   g_d149_em_episodes[n].valid=true;
   g_d149_em_episodes[n].map_tf=map_tf;
   g_d149_em_episodes[n].owner_id=owner_id;
   g_d149_em_episodes[n].direction=direction;
   g_d149_em_episodes[n].consecutive_losses=0;
   g_d149_em_episodes[n].hard_locked=false;
   g_d149_em_episodes[n].last_loss_at=0;
   g_d149_em_episodes[n].last_refresh_consumed_at=0;
   g_d149_em_episodes[n].last_authorized_at=0;
   g_d149_em_episodes[n].wins=0;
   g_d149_em_episodes[n].losses=0;
   g_d149_em_episodes[n].submitted=0;
   return n;
  }

void D149EMOnStructureEvent(const V1StructureState &s,
                            const int event_type,
                            const int direction,
                            const datetime available_at)
  {
   if(InpEpisodeManagementMode!=V1_EM_CAUSAL_EPISODE_V1 ||
      g_execution_epoch_start<=0 || available_at<g_execution_epoch_start ||
      (s.tf!=PERIOD_H1 && s.tf!=PERIOD_M30) ||
      (event_type!=V1_EVENT_INITIAL_BOS && event_type!=V1_EVENT_BOS) ||
      direction==0 || s.owner_id=="")
      return;

   int di=D149DirectionIndex(direction);
   if(s.tf==PERIOD_H1)
     {
      g_d149_last_h1_event_at[di]=available_at;
      g_d149_last_h1_event_owner[di]=s.owner_id;
     }
   else
     {
      g_d149_last_m30_event_at[di]=available_at;
      g_d149_last_m30_event_owner[di]=s.owner_id;
     }

   LogLine("D149_EM_STRUCTURE_REFRESH","M30",available_at,s.owner_id,
           StringFormat("tf=%s owner_id=%s direction=%s event=%s refresh_evidence=true",
                        TfName(s.tf),s.owner_id,DirectionName(direction),EventName(event_type)));
  }

datetime D149EMLatestRefreshForScenario(const int scenario_index,string &refresh_reason)
  {
   refresh_reason="NONE";
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios)) return 0;
   const int direction=g_scenarios[scenario_index].direction;
   const int di=D149DirectionIndex(direction);
   const ENUM_TIMEFRAMES map_tf=g_scenarios[scenario_index].active_map_tf;
   const string owner_id=g_scenarios[scenario_index].owner_id;

   datetime best=0;
   if(map_tf==PERIOD_H1)
     {
      if(g_d149_last_h1_event_owner[di]==owner_id && g_d149_last_h1_event_at[di]>best)
        {
         best=g_d149_last_h1_event_at[di];
         refresh_reason="SAME_H1_OWNER_BOS";
        }
      // Under a mature H1 thesis, a new same-direction M30 delivery is
      // sufficient fresh evidence for one retry; it need not share the old M30 owner.
      if(g_d149_last_m30_event_at[di]>best)
        {
         best=g_d149_last_m30_event_at[di];
         refresh_reason="NEW_SAME_DIRECTION_M30_DELIVERY";
        }
     }
   else if(map_tf==PERIOD_M30)
     {
      if(g_d149_last_m30_event_owner[di]==owner_id)
        {
         best=g_d149_last_m30_event_at[di];
         refresh_reason="SAME_M30_OWNER_BOS";
        }
     }
   return best;
  }

bool D149EMHasConcurrentEpisodeExposure(const int scenario_index)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios)) return false;
   for(int p=0;p<ArraySize(g_active_execution_scenario_indices);p++)
     {
      int i=g_active_execution_scenario_indices[p];
      if(i<0 || i>=ArraySize(g_scenarios) || i==scenario_index || !g_scenarios[i].valid)
         continue;
      if(g_scenarios[i].scope!=V1_SCOPE_EXTERNAL_CONTINUATION ||
         g_scenarios[i].direction!=g_scenarios[scenario_index].direction ||
         g_scenarios[i].active_map_tf!=g_scenarios[scenario_index].active_map_tf ||
         g_scenarios[i].owner_id!=g_scenarios[scenario_index].owner_id)
         continue;
      if(g_scenarios[i].strategy_state==V1_STRATEGY_PENDING ||
         g_scenarios[i].strategy_state==V1_STRATEGY_FILLED ||
         g_scenarios[i].execution_status==V1_EXEC_CANCEL_REQUESTED ||
         g_scenarios[i].execution_status==V1_EXEC_CANCEL_REJECTED ||
         g_scenarios[i].execution_status==V1_EXEC_DIVERGENCE)
         return true;
     }
   return false;
  }

bool D149EMAuthorizeOpportunity(const int scenario_index,const datetime available_at,string &block_reason)
  {
   block_reason="";
   if(InpEpisodeManagementMode!=V1_EM_CAUSAL_EPISODE_V1 ||
      scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION)
      return true;

   if(g_scenarios[scenario_index].owner_id=="" ||
      (g_scenarios[scenario_index].active_map_tf!=PERIOD_H1 &&
       g_scenarios[scenario_index].active_map_tf!=PERIOD_M30))
     {
      block_reason="EM_EPISODE_ID_UNAVAILABLE";
      g_d149_em_blocks_hard_lock++;
      return false;
     }

   if(D149EMHasConcurrentEpisodeExposure(scenario_index))
     {
      block_reason="EM_SAME_EPISODE_CONCURRENT_EXPOSURE";
      g_d149_em_blocks_concurrent++;
      return false;
     }

   int e=D149EMFindEpisode(g_scenarios[scenario_index].active_map_tf,
                          g_scenarios[scenario_index].owner_id,
                          g_scenarios[scenario_index].direction);
   if(e<0) return true;

   if(g_d149_em_episodes[e].hard_locked || g_d149_em_episodes[e].consecutive_losses>=2)
     {
      block_reason="EM_TWO_LOSS_OWNER_LOCK";
      g_d149_em_blocks_hard_lock++;
      return false;
     }

   if(g_d149_em_episodes[e].consecutive_losses==1)
     {
      string refresh_reason="";
      datetime refresh_at=D149EMLatestRefreshForScenario(scenario_index,refresh_reason);
      if(refresh_at<=g_d149_em_episodes[e].last_loss_at ||
         refresh_at<=g_d149_em_episodes[e].last_refresh_consumed_at)
        {
         block_reason="EM_FIRST_LOSS_REQUIRES_NEW_MAP_DELIVERY";
         g_d149_em_blocks_no_refresh++;
         return false;
        }
     }

   return true;
  }

void D149EMOnOpportunitySubmitted(const int scenario_index,const datetime available_at)
  {
   if(InpEpisodeManagementMode!=V1_EM_CAUSAL_EPISODE_V1 ||
      scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION)
      return;

   int e=D149EMGetOrCreateEpisode(g_scenarios[scenario_index].active_map_tf,
                                 g_scenarios[scenario_index].owner_id,
                                 g_scenarios[scenario_index].direction);
   if(e<0) return;
   string refresh_reason="NONE";
   datetime refresh_at=0;
   if(g_d149_em_episodes[e].consecutive_losses==1)
     {
      refresh_at=D149EMLatestRefreshForScenario(scenario_index,refresh_reason);
      if(refresh_at>g_d149_em_episodes[e].last_loss_at)
        {
         g_d149_em_episodes[e].last_refresh_consumed_at=refresh_at;
         g_d149_em_refresh_retries++;
        }
     }
   g_d149_em_episodes[e].last_authorized_at=available_at;
   g_d149_em_episodes[e].submitted++;
   LogLine("D149_EM_AUTHORIZED","M1",available_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s owner_id=%s map_tf=%s direction=%s consecutive_losses=%d refresh_at=%s refresh_reason=%s hard_locked=%s",
                        g_scenarios[scenario_index].id,g_scenarios[scenario_index].owner_id,
                        TfName(g_scenarios[scenario_index].active_map_tf),DirectionName(g_scenarios[scenario_index].direction),
                        g_d149_em_episodes[e].consecutive_losses,
                        refresh_at>0 ? TimeToString(refresh_at,TIME_DATE|TIME_SECONDS) : "NA",
                        refresh_reason,g_d149_em_episodes[e].hard_locked ? "true" : "false"));
  }

void D149EMOnPositionClosed(const int scenario_index,const datetime exit_at,const double realized_net_money)
  {
   if(InpEpisodeManagementMode!=V1_EM_CAUSAL_EPISODE_V1 ||
      scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].scope!=V1_SCOPE_EXTERNAL_CONTINUATION)
      return;
   if(g_scenarios[scenario_index].execution_divergence)
     {
      LogLine("D149_EM_RESULT_SKIPPED","M1",exit_at,g_scenarios[scenario_index].id,
              "reason=EXECUTION_DIVERGENCE episode_state_unchanged=true");
      return;
     }

   int e=D149EMGetOrCreateEpisode(g_scenarios[scenario_index].active_map_tf,
                                 g_scenarios[scenario_index].owner_id,
                                 g_scenarios[scenario_index].direction);
   if(e<0) return;
   bool win=(realized_net_money>0.0);
   if(win)
     {
      g_d149_em_episodes[e].wins++;
      g_d149_em_episodes[e].consecutive_losses=0;
      g_d149_em_episodes[e].hard_locked=false;
      g_d149_em_episode_wins++;
     }
   else
     {
      g_d149_em_episodes[e].losses++;
      g_d149_em_episodes[e].consecutive_losses++;
      g_d149_em_episodes[e].last_loss_at=exit_at;
      g_d149_em_episode_losses++;
      if(g_d149_em_episodes[e].consecutive_losses>=2)
        {
         if(!g_d149_em_episodes[e].hard_locked) g_d149_em_hard_locks++;
         g_d149_em_episodes[e].hard_locked=true;
        }
     }

   LogLine("D149_EM_RESULT","M1",exit_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s owner_id=%s map_tf=%s direction=%s realized_net_money=%.8f win=%s consecutive_losses_after=%d hard_locked_after=%s episode_wins=%d episode_losses=%d",
                        g_scenarios[scenario_index].id,g_scenarios[scenario_index].owner_id,
                        TfName(g_scenarios[scenario_index].active_map_tf),DirectionName(g_scenarios[scenario_index].direction),
                        realized_net_money,win ? "true" : "false",g_d149_em_episodes[e].consecutive_losses,
                        g_d149_em_episodes[e].hard_locked ? "true" : "false",
                        g_d149_em_episodes[e].wins,g_d149_em_episodes[e].losses));
  }

'''

D149_SP_HELPERS = r'''
//+------------------------------------------------------------------+
//| D-149 Smart Partial -- D145/D146 +1R continuation-state usage    |
//+------------------------------------------------------------------+
bool D149SPFreezeStateAtOneR(const int scenario_index,const datetime observed_at)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios)) return false;
   if(g_scenarios[scenario_index].sp_state_frozen) return true;

   g_scenarios[scenario_index].sp_state_frozen=true;
   g_scenarios[scenario_index].sp_state=V1_SP_STATE_DEFAULT;
   g_scenarios[scenario_index].sp_partial_fraction=V1_D149_SP_DEFAULT_PARTIAL_FRACTION;
   g_scenarios[scenario_index].sp_m30_range_available=false;
   g_scenarios[scenario_index].sp_m30_owner_id="";
   g_scenarios[scenario_index].sp_m30_protected_price=0.0;
   g_scenarios[scenario_index].sp_m30_external_price=0.0;
   g_scenarios[scenario_index].sp_m30_range_progress=0.0;
   g_scenarios[scenario_index].sp_m30_remaining_to_external_r=0.0;

   const int direction=g_scenarios[scenario_index].direction;
   const double risk=g_scenarios[scenario_index].exit_initial_risk_price;
   const double one_r_price=g_scenarios[scenario_index].fill_price+(double)direction*risk;
   bool have_protected=false,have_external=false;
   double protected_price=0.0,external_price=0.0;

   if(TrendDirection(g_structure[2].trend)==direction && g_structure[2].owner_id!="")
     {
      g_scenarios[scenario_index].sp_m30_owner_id=g_structure[2].owner_id;
      if(direction>0)
        {
         have_protected=g_structure[2].protected_low.valid;
         have_external=g_structure[2].external_high.valid;
         if(have_protected) protected_price=g_structure[2].protected_low.price;
         if(have_external) external_price=g_structure[2].external_high.price;
        }
      else
        {
         have_protected=g_structure[2].protected_high.valid;
         have_external=g_structure[2].external_low.valid;
         if(have_protected) protected_price=g_structure[2].protected_high.price;
         if(have_external) external_price=g_structure[2].external_low.price;
        }
     }

   if(have_protected && have_external && risk>0.0)
     {
      double span=(double)direction*(external_price-protected_price);
      if(span>LiquidityTickSize())
        {
         g_scenarios[scenario_index].sp_m30_range_available=true;
         g_scenarios[scenario_index].sp_m30_protected_price=protected_price;
         g_scenarios[scenario_index].sp_m30_external_price=external_price;
         g_scenarios[scenario_index].sp_m30_range_progress=
            ((double)direction*(one_r_price-protected_price))/span;
         g_scenarios[scenario_index].sp_m30_remaining_to_external_r=
            ((double)direction*(external_price-one_r_price))/risk;

         // Structural boundary, not a fitted percentile: if the current M30
         // external lies at or beyond the original +2R price, another full R
         // remains inside the current directional delivery geometry.
         if(g_scenarios[scenario_index].sp_m30_remaining_to_external_r>=V1_D149_SP_STRONG_ROOM_R)
           {
            g_scenarios[scenario_index].sp_state=V1_SP_STATE_STRONG_RUNNER;
            g_scenarios[scenario_index].sp_partial_fraction=V1_D149_SP_STRONG_PARTIAL_FRACTION;
           }
        }
     }

   if(g_scenarios[scenario_index].sp_state==V1_SP_STATE_STRONG_RUNNER) g_d149_sp_strong_states++;
   else g_d149_sp_default_states++;

   LogLine("D149_SP_STATE_FROZEN","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s state=%s partial_fraction=%.8f fill=%.10f one_r_price=%.10f risk=%.10f m30_range_available=%s m30_owner_id=%s m30_protected=%.10f m30_external=%.10f m30_range_progress=%.10f m30_remaining_to_external_r=%.10f strong_definition=M30_EXTERNAL_AT_OR_BEYOND_ORIGINAL_PLUS_2R threshold_r=%.8f future_backfill=false",
                        g_scenarios[scenario_index].id,SmartPartialStateName(g_scenarios[scenario_index].sp_state),
                        g_scenarios[scenario_index].sp_partial_fraction,g_scenarios[scenario_index].fill_price,one_r_price,risk,
                        g_scenarios[scenario_index].sp_m30_range_available ? "true" : "false",
                        g_scenarios[scenario_index].sp_m30_owner_id=="" ? "NA" : g_scenarios[scenario_index].sp_m30_owner_id,
                        g_scenarios[scenario_index].sp_m30_protected_price,g_scenarios[scenario_index].sp_m30_external_price,
                        g_scenarios[scenario_index].sp_m30_range_progress,g_scenarios[scenario_index].sp_m30_remaining_to_external_r,
                        V1_D149_SP_STRONG_ROOM_R));
   return true;
  }

bool D149SPRequestPartialClose(const int scenario_index,
                               const MqlTick &tick,
                               const ulong position_ticket,
                               const double current_volume)
  {
   double fraction=g_scenarios[scenario_index].sp_partial_fraction;
   double min_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double eps=MathMax(1.0e-10,step*1.0e-6);
   double close_volume=D147NormalizeVolumeDown(current_volume*fraction);
   double remaining=current_volume-close_volume;

   if(close_volume<min_volume-eps || remaining<min_volume-eps || close_volume<=0.0)
     {
      g_scenarios[scenario_index].exit_partial_disabled=true;
      g_scenarios[scenario_index].sp_partial_done=true;
      g_d149_sp_partial_infeasible++;
      LogLine("D149_SP_PARTIAL_INFEASIBLE","M1",(datetime)tick.time,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s state=%s current_volume=%.8f requested_fraction=%.8f normalized_close=%.8f remaining=%.8f volume_min=%.8f volume_step=%.8f action=NO_FULL_CLOSE_SUBSTITUTION remainder_keeps_original_sl_tp_until_2r_be=true",
                           g_scenarios[scenario_index].id,SmartPartialStateName(g_scenarios[scenario_index].sp_state),
                           current_volume,fraction,close_volume,remaining,min_volume,step));
      return false;
     }

   datetime observed_at=(datetime)tick.time;
   if(g_scenarios[scenario_index].exit_last_action_attempt_at==observed_at &&
      g_scenarios[scenario_index].exit_last_action_attempt_step==101)
      return false;
   g_scenarios[scenario_index].exit_last_action_attempt_at=observed_at;
   g_scenarios[scenario_index].exit_last_action_attempt_step=101;

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
   request.comment=StringFormat("D149SP-P%d",scenario_index);

   ResetLastError();
   bool call_ok=OrderSend(request,result);
   bool accepted=(call_ok && IsAcceptableTradeRetcode(result.retcode));
   if(!accepted)
     {
      g_d149_sp_action_rejections++;
      LogLine("D149_SP_PARTIAL_REJECTED","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s state=%s fraction=%.8f close_volume=%.8f current_volume=%.8f call_ok=%s retcode=%u comment=%s last_error=%d retry=true",
                           g_scenarios[scenario_index].id,SmartPartialStateName(g_scenarios[scenario_index].sp_state),fraction,
                           close_volume,current_volume,call_ok ? "true" : "false",result.retcode,result.comment,GetLastError()));
      return false;
     }

   g_scenarios[scenario_index].sp_partial_done=true;
   g_scenarios[scenario_index].exit_partial_count++;
   g_d149_sp_partials++;
   LogLine("D149_SP_PARTIAL_ACCEPTED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s state=%s fraction_of_original_remaining=%.8f requested_volume=%.8f pre_close_volume=%.8f expected_remaining=%.8f execution_price=%.10f original_sl=%.10f structural_tp=%.10f retcode=%u deal=%I64u order=%I64u",
                        g_scenarios[scenario_index].id,SmartPartialStateName(g_scenarios[scenario_index].sp_state),fraction,
                        close_volume,current_volume,remaining,(result.price>0.0 ? result.price : market_reference_price),
                        g_scenarios[scenario_index].normalized_sl,g_scenarios[scenario_index].final_objective_price,
                        result.retcode,result.deal,result.order));
   return true;
  }

bool D149SPRequestBreakEven(const int scenario_index,
                            const MqlTick &tick,
                            const ulong position_ticket,
                            const double current_sl,
                            const double current_tp)
  {
   double raw_target=g_scenarios[scenario_index].fill_price;
   double target_sl=(g_scenarios[scenario_index].direction>0 ?
                     NormalizePriceFloorToTick(raw_target) : NormalizePriceCeilToTick(raw_target));
   double eps=LiquidityTickSize()*0.5;
   if((g_scenarios[scenario_index].direction>0 && current_sl>0.0 && current_sl>=target_sl-eps) ||
      (g_scenarios[scenario_index].direction<0 && current_sl>0.0 && current_sl<=target_sl+eps))
     {
      g_scenarios[scenario_index].sp_be_done=true;
      g_scenarios[scenario_index].exit_dynamic_sl=current_sl;
      LogLine("D149_SP_BE_ALREADY_PROTECTED","M1",(datetime)tick.time,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s current_sl=%.10f be_target=%.10f no_change=true",g_scenarios[scenario_index].id,current_sl,target_sl));
      return true;
     }

   if(!D147TrailingTargetLegal(g_scenarios[scenario_index].direction,tick,target_sl))
      return false;

   datetime observed_at=(datetime)tick.time;
   if(g_scenarios[scenario_index].exit_last_action_attempt_at==observed_at &&
      g_scenarios[scenario_index].exit_last_action_attempt_step==202)
      return false;
   g_scenarios[scenario_index].exit_last_action_attempt_at=observed_at;
   g_scenarios[scenario_index].exit_last_action_attempt_step=202;

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
      LogLine("D149_SP_BE_REJECTED","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s position_ticket=%I64u be_target=%.10f current_sl=%.10f current_tp=%.10f call_ok=%s retcode=%u comment=%s last_error=%d retry=true",
                           g_scenarios[scenario_index].id,position_ticket,target_sl,current_sl,current_tp,
                           call_ok ? "true" : "false",result.retcode,result.comment,GetLastError()));
      return false;
     }

   g_scenarios[scenario_index].sp_be_done=true;
   g_scenarios[scenario_index].exit_dynamic_sl=target_sl;
   g_d149_sp_be_moves++;
   LogLine("D149_SP_BE_MOVED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s trigger=PLUS_2R new_sl=ACTUAL_FILL fill=%.10f old_sl=%.10f new_sl=%.10f structural_tp=%.10f retcode=%u comment=%s",
                        g_scenarios[scenario_index].id,g_scenarios[scenario_index].fill_price,current_sl,target_sl,current_tp,
                        result.retcode,result.comment));
   return true;
  }

void D149SPManageFilledPosition(const int scenario_index,const MqlTick &tick)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].strategy_state!=V1_STRATEGY_FILLED ||
      g_scenarios[scenario_index].exit_initial_risk_price<=0.0)
      return;

   ulong position_ticket=0;
   double open_price=0.0,volume=0.0,current_sl=0.0,current_tp=0.0;
   if(!D147GetManagedPositionState(scenario_index,position_ticket,open_price,volume,current_sl,current_tp))
      return;

   double px=(g_scenarios[scenario_index].direction>0 ? tick.bid : tick.ask);
   double favorable_r=(double)g_scenarios[scenario_index].direction*
                       (px-g_scenarios[scenario_index].fill_price)/
                       g_scenarios[scenario_index].exit_initial_risk_price;
   int reached_step=(int)MathFloor(favorable_r+1.0e-10);
   if(reached_step>g_scenarios[scenario_index].exit_highest_r_step_seen)
      g_scenarios[scenario_index].exit_highest_r_step_seen=reached_step;

   if(g_scenarios[scenario_index].exit_highest_r_step_seen>=1 && !g_scenarios[scenario_index].sp_state_frozen)
      D149SPFreezeStateAtOneR(scenario_index,(datetime)tick.time);

   // User-requested invariant has priority over profit-taking: once +2R has
   // been observed, the surviving position must first be protected at Fill.
   // If the broker rejects/temporarily disallows BE, keep retrying on later
   // ticks; a +1R partial may still secure profit on the current tick.
   if(g_scenarios[scenario_index].exit_highest_r_step_seen>=2 && !g_scenarios[scenario_index].sp_be_done)
     {
      if(D149SPRequestBreakEven(scenario_index,tick,position_ticket,current_sl,current_tp))
         return; // refresh broker position state before any remaining partial action
     }

   // Exactly one partial, state frozen at first +1R. Strong runner realizes
   // only 25% and keeps 75% for the structural objective; default realizes 50%.
   if(g_scenarios[scenario_index].exit_highest_r_step_seen>=1 &&
      !g_scenarios[scenario_index].sp_partial_done &&
      !g_scenarios[scenario_index].exit_partial_disabled)
      D149SPRequestPartialClose(scenario_index,tick,position_ticket,volume);
  }

'''

D149_HANDOFF = r'''
## D-149 SP + EM RESEARCH V1 — IMPLEMENTED / LOCAL VALIDATION PENDING

Build: `1.95R1L11 / SP_EM_RESEARCH_V1`.

Independent research toggles:

```text
Exit: ORIGINAL / R_STEP_TRAILING / R_STEP_PARTIAL / SMART_PARTIAL
EM:   OFF / CAUSAL_EPISODE_V1
```

Primary four-run matrix:

```text
A ORIGINAL + EM_OFF        baseline control
B SMART_PARTIAL + EM_OFF   SP isolated
C ORIGINAL + EM_ACTIVE     EM isolated
D SMART_PARTIAL + EM_ACTIVE combined
```

SP V1:
- first +1R freezes causally available M30 protected/external state;
- if current M30 external is at/beyond original +2R, close 25% only (`STRONG_RUNNER`);
- otherwise/missing M30 range, close 50% (`DEFAULT`);
- no repeated integer-R partials;
- first +2R moves remaining SL to actual Fill;
- structural TP remains unchanged.

EM V1, continuation only:
- episode identity = frozen active H1/M30 owner + direction;
- one pending/filled exposure per same episode;
- after first net loss, a fresh same-direction map delivery is required before one retry;
- H1-led episode accepts same-owner H1 BOS or new same-direction M30 INITIAL_BOS/BOS as refresh;
- M30-led episode requires same-owner M30 BOS;
- second consecutive net loss hard-locks that owner until a new owner creates a new episode;
- a positive realized-net trade resets the episode consecutive-loss count.

D148 audit remains available only for `ORIGINAL + EM_OFF`. Do not enable D148 audit on SP/EM performance runs.

2021 remains untouched.
'''

D149_STATE = r'''
## D-149 active strategy research — SP + EM

The project now tests two solution mechanisms rather than only describing failures.

`SMART_PARTIAL (SP)` attacks post-+1R giveback while preserving large winners. It uses the D145/D146 relationship only at the stage where it was discovered: first +1R. The V1 strong state is structurally defined as `current M30 external at/beyond original +2R`, not a fitted progress percentile. Strong closes 25%; default/missing state closes 50%. At +2R all SP remainder moves to Fill BE and then remains open to structural TP.

`EPISODE MANAGEMENT (EM)` attacks correlated repeated exposure. It does not mine a loser score. It groups continuation opportunities by frozen H1/M30 owner + direction, serializes exposure, requires new map delivery after the first loss, and hard-locks the same owner after a second consecutive net loss.

Neither mechanism is promoted strategy authority until identical-condition GOLD multi-year and then cross-market tests support it.
'''

D149_BACKLOG = r'''
## P0 — D-149 SP + EM controlled solution research

- [x] Add `V1_EXIT_SMART_PARTIAL` without changing existing mode numeric identities.
- [x] SP +1R state uses D145/D146 M30 continuation geometry only.
- [x] `STRONG_RUNNER`: current M30 external at/beyond original +2R -> 25% partial.
- [x] `DEFAULT`: all other / M30-range-unavailable -> 50% partial.
- [x] SP makes only one +1R partial; no repeated integer-R haircut.
- [x] SP +2R -> remaining SL to actual Fill; structural TP retained.
- [x] Add independent EM OFF/ACTIVE toggle.
- [x] EM serializes same-owner episode exposure.
- [x] First episode loss requires fresh map delivery before one retry.
- [x] Second consecutive same-owner loss hard-locks until owner changes.
- [x] Compact log allowlist includes D147/D149 action rows.
- [ ] MetaEditor compile 0 errors.
- [ ] ORIGINAL + EM_OFF behavior parity vs D148 control.
- [ ] GOLD 2025 four-run matrix A/B/C/D.
- [ ] GOLD 2023 and 2024 four-run matrix after clean 2025 execution.
- [ ] Compare WR, avg winner, expectancy, DD, longest streak, winner concentration, SP state split, EM blocks and skipped baseline opportunity character.
- [ ] Cross-market validation only after GOLD multi-year relation is understood.

Do not tune 25/50 fractions or EM loss count from GOLD 2025 after seeing results. Any next variant must be separately pre-registered.
'''

D149_DECISIONS = r'''
## D-149 — develop Smart Partial and Causal Episode Management as independent controls

Status: ACTIVE RESEARCH DECISION

Decision:

1. Add `SMART_PARTIAL` as a fourth D147-compatible exit mode while preserving ORIGINAL as control.
2. Freeze SP strong-state definition to a causal structural geometry: at first +1R, the current scenario-direction M30 external must lie at or beyond the original +2R price.
3. Freeze SP partial fractions for V1: 25% in `STRONG_RUNNER`, 50% otherwise. Missing M30 range is not imputed into strong state.
4. SP performs only the +1R partial. At first +2R, move the remainder SL to actual Fill and otherwise leave structural TP intact. No repeated staircase haircut after +2R.
5. Add EM as an independent toggle scoped to EXTERNAL_CONTINUATION. Episode identity is frozen map owner + direction, not elapsed time or a fitted regime score.
6. EM allows only one live/pending exposure per episode. After one net loss it requires new same-direction map delivery before one retry. After a second consecutive net loss, the owner is locked until owner identity changes. A positive net trade resets consecutive loss state.
7. H1-led refresh may be same-owner H1 BOS or a new same-direction M30 INITIAL_BOS/BOS; M30-led refresh must be same-owner M30 BOS.
8. Validate SP and EM separately before judging the combined mode.

Reason:

D147 showed mechanical partials improve realized shape but destroy large winners; D145/D146 supplied a stage-specific continuation signal. D148 and loss-cluster work showed that repeated exposure can amplify a single structural thesis. These two mechanisms address different causes and should not be conflated.
'''

D148_RESULT = r'''
## GOLD 2023-2025 D-148 generalization result — 2026-08-21

Clean continuation population after excluding the known 2024 stale-fill execution-divergence fixture:

```text
2023: 64 fills / 35 immediate +1R / 29 SL-first / 11 post-SL +1R recoveries
2024: 52 clean fills / 24 immediate +1R / 28 SL-first / 9 post-SL +1R recoveries
2025: 51 fills / 30 immediate +1R / 21 SL-first / 7 post-SL +1R recoveries

total: 167 fills / 89 immediate +1R / 78 SL-first
SL-first -> +1R before map-support loss = 27 / 78 = 34.6%
SL-first -> map-support failure first = 51 / 78 = 65.4%
```

Among the 27 post-SL +1R recoveries, the original Root had already invalidated in 18. Only 9 retained the original Root through recovery. Therefore most recoveries are not evidence for globally widening the SL; they are evidence that a local source can fail while the higher-timeframe directional premise survives.

Root-timeframe relationship survived all three years: M15-Root SL failures recovered later in the same HTF direction materially more often than H1/M30-Root failures. M30-led vs H1-led immediate-entry success did not generalize consistently and is not an Entry veto.

Known contaminated fixture excluded from 2024 clean inference:
`2023-12-22 cancel rejection retcode=10018 -> 2024-01-05 stale fill`.
'''

D147_SP_NOTE = r'''
## D-149 handoff from mechanical partial to Smart Partial

D-147 mechanical `R_STEP_PARTIAL` remains a control. D-149 does not tune it. The new `SMART_PARTIAL` changes the architecture in one deliberate way: one partial at +1R, fraction selected by the D145/D146 +1R M30 continuation geometry, then +2R BE protection with no further mechanical partials. This is intended to preserve large structural winners that D-147 repeatedly cut at every integer R.
'''

TEST_APPEND = r'''
## D-147 / D-148 solution-research handoff evidence — 2026-08-21

D-147 GOLD 2025 continuation control vs mechanical partial:

```text
ORIGINAL: 51 trades / WR 27.45% / expectancy +0.254R / avg winner +3.827R / max DD 19.53R
PARTIAL:  51 trades / WR 47.06% / expectancy +0.187R / avg winner +1.402R / max DD 7.66R
```

Mechanical partial materially improved realized win shape and drawdown but cut large winners. This motivates D149 SP rather than promotion of the repeated 50%-remaining staircase.

D-148 clean GOLD 2023-2025 continuation taxonomy:

```text
167 fills
89 immediate +1R = 53.3%
78 normalized-SL first = 46.7%
27 / 78 SL-first later recovered original +1R before H1/M30 map-support loss = 34.6%
51 / 78 lost map support before recovery = 65.4%
18 / 27 recovery cases had original Root invalidated before recovery
9 / 27 retained original Root through recovery
```

Interpretation: do not try to turn every SL into a winner. Separate true structural failure, local-source failure/re-entry opportunity, and the smaller same-Root timing/SL-sensitivity class. D149 EM addresses repeated correlated episode exposure; D149 SP addresses +1R giveback.
'''


def transform_ea(text: str) -> str:
    t=normalize(text)
    t=replace_once(t,
        '#property description "Mentor deterministic V1 EA - D-148 entry-survival failure-taxonomy shadow audit harness"',
        '#property description "Mentor deterministic V1 EA - D-149 SP + EM research harness"',
        'property description')

    enum_anchor='''enum V1ExitManagementMode\n  {\n   V1_EXIT_ORIGINAL=0,\n   V1_EXIT_R_STEP_TRAILING,\n   V1_EXIT_R_STEP_PARTIAL\n  };\n\n'''
    enum_new='''enum V1ExitManagementMode\n  {\n   V1_EXIT_ORIGINAL=0,\n   V1_EXIT_R_STEP_TRAILING,\n   V1_EXIT_R_STEP_PARTIAL,\n   V1_EXIT_SMART_PARTIAL\n  };\n\n'''+D149_ENUMS
    t=replace_once(t,enum_anchor,enum_new,'D149 enums')

    input_anchor='input V1ExitManagementMode InpExitManagementMode = V1_EXIT_ORIGINAL;\n'
    t=replace_once(t,input_anchor,input_anchor+'input V1EpisodeManagementMode InpEpisodeManagementMode = V1_EM_OFF;\n','EM input')

    define_anchor='''// D-147 research parameter is intentionally frozen; no fraction optimization in this phase.\n#define V1_D147_PARTIAL_FRACTION 0.50\n'''
    define_new=define_anchor+'''\n// D-149 V1 parameters are frozen research constants, not optimizer inputs.\n#define V1_D149_SP_STRONG_PARTIAL_FRACTION 0.25\n#define V1_D149_SP_DEFAULT_PARTIAL_FRACTION 0.50\n#define V1_D149_SP_STRONG_ROOM_R           1.00\n'''
    t=replace_once(t,define_anchor,define_new,'D149 frozen parameters')

    exec_candidate='''struct V1ExecutionCandidate\n  {\n   bool              valid;\n   int               scenario_index;\n   string            scenario_id;\n   int               direction;\n   datetime          authorization_at;\n  };\n\n'''
    t=replace_once(t,exec_candidate,exec_candidate+D149_EM_STRUCT,'EM struct')

    field_anchor='''   datetime          exit_last_action_attempt_at;\n   int               exit_last_action_attempt_step;\n'''
    t=replace_once(t,field_anchor,field_anchor+D149_SCENARIO_FIELDS,'SP scenario fields')

    globals_anchor='''long             g_d147_partial_infeasible=0;\n\nstring ExitManagementModeName(const int mode)\n'''
    t=replace_once(t,globals_anchor,
        'long             g_d147_partial_infeasible=0;\n'+D149_GLOBALS+'\nstring ExitManagementModeName(const int mode)\n',
        'D149 globals')

    name_anchor='''      case V1_EXIT_R_STEP_PARTIAL: return "R_STEP_PARTIAL";\n'''
    t=replace_once(t,name_anchor,name_anchor+'      case V1_EXIT_SMART_PARTIAL:  return "SMART_PARTIAL";\n','SP mode name')

    compact_anchor='''   // Research identity and PLAN-freeze classification.\n   if(event_name=="EA_START" ||\n'''
    compact_new='''   // D147/D149 action rows are low-volume research-critical diagnostics.\n   if(StringFind(event_name,"D147_")==0 || StringFind(event_name,"D149_")==0)\n      return true;\n\n'''+compact_anchor
    t=replace_once(t,compact_anchor,compact_new,'compact D147/D149 allowlist')

    # Initialize SP state on scenario creation. This exact block is distinct from fill reset.
    init_anchor='''   g_scenarios[n].exit_partial_disabled=false;\n   g_scenarios[n].exit_last_action_attempt_at=0;\n   g_scenarios[n].exit_last_action_attempt_step=0;\n'''
    init_new=init_anchor+'''   g_scenarios[n].sp_state_frozen=false;\n   g_scenarios[n].sp_state=V1_SP_STATE_UNSET;\n   g_scenarios[n].sp_partial_fraction=0.0;\n   g_scenarios[n].sp_m30_range_available=false;\n   g_scenarios[n].sp_m30_owner_id="";\n   g_scenarios[n].sp_m30_protected_price=0.0;\n   g_scenarios[n].sp_m30_external_price=0.0;\n   g_scenarios[n].sp_m30_range_progress=0.0;\n   g_scenarios[n].sp_m30_remaining_to_external_r=0.0;\n   g_scenarios[n].sp_partial_done=false;\n   g_scenarios[n].sp_be_done=false;\n'''
    # Current source contains the same trailing 3-line sequence twice. Anchor with following pending field.
    init_context=init_anchor+'   g_scenarios[n].pending_submitted_at=0;\n'
    init_context_new=init_new+'   g_scenarios[n].pending_submitted_at=0;\n'
    t=replace_once(t,init_context,init_context_new,'scenario SP initialization')

    fill_anchor='''   g_scenarios[scenario_index].exit_partial_disabled=false;\n   g_scenarios[scenario_index].exit_last_action_attempt_at=0;\n   g_scenarios[scenario_index].exit_last_action_attempt_step=0;\n'''
    fill_new=fill_anchor+'''   g_scenarios[scenario_index].sp_state_frozen=false;\n   g_scenarios[scenario_index].sp_state=V1_SP_STATE_UNSET;\n   g_scenarios[scenario_index].sp_partial_fraction=0.0;\n   g_scenarios[scenario_index].sp_m30_range_available=false;\n   g_scenarios[scenario_index].sp_m30_owner_id="";\n   g_scenarios[scenario_index].sp_m30_protected_price=0.0;\n   g_scenarios[scenario_index].sp_m30_external_price=0.0;\n   g_scenarios[scenario_index].sp_m30_range_progress=0.0;\n   g_scenarios[scenario_index].sp_m30_remaining_to_external_r=0.0;\n   g_scenarios[scenario_index].sp_partial_done=false;\n   g_scenarios[scenario_index].sp_be_done=false;\n'''
    # Remaining occurrence after scenario-init transformation is the fill reset.
    t=replace_once(t,fill_anchor,fill_new,'fill SP reset')

    log_structure_anchor='''void LogStructureEvent(V1StructureState &s,\n                       const int event_type,\n'''
    t=replace_once(t,log_structure_anchor,D149_EM_HELPERS+log_structure_anchor,'EM helper insertion')

    edge_hook='''   LogLine("STRUCTURE_"+EventName(event_type),s.name,available_at,id,detail);\n   EdgeAuditOnStructureEvent(s,event_type,direction,broken,protected_ref,bar,available_at);\n'''
    edge_hook_new='''   LogLine("STRUCTURE_"+EventName(event_type),s.name,available_at,id,detail);\n   D149EMOnStructureEvent(s,event_type,direction,available_at);\n   EdgeAuditOnStructureEvent(s,event_type,direction,broken,protected_ref,bar,available_at);\n'''
    t=replace_once(t,edge_hook,edge_hook_new,'EM structure hook')

    submit_anchor='''   int same_direction_exposure=\n      CountManagedBrokerExposureDirection(g_scenarios[master_index].direction);\n'''
    submit_new='''   string d149_em_block_reason="";\n   if(!D149EMAuthorizeOpportunity(master_index,available_at,d149_em_block_reason))\n     {\n      LogLine("D149_EM_BLOCKED","M1",available_at,g_scenarios[master_index].id,\n              StringFormat("scenario_id=%s owner_id=%s map_tf=%s direction=%s reason=%s",\n                           g_scenarios[master_index].id,g_scenarios[master_index].owner_id,\n                           TfName(g_scenarios[master_index].active_map_tf),DirectionName(g_scenarios[master_index].direction),\n                           d149_em_block_reason));\n      D134BlockReadyOpportunity(master_index,available_at,d149_em_block_reason,V1_EXEC_NONE);\n      return;\n     }\n\n'''+submit_anchor
    t=replace_once(t,submit_anchor,submit_new,'EM authorization gate')

    submit_call='''   bool submitted=SubmitPendingForScenario(master_index,available_at);\n   if(!submitted && g_scenarios[master_index].execution_opportunity_merged)\n'''
    submit_call_new='''   bool submitted=SubmitPendingForScenario(master_index,available_at);\n   if(submitted)\n      D149EMOnOpportunitySubmitted(master_index,available_at);\n   if(!submitted && g_scenarios[master_index].execution_opportunity_merged)\n'''
    t=replace_once(t,submit_call,submit_call_new,'EM submitted hook')

    d147_manage_anchor='''void D147ManageFilledPosition(const int scenario_index,const MqlTick &tick)\n'''
    t=replace_once(t,d147_manage_anchor,D149_SP_HELPERS+d147_manage_anchor,'SP helper insertion')

    manage_mode_anchor='''   int mode=g_scenarios[scenario_index].exit_management_mode;\n   if(mode==V1_EXIT_ORIGINAL)\n      return;\n   if(g_scenarios[scenario_index].exit_initial_risk_price<=0.0)\n'''
    manage_mode_new='''   int mode=g_scenarios[scenario_index].exit_management_mode;\n   if(mode==V1_EXIT_ORIGINAL)\n      return;\n   if(mode==V1_EXIT_SMART_PARTIAL)\n     {\n      D149SPManageFilledPosition(scenario_index,tick);\n      return;\n     }\n   if(g_scenarios[scenario_index].exit_initial_risk_price<=0.0)\n'''
    t=replace_once(t,manage_mode_anchor,manage_mode_new,'SP management dispatch')

    aggregate_anchor='''   if(g_scenarios[scenario_index].exit_management_mode==V1_EXIT_R_STEP_PARTIAL)\n'''
    aggregate_new='''   if(g_scenarios[scenario_index].exit_management_mode==V1_EXIT_R_STEP_PARTIAL ||\n      g_scenarios[scenario_index].exit_management_mode==V1_EXIT_SMART_PARTIAL)\n'''
    t=replace_once(t,aggregate_anchor,aggregate_new,'SP exit deal aggregation')

    closed_hook='''   LogLine("POSITION_CLOSED","M1",observed_at,g_scenarios[scenario_index].id,\n           StringFormat("scenario_id=%s symbol=%s exit_deal=%I64u position_id=%I64u sizing_mode=%s volume=%.8f target_risk_money=%.8f planned_risk_money=%.8f actual_fill_risk_money=%.8f exit_profit=%.8f exit_commission=%.8f exit_swap=%.8f exit_fee=%.8f realized_net_money=%.8f exit_at=%s actual_exit=%.10f deal_reason=%I64d strategy_sl=%.10f strategy_tp=%.10f execution_status=%s scenario_scoped_reconciliation=true",\n                        g_scenarios[scenario_index].id,_Symbol,exit_deal,g_scenarios[scenario_index].broker_position_id,\n                        PositionSizingModeName(g_scenarios[scenario_index].position_sizing_mode),g_scenarios[scenario_index].order_volume,\n                        g_scenarios[scenario_index].target_risk_money,g_scenarios[scenario_index].planned_risk_money,g_scenarios[scenario_index].actual_fill_risk_money,\n                        g_scenarios[scenario_index].exit_deal_profit,g_scenarios[scenario_index].exit_deal_commission,g_scenarios[scenario_index].exit_deal_swap,g_scenarios[scenario_index].exit_deal_fee,realized_net_money,\n                        TimeToString(exit_time,TIME_DATE|TIME_SECONDS),exit_price,exit_reason,\n                        g_scenarios[scenario_index].normalized_sl,g_scenarios[scenario_index].final_objective_price,\n                        ExecutionStatusName(g_scenarios[scenario_index].execution_status)));\n   D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);\n'''
    closed_hook_new=closed_hook.replace('   D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);\n',
        '   D149EMOnPositionClosed(scenario_index,exit_time,realized_net_money);\n   D135RemoveIndexValue(g_active_execution_scenario_indices,scenario_index);\n')
    t=replace_once(t,closed_hook,closed_hook_new,'EM close-result hook')

    oninit_guard='''int OnInit()\n  {\n   if(InpPositionSizingMode==V1_SIZE_FIXED_RISK_MONEY && InpFixedRiskMoneyPerTrade<=0.0)\n'''
    oninit_new='''int OnInit()\n  {\n   if(InpEnableEdgeAudit &&\n      (InpExitManagementMode!=V1_EXIT_ORIGINAL || InpEpisodeManagementMode!=V1_EM_OFF))\n     {\n      Print("D148 EdgeAudit requires D149 control settings: V1_EXIT_ORIGINAL + V1_EM_OFF");\n      return INIT_PARAMETERS_INCORRECT;\n     }\n   if(InpPositionSizingMode==V1_SIZE_FIXED_RISK_MONEY && InpFixedRiskMoneyPerTrade<=0.0)\n'''
    t=replace_once(t,oninit_guard,oninit_new,'D148 audit guard')

    t=replace_once(t,
        'build=1.94R1L10 property_version=1.00 magic=%I64d phase=ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW strategy_semantics=D134_ENTRY_INITIAL_GEOMETRY_UNCHANGED_D147_EXIT_TOGGLE_PRESENT_D148_AUDIT_ONLY',
        'build=1.95R1L11 property_version=1.00 magic=%I64d phase=SP_EM_RESEARCH_V1 strategy_semantics=D134_BASELINE_CONTROL_PLUS_D149_SP_EM_RESEARCH_TOGGLES',
        'EA_START identity')

    d147_start='''   LogLine("D147_EXIT_VARIANT_START","M1",TimeCurrent(),"",\n'''
    d149_start='''   LogLine("D149_RESEARCH_START","M1",TimeCurrent(),"",\n           StringFormat("exit_mode=%s em_mode=%s sp_strong_fraction=%.8f sp_default_fraction=%.8f sp_strong_room_r=%.8f sp_partial_once_at_1r=true sp_be_at_2r=true structural_tp_retained=true em_scope=EXTERNAL_CONTINUATION em_episode=FROZEN_MAP_OWNER_PLUS_DIRECTION em_first_loss_requires_refresh=true em_second_loss_owner_lock=true d148_audit_allowed_only_on_control=true",\n                        ExitManagementModeName((int)InpExitManagementMode),EpisodeManagementModeName((int)InpEpisodeManagementMode),\n                        V1_D149_SP_STRONG_PARTIAL_FRACTION,V1_D149_SP_DEFAULT_PARTIAL_FRACTION,V1_D149_SP_STRONG_ROOM_R));\n'''
    t=replace_once(t,d147_start,d149_start+d147_start,'D149 start log')

    deinit_anchor='''   EdgeAuditDeinit(reason);\n   LogLine("D147_EXIT_VARIANT_STOP","M1",TimeCurrent(),"",\n'''
    d149_stop='''   EdgeAuditDeinit(reason);\n   LogLine("D149_RESEARCH_STOP","M1",TimeCurrent(),"",\n           StringFormat("exit_mode=%s em_mode=%s sp_strong_states=%I64d sp_default_states=%I64d sp_partials=%I64d sp_be_moves=%I64d sp_action_rejections=%I64d sp_partial_infeasible=%I64d em_blocks_concurrent=%I64d em_blocks_no_refresh=%I64d em_blocks_hard_lock=%I64d em_refresh_retries=%I64d em_episode_wins=%I64d em_episode_losses=%I64d em_hard_locks=%I64d 2021_untouched=true",\n                        ExitManagementModeName((int)InpExitManagementMode),EpisodeManagementModeName((int)InpEpisodeManagementMode),\n                        g_d149_sp_strong_states,g_d149_sp_default_states,g_d149_sp_partials,g_d149_sp_be_moves,\n                        g_d149_sp_action_rejections,g_d149_sp_partial_infeasible,g_d149_em_blocks_concurrent,\n                        g_d149_em_blocks_no_refresh,g_d149_em_blocks_hard_lock,g_d149_em_refresh_retries,\n                        g_d149_em_episode_wins,g_d149_em_episode_losses,g_d149_em_hard_locks));\n   LogLine("D147_EXIT_VARIANT_STOP","M1",TimeCurrent(),"",\n'''
    t=replace_once(t,deinit_anchor,d149_stop,'D149 stop log')
    return normalize(t)


def transform_doc(rel: str, text: str) -> str:
    t=normalize(text)
    if rel==HANDOFF:
        old='''Last updated: 2026-08-21\nRepository base before this handoff package: `1889f9d5c53bc37e6061b9e309fa11b1534c1123`\nCurrent code/research build: `1.94R1L10 / ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW`\nCurrent research phase: **D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / LOCAL COMPILE + AUDIT PARITY PENDING**\nStrategy semantics: **D134 ENTRY + INITIAL GEOMETRY UNCHANGED / D147 EXIT TOGGLE PRESENT / D148 SHADOW ONLY**\nStrategy authority: **UNCHANGED; D148 HAS NONE**\n2021 status: **KEEP UNTOUCHED**\n'''
        new='''Last updated: 2026-08-21\nRepository base before this handoff package: `e449bc68b9e57bd7bd4170279057fddeb429985d`\nCurrent code/research build: `1.95R1L11 / SP_EM_RESEARCH_V1`\nCurrent research phase: **D-149 SMART PARTIAL + EPISODE MANAGEMENT — IMPLEMENTED / LOCAL VALIDATION PENDING**\nStrategy semantics: **D134 BASELINE CONTROL PRESERVED / D149 SP + EM CONTROLLED RESEARCH TOGGLES**\nStrategy authority: **UNCHANGED; ORIGINAL + EM_OFF IS BASELINE CONTROL**\n2021 status: **KEEP UNTOUCHED**\n'''
        t=replace_once(t,old,new,'HANDOFF header')
        return append_once(t,'## D-149 SP + EM RESEARCH V1 — IMPLEMENTED',D149_HANDOFF)
    if rel==STATE:
        old='''Last updated: 2026-08-21\nRepository base before handoff package: `1889f9d5c53bc37e6061b9e309fa11b1534c1123`\nCurrent code/research identity: `1.94R1L10 / ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW`\nCurrent research phase: **D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / COMPILE + AUDIT PARITY PENDING**\nStrategy authority: **UNCHANGED; D148 SHADOW ONLY**\n2021: **UNTOUCHED**\n'''
        new='''Last updated: 2026-08-21\nRepository base before handoff package: `e449bc68b9e57bd7bd4170279057fddeb429985d`\nCurrent code/research identity: `1.95R1L11 / SP_EM_RESEARCH_V1`\nCurrent research phase: **D-149 SMART PARTIAL + EPISODE MANAGEMENT — IMPLEMENTED / LOCAL VALIDATION PENDING**\nStrategy authority: **UNCHANGED; ORIGINAL + EM_OFF CONTROL PRESERVED**\n2021: **UNTOUCHED**\n'''
        t=replace_once(t,old,new,'STATE header')
        return append_once(t,'## D-149 active strategy research — SP + EM',D149_STATE)
    if rel==BACKLOG:
        old='''Last updated: 2026-08-21\nCurrent phase: **D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / COMPILE + AUDIT PARITY PENDING**\nStrategy authority: **UNCHANGED**\n2021: **KEEP UNTOUCHED**\n'''
        new='''Last updated: 2026-08-21\nCurrent phase: **D-149 SMART PARTIAL + EPISODE MANAGEMENT — IMPLEMENTED / LOCAL VALIDATION PENDING**\nStrategy authority: **UNCHANGED; RESEARCH TOGGLES ONLY**\n2021: **KEEP UNTOUCHED**\n'''
        t=replace_once(t,old,new,'BACKLOG header')
        return append_once(t,'## P0 — D-149 SP + EM controlled solution research',D149_BACKLOG)
    if rel==DECISIONS:
        return append_once(t,'## D-149 — develop Smart Partial and Causal Episode Management as independent controls',D149_DECISIONS)
    if rel==TEST_RESULTS:
        return append_once(t,'## D-147 / D-148 solution-research handoff evidence — 2026-08-21',TEST_APPEND)
    if rel==D147:
        return append_once(t,'## D-149 handoff from mechanical partial to Smart Partial',D147_SP_NOTE)
    if rel==D148:
        return append_once(t,'## GOLD 2023-2025 D-148 generalization result — 2026-08-21',D148_RESULT)
    raise RuntimeError(f'No document transform for {rel}')


def expected_outputs(repo: Path) -> dict[str,str]:
    out={}
    out[EA]=transform_ea(head_text(repo,EA))
    for rel in [HANDOFF,STATE,BACKLOG,DECISIONS,TEST_RESULTS,D147,D148]:
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

    # Verify authority/audit surfaces are locally clean even though D149 does not rewrite them.
    for rel in VERIFY_ONLY:
        path=repo/rel
        if not path.exists():
            raise RuntimeError(f'Missing verify-only file: {rel}')
        if read_file(path)!=head_text(repo,rel):
            raise RuntimeError(f'{rel}: unexpected local edit; D149 refuses to proceed')

    expected=expected_outputs(repo)
    for rel,new_text in expected.items():
        path=repo/rel
        current=read_file(path)
        base=head_text(repo,rel)
        if current!=base and current!=new_text:
            raise RuntimeError(f'{rel}: unexpected local state; expected exact HEAD or exact D149 output')

    for rel,src in NEW_FILES.items():
        desired=read_file(src)
        dst=repo/rel
        if dst.exists() and read_file(dst)!=desired:
            raise RuntimeError(f'{rel}: existing unknown content; refusing overwrite')

    for rel,new_text in expected.items():
        write_file(repo/rel,new_text)
    for rel,src in NEW_FILES.items():
        write_file(repo/rel,read_file(src))

    print('D-149 SP + EM research variant applied successfully.')
    print('Build: 1.95R1L11 / SP_EM_RESEARCH_V1')
    print('Baseline control: V1_EXIT_ORIGINAL + V1_EM_OFF')
    print('Primary matrix: ORIGINAL/OFF, SMART_PARTIAL/OFF, ORIGINAL/EM, SMART_PARTIAL/EM')
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        raise SystemExit(1)
