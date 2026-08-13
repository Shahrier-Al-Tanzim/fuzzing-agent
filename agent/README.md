# Module 4 — Agentic Loop: Grammar → Generator

Turns the ANTLR grammar into a validated Hypothesis strategy, using an LLM
behind a provider-agnostic interface. Two providers are wired up today:
a local 7B model (`qwen2.5-coder:7b` via Ollama) and a remote 70B model
(`llama-3.3-70b-versatile` via Groq's free tier). See
[`../OBSERVATIONS.md`](../OBSERVATIONS.md) for why both exist — this module
started with only Ollama, and Groq was added mid-module after documented,
repeated reliability problems with the 7B model (Case 1).

For a plain-language, no-jargon walkthrough of what this whole folder does
and why, read [`../HOW_MODULE_4_WORKS.md`](../HOW_MODULE_4_WORKS.md) first.
This README is the technical reference; that file is the explainer.

## Contents

| File | Purpose |
|---|---|
| `ollama_client.py` | HTTP client for local Ollama; finds it on the Windows host from WSL |
| `groq_client.py` | HTTP client for Groq's OpenAI-compatible API; same interface as the Ollama client |
| `grammar_context.py` | Builds the grammar section of the prompt from Module 1's artifacts |
| `prompts.py` | System prompt, output contract, seed template |
| `extract.py` | Pulls Python out of a markdown reply |
| `validator.py` | The six gates a candidate strategy must pass |
| `strategy_store.py` | Versioned strategies on disk, including rejected ones and an accepted-run archive |
| `seed.py` | Driver script: generate → validate → retry with feedback |
| `strategies/` | Generated output (gitignored except as noted below) |
| `state/prompts/` | Full prompt/reply transcript for every single attempt, ever |

## Two providers, one interface

Both clients expose the same shape — `generate(prompt, system="") -> LLMResponse`
and `usage_summary() -> dict` — so `seed.py` can swap between them with a
single `if`, and nothing in `validator.py`, `extract.py`, or `prompts.py`
needs to know which one is in use.

```
python -m agent.seed --iteration 0                  # local Ollama (default)
python -m agent.seed --iteration 0 --provider groq   # remote Groq
```

Using Groq requires a key in the environment first:
```
source .env       # loads GROQ_API_KEY into this shell
```
`.env` is gitignored — never commit it. `groq_client.py` also automatically
retries on HTTP 429 (rate limit), reading how long to wait from Groq's own
response rather than guessing, and sets a real `User-Agent` header (Groq's
API sits behind Cloudflare, which blocks the Python default one).

## The six validation gates

1. **extract** — a fenced Python block exists in the reply
2. **syntax** — `ast.parse` succeeds
3. **imports** — only `hypothesis`/`hypothesis.strategies`; checked statically, before execution
4. **exec/export** — the module runs and defines `toml_strategy: SearchStrategy`
5. **draw** — N `.example()` calls return `str` without raising
6. **acceptance** — the real `tomlc99` harness accepts at least `loop.acceptance_rate_floor` of generated documents

Gates run cheapest-first and stop at the first failure — a `[draw]` failure
means gates 1-4 passed and 5 is where it broke; gate 6 never ran that
attempt. Every failure message is written to be pasted directly into the
next attempt's prompt, quoting the exact error back to the model.

## Key design decisions

- **Named export contract (`toml_strategy`).** Without one fixed name,
  validation cannot distinguish a strategy from prose.
- **Validator errors are quoted verbatim into the retry prompt.** That
  feedback loop is what makes a small model usable at all.
- **Rejected candidates are saved, not discarded.** They're the evidence
  for the report's "what was harder than expected" section. Known gap:
  rejected saves currently don't record *which* gate they failed at
  anywhere on disk — only accepted saves get a `.json` sidecar with that
  detail. That information only exists in terminal output at run time
  unless you capture it yourself.
- **`base_url: auto` for Ollama.** It runs on Windows, this runs in WSL,
  and the gateway IP changes across reboots, so it's discovered at run
  time rather than hardcoded.
- **`exec` is guarded by an AST import blocklist, not a sandbox.** Accepted
  risk: the model-written code still runs locally with no OS-level
  isolation. Documented as a judgment call, not a claimed guarantee.
- **A successful save is archived automatically, never overwritten.**
  `agent/strategies/iter_00_strategy.py` is always the single, predictable
  "current state of this iteration" — Module 5 depends on finding it at
  exactly that path, so it's always overwritten by the latest pass, on
  purpose. But every time a save is accepted, a numbered copy also lands
  in `agent/strategies/accepted/` (`iter_00_strategy_1.py`, `_2.py`, ...),
  so re-running the seed script to test further never destroys evidence of
  an earlier pass.
- **Hypothesis's `NonInteractiveExampleWarning` is deliberately silenced**
  in `validator.py`. Gates 5 and 6 call `.example()` outside a `@given`
  test on purpose — that's the whole point of validation — so Hypothesis's
  warning about that usage pattern is expected noise, not a real signal.

## Known gap: config.yaml is missing keys this module reads

`agent/seed.py` and `agent/validator.py` read `llm.max_attempts`,
`llm.validation_samples`, and `llm.validation_probe_examples` from config,
but **`config.yaml` does not currently define any of them** — every run so
far has been silently using the Python-level fallback defaults
(`max_attempts=4`, `validation_samples=25`, `validation_probe_examples=40`).
This works, but it violates the project's own stated principle
("Central configuration. Every module reads this; nothing hardcodes
these.") — these three values, plus a `provider`/`groq_model` pair for
picking a default remote model without a CLI flag, should be added to
`config.yaml` explicitly. Not yet done.

## Run

```bash
source .venv/bin/activate
python -m agent.seed --iteration 0                    # Ollama, local
source .env && python -m agent.seed --iteration 0 --provider groq   # Groq, remote
python -m agent.seed --iteration 0 --no-probe          # skip gate 6 (faster, weaker)
```

Success looks like a final line reading:
```
saved: agent/strategies/iter_00_strategy.py
```
(No `_rejected` in that filename — that's the only line that means the run
actually produced a working generator.)
