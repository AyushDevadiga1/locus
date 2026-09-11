# Phase 3 — Recall Layer

## Goal

Build the layer that turns structured session records into something useful to the user. This phase is complete when Locus can: extract what a session was about, build a lightweight concept graph connecting sessions over time, and schedule reminders to bring the user back to those topics.

This phase runs entirely post-session, on idle CPU. Nothing here happens in real time.

---

## What this phase produces for the user

After a session ends, the user can open Locus and see:

1. **Session summary** — what you worked on, in which blocks, for how long
2. **Topic terms** — what concepts appeared across each task block
3. **Concept graph** — how topics from this session connect to topics from previous sessions
4. **Upcoming reminders** — when Locus will nudge you to revisit each topic

This is the "mirror" the whole project is built around. The user reads it and decides what it means. Locus does not tell them whether they were productive.

---

## Module: `analysis/topics.py`

**Job:** given a task block's `domain_mix` and `app_mix`, produce a list of topic terms.

**Approach — no LLM, no screen capture:**

Topic terms in V1 come from two sources only:

1. **Domain-to-topic mapping** — a curated dictionary mapping known domains to topic categories. `docs.python.org → Python`, `arxiv.org → Research/ML`, `leetcode.com → DSA`, `stackoverflow.com → Software Engineering`. This is deterministic, fast, and requires no NLP.

2. **Browser title tokens** — the `title_tokens` field stored in Phase 1 (sanitised, non-PII tokens from the page title). These are passed through spaCy's noun-chunk extractor to pull meaningful terms. spaCy runs locally, post-session, taking as long as it needs on idle CPU.

**Why not OCR or screen capture for topic extraction?**  
Because it violates the privacy model and the CPU constraint. The domain mapping + title tokens approach gives 80% of the value at 5% of the cost. OCR is a potential V2 opt-in feature, not a V1 dependency.

**Output:** `topic_terms` field in `task_blocks` table gets populated — a JSON list of strings.

---

## Module: `analysis/graph.py`

**Job:** build and update a concept graph across sessions.

**What the graph is:**  
A simple undirected graph where nodes are topic terms and edges represent co-occurrence within the same session. If `Python` and `Algorithms` both appear in the same session, they get an edge (or the edge weight increments if they've co-occurred before).

**What the graph is not:**  
A semantic knowledge graph, an ontology, or anything that requires embeddings or an ML model. Pure co-occurrence, weighted by frequency. Simple and honest.

**Storage:** stored as a JSON adjacency list in the DB. Not a separate graph database — SQLite is sufficient for V1 at personal scale.

**What the user sees:** a visual graph (rendered in the dashboard, Phase 3 extension) showing which topics they tend to work on together. Useful for understanding their own learning patterns over weeks.

---

## Module: `recall/scheduler.py`

**Job:** for each topic term extracted from a session, schedule a reminder using SM-2.

**Why SM-2:**  
SM-2 is a well-validated spaced repetition algorithm (SuperMemo, Anki). It schedules the next review based on how well the user recalled the item last time. For Locus: the "recall quality" signal comes from whether the user opened a related topic in a later session — passive recall detection, no quiz required in V1.

**V1 simplified SM-2:**  
- New topic seen for the first time → reminder in 1 day
- Topic seen again within reminder window → interval multiplied by ease factor (starts at 2.5)
- Topic not revisited within window → interval resets to 1 day
- No quality rating required from user — revisit detection is the signal

**What triggers "revisited":** if a topic term from a previous session appears in the current session's topic terms, the scheduler updates the SM-2 state for that term automatically.

---

## Module: `recall/notifier.py`

**Job:** send a desktop notification when a topic's SM-2 reminder date is due.

**V1 implementation:** Windows toast notification via `plyer` or `win10toast`. One notification per due topic, max 3 per day to avoid notification fatigue. The notification contains the topic name and the session it came from, with a timestamp.

**What it does not do:** it does not open an app, force a quiz, or block anything. It is a nudge, not an interruption.

---

## What "done" looks like for Phase 3

- [ ] After a real session, `topic_terms` is populated in all task blocks with meaningful terms (not garbage)
- [ ] The domain-to-topic mapping covers at least 30 commonly used domains relevant to study/work
- [ ] The concept graph updates correctly after two sessions that share a topic
- [ ] A desktop notification fires at the correct SM-2 scheduled time for a topic
- [ ] The full post-session pipeline (topics → graph → scheduler) runs in under 10 seconds on a standard laptop

---

## Open questions before writing code

1. **Domain mapping maintenance** — the domain-to-topic dictionary needs to be extensible by the user (they visit domains we haven't mapped). What's the UX for adding a mapping? A config file they edit? An interactive prompt on first visit to an unknown domain?

2. **Passive revisit detection** — SM-2 normally requires an explicit quality rating (0–5). We're using revisit-or-not as a binary signal. This is a simplification. Is it good enough, or does it collapse the SM-2 scheduling into something too coarse? Worth validating with real usage before deciding.

3. **Graph display** — Phase 3 as described here covers the data layer. The visual graph display is a UI concern. Does V1 need a UI at all, or is a JSON export sufficient to validate that the data is correct before building a frontend?

---

## What is explicitly out of scope for Phase 3

- Quiz generation (FKT had this — Locus V1 does not)
- LLM-based summarisation
- Cloud sync or multi-device support
- Any analysis that requires screen capture or OCR
- Sentiment or productivity scoring
