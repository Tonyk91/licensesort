# LicenseSort

Software invoices don't say *"Microsoft 365 E3, annual"*. They say
`MSFT O365 E3 NCE annual commit`, `E3 user subs (Microsoft) renew 36M` or
`Document Cloud Pro - team license 12 mo`. Before anyone can compare what a
company **pays for** with what is **installed**, every line has to be mapped to
one canonical product. LicenseSort does that mapping. It is a small internal tool
for Finance, and it is built to answer one question: **where should
deterministic code decide, and where should a model?**

> **All data is synthetic.** I wrote the 45 invoice lines and the catalog of 26
> products myself, in the style of real reseller invoices. No customer data was used.

## How it decides

```
invoice line ──► rules (regex, catalog) ──one hit──► product  [source: rule]
                       │
                  0 or 2+ hits
                       ▼
                 local model (Qwen2.5-3B via Ollama)
                 output constrained to the catalog ids + UNKNOWN
                 then validated again in code ──► product  [source: model]
                       │
                    UNKNOWN
                       ▼
                 human review queue               [source: review]
```

- **Billing term is always deterministic.** "12M", "P1Y" and "36M" are formats, not
  meaning, so the term comes from regex only.
- **The model can't invent a product.** The answer is constrained to an enum (a fixed
  list of allowed values) of catalog ids, and `llm.parse` checks it again. Anything
  outside the catalog becomes `UNKNOWN`. The two checks are separate on purpose:
  the first depends on the inference server honouring the schema, the second doesn't.
- **Every result records which layer decided it** (`rule` / `model` / `review`), so
  a person can audit the model's work without re-checking the rules' work.
- **One model interface for all providers.** It speaks the OpenAI-compatible chat
  API. The default is a self-hosted model on Ollama. Pointing `LS_LLM_BASE_URL` /
  `LS_LLM_MODEL` / `LS_LLM_API_KEY` at a commercial endpoint swaps the model without
  touching code.

## Results

`python eval.py` against 45 hand-labelled lines: 39 that belong to a catalog product, written to
include the traps that matter in licensing (Office 365 E3 ≠ Microsoft 365 E3,
AutoCAD ≠ AutoCAD LT, Acrobat Pro ≠ Standard), plus 6 lines that must *not* be
matched (freight, services, hardware, an add-on, two products outside the catalog).
Qwen2.5-3B (Q4) on a MacBook Air M2 with 8 GB RAM, temperature 0. Two runs gave identical results.

| setup | correct | **wrong** | to review | term correct | s / line |
|---|---|---|---|---|---|
| rules only | 36/45 | **1** | 8 | 43/45 | ~0 |
| model only (qwen2.5:3b) | 44/45 | **1** | 0 | 43/45 | 0.50 |
| rules + model | 43/45 | **2** | 0 | 43/45 | 0.14 |

`wrong` is the column that counts. A line sent to review costs a person a minute.
A line mapped to the wrong product becomes a license count that is wrong, and
nobody knows it.

### What this shows, including what I didn't expect

**My hypothesis was "rules first is safer", and on this set it didn't hold.**
The model alone made fewer mistakes than rules + model. Both setups get #31 wrong
(`Document Cloud Pro` → Creative Cloud instead of Acrobat Pro). The difference is #44:

```
"Microsoft 365 E5 Security add-on annual"
  rule  -> M365-E5   (wrong: it's an add-on, not the E5 suite)
  model -> UNKNOWN   (right)
```

The rule's mistake comes with no doubt attached. The pattern `microsoft 365 e5`
matches, so the rule answers, and the model never sees the line. The lesson isn't
"drop the rules". **A rule is only as safe as it is narrow.** A rule that recognizes
a product name also needs to know what *isn't* that product: add-ons, upgrades, the
"for Education" SKUs. The fix is negative patterns (`add-on`, `addon`, `upgrade`
→ no rule hit). I did **not** apply that fix and re-run, because the rules were
frozen before the first eval run. Tuning them now against the same 45 lines would
just make the table flatter me.

**What the rules still earn:** 36 of 45 lines decided in microseconds, with no model
call, the same answer every time, and a reason you can read. Rules + model is 3.6×
faster than model alone (0.14 vs 0.50 s/line). At invoice volume, on a laptop-class
box, that is the difference that matters. The 6 must-reject lines were all
rejected by the model, and none of the 39 real products was sent to review.

**Term parsing: 43/45.** Both misses are formats that weren't in the regex
(`12 month` singular, `per user/month`). They come out as `unknown`, not as a wrong
term, which is the failure you want.

### What this eval can't tell you

- **45 lines is small.** One line is 2.2 percentage points. Treat the table as
  direction, not as a benchmark.
- **The same person wrote the rules, the lines and the labels**, in one evening.
  That biases the rules upward. A real test set comes from real invoices labelled by
  someone who didn't write the rules.
- **A laptop isn't production inference.** The latency is from an M2 Air with Metal.
  On a CPU-only server it would be slower, and on a GPU box much faster.
- **I didn't run a commercial model.** The interface supports it, but there's no
  row for it in the table because I didn't measure one.

## Run it

```bash
brew install ollama && ollama serve &      # or: docker compose up (Linux)
ollama pull qwen2.5:3b
python -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest -q              # 10 unit tests, no model needed
.venv/bin/python eval.py                   # all three setups
.venv/bin/python eval.py --no-llm          # rules only, what CI runs
```

CI runs the tests and the rules-only eval on every push, and fails if the rules
ever produce more than the one known wrong answer.

On a Mac, run Ollama natively. Docker Desktop can't reach the Apple GPU, so the same
model inside Docker would run on CPU only. `docker-compose.yml` is for Linux hosts.

## Next steps (not built)

1. **Reconciliation:** paid vs installed. Join the mapped invoice lines with
   installation data (Devices + Softwares) and report "paying for 200, 140 installed".
   Matching names is the model's job; the counting and the subtraction are plain
   code. I'd build the adapter against a mock, since the inventory API is per tenant
   and its schema isn't public.
2. **Negative patterns** for add-ons/upgrades, measured on a *new* set of lines.
3. **A commercial-model row** in the table, through the same interface.

## Layout

```
licensesort/catalog.py   26 products + their regex patterns
licensesort/rules.py     normalize, product match (exactly one hit), term match
licensesort/llm.py       OpenAI-compatible client, enum-constrained, validated
licensesort/pipeline.py  rules -> model -> review, with source on every result
eval.py                  three setups, wrong/review/correct, s/line
data/invoice_lines.csv   45 hand-labelled lines
```
