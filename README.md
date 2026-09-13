# Locus

A lightweight, offline-first session logger for focused work.

Locus runs quietly in the background while you study or work. It observes what windows are in focus, groups app activity into categories, and produces a structured record of your work sessions. This makes it possible to review where your time went, detect task transitions, and later connect activity back to the topics you were working on.

---

## What Locus does

- Tracks the active foreground window on Windows using a native event hook
- Resolves the owning application executable and maps it to a category such as editor, browser, terminal, communication, or productivity
- Emits structured activity payloads with timestamp, app name, category, and duration in milliseconds
- Logs app transitions over time so later session logic can detect boundaries and work blocks
- Stores data locally on the machine with no external account or cloud dependency

---

## Current window capture capabilities

The current capture layer can:

- listen for foreground-window focus changes through the Windows event system
- read the process name behind the focused window
- match that process against the app category mapping in [locus/config/app_mapping.json](locus/config/app_mapping.json)
- emit JSON payloads like:

  {
    "timestamp": 1720000000000,
    "app_name": "code.exe",
    "window_category": "editor",
    "duration_ms": 42000
  }

- flush the final active app interval when the tracker stops
- run without side effects during import, so it remains testable and safe to use from other modules

---

## What Locus does not do yet

- It does not judge productivity.
- It does not capture keystrokes or clipboard content.
- It does not read browser tab titles or URLs by default in the core capture layer.
- It is not yet a complete session summarizer or reminder scheduler end-to-end.

---

## Privacy model

Every signal Locus collects is filtered at the point of capture. Window titles are not used for the core tracking loop, and local app classification is based on executable names rather than raw user content. The system is designed to stay on the machine and avoid sending data anywhere external.

---

## Project status

Active development. See [docs/phases/](docs/phases/) for the current build plan.

| Phase | Description | Status |
|---|---|---|
| 1 | Capture layer — window + browser signals | 🔨 In progress |
| 2 | Session layer — boundary detection + aggregation | 📋 Planned |
| 3 | Recall layer — summaries, graphs, reminders | 📋 Planned |

---

## Tech stack

- **Python 3.11+** — core daemon
- **SQLite** — local storage, single file, no server
- **Windows Win32 API + pywin32** — foreground window tracking
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
