#!/usr/bin/env python3
"""Apply D-148 Entry Survival Failure Taxonomy shadow audit.

Target: awindboy/Trading exact HEAD 1889f9d5c53bc37e6061b9e309fa11b1534c1123.
Fail-closed and idempotent. Tracked files must equal exact committed HEAD or the
exact D-148 transform generated from that HEAD. Unknown local edits abort.
"""
from __future__ import annotations

from pathlib import Path
import locale
import os
import shutil
import subprocess
import sys

EXPECTED_HEAD = "1889f9d5c53bc37e6061b9e309fa11b1534c1123"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

EA = "mt5/experts/MentorDeterministicV1EA.mq5"
EDGE = "mt5/experts/EdgeAuditV1.mqh"
HANDOFF = "docs/ea/HANDOFF.md"
STATE = "docs/ea/STRATEGY_RESEARCH_STATE.md"
BACKLOG = "docs/ea/BACKLOG.md"
DECISIONS = "docs/ea/DECISIONS.md"
TEST_RESULTS = "docs/ea/TEST_RESULTS.md"
D147 = "docs/ea/D147_EXIT_ARCHITECTURE_RESEARCH.md"

TRACKED_TARGETS = [EA, EDGE, HANDOFF, STATE, BACKLOG, DECISIONS, TEST_RESULTS, D147]
EXPECTED_BLOBS = {
    EA: "436934f670c09a831ecc67f024e39261eee3bf0a",
    EDGE: "718eb15e8d9d2d1417c4f11ae37beca6cdcfb26e",
    HANDOFF: "58d1c4e53a51616a6fd1f48f13f1b2895d588868",
    STATE: "275cb72c78af04fdde42876a687c75c05c886f1d",
    BACKLOG: "98b88858ea10030be6f6ed029025160116f29351",
    DECISIONS: "c89bc2ad80813f7da0e3bf1abe887e7f591c856a",
    TEST_RESULTS: "e051c94733884f8bdc45a22f2b22414a035ef727",
    D147: "f640f933f7246ccb78f7727cd87cadf396136ac7",
}

