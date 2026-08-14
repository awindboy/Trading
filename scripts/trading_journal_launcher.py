from __future__ import annotations

import argparse
import ctypes
import os
import signal
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
DEFAULT_MT5_PATHS = [
    Path(r"C:\Program Files\XM Global MT5\terminal64.exe"),
    Path(r"C:\Program Files\MetaTrader 5\terminal64.exe"),
    Path(r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe"),
]

CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_BREAKAWAY_FROM_JOB = 0x01000000
STARTF_USESHOWWINDOW = 0x00000001
SW_SHOWMINIMIZED = 2
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectExtendedLimitInformation = 9
STD_OUTPUT_HANDLE = -11
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004


RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BLUE = "\033[34m"


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)

kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
kernel32.CreateJobObjectW.restype = wintypes.HANDLE
kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
kernel32.SetInformationJobObject.restype = wintypes.BOOL
kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
kernel32.GetStdHandle.restype = wintypes.HANDLE
kernel32.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.GetConsoleMode.restype = wintypes.BOOL
kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.SetConsoleMode.restype = wintypes.BOOL


def enable_terminal_style() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    mode = wintypes.DWORD()
    if handle and kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)


def line(text: str = "", color: str = "") -> None:
    if color:
        print(f"{color}{text}{RESET}")
    else:
        print(text)


def service_label(name: str) -> str:
    labels = {
        "MT5": "MT5 Terminal",
        "Bridge": "Journal Bridge",
        "Web": "Web Console",
    }
    return labels.get(name, name)


def box_line(text: str, width: int, align: str = "left") -> str:
    if len(text) > width:
        text = text[: width - 1] + "."
    if align == "center":
        left = (width - len(text)) // 2
        right = width - len(text) - left
        return f"|{' ' * left}{text}{' ' * right}|"
    return f"| {text:<{width - 1}}|"


def draw_box(lines: list[tuple[str, str]], *, width: int = 60, color: str = "") -> None:
    line("+" + "-" * width + "+", color)
    for text, align in lines:
        line(box_line(text, width, align), color)
    line("+" + "-" * width + "+", color)


def banner() -> None:
    draw_box(
        [
            ("XM MT5 TRADING JOURNAL", "center"),
            ("LOCAL COMMAND CENTER", "center"),
        ],
        width=60,
        color=CYAN + BOLD,
    )
    line(f"{DIM}Session started  {time.strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    line()


def status(tag: str, message: str, color: str = "") -> None:
    line(f"{tag:<10} {message}", color)


def last_error() -> ctypes.WinError:
    return ctypes.WinError(ctypes.get_last_error())


def create_kill_on_close_job() -> wintypes.HANDLE:
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise last_error()

    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    ok = kernel32.SetInformationJobObject(
        job,
        JobObjectExtendedLimitInformation,
        ctypes.byref(info),
        ctypes.sizeof(info),
    )
    if not ok:
        raise last_error()
    return job


def assign_to_job(job: wintypes.HANDLE, process: subprocess.Popen[bytes]) -> bool:
    if not kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(process._handle)):  # noqa: SLF001 - Windows handle is needed here.
        error = last_error()
        status("WARN", f"Process guard could not attach pid={process.pid}: {error}", YELLOW)
        status("WARN", "q/Ctrl+C shutdown will still close it; forced window close may not catch this process.", YELLOW)
        return False
    return True


def find_mt5_path(explicit: str | None) -> Path:
    candidates = [Path(explicit)] if explicit else []
    candidates.extend(DEFAULT_MT5_PATHS)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("MT5 terminal64.exe path was not found. Pass --mt5-path.")


def find_npm() -> Path:
    candidates = [
        Path(r"C:\Program Files\nodejs\npm.cmd"),
        Path(r"C:\Program Files (x86)\nodejs\npm.cmd"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("npm.cmd")


def find_node() -> Path:
    candidates = [
        Path(r"C:\Program Files\nodejs\node.exe"),
        Path(r"C:\Program Files (x86)\nodejs\node.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("node.exe")


def process_ids_by_name(name: str) -> set[int]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        f"Get-Process -Name '{name}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    ids: set[int] = set()
    for line in result.stdout.splitlines():
        try:
            ids.add(int(line.strip()))
        except ValueError:
            pass
    return ids


def process_exists(pid: int) -> bool:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ 'yes' }}",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return "yes" in result.stdout


def kill_process_tree(pid: int) -> None:
    if not process_exists(pid):
        return
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True, check=False)


def listening_pids_for_ports(ports: list[int]) -> dict[int, set[int]]:
    if not ports:
        return {}
    joined = ",".join(str(port) for port in ports)
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            f"Get-NetTCPConnection -LocalPort {joined} -ErrorAction SilentlyContinue | "
            "Where-Object { $_.State -eq 'Listen' } | "
            "ForEach-Object { \"$($_.LocalPort):$($_.OwningProcess)\" }"
        ),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    found: dict[int, set[int]] = {port: set() for port in ports}
    for line in result.stdout.splitlines():
        left, _, right = line.partition(":")
        try:
            found.setdefault(int(left), set()).add(int(right))
        except ValueError:
            pass
    return found


