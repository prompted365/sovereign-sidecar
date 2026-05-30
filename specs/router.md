# Router Specification

The router is the sidecar's single hook entry point. One `UserPromptSubmit` hook → one router skill → chamber read → intent match → optional lane directive injection. Everything else is pointer-chased from the chamber.

## Hook Registration

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3",
            "args": ["${SIDECAR_ROOT}/hooks/sidecar-router.py"]
          }
        ]
      }
    ]
  }
}
```

The hook receives the user message JSON on stdin. It reads the chamber, assesses intent, and — when an arrow is warranted — injects the matched lane's protocol as a readable directive into `hookSpecificOutput.additionalContext`.

## Intent Assessment

The router classifies the user message against the chamber's arrow fire conditions:

| Signal | Detection Pattern | Arrow |
|---|---|---|
| External context entering | URLs, file refs, paste markers, "look at this", API docs | `/ingest` |
| Move landed | commit messages, "done", "shipped", PR description shorter than diff | `/complement` |
| Irreversible decision pending | architecture choices, "should we", schema changes, API contracts | `/counter` |
| Audience shift | "for the board", "explain to", "compress for", "rewrite as" | `/tom` |
| Publication pending | "publish", "deploy", "push to prod", "make public" | `/citation-intel` |
| Posture toggle | `[Posture →`, `POSTURE:` banner | Chamber disposition refresh |

The router does NOT use an LLM for classification. It uses keyword/regex pattern matching against the chamber's fire conditions. This keeps cost at zero — the hook is a Python script, not a model call.

## Lane Directive Output

When an arrow is warranted (confidence > disposition_bias), the router injects the
matched lane's **protocol as a readable directive** into its hook output. The model
reads the directive and runs that lane inline — the router does not emit a machine
tag and hope a downstream hook fires the arrow.

```
[sidecar · counter] An irreversible / hard-to-reverse decision looks imminent.
Run the COUNTER lane inline — you are the genuine adversary, not a devil's advocate:
  1. State the move in one sentence.
  2. Name the single premise that, if false, makes the whole move wrong.
  3. Build the strongest case it WILL fail (not "might") — cite evidence, or mark
     "structural, no current evidence."
  4. Verdict: HOLD / REVISE / PROCEED-WITH-AWARENESS. Do not soften to stay agreeable.
  (arrow: counter_warranted · confidence 0.75 · chamber_bias 0.40)
```

The hook output mechanism depends on the harness:
- **Claude Code**: `hookSpecificOutput.additionalContext` carries the directive
- **Generic**: stdout; the consuming harness injects it into the model's context

The trailing `(arrow: <key>_<verb> · …)` provenance line stays human-readable while
remaining greppable, so a tool that still wants to detect which lane fired can do so
without parsing a machine-only dict.

## Why a directive, not a tag

An earlier version emitted a KV tag (`<sidecar key="counter_warranted" .../>`) and
relied on a downstream hook to read the chamber pointer and fire the arrow. Two
problems: (1) that downstream consumer was never universal — without it, the tag did
nothing, which is exactly why the sidecar felt inert; (2) a machine KV blob is not
actionable by the model, and model-visible context should be human-readable text
intended for the LLM, not an inter-extension dict. Injecting the lane protocol makes
the **model** the consumer — no second hook required, and the arrow's actual
reasoning lands in the thread instead of a tag nobody reads.

## What the Router Does NOT Do

- Does not call LLMs (zero-cost hook)
- Does not read skill bodies (reads chamber pointers only)
- Does not persist state (session dies, chamber dies)
- Does not block the primary work (parallel, non-blocking hook)
- Does not require a second hook to act (the directive makes the model run the lane inline)
- Does not replace harness-native orchestration (wraps it with governance)

## Outpost Boundary (Zone-Aware Deferral)

The sidecar is the governance shim for **non-Ubiquity environments**. When the real federation is already present, the router defers and stays silent — it has arrived at the thing it was an onramp toward.

On every prompt the router walks from `cwd` up to filesystem root looking for a zone marker: `.ticzone`, `.federation-root`, `.estate-root`, `.domain-root`, or `.site-root`. If any is found, the router emits nothing and exits 0. This makes **global (user-scope) registration safe**: install once, fire everywhere a real federation is absent, fall silent wherever CGG/Ubiquity already governs.

This is the **outpost**: a hook that fires as a domain-level presence and stops at the zone root. The same primitive scopes a resident outpost (e.g. a visiting `homeskillet-gk`) to a domain boundary rather than bleeding across rungs.

Override with `SIDECAR_IGNORE_ZONE=1` (testing / debug / forced fire).

## Harness Compatibility

The router is designed to work across agent harnesses:

| Harness | Hook Event | Signal Delivery | Arrow Firing |
|---|---|---|---|
| Claude Code | `UserPromptSubmit` | `hookSpecificOutput.additionalContext` | Skill invocation via injected context |
| Grok | `user-prompt-submit` (if supported) | stdout → session context | Skill invocation via context |
| Cursor | Custom hook (TBD) | Comment injection | Rule-based trigger |
| Generic CLI | stdin/stdout pipe | stdout | Manual or scripted |

Phase 1 targets Claude Code and Grok. Other harnesses are future work gated on hook API availability.

## Cost Model

- Chamber fill: one-time at session start (~3-5 tool calls for /tactical-hydration + /consolidate + /tom)
- Per-message router: zero LLM cost (regex/keyword Python script)
- Arrow fire: LLM cost only when an arrow actually fires (confidence > bias)
- Expected fire rate: 1 arrow per ~10-15 user messages in a typical implementation session

The sidecar's steady-state cost is approximately zero. Cost spikes only when governance is warranted.
