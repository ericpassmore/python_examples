# AGENTS.md

## Delegation Policy

Use subagents aggressively whenever work can be divided into independent tracks. Favor delegation for investigation, codebase discovery, test analysis, documentation review, and separate implementation areas. Keep a coordinating agent responsible for the overall goal, integration decisions, and the final verification.

Before assigning work, confirm that each track has a distinct outcome and can proceed without relying on another track's intermediate results. Do not create subagents merely to repeat the same investigation or to add process overhead.

## Subagent Contracts

Give every subagent a clear, bounded contract that states:

- The objective and expected deliverable.
- The files, components, or questions in scope.
- Relevant constraints, assumptions, and non-goals.
- Whether the agent may edit files or should remain read-only.
- Required evidence or verification to report back.

Require subagents to surface uncertainty, conflicts, and scope drift promptly. Their findings should be concrete enough for the coordinating agent to integrate without redoing the work.

## Read-Heavy Work

Parallelize read-heavy work when the material can be partitioned cleanly. Examples include reviewing separate modules, tracing independent code paths, researching separate failure modes, or examining tests and documentation in parallel.

Avoid concurrent edits to the same files or tightly coupled components. Assign ownership explicitly when edits are necessary, and sequence dependent changes after the required findings are available.

## Stop Condition

Stop delegating or parallelizing when the remaining work is no longer independent. Consolidate the work under the coordinating agent when tasks require shared context, ordered decisions, integration across the same files, or a single verification path.

When this condition is reached, do not force additional subagent tasks. Proceed sequentially, reconcile prior results, and verify the integrated outcome.

## `spec and expand` Prompts

When a user prompt begins with `spec and expand`, treat all following text as a proto-prompt. Refine it into a specific, actionable prompt with clear goals and non-goals. Preserve the user's intent while expanding terse language where needed for precision.

This is a read-only action: do not edit files, run mutating commands, or otherwise change repository state. Ask concise follow-up questions only when material ambiguity prevents a reliable prompt. Otherwise, make reasonable, clearly stated assumptions.
