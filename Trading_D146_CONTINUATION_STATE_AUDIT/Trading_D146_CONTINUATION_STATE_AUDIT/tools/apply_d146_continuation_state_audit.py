#!/usr/bin/env python3
"""Apply D-146 continuation-state shadow audit to exact GitHub HEAD f0a9be86.

This installer is fail-closed: it verifies Git HEAD, clean target files, and
Git blob identities before changing anything. Strategy authority is unchanged.
"""
from __future__ import annotations

from pathlib import Path
import locale
import os
import shutil
import subprocess
import sys

EXPECTED_HEAD = "f0a9be86d7d8af4e22b21e9b657669aae1245fbd"
EXPECTED_BLOBS = {
    "mt5/experts/MentorDeterministicV1EA.mq5": "3268fbe3ae1e02d8252814a7f8f0412deda45444",
    "mt5/experts/EdgeAuditV1.mqh": "a1237f0bf6a4bdc0e7e24b5f11283654e682fd7d",
    "docs/ea/HANDOFF.md": "d99ced6e6f9e49373b713c7996489aae186eab76",
    "docs/ea/D146_CONTINUATION_STATE_AUDIT.md": "6ef6d45fc22287057e207083e09af14a094a9538",
    "docs/ea/STRATEGY_RESEARCH_STATE.md": "912b40e93e2ebff75586f50bac6f92fa852a99a3",
    "docs/ea/BACKLOG.md": "e6881c509540637bddfdb20e9faf2fd14fc84637",
    "docs/ea/DECISIONS.md": "bf3b5e7851bc5a3645f3802c4090c27eb1ee04c5",
}
NEW_TOOL = "tools/summarize_d146_continuation_state_audit.py"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_TOOL = PACKAGE_ROOT / "payload" / "tools" / "summarize_d146_continuation_state_audit.py"


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
            continue
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
    proc = subprocess.run(argv, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        err = decode_process_output(proc.stderr or proc.stdout)
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(map(str, argv))} :: {err}")
    return decode_process_output(proc.stdout)


def locate_repo() -> Path:
    candidates = [Path.cwd(), Path(__file__).resolve().parent, *Path(__file__).resolve().parents]
    seen = set()
    diagnostics = []
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
            if (root / "mt5/experts/EdgeAuditV1.mqh").exists():
                return root
            diagnostics.append(f"{c}: Git root found but EdgeAudit missing: {root}")
        except Exception as e:
            diagnostics.append(f"{c}: {e}")
    raise RuntimeError("Trading Git repository not found. " + " | ".join(diagnostics[:4]))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def require_clean(repo: Path, rel: str) -> None:
    proc = subprocess.run([GIT, "status", "--porcelain", "--", rel], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"git status failed for {rel}")
    if decode_process_output(proc.stdout):
        raise RuntimeError(f"Local edits detected in {rel}. Commit/stash/revert before applying D-146.")


def require_blob(repo: Path, rel: str, expected: str) -> None:
    # Verify the committed object rather than raw working-tree bytes so a clean
    # Windows checkout with core.autocrlf cannot false-fail on CRLF conversion.
    actual = run(repo, "git", "rev-parse", f"HEAD:{rel}")
    if actual != expected:
        raise RuntimeError(f"{rel}: HEAD blob mismatch {actual}, expected {expected}. Re-check GitHub; do not force.")


D146_STATE_STRUCT = r'''
// D-146: compact causal M30 state used only by +1R-success continuation audit.
struct V1EdgeD146M30State
  {
   bool       valid;
   bool       protected_available;
   bool       external_available;
   bool       range_available;
   int        trend;
   int        trend_direction;
   string     owner_id;
   datetime   owner_started_at;
   string     protected_id;
   double     protected_price;
   string     external_id;
   double     external_price;
   double     range_span;
   double     range_progress;
   double     remaining_to_external_r;
  };

'''

D146_RUNNER_FIELDS = r'''

   // D-146 shadow-only continuation-state audit. These fields have no strategy authority.
   bool       d146_eligible;
   bool       d146_active;
   bool       d146_terminal;
   string     d146_terminal_outcome;
   datetime   d146_resolved_at;
   datetime   d146_last_tick_at;
   double     d146_last_tick_price;
   double     d146_post_1r_mfe_r;
   double     d146_post_1r_mae_r;

   int        d146_one_r_m30_trend;
   string     d146_one_r_m30_owner_id;
   datetime   d146_one_r_m30_owner_started_at;
   string     d146_one_r_m30_protected_id;
   double     d146_one_r_m30_protected_price;
   string     d146_one_r_m30_external_id;
   double     d146_one_r_m30_external_price;
   bool       d146_one_r_m30_range_available;
   double     d146_one_r_m30_range_span;
   double     d146_one_r_m30_range_progress;
   double     d146_one_r_m30_remaining_to_external_r;

   bool       d146_original_external_available;
   bool       d146_original_external_at_or_beyond_at_1r;
   bool       d146_original_external_delivered_after_1r;
   datetime   d146_original_external_delivered_at;
   bool       d146_original_external_replaced_after_1r;
   datetime   d146_original_external_replaced_at;

   string     d146_last_m30_owner_id;
   int        d146_last_m30_trend;
   string     d146_last_valid_m30_protected_id;
   double     d146_last_valid_m30_protected_price;
   string     d146_last_valid_m30_external_id;
   double     d146_last_valid_m30_external_price;

   long       d146_m30_same_direction_initial_bos_count;
   long       d146_m30_same_direction_bos_count;
   long       d146_m30_opposite_direction_event_count;
   long       d146_m30_protected_break_count;
   long       d146_m30_owner_change_count;
   long       d146_m30_trend_loss_count;
   long       d146_m30_outward_external_refresh_count;
   datetime   d146_first_outward_external_refresh_at;
   datetime   d146_first_deterioration_at;
'''