NEW_FILES = {
    "docs/ea/D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY.md": PACKAGE_ROOT / "payload/docs/ea/D148_ENTRY_SURVIVAL_FAILURE_TAXONOMY.md",
    "tools/summarize_d148_entry_survival_failure_taxonomy.py": PACKAGE_ROOT / "payload/tools/summarize_d148_entry_survival_failure_taxonomy.py",
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


D148_FIELDS = r'''

   // D-148 shadow-only Entry-survival failure taxonomy. No strategy authority.
   bool       d148_eligible;
   bool       d148_pre_sl_resolved;
   bool       d148_post_sl_active;
   bool       d148_terminal;
   string     d148_terminal_outcome;
   datetime   d148_resolved_at;
   int        d148_original_map_tf;
   string     d148_original_owner_id;
   string     d148_root_id;
   bool       d148_original_authority_alive_at_fill;
   bool       d148_frozen_owner_invalidated;
   datetime   d148_frozen_owner_invalidated_at;
   bool       d148_map_support_loss_seen;
   datetime   d148_first_map_support_loss_at;
   int        d148_first_map_support_loss_direction;
   string     d148_first_map_support_loss_tf;
   string     d148_first_map_support_loss_owner_id;
   datetime   d148_post_sl_map_support_loss_at;
   int        d148_post_sl_map_support_loss_direction;
   string     d148_post_sl_map_support_loss_tf;
   string     d148_post_sl_map_support_loss_owner_id;
   datetime   d148_root_invalidated_at;
   string     d148_root_invalidation_reason;
   datetime   d148_sl_at;
   double     d148_sl_exit_side_price;
   double     d148_pre_sl_mfe_r;
   double     d148_pre_sl_mae_r;
   bool       d148_map_support_same_at_sl;
   bool       d148_entry_recovered_after_sl;
   datetime   d148_entry_recovered_at;
   bool       d148_one_r_recovered_after_sl;
   datetime   d148_one_r_recovered_at;
   double     d148_post_sl_max_adverse_r_from_fill;
   double     d148_post_sl_max_favorable_r_from_fill;
   long       d148_h1_same_events_at_sl;
   long       d148_h1_opp_events_at_sl;
   long       d148_m30_same_events_at_sl;
   long       d148_m30_opp_events_at_sl;
   long       d148_m1_same_events_at_sl;
   long       d148_m1_opp_events_at_sl;
   long       d148_h1_same_pb_at_sl;
   long       d148_h1_opp_pb_at_sl;
   long       d148_m30_same_pb_at_sl;
   long       d148_m30_opp_pb_at_sl;
   long       d148_m1_same_pb_at_sl;
   long       d148_m1_opp_pb_at_sl;
'''

D148_GLOBALS = r'''
long g_edge_d148_eligible=0;
long g_edge_d148_one_r_controls=0;
long g_edge_d148_sl_failures=0;
long g_edge_d148_entry_recoveries=0;
long g_edge_d148_one_r_recoveries=0;
long g_edge_d148_map_loss_terminals=0;
long g_edge_d148_frozen_owner_invalidations=0;
long g_edge_d148_root_invalidations=0;
long g_edge_d148_censored=0;
long g_edge_d148_pre_sl_censored=0;
'''

D148_HELPERS = r'''
//+------------------------------------------------------------------+
//| D-148 Entry-survival failure taxonomy -- shadow only             |
//+------------------------------------------------------------------+
void EdgeAuditD148CurrentMapState(int &direction,string &tf_name,string &owner_id)
  {
   ENUM_TIMEFRAMES tf=EdgeAuditHighestMapTf();
   direction=HighestActiveMapDirection();
   tf_name=(tf==PERIOD_CURRENT ? "NONE" : TfName(tf));
   owner_id="NA";
   if(tf==PERIOD_H1 && g_structure[1].owner_id!="") owner_id=g_structure[1].owner_id;
   else if(tf==PERIOD_M30 && g_structure[2].owner_id!="") owner_id=g_structure[2].owner_id;
  }

bool EdgeAuditD148OriginalAuthorityAlive(const V1EdgeRunnerTracker &r)
  {
   int index=-1;
   if(r.d148_original_map_tf==(int)PERIOD_H1) index=1;
   else if(r.d148_original_map_tf==(int)PERIOD_M30) index=2;
   if(index<0 || r.d148_original_owner_id=="") return false;
   return (g_structure[index].owner_id==r.d148_original_owner_id &&
           TrendDirection(g_structure[index].trend)==r.direction);
  }

void EdgeAuditD148ResetRunner(V1EdgeRunnerTracker &r)
  {
   r.d148_eligible=false;
   r.d148_pre_sl_resolved=false;
   r.d148_post_sl_active=false;
   r.d148_terminal=false;
   r.d148_terminal_outcome="";
   r.d148_resolved_at=0;
   r.d148_original_map_tf=(int)PERIOD_CURRENT;
   r.d148_original_owner_id="";
   r.d148_root_id="";
   r.d148_original_authority_alive_at_fill=false;
   r.d148_frozen_owner_invalidated=false;
   r.d148_frozen_owner_invalidated_at=0;
   r.d148_map_support_loss_seen=false;
   r.d148_first_map_support_loss_at=0;
   r.d148_first_map_support_loss_direction=0;
   r.d148_first_map_support_loss_tf="";
   r.d148_first_map_support_loss_owner_id="";
   r.d148_post_sl_map_support_loss_at=0;
   r.d148_post_sl_map_support_loss_direction=0;
   r.d148_post_sl_map_support_loss_tf="";
   r.d148_post_sl_map_support_loss_owner_id="";
   r.d148_root_invalidated_at=0;
   r.d148_root_invalidation_reason="";
   r.d148_sl_at=0;
   r.d148_sl_exit_side_price=0.0;
   r.d148_pre_sl_mfe_r=0.0;
   r.d148_pre_sl_mae_r=0.0;
   r.d148_map_support_same_at_sl=false;
   r.d148_entry_recovered_after_sl=false;
   r.d148_entry_recovered_at=0;
   r.d148_one_r_recovered_after_sl=false;
   r.d148_one_r_recovered_at=0;
   r.d148_post_sl_max_adverse_r_from_fill=0.0;
   r.d148_post_sl_max_favorable_r_from_fill=-1.0e100;
   r.d148_h1_same_events_at_sl=0;
   r.d148_h1_opp_events_at_sl=0;
   r.d148_m30_same_events_at_sl=0;
   r.d148_m30_opp_events_at_sl=0;
   r.d148_m1_same_events_at_sl=0;
   r.d148_m1_opp_events_at_sl=0;
   r.d148_h1_same_pb_at_sl=0;
   r.d148_h1_opp_pb_at_sl=0;
   r.d148_m30_same_pb_at_sl=0;
   r.d148_m30_opp_pb_at_sl=0;
   r.d148_m1_same_pb_at_sl=0;
   r.d148_m1_opp_pb_at_sl=0;
  }

void EdgeAuditD148ArmAtFill(V1EdgeRunnerTracker &r,const V1ScenarioPlan &p,const datetime at)
  {
   EdgeAuditD148ResetRunner(r);
   if(p.scope!=V1_SCOPE_EXTERNAL_CONTINUATION) return;
   r.d148_eligible=true;
   r.d148_original_map_tf=(int)p.active_map_tf;
   r.d148_original_owner_id=p.owner_id;
   r.d148_root_id=p.root_zone_id;
   r.d148_original_authority_alive_at_fill=EdgeAuditD148OriginalAuthorityAlive(r);
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   g_edge_d148_eligible++;
   EdgeAuditWrite("EDGE_AUDIT_D148_FILL_STATE","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s direction=%s fill_at=%s active_map_tf_at_plan=%s frozen_owner_id=%s frozen_owner_alive_at_fill=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s current_map_support_same=%s root_id=%s fill_price=%.10f normalized_sl=%.10f target_1r=%.10f risk_distance=%.10f strategy_authority=false",
                   r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),TfName((ENUM_TIMEFRAMES)r.d148_original_map_tf),
                   r.d148_original_owner_id=="" ? "NA" : r.d148_original_owner_id,
                   r.d148_original_authority_alive_at_fill ? "true" : "false",map_tf,map_owner,DirectionName(map_dir),
                   map_dir==r.direction ? "true" : "false",r.d148_root_id=="" ? "NA" : r.d148_root_id,
                   r.fill_price,r.normalized_sl,r.target_1r,r.risk_distance));
  }

string EdgeAuditD148PostSlEventDelta(const V1EdgeRunnerTracker &r)
  {
   return StringFormat("post_sl_h1_same_events=%I64d post_sl_h1_opp_events=%I64d post_sl_m30_same_events=%I64d post_sl_m30_opp_events=%I64d post_sl_m1_same_events=%I64d post_sl_m1_opp_events=%I64d post_sl_h1_same_pb=%I64d post_sl_h1_opp_pb=%I64d post_sl_m30_same_pb=%I64d post_sl_m30_opp_pb=%I64d post_sl_m1_same_pb=%I64d post_sl_m1_opp_pb=%I64d",
      EdgeAuditDirCounter(PERIOD_H1,r.direction)-r.d148_h1_same_events_at_sl,
      EdgeAuditDirCounter(PERIOD_H1,-r.direction)-r.d148_h1_opp_events_at_sl,
      EdgeAuditDirCounter(PERIOD_M30,r.direction)-r.d148_m30_same_events_at_sl,
      EdgeAuditDirCounter(PERIOD_M30,-r.direction)-r.d148_m30_opp_events_at_sl,
      EdgeAuditDirCounter(PERIOD_M1,r.direction)-r.d148_m1_same_events_at_sl,
      EdgeAuditDirCounter(PERIOD_M1,-r.direction)-r.d148_m1_opp_events_at_sl,
      EdgeAuditPbCounter(PERIOD_H1,r.direction)-r.d148_h1_same_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_H1,-r.direction)-r.d148_h1_opp_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_M30,r.direction)-r.d148_m30_same_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_M30,-r.direction)-r.d148_m30_opp_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_M1,r.direction)-r.d148_m1_same_pb_at_sl,
      EdgeAuditPbCounter(PERIOD_M1,-r.direction)-r.d148_m1_opp_pb_at_sl);
  }

void EdgeAuditD148Terminal(V1EdgeRunnerTracker &r,const string outcome,const datetime at,const double px)
  {
   if(!r.d148_eligible || r.d148_terminal) return;
   r.d148_post_sl_active=false;
   r.d148_terminal=true;
   r.d148_terminal_outcome=outcome;
   r.d148_resolved_at=at;
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   double extra_beyond_sl=MathMax(0.0,r.d148_post_sl_max_adverse_r_from_fill-1.0);
   string detail=StringFormat("scenario_id=%s direction=%s outcome=%s sl_at=%s resolved_at=%s exit_side_price=%.10f fill_price=%.10f risk_distance=%.10f pre_sl_mfe_r=%.10f pre_sl_mae_r=%.10f map_support_same_at_sl=%s entry_recovered_after_sl=%s entry_recovered_at=%s one_r_recovered_after_sl=%s one_r_recovered_at=%s post_sl_max_adverse_r_from_fill=%.10f post_sl_extra_beyond_sl_r=%.10f post_sl_max_favorable_r_from_fill=%.10f frozen_owner_invalidated=%s frozen_owner_invalidated_at=%s first_map_support_loss_at=%s first_map_support_loss_direction=%s first_map_support_loss_tf=%s first_map_support_loss_owner_id=%s post_sl_map_support_loss_at=%s post_sl_map_support_loss_direction=%s post_sl_map_support_loss_tf=%s post_sl_map_support_loss_owner_id=%s root_invalidated_at=%s root_invalidation_reason=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s strategy_authority=false",
      r.scenario_id,DirectionName(r.direction),outcome,EdgeAuditTimeOrNA(r.d148_sl_at),EdgeAuditTimeOrNA(at),px,r.fill_price,r.risk_distance,
      r.d148_pre_sl_mfe_r,r.d148_pre_sl_mae_r,r.d148_map_support_same_at_sl ? "true" : "false",
      r.d148_entry_recovered_after_sl ? "true" : "false",EdgeAuditTimeOrNA(r.d148_entry_recovered_at),
      r.d148_one_r_recovered_after_sl ? "true" : "false",EdgeAuditTimeOrNA(r.d148_one_r_recovered_at),
      r.d148_post_sl_max_adverse_r_from_fill,extra_beyond_sl,r.d148_post_sl_max_favorable_r_from_fill,
      r.d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(r.d148_frozen_owner_invalidated_at),
      EdgeAuditTimeOrNA(r.d148_first_map_support_loss_at),DirectionName(r.d148_first_map_support_loss_direction),
      r.d148_first_map_support_loss_tf=="" ? "NA" : r.d148_first_map_support_loss_tf,
      r.d148_first_map_support_loss_owner_id=="" ? "NA" : r.d148_first_map_support_loss_owner_id,
      EdgeAuditTimeOrNA(r.d148_post_sl_map_support_loss_at),DirectionName(r.d148_post_sl_map_support_loss_direction),
      r.d148_post_sl_map_support_loss_tf=="" ? "NA" : r.d148_post_sl_map_support_loss_tf,
      r.d148_post_sl_map_support_loss_owner_id=="" ? "NA" : r.d148_post_sl_map_support_loss_owner_id,
      EdgeAuditTimeOrNA(r.d148_root_invalidated_at),r.d148_root_invalidation_reason=="" ? "NA" : r.d148_root_invalidation_reason,
      map_tf,map_owner,DirectionName(map_dir));
   detail+=" "+EdgeAuditD148PostSlEventDelta(r);
   if(r.scenario_index>=0 && r.scenario_index<ArraySize(g_scenarios) && g_scenarios[r.scenario_index].valid)
      detail+=" "+EdgeAuditRunnerMarketContext(g_scenarios[r.scenario_index],at,px,r.risk_distance,"d148_terminal");
   EdgeAuditWrite("EDGE_AUDIT_D148_TERMINAL","TICK",at,r.scenario_id,detail);
   if(outcome=="ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS") g_edge_d148_one_r_recoveries++;
   else g_edge_d148_map_loss_terminals++;
  }

void EdgeAuditD148OnOneRBeforeSl(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(!r.d148_eligible || r.d148_pre_sl_resolved) return;
   r.d148_pre_sl_resolved=true;
   r.d148_terminal=true;
   r.d148_terminal_outcome="ONE_R_CONTROL";
   r.d148_resolved_at=at;
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   EdgeAuditWrite("EDGE_AUDIT_D148_1R_CONTROL","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s direction=%s one_r_at=%s exit_side_price=%.10f fill_price=%.10f risk_distance=%.10f pre_1r_mfe_r=%.10f pre_1r_mae_r=%.10f frozen_owner_invalidated_before_1r=%s frozen_owner_invalidated_at=%s map_support_loss_seen_before_1r=%s first_map_support_loss_at=%s root_invalidated_before_1r=%s root_invalidated_at=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s strategy_authority=false",
         r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(at),px,r.fill_price,r.risk_distance,r.max_favorable_r,r.max_adverse_r,
         r.d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(r.d148_frozen_owner_invalidated_at),
         r.d148_map_support_loss_seen ? "true" : "false",EdgeAuditTimeOrNA(r.d148_first_map_support_loss_at),
         r.d148_root_invalidated_at>0 ? "true" : "false",EdgeAuditTimeOrNA(r.d148_root_invalidated_at),map_tf,map_owner,DirectionName(map_dir)));
   g_edge_d148_one_r_controls++;
  }

void EdgeAuditD148FreezeSlCounters(V1EdgeRunnerTracker &r)
  {
   r.d148_h1_same_events_at_sl=EdgeAuditDirCounter(PERIOD_H1,r.direction);
   r.d148_h1_opp_events_at_sl=EdgeAuditDirCounter(PERIOD_H1,-r.direction);
   r.d148_m30_same_events_at_sl=EdgeAuditDirCounter(PERIOD_M30,r.direction);
   r.d148_m30_opp_events_at_sl=EdgeAuditDirCounter(PERIOD_M30,-r.direction);
   r.d148_m1_same_events_at_sl=EdgeAuditDirCounter(PERIOD_M1,r.direction);
   r.d148_m1_opp_events_at_sl=EdgeAuditDirCounter(PERIOD_M1,-r.direction);
   r.d148_h1_same_pb_at_sl=EdgeAuditPbCounter(PERIOD_H1,r.direction);
   r.d148_h1_opp_pb_at_sl=EdgeAuditPbCounter(PERIOD_H1,-r.direction);
   r.d148_m30_same_pb_at_sl=EdgeAuditPbCounter(PERIOD_M30,r.direction);
   r.d148_m30_opp_pb_at_sl=EdgeAuditPbCounter(PERIOD_M30,-r.direction);
   r.d148_m1_same_pb_at_sl=EdgeAuditPbCounter(PERIOD_M1,r.direction);
   r.d148_m1_opp_pb_at_sl=EdgeAuditPbCounter(PERIOD_M1,-r.direction);
  }

void EdgeAuditD148OnSlFirst(V1EdgeRunnerTracker &r,const datetime at,const double px,const double signed_r)
  {
   if(!r.d148_eligible || r.d148_pre_sl_resolved) return;
   r.d148_pre_sl_resolved=true;
   r.d148_sl_at=at;
   r.d148_sl_exit_side_price=px;
   r.d148_pre_sl_mfe_r=r.max_favorable_r;
   r.d148_pre_sl_mae_r=r.max_adverse_r;
   r.d148_post_sl_max_adverse_r_from_fill=MathMax(0.0,-signed_r);
   r.d148_post_sl_max_favorable_r_from_fill=signed_r;
   EdgeAuditD148FreezeSlCounters(r);
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   r.d148_map_support_same_at_sl=(map_dir==r.direction);
   g_edge_d148_sl_failures++;
   string detail=StringFormat("scenario_id=%s direction=%s sl_at=%s exit_side_price=%.10f fill_price=%.10f normalized_sl=%.10f risk_distance=%.10f pre_sl_mfe_r=%.10f pre_sl_mae_r=%.10f active_map_tf_at_plan=%s frozen_owner_id=%s frozen_owner_alive_at_fill=%s frozen_owner_invalidated_before_sl=%s frozen_owner_invalidated_at=%s map_support_loss_seen_before_sl=%s first_map_support_loss_at=%s map_support_same_at_sl=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s root_id=%s root_invalidated_before_sl=%s root_invalidated_at=%s root_invalidation_reason=%s strategy_authority=false",
      r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(at),px,r.fill_price,r.normalized_sl,r.risk_distance,
      r.d148_pre_sl_mfe_r,r.d148_pre_sl_mae_r,TfName((ENUM_TIMEFRAMES)r.d148_original_map_tf),
      r.d148_original_owner_id=="" ? "NA" : r.d148_original_owner_id,r.d148_original_authority_alive_at_fill ? "true" : "false",
      r.d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(r.d148_frozen_owner_invalidated_at),
      r.d148_map_support_loss_seen ? "true" : "false",EdgeAuditTimeOrNA(r.d148_first_map_support_loss_at),
      r.d148_map_support_same_at_sl ? "true" : "false",map_tf,map_owner,DirectionName(map_dir),
      r.d148_root_id=="" ? "NA" : r.d148_root_id,r.d148_root_invalidated_at>0 ? "true" : "false",
      EdgeAuditTimeOrNA(r.d148_root_invalidated_at),r.d148_root_invalidation_reason=="" ? "NA" : r.d148_root_invalidation_reason);
   if(r.scenario_index>=0 && r.scenario_index<ArraySize(g_scenarios) && g_scenarios[r.scenario_index].valid)
      detail+=" "+EdgeAuditRunnerMarketContext(g_scenarios[r.scenario_index],at,px,r.risk_distance,"d148_sl");
   EdgeAuditWrite("EDGE_AUDIT_D148_SL_FAILURE","TICK",at,r.scenario_id,detail);
   r.d148_post_sl_active=true;
   if(!r.d148_map_support_same_at_sl)
      EdgeAuditD148Terminal(r,"MAP_SUPPORT_NOT_SAME_AT_SL",at,px);
  }

void EdgeAuditD148TrackPostSl(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(!r.d148_post_sl_active || r.d148_terminal || r.risk_distance<=0.0) return;
   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;
   if(-signed_r>r.d148_post_sl_max_adverse_r_from_fill) r.d148_post_sl_max_adverse_r_from_fill=-signed_r;
   if(signed_r>r.d148_post_sl_max_favorable_r_from_fill) r.d148_post_sl_max_favorable_r_from_fill=signed_r;
   bool hit_entry=(r.direction>0 ? px>=r.fill_price : px<=r.fill_price);
   bool hit_one=(r.direction>0 ? px>=r.target_1r : px<=r.target_1r);
   if(hit_entry && !r.d148_entry_recovered_after_sl)
     {
      r.d148_entry_recovered_after_sl=true;
      r.d148_entry_recovered_at=at;
      g_edge_d148_entry_recoveries++;
      EdgeAuditWrite("EDGE_AUDIT_D148_ENTRY_RECOVERED","TICK",at,r.scenario_id,
         StringFormat("scenario_id=%s direction=%s sl_at=%s entry_recovered_at=%s exit_side_price=%.10f post_sl_max_adverse_r_from_fill=%.10f strategy_authority=false",
                      r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.d148_sl_at),EdgeAuditTimeOrNA(at),px,r.d148_post_sl_max_adverse_r_from_fill));
     }
   if(hit_one)
     {
      r.d148_one_r_recovered_after_sl=true;
      r.d148_one_r_recovered_at=at;
      EdgeAuditD148Terminal(r,"ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS",at,px);
     }
  }

void EdgeAuditD148OnStructureEvent(const V1StructureState &state,const int event_type,const int direction,const datetime available_at)
  {
   if(event_type!=V1_EVENT_PROTECTED_BREAK) return;
   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid || !g_edge_runners[i].d148_eligible || g_edge_runners[i].d148_terminal || g_edge_runners[i].d148_frozen_owner_invalidated) continue;
      if((int)state.tf!=g_edge_runners[i].d148_original_map_tf) continue;
      if(g_edge_runners[i].d148_original_owner_id=="" || state.owner_id!=g_edge_runners[i].d148_original_owner_id) continue;
      g_edge_runners[i].d148_frozen_owner_invalidated=true;
      g_edge_runners[i].d148_frozen_owner_invalidated_at=available_at;
      g_edge_d148_frozen_owner_invalidations++;
      EdgeAuditWrite("EDGE_AUDIT_D148_FROZEN_OWNER_INVALIDATED",TfName(state.tf),available_at,g_edge_runners[i].scenario_id,
         StringFormat("scenario_id=%s direction=%s active_map_tf_at_plan=%s frozen_owner_id=%s event_direction=%s invalidated_at=%s pre_sl_resolved=%s post_sl_active=%s callback_state_is_pre_transition=true protected_break_itself_is_causal_invalidation=true strategy_authority=false",
                      g_edge_runners[i].scenario_id,DirectionName(g_edge_runners[i].direction),TfName((ENUM_TIMEFRAMES)g_edge_runners[i].d148_original_map_tf),g_edge_runners[i].d148_original_owner_id,
                      DirectionName(direction),EdgeAuditTimeOrNA(available_at),g_edge_runners[i].d148_pre_sl_resolved ? "true" : "false",g_edge_runners[i].d148_post_sl_active ? "true" : "false"));
     }
  }

void EdgeAuditD148OnRootInvalidated(const V1SourceZone &root,const datetime available_at,const string reason)
  {
   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid || !g_edge_runners[i].d148_eligible || g_edge_runners[i].d148_terminal || g_edge_runners[i].d148_root_invalidated_at>0) continue;
      if(g_edge_runners[i].d148_root_id=="" || root.id!=g_edge_runners[i].d148_root_id) continue;
      g_edge_runners[i].d148_root_invalidated_at=available_at;
      g_edge_runners[i].d148_root_invalidation_reason=reason;
      g_edge_d148_root_invalidations++;
      EdgeAuditWrite("EDGE_AUDIT_D148_ROOT_INVALIDATED",TfName(root.tf),available_at,g_edge_runners[i].scenario_id,
         StringFormat("scenario_id=%s direction=%s root_id=%s root_tf=%s invalidated_at=%s reason=%s pre_sl_resolved=%s post_sl_active=%s strategy_authority=false",
                      g_edge_runners[i].scenario_id,DirectionName(g_edge_runners[i].direction),root.id,TfName(root.tf),EdgeAuditTimeOrNA(available_at),reason,
                      g_edge_runners[i].d148_pre_sl_resolved ? "true" : "false",g_edge_runners[i].d148_post_sl_active ? "true" : "false"));
     }
  }

void EdgeAuditD148OnMapSample(const datetime available_at,const string sample_reason)
  {
   int map_dir=0; string map_tf="NONE",map_owner="NA";
   EdgeAuditD148CurrentMapState(map_dir,map_tf,map_owner);
   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid || !g_edge_runners[i].d148_eligible || g_edge_runners[i].d148_terminal) continue;
      if(map_dir==g_edge_runners[i].direction) continue;
      if(!g_edge_runners[i].d148_map_support_loss_seen)
        {
         g_edge_runners[i].d148_map_support_loss_seen=true;
         g_edge_runners[i].d148_first_map_support_loss_at=available_at;
         g_edge_runners[i].d148_first_map_support_loss_direction=map_dir;
         g_edge_runners[i].d148_first_map_support_loss_tf=map_tf;
         g_edge_runners[i].d148_first_map_support_loss_owner_id=map_owner;
         EdgeAuditWrite("EDGE_AUDIT_D148_MAP_SUPPORT_LOST",map_tf,available_at,g_edge_runners[i].scenario_id,
            StringFormat("scenario_id=%s direction=%s lost_at=%s sample_reason=%s current_highest_map_tf=%s current_map_owner_id=%s current_map_direction=%s pre_sl_resolved=%s post_sl_active=%s frozen_owner_invalidated=%s frozen_owner_invalidated_at=%s strategy_authority=false",
                         g_edge_runners[i].scenario_id,DirectionName(g_edge_runners[i].direction),EdgeAuditTimeOrNA(available_at),sample_reason,map_tf,map_owner,DirectionName(map_dir),
                         g_edge_runners[i].d148_pre_sl_resolved ? "true" : "false",g_edge_runners[i].d148_post_sl_active ? "true" : "false",
                         g_edge_runners[i].d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(g_edge_runners[i].d148_frozen_owner_invalidated_at)));
        }
      if(g_edge_runners[i].d148_post_sl_active)
        {
         if(g_edge_runners[i].d148_post_sl_map_support_loss_at<=0)
           {
            g_edge_runners[i].d148_post_sl_map_support_loss_at=available_at;
            g_edge_runners[i].d148_post_sl_map_support_loss_direction=map_dir;
            g_edge_runners[i].d148_post_sl_map_support_loss_tf=map_tf;
            g_edge_runners[i].d148_post_sl_map_support_loss_owner_id=map_owner;
           }
         double map_px=(g_edge_runners[i].direction>0 ? SymbolInfoDouble(_Symbol,SYMBOL_BID) : SymbolInfoDouble(_Symbol,SYMBOL_ASK));
         EdgeAuditD148Terminal(g_edge_runners[i],"MAP_SUPPORT_LOST_AFTER_SL",available_at,map_px);
        }
     }
  }

void EdgeAuditD148Censor(V1EdgeRunnerTracker &r,const datetime at)
  {
   if(!r.d148_eligible || r.d148_terminal) return;
   if(r.d148_post_sl_active)
     {
      r.d148_post_sl_active=false;
      r.d148_terminal=true;
      r.d148_terminal_outcome="RIGHT_CENSORED_AFTER_SL";
      r.d148_resolved_at=at;
      g_edge_d148_censored++;
      EdgeAuditWrite("EDGE_AUDIT_D148_CENSORED","TICK",at,r.scenario_id,
         StringFormat("scenario_id=%s direction=%s sl_at=%s censored_at=%s entry_recovered_after_sl=%s entry_recovered_at=%s post_sl_max_adverse_r_from_fill=%.10f post_sl_max_favorable_r_from_fill=%.10f frozen_owner_invalidated=%s frozen_owner_invalidated_at=%s first_map_support_loss_at=%s tester_end_right_censored=true strategy_authority=false",
                      r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.d148_sl_at),EdgeAuditTimeOrNA(at),
                      r.d148_entry_recovered_after_sl ? "true" : "false",EdgeAuditTimeOrNA(r.d148_entry_recovered_at),
                      r.d148_post_sl_max_adverse_r_from_fill,r.d148_post_sl_max_favorable_r_from_fill,
                      r.d148_frozen_owner_invalidated ? "true" : "false",EdgeAuditTimeOrNA(r.d148_frozen_owner_invalidated_at),
                      EdgeAuditTimeOrNA(r.d148_first_map_support_loss_at)));
      return;
     }
   if(!r.d148_pre_sl_resolved)
     {
      r.d148_terminal=true;
      r.d148_terminal_outcome="RIGHT_CENSORED_BEFORE_1R_OR_SL";
      r.d148_resolved_at=at;
      g_edge_d148_pre_sl_censored++;
      EdgeAuditWrite("EDGE_AUDIT_D148_PRE_SL_CENSORED","TICK",at,r.scenario_id,
         StringFormat("scenario_id=%s direction=%s fill_at=%s censored_at=%s max_favorable_r=%.10f max_adverse_r=%.10f tester_end_right_censored=true strategy_authority=false",
                      r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),EdgeAuditTimeOrNA(at),r.max_favorable_r,r.max_adverse_r));
     }
  }

'''


def transform_ea(text: str) -> str:
    t = normalize(text)
    t = replace_once(t,
        '#property description "Mentor deterministic V1 EA - D-147 exit-architecture research harness"',
        '#property description "Mentor deterministic V1 EA - D-148 entry-survival failure-taxonomy shadow audit harness"',
        "EA property description")
    t = replace_once(t,
        '// D-146 shadow-only CONTINUATION STATE AUDIT implementation.\n#include "EdgeAuditV1.mqh"',
        '// D-148 shadow-only ENTRY SURVIVAL FAILURE TAXONOMY implementation; D-146 post-1R tracker remains dormant.\n#include "EdgeAuditV1.mqh"',
        "EA audit include comment")
    t = replace_once(t,
        'build=1.93R1L9 property_version=1.00 magic=%I64d phase=EXIT_ARCHITECTURE_RESEARCH_V1 strategy_semantics=D134_ENTRY_INITIAL_GEOMETRY_UNCHANGED_D147_EXIT_VARIANT',
        'build=1.94R1L10 property_version=1.00 magic=%I64d phase=ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW strategy_semantics=D134_ENTRY_INITIAL_GEOMETRY_UNCHANGED_D147_EXIT_TOGGLE_PRESENT_D148_AUDIT_ONLY',
        "EA_START identity")
    return normalize(t)


def transform_edge(text: str) -> str:
    t = normalize(text)
    t = replace_once(t,
        '//| D-146 CONTINUATION STATE AUDIT -- shadow measurement          |',
        '//| D-148 ENTRY SURVIVAL FAILURE TAXONOMY -- shadow measurement   |',
        "Edge header phase")
    t = replace_once(t,
        '#define V1_EDGE_AUDIT_BUILD       "1.92R1L8"\n#define V1_EDGE_AUDIT_PHASE       "CONTINUATION_STATE_AUDIT_V1_SHADOW"',
        '#define V1_EDGE_AUDIT_BUILD       "1.94R1L10"\n#define V1_EDGE_AUDIT_PHASE       "ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW"',
        "Edge build phase")

    field_anchor = '   datetime   d146_first_deterioration_at;\n  };\n'
    t = replace_once(t, field_anchor, '   datetime   d146_first_deterioration_at;\n' + D148_FIELDS + '  };\n', "D148 runner fields")

    global_anchor = 'long g_edge_d146_censored=0;\n\n// Event counters are observation-only.'
    t = replace_once(t, global_anchor, 'long g_edge_d146_censored=0;\n' + D148_GLOBALS + '\n// Event counters are observation-only.', "D148 globals")

    process_anchor = 'void EdgeAuditProcessRunner(V1EdgeRunnerTracker &r,const MqlTick &tick)\n'
    t = replace_once(t, process_anchor, D148_HELPERS + process_anchor, "D148 helper insertion")

    runner_tick_anchor = '''   double px=(r.direction>0 ? tick.bid : tick.ask);\n   if(px<=0.0 || r.risk_distance<=0.0) return;\n   r.ticks_seen++;\n   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;\n   if(signed_r>r.max_favorable_r) r.max_favorable_r=signed_r;\n'''
    runner_tick_new = '''   double px=(r.direction>0 ? tick.bid : tick.ask);\n   if(px<=0.0 || r.risk_distance<=0.0) return;\n   r.ticks_seen++;\n   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;\n   if(r.d148_post_sl_active)\n     {\n      EdgeAuditD148TrackPostSl(r,(datetime)tick.time,px);\n      return;\n     }\n   if(signed_r>r.max_favorable_r) r.max_favorable_r=signed_r;\n'''
    t = replace_once(t, runner_tick_anchor, runner_tick_new, "post-SL tracking branch")

    hit1_anchor = '''      r.first_1r_at=(datetime)tick.time;\n      EdgeAuditEmitRunnerOutcome(r,"1R","REACHED_BEFORE_SL",(datetime)tick.time,px);\n'''
    hit1_new = '''      r.first_1r_at=(datetime)tick.time;\n      EdgeAuditD148OnOneRBeforeSl(r,(datetime)tick.time,px);\n      EdgeAuditEmitRunnerOutcome(r,"1R","REACHED_BEFORE_SL",(datetime)tick.time,px);\n'''
    t = replace_once(t, hit1_anchor, hit1_new, "D148 +1R control hook")

    d146_arm_anchor = '      EdgeAuditD146Arm(r,(datetime)tick.time,px);\n'
    d146_arm_new = '      // D-148 intentionally does not arm D-146 post-1R continuation tracking.\n'
    t = replace_once(t, d146_arm_anchor, d146_arm_new, "D148 dormant D146 arm")

    sl_anchor = '''   if(hit_sl)\n     {\n      if(r.d146_active && r.reached_1r) EdgeAuditD146Terminal(r,"SL_AFTER_1R",(datetime)tick.time,px);\n      if(!r.resolved_1r) { r.resolved_1r=true; EdgeAuditEmitRunnerOutcome(r,"1R","SL_FIRST",(datetime)tick.time,px); }\n'''
    sl_new = '''   if(hit_sl)\n     {\n      if(!r.reached_1r) EdgeAuditD148OnSlFirst(r,(datetime)tick.time,px,signed_r);\n      if(r.d146_active && r.reached_1r) EdgeAuditD146Terminal(r,"SL_AFTER_1R",(datetime)tick.time,px);\n      if(!r.resolved_1r) { r.resolved_1r=true; EdgeAuditEmitRunnerOutcome(r,"1R","SL_FIRST",(datetime)tick.time,px); }\n'''
    t = replace_once(t, sl_anchor, sl_new, "D148 SL-first hook")

    reset_anchor = '''   g_edge_d146_terminals=0;\n   g_edge_d146_censored=0;\n   ArrayInitialize(g_edge_h1_dir_events,0);\n'''
    reset_new = '''   g_edge_d146_terminals=0;\n   g_edge_d146_censored=0;\n   g_edge_d148_eligible=0;\n   g_edge_d148_one_r_controls=0;\n   g_edge_d148_sl_failures=0;\n   g_edge_d148_entry_recoveries=0;\n   g_edge_d148_one_r_recoveries=0;\n   g_edge_d148_map_loss_terminals=0;\n   g_edge_d148_frozen_owner_invalidations=0;\n   g_edge_d148_root_invalidations=0;\n   g_edge_d148_censored=0;\n   g_edge_d148_pre_sl_censored=0;\n   ArrayInitialize(g_edge_h1_dir_events,0);\n'''
    t = replace_once(t, reset_anchor, reset_new, "D148 counter reset")

    init_anchor = '''   EdgeAuditWrite("EDGE_AUDIT_START","",TimeCurrent(),"",\n      StringFormat("build=%s phase=%s strategy_authority=false unified_ledger=true event_csv=%s lightweight=true tick_tracking=PREFILL_FVG_SELECTED|ACTUAL_FILL|D146_POST_1R_CONTINUATION_ONLY front_end_forward_labels=false stage_virtual_barriers=false mirror_direction=false fill_snapshot=true first_1r_snapshot=true d146_post_1r_state=true d146_population=EXTERNAL_CONTINUATION_1R_SUCCESS d146_terminal=EXACT_2R_OR_NORMALIZED_SL hypotheses=M30_OUTWARD_EXTERNAL_REFRESH|M30_DETERIORATION future_backfill=false strategy_change=false",\n                   V1_EDGE_AUDIT_BUILD,V1_EDGE_AUDIT_PHASE,InpEventCsvFile));\n'''
    init_new = '''   EdgeAuditWrite("EDGE_AUDIT_START","",TimeCurrent(),"",\n      StringFormat("build=%s phase=%s strategy_authority=false unified_ledger=true event_csv=%s lightweight=true tick_tracking=CONTINUATION_PREFILL_FVG_SELECTED|CONTINUATION_ACTUAL_FILL_TO_1R_OR_SL|D148_POST_SL_FAILURE_ONLY front_end_forward_labels=false stage_virtual_barriers=false mirror_direction=false fill_snapshot=true first_1r_snapshot=true d146_post_1r_state=false d148_entry_survival_taxonomy=true d148_population=EXTERNAL_CONTINUATION_SL_BEFORE_1R d148_terminal=ORIGINAL_1R_RECOVERY_OR_MAP_SUPPORT_LOSS_OR_CENSOR d148_exit_mode_required=ORIGINAL observed_exit_mode=%s d148_no_time_cutoff=true d148_frozen_owner_break_is_context_not_terminal=true future_backfill=false strategy_change=false",\n                   V1_EDGE_AUDIT_BUILD,V1_EDGE_AUDIT_PHASE,InpEventCsvFile,ExitManagementModeName((int)InpExitManagementMode)));\n'''
    t = replace_once(t, init_anchor, init_new, "D148 audit start identity")

    structure_anchor = '''   EdgeAuditCountStructureEvent(state.tf,event_type,direction);\n   if(state.tf==PERIOD_M30)\n      EdgeAuditD146OnM30StructureEvent(state,event_type,direction,broken,protected_ref,bar,available_at);\n'''
    structure_new = '''   EdgeAuditCountStructureEvent(state.tf,event_type,direction);\n   EdgeAuditD148OnStructureEvent(state,event_type,direction,available_at);\n   // D-146 post-1R mechanism tracking is intentionally dormant in D-148.\n'''
    t = replace_once(t, structure_anchor, structure_new, "D148 structure event hook")

    root_anchor = '''   if(!g_edge_enabled || !root.valid || root.kind!=V1_SOURCE_ROOT)\n      return;\n   int index=EdgeAuditFindRootMeta(root.id);\n   if(index>=0) EdgeAuditRemoveRootMetaAt(index);\n'''
    root_new = '''   if(!g_edge_enabled || !root.valid || root.kind!=V1_SOURCE_ROOT)\n      return;\n   EdgeAuditD148OnRootInvalidated(root,available_at,reason);\n   int index=EdgeAuditFindRootMeta(root.id);\n   if(index>=0) EdgeAuditRemoveRootMetaAt(index);\n'''
    t = replace_once(t, root_anchor, root_new, "D148 Root invalidation hook")

    prefill_scope_anchor = '   if(stage==V1_EDGE_STAGE_FVG)\n      EdgeAuditArmPrefill(scenario_index,stage_at);\n'
    prefill_scope_new = '   if(stage==V1_EDGE_STAGE_FVG && g_scenarios[scenario_index].scope==V1_SCOPE_EXTERNAL_CONTINUATION)\n      EdgeAuditArmPrefill(scenario_index,stage_at);\n'
    t = replace_once(t, prefill_scope_anchor, prefill_scope_new, "D148 continuation-only prefill scope")

    mapsample_anchor = '''void EdgeAuditOnMapSample(const datetime available_at,const string sample_reason)\n  {\n   // Disabled in D-145. Persistent MAP forward sampling was completed in D-143.\n   return;\n  }\n'''
    mapsample_new = '''void EdgeAuditOnMapSample(const datetime available_at,const string sample_reason)\n  {\n   // Persistent forward labels remain disabled. D-148 only checks the current\n   // H1/M30 directional support at completed timestamp groups for active taxonomy trackers.\n   if(!g_edge_enabled) return;\n   EdgeAuditD148OnMapSample(available_at,sample_reason);\n  }\n'''
    t = replace_once(t, mapsample_anchor, mapsample_new, "D148 completed-map sampling")

    continuation_runner_anchor = '   int old=EdgeAuditFindPrefill(p.id); if(old>=0) EdgeAuditRemovePrefillAt(old);\n\n   int n=ArraySize(g_edge_runners);\n'
    continuation_runner_new = '   int old=EdgeAuditFindPrefill(p.id); if(old>=0) EdgeAuditRemovePrefillAt(old);\n\n   // D-148 runner population is continuation-only. Reversal outcomes are outside this research question.\n   if(p.scope!=V1_SCOPE_EXTERNAL_CONTINUATION) return;\n\n   int n=ArraySize(g_edge_runners);\n'
    t = replace_once(t, continuation_runner_anchor, continuation_runner_new, "D148 continuation-only runner population")

    fill_reset_anchor = '   EdgeAuditD146ResetRunner(r);\n   r.h1_same_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_H1,p.direction);\n'
    fill_reset_new = '   EdgeAuditD146ResetRunner(r);\n   EdgeAuditD148ArmAtFill(r,p,observed_at);\n   r.h1_same_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_H1,p.direction);\n'
    t = replace_once(t, fill_reset_anchor, fill_reset_new, "D148 fill arm")

    remove_anchor = '''      if(g_edge_runners[i].resolved_1r && g_edge_runners[i].resolved_2r &&\n         g_edge_runners[i].resolved_3r && g_edge_runners[i].resolved_structural)\n        { EdgeAuditRemoveRunnerAt(i); continue; }\n'''
    remove_new = '''      if(g_edge_runners[i].d148_terminal && g_edge_runners[i].d148_terminal_outcome=="ONE_R_CONTROL")\n        { EdgeAuditRemoveRunnerAt(i); continue; }\n      if(g_edge_runners[i].resolved_1r && g_edge_runners[i].resolved_2r &&\n         g_edge_runners[i].resolved_3r && g_edge_runners[i].resolved_structural &&\n         !g_edge_runners[i].d148_post_sl_active)\n        { EdgeAuditRemoveRunnerAt(i); continue; }\n'''
    t = replace_once(t, remove_anchor, remove_new, "retain post-SL D148 tracker")

    deinit_runner_anchor = '''      if(!g_edge_runners[i].valid) continue;\n      if(g_edge_runners[i].d146_active) EdgeAuditD146Censor(g_edge_runners[i],now);\n      EdgeAuditWrite("EDGE_AUDIT_RUNNER_CENSORED","TICK",now,g_edge_runners[i].scenario_id,\n'''
    deinit_runner_new = '''      if(!g_edge_runners[i].valid) continue;\n      if(g_edge_runners[i].d146_active) EdgeAuditD146Censor(g_edge_runners[i],now);\n      EdgeAuditD148Censor(g_edge_runners[i],now);\n      EdgeAuditWrite("EDGE_AUDIT_RUNNER_CENSORED","TICK",now,g_edge_runners[i].scenario_id,\n'''
    t = replace_once(t, deinit_runner_anchor, deinit_runner_new, "D148 deinit censor")

    stop_anchor = '''      StringFormat("reason=%d rows=%I64d fill_snapshots=%I64d one_r_snapshots=%I64d runner_outcomes=%I64d runner_skipped=%I64d d146_armed=%I64d d146_structure_events=%I64d d146_original_external_deliveries=%I64d d146_terminals=%I64d d146_censored=%I64d active_prefill=%d active_runners=%d front_end_forward_labels=false stage_virtual_barriers=false lightweight=true strategy_authority=false",\n                   reason,g_edge_rows,g_edge_runner_fill_snapshots,g_edge_runner_one_r_snapshots,g_edge_runner_outcomes,\n                   g_edge_runner_skipped,g_edge_d146_armed,g_edge_d146_structure_events,g_edge_d146_original_external_deliveries,\n                   g_edge_d146_terminals,g_edge_d146_censored,ArraySize(g_edge_prefill),ArraySize(g_edge_runners)));\n'''
    stop_new = '''      StringFormat("reason=%d rows=%I64d fill_snapshots=%I64d one_r_snapshots=%I64d runner_outcomes=%I64d runner_skipped=%I64d d146_armed=%I64d d146_structure_events=%I64d d146_original_external_deliveries=%I64d d146_terminals=%I64d d146_censored=%I64d d148_eligible=%I64d d148_one_r_controls=%I64d d148_sl_failures=%I64d d148_entry_recoveries=%I64d d148_one_r_recoveries=%I64d d148_map_loss_terminals=%I64d d148_frozen_owner_invalidations=%I64d d148_root_invalidations=%I64d d148_censored=%I64d d148_pre_sl_censored=%I64d active_prefill=%d active_runners=%d front_end_forward_labels=false stage_virtual_barriers=false lightweight=true strategy_authority=false",\n                   reason,g_edge_rows,g_edge_runner_fill_snapshots,g_edge_runner_one_r_snapshots,g_edge_runner_outcomes,\n                   g_edge_runner_skipped,g_edge_d146_armed,g_edge_d146_structure_events,g_edge_d146_original_external_deliveries,\n                   g_edge_d146_terminals,g_edge_d146_censored,g_edge_d148_eligible,g_edge_d148_one_r_controls,g_edge_d148_sl_failures,\n                   g_edge_d148_entry_recoveries,g_edge_d148_one_r_recoveries,g_edge_d148_map_loss_terminals,g_edge_d148_frozen_owner_invalidations,\n                   g_edge_d148_root_invalidations,g_edge_d148_censored,g_edge_d148_pre_sl_censored,ArraySize(g_edge_prefill),ArraySize(g_edge_runners)));\n'''
    t = replace_once(t, stop_anchor, stop_new, "D148 stop counters")
    return normalize(t)


D148_HANDOFF_BLOCK = r'''
## D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / LOCAL COMPILE + AUDIT PARITY PENDING

D-147 established that post-+1R profit giveback and pre-+1R Entry survival are different problems. GOLD 2025 mechanical partial exits improved realized win-rate / drawdown behavior but did not change the 21 continuation trades that hit the original SL before +1R.

D-148 now studies only:

```text
actual filled EXTERNAL_CONTINUATION
+
normalized SL reached before first +1R
```

D-148 is shadow-only. It does not change Entry, SL, TP, exit mode, order lifecycle, sizing, map authority, or scenario authorization.

For each failure it freezes exact SL-first time, then keeps a private shadow tracker after the real position is closed until the first of:

```text
original +1R price recovered
current H1/M30 map no longer supports the trade direction
Strategy Tester end (right censor)
```

`frozen owner invalidated` and `Root invalidated` are recorded separately. A frozen M30 owner break is not automatically treated as a directional premise failure because a same-direction H1/M30 successor authority may exist.

Required test configuration:

```text
InpExitManagementMode = V1_EXIT_ORIGINAL
InpEnableEdgeAudit = true for the audit run
InpRegimeResearchMode = V1_REGIME_BASELINE_NO_GATE
InpStopLossModel = V1_SL_ROOT_OB_DISTAL_20
InpPositionSizingMode = V1_SIZE_FIXED_RISK_MONEY
InpFixedRiskMoneyPerTrade = 100
InpEventLogMode = V1_LOG_RESEARCH_COMPACT
Every tick based on real ticks
```

Validation order:

```text
1. MetaEditor compile = 0 errors
2. short GOLD audit OFF/ON non-audit parity PASS
3. GOLD 2025 full Audit ON
4. summarize_d148_entry_survival_failure_taxonomy.py => EVENT INTEGRITY PASS
5. classify early-entry/stop-sensitivity vs map-premise failure before designing any Entry filter
```

No pooled threshold optimization. 2021 remains untouched.
'''

D148_STATE_BLOCK = r'''
## D-148 Entry-survival failure taxonomy

Current priority shifts to the `Fill -> +1R` branch on GOLD while D-147 exit management remains a separate research branch.

Primary D-148 question:

> When a continuation fill reaches the original normalized SL before +1R, was the higher-timeframe directional premise already losing causal support, or did price stop the trade while the same direction remained structurally supported and later recover?

Primary outcomes are causal sequence outcomes, not fitted features:

```text
ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS
MAP_SUPPORT_NOT_SAME_AT_SL
MAP_SUPPORT_LOST_AFTER_SL
RIGHT_CENSORED_AFTER_SL
```

The frozen PLAN owner and Root are tracked as context. Their invalidation is not automatically equated with total direction failure.

This phase is taxonomy/measurement only. Any future Entry timing, SL, M1 confirmation, Root-depth, or map-quality rule must be proposed only after the failure classes are measured.
'''

D148_BACKLOG_BLOCK = r'''
## P0 — D-148 Entry-survival failure taxonomy

- [x] define population as `EXTERNAL_CONTINUATION + normalized SL before +1R`
- [x] keep exact Fill-to-SL risk and exact Bid/Ask barrier semantics
- [x] freeze original PLAN map timeframe/owner and Root identity
- [x] record frozen-owner protected break separately from total map-direction support
- [x] record Root invalidation separately
- [x] after SL, shadow-track original Entry recovery and original +1R recovery
- [x] terminalize on +1R recovery vs current H1/M30 direction-support loss vs right censor
- [x] no arbitrary post-SL time cutoff
- [x] retain runner after real position close without changing broker/strategy state
- [ ] MetaEditor compile 0 errors
- [ ] GOLD short audit OFF/ON non-audit parity PASS
- [ ] GOLD 2025 D-148 EVENT INTEGRITY PASS
- [ ] classify the 21 GOLD 2025 `<1R` failures by causal outcome
- [ ] compare causal pre-Fill context across failure classes and +1R controls
- [ ] decide whether D-148B needs extra M1 reaction-strength / correction-completion instrumentation
- [ ] validate any discovered relation on other GOLD years before strategy authority

### Future — smart partial management (recorded, not active)

- [ ] revisit `R_STEP_PARTIAL` together with D-145/D-146 continuation state so the fraction left as runner can depend on causally available post-+1R structure rather than a blind fixed 50%
- [ ] preserve a mechanical PARTIAL control when that study begins
- [ ] do not optimize a pooled M30-progress cutoff or partial fraction from GOLD 2025
'''

D148_DECISION_BLOCK = r'''
## D-148 — classify `<1R` failures before changing Entry

Status: ACTIVE RESEARCH DECISION / ZERO STRATEGY AUTHORITY

GOLD 2025 D-147 confirmed that exit management can repair profit giveback only after favorable excursion exists. The continuation trades that never reached +1R were unchanged across ORIGINAL / TRAILING / PARTIAL.

Therefore the next research branch isolates `Fill -> +1R` failure and asks whether each SL-first trade is better explained by:

```text
higher-timeframe direction support failure
vs
entry/correction timing or SL sensitivity while direction remains supported
```

D-148 observes exact causal state and post-SL counterfactual price only. It does not change Entry, SL, TP, exit management, map state, or order lifecycle.

A frozen PLAN owner protected break is recorded as an authority-event, but is not automatically called total direction failure: same-direction successor H1/M30 authority may exist.

Separately record a future research idea:

```text
SMART_PARTIAL_WITH_CONTINUATION_STATE
= combine mechanical partial realization with causally available +1R continuation state to reduce needless big-winner haircut
```

This idea is backlog only and is not implemented in D-148.
'''

D147_RESULT_BLOCK = r'''
## GOLD 2025 three-mode result — 2026-08-21

User-provided ledgers:

```text
GOLD_original.csv  SHA-256 6cae85b2913e81e7e847fb0c7794ee7c0926f1dfae140d37bd038f735a18d7d1
GOLD_step.csv      SHA-256 462afaaf843d85b2a97a9f5287083f3c76cc83d9a426bfb7e21ca82f34acb2ab
GOLD_particial.csv SHA-256 13b9ed5b95f3ec1db6a8138c10746f5f89f800f8e484c795d600e99c946c58ee
```

All modes retained the same 58 fills / 58 closes and zero execution divergence. The same Entry / initial SL / structural TP population was preserved.

All-scope cost-adjusted net result:

| Mode | WR | Avg winner | Avg loser | Expectancy | Total net R | Max DD | Loss streak |
|---|---:|---:|---:|---:|---:|---:|---:|
| ORIGINAL | 24.14% | +3.827R | -1.092R | +0.095R | +5.532R | -23.00R | 11 |
| R_STEP_TRAILING | 29.31% | +1.623R | -0.685R | -0.008R | -0.478R | -9.35R | 9 |
| R_STEP_PARTIAL | 43.10% | +1.419R | -0.867R | +0.118R | +6.864R | -9.00R | 8 |

Continuation-only (51 trades):

```text
ORIGINAL: WR 27.45%, expectancy +0.254R, avg winner +3.827R, max DD 19.53R
TRAILING: WR 31.37%, expectancy +0.015R, avg winner +1.540R, max DD 8.10R
PARTIAL:  WR 47.06%, expectancy +0.187R, avg winner +1.402R, max DD 7.66R
```

The 21 continuation trades that never reached +1R were identical across all three modes. Among 16 ORIGINAL trades that reached +1R and later realized a loss, PARTIAL improved all 16 and converted 10 into positive net trades, while preserving all 14 original continuation winners as positive trades. TRAILING protected giveback but cut too many large winners.

Interpretation: mechanical PARTIAL is the strongest GOLD-2025 exit candidate, but it still reduces large-winner payoff and is not cross-market validated. A later smart-partial study may use the already-discovered +1R continuation state, but is not part of D-148.

Instrumentation caveat: D147_* action rows are suppressed under RESEARCH_COMPACT, so execution-action counts were not directly visible in these three ledgers. The realized trade accounting and identical fill population remain usable; D-147 action-log QA remains separate.
'''

TEST_RESULTS_BLOCK = r'''
## D-147 GOLD 2025 exit-architecture comparison

Analyzed 2026-08-21 from user-provided Strategy Tester ledgers.

```text
ORIGINAL  : 58 trades, WR 24.14%, expectancy +0.095R, total +5.532R, max DD 23.00R
TRAILING  : 58 trades, WR 29.31%, expectancy -0.008R, total -0.478R, max DD 9.35R
PARTIAL   : 58 trades, WR 43.10%, expectancy +0.118R, total +6.864R, max DD 9.00R
```

Continuation-only:

```text
ORIGINAL  51 trades / 14 winners / WR 27.45% / expectancy +0.254R
TRAILING  51 trades / 16 winners / WR 31.37% / expectancy +0.015R
PARTIAL   51 trades / 24 winners / WR 47.06% / expectancy +0.187R
```

The `<1R` failure population was exactly 21 continuation trades and did not change across exit modes. This is now the D-148 Entry-survival taxonomy population.

PARTIAL improved every one of the 16 ORIGINAL continuation trades that first reached +1R but later realized a loss; 10/16 became positive net trades. However large winners were materially haircut, so continuation-state-aware partial management is recorded only as a future research idea.

D147 compact action rows were suppressed; action-level execution QA is not claimed from these ledgers.
'''


def transform_docs(rel: str, text: str) -> str:
    t = normalize(text)
    if rel == HANDOFF:
        old = '''Last updated: 2026-08-21\nRepository base before this handoff package: `c541b19d68ac1589575bfaf1ab07abf1ee296a09`\nCurrent code/research build: `1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1`\nCurrent research phase: **D-147 EXIT ARCHITECTURE RESEARCH V1 — IMPLEMENTED / LOCAL COMPILE + BASELINE PARITY PENDING**\nStrategy semantics: **D134 ENTRY + INITIAL GEOMETRY UNCHANGED / D147 POST-FILL EXIT VARIANT**\nStrategy authority: **UNCHANGED; ORIGINAL MODE IS BASELINE CONTROL**\n2021 status: **KEEP UNTOUCHED**\n'''
        new = '''Last updated: 2026-08-21\nRepository base before this handoff package: `1889f9d5c53bc37e6061b9e309fa11b1534c1123`\nCurrent code/research build: `1.94R1L10 / ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW`\nCurrent research phase: **D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / LOCAL COMPILE + AUDIT PARITY PENDING**\nStrategy semantics: **D134 ENTRY + INITIAL GEOMETRY UNCHANGED / D147 EXIT TOGGLE PRESENT / D148 SHADOW ONLY**\nStrategy authority: **UNCHANGED; D148 HAS NONE**\n2021 status: **KEEP UNTOUCHED**\n'''
        t = replace_once(t, old, new, "HANDOFF header")
        return append_once(t, "## D-148 ENTRY SURVIVAL FAILURE TAXONOMY", D148_HANDOFF_BLOCK)
    if rel == STATE:
        old = '''Last updated: 2026-08-21\nRepository base before handoff package: `c541b19d68ac1589575bfaf1ab07abf1ee296a09`\nCurrent code/research identity: `1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1`\nCurrent research phase: **D-147 EXIT ARCHITECTURE RESEARCH V1 — IMPLEMENTED / COMPILE + BASELINE PARITY PENDING**\nStrategy authority: **UNCHANGED; ORIGINAL MODE IS BASELINE CONTROL**\n2021: **UNTOUCHED**\n'''
        new = '''Last updated: 2026-08-21\nRepository base before handoff package: `1889f9d5c53bc37e6061b9e309fa11b1534c1123`\nCurrent code/research identity: `1.94R1L10 / ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW`\nCurrent research phase: **D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / COMPILE + AUDIT PARITY PENDING**\nStrategy authority: **UNCHANGED; D148 SHADOW ONLY**\n2021: **UNTOUCHED**\n'''
        t = replace_once(t, old, new, "STATE header")
        return append_once(t, "## D-148 Entry-survival failure taxonomy", D148_STATE_BLOCK)
    if rel == BACKLOG:
        old = 'Current phase: **D-146 CONTINUATION STATE AUDIT — IMPLEMENTED / COMPILE + PARITY PENDING**\n'
        new = 'Current phase: **D-148 ENTRY SURVIVAL FAILURE TAXONOMY — IMPLEMENTED / COMPILE + AUDIT PARITY PENDING**\n'
        t = replace_once(t, old, new, "BACKLOG current phase")
        return append_once(t, "## P0 — D-148 Entry-survival failure taxonomy", D148_BACKLOG_BLOCK)
    if rel == DECISIONS:
        return append_once(t, "## D-148 — classify `<1R` failures before changing Entry", D148_DECISION_BLOCK)
    if rel == D147:
        t = replace_once(t,
            'Status: `IMPLEMENTED / LOCAL COMPILE + BASELINE PARITY PENDING`',
            'Status: `GOLD 2025 THREE-MODE RESULT RECORDED / CROSS-MARKET NOT YET VALIDATED`',
            "D147 status")
        return append_once(t, "## GOLD 2025 three-mode result — 2026-08-21", D147_RESULT_BLOCK)
    if rel == TEST_RESULTS:
        return append_once(t, "## D-147 GOLD 2025 exit-architecture comparison", TEST_RESULTS_BLOCK)
    raise RuntimeError(f"No document transform defined for {rel}")


def expected_for(repo: Path, rel: str) -> str:
    base = head_text(repo, rel)
    if rel == EA:
        return transform_ea(base)
    if rel == EDGE:
        return transform_edge(base)
    return transform_docs(rel, base)


def classify(repo: Path, rel: str, expected: str) -> str:
    current = read_file(repo / rel)
    base = head_text(repo, rel)
    if current == base:
        return "BASELINE"
    if current == expected:
        return "D148_ALREADY_APPLIED"
    p = subprocess.run([GIT, "diff", "--", rel], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    diff = decode_process_output(p.stdout)
    if len(diff) > 2200:
        diff = diff[:2200] + " ..."
    raise RuntimeError(f"Unexpected local edits in {rel}. Only exact HEAD or exact D-148 output is accepted.\n{diff}")


def validate_expected(ea: str, edge: str) -> None:
    for item in [
        "build=1.94R1L10",
        "phase=ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW",
        "D147_EXIT_VARIANT_START",
        "V1_EXIT_R_STEP_PARTIAL",
    ]:
        if item not in ea:
            raise RuntimeError(f"EA static assertion missing: {item}")
    for item in [
        'V1_EDGE_AUDIT_BUILD       "1.94R1L10"',
        'V1_EDGE_AUDIT_PHASE       "ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW"',
        "EDGE_AUDIT_D148_SL_FAILURE",
        "EDGE_AUDIT_D148_TERMINAL",
        "ORIGINAL_1R_RECOVERED_BEFORE_MAP_SUPPORT_LOSS",
        "MAP_SUPPORT_LOST_AFTER_SL",
        "EdgeAuditD148OnMapSample",
        "EdgeAuditD148OnRootInvalidated",
        "EdgeAuditD148OnStructureEvent",
        "d148_post_sl_active",
    ]:
        if item not in edge:
            raise RuntimeError(f"Edge static assertion missing: {item}")
    forbidden = [
        "V1EdgeRunnerTracker &r=g_edge_runners[i]",
        "D148ClosePosition",
        "D148ModifyStop",
        "InpD148Threshold",
        "InpD148TimeCutoff",
    ]
    for item in forbidden:
        if item in edge or item in ea:
            raise RuntimeError(f"Forbidden D-148 strategy surface found: {item}")


def main() -> int:
    try:
        repo = locate_repo()
        head = run(repo, "git", "rev-parse", "HEAD")
        if head != EXPECTED_HEAD:
            raise RuntimeError(f"Git HEAD is {head}, expected {EXPECTED_HEAD}. Re-check latest GitHub and rebuild package; do not force.")
        for rel, blob in EXPECTED_BLOBS.items():
            actual = run(repo, "git", "rev-parse", f"HEAD:{rel}")
            if actual != blob:
                raise RuntimeError(f"Committed blob mismatch for {rel}: {actual} != {blob}")

        expected_map = {rel: expected_for(repo, rel) for rel in TRACKED_TARGETS}
        validate_expected(expected_map[EA], expected_map[EDGE])

        print("D-148 fail-closed preflight:")
        states = {}
        for rel in TRACKED_TARGETS:
            states[rel] = classify(repo, rel, expected_map[rel])
            print(f"  {states[rel]:21s} {rel}")

        for rel, payload in NEW_FILES.items():
            expected = read_file(payload)
            target = repo / rel
            if target.exists():
                if read_file(target) != expected:
                    raise RuntimeError(f"Unexpected existing file: {rel}. Refusing to overwrite.")
                print(f"  {'D148_ALREADY_APPLIED':21s} {rel}")
            else:
                print(f"  {'NEW':21s} {rel}")

        for rel in TRACKED_TARGETS:
            if states[rel] == "BASELINE":
                write_file(repo / rel, expected_map[rel])
        for rel, payload in NEW_FILES.items():
            target = repo / rel
            if not target.exists():
                write_file(target, read_file(payload))

        for rel in TRACKED_TARGETS:
            if read_file(repo / rel) != expected_map[rel]:
                raise RuntimeError(f"Post-apply identity mismatch: {rel}")
        for rel, payload in NEW_FILES.items():
            if read_file(repo / rel) != read_file(payload):
                raise RuntimeError(f"Post-apply payload mismatch: {rel}")
        validate_expected(read_file(repo / EA), read_file(repo / EDGE))

        print("\nD-148 Entry-survival failure taxonomy applied successfully.")
        print("Build: 1.94R1L10 / ENTRY_SURVIVAL_FAILURE_TAXONOMY_V1_SHADOW")
        print("Strategy authority: NONE (shadow-only)")
        print("Required research mode: V1_EXIT_ORIGINAL + InpEnableEdgeAudit=true")
        print("2021: UNTOUCHED")
        print("\nGit diff --stat:")
        print(run(repo, "git", "diff", "--stat"))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
