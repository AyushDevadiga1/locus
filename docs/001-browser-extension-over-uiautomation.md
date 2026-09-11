# ADR-001 — Browser Extension over UIAutomation for Tab Metadata

**Date:** 2026-09  
**Status:** Decided

---

## Context

Locus needs to know which browser tab the user has in focus — specifically the full URL and page title — to perform domain classification and topic inference.

Two approaches were evaluated:

**Approach A — OS UIAutomation / win32gui**  
Query the Windows accessibility tree to read the browser's address bar.

**Approach B — Browser Extension (WebExtensions API)**  
A lightweight companion extension streams `{url, title, tabId}` to the desktop daemon via native messaging on every tab change.

---

## Decision

**Approach B — Browser Extension.**

---

## Reasoning

UIAutomation on Windows returns the window title, not the URL. Chrome's window title for a tab is the page title (e.g. "Stack Overflow — Where Developers Learn"). This gives us a string to tokenise but not a URL, which means:
- No domain extraction
- No path-based category detection (e.g. `/watch` vs `/course` on the same domain)
- No reliable deduplication across tabs showing the same title

The browser extension via native messaging gives us the exact URL on every tab switch, with no polling — it is event-driven. The overhead is a JSON message of ~200 bytes per tab change. This is negligible.

The tradeoff is that the user must install the extension alongside the daemon. This is a one-time setup cost and is documented in the README.

---

## Consequences

- `capture/browser.py` implements a native messaging host (reads from stdin, writes to stdout)
- `extension/background.js` sends tab change events to the native host
- `extension/manifest.json` declares the native messaging permission and host name
- First-run setup must register the native messaging host in the Windows registry
- Firefox and Chrome both support WebExtensions native messaging — V1 targets Chrome only
