# Goals Extract
- Task name: real-returns-bootstrap
- Iteration: v0
- State: locked

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