D146_HELPERS = r'''
//+------------------------------------------------------------------+
//| D-146 continuation-state audit helpers                           |
//+------------------------------------------------------------------+
void EdgeAuditD146ReadM30State(const V1StructureState &state,
                               const int direction,
                               const double price,
                               const double risk,
                               V1EdgeD146M30State &s)
  {
   s.valid=(state.tf==PERIOD_M30);
   s.protected_available=false;
   s.external_available=false;
   s.range_available=false;
   s.trend=state.trend;
   s.trend_direction=TrendDirection(state.trend);
   s.owner_id=state.owner_id;
   s.owner_started_at=state.owner_started_at;
   s.protected_id="";
   s.protected_price=0.0;
   s.external_id="";
   s.external_price=0.0;
   s.range_span=0.0;
   s.range_progress=0.0;
   s.remaining_to_external_r=0.0;

   if(direction>0)
     {
      if(state.protected_low.valid)
        {
         s.protected_available=true;
         s.protected_id=state.protected_low.id;
         s.protected_price=state.protected_low.price;
        }
      if(state.external_high.valid)
        {
         s.external_available=true;
         s.external_id=state.external_high.id;
         s.external_price=state.external_high.price;
        }
     }
   else if(direction<0)
     {
      if(state.protected_high.valid)
        {
         s.protected_available=true;
         s.protected_id=state.protected_high.id;
         s.protected_price=state.protected_high.price;
        }
      if(state.external_low.valid)
        {
         s.external_available=true;
         s.external_id=state.external_low.id;
         s.external_price=state.external_low.price;
        }
     }

   if(!s.valid || direction==0 || !s.protected_available || !s.external_available || price<=0.0)
      return;

   double span=MathAbs(s.external_price-s.protected_price);
   if(s.trend_direction!=direction || span<=MathMax(LiquidityTickSize(),1.0e-12))
      return;

   s.range_available=true;
   s.range_span=span;
   s.range_progress=(direction>0 ? (price-s.protected_price)/span : (s.protected_price-price)/span);
   if(risk>0.0)
      s.remaining_to_external_r=(direction>0 ? s.external_price-price : price-s.external_price)/risk;
  }

string EdgeAuditD146M30StateDetail(const V1EdgeD146M30State &s,const string prefix)
  {
   return StringFormat("%s_valid=%s %s_trend=%s %s_trend_direction=%s %s_owner_id=%s %s_owner_started_at=%s %s_protected_available=%s %s_protected_id=%s %s_protected_price=%.10f %s_external_available=%s %s_external_id=%s %s_external_price=%.10f %s_range_available=%s %s_range_span=%.10f %s_range_progress=%.10f %s_remaining_to_external_r=%.10f",
      prefix,s.valid ? "true" : "false",
      prefix,TrendName(s.trend),
      prefix,DirectionName(s.trend_direction),
      prefix,s.owner_id=="" ? "NA" : s.owner_id,
      prefix,EdgeAuditTimeOrNA(s.owner_started_at),
      prefix,s.protected_available ? "true" : "false",
      prefix,s.protected_id=="" ? "NA" : s.protected_id,
      prefix,s.protected_price,
      prefix,s.external_available ? "true" : "false",
      prefix,s.external_id=="" ? "NA" : s.external_id,
      prefix,s.external_price,
      prefix,s.range_available ? "true" : "false",
      prefix,s.range_span,
      prefix,s.range_progress,
      prefix,s.remaining_to_external_r);
  }

void EdgeAuditD146ResetRunner(V1EdgeRunnerTracker &r)
  {
   r.d146_eligible=(r.scope==V1_SCOPE_EXTERNAL_CONTINUATION);
   r.d146_active=false;
   r.d146_terminal=false;
   r.d146_terminal_outcome="";
   r.d146_resolved_at=0;
   r.d146_last_tick_at=0;
   r.d146_last_tick_price=0.0;
   r.d146_post_1r_mfe_r=0.0;
   r.d146_post_1r_mae_r=0.0;

   r.d146_one_r_m30_trend=V1_TREND_NEUTRAL;
   r.d146_one_r_m30_owner_id="";
   r.d146_one_r_m30_owner_started_at=0;
   r.d146_one_r_m30_protected_id="";
   r.d146_one_r_m30_protected_price=0.0;
   r.d146_one_r_m30_external_id="";
   r.d146_one_r_m30_external_price=0.0;
   r.d146_one_r_m30_range_available=false;
   r.d146_one_r_m30_range_span=0.0;
   r.d146_one_r_m30_range_progress=0.0;
   r.d146_one_r_m30_remaining_to_external_r=0.0;

   r.d146_original_external_available=false;
   r.d146_original_external_at_or_beyond_at_1r=false;
   r.d146_original_external_delivered_after_1r=false;
   r.d146_original_external_delivered_at=0;
   r.d146_original_external_replaced_after_1r=false;
   r.d146_original_external_replaced_at=0;

   r.d146_last_m30_owner_id="";
   r.d146_last_m30_trend=V1_TREND_NEUTRAL;
   r.d146_last_valid_m30_protected_id="";
   r.d146_last_valid_m30_protected_price=0.0;
   r.d146_last_valid_m30_external_id="";
   r.d146_last_valid_m30_external_price=0.0;

   r.d146_m30_same_direction_initial_bos_count=0;
   r.d146_m30_same_direction_bos_count=0;
   r.d146_m30_opposite_direction_event_count=0;
   r.d146_m30_protected_break_count=0;
   r.d146_m30_owner_change_count=0;
   r.d146_m30_trend_loss_count=0;
   r.d146_m30_outward_external_refresh_count=0;
   r.d146_first_outward_external_refresh_at=0;
   r.d146_first_deterioration_at=0;
  }

void EdgeAuditD146TrackTick(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(!r.d146_active || r.d146_terminal || r.risk_distance<=0.0 || px<=0.0)
      return;

   r.d146_last_tick_at=at;
   r.d146_last_tick_price=px;
   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;
   double favorable_after_1r=MathMax(0.0,signed_r-1.0);
   double adverse_after_1r=MathMax(0.0,1.0-signed_r);
   if(favorable_after_1r>r.d146_post_1r_mfe_r) r.d146_post_1r_mfe_r=favorable_after_1r;
   if(adverse_after_1r>r.d146_post_1r_mae_r) r.d146_post_1r_mae_r=adverse_after_1r;

   if(r.d146_original_external_available &&
      !r.d146_original_external_at_or_beyond_at_1r &&
      !r.d146_original_external_delivered_after_1r)
     {
      bool reached=(r.direction>0 ? px>=r.d146_one_r_m30_external_price : px<=r.d146_one_r_m30_external_price);
      if(reached)
        {
         r.d146_original_external_delivered_after_1r=true;
         r.d146_original_external_delivered_at=at;
         EdgeAuditWrite("EDGE_AUDIT_D146_ORIGINAL_EXTERNAL_DELIVERED","TICK",at,r.scenario_id,
            StringFormat("scenario_id=%s direction=%s one_r_at=%s original_external_id=%s original_external_price=%.10f delivered_at=%s exit_side_price=%.10f after_t0=true strategy_authority=false",
                         r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.first_1r_at),
                         r.d146_one_r_m30_external_id=="" ? "NA" : r.d146_one_r_m30_external_id,
                         r.d146_one_r_m30_external_price,EdgeAuditTimeOrNA(at),px));
         g_edge_d146_original_external_deliveries++;
        }
     }
  }

void EdgeAuditD146Arm(V1EdgeRunnerTracker &r,const datetime at,const double px)
  {
   if(!r.d146_eligible || r.d146_active || r.d146_terminal || r.first_1r_at<=0)
      return;

   V1EdgeD146M30State s;
   EdgeAuditD146ReadM30State(g_structure[2],r.direction,px,r.risk_distance,s);
   r.d146_active=true;
   r.d146_last_tick_at=at;
   r.d146_last_tick_price=px;
   r.d146_one_r_m30_trend=s.trend;
   r.d146_one_r_m30_owner_id=s.owner_id;
   r.d146_one_r_m30_owner_started_at=s.owner_started_at;
   r.d146_one_r_m30_protected_id=s.protected_id;
   r.d146_one_r_m30_protected_price=s.protected_price;
   r.d146_one_r_m30_external_id=s.external_id;
   r.d146_one_r_m30_external_price=s.external_price;
   r.d146_one_r_m30_range_available=s.range_available;
   r.d146_one_r_m30_range_span=s.range_span;
   r.d146_one_r_m30_range_progress=s.range_progress;
   r.d146_one_r_m30_remaining_to_external_r=s.remaining_to_external_r;

   r.d146_original_external_available=s.external_available;
   if(s.external_available)
      r.d146_original_external_at_or_beyond_at_1r=(r.direction>0 ? px>=s.external_price : px<=s.external_price);

   r.d146_last_m30_owner_id=s.owner_id;
   r.d146_last_m30_trend=s.trend;
   if(s.protected_available)
     {
      r.d146_last_valid_m30_protected_id=s.protected_id;
      r.d146_last_valid_m30_protected_price=s.protected_price;
     }
   if(s.external_available)
     {
      r.d146_last_valid_m30_external_id=s.external_id;
      r.d146_last_valid_m30_external_price=s.external_price;
     }

   double signed_r=(r.direction>0 ? px-r.fill_price : r.fill_price-px)/r.risk_distance;
   r.d146_post_1r_mfe_r=MathMax(0.0,signed_r-1.0);
   r.d146_post_1r_mae_r=MathMax(0.0,1.0-signed_r);

   EdgeAuditWrite("EDGE_AUDIT_D146_1R_STATE","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s scope=%s direction=%s fill_at=%s one_r_at=%s one_r_price=%.10f target_2r=%.10f risk_distance=%.10f original_external_available=%s original_external_at_or_beyond_at_1r=%s original_external_future_backfill=false %s %s strategy_authority=false",
         r.scenario_id,ScenarioScopeName(r.scope),DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),
         EdgeAuditTimeOrNA(at),px,r.target_2r,r.risk_distance,
         r.d146_original_external_available ? "true" : "false",
         r.d146_original_external_at_or_beyond_at_1r ? "true" : "false",
         EdgeAuditCurrentMapIdentity(at,r.direction),EdgeAuditD146M30StateDetail(s,"one_r_m30")));
   g_edge_d146_armed++;
  }

void EdgeAuditD146OnM30StructureEvent(const V1StructureState &state,
                                      const int event_type,
                                      const int event_direction,
                                      const V1WaveRef &broken,
                                      const V1WaveRef &protected_ref,
                                      const MqlRates &bar,
                                      const datetime available_at)
  {
   if(state.tf!=PERIOD_M30)
      return;

   for(int i=0;i<ArraySize(g_edge_runners);i++)
     {
      if(!g_edge_runners[i].valid || !g_edge_runners[i].d146_active || g_edge_runners[i].d146_terminal)
         continue;
      V1EdgeRunnerTracker r=g_edge_runners[i];
      if(available_at<r.first_1r_at)
         continue;

      string before_owner=r.d146_last_m30_owner_id;
      int before_trend=r.d146_last_m30_trend;
      string before_protected_id=r.d146_last_valid_m30_protected_id;
      double before_protected_price=r.d146_last_valid_m30_protected_price;
      string before_external_id=r.d146_last_valid_m30_external_id;
      double before_external_price=r.d146_last_valid_m30_external_price;

      V1EdgeD146M30State s;
      EdgeAuditD146ReadM30State(state,r.direction,bar.close,r.risk_distance,s);

      bool directional_event=(event_type==V1_EVENT_INITIAL_BOS || event_type==V1_EVENT_BOS);
      bool same_direction=(directional_event && event_direction==r.direction);
      bool opposite_direction=(directional_event && event_direction==-r.direction);
      bool protected_break=(event_type==V1_EVENT_PROTECTED_BREAK);
      bool owner_changed=(before_owner!="" && before_owner!=s.owner_id);
      bool trend_lost=(TrendDirection(before_trend)==r.direction && s.trend_direction!=r.direction);
      bool outward_refresh=false;
      if(same_direction && before_external_price>0.0 && s.external_available)
        {
         double eps=MathMax(LiquidityTickSize()*0.5,1.0e-12);
         outward_refresh=(r.direction>0 ? s.external_price>before_external_price+eps : s.external_price<before_external_price-eps);
        }

      if(event_type==V1_EVENT_INITIAL_BOS && same_direction)
         r.d146_m30_same_direction_initial_bos_count++;
      if(event_type==V1_EVENT_BOS && same_direction)
         r.d146_m30_same_direction_bos_count++;
      if(opposite_direction)
         r.d146_m30_opposite_direction_event_count++;
      if(protected_break)
         r.d146_m30_protected_break_count++;
      if(owner_changed)
         r.d146_m30_owner_change_count++;
      if(trend_lost)
         r.d146_m30_trend_loss_count++;
      if(outward_refresh)
        {
         r.d146_m30_outward_external_refresh_count++;
         if(r.d146_first_outward_external_refresh_at<=0)
            r.d146_first_outward_external_refresh_at=available_at;
        }

      if(r.d146_first_deterioration_at<=0 && (protected_break || opposite_direction || owner_changed || trend_lost))
         r.d146_first_deterioration_at=available_at;

      if(r.d146_original_external_available && s.external_available)
        {
         double eps=MathMax(LiquidityTickSize()*0.5,1.0e-12);
         bool replaced=(s.external_id!=r.d146_one_r_m30_external_id ||
                        MathAbs(s.external_price-r.d146_one_r_m30_external_price)>eps);
         if(replaced && !r.d146_original_external_replaced_after_1r)
           {
            r.d146_original_external_replaced_after_1r=true;
            r.d146_original_external_replaced_at=available_at;
           }
        }

      EdgeAuditWrite("EDGE_AUDIT_D146_M30_EVENT","M30",available_at,r.scenario_id,
         StringFormat("scenario_id=%s direction=%s one_r_at=%s event_type=%s event_direction=%s event_bar_open=%s event_available_at=%s same_direction=%s opposite_direction=%s protected_break=%s owner_changed=%s trend_lost=%s outward_external_refresh=%s broken_id=%s broken_price=%.10f protected_ref_id=%s protected_ref_price=%.10f before_owner_id=%s before_trend=%s before_protected_id=%s before_protected_price=%.10f before_external_id=%s before_external_price=%.10f %s strategy_authority=false",
            r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.first_1r_at),EventName(event_type),DirectionName(event_direction),
            EdgeAuditTimeOrNA(bar.time),EdgeAuditTimeOrNA(available_at),
            same_direction ? "true" : "false",opposite_direction ? "true" : "false",protected_break ? "true" : "false",
            owner_changed ? "true" : "false",trend_lost ? "true" : "false",outward_refresh ? "true" : "false",
            broken.valid ? broken.id : "NA",broken.valid ? broken.price : 0.0,
            protected_ref.valid ? protected_ref.id : "NA",protected_ref.valid ? protected_ref.price : 0.0,
            before_owner=="" ? "NA" : before_owner,TrendName(before_trend),
            before_protected_id=="" ? "NA" : before_protected_id,before_protected_price,
            before_external_id=="" ? "NA" : before_external_id,before_external_price,
            EdgeAuditD146M30StateDetail(s,"after_m30")));
      g_edge_d146_structure_events++;

      r.d146_last_m30_owner_id=s.owner_id;
      r.d146_last_m30_trend=s.trend;
      if(s.protected_available)
        {
         r.d146_last_valid_m30_protected_id=s.protected_id;
         r.d146_last_valid_m30_protected_price=s.protected_price;
        }
      if(s.external_available)
        {
         r.d146_last_valid_m30_external_id=s.external_id;
         r.d146_last_valid_m30_external_price=s.external_price;
        }

      g_edge_runners[i]=r;
     }
  }

void EdgeAuditD146Terminal(V1EdgeRunnerTracker &r,const string outcome,const datetime at,const double px)
  {
   if(!r.d146_active || r.d146_terminal)
      return;
   EdgeAuditD146TrackTick(r,at,px);

   V1EdgeD146M30State s;
   EdgeAuditD146ReadM30State(g_structure[2],r.direction,px,r.risk_distance,s);
   r.d146_active=false;
   r.d146_terminal=true;
   r.d146_terminal_outcome=outcome;
   r.d146_resolved_at=at;

   EdgeAuditWrite("EDGE_AUDIT_D146_TERMINAL","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s scope=%s direction=%s outcome=%s fill_at=%s one_r_at=%s resolved_at=%s time_from_1r_seconds=%I64d exit_side_price=%.10f post_1r_mfe_r=%.10f post_1r_mae_r=%.10f original_external_available=%s original_external_id=%s original_external_price=%.10f original_external_at_or_beyond_at_1r=%s original_external_delivered_after_1r=%s original_external_delivered_at=%s original_external_replaced_after_1r=%s original_external_replaced_at=%s m30_same_direction_initial_bos_count=%I64d m30_same_direction_bos_count=%I64d m30_opposite_direction_event_count=%I64d m30_protected_break_count=%I64d m30_owner_change_count=%I64d m30_trend_loss_count=%I64d m30_outward_external_refresh_count=%I64d first_outward_external_refresh_at=%s first_deterioration_at=%s one_r_m30_range_available=%s one_r_m30_range_progress=%.10f one_r_m30_remaining_to_external_r=%.10f %s strategy_authority=false",
         r.scenario_id,ScenarioScopeName(r.scope),DirectionName(r.direction),outcome,
         EdgeAuditTimeOrNA(r.fill_at),EdgeAuditTimeOrNA(r.first_1r_at),EdgeAuditTimeOrNA(at),
         EdgeAuditAgeSeconds(at,r.first_1r_at),px,r.d146_post_1r_mfe_r,r.d146_post_1r_mae_r,
         r.d146_original_external_available ? "true" : "false",
         r.d146_one_r_m30_external_id=="" ? "NA" : r.d146_one_r_m30_external_id,
         r.d146_one_r_m30_external_price,
         r.d146_original_external_at_or_beyond_at_1r ? "true" : "false",
         r.d146_original_external_delivered_after_1r ? "true" : "false",
         EdgeAuditTimeOrNA(r.d146_original_external_delivered_at),
         r.d146_original_external_replaced_after_1r ? "true" : "false",
         EdgeAuditTimeOrNA(r.d146_original_external_replaced_at),
         r.d146_m30_same_direction_initial_bos_count,r.d146_m30_same_direction_bos_count,
         r.d146_m30_opposite_direction_event_count,r.d146_m30_protected_break_count,
         r.d146_m30_owner_change_count,r.d146_m30_trend_loss_count,
         r.d146_m30_outward_external_refresh_count,EdgeAuditTimeOrNA(r.d146_first_outward_external_refresh_at),
         EdgeAuditTimeOrNA(r.d146_first_deterioration_at),
         r.d146_one_r_m30_range_available ? "true" : "false",
         r.d146_one_r_m30_range_progress,r.d146_one_r_m30_remaining_to_external_r,
         EdgeAuditD146M30StateDetail(s,"terminal_m30")));
   g_edge_d146_terminals++;
  }

void EdgeAuditD146Censor(V1EdgeRunnerTracker &r,const datetime at)
  {
   if(!r.d146_active || r.d146_terminal)
      return;
   V1EdgeD146M30State s;
   EdgeAuditD146ReadM30State(g_structure[2],r.direction,r.d146_last_tick_price,r.risk_distance,s);
   EdgeAuditWrite("EDGE_AUDIT_D146_CENSORED","TICK",at,r.scenario_id,
      StringFormat("scenario_id=%s direction=%s fill_at=%s one_r_at=%s censored_at=%s last_tick_at=%s last_tick_price=%.10f post_1r_mfe_r=%.10f post_1r_mae_r=%.10f original_external_delivered_after_1r=%s m30_same_direction_initial_bos_count=%I64d m30_same_direction_bos_count=%I64d m30_opposite_direction_event_count=%I64d m30_protected_break_count=%I64d m30_owner_change_count=%I64d m30_trend_loss_count=%I64d m30_outward_external_refresh_count=%I64d tester_end_right_censored=true %s strategy_authority=false",
         r.scenario_id,DirectionName(r.direction),EdgeAuditTimeOrNA(r.fill_at),EdgeAuditTimeOrNA(r.first_1r_at),
         EdgeAuditTimeOrNA(at),EdgeAuditTimeOrNA(r.d146_last_tick_at),r.d146_last_tick_price,
         r.d146_post_1r_mfe_r,r.d146_post_1r_mae_r,
         r.d146_original_external_delivered_after_1r ? "true" : "false",
         r.d146_m30_same_direction_initial_bos_count,r.d146_m30_same_direction_bos_count,
         r.d146_m30_opposite_direction_event_count,r.d146_m30_protected_break_count,
         r.d146_m30_owner_change_count,r.d146_m30_trend_loss_count,
         r.d146_m30_outward_external_refresh_count,EdgeAuditD146M30StateDetail(s,"censor_m30")));
   g_edge_d146_censored++;
  }

'''


