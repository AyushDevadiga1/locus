# Phase 1 — Capture Layer

## Goal

Build the raw signal collection layer. This phase is complete when Locus can reliably observe what the user is doing — which window is active, which browser tab is in focus, and keystroke timing — and write those signals to the database in a clean, privacy-filtered format.

Nothing in this phase interprets signals. Capture only.

---

## Inputs → Outputs

| Module | Input | Output stored to DB |
|---|---|---|
| `capture/window.py` | OS focus change events | `{timestamp, app_name, window_category, duration_ms}` |
| `capture/browser.py` | Extension message via native messaging | `{timestamp, domain, path_category, title_keywords}` |
| `capture/keyboard.py` | Key event stream from pynput | `{timestamp, iki_ms, burst_length, pause_duration_ms}` |

IKI = inter-key interval. Characters are never stored.

---

## What "done" looks like for Phase 1

- [ ] `window.py` fires an event on every focus change, suppresses sensitive app categories, writes to DB
- [ ] `browser.py` receives a native messaging JSON packet from the extension, strips PII from URL, writes to DB
- [ ] `keyboard.py` listens to key events, computes IKI and burst metrics, discards all key identity information
- [ ] `storage/db.py` has the raw signals schema initialised and migrated
- [ ] Running `python -m locus.capture` for 5 minutes produces a readable log of events with no sensitive data visible

---

## Signals selected for V1 and why

**Window / focus tracking** — highest signal-to-cost ratio. An OS focus change event fires once per switch, costs microseconds, and tells us the application and window title. This is the backbone of session detection.

**Browser extension** — the only reliable way to get full tab URLs. UIAutomation on Windows returns the window title, not the URL, which is insufficient for domain classification. The extension sends a JSON message on tab change via native messaging — zero polling, accurate, privacy-controlled at the source.

**Keystroke dynamics** — inter-key intervals and burst patterns indicate activity level without capturing what was typed. A long pause in keystrokes is a boundary signal. A burst of fast typing indicates active engagement. Characters are discarded immediately at the listener level.

---

## Signals excluded from V1 and why

| Signal | Reason excluded |
|---|---|
| Screen capture / OCR | High CPU, high privacy risk, low accuracy on partial screens. Post-V1 opt-in only. |
| Audio classification | Classifier not validated for use case. Resolves the "music = studying?" problem wrongly. |
| Webcam / gaze | Extreme overhead, requires explicit consent infrastructure not built yet. |
| Mouse coordinates | Behavioural patterns possible but not needed for V1 session detection. |
| Clipboard | High privacy risk. Copy/paste frequency not needed for topic detection. |

---

## Privacy rules enforced at capture

### Window titles
A window is checked against a category denylist before its title is stored. Matching categories: banking, password managers, private messaging, system credential prompts. On match: app name is stored as `[SUPPRESSED]`, title is discarded entirely.

### Browser URLs
Before storage, URLs pass through a sanitiser that:
1. Strips all query parameters (`?` and everything after)
2. Strips path segments that look like user IDs (numeric, UUID-shaped, or base64-shaped)
3. Keeps: domain, TLD, and meaningful path segments (e.g. `/docs`, `/watch`, `/course`)

Example: `https://github.com/AyushDevadiga1/private-repo/issues/42` → `{domain: github.com, path_category: repository/issues}`

### Keyboard
`pynput` listener receives key events. The first operation on every event is: discard the key identity. Only the timestamp is kept. IKI is computed from consecutive timestamps. The key value never touches a variable that gets passed anywhere.

---

## Database schema for Phase 1

```sql
CREATE TABLE raw_window_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,       -- Unix ms timestamp
    app_name    TEXT NOT NULL,
    win_category TEXT,                  -- e.g. 'browser', 'editor', 'suppressed'
    title_hash  TEXT                    -- SHA256 of title for dedup, never plaintext
);

CREATE TABLE raw_browser_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           INTEGER NOT NULL,
    domain       TEXT NOT NULL,
    path_category TEXT,                 -- sanitised path label
    title_tokens TEXT                   -- space-separated keyword tokens, not full title
);

CREATE TABLE raw_keyboard_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             INTEGER NOT NULL,
    iki_ms         REAL,               -- inter-key interval in milliseconds
    burst_length   INTEGER,            -- keys in current burst
    pause_ms       REAL                -- ms since last burst ended (null if in burst)
);
```

---

## Open questions before writing code

1. **Native messaging host registration** — on Windows, the extension communicates via a registry entry pointing to a manifest JSON file. This needs to be set up as part of the install process. How should we handle first-run setup?

2. **Sensitive app denylist** — the denylist needs to be maintained. Should it be hardcoded in `constants.py`, user-editable in `config.py`, or both?

3. **Window title vs app name on Windows** — `win32gui.GetForegroundWindow()` gives the HWND; `GetWindowText()` gives the title; `GetWindowModuleFileName()` or process enumeration gives the exe name. Which combination is sufficient for category detection without over-capturing?

These questions get answered during implementation, not before. Document the decision made in `docs/decisions/` when you make it.
