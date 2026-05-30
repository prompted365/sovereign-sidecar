#!/usr/bin/env python3
"""
Sovereign Sidecar — Chamber Fill (v0.2, layered).

Writes the v0.2 chamber: the sidecar's only organ for holding constitutional state
(the stateless cousin of Ubiquity's harmony disposition). Two layers:

  L1  STRUCTURED BASE  (cheap, always-on, no LLM)
        cwd / repo-shape / git-state / file-types / explicit posture toggle
        → posture HINT + a coarse mode HINT + a structured stakes signal + repo_shape
        The floor the sidecar never goes blind below.

  L2  LLM ENRICH       (triggered, deep — NOT per-prompt)
        shells out to the `claude` CLI to resolve MODE, write a rich disposition
        (the constitutional backdrop), per-arrow live_context, and a disposition_lean
        that DERIVES the per-arrow biases (§4 of specs/chamber-v2.md).

Honesty about the split (spec §2): L1 *hints* posture and (only via an explicit
[Posture → X/Y] toggle) mode; it CANNOT reliably resolve the working mode from
cwd/git alone. Without L2 (or a toggle), mode is written as `unresolved` so the
router gates conservatively rather than acting on a guess.

Degradation ladder (fail-soft, spec §2):
  1. L1 + L2 fresh   → full backdrop; biases derived; mode resolved.
  2. L1 only         → coarse backdrop; mode `unresolved`; biases = conservative
                        structured defaults. Shallower, not blind.
  3. (router side)   → no chamber at all → router fail-soft to raw pattern match.

Trigger discipline (spec §5): L2 is NOT per-prompt. It runs on session-start ∪
posture-shift ∪ stakes-crossed (∪ --force / --enrich). Between triggers the router
reads the cached chamber. A refreshed_at + TTL guards staleness (Volatility Handling
Law — internal snapshots carry explicit timestamps/TTLs).

Usage:
  python3 chamber_fill.py [--root PATH] [--out PATH]
                          [--posture ENG/DIRECT]          # explicit toggle (resolves mode)
                          [--trigger session_start|posture_shift|stakes_crossed|manual]
                          [--enrich] [--no-enrich]        # force / forbid L2
                          [--model MODEL] [--ttl-min N] [--force] [--now ISO]

Exit codes: 0 always when a chamber is written (fail-soft); 2 only on unwritable --out.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------------
# Conservative structured-default biases (the L1-only fallback floor).
# These are the documented constants the spec §4 calls for — NOT the old
# hand-tuned "magic floats". Lower bias = fires more easily.
# ----------------------------------------------------------------------
DEFAULT_BIAS = {
    "ingest": 0.40,
    "tom": 0.45,
    "complement": 0.55,
    "counter": 0.50,
    "citation_intel": 0.50,
    "delegate": 0.55,
    "preflight": 0.45,
}

ARROW_POINTERS = {
    "ingest": "skills/ingest/SKILL.md",
    "tom": "skills/tom/SKILL.md",
    "complement": "skills/complement/SKILL.md",
    "counter": "skills/counter/SKILL.md",
    "citation_intel": "skills/citation-intel/SKILL.md",
    "posture": "skills/posture/SKILL.md",
    "delegate": "skills/delegate/SKILL.md",
    "preflight": "skills/preflight/SKILL.md",
}

ARROW_STANCE = {
    "ingest": "metabolize",
    "tom": "centroid_preserving",
    "complement": "cooperative_topological",
    "counter": "adversarial_falsifying",
    "citation_intel": "readiness_check",
    "posture": "contract_declaration",
    "delegate": "swarm_governing",
    "preflight": "preflight_obstacle_avoidance",
}

# Mutation-class arrows (META suppresses their firing; DIRECT raises it).
_MUTATION_ARROWS = {"preflight"}
# Analysis-class arrows (META raises their firing — analysis is allowed read-only).
_ANALYSIS_ARROWS = {"counter", "complement"}

# Risk surfaces for the L1 stakes signal — reuse the router's vocabulary so the
# two layers agree on what "risky" means (spec §9 open-question: don't over-escalate).
_RISKY_PATH_RE = re.compile(
    r"(migrations?/|\b(ledger|charge|refund|payment|payout|balance|transaction|webhook)\b|"
    r"\.env\b|secrets?|credential|package\.json|package-lock|yarn\.lock|"
    r"Dockerfile|docker-compose|/deploy|/prod|\.github/workflows/)",
    re.IGNORECASE,
)
# Concept words whose multiple writers form an invariant hotspot (coupled surfaces).
_HOTSPOT_WORDS = ["ledger", "charge", "refund", "payment", "payout", "balance",
                  "transaction", "auth", "idempotenc", "migration", "secret"]

_LANG_BY_EXT = {
    ".ts": "ts", ".tsx": "ts", ".js": "js", ".jsx": "js", ".py": "py",
    ".rs": "rust", ".go": "go", ".sql": "sql", ".rb": "ruby", ".java": "java",
    ".kt": "kotlin", ".c": "c", ".cpp": "cpp", ".h": "c", ".sh": "sh",
    ".md": "md", ".yaml": "yaml", ".yml": "yaml", ".json": "json",
}

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
              "build", ".next", "target", ".cache", "vendor", ".iso-home"}


def _now_iso(override=None):
    if override:
        return override
    # new datetime() is fine here (script context, not workflow); UTC ISO-8601.
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


# ----------------------------------------------------------------------
# L1 — structured base (cheap, deterministic, no LLM)
# ----------------------------------------------------------------------

def _git_dirty(root: Path):
    """True if the tree has uncommitted changes. Fail-soft → False."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        return bool(out.stdout.strip())
    except Exception:
        return False