def patch_edge(text: str) -> str:
    text = replace_once(text,
        "//| D-145 RUNNER MARKET-CONTEXT AUDIT -- lightweight shadow       |",
        "//| D-146 CONTINUATION STATE AUDIT -- shadow measurement          |",
        "edge header")
    text = replace_once(text,
        '#define V1_EDGE_AUDIT_BUILD       "1.92R1L7"',
        '#define V1_EDGE_AUDIT_BUILD       "1.92R1L8"',
        "edge build")
    text = replace_once(text,
        '#define V1_EDGE_AUDIT_PHASE       "RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT"',
        '#define V1_EDGE_AUDIT_PHASE       "CONTINUATION_STATE_AUDIT_V1_SHADOW"',
        "edge phase")

    text = replace_once(text,
        "struct V1EdgeRunnerTracker\n  {",
        D146_STATE_STRUCT + "struct V1EdgeRunnerTracker\n  {",
        "D146 state struct insertion")

    old_fields = "   long       m1_same_pb_events_at_fill;\n   long       m1_opposite_pb_events_at_fill;\n  };"
    new_fields = "   long       m1_same_pb_events_at_fill;\n   long       m1_opposite_pb_events_at_fill;" + D146_RUNNER_FIELDS + "  };"
    text = replace_once(text, old_fields, new_fields, "D146 runner fields")

    text = replace_once(text,
        "long g_edge_runner_skipped=0;",
        "long g_edge_runner_skipped=0;\nlong g_edge_d146_armed=0;\nlong g_edge_d146_structure_events=0;\nlong g_edge_d146_original_external_deliveries=0;\nlong g_edge_d146_terminals=0;\nlong g_edge_d146_censored=0;",
        "D146 global counters")

    text = replace_once(text,
        "void EdgeAuditArmPrefill(const int scenario_index,const datetime stage_at)",
        D146_HELPERS + "void EdgeAuditArmPrefill(const int scenario_index,const datetime stage_at)",
        "D146 helper insertion")

    text = replace_once(text,
        "   EdgeAuditCountStructureEvent(state.tf,event_type,direction);\n   if(state.tf!=PERIOD_H1 && state.tf!=PERIOD_M30)",
        "   EdgeAuditCountStructureEvent(state.tf,event_type,direction);\n   if(state.tf==PERIOD_M30)\n      EdgeAuditD146OnM30StructureEvent(state,event_type,direction,broken,protected_ref,bar,available_at);\n   if(state.tf!=PERIOD_H1 && state.tf!=PERIOD_M30)",
        "D146 structure hook")

    text = replace_once(text,
        "   r.max_adverse_before_1r_r=0.0;\n   r.ticks_seen=0;\n   r.h1_same_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_H1,p.direction);",
        "   r.max_adverse_before_1r_r=0.0;\n   r.ticks_seen=0;\n   EdgeAuditD146ResetRunner(r);\n   r.h1_same_dir_events_at_fill=EdgeAuditDirCounter(PERIOD_H1,p.direction);",
        "D146 runner init")

    text = replace_once(text,
        "   if(!r.reached_1r && r.max_adverse_r>r.max_adverse_before_1r_r) r.max_adverse_before_1r_r=r.max_adverse_r;\n\n   bool hit_sl=",
        "   if(!r.reached_1r && r.max_adverse_r>r.max_adverse_before_1r_r) r.max_adverse_before_1r_r=r.max_adverse_r;\n   if(r.d146_active)\n      EdgeAuditD146TrackTick(r,(datetime)tick.time,px);\n\n   bool hit_sl=",
        "D146 tick tracking")

    text = replace_once(text,
        "      EdgeAuditEmitRunnerOutcome(r,\"1R\",\"REACHED_BEFORE_SL\",(datetime)tick.time,px);\n      EdgeAuditSnapshotAtOneR(r,(datetime)tick.time,px);\n     }",
        "      EdgeAuditEmitRunnerOutcome(r,\"1R\",\"REACHED_BEFORE_SL\",(datetime)tick.time,px);\n      EdgeAuditSnapshotAtOneR(r,(datetime)tick.time,px);\n      EdgeAuditD146Arm(r,(datetime)tick.time,px);\n     }",
        "D146 arm at 1R")

    text = replace_once(text,
        "   if(hit_2 && !r.resolved_2r)\n     { r.resolved_2r=true; EdgeAuditEmitRunnerOutcome(r,\"2R\",\"REACHED_BEFORE_SL\",(datetime)tick.time,px); }",
        "   if(hit_2 && !r.resolved_2r)\n     {\n      if(r.d146_active) EdgeAuditD146Terminal(r,\"+2R_REACHED\",(datetime)tick.time,px);\n      r.resolved_2r=true;\n      EdgeAuditEmitRunnerOutcome(r,\"2R\",\"REACHED_BEFORE_SL\",(datetime)tick.time,px);\n     }",
        "D146 2R terminal")

    text = replace_once(text,
        "   if(hit_sl)\n     {\n      if(!r.resolved_1r)",
        "   if(hit_sl)\n     {\n      if(r.d146_active && r.reached_1r) EdgeAuditD146Terminal(r,\"SL_AFTER_1R\",(datetime)tick.time,px);\n      if(!r.resolved_1r)",
        "D146 SL terminal")

    text = replace_once(text,
        "   g_edge_runner_outcomes=0;\n   g_edge_runner_skipped=0;\n   ArrayInitialize(g_edge_h1_dir_events,0);",
        "   g_edge_runner_outcomes=0;\n   g_edge_runner_skipped=0;\n   g_edge_d146_armed=0;\n   g_edge_d146_structure_events=0;\n   g_edge_d146_original_external_deliveries=0;\n   g_edge_d146_terminals=0;\n   g_edge_d146_censored=0;\n   ArrayInitialize(g_edge_h1_dir_events,0);",
        "D146 reset counters")

    old_start = 'StringFormat("build=%s phase=%s strategy_authority=false unified_ledger=true event_csv=%s lightweight=true tick_tracking=PREFILL_FVG_SELECTED|ACTUAL_FILL_ONLY front_end_forward_labels=false stage_virtual_barriers=false mirror_direction=false fill_snapshot=true first_1r_snapshot=true outcomes=1R|2R|3R|STRUCTURAL_TP_vs_SL hypotheses=MARKET_BACKGROUND|DIRECTIONAL_MATURITY|M30_NET_ADVANCE|PREFILL_DISPLACEMENT|POST_FILL_CONTINUATION strategy_change=false",'
    new_start = 'StringFormat("build=%s phase=%s strategy_authority=false unified_ledger=true event_csv=%s lightweight=true tick_tracking=PREFILL_FVG_SELECTED|ACTUAL_FILL|D146_POST_1R_CONTINUATION_ONLY front_end_forward_labels=false stage_virtual_barriers=false mirror_direction=false fill_snapshot=true first_1r_snapshot=true d146_post_1r_state=true d146_population=EXTERNAL_CONTINUATION_1R_SUCCESS d146_terminal=EXACT_2R_OR_NORMALIZED_SL hypotheses=M30_OUTWARD_EXTERNAL_REFRESH|M30_DETERIORATION future_backfill=false strategy_change=false",'
    text = replace_once(text, old_start, new_start, "D146 start identity")

    text = replace_once(text,
        "      if(!g_edge_runners[i].valid) continue;\n      EdgeAuditWrite(\"EDGE_AUDIT_RUNNER_CENSORED\"",
        "      if(!g_edge_runners[i].valid) continue;\n      if(g_edge_runners[i].d146_active) EdgeAuditD146Censor(g_edge_runners[i],now);\n      EdgeAuditWrite(\"EDGE_AUDIT_RUNNER_CENSORED\"",
        "D146 censor hook")

    old_stop = 'StringFormat("reason=%d rows=%I64d fill_snapshots=%I64d one_r_snapshots=%I64d runner_outcomes=%I64d runner_skipped=%I64d active_prefill=%d active_runners=%d front_end_forward_labels=false stage_virtual_barriers=false lightweight=true strategy_authority=false",\n                   reason,g_edge_rows,g_edge_runner_fill_snapshots,g_edge_runner_one_r_snapshots,g_edge_runner_outcomes,\n                   g_edge_runner_skipped,ArraySize(g_edge_prefill),ArraySize(g_edge_runners)))'
    new_stop = 'StringFormat("reason=%d rows=%I64d fill_snapshots=%I64d one_r_snapshots=%I64d runner_outcomes=%I64d runner_skipped=%I64d d146_armed=%I64d d146_structure_events=%I64d d146_original_external_deliveries=%I64d d146_terminals=%I64d d146_censored=%I64d active_prefill=%d active_runners=%d front_end_forward_labels=false stage_virtual_barriers=false lightweight=true strategy_authority=false",\n                   reason,g_edge_rows,g_edge_runner_fill_snapshots,g_edge_runner_one_r_snapshots,g_edge_runner_outcomes,\n                   g_edge_runner_skipped,g_edge_d146_armed,g_edge_d146_structure_events,g_edge_d146_original_external_deliveries,\n                   g_edge_d146_terminals,g_edge_d146_censored,ArraySize(g_edge_prefill),ArraySize(g_edge_runners)))'
    text = replace_once(text, old_stop, new_stop, "D146 stop counters")

    required = [
        'V1_EDGE_AUDIT_BUILD       "1.92R1L8"',
        'CONTINUATION_STATE_AUDIT_V1_SHADOW',
        'EDGE_AUDIT_D146_1R_STATE',
        'EDGE_AUDIT_D146_M30_EVENT',
        'EDGE_AUDIT_D146_TERMINAL',
        'EDGE_AUDIT_D146_CENSORED',
        'EdgeAuditD146Terminal(r,"+2R_REACHED"',
        'EdgeAuditD146Terminal(r,"SL_AFTER_1R"',
    ]
    for item in required:
        if item not in text:
            raise RuntimeError(f"D-146 EdgeAudit assertion failed: {item}")
    return text


