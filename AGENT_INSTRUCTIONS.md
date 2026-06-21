# Repository AI-First Agent Instructions

This is the repository-level operating contract for AI-first development.

It is client-agnostic. Follow it whether the active client is an IDE, CLI, web agent, local runtime, or multi-agent harness.

## Operating Mode

Once intake is complete and the task is safe to start, continue working through discovery, planning, implementation, verification, review, and recording without waiting for the human between routine phases.

Stop only when:

- human judgment is required
- authority or credentials are missing
- requirements are unsafe or materially ambiguous
- the next action is irreversible or production-impacting
- the configured token or iteration budget is exhausted
- verification reveals a larger repair outside the approved task

Progress updates are useful, but they are not approval gates.

## State

Use `state/` as durable memory:

- `state/tasks/<task-id>.md`: human-readable task spec
- `state/tasks/<task-id>.json`: machine-readable loop state
- `state/token-usage.jsonl`: append-only model usage ledger
- `state/known-flakes.txt`: known flaky checks or fingerprints

Do not rely on chat memory for task status.

## Context Economy

- Read the smallest useful slice of the repository.
- Do not reload full instruction files, README files, run histories, or skill files unless they are directly needed.
- Write discovery once, then read the cached summary plus the current diff.
- Prefer file lists and line-targeted reads over dumping whole directories.
- Use role-specific context. An explorer should not load implementation-only material; a verifier should not load brainstorming notes.

## Slice Policy

- A slice is the smallest verifiable result, not the smallest possible code edit.
- Do not stop after read-only discovery, planning, a tiny helper, or a phase transition unless a real blocker exists.
- A slice should usually include a coherent behavior, the minimal implementation, verification evidence, and a compact record.
- Fold tiny mechanical edits into the nearest meaningful slice.
- Split only when behavior, risk, contract boundary, or reviewability requires it.

## Safety

- Do not push directly to protected branches unless explicitly asked.
- Do not run destructive commands such as hard reset, mass delete, force push, destructive database operations, or production deploys without explicit approval.
- Do not commit secrets, `.env` files, local credentials, private tokens, or generated private artifacts.
- Treat existing working-tree changes as user work. Do not revert them unless explicitly asked.

## Build Discipline

- Prefer existing project conventions.
- Keep edits narrowly scoped.
- Avoid unrelated refactors.
- Add tests when behavior changes or risk is non-trivial.
- Verify with project-native commands.
- If verification cannot run, record why and what risk remains.

## Role Tiers

Use cheaper/smaller roles for broad or mechanical work:

- Explorer: read-only discovery and relevant file mapping
- Verifier Dependency: dependency and supply-chain checks

Use medium/strong roles for:

- Implementer: code changes and tests
- Checker: independent done/stuck judgment
- Verifier Quality: correctness and maintainability review

Use the strongest available role only for:

- Security boundary review
- irreversible/high-risk decisions
- final architecture judgment

## Definition Of Done

A task is complete only when:

- acceptance criteria are met or explicitly revised
- relevant verification passed or failures are recorded
- task state is updated under `state/`
- token/iteration usage is recorded when available
- final handoff explains what changed, how it was verified, and what remains
