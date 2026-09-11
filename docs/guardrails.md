# Privacy Guardrails

This document defines what Locus captures, what it discards, and where filtering happens. The principle is: **filtering happens at the point of capture, before data enters any other part of the system.**

---

## Core principle

Locus is a mirror, not a surveillance tool. It observes the minimum signal needed to produce a useful session summary. When in doubt about whether to capture something, the answer is no.

---

## Signal-by-signal rules

| Signal | What we capture | What we discard | Where filtering happens |
|---|---|---|---|
| Window focus | App name, app category, duration | Window title of suppressed apps | `capture/window.py` at event time |
| Browser tab | Domain, sanitised path category, title keyword tokens | Query parameters, user IDs in path, full title | `capture/browser.py` before DB write |
| Keyboard | Inter-key interval (ms), burst length, pause duration | Every key identity, every character | `capture/keyboard.py` at listener callback |
| Mouse | Not captured in V1 | Everything | — |
| Screen | Not captured in V1 | Everything | — |
| Audio | Not captured in V1 | Everything | — |
| Webcam | Not captured in V1 | Everything | — |
| Clipboard | Not captured in V1 | Everything | — |
| System state | Lock/unlock, sleep/wake events | — | `capture/window.py` via OS events |

---

## Suppressed application categories

Windows from these categories are detected by executable name or window class. On match, the app is logged as `[SUPPRESSED]` and the window title is discarded entirely.

- Password managers (1Password, Bitwarden, KeePass, etc.)
- Banking and financial applications
- Private messaging (WhatsApp Desktop, Telegram, Signal)
- System credential prompts (UAC dialogs, PIN entry)
- VPN clients

This list lives in `locus/constants.py` and is user-extensible via `config.py`.

---

## URL sanitisation rules

Applied in `capture/browser.py` before any DB write:

1. Strip everything after `?` (query parameters)
2. Strip path segments matching: pure integers, UUIDs, base64-shaped strings (>20 chars, alphanumeric + `-_`)
3. Map the remaining path to a category label where possible
4. If the domain is in the sensitive domain list (banking, health, private email), suppress entirely

Example transformations:
```
https://github.com/AyushDevadiga1/my-repo/issues/42  →  {domain: github.com, path: repository/issues}
https://www.youtube.com/watch?v=dQw4w9WgXcQ          →  {domain: youtube.com, path: watch}
https://mail.google.com/mail/u/0/#inbox               →  [SUPPRESSED - private email]
```

---

## What is never stored

These are hard rules with no exceptions and no config override:

- Raw keystroke characters or key identities
- Raw clipboard content
- Raw audio or video
- Full browser URLs with query parameters
- Window titles from suppressed application categories
- Any data from applications the user has manually added to their personal denylist

---

## Local-only guarantee

Locus has no network calls in V1 except the browser extension's native messaging pipe, which is local (stdin/stdout). There is no telemetry, no crash reporting, no update check, no external API dependency. The SQLite database file lives at a user-configurable path, defaulting to `~/.locus/locus.db`.

---

## User control

- Users can pause capture at any time with a single action
- Users can delete any session or task block from the DB
- Users can add apps or domains to their personal denylist via `config.py`
- The full DB is a plain SQLite file the user can inspect, copy, or delete at any time