def patch_ea_identity(text: str) -> str:
    # D-146 measurement logic stays in EdgeAuditV1.mqh. These EA edits are
    # diagnostic identity only; no strategy/order hook or execution code changes.
    text = replace_once(text,
        '#property description "Mentor deterministic V1 EA - lightweight runner market-context audit harness"',
        '#property description "Mentor deterministic V1 EA - D-146 continuation-state shadow audit harness"',
        "EA property description")
    text = replace_once(text,
        '// D-145 shadow-only LIGHTWEIGHT RUNNER MARKET-CONTEXT AUDIT implementation.',
        '// D-146 shadow-only CONTINUATION STATE AUDIT implementation.',
        "EA audit comment")
    text = replace_once(text,
        'build=1.92R1L7 property_version=1.00 magic=%I64d phase=RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT strategy_semantics=D134_EXECUTION_CORE_UNCHANGED',
        'build=1.92R1L8 property_version=1.00 magic=%I64d phase=CONTINUATION_STATE_AUDIT_V1_SHADOW strategy_semantics=D134_EXECUTION_CORE_UNCHANGED',
        "EA_START research identity")
    if 'build=1.92R1L8 property_version=1.00 magic=%I64d phase=CONTINUATION_STATE_AUDIT_V1_SHADOW' not in text:
        raise RuntimeError("EA D-146 diagnostic identity assertion failed")
    return text


