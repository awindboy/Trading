#!/usr/bin/env python3
"""Apply D-147 Exit Architecture Research V1 to exact Trading HEAD c541b19d.

Fail-closed and idempotent: tracked targets must equal either exact committed HEAD
or the exact D-147 transform generated from that HEAD. Unknown local edits abort.
"""
from __future__ import annotations

from pathlib import Path
import locale
import os
import shutil
import subprocess
import sys

EXPECTED_HEAD = "c541b19d68ac1589575bfaf1ab07abf1ee296a09"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

EA = "mt5/experts/MentorDeterministicV1EA.mq5"
HANDOFF = "docs/ea/HANDOFF.md"
STATE = "docs/ea/STRATEGY_RESEARCH_STATE.md"
BACKLOG = "docs/ea/BACKLOG.md"
DECISIONS = "docs/ea/DECISIONS.md"
D146 = "docs/ea/D146_CONTINUATION_STATE_AUDIT.md"
TEST_RESULTS = "docs/ea/TEST_RESULTS.md"

TRACKED_TARGETS = [EA, HANDOFF, STATE, BACKLOG, DECISIONS, D146, TEST_RESULTS]
NEW_FILES = {
    "docs/ea/D147_EXIT_ARCHITECTURE_RESEARCH.md": PACKAGE_ROOT / "payload/docs/ea/D147_EXIT_ARCHITECTURE_RESEARCH.md",
    "tools/summarize_d147_exit_architecture.py": PACKAGE_ROOT / "payload/tools/summarize_d147_exit_architecture.py",
    "tools/compare_d147_original_baseline.py": PACKAGE_ROOT / "payload/tools/compare_d147_original_baseline.py",
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


D147_ENUM = r'''// D-147 controlled exit-architecture research. ORIGINAL preserves baseline behavior.
enum V1ExitManagementMode
  {
   V1_EXIT_ORIGINAL=0,
   V1_EXIT_R_STEP_TRAILING,
   V1_EXIT_R_STEP_PARTIAL
  };

'''

D147_SCENARIO_FIELDS = r'''

   // D-147 fill-frozen exit-management state. Entry/initial SL/structural TP remain unchanged.
   int               exit_management_mode;
   double            exit_initial_risk_price;
   int               exit_highest_r_step_seen;
   int               exit_last_completed_r_step;
   double            exit_dynamic_sl;
   int               exit_partial_count;
   bool              exit_partial_disabled;
   datetime          exit_last_action_attempt_at;
   int               exit_last_action_attempt_step;
'''

D147_GLOBALS_AND_NAME = r'''
long             g_d147_trailing_moves=0;
long             g_d147_partial_closes=0;
long             g_d147_action_rejections=0;
long             g_d147_partial_infeasible=0;

string ExitManagementModeName(const int mode)
  {
   switch(mode)
     {
      case V1_EXIT_ORIGINAL:       return "ORIGINAL";
      case V1_EXIT_R_STEP_TRAILING:return "R_STEP_TRAILING";
      case V1_EXIT_R_STEP_PARTIAL: return "R_STEP_PARTIAL";
     }
   return "UNKNOWN";
  }
'''

D147_HELPERS = r'''
//+------------------------------------------------------------------+
//| D-147 controlled exit-architecture research                      |
//+------------------------------------------------------------------+
bool D147GetManagedPositionState(const int scenario_index,
                                 ulong &position_ticket,
                                 double &open_price,
                                 double &volume,
                                 double &current_sl,
                                 double &current_tp)
  {
   position_ticket=0;
   open_price=0.0;
   volume=0.0;
   current_sl=0.0;
   current_tp=0.0;
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].broker_position_id==0)
      return false;

   if(!FindManagedPositionByIdentifier(g_scenarios[scenario_index].broker_position_id,
                                       position_ticket,open_price))
      return false;
   if(position_ticket==0 || !PositionSelectByTicket(position_ticket))
      return false;

   volume=PositionGetDouble(POSITION_VOLUME);
   current_sl=PositionGetDouble(POSITION_SL);
   current_tp=PositionGetDouble(POSITION_TP);
   return (volume>0.0);
  }

ENUM_ORDER_TYPE_FILLING D147MarketFillingMode()
  {
   long flags=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
   if((flags & SYMBOL_FILLING_FOK)==SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   if((flags & SYMBOL_FILLING_IOC)==SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
  }

double D147NormalizeVolumeDown(const double raw_volume)
  {
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(step<=0.0 || raw_volume<=0.0)
      return 0.0;
   double units=MathFloor(raw_volume/step+1.0e-10);
   return NormalizeDouble(units*step,8);
  }

bool D147TrailingTargetLegal(const int direction,
                             const MqlTick &tick,
                             const double target_sl)
  {
   double point=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   double min_distance=(double)MathMax(SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL),
                                       SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL))*point;
   double eps=LiquidityTickSize()*1.0e-6;
   if(direction>0)
      return (tick.bid-target_sl+eps>=min_distance);
   return (target_sl-tick.ask+eps>=min_distance);
  }

bool D147RequestTrailingStop(const int scenario_index,
                             const MqlTick &tick,
                             const ulong position_ticket,
                             const double current_sl,
                             const double current_tp,
                             const int target_step,
                             const double target_sl)
  {
   double eps=LiquidityTickSize()*0.5;
   if((g_scenarios[scenario_index].direction>0 && current_sl>0.0 && target_sl<=current_sl+eps) ||
      (g_scenarios[scenario_index].direction<0 && current_sl>0.0 && target_sl>=current_sl-eps))
     {
      g_scenarios[scenario_index].exit_last_completed_r_step=target_step;
      g_scenarios[scenario_index].exit_dynamic_sl=current_sl;
      return true;
     }

   if(!D147TrailingTargetLegal(g_scenarios[scenario_index].direction,tick,target_sl))
      return false;

   datetime observed_at=(datetime)tick.time;
   if(g_scenarios[scenario_index].exit_last_action_attempt_at==observed_at &&
      g_scenarios[scenario_index].exit_last_action_attempt_step==target_step)
      return false;
   g_scenarios[scenario_index].exit_last_action_attempt_at=observed_at;
   g_scenarios[scenario_index].exit_last_action_attempt_step=target_step;

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
      g_d147_action_rejections++;
      LogLine("D147_TRAILING_SL_REJECTED","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s position_ticket=%I64u target_step=%d target_sl=%.10f current_sl=%.10f current_tp=%.10f call_ok=%s retcode=%u comment=%s last_error=%d retry=true",
                           g_scenarios[scenario_index].id,position_ticket,target_step,target_sl,current_sl,current_tp,
                           call_ok ? "true" : "false",result.retcode,result.comment,GetLastError()));
      return false;
     }

   g_scenarios[scenario_index].exit_last_completed_r_step=target_step;
   g_scenarios[scenario_index].exit_dynamic_sl=target_sl;
   g_d147_trailing_moves++;
   LogLine("D147_TRAILING_SL_MOVED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s position_ticket=%I64u reached_step=%d new_sl_r=%d actual_fill=%.10f initial_risk_price=%.10f old_sl=%.10f new_sl=%.10f structural_tp=%.10f retcode=%u comment=%s",
                        g_scenarios[scenario_index].id,position_ticket,target_step,target_step-1,
                        g_scenarios[scenario_index].fill_price,g_scenarios[scenario_index].exit_initial_risk_price,
                        current_sl,target_sl,current_tp,result.retcode,result.comment));
   return true;
  }

bool D147RequestPartialClose(const int scenario_index,
                             const MqlTick &tick,
                             const ulong position_ticket,
                             const double current_volume,
                             const int target_step)
  {
   double min_volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double eps=MathMax(1.0e-10,step*1.0e-6);
   double close_volume=D147NormalizeVolumeDown(current_volume*V1_D147_PARTIAL_FRACTION);
   double remaining=current_volume-close_volume;

   if(close_volume<min_volume-eps || remaining<min_volume-eps || close_volume<=0.0)
     {
      g_scenarios[scenario_index].exit_partial_disabled=true;
      g_d147_partial_infeasible++;
      LogLine("D147_PARTIAL_INFEASIBLE","M1",(datetime)tick.time,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s target_step=%d current_volume=%.8f requested_fraction=%.8f normalized_close=%.8f remaining=%.8f volume_min=%.8f volume_step=%.8f action=KEEP_REMAINDER_ON_ORIGINAL_SL_TP full_close_substitution=false",
                           g_scenarios[scenario_index].id,target_step,current_volume,V1_D147_PARTIAL_FRACTION,
                           close_volume,remaining,min_volume,step));
      return false;
     }

   datetime observed_at=(datetime)tick.time;
   if(g_scenarios[scenario_index].exit_last_action_attempt_at==observed_at &&
      g_scenarios[scenario_index].exit_last_action_attempt_step==target_step)
      return false;
   g_scenarios[scenario_index].exit_last_action_attempt_at=observed_at;
   g_scenarios[scenario_index].exit_last_action_attempt_step=target_step;

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
   request.comment=StringFormat("D147-P%d-R%d",scenario_index,target_step);

   ResetLastError();
   bool call_ok=OrderSend(request,result);
   bool accepted=(call_ok && IsAcceptableTradeRetcode(result.retcode));
   if(!accepted)
     {
      g_d147_action_rejections++;
      LogLine("D147_PARTIAL_CLOSE_REJECTED","M1",observed_at,g_scenarios[scenario_index].id,
              StringFormat("scenario_id=%s position_ticket=%I64u target_step=%d close_volume=%.8f current_volume=%.8f price=%.10f filling=%d call_ok=%s retcode=%u comment=%s last_error=%d retry=true",
                           g_scenarios[scenario_index].id,position_ticket,target_step,close_volume,current_volume,market_reference_price,
                           (int)request.type_filling,call_ok ? "true" : "false",result.retcode,result.comment,GetLastError()));
      return false;
     }

   g_scenarios[scenario_index].exit_last_completed_r_step=target_step;
   g_scenarios[scenario_index].exit_partial_count++;
   g_d147_partial_closes++;
   LogLine("D147_PARTIAL_CLOSE_ACCEPTED","M1",observed_at,g_scenarios[scenario_index].id,
           StringFormat("scenario_id=%s position_ticket=%I64u reached_step=%d close_fraction_of_remaining=%.8f requested_volume=%.8f pre_close_volume=%.8f expected_remaining=%.8f execution_price=%.10f structural_sl=%.10f structural_tp=%.10f retcode=%u deal=%I64u order=%I64u comment=%s",
                        g_scenarios[scenario_index].id,position_ticket,target_step,V1_D147_PARTIAL_FRACTION,
                        close_volume,current_volume,remaining,(result.price>0.0 ? result.price : market_reference_price),g_scenarios[scenario_index].normalized_sl,
                        g_scenarios[scenario_index].final_objective_price,result.retcode,result.deal,result.order,result.comment));
   return true;
  }

void D147ManageFilledPosition(const int scenario_index,const MqlTick &tick)
  {
   if(scenario_index<0 || scenario_index>=ArraySize(g_scenarios) ||
      g_scenarios[scenario_index].strategy_state!=V1_STRATEGY_FILLED)
      return;

   int mode=g_scenarios[scenario_index].exit_management_mode;
   if(mode==V1_EXIT_ORIGINAL)
      return;
   if(g_scenarios[scenario_index].exit_initial_risk_price<=0.0)
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
   if(reached_step<1)
      return;
   if(reached_step>g_scenarios[scenario_index].exit_highest_r_step_seen)
      g_scenarios[scenario_index].exit_highest_r_step_seen=reached_step;

   if(mode==V1_EXIT_R_STEP_TRAILING)
     {
      int target_step=g_scenarios[scenario_index].exit_highest_r_step_seen;
      if(target_step<=g_scenarios[scenario_index].exit_last_completed_r_step)
         return;
      double raw_target=g_scenarios[scenario_index].fill_price+
                        (double)g_scenarios[scenario_index].direction*
                        (double)(target_step-1)*g_scenarios[scenario_index].exit_initial_risk_price;
      double target_sl=(g_scenarios[scenario_index].direction>0 ?
                        NormalizePriceFloorToTick(raw_target) : NormalizePriceCeilToTick(raw_target));
      D147RequestTrailingStop(scenario_index,tick,position_ticket,current_sl,current_tp,target_step,target_sl);
      return;
     }

   if(mode==V1_EXIT_R_STEP_PARTIAL && !g_scenarios[scenario_index].exit_partial_disabled)
     {
      int target_step=g_scenarios[scenario_index].exit_last_completed_r_step+1;
      if(target_step<=g_scenarios[scenario_index].exit_highest_r_step_seen)
         D147RequestPartialClose(scenario_index,tick,position_ticket,volume,target_step);
     }
  }

bool D147AggregateExitDealsForPosition(const ulong position_id,
                                       const datetime from_time,
                                       ulong &latest_deal,
                                       datetime &latest_time,
                                       double &latest_price,
                                       long &latest_reason,
                                       double &profit_sum,
                                       double &commission_sum,
                                       double &swap_sum,
                                       double &fee_sum,
                                       int &exit_deal_count)
  {
   latest_deal=0;
   latest_time=0;
   latest_price=0.0;
   latest_reason=0;
   profit_sum=0.0;
   commission_sum=0.0;
   swap_sum=0.0;
   fee_sum=0.0;
   exit_deal_count=0;
   if(position_id==0)
      return false;

   datetime from=(from_time>86400 ? from_time-86400 : 0);
   if(!HistorySelect(from,TimeCurrent()+60))
      return false;

   long latest_msc=-1;
   for(int i=0;i<HistoryDealsTotal();i++)
     {
      ulong deal=HistoryDealGetTicket(i);
      if(deal==0 ||
         HistoryDealGetString(deal,DEAL_SYMBOL)!=_Symbol ||
         (long)HistoryDealGetInteger(deal,DEAL_MAGIC)!=InpMagicNumber ||
         (ulong)HistoryDealGetInteger(deal,DEAL_POSITION_ID)!=position_id)
         continue;
      ENUM_DEAL_ENTRY entry=(ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal,DEAL_ENTRY);
      if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY && entry!=DEAL_ENTRY_INOUT)
         continue;

      exit_deal_count++;
      profit_sum+=HistoryDealGetDouble(deal,DEAL_PROFIT);
      commission_sum+=HistoryDealGetDouble(deal,DEAL_COMMISSION);
      swap_sum+=HistoryDealGetDouble(deal,DEAL_SWAP);
      fee_sum+=HistoryDealGetDouble(deal,DEAL_FEE);
      long msc=HistoryDealGetInteger(deal,DEAL_TIME_MSC);
      if(msc>latest_msc || (msc==latest_msc && deal>latest_deal))
        {
         latest_msc=msc;
         latest_deal=deal;
         latest_time=(datetime)HistoryDealGetInteger(deal,DEAL_TIME);
         latest_price=HistoryDealGetDouble(deal,DEAL_PRICE);
         latest_reason=HistoryDealGetInteger(deal,DEAL_REASON);
        }
     }
   return (exit_deal_count>0 && latest_deal>0);
  }

'''


def transform_ea(text: str) -> str:
    t = normalize(text)
    t = replace_once(t,
        '#property description "Mentor deterministic V1 EA - D-146 continuation-state shadow audit harness"',
        '#property description "Mentor deterministic V1 EA - D-147 exit-architecture research harness"',
        "property description")

    enum_anchor = '''enum V1PositionSizingMode\n  {\n   V1_SIZE_MINIMUM_VOLUME_PARITY=0,\n   V1_SIZE_FIXED_RISK_MONEY=1,\n   V1_SIZE_EQUITY_PERCENT_RISK=2\n  };\n\n'''
    t = replace_once(t, enum_anchor, enum_anchor + D147_ENUM, "exit mode enum")

    input_anchor = 'input V1PositionSizingMode InpPositionSizingMode = V1_SIZE_MINIMUM_VOLUME_PARITY;\n'
    t = replace_once(t, input_anchor, input_anchor + 'input V1ExitManagementMode InpExitManagementMode = V1_EXIT_ORIGINAL;\n', "exit mode input")

    audit_input_anchor = 'input bool   InpEnableEdgeAudit     = false;\n'
    t = replace_once(t, audit_input_anchor, audit_input_anchor + '\n// D-147 research parameter is intentionally frozen; no fraction optimization in this phase.\n#define V1_D147_PARTIAL_FRACTION 0.50\n', "partial fraction freeze")

    field_anchor = '   double            exit_deal_fee;\n'
    t = replace_once(t, field_anchor, field_anchor + D147_SCENARIO_FIELDS, "scenario fields")

    global_anchor = 'long             g_positions_closed=0;\n\n//+------------------------------------------------------------------+\n//| Helpers                                                          |\n//+------------------------------------------------------------------+\n'
    t = replace_once(t, global_anchor,
                     'long             g_positions_closed=0;\n' + D147_GLOBALS_AND_NAME + '\n//+------------------------------------------------------------------+\n//| Helpers                                                          |\n//+------------------------------------------------------------------+\n',
                     "D147 globals")

    init_anchor = '''   g_scenarios[n].exit_deal_profit=0.0;\n   g_scenarios[n].exit_deal_commission=0.0;\n   g_scenarios[n].exit_deal_swap=0.0;\n   g_scenarios[n].exit_deal_fee=0.0;\n'''
    init_new = init_anchor + '''   g_scenarios[n].exit_management_mode=V1_EXIT_ORIGINAL;\n   g_scenarios[n].exit_initial_risk_price=0.0;\n   g_scenarios[n].exit_highest_r_step_seen=0;\n   g_scenarios[n].exit_last_completed_r_step=0;\n   g_scenarios[n].exit_dynamic_sl=0.0;\n   g_scenarios[n].exit_partial_count=0;\n   g_scenarios[n].exit_partial_disabled=false;\n   g_scenarios[n].exit_last_action_attempt_at=0;\n   g_scenarios[n].exit_last_action_attempt_step=0;\n'''
    t = replace_once(t, init_anchor, init_new, "scenario D147 initialization")

    fill_anchor = '''   CalculateStopLossMoney(g_scenarios[scenario_index].direction,\n                          g_scenarios[scenario_index].order_volume,\n                          g_scenarios[scenario_index].fill_price,\n                          g_scenarios[scenario_index].normalized_sl,\n                          g_scenarios[scenario_index].actual_fill_risk_money);\n'''
    fill_new = fill_anchor + '''   g_scenarios[scenario_index].exit_management_mode=(int)InpExitManagementMode;\n   g_scenarios[scenario_index].exit_initial_risk_price=MathAbs(g_scenarios[scenario_index].fill_price-g_scenarios[scenario_index].normalized_sl);\n   g_scenarios[scenario_index].exit_highest_r_step_seen=0;\n   g_scenarios[scenario_index].exit_last_completed_r_step=0;\n   g_scenarios[scenario_index].exit_dynamic_sl=g_scenarios[scenario_index].normalized_sl;\n   g_scenarios[scenario_index].exit_partial_count=0;\n   g_scenarios[scenario_index].exit_partial_disabled=false;\n   g_scenarios[scenario_index].exit_last_action_attempt_at=0;\n   g_scenarios[scenario_index].exit_last_action_attempt_step=0;\n'''
    t = replace_once(t, fill_anchor, fill_new, "fill-frozen D147 state")

    reconcile_anchor = 'void ReconcileScenarioExecution(const int scenario_index,const datetime observed_at,const bool force_history_probe=false)\n'
    t = replace_once(t, reconcile_anchor, D147_HELPERS + reconcile_anchor, "D147 helper insertion")

    exit_anchor = '''   ulong exit_deal=0;\n   datetime exit_time=0;\n   double exit_price=0.0;\n   long exit_reason=0;\n   if(!FindExitDealForPosition(g_scenarios[scenario_index].broker_position_id,\n                               g_scenarios[scenario_index].fill_at,\n                               exit_deal,exit_time,exit_price,exit_reason))\n      return;\n\n   g_scenarios[scenario_index].position_closed_at=exit_time;\n   g_scenarios[scenario_index].exit_price=exit_price;\n   g_scenarios[scenario_index].exit_reason=exit_reason;\n   g_scenarios[scenario_index].exit_deal_ticket=exit_deal;\n   g_scenarios[scenario_index].exit_deal_profit=HistoryDealGetDouble(exit_deal,DEAL_PROFIT);\n   g_scenarios[scenario_index].exit_deal_commission=HistoryDealGetDouble(exit_deal,DEAL_COMMISSION);\n   g_scenarios[scenario_index].exit_deal_swap=HistoryDealGetDouble(exit_deal,DEAL_SWAP);\n   g_scenarios[scenario_index].exit_deal_fee=HistoryDealGetDouble(exit_deal,DEAL_FEE);\n'''
    exit_new = '''   ulong exit_deal=0;\n   datetime exit_time=0;\n   double exit_price=0.0;\n   long exit_reason=0;\n   double exit_profit=0.0,exit_commission=0.0,exit_swap=0.0,exit_fee=0.0;\n   int exit_deal_count=0;\n\n   if(g_scenarios[scenario_index].exit_management_mode==V1_EXIT_R_STEP_PARTIAL)\n     {\n      if(!D147AggregateExitDealsForPosition(g_scenarios[scenario_index].broker_position_id,\n                                            g_scenarios[scenario_index].fill_at,\n                                            exit_deal,exit_time,exit_price,exit_reason,\n                                            exit_profit,exit_commission,exit_swap,exit_fee,exit_deal_count))\n         return;\n     }\n   else\n     {\n      if(!FindExitDealForPosition(g_scenarios[scenario_index].broker_position_id,\n                                  g_scenarios[scenario_index].fill_at,\n                                  exit_deal,exit_time,exit_price,exit_reason))\n         return;\n      exit_deal_count=1;\n      exit_profit=HistoryDealGetDouble(exit_deal,DEAL_PROFIT);\n      exit_commission=HistoryDealGetDouble(exit_deal,DEAL_COMMISSION);\n      exit_swap=HistoryDealGetDouble(exit_deal,DEAL_SWAP);\n      exit_fee=HistoryDealGetDouble(exit_deal,DEAL_FEE);\n     }\n\n   g_scenarios[scenario_index].position_closed_at=exit_time;\n   g_scenarios[scenario_index].exit_price=exit_price;\n   g_scenarios[scenario_index].exit_reason=exit_reason;\n   g_scenarios[scenario_index].exit_deal_ticket=exit_deal;\n   g_scenarios[scenario_index].exit_deal_profit=exit_profit;\n   g_scenarios[scenario_index].exit_deal_commission=exit_commission;\n   g_scenarios[scenario_index].exit_deal_swap=exit_swap;\n   g_scenarios[scenario_index].exit_deal_fee=exit_fee;\n'''
    t = replace_once(t, exit_anchor, exit_new, "partial exit aggregation")

    filled_anchor = '''      // Filled positions are individually owned by their frozen server SL/TP.\n      // Same-direction later scenarios may coexist in separate hedging positions.\n      if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_FILLED)\n         continue;\n'''
    filled_new = '''      // D-147 changes only post-fill management. ORIGINAL returns immediately and\n      // therefore preserves the baseline frozen server SL/TP behavior.\n      if(g_scenarios[scenario_index].strategy_state==V1_STRATEGY_FILLED)\n        {\n         D147ManageFilledPosition(scenario_index,tick);\n         continue;\n        }\n'''
    t = replace_once(t, filled_anchor, filled_new, "filled-position management hook")

    t = replace_once(t,
        'build=1.92R1L8 property_version=1.00 magic=%I64d phase=CONTINUATION_STATE_AUDIT_V1_SHADOW strategy_semantics=D134_EXECUTION_CORE_UNCHANGED',
        'build=1.93R1L9 property_version=1.00 magic=%I64d phase=EXIT_ARCHITECTURE_RESEARCH_V1 strategy_semantics=D134_ENTRY_INITIAL_GEOMETRY_UNCHANGED_D147_EXIT_VARIANT',
        "EA_START identity")

    regime_start = '   LogLine("REGIME_RESEARCH_VARIANT_START","M30",TimeCurrent(),"",\n'
    d147_start = '''   LogLine("D147_EXIT_VARIANT_START","M1",TimeCurrent(),"",\n           StringFormat("mode=%s partial_fraction=%.8f r_basis=ACTUAL_FILL_TO_ORIGINAL_NORMALIZED_SL structural_tp_retained=true original_mode_baseline_control=true trailing_rule=PLUS_N_R_THEN_SL_N_MINUS_1_R partial_rule=HALF_REMAINING_AT_EACH_NEW_INTEGER_R full_close_substitution_on_min_volume=false m30_threshold_used=false entry_change=false initial_sl_change=false initial_tp_change=false audit_recommended_off_for_performance_comparison=true",\n                        ExitManagementModeName((int)InpExitManagementMode),V1_D147_PARTIAL_FRACTION));\n'''
    t = replace_once(t, regime_start, d147_start + regime_start, "D147 start log")

    deinit_anchor = '''   EdgeAuditDeinit(reason);\n   LogLine("EA_STOP","",TimeCurrent(),"",\n'''
    deinit_new = '''   EdgeAuditDeinit(reason);\n   LogLine("D147_EXIT_VARIANT_STOP","M1",TimeCurrent(),"",\n           StringFormat("mode=%s trailing_moves=%I64d partial_closes=%I64d action_rejections=%I64d partial_infeasible=%I64d partial_fraction=%.8f structural_tp_retained=true 2021_untouched=true",\n                        ExitManagementModeName((int)InpExitManagementMode),g_d147_trailing_moves,g_d147_partial_closes,\n                        g_d147_action_rejections,g_d147_partial_infeasible,V1_D147_PARTIAL_FRACTION));\n   LogLine("EA_STOP","",TimeCurrent(),"",\n'''
    t = replace_once(t, deinit_anchor, deinit_new, "D147 stop log")
    return normalize(t)


D147_HANDOFF_BLOCK = r'''
## D-147 EXIT ARCHITECTURE RESEARCH V1 — IMPLEMENTED / LOCAL COMPILE + BASELINE PARITY PENDING

D-147 is a controlled post-fill research variant. It does not change PLAN, Root/Sweep/CHoCH/FVG authorization, Entry, initial normalized SL, position sizing, structural objective selection, or initial structural TP.

Modes:

```text
V1_EXIT_ORIGINAL
  exact baseline post-fill server SL/TP behavior

V1_EXIT_R_STEP_TRAILING
  R0 = |actual fill - original normalized SL|, frozen forever
  +1R -> SL 0R
  +2R -> SL +1R
  +3R -> SL +2R
  ...
  structural TP retained

V1_EXIT_R_STEP_PARTIAL
  each newly reached integer R closes 50% of CURRENT remaining volume
  original SL retained
  structural TP retained
  if broker min/step volume makes a true partial impossible, do not substitute a full close
```

The 50% fraction is frozen and not exposed as an optimizer input. D-145/D-146 M30 maturity is not used as a threshold or gate in this first exit experiment.

Required validation order:

```text
1. MetaEditor compile = 0 errors
2. D-147 ORIGINAL vs D-146 baseline canonical event parity = PASS
3. GOLD 2025 ORIGINAL / TRAILING / PARTIAL under identical settings
4. compare realized net WR, average winner/loser R, cost-adjusted expectancy, DD, loss streak, direction split, large-winner dependence
5. only then expand to the development panel
```

Use `InpEnableEdgeAudit=false` for the D-147 performance comparison so the D-146 counterfactual tracker does not complicate the exit-variant ledger. 2021 remains untouched.
'''

D147_STATE_BLOCK = r'''
## D-147 controlled exit-architecture branch

The next controlled strategy research branch is now D-147. It asks how much of the current realized-performance problem comes from post-fill profit giveback rather than Entry survival.

It intentionally does **not** use the D-145 M30 progress relationship as a threshold. The first comparison isolates mechanical exit architecture:

```text
ORIGINAL vs R_STEP_TRAILING vs R_STEP_PARTIAL
```

All three share the same Entry, original normalized SL, frozen structural objective, and initial structural TP. `R_STEP_PARTIAL` uses a frozen 50% of remaining volume at each newly reached integer R; no pooled parameter optimization is authorized.

Entry survival (`Fill -> +1R`) remains a separate causal study. A good D-147 result cannot be used as evidence that the Entry architecture has been fixed.
'''

D147_BACKLOG_BLOCK = r'''
## D-147 EXIT ARCHITECTURE RESEARCH V1

- [x] preserve ORIGINAL baseline mode
- [x] add actual-fill-risk frozen R-step trailing mode
- [x] retain structural TP under trailing mode
- [x] add frozen 50%-of-remaining integer-R partial mode
- [x] retain original SL and structural TP under partial mode
- [x] fail safe on broker min/step volume instead of substituting full close
- [x] aggregate partial-exit deals for final realized-net accounting
- [x] add D-147 result summarizer and ORIGINAL baseline comparator
- [ ] MetaEditor compile 0 errors
- [ ] D-147 ORIGINAL canonical parity vs D-146 baseline
- [ ] GOLD 2025 three-mode comparison
- [ ] development-panel cross-market validation
- [ ] decide whether any exit mode deserves promotion beyond research
- [ ] separately resume Fill -> +1R Entry-survival causal study

`2021` remains untouched.
'''

D147_DECISION_BLOCK = r'''
## D-147 — isolate post-fill exit architecture before using M30 continuation state as strategy authority

Decision: introduce one research toggle with three modes: `ORIGINAL`, `R_STEP_TRAILING`, `R_STEP_PARTIAL`.

R is frozen from actual fill to the original normalized strategy SL. Trailing uses integer-R staircase protection; partial mode realizes 50% of the then-current remaining volume at each newly reached integer R. The structural TP stays active in both variants. The partial fraction is frozen rather than optimized.

Reason: D-144/D-145 show substantial favorable excursion that is later given back, while D-145 separately shows that Fill -> +1R survival is not solved. A mechanical exit comparison can measure the contribution of profit giveback without reusing the M30 continuation variable as an Entry filter or fitting a maturity threshold.

Research authority only. `AGENTS.md` / `EA_SPEC.md` baseline authority is unchanged. 2021 remains untouched.
'''

D146_RESULT_APPEND = r'''
## GOLD 2025 D-146 preliminary validation note — 2026-08-21

The uploaded GOLD 2025 unified ledger reproduced the prior continuation population exactly:

```text
EXTERNAL_CONTINUATION fills = 51
+1R before normalized SL = 30 / 51 = 58.82%
+2R before normalized SL = 20 / 51 = 39.22%
P(+2R | +1R) = 20 / 30 = 66.67%
D-146 armed = 30
D-146 terminal = 30
D-146 censored = 0
execution divergence = 0
```

The D-145 M30 maturity relation was reproduced on valid scenario-direction M30 ranges: +2R runners had lower median range progress (0.796 vs 0.918) and more remaining external room (0.954R vs 0.232R).

D-146 outward refresh was common in both constrained runners and constrained failures, so it is not by itself an exit discriminator. PROTECTED_BREAK appeared in 4/10 trade-level failures and 0/20 +2R winners, but the four trades correspond to only three independent M30 PB events and PB occurred after substantial giveback, so it is too late to claim winner-protection authority.

Instrumentation caveats discovered during analysis:

1. the PB callback is emitted before `EnterTransition`, therefore D-146 fields labeled post-state (`owner_changed`, `trend_lost`, `after_m30_*`) are pre-transition on PB rows;
2. the original D-146 summarizer used `external_available` rather than `one_r_m30_range_available` for one geometry classification, misclassifying three GOLD cases. Correct GOLD geometry is 11 room-rich / 13 external-constrained / 6 M30-range-unavailable.

These caveats do not invalidate exact +1R/+2R/SL barriers or PB timestamps, but D-146 MQL instrumentation is not silently repaired inside D-147. A separate instrumentation correction remains available if D-146 causal-state research is resumed.
'''

TEST_RESULTS_BLOCK = r'''
## D-146 GOLD 2025 continuation-state audit — preliminary validated ledger

Source: user-provided GOLD 2025 unified event ledger, analyzed 2026-08-21.

```text
continuation fills = 51
+1R = 30 / 51 = 58.82%
+2R = 20 / 51 = 39.22%
+2R | +1R = 20 / 30 = 66.67%
D146 T0 = 30
D146 terminals = 30
D146 censored = 0
execution divergence = 0
```

D-145 relation reproduced: valid-range +2R runners had lower +1R M30 progress (median 0.796 vs 0.918) and more remaining external room (0.954R vs 0.232R).

Ten trades reached +1R and then failed before +2R; their post-+1R peak total-R levels were approximately 1.083, 1.219, 1.246, 1.364, 1.463, 1.518, 1.560, 1.737, 1.746, 1.893. This confirms material post-fill giveback and motivates D-147 exit-architecture research, but does not authorize a fixed TP.

See `D146_CONTINUATION_STATE_AUDIT.md` for instrumentation caveats. D-147 performance results are pending local compile/parity and MT5 Strategy Tester runs.
'''


def transform_docs(rel: str, text: str) -> str:
    t = normalize(text)
    if rel == HANDOFF:
        old = '''Last updated: 2026-08-21\nRepository base before this handoff package: `f0a9be86d7d8af4e22b21e9b657669aae1245fbd`\nCurrent code/audit build: `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW`\nCurrent research phase: **D-146 CONTINUATION STATE AUDIT — IMPLEMENTED / LOCAL COMPILE + PARITY PENDING**\nStrategy semantics: **D134_EXECUTION_CORE_UNCHANGED**\nStrategy authority: **UNCHANGED**\n2021 status: **KEEP UNTOUCHED**\n'''
        new = '''Last updated: 2026-08-21\nRepository base before this handoff package: `c541b19d68ac1589575bfaf1ab07abf1ee296a09`\nCurrent code/research build: `1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1`\nCurrent research phase: **D-147 EXIT ARCHITECTURE RESEARCH V1 — IMPLEMENTED / LOCAL COMPILE + BASELINE PARITY PENDING**\nStrategy semantics: **D134 ENTRY + INITIAL GEOMETRY UNCHANGED / D147 POST-FILL EXIT VARIANT**\nStrategy authority: **UNCHANGED; ORIGINAL MODE IS BASELINE CONTROL**\n2021 status: **KEEP UNTOUCHED**\n'''
        t = replace_once(t, old, new, "HANDOFF header")
        return append_once(t, "## D-147 EXIT ARCHITECTURE RESEARCH V1 — IMPLEMENTED", D147_HANDOFF_BLOCK)
    if rel == STATE:
        old = '''Last updated: 2026-08-21\nRepository base before handoff package: `f0a9be86d7d8af4e22b21e9b657669aae1245fbd`\nCurrent code/audit identity: `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW`\nCurrent research phase: **D-146 CONTINUATION STATE AUDIT — IMPLEMENTED / TEST PENDING**\nStrategy authority: **UNCHANGED**\n2021: **UNTOUCHED**\n'''
        new = '''Last updated: 2026-08-21\nRepository base before handoff package: `c541b19d68ac1589575bfaf1ab07abf1ee296a09`\nCurrent code/research identity: `1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1`\nCurrent research phase: **D-147 EXIT ARCHITECTURE RESEARCH V1 — IMPLEMENTED / COMPILE + BASELINE PARITY PENDING**\nStrategy authority: **UNCHANGED; ORIGINAL MODE IS BASELINE CONTROL**\n2021: **UNTOUCHED**\n'''
        t = replace_once(t, old, new, "STATE header")
        return append_once(t, "## D-147 controlled exit-architecture branch", D147_STATE_BLOCK)
    if rel == BACKLOG:
        return append_once(t, "## D-147 EXIT ARCHITECTURE RESEARCH V1", D147_BACKLOG_BLOCK)
    if rel == DECISIONS:
        return append_once(t, "## D-147 — isolate post-fill exit architecture", D147_DECISION_BLOCK)
    if rel == D146:
        return append_once(t, "## GOLD 2025 D-146 preliminary validation note", D146_RESULT_APPEND)
    if rel == TEST_RESULTS:
        return append_once(t, "## D-146 GOLD 2025 continuation-state audit — preliminary validated ledger", TEST_RESULTS_BLOCK)
    raise RuntimeError(f"No document transform defined for {rel}")


def expected_for(repo: Path, rel: str) -> str:
    base = head_text(repo, rel)
    if rel == EA:
        return transform_ea(base)
    return transform_docs(rel, base)


def classify(repo: Path, rel: str, expected: str) -> str:
    current = read_file(repo / rel)
    base = head_text(repo, rel)
    if current == base:
        return "BASELINE"
    if current == expected:
        return "D147_ALREADY_APPLIED"
    p = subprocess.run([GIT, "diff", "--", rel], cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    diff = decode_process_output(p.stdout)
    if len(diff) > 1800:
        diff = diff[:1800] + " ..."
    raise RuntimeError(f"Unexpected local edits in {rel}. Only exact HEAD or exact D-147 output is accepted.\n{diff}")


def validate_expected_ea(ea: str) -> None:
    required = [
        "V1_EXIT_ORIGINAL=0",
        "V1_EXIT_R_STEP_TRAILING",
        "V1_EXIT_R_STEP_PARTIAL",
        "#define V1_D147_PARTIAL_FRACTION 0.50",
        "void D147ManageFilledPosition",
        "TRADE_ACTION_SLTP",
        "D147_PARTIAL_CLOSE_ACCEPTED",
        "D147AggregateExitDealsForPosition",
        "build=1.93R1L9",
        "phase=EXIT_ARCHITECTURE_RESEARCH_V1",
    ]
    for item in required:
        if item not in ea:
            raise RuntimeError(f"Post-apply static assertion missing: {item}")
    forbidden = ["InpD147PartialFraction", "progress >", "remaining_room_threshold"]
    for item in forbidden:
        if item in ea:
            raise RuntimeError(f"Forbidden D-147 strategy surface found: {item}")


def main() -> int:
    try:
        repo = locate_repo()
        head = run(repo, "git", "rev-parse", "HEAD")
        if head != EXPECTED_HEAD:
            raise RuntimeError(f"Git HEAD is {head}, expected {EXPECTED_HEAD}. Re-check latest GitHub and rebuild package; do not force.")

        expected_map = {rel: expected_for(repo, rel) for rel in TRACKED_TARGETS}
        validate_expected_ea(expected_map[EA])

        print("D-147 fail-closed preflight:")
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
                print(f"  {'D147_ALREADY_APPLIED':21s} {rel}")
            else:
                print(f"  {'NEW':21s} {rel}")

        for rel in TRACKED_TARGETS:
            if states[rel] == "BASELINE":
                write_file(repo / rel, expected_map[rel])
        for rel, payload in NEW_FILES.items():
            target = repo / rel
            if not target.exists():
                write_file(target, read_file(payload))

        # Strong post-apply identity: regenerate exact expected from committed HEAD.
        for rel in TRACKED_TARGETS:
            if read_file(repo / rel) != expected_map[rel]:
                raise RuntimeError(f"Post-apply identity mismatch: {rel}")
        for rel, payload in NEW_FILES.items():
            if read_file(repo / rel) != read_file(payload):
                raise RuntimeError(f"Post-apply payload mismatch: {rel}")
        validate_expected_ea(read_file(repo / EA))

        print("\nD-147 exit-architecture research variant applied successfully.")
        print("Build: 1.93R1L9 / EXIT_ARCHITECTURE_RESEARCH_V1")
        print("Baseline control: V1_EXIT_ORIGINAL")
        print("Strategy authority: AGENTS.md / EA_SPEC.md unchanged")
        print("2021: UNTOUCHED")
        print("\nGit diff --stat:")
        print(run(repo, "git", "diff", "--stat"))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
