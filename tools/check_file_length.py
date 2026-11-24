"""Fail when a source file is over the line limit (non-blank lines).

ESLint `max-lines` already covers .ts and .html; this covers the file types it can't
(.py, .scss) so every language has the same 400-line ceiling.
Usage: python tools/check_file_length.py [--max N] [FILES...]  (no files: scan the repo)
"""

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_MAX = 400
SUFFIXES = (".py", ".scss")
EXCLUDED_PARTS = ("generated", "migrations", "node_modules", "dist")


def tracked_files() -> list[Path]:
    """Return git-tracked files with a checked suffix."""
    out = subprocess.run(  # noqa: S603 -- fixed argv, no shell
        ["git", "ls-files", *(f"*{suffix}" for suffix in SUFFIXES)],  # noqa: S607 -- git on PATH
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [Path(line) for line in out.splitlines() if line]


def is_checked(path: Path) -> bool:
    """Return True if the file type and location are in scope."""
    return path.suffix in SUFFIXES and not any(part in EXCLUDED_PARTS for part in path.parts)


def count_lines(path: Path) -> int:
    """Count non-blank lines."""
    text = path.read_text(encoding="utf-8", errors="replace")
    return sum(1 for line in text.splitlines() if line.strip())


def main(argv: list[str] | None = None) -> int:
    """Report every oversized file; exit 1 if any."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max", type=int, default=DEFAULT_MAX)
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args(argv)

    files = args.files or tracked_files()
    too_long = [(p, n) for p in files if is_checked(p) and (n := count_lines(p)) > args.max]
    for path, lines in too_long:
        sys.stderr.write(f"{path}: {lines} lines (max {args.max}); split it into smaller files\n")
    return 1 if too_long else 0


if __name__ == "__main__":
    sys.exit(main())