def patch_docs(repo: Path) -> None:
    hand = read(repo / "docs/ea/HANDOFF.md")
    hand = replace_once(hand,
        "Repository base before this handoff package: `b902a7795cc8b8f16adb8dba67b803875d07b97e`",
        f"Repository base before this handoff package: `{EXPECTED_HEAD}`",
        "HANDOFF base")
    hand = replace_once(hand,
        "Current code/audit build: `1.92R1L7 / RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT`",
        "Current code/audit build: `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW`",
        "HANDOFF build")
    hand = replace_once(hand,
        "Current research phase: **D-146 CONTINUATION STATE AUDIT — PREP / NOT YET IMPLEMENTED**",
        "Current research phase: **D-146 CONTINUATION STATE AUDIT — IMPLEMENTED / LOCAL COMPILE + PARITY PENDING**",
        "HANDOFF phase")
    hand = replace_once(hand,
        "The first concrete engineering task is:\n\n> inspect current `EdgeAuditV1.mqh` / EA hooks and design the smallest D-146 shadow extension that records M30 structure changes from first +1R until exact +2R-or-SL resolution, without strategy authority and without reintroducing heavy tracker fan-out.",
        "The D-146 shadow extension is now prepared in `EdgeAuditV1.mqh` as build `1.92R1L8`.\n\nThe first concrete validation task is:\n\n> MetaEditor compile with 0 errors, then run the GOLD short-window Audit OFF/ON smoke and require exact non-audit parity before using any D-146 evidence.\n\nAfter parity, run GOLD 2025 full-year Audit ON and validate D-146 terminal uniqueness, causal M30 event ordering, original-+1R-external tracking, and runtime before broader reruns.",
        "HANDOFF next task")
    write(repo / "docs/ea/HANDOFF.md", hand)

    d146 = read(repo / "docs/ea/D146_CONTINUATION_STATE_AUDIT.md")
    d146 = replace_once(d146,
        "Status: **RESEARCH CONTRACT / NOT YET IMPLEMENTED**",
        "Status: **IMPLEMENTED SHADOW MEASUREMENT / LOCAL COMPILE + PARITY PENDING**",
        "D146 status")
    marker = "Strategy authority: **NONE**\nParent evidence: `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`"
    implementation = "Strategy authority: **NONE**\nImplementation identity: `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW`\nMeasurement logic surface: `mt5/experts/EdgeAuditV1.mqh`; EA changes are diagnostic identity only and strategy/order hooks remain unchanged\nParent evidence: `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`"
    d146 = replace_once(d146, marker, implementation, "D146 identity")
    runtime_anchor = "Use the existing single unified CSV.\n"
    runtime_insert = "Use the existing single unified CSV.\n\nImplemented D-146 event rows:\n\n```text\nEDGE_AUDIT_D146_1R_STATE\nEDGE_AUDIT_D146_M30_EVENT\nEDGE_AUDIT_D146_ORIGINAL_EXTERNAL_DELIVERED\nEDGE_AUDIT_D146_TERMINAL\nEDGE_AUDIT_D146_CENSORED\n```\n\nThe +1R-time M30 external is frozen as its own identity. A later M30 external is logged as a later causal state and is never backfilled into the +1R snapshot.\n"
    d146 = replace_once(d146, runtime_anchor, runtime_insert, "D146 event rows")
    write(repo / "docs/ea/D146_CONTINUATION_STATE_AUDIT.md", d146)

    state = read(repo / "docs/ea/STRATEGY_RESEARCH_STATE.md")
    state = replace_once(state,
        "Repository base before handoff package: `b902a7795cc8b8f16adb8dba67b803875d07b97e`",
        f"Repository base before handoff package: `{EXPECTED_HEAD}`",
        "STATE base")
    state = replace_once(state,
        "Current code/audit identity: `1.92R1L7 / RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT`",
        "Current code/audit identity: `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW`",
        "STATE build")
    state = replace_once(state,
        "Next research phase: **D-146 CONTINUATION STATE AUDIT**",
        "Current research phase: **D-146 CONTINUATION STATE AUDIT — IMPLEMENTED / TEST PENDING**",
        "STATE phase")
    state = replace_once(state,
        "1. Implement the smallest D-146 shadow tracker.\n2. Validate non-interference and event integrity.",
        "1. Compile the D-146 shadow tracker and validate audit OFF/ON non-interference.\n2. Validate D-146 event integrity and runtime on GOLD 2025.",
        "STATE next decisions")
    write(repo / "docs/ea/STRATEGY_RESEARCH_STATE.md", state)

    backlog = read(repo / "docs/ea/BACKLOG.md")
    backlog = replace_once(backlog,
        "Current phase: **D-146 CONTINUATION STATE AUDIT — NEXT**",
        "Current phase: **D-146 CONTINUATION STATE AUDIT — IMPLEMENTED / COMPILE + PARITY PENDING**",
        "BACKLOG phase")
    for item in [
        "Freeze D-146 measurement contract in code with zero strategy authority.",
        "At first +1R, freeze current M30 owner/protected/external/range state.",
        "From +1R until +2R-or-SL, count/identify causal M30 same-direction BOS, opposite events, protected breaks, owner changes, and external refreshes.",
        "Record whether the +1R-time external was delivered before terminal resolution.",
        "Record whether a new outward M30 external becomes causally available before +2R.",
        "At exact `+2R_REACHED` or `SL_AFTER_1R`, freeze terminal M30 state.",
        "Keep exact tick outcome ordering; no OHLC reconstruction.",
        "Keep unified one-file event ledger.",
        "Keep active research objects restricted to actual +1R-success trades.",
    ]:
        backlog = replace_once(backlog, f"- [ ] {item}", f"- [x] {item}", f"BACKLOG {item[:36]}")
    write(repo / "docs/ea/BACKLOG.md", backlog)

    decisions = read(repo / "docs/ea/DECISIONS.md")
    decisions = replace_once(decisions,
        "Status: PRE-REGISTERED SHADOW RESEARCH / STRATEGY AUTHORITY UNCHANGED — 2026-08-21\n\n### Evidence trigger",
        "Status: IMPLEMENTED SHADOW MEASUREMENT / LOCAL COMPILE + PARITY PENDING / STRATEGY AUTHORITY UNCHANGED — 2026-08-21\n\n### Evidence trigger",
        "DECISIONS D146 status")
    gov_anchor = "### Governance\n\nD-146 has no trade authority and does not authorize:"
    impl = "### Implementation freeze\n\nBuild `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW` implements D-146 measurement logic only inside `EdgeAuditV1.mqh`. `MentorDeterministicV1EA.mq5` changes only its research-harness description and `EA_START` build/phase identity; strategy/order hooks are unchanged.\n\nThe implementation arms only actual `EXTERNAL_CONTINUATION` runners at their first exact +1R touch. It freezes the then-causal M30 owner/protected/external state, tracks later M30 structure events only while unresolved to +2R/SL, and terminalizes at the first exact `+2R_REACHED` or `SL_AFTER_1R`. The original +1R-time external keeps its own immutable identity; later outward externals are separate causal refresh events and are never backfilled. Right-censored tester endings remain censored.\n\nAudit rows stay in the existing unified ledger under `EDGE_AUDIT_*`. No Entry, SL, TP, order, scenario, map, structure, sizing, or exposure state is modified by D-146.\n\n### Governance\n\nD-146 has no trade authority and does not authorize:"
    decisions = replace_once(decisions, gov_anchor, impl, "DECISIONS D146 implementation")
    write(repo / "docs/ea/DECISIONS.md", decisions)


