"""Run one explicit offline PDF typesetting performance scenario.

The runner requires a completed translation HTML and never contacts Ollama.
Use a distinct output path for each mode when comparing reports.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from doctranslate import translate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark offline PDF typesetting")
    parser.add_argument("--infile", type=Path, required=True, help="source PDF")
    parser.add_argument("--htmlfile", type=Path, required=True, help="completed translation HTML")
    parser.add_argument("--outfile", type=Path, required=True, help="benchmark output PDF")
    parser.add_argument("--mode", choices=("adaptive", "memory", "checkpoint"), default="adaptive")
    parser.add_argument("--checkpoint-pages", type=int, default=16)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.checkpoint_pages < 1:
        raise SystemExit("--checkpoint-pages must be positive")
    if not args.infile.is_file():
        raise SystemExit(f"Input PDF does not exist: {args.infile}")
    if not args.htmlfile.is_file():
        raise SystemExit(f"Translation HTML does not exist: {args.htmlfile}")

    translate.configure(args.infile, args.outfile, "en", "cs")
    translate.configure_phases("pdf", args.htmlfile)
    translate.use_html_job_metadata(translate.read_translation_html(args.htmlfile).metadata)
    translate.PDF_SAVE_MODE = args.mode
    translate.PDF_CHECKPOINT_PAGES = args.checkpoint_pages
    translate.TRACE = True
    translate.main()

    print(f"Performance JSON: {args.outfile.with_suffix('.performance.json')}")
    print(f"Performance Markdown: {args.outfile.with_suffix('.performance.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
