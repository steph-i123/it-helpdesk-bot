## Cursor Cloud specific instructions

### Project overview

PingPal — an AI-powered IT assistant that uses GPT-4 with function calling to diagnose, explain, and fix tech problems. Built with Flask, targeting non-technical individual users.

### Architecture

- **GPT-4 is the primary brain** — no keyword routing. All user messages go to GPT-4 which decides which diagnostic tools to call.
- **27 real diagnostic tools** in `modules/diagnostics.py` — network, system, device, printer, security. All cross-platform (Linux/macOS/Windows).
- **Conversation memory** — per-session chat history stored in `sessions` dict in `main.py`.
- **Report generator** — `modules/report_generator.py` runs diagnostics and sends results to GPT-4 for plain English translation.

### Running the app

```bash
source .venv/bin/activate
python3 main.py
```

Flask dev server on `http://127.0.0.1:5000` with `debug=True` (auto-reload for templates/static, restart needed for `.env` changes).

### Routes

| Route | What it does |
|---|---|
| `/` | Chat UI (main troubleshooting page) |
| `/preview` | Marketing/hero landing page |
| `/reports` | Report type selection |
| `/reports/generate/<type>` | Generates report with AI summary |
| `/reports/download/<type>` | Downloads report as .txt |
| `/knowledge` | Knowledge base topics |
| `/chat` (POST) | Chat API endpoint |
| `/chat/clear` (POST) | Clears session history |

### Key caveats

- **`OPENAI_API_KEY` required** — set as an environment secret or in `.env`. Without it, chat returns API errors and reports fall back to raw data without AI summaries.
- **No test suite** — no pytest, no test files. Testing is manual via chat UI, `curl`, or browser.
- **No linter configured** — no pyproject.toml or linter config.
- **`.env` changes require server restart** — `dotenv` loads at startup, Flask debug auto-reload does not pick up `.env` changes.
- **`python3.12-venv` must be installed** on Debian/Ubuntu before creating the virtualenv.
- **Report generation takes 15-30 seconds** — GPT-4 summarizes all diagnostic sections into plain English. This is expected.
- **Old modules still exist** in `modules/` (network.py, device.py, etc.) but are no longer routed to from `main.py`. They remain for reference.
