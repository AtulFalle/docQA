"""Command-line entry point: ``docqa-eval validate`` and ``docqa-eval stats``."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from docqa_eval.dataset import (
    dataset_stats,
    load_golden,
    load_manifest,
    validate_dataset,
    validate_tenants,
)
from docqa_eval.schema import GoldenItem


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docqa-eval", description="docQA evaluation tools")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a golden JSONL file")
    validate.add_argument("golden", type=Path, help="path to golden JSONL")
    validate.add_argument(
        "--corpus", type=Path, default=None, help="corpus dir containing manifest.json"
    )

    stats = sub.add_parser("stats", help="print dataset statistics as JSON")
    stats.add_argument("golden", type=Path, help="path to golden JSONL")
    return parser


def _validate(items: list[GoldenItem], corpus: Path | None) -> int:
    doc_ids: set[str] | None = None
    errors: list[str] = []
    if corpus is not None:
        manifest = load_manifest(corpus / "manifest.json")
        doc_ids = set(manifest)
        errors.extend(validate_tenants(items, manifest))
        errors.extend(
            f"manifest doc {doc_id!r} has no file {doc_id}.md"
            for doc_id in sorted(manifest)
            if not (corpus / f"{doc_id}.md").is_file()
        )
    errors = validate_dataset(items, doc_ids) + errors
    for message in errors:
        sys.stderr.write(f"error: {message}\n")
    if errors:
        sys.stderr.write(f"{len(errors)} error(s) found\n")
        return 1
    sys.stdout.write(f"OK: {len(items)} items valid\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    args = _build_parser().parse_args(argv)
    try:
        items = load_golden(args.golden)
        if args.command == "stats":
            sys.stdout.write(json.dumps(dataset_stats(items), indent=2, sort_keys=True) + "\n")
            return 0
        return _validate(items, args.corpus)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
