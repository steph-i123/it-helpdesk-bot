# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is **PingPal / IT Help Desk Bot** — a Python/Flask chatbot that handles IT support queries via keyword-based intent detection with real command execution on the host OS, simulated responses for enterprise services, and GPT-4 fallback for unrecognized queries.

### Running the app

```bash
source .venv/bin/activate
python3 main.py
```

- Chat interface: `http://127.0.0.1:5000/`
- PingPal preview: `http://127.0.0.1:5000/preview`

### Key caveats

- **No automated test suite exists.** There are no unit/integration tests in the repo. Manual testing via `curl` or the browser UI is the primary validation method.
- **No linter configuration exists.** No flake8, pylint, mypy, or similar is configured.
- **Module response format inconsistency:** The `system` module returns a `list`, which `main.py` handles correctly. Other modules (`network`, `printer`, `active_directory`, `cloud`, `qol`, `security`, `software`, `device`) return `dict` with `"output"`/`"summary"` keys, but `main.py`'s `/chat` handler expects `dict` with `"type"`/`"steps"` or `"type"`/`"chatgpt"` keys. This mismatch causes some commands to return empty or error responses. The `show uptime` command (system module) works reliably for end-to-end testing.
- **OpenAI API key is optional.** The GPT-4 fallback requires `OPENAI_API_KEY` in a `.env` file. Without it, all keyword-matched intents still work; only unrecognized queries will fail.
- **`python3-venv` must be installed** on Debian/Ubuntu before creating the virtual environment: `apt-get install -y python3.12-venv`.
