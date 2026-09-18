from __future__ import annotations

import argparse
import json
from pathlib import Path

from .candidates import candidate_count_report
from .cards import load_deck
from .validation import deterministic_checks, run_a, validate_candidate_report
from .run_c_validation import run_c
from .run_e_validation import run_e


def _root(value: str | None) -> Path:
    return Path(value).resolve() if value else Path.cwd().resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mana-lab")
    parser.add_argument("--root", help="repository root (defaults to current directory)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("candidate-count", help="enumerate/count legal candidates without simulation")
    subparsers.add_parser("deterministic-checks", help="print exact benchmark checks")
    subparsers.add_parser("run-a", help="execute build/validation smoke only")
    subparsers.add_parser("run-c", help="execute Run C remediation validation only")
    subparsers.add_parser("run-e", help="execute Run E remediation validation only")
    args = parser.parse_args(argv)
    root = _root(args.root)
    deck = load_deck(root / "configs" / "decks" / "Strixpatch_Affinity_v1.3.deck.yaml")
    if args.command == "candidate-count":
        report = candidate_count_report(deck)
        validate_candidate_report(report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.command == "deterministic-checks":
        print(json.dumps(deterministic_checks(deck), indent=2, sort_keys=True))
        return 0
    if args.command == "run-c":
        return run_c(root)
    if args.command == "run-e":
        return run_e(root)
    return run_a(root)


if __name__ == "__main__":
    raise SystemExit(main())
