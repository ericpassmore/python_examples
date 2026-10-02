# Establish Goals

## Status

- Task name: real-returns-bootstrap
- Iteration: v0
- State: locked

## Request

- Create a `calc_real_returns.py` program modeled on the existing CLAT bootstrap
  calculator. It must use the same historical CSV data source to calculate real
  portfolio returns with block bootstrap paths. Portfolio allocations are supplied
  as percentages, for example: `calc_real_returns.py --sp500 72 --corp-bonds 15
  --tbils 3 --gold 10`.

## Blocking ambiguity

- None. "SLAT" is treated as a reference to the existing
  `clat_gold_bootstrap.py` calculator, the only matching implementation in this
  repository.

## Assumptions

- Default to the same external CSV used by the CLAT calculator,
  `/Users/eric/Downloads/Block Finance 10 Year - Data.csv`, while allowing an
  explicit override for portability.
- Use the data source's existing real-return columns for S&P 500, 3-month
  Treasury bills, Baa corporate bonds, and gold.
- Replicate the CLAT calculator's exhaustive paired, rolling 10-year block
  bootstrap from 1970: all ordered pairs form 20-year paths.
- Treat supplied allocations as whole percentages that must total 100; accept
  `--tbils` from the request and intuitive Treasury-bill aliases.

## Goals

1. Add a standalone `calc_real_returns.py` CLI that computes weighted annual
   real portfolio returns from the shared historical CSV and validates portfolio
   allocation inputs.
2. Produce real-return block-bootstrap path and summary results using the same
   10-year paired-block method as the CLAT calculator.
3. Add focused automated tests for CSV parsing, percentage-weight validation,
   and deterministic bootstrap outputs.

## Non-goals

- Change the existing CLAT calculator or its output files.
- Fetch, package, or alter the external historical data source.
- Add third-party runtime dependencies or randomized simulation.

## Success criteria

- [G1] The documented allocation example runs with the default data source and
  emits real-return bootstrap results.
- [G2] Invalid allocations are rejected unless the supplied percentages total
  exactly 100 (within normal floating-point tolerance).
- [G3] The output reports the configured allocation, loaded historical range,
  path count, and real-return / ending-value distribution metrics.
- [G4] Focused tests pass without requiring the external data file.

## Next action

- Hand off to implement
