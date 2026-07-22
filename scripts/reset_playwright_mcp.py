#!/usr/bin/env python3
"""Terminate stale Playwright MCP processes and clear leftover profile locks.

This is a targeted recovery tool for CineForge browser validation when the
Playwright-managed Chrome profile gets wedged. It only touches Playwright MCP
processes and Chrome processes launched with the Playwright cache profiles under
``~/Library/Caches/ms-playwright``.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessMatch:
    pid: int
    command: str


def _playwright_cache_root() -> Path:
    return Path.home() / "Library" / "Caches" / "ms-playwright"


def _list_processes() -> list[ProcessMatch]:
    result = subprocess.run(
        ["ps", "-ax", "-o", "pid=,command="],
        check=True,
        capture_output=True,
        text=True,
    )
    matches: list[ProcessMatch] = []
    current_pid = os.getpid()
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            pid_text, command = line.split(None, 1)
        except ValueError:
            continue
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if pid == current_pid:
            continue
        if _is_playwright_mcp_process(command):
            matches.append(ProcessMatch(pid=pid, command=command))
    return matches


def _is_playwright_mcp_process(command: str) -> bool:
    cache_root = str(_playwright_cache_root())
    if ".bin/playwright-mcp" in command:
        return True
    if "npm exec @playwright/mcp@latest" in command:
        return True
    return cache_root in command and "--user-data-dir=" in command and "/mcp-" in command


def _terminate_processes(
    processes: list[ProcessMatch], *, dry_run: bool
) -> tuple[list[int], list[int]]:
    if not processes:
        return [], []

    terminated: list[int] = []
    force_killed: list[int] = []
    for process in processes:
        action = "would terminate" if dry_run else "terminating"
        print(f"{action} pid={process.pid} :: {process.command}")
        if dry_run:
            continue
        try:
            os.kill(process.pid, signal.SIGTERM)
            terminated.append(process.pid)
        except ProcessLookupError:
            continue

    if dry_run:
        return terminated, force_killed

    time.sleep(2.0)

    for process in processes:
        try:
            os.kill(process.pid, 0)
        except ProcessLookupError:
            continue
        print(f"force killing pid={process.pid}")
        try:
            os.kill(process.pid, signal.SIGKILL)
            force_killed.append(process.pid)
        except ProcessLookupError:
            continue
    return terminated, force_killed


def _clear_singleton_locks(*, dry_run: bool) -> list[Path]:
    cache_root = _playwright_cache_root()
    if not cache_root.exists():
        return []

    removed: list[Path] = []
    for profile_dir in sorted(cache_root.glob("mcp-*")):
        if not profile_dir.is_dir():
            continue
        for name in ("SingletonCookie", "SingletonLock", "SingletonSocket"):
            path = profile_dir / name
            if not path.exists() and not path.is_symlink():
                continue
            print(f"{'would remove' if dry_run else 'removing'} {path}")
            if not dry_run:
                path.unlink(missing_ok=True)
            removed.append(path)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset stale Playwright MCP browser processes and profile locks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report matching processes and lock files without changing anything.",
    )
    args = parser.parse_args()

    processes = _list_processes()
    print(f"matched processes: {len(processes)}")
    terminated, force_killed = _terminate_processes(processes, dry_run=args.dry_run)
    removed = _clear_singleton_locks(dry_run=args.dry_run)

    print(f"terminated: {len(terminated)}")
    print(f"force_killed: {len(force_killed)}")
    print(f"locks_cleared: {len(removed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
