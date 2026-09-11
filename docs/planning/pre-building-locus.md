# Computational Overhead of Inputs :
Capturing different Input from user like  :  text ,prompts,screenshots,videos,frames,eventlogs,gaze,etc.cause an overehead in system CPU and GPU (if) causing the system to slow down and create variour problems with the actual running processes in foreground.

Below is the ranked list of these : 

## Overhead Matrix Overview
| Rank | Input Method | Resource Cost | Primary Bottleneck | Data Footprint |
|---|---|---|---|---|
| 1 | Gaze Tracking (Webcam) | Extreme | Real-time GPU Inference & Video Decoding | Gigabytes/hour (Raw) |
| 2 | Visual Screen Parsing | High | Image Processing & Vision Models | Megabytes/second |
| 3 | NLP Context Summarization | Moderate-High | Text Tokenization & LLM/SLM Embeddings | Kilobytes to Megabytes |
| 4 | Task Mining (OS Logs) | Low-Moderate | Data Clustering & Event Streaming | Kilobytes/minute |
| 5 | Keystroke/Mouse Dynamics | Negligible | Event Listeners & Basic Analytics | Bytes/second |


# List of ways to extract Information : 

| Activity / Signal | Raw Data You Can Observe | Derived Features / Information | Possible Higher-Level Inference | Typical Latency | Resource Cost |
|---|---|---|---|---|---|
| **Keyboard Activity** | Key-down/up events, timestamps, modifier keys | Inter-key interval, typing speed, pause duration, correction/backspace rate, burst length | Typing/interaction patterns, activity level | Real-time | 🟢 Low |
| **Mouse Activity** | Cursor coordinates, clicks, scrolls, timestamps | Cursor velocity, distance travelled, click rate, idle periods, movement patterns | Interaction intensity, navigation patterns | Real-time | 🟢 Low |
| **Window / Focus Tracking** | Active window, application name, window title, focus changes | Time per application, context switches, active/idle periods | Current task/context, workflow patterns | Real-time | 🟢 Low |
| **Process Tracking** | Process ID, executable, start/stop events | Application sessions, process duration, application sequences | Software usage and workflow | Real-time → Batch | 🟢 Low |
| **Filesystem Activity** | File create/modify/delete/rename events, paths | File activity frequency, directory activity, temporal patterns | Document/workflow activity | Near real-time | 🟢 Low |
| **Screen Capture / Parsing** | Screenshots or video frames | OCR text, UI elements, visible application, screen regions, visual state | Visible task/context | Near real-time → Batch | 🟡 Medium → 🔴 High |
| **Clipboard Activity** | Clipboard-change events, content type/metadata | Copy/paste frequency, text length, source/destination patterns | Copy/paste behavior and workflow | Real-time | 🟢 Low → 🟡 Medium |
| **Web / Network Metadata** | DNS queries, IPs, ports, connection metadata, traffic volume | Domains contacted, connection frequency, upload/download volume, session patterns | Network/web activity | Real-time → Batch | 🟡 Medium → 🔴 High |
| **Webcam / Gaze** | Video frames | Face landmarks, eye landmarks, gaze estimate, head pose | Approximate visual-attention/gaze signals | Real-time | 🟡 Medium → 🔴 High |
| **Audio / Microphone** | Audio stream/waveform *(with explicit permission)* | Speech activity, volume, pauses, acoustic features | Conversation/activity context | Real-time | 🟡 Medium → 🔴 High |
| **System State** | Lock/unlock, sleep/wake, login/logout, system events | Session duration, idle periods, interruptions | Overall session/activity timeline | Real-time | 🟢 Very Low |
| **Application-Specific Events** | Events exposed by the application's API/logs | Commands, document state, task completion, errors, etc. | Precise application workflow | Real-time → Batch | 🟢 Low → 🟡 Medium |

# GUARDRAILS : 

| Data Source | Main Risk | Primary Guardrail | Secondary Guardrails | What We Ideally Retain |
|---|---|---|---|---|
| **Keyboard** | Passwords, OTPs, messages, API keys | Don't collect characters | Sensitive-field exclusion, local processing, discard raw events | Timing/dynamics |
| **Mouse** | Revealing exact user interaction/location | Prefer behavioral features | Coordinate minimization, aggregation | Velocity, clicks, pauses |
| **Window/Focus** | Sensitive window titles/content | Collect application category/name | Title redaction, allow/deny lists | App/session duration |
| **Processes** | Command-line arguments/secrets | Collect process metadata only | Exclude arguments/environment/memory | Process/session events |
| **Filesystem** | Sensitive filenames/paths/documents | Metadata-only collection | Path filtering, sensitive-directory exclusion | File activity category/timestamp |
| **Screen** | Almost unlimited sensitive information | Explicit opt-in + restricted applications | Redaction, local OCR/CV, discard frames | Required visual features |
| **Clipboard** | Passwords, tokens, private text | Don't retain clipboard content | Content-type filtering, opt-in, immediate discard | Copy/paste events/statistics |
| **Network** | Browsing/activity information | Metadata-only where possible | Domain aggregation, retention limits | Aggregated network activity |
| **Webcam/Gaze** | Face/video/private environment | Explicit opt-in + local processing | No raw-video storage, app/session restrictions | Gaze/pose features |
| **Microphone** | Conversations/private speech | Explicit opt-in | Local VAD, no raw-audio retention | Speech activity features |
| **System State** | Session/activity patterns | Minimize identity information | Retention limits | Login/lock/idle/session events |
| **Application APIs** | Application-specific private data | Request only required events | Permission scopes, API-level filtering | Semantic application events |

