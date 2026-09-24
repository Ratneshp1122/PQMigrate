"""
progress.py — Scan progress display and statistics
====================================================

WHY we need this:
  Scanning Vault took ~30 seconds. Scanning Kubernetes will take ~2 minutes.
  Without feedback, the tool looks frozen. A live counter showing
  "Scanning... 4,231 / ~8,000 files  |  23 findings so far  |  45.2 files/sec"
  turns a painful wait into an informative one.

HOW it works:
  ScanProgress is a context manager. Wrap the scan loop with it:
    with ScanProgress(root) as prog:
        for f in walk_files(root):
            findings = scan_file(f)
            prog.update(f, len(findings))
  On exit, it prints the final summary line.

DESIGN:
  - Single line, updated in place using carriage return (\r)
  - Falls back gracefully if stdout is not a TTY (CI/CD, pipes)
  - Calculates files/sec from elapsed time
  - Prints a clean newline on exit so subsequent output isn't garbled
  - Zero external dependencies (no tqdm, no rich)
"""

import os
import sys
import time


class ScanProgress:
    """
    Context manager for live scan progress display.

    Usage:
        with ScanProgress(root, quiet=False) as prog:
            for filepath in all_files:
                findings = scan_file(filepath)
                prog.update(filepath, len(findings))
        # On exit: prints final "Scanned 2,371 files in 28.4s" line

    The quiet flag suppresses all output — used in JSON/pipe mode.
    """

    def __init__(self, root: str, quiet: bool = False, total_hint: int = 0):
        self.root         = root
        self.quiet        = quiet
        self.total_hint   = total_hint   # optional estimated file count
        self.is_tty       = sys.stdout.isatty() and not quiet

        self._files_done  = 0
        self._findings    = 0
        self._start_time  = 0.0
        self._last_update = 0.0
        self._last_file   = ""

    def __enter__(self) -> "ScanProgress":
        self._start_time  = time.perf_counter()
        self._last_update = self._start_time
        if self.is_tty:
            print()  # blank line before progress
        return self

    def __exit__(self, *_):
        elapsed = time.perf_counter() - self._start_time
        if self.is_tty:
            # Clear the progress line
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()
        if not self.quiet:
            rate  = self._files_done / elapsed if elapsed > 0 else 0
            self._print_summary(elapsed, rate)

    def update(self, filepath: str, new_findings: int = 0):
        """Call once per file processed."""
        self._files_done += 1
        self._findings   += new_findings
        self._last_file   = os.path.basename(filepath)

        now = time.perf_counter()
        # Throttle display updates to 20 Hz
        if self.is_tty and (now - self._last_update) >= 0.05:
            self._last_update = now
            self._render()

    def _render(self):
        elapsed = time.perf_counter() - self._start_time
        rate    = self._files_done / elapsed if elapsed > 0 else 0

        if self.total_hint > 0:
            pct     = min(self._files_done / self.total_hint * 100, 99.9)
            counter = f"{self._files_done:,}/{self.total_hint:,} ({pct:.0f}%)"
        else:
            counter = f"{self._files_done:,} files"

        findings_str = (f"  ⚠ {self._findings} findings" if self._findings else "")
        line = (
            f"  Scanning  {counter}"
            f"  {rate:5.1f} files/s"
            f"{findings_str}"
            f"  [{self._last_file[:30]}]"
        )
        # Pad to 80 chars so previous longer lines are overwritten
        line = line.ljust(80)[:80]
        sys.stdout.write(f"\r{line}")
        sys.stdout.flush()

    def _print_summary(self, elapsed: float, rate: float):
        elapsed_str = (
            f"{elapsed:.1f}s"
            if elapsed < 60
            else f"{int(elapsed // 60)}m {elapsed % 60:.0f}s"
        )
        print(
            f"  Scanned {self._files_done:,} files in {elapsed_str}"
            f"  ({rate:.0f} files/sec)"
        )


class ScanStats:
    """
    Lightweight accumulator for scan statistics.
    Separate from ScanProgress so it can be used in quiet/headless mode.

    Usage:
        stats = ScanStats()
        stats.record_file(filepath, findings)
        stats.record_skip(filepath, reason)
        print(stats.summary())
    """

    def __init__(self):
        self.files_scanned  = 0
        self.files_skipped  = 0
        self.files_with_hits= 0
        self.total_findings = 0
        self.bytes_read     = 0
        self.elapsed        = 0.0
        self._t0            = time.perf_counter()
        self._skips: dict[str, int] = {}   # reason → count

    def record_file(self, filepath: str, n_findings: int):
        self.files_scanned  += 1
        self.bytes_read     += _safe_size(filepath)
        if n_findings:
            self.files_with_hits += 1
            self.total_findings  += n_findings

    def record_skip(self, filepath: str, reason: str):
        self.files_skipped            += 1
        self._skips[reason]           = self._skips.get(reason, 0) + 1

    def stop(self):
        self.elapsed = time.perf_counter() - self._t0

    def summary(self) -> str:
        lines = [
            f"  Files scanned : {self.files_scanned:,}",
            f"  Files skipped : {self.files_skipped:,}",
        ]
        for reason, count in sorted(self._skips.items(),
                                     key=lambda x: -x[1]):
            lines.append(f"    ↳ {reason}: {count:,}")
        lines += [
            f"  With findings : {self.files_with_hits:,}",
            f"  Total findings: {self.total_findings:,}",
            f"  Data read     : {self.bytes_read / 1_048_576:.1f} MB",
            f"  Elapsed       : {self.elapsed:.2f}s",
        ]
        return "\n".join(lines)


def _safe_size(filepath: str) -> int:
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0
