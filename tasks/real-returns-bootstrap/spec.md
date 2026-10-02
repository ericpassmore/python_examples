# Real returns bootstrap calculator

## Goal reference

- `goals/real-returns-bootstrap/goals.v0.md`

## Scope

### In scope

- Add `calc_real_returns.py` and focused unit tests.
- Reuse the historical CSV's existing real-return columns for the four requested
  portfolio components.
- Match the CLAT calculator's 1970-onward exhaustive paired 10-year-block
  bootstrap behavior.

### Out of scope

- Do not modify `clat_gold_bootstrap.py`, generated CLAT results, or the
  external source CSV.
- Do not add non-stdlib runtime dependencies or randomized simulation.

## Approach

- Keep parsing and rolling-block logic standalone so this tool can run without
  changing the CLAT calculator. Default all portfolio weights only when none
  are supplied; otherwise require the supplied set to total 100%.

## Verification commands

- Lint: `python3 -m compileall -q calc_real_returns.py`
- Build: `not configured`
- Tests: `python3 -m pytest -q`

## Delivery

- Delivered: `calc_real_returns.py` accepts percentage allocation flags,
  including `--tbils` and `--tbills`; defaults to the shared historical CSV at
  `/Users/eric/Documents/FinanceData/Block Finance 10 Year - Data.csv`; writes
  per-path and annual real-return data plus a JSON distribution summary. The
  CLAT example and generated result provenance use that same path. Focused tests
  cover parsing, allocation validation, gap-safe blocks, ordered block-pair
  enumeration, and generated summaries.
- Exceptions: None
- Deferred work: None
- Dirty-worktree decision: continue; the pre-existing untracked `AGENTS.md`
  and generated Python cache directories do not overlap this task. Goal and
  task artifacts belong to this workflow.

## Quality gate results

- Lint: passed (`python3 -m compileall -q calc_real_returns.py`)
- Build: not configured
- Tests: passed (`python3 -m pytest -q`; 11 passed)
- Code review: deferred to the landing workflow
- Clean merge: deferred to the landing workflow
