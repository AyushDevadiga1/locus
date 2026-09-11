# Phase 2 — Session Layer

## Goal

Build the layer that transforms raw signals from Phase 1 into structured session records. This phase is complete when Locus can look at a stream of window and browser events, detect where one task ends and another begins, and produce a clean session record with task blocks inside it.

Nothing in this phase does NLP or topic extraction. That is Phase 3. This phase only segments and aggregates.

---

## The core problem this phase solves

Phase 1 produces a stream of events like:

```
10:00 — VSCode focused
10:04 — Chrome focused (tab: docs.python.org)
10:06 — Chrome tab changed (stackoverflow.com)
10:11 — Chrome focused (youtube.com/watch?...) 
10:31 — VSCode focused
10:33 — Chrome focused (docs.python.org)
```

Phase 2 answers: which of these belong together? Where does one task end and another begin? What is a meaningful unit to show the user in their session summary?

---

## Key concept: task block vs session

A **session** is everything from when the user starts working to when they stop (long idle or explicit stop). A **session** contains multiple **task blocks**.

A **task block** is a coherent cluster of activity around one context. The three chrome tabs above — docs, stackoverflow, VSCode — form one task block even though three different windows were focused. The YouTube visit at 10:11 is potentially a different block or a boundary signal.

The user sees task blocks in their summary, not individual events.

---

## Boundary detection rules

A new task block begins when any of the following is true:

| Signal | Threshold | Reasoning |
|---|---|---|
| Keyboard/mouse idle gap | > 5 minutes | User stepped away or switched mental context |
| Domain category jump | Unrelated domains, no return within 3 min | e.g. switching from github.com to instagram.com |
| App category switch | e.g. editor → game, browser → video player | Strong context signal |
| Explicit session stop | User triggers stop | Ground truth boundary |

These thresholds are starting values. They will be tuned after real usage. They live in `config.py`, not hardcoded.

---

## The "tethered research" rule

A browser tab open alongside an IDE or editor is not a context switch — it is part of the same task block. If `chrome.exe` is active showing `stackoverflow.com` and `code.exe` was active 2 minutes ago, these belong to the same block.

Rule: if a browser tab's domain category matches the category of the previously active non-browser app (e.g. both are `software-development`), do not start a new block.

This is the insight from your research document. It prevents the system from incorrectly splitting a "coding + googling" session into two separate blocks.

---

## Inputs → Outputs

**Input:** raw event tables from Phase 1 DB  
**Output:** two new tables

```sql
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  INTEGER NOT NULL,    -- Unix ms
    ended_at    INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    block_count INTEGER NOT NULL
);

CREATE TABLE task_blocks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    started_at  INTEGER NOT NULL,
    ended_at    INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    app_mix     TEXT NOT NULL,       -- JSON: {app_name: total_ms, ...}
    domain_mix  TEXT NOT NULL,       -- JSON: {domain: total_ms, ...}
    idle_ms     INTEGER NOT NULL,    -- total idle time within block
    topic_terms TEXT                 -- NULL until Phase 3 fills this in
);
```

`topic_terms` is intentionally null in Phase 2. Phase 3 will populate it.

---

## Module responsibilities

**`session/boundary.py`**  
Takes the raw event stream and produces a list of boundary timestamps. Pure function — no DB access. Input: list of events. Output: list of cut points. Testable in isolation with no DB required.

**`session/aggregator.py`**  
Takes the event stream and a list of boundary cut points. Groups events into blocks. Computes `app_mix` and `domain_mix` dictionaries. Writes sessions and task_blocks to DB via `storage/queries.py`. Never touches DB directly.

**`session/schema.py`**  
Dataclasses for `Session` and `TaskBlock`. These are the internal data contracts between modules. Nothing outside `session/` should construct these — only `aggregator.py` creates them.

---

## What "done" looks like for Phase 2

- [ ] `boundary.py` correctly splits a hand-crafted event list into the expected blocks (tested with pytest, no DB needed)
- [ ] `aggregator.py` correctly computes `app_mix` and `domain_mix` from a known event list
- [ ] After a 30-minute real work session, the DB contains one `sessions` row and 2–5 `task_blocks` rows with sensible time distributions
- [ ] The tethered research rule prevents browser tabs from splitting a coding session

---

## Open questions before writing code

1. What is the minimum session length worth logging? A 3-minute accidental open of VSCode should probably not become a session record.

2. Should the session start automatically when the system boots, or only when the user explicitly starts one? V1 is probably explicit start — simpler, more honest, and avoids logging things the user didn't intend to track.

3. How do we handle a machine coming back from sleep? The idle gap would be enormous. Sleep/wake events from the OS are the signal here — Phase 1 should capture system state events too.