def startup_info(minimized: bool) -> subprocess.STARTUPINFO:
    startup = subprocess.STARTUPINFO()
    if minimized:
        startup.dwFlags |= STARTF_USESHOWWINDOW
        startup.wShowWindow = SW_SHOWMINIMIZED
    return startup


def open_log(name: str):
    LOG_DIR.mkdir(exist_ok=True)
    return (LOG_DIR / name).open("ab", buffering=0)


def launch(
    name: str,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    minimized: bool = False,
    log_name: str,
) -> tuple[subprocess.Popen[bytes], object]:
    log = open_log(log_name)
    log.write(f"\n\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} {name} start =====\n".encode("utf-8"))
    try:
        process = subprocess.Popen(
            args,
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB,
            startupinfo=startup_info(minimized),
        )
    except OSError as exc:
        if getattr(exc, "winerror", None) != 5:
            raise
        log.write(b"[warning] CREATE_BREAKAWAY_FROM_JOB denied; retrying without breakaway.\n")
        process = subprocess.Popen(
            args,
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NEW_PROCESS_GROUP,
            startupinfo=startup_info(minimized),
        )
    status("ONLINE", f"{service_label(name)} armed  pid={process.pid}", GREEN)
    return process, log


BOOL = wintypes.BOOL
LPARAM = wintypes.LPARAM
HWND = wintypes.HWND
DWORD = wintypes.DWORD
EnumWindowsProc = ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)

