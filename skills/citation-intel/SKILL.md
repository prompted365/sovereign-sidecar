---
name: citation-intel
description: |
  Agentic citation intelligence and AI-search optimization for long-form
  publication. Trigger on /citation-intel, "is this citation ready", "what
  schema for", "optimize for citation", or any request to check discoverability
  / schema / token efficiency / citation readiness before publication.

  CENTROID:
  article-specific citation intelligence — what makes AI agents cite this
  article in 2026, not generic SEO

  IS:
  - extractable-claim check (is the primary claim in the first 500 tokens?)
  - entity-density scan (proper nouns + concrete stats — agents cite 3× more)
  - FAQPage schema generator (AI cites FAQ content heavily)
  - community-language alignment (Perplexity cites Reddit at 24%)
  - token-efficiency audit (posts <10k, articles <20k, centroid <15k)
  - site-level AI-access stack audit (robots.txt allowlist, llms.txt)

  IS NOT:
    collapse_zones:
      - prestige SEO advice (keyword-stuffed listicles are tier-3, skipped entirely)
      - generic content marketing (must be article-specific, never templated)
      - llms.txt evangelism (llms.txt is one signal, not the whole game)
      - "add FAQ schema" boilerplate (FAQ must be article-derived, no new claims)
      - publication action (citation-intel checks readiness; publish is downstream)
    sibling_overlaps:
      - /tom (both pre-publication; tom re-expresses, citation-intel optimizes
        for citation)
      - /complement (both check for missing pieces; complement on structure,
        citation-intel on discoverability)

  WHEN:
  - before publishing long-form to AI-searchable surfaces (blog, docs, paper)
  - when an article should be cited by Perplexity / ChatGPT / Claude in
    response to topic queries
  - when the sidecar router injects a `citation_ready_due` lane directive into additionalContext
  - on site-level audit request (robots.txt / llms.txt / AI crawler allowlist)

  NOT WHEN:
  - for internal-only documents (no citation surface exists)
  - for short-form (tweet / chat / single-screen — token efficiency moot)
  - for non-AI-searchable formats (PDF behind login, internal wiki)
user-invocable: true
---

# /citation-intel — Citation-Ready Audit

Article-specific citation intelligence, not generic SEO. What actually moves AI
citation in 2026:

- **Extractable claim in first 500 tokens** — agents skip preamble
- **Entity density** — proper nouns + concrete stats cited 3× more
- **Synthesis content** — centroid articles are citation gold
- **FAQPage schema** — AI cites FAQ content heavily
- **Community language alignment** — Perplexity cites Reddit at 24%
- **Token efficiency** — posts <10k, articles <20k, centroid <15k
- **robots.txt AI allowlist** — 96% of top domains haven't done this

## Inputs

```yaml
slug:          [identifier]
article-type:  BIZ | INFRA | CENTROID
headline:      [plain text]
lede:          [plain text]
draft-body:    [full draft]
skip-research: false  # set true to return schema only (quick mode)
```

## Outputs

```yaml
status:          ok | blocked
blocked-reason:  null | [string]

primary-claim:   "[single extractable sentence]"
claim-in-500:    true | false
token-estimate:  [integer]
entities:        [list of proper nouns + concrete stats]
community-lang:  [2-4 phrases the community uses for this topic]

faq:
  - q: "[question]"
    a: "[answer — from article body, not new claims]"

schema-type:     BlogPosting | Article
schema-faq-block: |
  [FAQPage JSON-LD string, ready to insert]
schema-centroid-additions: |
  [mentions + about additions for CENTROID articles]

citation-tier1:  [primary source URLs]
citation-tier2:  [Reddit / HN URLs for community context]
flags:           [non-blocking notes]
```

## Six-Step Research Loop

Run all 6 unless `skip-research: true` (then run steps 1+6 only).

**Step 1 — Claim extraction**
Identify the single most extractable sentence. Token-estimate the draft
(words ÷ 0.75). Is the claim in first 500 tokens? If not: flag (not block).

**Step 2 — Entity scan**
Extract all proper nouns, named systems, concrete statistics. Minimum 3
entities. If fewer: flag — article may be too abstract for citation.

**Step 3 — Category search**
```
[topic] [voice] 2026 site:reddit.com OR site:news.ycombinator.com
[topic] [article-type context] 2026 research
```
Target: 2 tier-2 sources (Reddit / HN) + 1 tier-1 (primary data). Skip
prestige SEO blogs — they are tier-3.

**Step 4 — Competitive scan**
```
"[primary claim keywords]" thought leadership 2026
```
Is the claim already saturated? If yes: sharpen, don't soften. If unique:
note as citation advantage.

**Step 5 — FAQ generation**
Generate 2-3 questions a real person would search that this article answers.
Rules: questions must be answerable from article body, answers must contain
the primary claim, combined FAQ text <1500 tokens, no new claims introduced.

**Step 6 — Schema assignment**
Assign by article-type:
- BIZ → BlogPosting + FAQ
- INFRA → BlogPosting + FAQ + speakable
- CENTROID → Article + mentions + FAQ

## Site-Level Audit

Check and report on:
- `robots.txt` — are all major AI crawlers explicitly allowed? (GPTBot,
  ClaudeBot, PerplexityBot, anthropic-ai, Google-Extended, OAI-SearchBot,
  Meta-ExternalAgent)
- `llms.txt` — present? current? all published articles listed?
- Headers — Content-Type for `text/plain; charset=utf-8` on llms.txt?
- Internal link graph — do articles link to 3+ related pieces?
- Token efficiency — spot-check most recent 3 articles for token estimate

Returns: per-check status + one action item per failure.

## Quick Reference

```yaml
token-rule:  claim in first 500 tokens — always
schema:      BIZ → BlogPosting+FAQ | INFRA → BlogPosting+FAQ+speakable |
             CENTROID → Article+mentions+FAQ
site-files:  robots.txt + llms.txt + Content-Type headers
reddit:      Perplexity cites Reddit 24% — community language = citation surface
claudebot:   up 800% early 2026 — assume crawled, make it extractable
```
