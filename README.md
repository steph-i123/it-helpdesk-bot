# it-helpdesk-bot
AI powered IT help desk bot with intent detection and real automation.

## Structure
- `main.py`: main backend logic
- `modules/`: command modules grouped by category
- `static/`: frontend assets, CSS, and JavaScript
- `templates/`: chat interface HTML
- `preview/`: PingPal product preview mockup

## Goal
- Smart natural language understanding
- Real execution for commands on Windows or macOS
- Active Directory and network troubleshooting support
- Escalation logic and follow-up handling
- GPT fallback support for unknown queries

## Setup
Use a virtual environment so Python packages do not conflict with system packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If creating the virtual environment fails on Linux, install venv support first:

```bash
sudo apt install python3-venv
```

## Run locally
```bash
source .venv/bin/activate
python3 main.py
```

Then open:
- Chat app: `http://127.0.0.1:5000/`
- PingPal preview: `http://127.0.0.1:5000/preview`

## Preview without Flask
To view the static PingPal preview without installing dependencies:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/preview/
```
