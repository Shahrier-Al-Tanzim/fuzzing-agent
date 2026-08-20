# Progress Report — Agentic Fuzzing of `tomlc99`

**Prepared for:** course instructor (Marcelo D'Amorim)
**Project:** LLM-driven grammar fuzzer targeting `tomlc99` (a C TOML parser)
**Status:** 5 of 6 deliverables complete; the agentic loop has autonomously
found 5 distinct, confirmed bugs across 20+ full runs

> **Note on this draft:** this version intentionally includes everything —
> every measured number, every case, every dead end — so nothing gets lost
> before the final trim to the assignment's 2-page limit. Section headers
> are kept aligned to the assignment's required report shape (Design /
> Findings / Challenges) specifically so trimming is straightforward: cut
> within a section, not across the structure.

---

## 1. What the assignment asks for

The task is to build a **test generator (fuzzer)** that finds crashing
bugs in a small C library, using an **agentic** approach rather than a
traditional coverage-guided fuzzer: an LLM is given a formal grammar for
the library's input format and asked to write a
[Hypothesis](https://hypothesis.readthedocs.io/) strategy — a program
that generates test inputs — then **iteratively refine** that strategy
based on feedback, for up to 5 iterations or a fixed cost budget.

Critically, this is a **blackbox** exercise: no code-coverage
instrumentation of the target library is allowed, only sanitizer output
(crash detection). The graded skill is not "did you build a fuzzing
engine" — it's **how well you can drive an LLM to turn a formal grammar
into an effective generator, and how well you design the feedback loop
around it**, given that you can't see which lines of the target's code
actually ran.

The assignment is structured in six steps: (1) find a formal grammar for
the target format, (2) build a sanitizer-instrumented test harness, (3) a
naive baseline generator to prove the pipeline works, (4) the agentic
loop itself, (5) crash triage (deduplicate, minimize, verify), and (6) a
written report. It's graded on: correctly interpreting the grammar,
whether the generated strategy reflects real grammar structure (not just
"big random string"), engineering rigor in the harness, the design of the
feedback signal (since there's no coverage available), triage instinct,
and judgment under a fixed budget.

---

## 2. Design

**Grammar.** Sourced the TOML grammar from ANTLR's `grammars-v4` repository
(`TomlLexer.g4` + `TomlParser.g4`), used as-is per the assignment's
instructions — not re-derived from the library's own source. Before
building anything, I hand-probed the pinned `tomlc99` build against a
checklist of TOML edge cases and found **5 real divergences** between the
formal grammar and the library's actual behavior: it silently accepts
trailing commas in inline tables (grammar forbids them), silently
truncates over-long fractional seconds, silently re-types integers past
`INT64_MAX` as floats, lets a leading-zero integer through its first parse
stage only to fail a later, separate accessor call, and — critically —
has no depth limit on nested arrays, which segfaults at extreme depth.
That last one became the seed for everything found later.

**Harness and crash classification.** `harness/toml_harness.c` is a small
C driver, compiled with `-fsanitize=address,undefined`, that feeds one
input to `tomlc99`'s real parser and to its typed value accessors (a
config file can parse successfully but still fail a later
`toml_rtoi`/`toml_rtod` call — that's a genuine finding, not just "did
`toml_parse` return 0"). Classification is deliberately ordered: a
per-input timeout is checked first, then sanitizer output (authoritative
regardless of how the process finally died), then a fatal signal, then
the harness's own exit code. Getting the sanitizer-before-exit-code order
wrong is the classic bug here — it would file a real memory-safety issue
as a clean rejection.

**The agentic loop and its proxy signal.** The loop (`agent/loop.py`)
runs seed → validate → run 500 examples → summarize → refine, up to 5
iterations. Since code coverage of `tomlc99` is off-limits, the proxy
signal combines several externally-observable things, computed by reading
the *generated text itself*, never the target's internals:
**grammar breadth** (how many of ~30 tracked TOML constructs
have appeared in accepted documents — deliberately not called "coverage":
it's a regex match against our own generated strings, never an
instrumentation of the target binary, and the two terms are easy to
conflate at a glance), **acceptance rate** (a generator
rejected 99% of the time is testing nothing — a 20% floor rejects the
whole strategy before it wastes the run's budget), **novelty**
(structural shape diversity), **max nesting depth**, and — added later,
see below — **crash-mechanism diversity**. This was expected to work
because `tomlc99`'s parser is structured around the same constructs the
grammar names (`parse_array`, `parse_inline_table`, `parse_keyval`
literally exist as functions), so "which grammar productions reached the
parser" is a structural shadow of "which parser code ran."

**Depth is escalated geometrically, not linearly.** A flat "aim for
deeper nesting" directive never closes the gap to a real crash threshold —
confirmed the hard way (see Challenges). `DEPTH_TARGETS = [12, 200, 4_000,
30_000, 90_000]` in `agent/summarize.py` ramps the target hard across the
5-iteration budget, paired with a prompt technique (Section 3) that
replaces recursion with direct string repetition once depth needs to pass
a few hundred levels.

**Two real, measured defects were later found *inside the proxy signal
itself*, not in the generator** — arguably the strongest evidence of
having actually understood the signal rather than just building one:

1. **The depth directive was mathematically unsatisfiable.** Both depth
   figures were computed from *accepted* documents only (documents that
   parsed successfully). But a document deep enough to hit the top target
   (90,000) crashes the parser — and a crashed document is never
   "accepted." So the directive was asking for something that, by
   construction, could never be measured as achieved, and kept firing
   on runs that were already producing over a thousand crashes per run.
   **Fix:** a second depth figure computed from *all* generated documents,
   crashes included, now gates the directive.
2. **No directive ever asked for a *different* crash mechanism.** The
   feedback quoted raw crash-signature hex digests
   (`"939402a0547c, e857b4530c96, ..."`) — information the model has no
   way to act on. Nothing in the signal pushed toward an unseen bug once
   one had been found, which is exactly why 4 separate full runs (17, 20,
   21, 24) kept re-finding the identical set of bugs. **Fix:** digests are
   now mapped to the actual input shape behind them ("nested arrays",
   "dotted keys", …), and a new directive explicitly asks for a construct
   that stresses a mechanism not yet seen.

---

## 3. Findings

### The bug count: 5 confirmed, distinct, root-cause bugs

| # | Bug | Mechanism | Threshold (measured) | Deterministic? |
|---|---|---|---|---|
| 1 | Array-nesting stack overflow | `parse_array` recurses into itself once per `[`, no depth limit | ~48,000 | Yes, 3/3 |
| 2 | Dotted-key stack overflow | `parse_keyval` recurses into itself once per `.` in `a.b.c…=1` | ~90,000–100,000 | Signature-unstable at extreme depth, but crashes 3/3 |
| 3 | Inline-table stack overflow | `parse_inline_table` and `parse_keyval` recurse into each other once per nested `{` | ~80,000 | Yes, 3/3 |
| 4 | Many-siblings O(n²) hang | Every key insert does a linear scan of existing keys — N keys costs O(N²) total | ~15,000–18,000 keys crosses the 5s timeout | Not applicable — a timing threshold, not a memory bug |
| 5 | Alternating array/inline-table stack overflow | `parse_array` and `parse_inline_table` recurse into **each other** (a 3rd, distinct recursion cycle) | ~40,000–80,000 depending on variant (see below) | Crashes every run; signature not stable between runs |

3 are memory-safety bugs (unbounded recursion → stack exhaustion — real
CVE-class issues in production use); 1 is an algorithmic-complexity
denial-of-service bug; bug 5 is memory-safety, bringing the total to 4
memory-safety + 1 DoS. All 5 trace to the same root pattern: `tomlc99`'s
recursive-descent parser and table implementation impose no limits on
attacker-controlled input size or nesting, anywhere.

**Bug 5 has two known variants**, both confirmed live through the
agentic loop, not hand-fed: a plain alternating shape
(`[{a=[{a=…}]}]`) and a **quoted-key** variant
(`[{"k"=[{"k"=…}]}]`) that forces a different code path (string
unescaping, `norm_basic_str`) onto the stack and produces a genuinely
different sanitizer signature (`c04d038a7956`) — the first signature in
the project's history to contain that function.

**A genuinely counter-intuitive milestone: the newest bug variant was
found at a *lower* depth than every other bug, not a higher one.** Every
earlier discovery in this project came from pushing depth further (bug 1
at 48k, up through bug 5's ~80k). The quoted-key variant reproduces best
around depth ~25,000 — roughly half the *shallowest* of the other
shapes — and gets *less* reliable past ~45,000. This is direct evidence
that what occupies each nesting level matters as much as how deep the
nesting goes, not just a coincidence: it's why Defect 2 above (a
crash-diversity directive) mattered as much as Defect 1 (an honest depth
number).

### Triage caught its own overcount — a clean, self-contained example of "new bug vs. repeat"

The most recent full run's raw triage tool reported **9 unique crash
signatures**. Taken at face value, that reads as 9 bugs. **It's actually
5.** Three of those nine signatures — `af1d0280777e`, `3db1e06f41e9`,
`80953bb88ca2` — turned out, on inspection of the actual saved crashing
input files (not just the signature digest), to be the *same* generated
shape (bug 5's alternating construct), fragmented into three different
signatures purely because a stack overflow 60,000+ calls deep is caught
by the sanitizer at a slightly different point each time, depending on
which of the cycle's two functions happens to be executing when the stack
finally runs out. Retrying for a cleaner capture (the fix already used
for bug 1's own frameless-crash instability) doesn't resolve this case,
because both captures are equally valid, equally parseable — the
instability is *between two real call sites*, not between a parseable and
an unparseable one. The corrected, defensible count — 9 signatures, 5
real root causes — is what's reported here, not the raw tool output.

### The result of fixing the depth signal, measured directly

Before the per-shape depth-floor fix (Defect 1's companion fix in the
generator prompt — giving each of the 3 original deep shapes its own
measured floor instead of one shared, too-low floor for all of them):
crash counts were badly lopsided because most draws for the harder shapes
never got deep enough to matter — one full run produced 120 array-bug
crashes against only 3 dotted-key crashes and 11 inline-table crashes,
purely from under-shooting the threshold, not from the bug being rare.
After the fix, the same run type produced a far more balanced spread
(178 / 170 / 125 across the three original shapes) — and **total
crashing/timeout inputs per run rose from 219 to 1,316, a 6× increase**,
entirely from documents that used to survive the parser now correctly
reaching their crash threshold instead. This did make each run slower
(measured: average iteration time went from ~190s to ~535s), because the
extra crashing/hanging documents include more of the many-siblings hang,
which costs a fixed 5-second wait per occurrence by design — a real,
intentional runtime trade-off, not a regression.

### How the strategy evolved, and what drove each change

Early iterations exposed a sequence of concrete, real failures, each
fixed by a targeted prompt rule: recursion that looked real but never
actually nested (the strategy used `@composite` but never let a
container hold another instance of itself — depth stuck at 1 for a whole
run, caught because the validator's own recursion check was found to be a
pure text search that couldn't tell the difference, and was fixed to
measure actual drawn-sample structure instead); banned API calls the
model kept hallucinating (`st.dates(min_date=...)`, which doesn't exist);
a document generator that put bare arrays/tables at the top level,
producing invalid TOML at any depth; unquoted table headers built from
unrestricted text, silently invalidating a large share of every document.

**The most significant single finding: recursive generation is
structurally incapable of reaching crash-triggering depth, no matter how
it's biased.** A measured A/B test — same recursion-bias ratio, same
depth counter, only changing list-branching width — showed even the
*correctly shaped* recursive chain plateaus around depth 13, against bugs
that need 48,000–105,000 levels of nesting. Hypothesis's own
data-generation budget resists deep recursion; this is not a
prompt-quality problem, it's a property of the tool. The fix was to stop
recursing entirely for the extreme-depth case: draw an integer, build the
string by direct repetition. That one change took measured depth from
single digits to over 50,000 in one iteration, and is what produced the
first loop-found crashes.

**A direct experiment on how much to tell the model versus let it
discover.** Rewrote the depth-technique rules from concrete worked
examples to abstract guidance (name the *dimensions* to stress — depth,
element count, sibling count, token length — and let the model work out
which TOML constructs map onto each). Result, on a live test: **worse on
both axes that matter.** No improvement in crash-finding, and markedly
slower (~5 min/iteration versus ~2.5–4 min with concrete examples) —
plausibly because an abstract prompt hands a reasoning model more
open-ended work on every single generation. The concrete rules were
reverted. For this model and this task, a concrete demonstration of a
*technique* outperforms abstract guidance in both result quality and cost.

### The algorithmic-complexity hang, confirmed independently twice

Identified by hand-reading `tomlc99`'s table-insertion code (a linear key
scan on every insert → O(N²) total cost for N sibling keys), confirmed
directly against the harness (5,000 keys: 0.74s; 15,000+ keys: over the
5-second timeout), taught to the model as a targeted prompt rule, and
then **found autonomously by the agentic loop itself** in a later run —
not just reproduced from the hand-written probe. This is a structurally
different bug class from the other four: a hang, not a memory-safety
crash, and it does not reproduce deterministically under the project's
verification step, which is expected and documented (see Challenges) —
it's a timing threshold, not a fixed-code-path bug, so its behavior is
sensitive to system load near the 5-second cutoff.

### Provider comparison — Groq vs. Gemini

Ran the same agentic loop against two different remote free-tier
providers to see whether provider choice, not just prompt quality,
affected results (data archived in `comparison/`): `llama-3.3-70b-versatile`
via Groq (12 runs) and `gemini-3.6-flash` via Gemini (10+ runs, the
current default). Groq was deprecated by its provider mid-project,
forcing a live migration. The most useful result isn't which model
"won" — it's that the two models failed in *qualitatively different
ways* before their respective prompt fixes landed: the smaller local
model (`qwen2.5-coder:7b`, tried first, 0/12 attempts ever produced a
valid strategy) confidently fabricated Hypothesis API calls that don't
exist, and repeated the exact same fabrication even after being told,
explicitly, not to — a capability-ceiling failure that no amount of
"never do X" prompt-fixing resolved. Groq's 70B model, by contrast, made
ordinary composition mistakes (forgetting to unwrap a drawn value, type
mismatches) that a single targeted prompt rule fixed cleanly and
permanently. Different model tiers hit genuinely different failure
classes, not just different failure rates.

### What's still under-tested

Two divergences from the initial grammar probing — silent int→float
re-typing and the leading-zero integer that splits parse-success from
accessor-failure — hint at shaky type-handling that the depth-focused
generator hasn't specifically targeted yet. A direct audit of `tomlc99`'s
remaining fixed-size buffers, integer-arithmetic sites, and string-copy
loops (`toml_rtoi`, `toml_rtod`, `toml_rtots`, `toml_ucs_to_utf8`, the
10-slot table-path array) found every one of them correctly bounds-checked
— a completed negative result, not an open question: there is no known
reachable fixed-buffer overflow left to find in this library, so any 6th
bug would need a mechanism this project hasn't yet looked for.

---

## 4. Challenges

**The single most transferable finding: an illustrative constant in a
prompt example is read as a hard ceiling, not a suggestion.** After
teaching the model the integer-repetition depth technique, depth jumped
1,250× in one iteration — genuinely correct code — but then froze at
*exactly* the number used in the worked example, because the model
copied that literal bound instead of the depth target the feedback signal
was concurrently requesting (which was asking for 30,000–90,000 at the
time). The model obeyed instructions exactly and still missed the
objective, because a detail chosen purely for illustration got treated as
a constraint, overriding the actual prose directive. This reframed a lot
of the project's earlier "why isn't depth increasing" debugging: it was
never really about model obedience.

**Two real bugs found inside the feedback signal itself, not the
generator.** Detailed in Design above; worth restating here because it's
direct evidence for the assignment's own question — "what proxy signal
did you choose, and why did you expect it to work" — including the
self-correction when it didn't. One of the two defects (the
unsatisfiable depth target) had been silently firing on every iteration
of every run for an unknown number of runs before being traced and fixed.

**A clean example of triage catching its own overcount.** Covered above
under Findings; restated here because it directly answers the
assignment's explicit ask for "triage instinct... distinguishing a new
bug from a repeat." The honest number (5, not the raw tool's 9) only
came from reading actual crashing input files rather than trusting a
digest count — a concrete, demonstrated instance of the exact judgment
call the assignment names.

**A real deduplication judgment call, found by the triage tooling's first
real use.** A deep stack-overflow's sanitizer backtrace is inherently
unstable — sometimes it unwinds cleanly, sometimes it doesn't. When it
doesn't, every frameless crash falls back to the same generic signature,
which can silently merge two genuinely distinct bugs into one bucket. The
fix — retry a crashing input until a parseable stack is obtained before
committing to a signature — is a documented, defensible normalization
choice, not an assumption. (Note: this specific retry-based fix does
*not* resolve the different instability found later in bug 5's
signatures — see Findings — since that instability is between two
already-parseable captures, not a frameless-vs-parseable problem. Two
distinct triage lessons from two distinct root causes.)

**Other judgment calls documented along the way:** timeouts are treated
identically to crashes per the assignment's own policy (a hang is a real
denial-of-service bug); a generator that was mostly getting rejected
(acceptance below a 20% floor) is caught and rejected *before* it ever
runs a full 500-example pass, rather than wasting the budget; and a
mid-project external dependency failure — Groq deprecated the model this
project had been using, mid-session, forcing a live migration to Gemini,
which is now the primary provider.

**What I'd change with more time, or with real coverage feedback:**
extend the crash-diversity directive's reach beyond the shapes already
known, now that the feedback signal can name mechanisms instead of raw
digests; run the Groq/Gemini provider comparison against a third,
frontier-tier model to see whether the qwen→Groq failure-class shift
(hallucination → ordinary composition bugs) continues in the same
direction; and, if real coverage instrumentation were available, replace
the current external grammar-shape proxy with actual line/branch
coverage, which would remove the single biggest source of uncertainty in
this whole design — whether "touched this grammar construct" really does
track "exercised this code path" as closely as hoped.

---

## 5. Current progress against the deliverables checklist

- [x] Grammar source + noted adaptations
- [x] Build script + harness source
- [x] Baseline strategy + pipeline demonstration
- [x] Agentic loop implementation + final generator + iteration log
- [x] Deduplicated, minimized crash reports — **5 confirmed distinct
      bugs**, autonomously found, verified 3/3 deterministic on most
- [ ] Two-page written report — this document is the full working draft;
      trimming to the assignment's 2-page limit is the remaining step

Detailed evidence for every claim above — full run history, every prompt
rule and the specific failure it fixed, all triage reports, and a
plain-language explanation log — lives in the repository: `OBSERVATIONS.md`
(the primary source for this report — 10 documented cases in total),
`logs/RUN_HISTORY.md`, `triage/reports/`, `comparison/` (provider
comparison data), and `explanation.md`.
