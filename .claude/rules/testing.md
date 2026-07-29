---
paths:
  - "**/*.test.*"
  - "**/*.spec.*"
  - "tests/**/*"
  - "test/**/*"
  - "**/__tests__/**/*"
---

# Testing Rules

- Write tests for non-trivial logic (branching, edge cases, parsing, calculation, state). Skip trivial glue.
- Use this repo's existing test framework and file conventions — match the surrounding tests.
- Cover the main path plus edge cases: empty input, boundaries, error conditions.
- Tests must be deterministic and isolated — no reliance on external services in unit tests; mock or use fixtures.
- Name tests for the behavior they assert, not the function name alone.
- Never claim tests pass without running them and seeing the result. If they can't run, say so and give the command.

<!-- Replace the example commands below with this repo's real ones. -->
- Run all: `<TEST_COMMAND>`
- Run one: `<SINGLE_TEST_COMMAND>`