def static_assertions(repo: Path) -> None:
    edge = read(repo / "mt5/experts/EdgeAuditV1.mqh")
    checks = [
        '#define V1_EDGE_AUDIT_BUILD       "1.92R1L8"',
        '#define V1_EDGE_AUDIT_PHASE       "CONTINUATION_STATE_AUDIT_V1_SHADOW"',
        'd146_original_external_at_or_beyond_at_1r',
        'EDGE_AUDIT_D146_M30_EVENT',
        'future_backfill=false',
        'EdgeAuditD146Terminal(r,"+2R_REACHED"',
        'EdgeAuditD146Terminal(r,"SL_AFTER_1R"',
    ]
    for c in checks:
        if c not in edge:
            raise RuntimeError(f"post-apply static assertion failed: {c}")
    if '#define V1_EDGE_AUDIT_PHASE       "RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT"' in edge:
        raise RuntimeError("stale D-145 phase macro remains")

    ea = read(repo / "mt5/experts/MentorDeterministicV1EA.mq5")
    if "build=1.92R1L8 property_version=1.00 magic=%I64d phase=CONTINUATION_STATE_AUDIT_V1_SHADOW" not in ea:
        raise RuntimeError("EA_START D-146 identity assertion failed")

    hand = read(repo / "docs/ea/HANDOFF.md")
    if "1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW" not in hand:
        raise RuntimeError("HANDOFF build identity assertion failed")
    d146 = read(repo / "docs/ea/D146_CONTINUATION_STATE_AUDIT.md")
    if "IMPLEMENTED SHADOW MEASUREMENT / LOCAL COMPILE + PARITY PENDING" not in d146:
        raise RuntimeError("D146 doc status assertion failed")