def _scan_repo(root: Path, max_files=4000):
    """Walk the repo once. Returns (languages, dirty_risky_paths, hotspot_counts, all_risky_paths)."""
    langs = {}
    risky = []
    dirty_risky = []
    hotspot_counts = {w: 0 for w in _HOTSPOT_WORDS}
    seen = 0
    try:
        dirty_set = _git_dirty_files(root)
    except Exception:
        dirty_set = set()
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
            for fn in filenames:
                seen += 1
                if seen > max_files:
                    break
                ext = os.path.splitext(fn)[1].lower()
                lang = _LANG_BY_EXT.get(ext)
                if lang:
                    langs[lang] = langs.get(lang, 0) + 1
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                if _RISKY_PATH_RE.search(rel):
                    risky.append(rel)
                    if rel in dirty_set:
                        dirty_risky.append(rel)
                low = fn.lower()
                for w in _HOTSPOT_WORDS:
                    if w in low or w in rel.lower():
                        hotspot_counts[w] += 1
            if seen > max_files:
                break
    except Exception:
        pass
    # languages sorted by frequency, top 5
    languages = [l for l, _ in sorted(langs.items(), key=lambda kv: -kv[1])][:5]
    hotspots = [w for w, c in sorted(hotspot_counts.items(), key=lambda kv: -kv[1]) if c > 0][:6]
    return languages, dirty_risky, hotspots, risky


def _git_dirty_files(root: Path):
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        files = set()
        for line in out.stdout.splitlines():
            # porcelain: "XY path"
            path = line[3:].strip()
            if "->" in path:  # renames
                path = path.split("->")[-1].strip()
            if path:
                files.add(path)
        return files
    except Exception:
        return set()