user32.EnumWindows.argtypes = [EnumWindowsProc, LPARAM]
user32.EnumWindows.restype = BOOL
user32.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(DWORD)]
user32.GetWindowThreadProcessId.restype = DWORD
user32.IsWindowVisible.argtypes = [HWND]
user32.IsWindowVisible.restype = BOOL
user32.PostMessageW.argtypes = [HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = BOOL

WM_CLOSE = 0x0010


def close_windows_for_pid(pid: int) -> None:
    @EnumWindowsProc
    def callback(hwnd: HWND, _lparam: LPARAM) -> BOOL:
        window_pid = DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if window_pid.value == pid and user32.IsWindowVisible(hwnd):
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        return True

    user32.EnumWindows(callback, 0)


def terminate_process(name: str, process: subprocess.Popen[bytes], graceful_window: bool = False) -> None:
    if process.poll() is not None and not process_exists(process.pid):
        return

    status("CLOSING", service_label(name), YELLOW)
    if graceful_window and process_exists(process.pid):
        close_windows_for_pid(process.pid)
    elif process.poll() is None:
        try:
            process.send_signal(signal.CTRL_BREAK_EVENT)
        except Exception:
            process.terminate()

    try:
        process.wait(timeout=8)
        if not process_exists(process.pid):
            return
    except subprocess.TimeoutExpired:
        pass

    kill_process_tree(process.pid)
    try:
        process.wait(timeout=5)
    except Exception:
        pass


def terminate_pids(name: str, pids: set[int]) -> None:
    for pid in sorted(pids):
        if not process_exists(pid):
            continue
        status("CLOSING", f"{service_label(name)} pid={pid}", YELLOW)
        close_windows_for_pid(pid)
        deadline = time.time() + 8
        while time.time() < deadline:
            if not process_exists(pid):
                break
            time.sleep(0.25)
        if process_exists(pid):
            kill_process_tree(pid)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch MT5, Trading Journal web app, and MT5 bridge together.")
    parser.add_argument("--mt5-path", default=os.environ.get("TRADING_JOURNAL_MT5_PATH"), help="Path to terminal64.exe")
    parser.add_argument("--no-mt5", action="store_true", help="Do not launch MT5.")
    parser.add_argument("--no-web", action="store_true", help="Do not launch Vite web server.")
    parser.add_argument("--no-bridge", action="store_true", help="Do not launch MT5 bridge.")
    parser.add_argument("--mt5-minimized", action="store_true", default=True, help="Start MT5 minimized.")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved commands without launching.")
    return parser.parse_args()


def main() -> int:
    enable_terminal_style()
    args = parse_args()
    node = find_node()
    python = Path(sys.executable)
    mt5_path = None if args.no_mt5 else find_mt5_path(args.mt5_path)
    vite_bin = ROOT / "node_modules" / "vite" / "bin" / "vite.js"
    if not args.no_web and not vite_bin.exists():
        raise FileNotFoundError(f"Vite binary was not found: {vite_bin}. Run npm install first.")

    commands: list[tuple[str, list[str], bool, str]] = []
    if mt5_path:
        commands.append(("MT5", [str(mt5_path)], args.mt5_minimized, "mt5.log"))
    if not args.no_bridge:
        commands.append(("Bridge", [str(python), str(ROOT / "bridge" / "mt5_bridge.py")], False, "bridge.log"))
    if not args.no_web:
        commands.append(("Web", [str(node), str(vite_bin), "--host", "0.0.0.0", "--port", "5173", "--strictPort"], False, "web.log"))

    banner()
    status("BASE", str(ROOT), BLUE)
    status("JOURNAL", "http://127.0.0.1:5173/", CYAN)
    status("BRIDGE", "http://127.0.0.1:8765/health", CYAN)
    status("LOGBOOK", str(LOG_DIR), BLUE)
    line()
    line("Launch sequence", BOLD)
    for name, command, minimized, log_name in commands:
        window_state = "minimized" if minimized else "service"
        status("READY", f"{service_label(name):<16} {window_state:<9} logs\\{log_name}", DIM)
    if args.dry_run:
        return 0

    mt5_before = process_ids_by_name("terminal64")
    if mt5_path and mt5_before:
        status("TRACKING", f"Existing MT5 session detected: pid={','.join(str(pid) for pid in sorted(mt5_before))}", YELLOW)
    job = create_kill_on_close_job()
    children: list[tuple[str, subprocess.Popen[bytes], object, bool]] = []
    managed_mt5_pids: set[int] = set(mt5_before if mt5_path else set())
    try:
        line()
        line("System ignition", BOLD)
        for name, command, minimized, log_name in commands:
            process, log = launch(name, command, minimized=minimized, log_name=log_name)
            assign_to_job(job, process)
            children.append((name, process, log, name == "MT5"))
            time.sleep(1)
            if name == "MT5":
                mt5_after = process_ids_by_name("terminal64")
                managed_mt5_pids |= {process.pid} | mt5_after
            if process.poll() is not None:
                if name == "MT5" and process_ids_by_name("terminal64"):
                    status("TRACKING", "MT5 launcher handed off to terminal64.exe and is still managed.", YELLOW)
                    continue
                raise RuntimeError(f"{name} exited immediately. Check logs\\{log_name}.")

        line()
        draw_box(
            [
                ("LIVE DESK", "center"),
                ("Trading Journal is online.", "left"),
                ("Open  http://127.0.0.1:5173/", "left"),
                ("Stop  type q + Enter, or press Ctrl+C", "left"),
            ],
            width=60,
            color=GREEN + BOLD,
        )
        while True:
            command = input().strip().lower()
            if command in {"q", "quit", "exit"}:
                break
    except KeyboardInterrupt:
        line()
        status("HALT", "Ctrl+C received. Closing the desk.", YELLOW)
    finally:
        line()
        line("Shutdown sequence", BOLD)
        for name, process, _log, graceful in reversed(children):
            terminate_process(name, process, graceful_window=graceful)
        if managed_mt5_pids:
            terminate_pids("MT5 tracked", managed_mt5_pids)
        for _name, _process, log, _graceful in children:
            try:
                log.close()
            except Exception:
                pass
        kernel32.CloseHandle(job)
        ports = listening_pids_for_ports([5173, 8765])
        for port, pids in ports.items():
            if pids:
                status("WARN", f"Port {port} still listening: pid={','.join(str(pid) for pid in sorted(pids))}", YELLOW)
            else:
                status("CLOSED", f"Port {port}", GREEN)
        status("OFFLINE", "Trading Journal Command Center closed.", GREEN)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