def main() -> int:
    try:
        repo = locate_repo()
        head = run(repo, "git", "rev-parse", "HEAD")
        if head != EXPECTED_HEAD:
            raise RuntimeError(f"Git HEAD is {head}, expected {EXPECTED_HEAD}. Re-check GitHub; do not force.")

        for rel, blob in EXPECTED_BLOBS.items():
            p = repo / rel
            if not p.exists():
                raise RuntimeError(f"Missing tracked file: {rel}")
            require_clean(repo, rel)
            require_blob(repo, rel, blob)

        new_tool_path = repo / NEW_TOOL
        if new_tool_path.exists():
            raise RuntimeError(f"Unexpected existing file: {NEW_TOOL}. Remove/reconcile it before applying.")
        if not PAYLOAD_TOOL.exists():
            raise RuntimeError(f"Package payload missing: {PAYLOAD_TOOL}")

        ea_path = repo / "mt5/experts/MentorDeterministicV1EA.mq5"
        write(ea_path, patch_ea_identity(read(ea_path)))

        edge_path = repo / "mt5/experts/EdgeAuditV1.mqh"
        edge = patch_edge(read(edge_path))
        write(edge_path, edge)
        patch_docs(repo)
        shutil.copyfile(PAYLOAD_TOOL, new_tool_path)

        static_assertions(repo)

        print("D-146 continuation-state shadow audit applied successfully.")
        print(f"Repository: {repo}")
        print("Build: 1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW")
        print("Strategy authority: NONE; AGENTS.md and EA_SPEC.md unchanged.")
        print("Next: MetaEditor compile -> GOLD short Audit OFF/ON parity -> GOLD 2025 event-integrity/runtime validation.")
        subprocess.run([GIT, "diff", "--stat", "--", *EXPECTED_BLOBS.keys(), NEW_TOOL], cwd=str(repo), check=False)
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
