# Comprehensive Iframe Scanner

A modern toolkit to discover iframes and find text across pages and embedded frames.

Supports three workflows:
- Web UI with real-time logs and results (Flask + Socket.IO)
- CLI scanning for URL or pasted HTML/DOM
- DOM-only iframe XPath finder (no browser) from pasted HTML

---

## Features
- Comprehensive iframe discovery (including nested)
- Multiple text search strategies (exact, contains, case-insensitive, attributes)
- Detailed report with iframe hierarchy, XPaths, and previews
- Real-time web UI with progress, logs, and results
- DOM-only helper to extract iframe XPath(s) from pasted HTML attributes/srcdoc

---

## Prerequisites
- Python 3.9+ (tested with 3.10+)
- Google Chrome (latest stable)
- Network access if scanning live URLs

Python packages (install below):
- selenium
- Flask
- Flask-SocketIO
- eventlet or threading (we default to threading)
- beautifulsoup4

Note: Modern Selenium auto-manages ChromeDriver via Selenium Manager.

---

## Installation

From the project directory:

```bash
# Recommended: create a venv
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt  # if present
# or install directly
pip install selenium Flask Flask-SocketIO beautifulsoup4
```

If you see SSL or build errors behind a proxy, configure `pip`/proxy first.

---

## Quick Start (Web UI)

```bash
# From project root (mind the space in path)
python "d:/UK Intern/iframe/start_web_app.py"
```

Then open: http://localhost:5000

In the UI:
- Choose URL or HTML/DOM input
- Provide search text
- Click Start Scan to run Selenium-based scan
- Or, in HTML mode, use the "DOM-only iframe XPath → Get XPaths" button to extract iframe XPath(s) using only your pasted HTML

---

## CLI Tools

### 1) simple_scanner.py (URL or DOM input)
Interactive scanner that can take a URL or pasted HTML and search for text.

```bash
python "d:/UK Intern/iframe/simple_scanner.py"
```
Follow prompts:
- Choose input method (URL or HTML/DOM)
- Provide the URL or paste HTML
- Enter the search text

### 2) dom_scanner.py (DOM-focused)
Paste raw HTML/DOM and search for text. Also prints DOM-only iframe XPath matches from attributes/srcdoc.

```bash
python "d:/UK Intern/iframe/dom_scanner.py"
```
Paste your HTML, then enter the search text.

---

## DOM-only iframe XPath Finder (UI + CLI)

The DOM-only helper finds iframes where the search term appears in:
- iframe attributes (id, name, title, class, src, etc.)
- inline `srcdoc` HTML

It does not fetch external `src` documents or execute JavaScript. This avoids cross-origin restrictions but requires that relevant content be present in the pasted DOM or `srcdoc`.

In Web UI:
- Switch to HTML/DOM Source
- Paste HTML
- Enter search text
- Click "Get XPaths"

In CLI (`dom_scanner.py`):
- After the standard scan report, a section prints DOM-only matches.

---

## API (Web UI backend)

- POST `/api/start-scan` — starts a Selenium-based scan (URL or HTML)
- GET  `/api/scan-status/<session_id>` — current status
- GET  `/api/scan-results/<session_id>` — final results
- POST `/api/stop-scan/<session_id>` — stop running scan
- POST `/api/dom-iframe-xpaths` — DOM-only iframe XPath matches
  - JSON body: `{ "html_source": "...", "search_text": "..." }`
  - Response: `{ success: true, count: <int>, xpaths: ["/html/body//iframe[1]", ...] }`

---

## Tips for Stable Locators
- Prefer attribute-based XPaths:
  - `//iframe[@id='...']`
  - `//iframe[contains(@src,'partial')]`
- Avoid brittle absolute paths like `/html/body/div[2]/.../iframe`
- If using web components (shadow DOM), XPath cannot cross shadow roots; use JS shadowRoot traversal.

---

## Troubleshooting

- Chrome/Driver errors:
  - Update Chrome to latest
  - Ensure Selenium 4.12+ (Manager auto-handles driver)
  - Try `pip install -U selenium`

- Cannot access iframe content:
  - Cross-origin iframes block access by design (CORS). Use the DOM-only helper if you only have pasted HTML
  - For live scans, ensure the target text is rendered and accessible; some apps defer content until login or later

- Windows paths with spaces:
  - Quote the path, e.g. `python "d:/UK Intern/iframe/dom_scanner.py"`

- Shadow DOM:
  - XPath won’t traverse shadow roots. Consider JS evaluation with `element.shadowRoot.querySelector()` hops.

---

## Project Structure (key files)

```
iframe/
├─ comprehensive_iframe_scanner.py   # Selenium-powered scanner core
├─ simple_scanner.py                 # CLI (URL or DOM)
├─ dom_scanner.py                    # CLI (DOM-focused + DOM-only XPath helper)
├─ web_app.py                        # Flask backend + Socket.IO
├─ start_web_app.py                  # Launcher for web app
├─ templates/
│  └─ index.html                     # Web UI
├─ static/
│  ├─ js/app.js                     # Frontend logic
│  └─ css/style.css                 # Styles
└─ README.md                         # This document
```

---

## Security
- Do not paste sensitive HTML/DOM into shared environments
- Do not hardcode API keys or credentials

---

## License
Proprietary/internal use unless otherwise specified.
