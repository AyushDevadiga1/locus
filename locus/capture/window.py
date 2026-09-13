"""Active window tracking for the Windows capture layer."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from locus.constants import SUPPRESSED_APPS

try:  # pragma: no cover - Windows-only dependency
    import ctypes
    import ctypes.wintypes
    import win32con
    import win32gui
    import win32process
except ImportError:  # pragma: no cover - non-Windows test environments
    ctypes = None
    ctypes = None
    wintypes = None
    win32con = None
    win32gui = None
    win32process = None


@dataclass(frozen=True)
class WindowSnapshot:
    """Structured data describing one foreground app interval."""

    timestamp: int
    app_name: str
    window_category: str
    duration_ms: int


if ctypes is not None:
    WIN_EVENT_PROC_TYPE = ctypes.WINFUNCTYPE(
        None,
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.HWND,
        ctypes.wintypes.LONG,
        ctypes.wintypes.LONG,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
    )
else:  # pragma: no cover - only used when the Windows API is unavailable
    WIN_EVENT_PROC_TYPE = None


class WindowTracker:
    """Track foreground window switches and emit structured activity events."""

    def __init__(
        self,
        callback_action: Callable[[str], None],
        config_path: str | os.PathLike[str] | None = None,
    ) -> None:
        self.user_callback = callback_action
        self.config_path = (
            Path(config_path)
            if config_path is not None
            else Path(__file__).resolve().parents[1] / "config" / "app_mapping.json"
        )
        self.raw_mapping = self._load_mapping()

        self.hook = None
        self._c_callback_ptr = None
        self.running = False
        self.last_app_name = None
        self.last_category = None
        self.last_switch_time = None

    def _load_mapping(self) -> dict[str, list[str]]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as handle:
                mapping = json.load(handle)
            if isinstance(mapping, dict):
                return {str(key): [str(value) for value in values] for key, values in mapping.items()}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}
        return {}

    def _get_process_name(self, pid: int) -> str:
        """Resolve a process ID into the executable name used by the app map."""
        if ctypes is None or not hasattr(ctypes, "windll"):
            return "unknown.exe"

        try:
            process_handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not process_handle:
                return "unknown.exe"

            buffer = ctypes.create_unicode_buffer(1024)
            size = ctypes.c_ulong(1024)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(
                process_handle,
                0,
                buffer,
                ctypes.byref(size),
            ):
                ctypes.windll.kernel32.CloseHandle(process_handle)
                return os.path.basename(buffer.value)

            ctypes.windll.kernel32.CloseHandle(process_handle)
        except Exception:
            return "unknown.exe"

        return "unknown.exe"

    def _determine_category(self, app_name: str) -> str:
        app_lower = app_name.lower()
        if app_lower in {name.lower() for name in SUPPRESSED_APPS}:
            return "suppressed"

        for category, exe_list in self.raw_mapping.items():
            if app_lower in {name.lower() for name in exe_list}:
                return category
        return "uncategorized"

    def _emit_activity(self, timestamp_ms: int, app_name: str | None, category: str | None) -> None:
        if app_name is None or category is None:
            return

        activity = WindowSnapshot(
            timestamp=timestamp_ms,
            app_name=app_name,
            window_category=category,
            duration_ms=max(0, int(time.time() * 1000) - timestamp_ms),
        )
        self.user_callback(json.dumps(activity.__dict__, separators=(",", ":")))

    def _internal_windows_callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if not self.running:
            return

        if event != win32con.EVENT_SYSTEM_FOREGROUND or not hwnd or not win32gui.IsWindow(hwnd):
            return

        window_title = win32gui.GetWindowText(hwnd)
        if not window_title:
            return

        current_time_ms = int(time.time() * 1000)
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        current_app = self._get_process_name(process_id)
        current_category = self._determine_category(current_app)
        current_app_name = "[SUPPRESSED]" if current_category == "suppressed" else current_app

        if self.last_switch_time is not None and self.last_app_name is not None and self.last_category is not None:
            duration = current_time_ms - self.last_switch_time
            activity_payload = {
                "timestamp": self.last_switch_time,
                "app_name": self.last_app_name,
                "window_category": self.last_category,
                "duration_ms": max(0, duration),
            }
            self.user_callback(json.dumps(activity_payload, separators=(",", ":")))

        self.last_app_name = current_app_name
        self.last_category = current_category
        self.last_switch_time = current_time_ms

    def start(self) -> bool:
        """Start listening for foreground-window changes."""
        if win32con is None or win32gui is None or win32process is None or WIN_EVENT_PROC_TYPE is None:
            return False

        self.running = True
        self._c_callback_ptr = WIN_EVENT_PROC_TYPE(self._internal_windows_callback)
        ctypes.windll.user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

        self.hook = ctypes.windll.user32.SetWinEventHook(
            win32con.EVENT_SYSTEM_FOREGROUND,
            win32con.EVENT_SYSTEM_FOREGROUND,
            0,
            self._c_callback_ptr,
            0,
            0,
            win32con.WINEVENT_OUTOFCONTEXT,
        )
        return self.hook is not None

    def stop(self) -> None:
        """Stop the hook and flush the final in-progress interval."""
        self.running = False

        if self.last_switch_time is not None and self.last_app_name is not None and self.last_category is not None:
            final_time_ms = int(time.time() * 1000)
            duration = final_time_ms - self.last_switch_time
            activity_payload = {
                "timestamp": self.last_switch_time,
                "app_name": self.last_app_name,
                "window_category": self.last_category,
                "duration_ms": max(0, duration),
            }
            self.user_callback(json.dumps(activity_payload, separators=(",", ":")))

        if self.hook:
            ctypes.windll.user32.UnhookWinEvent(self.hook)
            self.hook = None
        self._c_callback_ptr = None


def read_active_window() -> WindowSnapshot:
    """Return a basic fallback snapshot for current active-window state."""
    return WindowSnapshot(
        timestamp=int(time.time() * 1000),
        app_name="unknown.exe",
        window_category="uncategorized",
        duration_ms=0,
    )


def run_window_tracker(callback_action: Callable[[str], None]) -> None:
    """Run the Windows focus tracker in a blocking loop."""
    tracker = WindowTracker(callback_action=callback_action)
    if not tracker.start():
        raise RuntimeError("Window tracking requires Windows and the pywin32 package.")

    print("Locus window monitor active. Press Ctrl+C to stop.")
    try:
        while True:
            win32gui.PumpWaitingMessages()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()


if __name__ == "__main__":
    run_window_tracker(print)