def _infer_posture(root: Path, explicit, languages, git_dirty):
    """Return (posture_value, posture_source, mode_value, mode_source, confidence).

    Explicit --posture toggle (always wins) resolves BOTH posture and mode.
    Otherwise L1 infers a posture LEAN from repo shape, and leaves mode unresolved
    (L1 cannot reliably resolve DIRECT vs META — spec §2).
    """
    if explicit:
        m = re.match(r"\s*([A-Za-z]+)\s*/\s*([A-Za-z]+)\s*$", explicit)
        if m:
            dom, dep = m.group(1).upper(), m.group(2).upper()
            return f"{dom}/{dep}", "toggle", dep, "toggle", 0.95
    # Inferred lean (cheap): code-heavy repo → ENG; ops/infra-heavy → OPS lean.
    domain = "ENG"
    ops_signal = any(l in ("sql", "sh", "yaml") for l in languages[:2])
    code_signal = any(l in ("ts", "js", "py", "rust", "go") for l in languages[:2])
    if ops_signal and not code_signal:
        domain = "OPS"
    # Mode: L1 only HINTS. A dirty tree leans DIRECT (work in flight) but cannot
    # RESOLVE it — keep source "hinted" with a coarse value, or "unresolved" if no signal.
    if git_dirty:
        return f"{domain}/DIRECT", "inferred", "DIRECT", "hinted", 0.45
    return f"{domain}/DIRECT", "default", "DIRECT", "unresolved", 0.30


def compute_l1(root: Path, explicit_posture=None):
    """Compute the L1 structured base. Always succeeds (fail-soft to safe defaults)."""
    root = root.resolve()
    languages, dirty_risky, hotspots, all_risky = _scan_repo(root)
    git_dirty = _git_dirty(root)
    posture_v, posture_src, mode_v, mode_src, conf = _infer_posture(
        root, explicit_posture, languages, git_dirty
    )

    # Stakes: dirty work on a risky path = elevated/high; risky paths present = elevated; else low.
    signals = []
    for p in dirty_risky[:6]:
        signals.append(f"dirty:{p}")
    for h in hotspots[:4]:
        signals.append(f"hotspot:{h}")
    if dirty_risky:
        level = "high"
    elif all_risky or hotspots:
        level = "elevated"
    else:
        level = "low"

    return {
        "posture": {"value": posture_v, "source": posture_src, "confidence": round(conf, 2)},
        "mode": {"value": mode_v, "source": mode_src},
        "stakes": {"level": level, "signals": signals},
        "repo_shape": {
            "root": str(root),
            "languages": languages,
            "invariant_hotspots": hotspots,
            "git_dirty": git_dirty,
        },
    }


# ----------------------------------------------------------------------
# §4 — biases are DERIVED from the backdrop, not hand-tuned
# ----------------------------------------------------------------------

def derive_biases(l1, disposition_lean=None):
    """bias(arrow) = f(disposition_lean, posture, mode, stakes, repo_shape).

    Lower bias = fires more easily. Returns {arrow: float}. Pure function over the
    L1 base + the optional L2 disposition_lean ({arrow: 'hard'|'soft'|'suppress'}).
    """
    lean = disposition_lean or {}
    mode = (l1.get("mode") or {}).get("value", "DIRECT")
    mode_src = (l1.get("mode") or {}).get("source", "unresolved")
    stakes = (l1.get("stakes") or {}).get("level", "low")
    hotspots = (l1.get("repo_shape") or {}).get("invariant_hotspots", []) or []

    out = {}
    for arrow, base in DEFAULT_BIAS.items():
        bias = base

        # --- mode modulation (only when mode is RESOLVED; unresolved → stay conservative) ---
        if mode_src in ("resolved", "toggle"):
            if mode == "META":
                if arrow in _MUTATION_ARROWS:
                    bias += 0.25       # META suppresses mutation-class firing
                if arrow in _ANALYSIS_ARROWS:
                    bias -= 0.10       # META raises analysis lanes
            elif mode == "DIRECT":
                if arrow in _MUTATION_ARROWS:
                    bias -= 0.10       # DIRECT raises preflight / PreToolUse

        # --- stakes modulation ---
        if stakes == "high":
            if arrow in ("preflight", "counter"):
                bias -= 0.15
        elif stakes == "elevated":
            if arrow in ("preflight", "counter"):
                bias -= 0.07

        # --- repo_shape modulation: coupled hotspots → eager preflight ---
        if hotspots and arrow == "preflight":
            bias -= 0.05

        # --- L2 disposition_lean (dominant) ---
        l = str(lean.get(arrow, "")).lower()
        if l == "hard":
            bias -= 0.20
        elif l == "soft":
            bias += 0.15
        elif l == "suppress":
            bias = 1.0

        out[arrow] = round(_clamp(bias), 2)
    return out