# 1.Reversible Token Anonymization (RTA) on Textual Data 
> NOTE : This is in case we use LLM models for our pipeline
------------------------------
## 1. Architectural Architecture & Data Flow
sequenceDiagram
    autonumber
    box "Secure Local Environment"
    actor User
    participant NER as Local NER Engine<br/>(Regex + SpaCy/BERT)
    participant Map as Local Mapping Store
    participant DeMask as Local De-masking Engine
    end

    box "Public / Cloud Space"
    participant LLM as Third-Party LLM<br/>(API Endpoint)
    end

    User->>NER: 1. Send Raw Text Input
    NER->>Map: Store Original Entities & Token Mappings
    NER->>NER: Mask Sensitive Data (PII/PHI)
    NER->>LLM: 3. Send Masked Prompt (Anonymized Payload)
    LLM->>LLM: Process Request
    LLM->>DeMask: 4. Return Anonymized LLM Response
    Map->>DeMask: Fetch Original Entity Mappings
    DeMask->>DeMask: Replace Masked Tokens with Original Values
    DeMask->>User: 5. Output Final De-masked Text
------------------------------
## 2. Process Explanation

   1. Local Ingestion: Raw, sensitive text enters the secure local environment.
   2. Deterministic Masking: A local Named Entity Recognition (NER) engine runs alongside Regex patterns. It identifies sensitive data (Names, Locations, IDs, Financial values) and swaps them with unique, structured tokens (e.g., [PERSON_1], [COMPANY_1]).
   3. Isolated Mapping Storage: The exact original values and their assigned tokens are saved to a temporary Lookup Dictionary inside the local environment. Crucially, this map never leaves the local machine.
   4. External Processing: The anonymized prompt—now entirely stripped of private data—is sent over the cloud to the third-party LLM. The LLM processes the conceptual intent and replies, treating the tokens as passive variables.
   5. Reversible Restoration: The LLM's response arrives back at the local environment. A script reads the response, checks the local lookup dictionary, and swaps the placeholder tokens back to their original cleartext values.

------------------------------
## 3. Process Limitations

* Context & Attribute Leakage: While direct identifiers (Nouns) are masked, unique context clues (e.g., "the founder of a space company that bought a social media platform") can still allow an LLM to infer the identity.
* Pronoun Disclosures: Basic NER models miss pronouns. Leaving phrases like "He authorized the wire transfer" leaks demographic, gendered, or contextual footprints to the model.
* NER Inaccuracy (False Negatives): If the local NER model misses even a single name or account number due to bad formatting, that sensitive data is directly leaked to the external API.
* LLM Token Mismanagement: External LLMs can occasionally alter, drop brackets, or hallucinate the placeholder tokens ([PERSON_1] becoming [person-one]), breaking the automated local restoration script.

------------------------------
## 🌐 Extension: Browser Metadata Extraction Layer
Incorporating browser tab metadata extraction transforms the web browser from an unreadable "black box" into a highly rich context engine. Rather than treating all browser usage as identical, this layer decodes the intent behind the browsing session.
------------------------------
## 1. The Core Telemetry Matrix

* Raw Data Captured: Full URL strings, active tab titles, and favicons/web-app signatures.
* Derived Features: Top-Level Domain (TLD) grouping, subpath categories (e.g., separating a /watch path on YouTube from a /course path on an educational platform), and keyword semantic vectors.
* Higher-Level Inference: Distinguishing passive entertainment from active technical documentation research or administrative tracking.
* Latency & Resource Cost: Real-time extraction with 🟢 Low CPU/RAM overhead.

------------------------------
## 2. Strategic Benefits to the Machine Learning Engine

        [ Active App: chrome.exe ] ──► [ Tab Title: "python index out of bounds" ] ──┐
                                                                                    ├──► ML Classifier: "Tethered Deep Work"
        [ Active App: vscode.exe ] ──► [ File Name: "main.py"                    ] ──┘

## 🎯 Context Disambiguation
Typing inputs can look identical across different websites. Tab metadata allows the model to instantly separate "Active Technical Troubleshooting" (e.g., reading StackOverflow or documentation) from a casual writing session on a social media site, even though both occur inside the same browser executable.
## 🔗 The "Tethered Research" Heuristic
Users constantly switch between an IDE/Editor and a browser. If the semantic keywords in the active browser tab match the project file name or workspace context currently active in Tier 1, the system computes a Linked Activity Block. This ensures the user is not falsely penalized for web browsing when they are actually performing vital task-related research.
------------------------------
## 3. Engineering Implementation Strategies
To capture this data, the research architecture evaluates two primary technical approaches:

* Approach A: OS-Level Accessibility APIs (UIAutomation / AppleScript): The local daemon queries the operating system's window tree to read the browser's address bar. Pros: Universal setup with zero user-installed plugins. Cons: Easily broken by browser UI layout updates; typically only returns the window title rather than the complete URL string.
* Approach B: Browser Extension Companion (WebExtensions API): A lightweight background extension streams the exact active URL and title locally to your main desktop app daemon via Native Messaging. Pros: 🏆 Highly Recommended for Research. Incredibly stable, accurate, and provides full subpaths for flawless domain classification. Cons: Requires the user to authorize a browser extension alongside the core desktop application.

------------------------------
## 4. Privacy Guardrails (Local Tokenization)


    To remain compliant with strict global privacy laws (GDPR/CCPA) and handle company-sensitive information safely, the system utilizes a Local Tokenization Layer.
    Before a URL is logged or passed to the local adapter model, it is immediately stripped of private query parameters, user accounts, or specific repository names. For example, https://github.com is processed locally and safely converted into: [Domain: github.com | Context: Software Engineering / Issue Tracker].
