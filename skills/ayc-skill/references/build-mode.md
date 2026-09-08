# Build mode — the user brings the work list

The review pipeline starts from *"find what's wrong."* Build mode starts from
**"here is what I want done"**: a list of issues to fix, features to add, or
patches to apply. The user sets the agenda; you take the lead on how it gets
built, verified and shipped.

Trigger it on any request shaped like a work list — *"I have issues in X, Y, Z and
I want features A, B, C"*, "add …", "fix this bug", "patch …", "implement …" —
whether the list has one item or ten.

**This is a writing mode from the start.** There is no read-only review phase to
hide behind, so the discipline moves into the per-item loop below: nothing is
built that wasn't agreed, and nothing is claimed done that wasn't verified.

---

## Step B0 — Memory and detection, same as always

Load `.ayc-skill/memory.md` (Step 0) and detect stack, real commands and
scope (Step 1) if memory doesn't already hold them verified. Check the **Findings
& fix ledger** before anything else: an issue the user just reported may already
be `[open]` there with an agent's diagnosis attached, or `[wontfix]` with a reason
worth raising before you build over it.

Skip nothing here. Building against a guessed test command wastes a whole item.

---

## Step B1 — Turn the list into a work plan

**Restate every item back as a discrete work item**, numbered, in the user's own
order. For each one, establish four things:

| Field | How you get it |
|---|---|
| **Type** | `bug` / `feature` / `patch` — decides how it's verified |
| **Owner** | the agent whose surface it lands on (`standards.py --who "<item>"` when unclear) |
| **Acceptance** | how you and the user will both know it's done |
| **Unknowns** | what you'd otherwise have to assume |

**Ask about the unknowns — batched, once.** A bug report without a repro, a
feature without a scope boundary, a patch without a target version: these are the
questions that decide whether the work is right, and they cost one round-trip now
versus a rebuild later. Ask them together, in one prioritized round, not
item-by-item across ten turns. What you can determine from the code, determine
from the code — never ask what you can read.

**For a bug, reproduce before you plan.** An unreproduced bug gets a diagnosis
labelled *unverified* and a first item of "reproduce it", not a speculative fix.
The user's description of a bug is evidence, not a diagnosis.

**Raise the real design decisions ADR-style** — problem, options, trade-off,
recommendation — and keep them short. A feature that implies a new dependency, a
schema change, a new external call, or a public API shape is a decision the user
owns, not an implementation detail you pick silently.

**Then present the plan and get it approved**: the numbered items, each with its
owner, acceptance criterion, rough size, and anything it will change that the
user didn't ask for (a migration, a new dep, a config change). Flag items you
think are a bad idea *once*, with the reason — then build what they confirm.

**Order the items yourself.** Blockers and shared foundations first, then by the
user's priority. Say why the order differs from theirs if it does.

---

## Step B2 — Build, one item at a time

**Dispatch the owning agent per item, sequentially.** Never in parallel: these are
writes, and two agents editing a shared tree corrupt it. The dispatch carries the
usual brief (shared rules, role block, standards, scope, commands, skill dir,
`recall.py` line) plus **this item and only this item** — its acceptance
criterion, its unknowns already answered, and the decisions already made.

Per item, the owning agent:

1. **Reads before writing.** The existing pattern for this kind of change in this
   repo wins over the agent's preferred pattern. New code should be
   indistinguishable in style from the code around it.
2. **Makes the smallest change that satisfies the acceptance criterion.** No
   drive-by refactors, no renames, no reformatting untouched lines. Something
   genuinely worth changing that wasn't asked for is *reported*, not done.
3. **Applies the standards it owns** (`standards.py --agent <role>`). A new
   endpoint gets rate limiting; a new form input gets a bound label; a new AI
   call gets a per-user cap. Shipping a fresh violation of a blocking standard is
   not "done".
4. **Verifies against the acceptance criterion** with real output — the test it
   wrote or ran, the command result, the rendered screen. `tester` and `frontend`
   drive the in-app browser (`mcp__Claude_Browser__*`) for anything with a UI:
   both viewports, the new control actually clicked, console and network clean.
5. **Reports** what changed, which files, the verification output, and anything it
   deliberately left alone. Same output caps as review (`report-format.md`).

**You verify independently.** After each item, *you* re-run the relevant test,
lint, type-check or build command and report that output. An agent grading its own
work is the blind spot of this design; objective command output closes it. An item
whose verification fails goes back to the same agent with the failure attached —
it does not silently move to the next item.

**Regression check on every item, not just at the end.** The suite that passed
before item 3 must still pass after it. A green new feature on top of a broken
existing one is a net loss, and finding it now costs one item's context instead of
ten.

**Stop and ask** when an item turns out to be materially bigger than planned,
blocked by something the user didn't mention, or in conflict with an item further
down the list. Deliver what's finished, say plainly what's blocked and why — do
not quietly scale the item down.

---

## Step B3 — Deliver

Report per item: `done` / `done with caveats` / `blocked`, the files touched, the
verification evidence, and the diff summary. Then, across the whole set:

- **What else changed** — migrations, new dependencies, config, generated files.
- **What you noticed but didn't touch** — the drive-by findings from step B2.2,
  offered as a follow-up list, never applied unasked.
- **Suggested next step** — usually the review pipeline over the diff you just
  created (`run ayc-skill` scoped to the working diff), which is the honest
  way to catch what the building agents were too close to see.

Consolidate into memory: each item into the **Findings & fix ledger** (`[fixed]`
with its verification, or `[open]` if blocked), new stack/command facts into their
sections, *Improvements* into *Agent learnings*, and unbuilt suggestions into the
*Enhancement backlog*. Run it all through `redact.py --strict` first.

**Deploying is Step 6, unchanged and still gated.** Finishing the work list does
not authorize shipping it.

---

## Mixed requests

*"Fix these three and review the rest"* is build mode followed by the review
pipeline over the resulting diff — in that order, because reviewing code you are
about to rewrite wastes the review. Say which order you're taking and why.

*"Just tell me how you'd do X"* is not build mode. Answer it (ask mode in
`SKILL.md`), and offer to build it.