# ----------------------------------------------------------------------
# L2 — LLM enrich (shells to the claude CLI; fail-soft to L1-only)
# ----------------------------------------------------------------------

L2_SYSTEM = (
    "You are the Sovereign Sidecar chamber-fill enrich pass. You read a STRUCTURED "
    "BASE about a repo/session and return ONLY a compact JSON object — no prose, no "
    "markdown fence. The JSON is the constitutional backdrop the sidecar carries for "
    "this session (the stateless cousin of a persistent disposition). Be concrete and "
    "honest; this shapes which governance lanes fire."
)

L2_ARROWS = ["ingest", "tom", "complement", "counter", "citation_intel", "delegate", "preflight"]

L2_INSTRUCTION = """\
Given this L1 structured base:

{l1_json}

Return ONLY this JSON shape (no fence):
{{
  "mode": {{"value": "DIRECT | META", "source": "resolved"}},
  "disposition": {{
    "text": "2-4 sentences: the SHAPE of the work, what it's biased toward, and WHY. Name the live risk.",
    "meaning_state": "preserved | strained | dissonant"
  }},
  "disposition_lean": {{ "<arrow>": "hard | soft | suppress", ... }},
  "live_context": {{ "<arrow>": "one line: what this lane means RIGHT NOW for THIS work", ... }}
}}

Arrows you may key: {arrows}.
- disposition_lean: only list arrows the work clearly biases toward (hard) or away from
  (soft/suppress); omit the neutral ones.
- live_context: write a line ONLY for arrows that have a concrete meaning this session;
  omit the rest. Each line must reference the actual repo shape / hotspots above.
- Resolve mode from the work shape; if genuinely ambiguous, prefer "META" (conservative).
"""


def run_l2(l1, model, timeout=180):
    """Shell to the claude CLI to enrich. Returns parsed dict or None (fail-soft)."""
    if not _claude_available():
        return None
    prompt = L2_INSTRUCTION.format(
        l1_json=json.dumps(l1, indent=2),
        arrows=", ".join(L2_ARROWS),
    )
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--model", model,
             "--append-system-prompt", L2_SYSTEM,
             "--output-format", "json", "--max-turns", "1"],
            capture_output=True, text=True, timeout=timeout,
        )
        if proc.returncode != 0:
            return None
        return _parse_l2(proc.stdout)
    except Exception:
        return None


def _parse_l2(stdout):
    """Extract the enrich JSON from the claude -p envelope. Fail-soft → None."""
    try:
        env = json.loads(stdout)
        result = env.get("result") if isinstance(env, dict) else None
        text = result if isinstance(result, str) else stdout
    except Exception:
        text = stdout
    # The result text should be raw JSON; tolerate a stray fence.
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _claude_available():
    try:
        from shutil import which
        return which("claude") is not None
    except Exception:
        return False


# ----------------------------------------------------------------------
# Chamber assembly + emission
# ----------------------------------------------------------------------

