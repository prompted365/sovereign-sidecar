# Router Specification

The router is the sidecar's single hook entry point. One `UserPromptSubmit` hook → one router skill → chamber read → intent match → optional quick-fire signal. Everything else is pointer-chased from the chamber.

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

The hook receives the user message JSON on stdin. It reads the chamber, assesses intent, and optionally emits quick-fire signal tags.

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

## Quick-Fire Output

When an arrow is warranted (confidence > disposition_bias), the router emits a signal tag in its hook output:

```html
<sidecar key="complement_due" target="commit_message" confidence="0.85" />
```

The hook output mechanism depends on the harness:
- **Claude Code**: `hookSpecificOutput.additionalContext` carries the tag
- **Grok**: hook stdout carries the tag  
- **Generic**: stdout; the consuming harness must regex-match `<sidecar ... />`

## Signal Tag Schema

```
<sidecar
  key="<arrow_name>_<trigger_verb>"    # e.g. "complement_due", "counter_warranted"
  target="<what_to_examine>"           # e.g. "pr-description", "schema_change"
  confidence="<0.0-1.0>"              # router's pattern-match confidence
  chamber_bias="<0.0-1.0>"            # disposition_bias from chamber
/>
```

A downstream hook or the harness itself catches the tag and:
1. Reads the arrow's `pointer` from the chamber
2. Pulls context from the pointer target (bounded read)
3. Fires the arrow skill with that context
4. Returns the arrow's output to the human thread

## What the Router Does NOT Do

- Does not call LLMs (zero-cost hook)
- Does not read skill bodies (reads chamber pointers only)
- Does not persist state (session dies, chamber dies)
- Does not block the primary work (parallel, non-blocking hook)
- Does not fire arrows directly (emits signals; downstream hooks fire arrows)
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
