#!/usr/bin/env python3
"""Apply EDGE_AUDIT_V1 to the exact GitHub source state checked 2026-08-20."""
from pathlib import Path
import hashlib
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
EA = REPO / "mt5" / "experts" / "MentorDeterministicV1EA.mq5"
DECISIONS = REPO / "docs" / "ea" / "DECISIONS.md"

EXPECTED_EA_GIT_BLOB = "33912d32d5861b1d2ccb7e77a9f6a09446db41ac"
EXPECTED_DECISIONS_GIT_BLOB = "834ccb6929ead8a3729df14a2c547ed5a07920dc"


def norm_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def git_head_blob(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    try:
        return subprocess.check_output(
            ["git", "rev-parse", f"HEAD:{rel}"],
            cwd=REPO,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        raise RuntimeError(f"Cannot verify Git HEAD blob for {rel}: {exc}")


def require_clean_exact_source(path: Path, expected_blob: str, label: str) -> None:
    rel = path.relative_to(REPO).as_posix()
    actual = git_head_blob(path)
    if actual != expected_blob:
        raise RuntimeError(
            f"{label} HEAD source identity mismatch.\n"
            f"  expected Git blob: {expected_blob}\n"
            f"  actual HEAD Git blob: {actual}\n"
            "Refresh from the checked GitHub main state and do not force-apply."
        )
    rc = subprocess.run(["git", "diff", "--quiet", "--", rel], cwd=REPO).returncode
    if rc != 0:
        raise RuntimeError(
            f"{label} has local uncommitted changes: {rel}\n"
            "Commit/stash/revert them before applying this exact replacement package."
        )


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_ea() -> None:
    if not EA.exists():
        raise RuntimeError(f"EA not found: {EA}")
    text = norm_text(EA)

    if 'build=1.92R1L4' in text and '#include "EdgeAuditV1.mqh"' in text:
        print("EA: EDGE_AUDIT_V1 already applied; skipping.")
        return

    require_clean_exact_source(EA, EXPECTED_EA_GIT_BLOB, "EA")

    enum_anchor = '''enum V1PositionSizingMode
  {
   V1_SIZE_MINIMUM_VOLUME_PARITY=0,
   V1_SIZE_FIXED_RISK_MONEY=1,
   V1_SIZE_EQUITY_PERCENT_RISK=2
  };
'''
    enum_new = enum_anchor + '''
// D-142A shadow-only base-edge checkpoints. No strategy authority.
enum V1EdgeAuditStage
  {
   V1_EDGE_STAGE_MAP=0,
   V1_EDGE_STAGE_PLAN,
   V1_EDGE_STAGE_ROOT_CONTACT,
   V1_EDGE_STAGE_SWEEP,
   V1_EDGE_STAGE_CHOCH,
   V1_EDGE_STAGE_FVG,
   V1_EDGE_STAGE_FILL
  };
'''
    text = replace_once(text, enum_anchor, enum_new, "edge enum")

    input_anchor = 'input string InpEventCsvFile       = "mentor_v1_regime_research_v1_compact_events.csv";\n'
    input_new = input_anchor + '''
// D-142A EDGE_AUDIT_V1 is shadow-only. Default OFF is the parity control.
input bool   InpEnableEdgeAudit     = false;
input string InpEdgeAuditCsvFile    = "mentor_v1_edge_audit_v1.csv";
'''
    text = replace_once(text, input_anchor, input_new, "edge inputs")

    proto_anchor = '''void ManageIntegratedExecution(const MqlTick &tick);
bool HasManagedAccountExposure();
'''
    proto_new = proto_anchor + '''
// D-142A shadow instrumentation; definitions included immediately before OnInit.
void EdgeAuditResetState();
bool EdgeAuditInit();
void EdgeAuditDeinit(const int reason);
void EdgeAuditOnMapSample(const datetime available_at,const string sample_reason);
void EdgeAuditOnScenarioStage(const int stage,const int scenario_index,const datetime stage_at,const double reference_price,const string extra);
void EdgeAuditOnActualFill(const int scenario_index,const datetime observed_at);
void EdgeAuditOnM1BarBeforeStrategy(const MqlRates &bar,const datetime available_at);
void EdgeAuditOnTick(const MqlTick &tick);
'''
    text = replace_once(text, proto_anchor, proto_new, "edge prototypes")

    text = replace_once(
        text,
        '   g_regime_plan_pass++;\n',
        '''   EdgeAuditOnScenarioStage(V1_EDGE_STAGE_PLAN,n,frozen_at,plan_reference_price,
                            "baseline_plan_after_map_root_objective_qualification=true");
   g_regime_plan_pass++;
''',
        "PLAN hook",
    )

    text = replace_once(
        text,
        '   g_scenario_root_contacts++;\n',
        '''   EdgeAuditOnScenarioStage(V1_EDGE_STAGE_ROOT_CONTACT,scenario_index,available_at,bar.close,
                            "preplanned_root_contact_bound=true");
   g_scenario_root_contacts++;
''',
        "ROOT_CONTACT hook",
    )

    text = replace_once(
        text,
        '      g_scenario_sweep_accepts++;\n',
        '''      EdgeAuditOnScenarioStage(V1_EDGE_STAGE_SWEEP,sidx,available_at,bar.close,
                               "d127_sequence_only_sweep=true");
      g_scenario_sweep_accepts++;
''',
        "SWEEP hook",
    )

    text = replace_once(
        text,
        '      g_scenario_choch_accepts++;\n',
        '''      EdgeAuditOnScenarioStage(V1_EDGE_STAGE_CHOCH,sidx,available_at,bar.close,
                               "d127_generic_protected_break_choch=true");
      g_scenario_choch_accepts++;
''',
        "CHOCH hook",
    )

    text = replace_once(
        text,
        '   g_scenario_fvg_selected++;\n',
        '''   EdgeAuditOnScenarioStage(V1_EDGE_STAGE_FVG,scenario_index,available_at,choch_bar.close,
                            "unique_widest_causal_fresh_fvg_selected=true");
   g_scenario_fvg_selected++;
''',
        "FVG hook",
    )

    text = replace_once(
        text,
        '   g_positions_filled++;\n',
        '''   EdgeAuditOnActualFill(scenario_index,observed_at);
   g_positions_filled++;
''',
        "FILL hook",
    )

    group_anchor = '''         if(d127_m1_bar_open>0) PrepareD127M1SweepDetectorSnapshot(d127_m1_bar_open);
         else
'''
    group_new = '''         if(d127_m1_bar_open>0)
           {
            for(int j=i;j<ArraySize(events) && events[j].available_at==group_time;j++)
              {
               if(events[j].tf_index!=5)
                  continue;
               EdgeAuditOnM1BarBeforeStrategy(events[j].bar,group_time);
               break;
              }
            PrepareD127M1SweepDetectorSnapshot(d127_m1_bar_open);
           }
         else
'''
    text = replace_once(text, group_anchor, group_new, "pre-group M1 label feed")

    prior_group_anchor = '''         if(group_time!=0)
           { EnsurePostContactRootWatches(group_time,false); RefreshScenarioLayer(group_time,false); }
         group_time=events[i].available_at;
'''
    prior_group_new = '''         if(group_time!=0)
           {
            EnsurePostContactRootWatches(group_time,false);
            EdgeAuditOnMapSample(group_time,"COMPLETE_TIMESTAMP_GROUP");
            RefreshScenarioLayer(group_time,false);
           }
         group_time=events[i].available_at;
'''
    text = replace_once(text, prior_group_anchor, prior_group_new, "MAP sample after group")

    final_group_anchor = '''   if(group_time!=0)
     { EnsurePostContactRootWatches(group_time,false); RefreshScenarioLayer(group_time,false); }
   ArrayResize(g_m1_sweep_detector_snapshot,0);
'''
    final_group_new = '''   if(group_time!=0)
     {
      EnsurePostContactRootWatches(group_time,false);
      EdgeAuditOnMapSample(group_time,"COMPLETE_TIMESTAMP_GROUP");
      RefreshScenarioLayer(group_time,false);
     }
   ArrayResize(g_m1_sweep_detector_snapshot,0);
'''
    text = replace_once(text, final_group_anchor, final_group_new, "final MAP sample")

    include_anchor = '\nint OnInit()\n  {\n'
    include_new = '''
// D-142A shadow-only BASE EDGE AUDIT V1 implementation.
#include "EdgeAuditV1.mqh"

int OnInit()
  {
'''
    text = replace_once(text, include_anchor, include_new, "edge include")

    init_anchor = '''   InitializeAllStructureStates();
   if(InpWriteEventCsv)
'''
    init_new = '''   InitializeAllStructureStates();
   EdgeAuditResetState();
   EdgeAuditInit(); // audit failure cannot alter strategy execution
   if(InpWriteEventCsv)
'''
    text = replace_once(text, init_anchor, init_new, "audit init")

    deinit_anchor = '''void OnDeinit(const int reason)
  {
   EventKillTimer();
   LogLine("EA_STOP","",TimeCurrent(),"",
'''
    deinit_new = '''void OnDeinit(const int reason)
  {
   EventKillTimer();
   EdgeAuditDeinit(reason);
   LogLine("EA_STOP","",TimeCurrent(),"",
'''
    text = replace_once(text, deinit_anchor, deinit_new, "audit deinit")

    tick_anchor = '''   ProcessRuntimeClosedBars((datetime)tick.time);
   ManageIntegratedExecution(tick);
  }
'''
    tick_new = '''   ProcessRuntimeClosedBars((datetime)tick.time);
   ManageIntegratedExecution(tick);
   EdgeAuditOnTick(tick);
  }
'''
    text = replace_once(text, tick_anchor, tick_new, "audit tick hook")

    text = replace_once(
        text,
        'build=1.92R1L3 property_version=1.00 magic=%I64d phase=REGIME_RESEARCH_V1_MULTI_SYMBOL_RISK_SIZING',
        'build=1.92R1L4 property_version=1.00 magic=%I64d phase=BASE_EDGE_AUDIT_V1_STAGE_FORWARD_SHADOW',
        "build identity",
    )

    text = text.replace(
        '#property description "Mentor deterministic V1 EA - frozen M30 Regime Research V1 variant"',
        '#property description "Mentor deterministic V1 EA - Regime V1 harness + shadow Base Edge Audit V1"',
        1,
    )

    EA.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"EA patched: {EA}")


DECISION_APPEND = r"""

---

## D-141 — Cross-symbol position sizing is an execution-only research layer

Status: ACTIVE RESEARCH HARNESS / STRATEGY SEMANTICS UNCHANGED — 2026-08-20

Research build `1.92R1L3` added minimum-volume, fixed-money, and equity-percent sizing modes for cross-symbol testing.

Risk-sized modes use MT5 `OrderCalcProfit` on the already-frozen Entry -> SL geometry. Volume is normalized downward to symbol MIN/MAX/STEP and may under-use target risk but must not intentionally exceed it. `OrderCalcMargin` is diagnostic; `OrderCheck` remains final execution-feasibility authority.

This layer changes no Map, Root, Sweep, CHoCH, FVG, Entry, SL, TP, contributor-merge, or direction/exposure rule. Cross-symbol strategy comparison remains primarily R-based.

```text
AGENTS.md = unchanged
EA_SPEC.md = unchanged
strategy semantics = D134_EXECUTION_CORE_UNCHANGED
```

---

## D-142 — BASE EDGE AUDIT V1 is shadow-only and precedes strategy redesign

Status: D-142A PREPARED / LOCAL COMPILE + AUDIT-OFF/AUDIT-ON PARITY PENDING — 2026-08-20

### Trigger

The 2025 18-symbol NO-GATE study remained negative after excluding every execution-divergent symbol-year:

```text
EXTERNAL_CONTINUATION
901 trades / 165 wins
-179.573032R
mean -0.199304R/trade
planned-barrier-only = -166.492129R
```

The largest warning is bearish continuation. Therefore the project must first locate whether predictive information exists before adding another strategy filter.

### D-142A decision

Prepared build:

```text
1.92R1L4
BASE_EDGE_AUDIT_V1_STAGE_FORWARD_SHADOW
strategy semantics = D134_EXECUTION_CORE_UNCHANGED
```

No audit output may authorize/reject/modify/delay/resize/cancel a strategy trade. Audit file-open failure disables only the audit.

D-142A records:

```text
hourly final highest-MAP state
PLAN
ROOT_CONTACT
SWEEP
CHOCH
FVG
ACTUAL_FILL snapshot
```

For MAP through FVG it records future 15m / 1h / 4h / 24h directional return, MFE, and MAE from subsequently completed M1 bars only.

MAP is sampled on a fixed H1 cadence after the complete same-timestamp MTF group because MAP is persistent state; transition-only sampling would bias the population.

If a horizon falls in a market gap, only the last causally available close at or before the target is used. A reopening price is not backdated.

ACTUAL_FILL is logged for identity/joining only in D-142A. Exact fill-to-horizon and same-direction/flipped 1R/2R/3R virtual barriers are deliberately deferred to D-142B until D-142A proves strategy parity. This keeps the first instrumentation change narrow.

### Acceptance gate

Before using D-142A evidence:

```text
MetaEditor compile = 0 errors
audit OFF fixture = complete
audit ON identical fixture = complete
main PLAN/FVG/Entry/SL/TP/order/fill/cancel/close/divergence path = identical
only audit ON writes the separate audit CSV
```

Any strategy difference invalidates the audit build.

### Research governance

Do not derive an immediate SHORT veto, RR cap, time cutoff, PD veto, quality score, or D-126 restoration from the 2025 result.

After D-142A identifies where signal quality improves or deteriorates, change one causal hypothesis at a time.

```text
2021 = KEEP UNTOUCHED
```
"""


def patch_decisions() -> None:
    if not DECISIONS.exists():
        raise RuntimeError(f"DECISIONS not found: {DECISIONS}")
    text = norm_text(DECISIONS)
    if "## D-142 — BASE EDGE AUDIT V1" in text:
        print("DECISIONS: D-142 already present; skipping.")
        return
    require_clean_exact_source(DECISIONS, EXPECTED_DECISIONS_GIT_BLOB, "DECISIONS")
    DECISIONS.write_text(text.rstrip() + DECISION_APPEND.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"DECISIONS appended: {DECISIONS}")


def main() -> None:
    include = REPO / "mt5" / "experts" / "EdgeAuditV1.mqh"
    if not include.exists():
        raise RuntimeError(f"Missing {include}; extract package into repository root first.")
    patch_ea()
    patch_decisions()
    print("\nEDGE_AUDIT_V1 D-142A application complete.")
    print("Next: compile mt5/experts/MentorDeterministicV1EA.mq5.")
    print("Do not push as validated until audit OFF/ON parity passes.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