def build_chamber(l1, l2, trigger, now_iso):
    """Assemble the v0.2 chamber dict from L1 (always) + L2 (optional)."""
    layers = ["L1"]
    mode = dict(l1.get("mode") or {})
    disposition = None
    live_context = {}
    lean = {}

    if l2:
        layers.append("L2")
        l2_mode = l2.get("mode") or {}
        if l2_mode.get("value") in ("DIRECT", "META"):
            mode = {"value": l2_mode["value"], "source": "resolved"}
        disp = l2.get("disposition") or {}
        disposition = {
            "text": str(disp.get("text", "")).strip() or "(enrich returned no disposition text)",
            "meaning_state": disp.get("meaning_state", "preserved"),
            "derived_at": now_iso,
        }
        lean = l2.get("disposition_lean") or {}
        live_context = l2.get("live_context") or {}

    # Effective L1 for derivation must carry the (possibly L2-resolved) mode.
    l1_for_derive = dict(l1)
    l1_for_derive["mode"] = mode
    biases = derive_biases(l1_for_derive, lean)

    arrows = {}
    for arrow in DEFAULT_BIAS:
        entry = {
            "pointer": ARROW_POINTERS.get(arrow, f"skills/{arrow}/SKILL.md"),
            "bias": biases[arrow],
            "stance": ARROW_STANCE.get(arrow, ""),
        }
        lc = live_context.get(arrow)
        if lc:
            entry["live_context"] = str(lc).strip()
        ld = lean.get(arrow)
        if ld:
            entry["disposition_lean"] = str(ld).strip()
        arrows[arrow] = entry

    # posture arrow is toggle-detected, not bias-gated — carry it for completeness.
    arrows["posture"] = {
        "pointer": ARROW_POINTERS["posture"],
        "stance": ARROW_STANCE["posture"],
    }

    chamber = {
        "schema_version": "0.2",
        "posture": l1.get("posture"),
        "mode": mode,
        "stakes": l1.get("stakes"),
        "repo_shape": l1.get("repo_shape"),
        "disposition": disposition or {
            "text": "(L1-only — no enrich; mode unresolved, biases are conservative defaults)",
            "meaning_state": "preserved",
            "derived_at": None,
        },
        "arrows": arrows,
        "support": {
            "tactical_hydration": {"pointer": "skills/tactical-hydration/SKILL.md",
                                   "role": "discover pointer targets at fill"},
            "consolidate": {"pointer": "skills/consolidate/SKILL.md",
                            "role": "package discovered targets into chamber-consumable form"},
        },
        "refreshed_at": now_iso,
        "fill_source": trigger,
        "layers_present": layers,
        "muted": [],
    }
    return chamber


def emit_yaml(chamber):
    """Serialize the chamber to YAML. Prefer PyYAML; fall back to a hand emitter."""
    try:
        import yaml
        return yaml.safe_dump(chamber, sort_keys=False, default_flow_style=False, width=100)
    except Exception:
        return _hand_yaml(chamber)


def _hand_yaml(obj, indent=0):
    """Minimal YAML emitter for the chamber shape (dicts, lists, scalars, multiline str)."""
    pad = "  " * indent
    lines = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, dict):
                if not v:
                    lines.append(f"{pad}{k}: {{}}")
                else:
                    lines.append(f"{pad}{k}:")
                    lines.append(_hand_yaml(v, indent + 1))
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{pad}{k}: []")
                else:
                    lines.append(f"{pad}{k}:")
                    for item in v:
                        lines.append(f"{pad}  - {_scalar(item)}")
            elif isinstance(v, str) and "\n" in v:
                lines.append(f"{pad}{k}: |")
                for ln in v.splitlines():
                    lines.append(f"{pad}  {ln}")
            else:
                lines.append(f"{pad}{k}: {_scalar(v)}")
    return "\n".join(lines)


