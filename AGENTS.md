## Cursor Cloud specific instructions

### Project overview

IT Help Desk Bot ("PingPal") — a Flask-based AI chatbot with intent detection and real command execution. See `README.md` for structure and setup.

### Running the app

```bash
source .venv/bin/activate
python3 main.py
```

The Flask dev server starts on `http://127.0.0.1:5000` with `debug=True` (auto-reload enabled).

- Chat UI: `http://127.0.0.1:5000/`
- PingPal preview: `http://127.0.0.1:5000/preview`

### Key caveats

- **No test suite exists** — there are no automated tests, no `pytest.ini`, no test files. Testing is manual via the chat UI or `curl`.
- **No linter configured** — no `pyproject.toml`, `setup.cfg`, or linter config in the repo.
- **OpenAI API key required for GPT fallback** — create a `.env` file with `OPENAI_API_KEY=<key>`. Without a valid key, intent-matched commands still work but unrecognized queries return an API error (this is expected behavior).
- **Response format mismatch** — some modules (e.g. `network.py`, `qol.py`) return `{"output": [...], "summary": "..."}` dicts, while `main.py` expects `{"type": "steps", "steps": [...], "summary": "..."}` or lists. This causes `None` responses for some intent-matched queries. This is a pre-existing code issue.
- **System commands are OS-specific** — modules use macOS commands (e.g. `dscacheutil`, `ifconfig en0`). On Linux, some commands will fail or return empty output. The `system.py` module uses portable commands (`df -h`, `uptime`).
- **`python3.12-venv` must be installed** on Debian/Ubuntu before creating the virtualenv: `apt-get install -y python3.12-venv`.
