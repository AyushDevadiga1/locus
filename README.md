# Locus

A lightweight, offline-first session logger for focused work.

Locus runs quietly in the background while you study or work. It observes what windows and browser tabs you have open, detects natural task boundaries, and at the end of a session gives you a structured summary — what you worked on, for how long, and what topics connected to each other. It then schedules reminders so you return to those topics before you forget them.

---

## What Locus does

- Tracks active windows and browser tabs passively, with near-zero CPU overhead
- Groups activity into task blocks automatically, based on context switches and idle gaps
- Produces a session summary: topics covered, time distribution, concept connections
- Schedules spaced-repetition reminders (SM-2) to nudge you back to what you studied
- Stores everything locally — no cloud, no accounts, no data leaving your machine

---

## What Locus explicitly does not do

- **It does not judge productivity.** Locus does not decide whether you were focused or distracted. That judgment belongs to you.
- **It does not capture keystrokes or clipboard content.** Only timing dynamics are observed, never characters.
- **It does not record audio or video.** No microphone, no webcam in V1.
- **It does not perform real-time classification.** All analysis runs after a session ends, on idle CPU.
- **It does not send anything to any external API.** The entire pipeline runs on your machine.

---

## Privacy model

Every signal Locus collects is filtered at the point of capture — before it touches any other part of the system. Window titles from sensitive applications (banking, passwords, private messaging) are suppressed entirely. Browser URLs are stripped of query parameters and personal identifiers before storage. Raw keystroke characters are never recorded; only inter-key timing intervals are kept. No raw text from your screen is stored — only extracted topic terms.

---

## Project status

Active development. See [`docs/phases/`](docs/phases/) for the current build plan.

| Phase | Description | Status |
|---|---|---|
| 1 | Capture layer — window + browser signals | 🔨 In progress |
| 2 | Session layer — boundary detection + aggregation | 📋 Planned |
| 3 | Recall layer — summaries, graphs, reminders | 📋 Planned |

---

## Tech stack

- **Python 3.11+** — core daemon
- **SQLite** — local storage, single file, no server
- **Browser Extension (WebExtensions API)** — accurate tab metadata
- **spaCy** — local NLP for topic extraction, post-session only
- **SM-2** — spaced repetition scheduling algorithm

---

## Design principles

1. **Mirror, not judge** — the system observes and reports. You interpret.
2. **Event-driven, not polling** — the daemon does nothing until something changes.
3. **Batch analysis, not real-time** — heavy work runs when your session ends, not during it.
4. **One module, one responsibility** — each component has a single job and clear boundaries.
5. **Privacy at the point of capture** — filtering happens before data enters the pipeline, not after.