def _scalar(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or re.search(r"[:#\[\]{}]|^\s|\s$|^[>|&*!%@`]", s):
        return json.dumps(s)
    return s


# ----------------------------------------------------------------------
# Trigger / staleness gate (spec §5)
# ----------------------------------------------------------------------

_ENRICH_TRIGGERS = {"session_start", "posture_shift", "stakes_crossed"}


def _is_fresh(out_path: Path, ttl_min, now_iso):
    """True if an existing chamber at out_path is within TTL (skip re-enrich)."""
    if ttl_min is None or ttl_min <= 0:
        return False
    try:
        import yaml
        existing = yaml.safe_load(out_path.read_text())
        ts = (existing or {}).get("refreshed_at")
        if not ts:
            return False
        prev = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        now = datetime.strptime(now_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        age_min = (now - prev).total_seconds() / 60.0
        # only "fresh" if it already has L2 — an L1-only cache should still upgrade.
        has_l2 = "L2" in ((existing or {}).get("layers_present") or [])
        return age_min < ttl_min and has_l2
    except Exception:
        return False


def should_enrich(args, out_path, now_iso):
    """Decide whether to run L2 this fill. Returns (do_enrich, reason)."""
    if args.no_enrich:
        return False, "forbidden by --no-enrich"
    if args.enrich:
        return True, "forced by --enrich"
    if args.trigger not in _ENRICH_TRIGGERS:
        return False, f"trigger '{args.trigger}' is not an enrich trigger"
    if not args.force and out_path and out_path.is_file() and _is_fresh(out_path, args.ttl_min, now_iso):
        return False, "cached chamber still fresh (within TTL)"
    if not _claude_available():
        return False, "claude CLI not available (L1-only)"
    return True, f"trigger '{args.trigger}'"


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def default_out_path():
    env = os.environ.get("SIDECAR_CHAMBER")
    if env:
        return Path(env).expanduser()
    for cand in ("~/.sidecar/chamber.yaml", "~/.claude/sidecar/chamber.yaml"):
        p = Path(cand).expanduser()
        if p.parent.is_dir():
            return p
    return Path("~/.sidecar/chamber.yaml").expanduser()


def main():
    ap = argparse.ArgumentParser(description="Fill the Sovereign Sidecar v0.2 chamber (L1 + optional L2).")
    ap.add_argument("--root", default=".", help="repo root to read L1 from (default cwd)")
    ap.add_argument("--out", default=None, help="chamber output path (default: $SIDECAR_CHAMBER or ~/.sidecar/chamber.yaml)")
    ap.add_argument("--posture", default=None, help="explicit posture toggle, e.g. ENG/DIRECT (resolves mode)")
    ap.add_argument("--trigger", default="manual",
                    choices=["session_start", "posture_shift", "stakes_crossed", "manual"])
    ap.add_argument("--enrich", action="store_true", help="force L2 enrich")
    ap.add_argument("--no-enrich", action="store_true", help="forbid L2 (L1-only)")
    ap.add_argument("--model", default=os.environ.get("SIDECAR_ENRICH_MODEL", "claude-sonnet-4-6"))
    ap.add_argument("--ttl-min", type=float, default=120.0, help="staleness TTL in minutes")
    ap.add_argument("--force", action="store_true", help="ignore TTL freshness")
    ap.add_argument("--now", default=None, help="override ISO timestamp (testing)")
    ap.add_argument("--print", dest="do_print", action="store_true", help="also print the chamber to stdout")
    args = ap.parse_args()

    now_iso = _now_iso(args.now)
    out_path = Path(args.out).expanduser() if args.out else default_out_path()

    # L1 always.
    root = Path(args.root)
    l1 = compute_l1(root, args.posture)

    # L2 gate.
    do_enrich, reason = should_enrich(args, out_path, now_iso)
    l2 = run_l2(l1, args.model) if do_enrich else None
    if do_enrich and l2 is None:
        reason += " → enrich attempted but failed; L1-only"

    chamber = build_chamber(l1, l2, args.trigger, now_iso)
    text = emit_yaml(chamber)

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text)
    except Exception as e:
        print(f"FATAL: cannot write chamber to {out_path}: {e}", file=sys.stderr)
        sys.exit(2)

    layers = "+".join(chamber["layers_present"])
    print(f"[chamber_fill] wrote {out_path} · layers={layers} · "
          f"mode={chamber['mode'].get('value')}({chamber['mode'].get('source')}) · "
          f"stakes={chamber['stakes'].get('level')} · enrich={reason}", file=sys.stderr)
    if args.do_print:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
