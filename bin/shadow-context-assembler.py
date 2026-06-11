#!/usr/bin/env python3
"""shadow-context-assembler.py — the tmux-dump-shaped cousin of /tactical-hydration.

SOVEREIGN ENGINE (portable, arg-driven, no hardcoded federation paths). Assembles a
BOUNDED session-context packet from tdelta tmux delta-snapshots for a shadow apprentice
(or any consumer that needs "what just happened in this terminal" as bounded input).

RTCH discipline applied to tmux dumps:
  - read the INCREMENTAL delta pieces (`*-new-Nof*.txt`), NEVER the giant `*-full.txt`
  - bound the packet by a char budget (default 120k) — newest pieces first, oldest dropped
  - declare what was SKIPPED (never silently truncate) — the dropped pieces are named
  - tail-bias: the most recent terminal activity is the most relevant to a handoff

This is the ENGINE half of the shadow-cadence lane (Architect tic 399, engine-content
split). The federation supplies the CONTENT (which dump dir, where to write, the budget).

CLI:
  shadow-context-assembler.py --dump-dir DIR --out PATH [--budget-chars N] [--extra FILE ...]
  shadow-context-assembler.py --latest-under ~/tmux-dumps/incremental --session canon --out PATH
"""

import argparse
import sys
from pathlib import Path


def _newest_dump(root: Path, session: str) -> Path | None:
    """Newest `{session}-*` dump directory under root (by name — names are timestamped)."""
    if not root.is_dir():
        return None
    cands = sorted((d for d in root.iterdir() if d.is_dir() and d.name.startswith(session + "-")),
                   key=lambda d: d.name, reverse=True)
    return cands[0] if cands else None


def _delta_pieces(dump_dir: Path) -> list[Path]:
    """The incremental delta snapshots, in chronological order (1of24 .. 24of24).

    Sorted by the `Nof` index so 'newest first' selection is meaningful. The giant
    `*-full.txt` is DELIBERATELY excluded (RTCH: bounded chunks beat blind full reads)."""
    import re
    pieces = []
    for p in dump_dir.glob("*-new-*of*.txt"):
        m = re.search(r"-new-(\d+)of(\d+)\.txt$", p.name)
        idx = int(m.group(1)) if m else 0
        pieces.append((idx, p))
    return [p for _, p in sorted(pieces)]


def assemble(dump_dir: Path, budget_chars: int, extra: list[Path]) -> tuple[str, dict]:
    """Build the bounded packet. Returns (packet_text, provenance_dict).

    Tail-bias: include delta pieces NEWEST-first until the budget is hit; the dropped
    (older) pieces are enumerated in provenance — never silently omitted (federation KI).
    """
    pieces = _delta_pieces(dump_dir)
    meta = next(iter(dump_dir.glob("*-meta.txt")), None)

    included, skipped, used = [], [], 0
    # newest-first: reverse chronological so the freshest terminal activity is kept
    for p in reversed(pieces):
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            skipped.append((p.name, "unreadable"))
            continue
        if used + len(body) > budget_chars and included:
            skipped.append((p.name, f"over budget ({len(body)} chars)"))
            continue
        included.append((p, body))
        used += len(body)
    included.reverse()  # restore chronological order in the packet

    parts = []
    if meta and meta.is_file():
        parts.append(f"### tmux dump meta\n```\n{meta.read_text(encoding='utf-8', errors='replace').strip()}\n```\n")
    for p in included:
        parts.append(f"### {p[0].name}\n```\n{p[1].rstrip()}\n```\n")
    for ex in extra:
        if ex.is_file():
            parts.append(f"### extra: {ex.name}\n```\n{ex.read_text(encoding='utf-8', errors='replace').strip()}\n```\n")

    prov = {
        "dump_dir": str(dump_dir),
        "pieces_total": len(pieces),
        "pieces_included": [p[0].name for p in included],
        "pieces_skipped": skipped,
        "budget_chars": budget_chars,
        "chars_used": used,
        "extra_files": [str(e) for e in extra],
    }
    return "\n".join(parts), prov


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble a bounded tmux-delta context packet.")
    ap.add_argument("--dump-dir", help="explicit dump directory")
    ap.add_argument("--latest-under", help="root under which to pick the newest {session}-* dump")
    ap.add_argument("--session", default="canon", help="session prefix for --latest-under (default canon)")
    ap.add_argument("--out", required=True, help="output packet path (.md)")
    ap.add_argument("--budget-chars", type=int, default=120_000, help="max packet chars (default 120k)")
    ap.add_argument("--extra", nargs="*", default=[], help="extra files to append (e.g. terminal logs)")
    args = ap.parse_args()

    if args.dump_dir:
        dump_dir = Path(args.dump_dir).expanduser()
    elif args.latest_under:
        dump_dir = _newest_dump(Path(args.latest_under).expanduser(), args.session)
        if dump_dir is None:
            sys.stderr.write(f"no {args.session}-* dump under {args.latest_under}\n")
            return 2
    else:
        sys.stderr.write("need --dump-dir or --latest-under\n")
        return 2

    if not dump_dir.is_dir():
        sys.stderr.write(f"dump dir not found: {dump_dir}\n")
        return 2

    packet, prov = assemble(dump_dir, args.budget_chars, [Path(e).expanduser() for e in args.extra])

    header = (
        "# SESSION CONTEXT PACKET (tmux delta snapshots — bounded)\n"
        f"> source: {prov['dump_dir']}\n"
        f"> pieces: {len(prov['pieces_included'])}/{prov['pieces_total']} included "
        f"({prov['chars_used']} chars, budget {prov['budget_chars']})\n"
        f"> skipped (named, not silent): {', '.join(n for n, _ in prov['pieces_skipped']) or 'none'}\n\n"
    )
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + packet, encoding="utf-8")
    sys.stderr.write(
        f"[assembler] wrote {out} — {len(prov['pieces_included'])}/{prov['pieces_total']} pieces, "
        f"{prov['chars_used']} chars, {len(prov['pieces_skipped'])} skipped\n"
    )
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
