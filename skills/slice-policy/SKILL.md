---
name: slice-policy
description: Define implementation slices as the smallest coherent verifiable result, preventing token-wasting micro-slices and unnecessary human approval stops. Use for every implementation task, when planning work units, when deciding whether to continue or stop, and when checker agents judge whether a slice advanced the stop condition.
---

# Slice Policy

Use this skill for every implementation task.

## Principle

A slice is the smallest verifiable result, not the smallest possible code edit.

The goal is to reduce risk without multiplying fixed overhead. A good slice advances the stop condition and can be verified as a coherent behavior.

## Good Slice

A good slice usually includes:

- one user-visible or system-visible behavior
- the minimal code needed for that behavior
- tests or equivalent verification for that behavior
- a compact record of what changed and what evidence proves it

Examples:

- Add a CLI command with its basic parser, core behavior, tests, and one smoke run.
- Add one API endpoint with request validation, handler, route registration, and API tests.
- Add one feature-flagged UI path with the flag, component change, and browser smoke check.
- Fix one bug with a reproduction test, the fix, and regression verification.

## Bad Slice

Do not create slices that only:

- read files
- write a plan
- rename a variable
- add one helper that cannot be verified independently
- run one command without changing task state
- stop because the phase changed from PLAN to BUILD or BUILD to VERIFY

These are steps, not slices. Record them inside the current slice instead of turning them into separate loops.

## Slice Size Bounds

Prefer one slice per coherent behavior.

Suggested bounds:

- Files changed: usually 1-6 related files
- Verification: one narrow test/check plus broader checks when justified
- Run artifacts: one compact summary, not a transcript
- Human approval: only when scope, authority, safety, or product judgment changes

If a slice touches more than 8 files, split it by behavior, risk, or contract boundary.

If a slice touches only one line and cannot be independently verified, fold it into the nearest meaningful slice.

## Stop Rules

Continue within the current slice when:

- the next step is mechanically implied
- verification failed but the fix is inside the approved scope
- the plan changed only in implementation detail
- more files are needed to complete the same behavior

Stop and ask when:

- the user/product decision changes
- the implementation crosses a safety boundary
- the next step is irreversible or production-impacting
- credentials or authority are missing
- the slice has grown beyond its behavioral boundary
- the token or iteration budget is exhausted

## Checker Questions

The checker should evaluate:

1. Did this slice produce a coherent behavior?
2. Did it advance the stop condition?
3. Is there evidence, not just explanation?
4. Is the next step still within the same slice, or should a new slice start?
5. Did the agent create needless micro-slices?
