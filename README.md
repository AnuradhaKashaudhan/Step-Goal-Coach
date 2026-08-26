# Stride — Step Goal Coach (Agentic AI Project)

A small agentic AI app: a Gemini-powered coach that helps you hit a daily
step goal. You chat with it in plain English ("I just walked 2000 steps",
"how am I doing?"); it **decides on its own** which tools to call, reads
the results, and replies with a specific, encouraging nudge.

## What makes it "agentic"

The LLM (Gemini) is given three Python functions as **tools** and decides
for itself, per message, which ones to call and with what arguments:

| Tool | What it does |
|---|---|
| `log_steps(count)` | Adds steps to today's total |
| `get_progress()` | Today's steps, goal, and steps remaining |
| `get_weekly_summary()` | Rolling 7-day total + milestone check (10k / 25k / 50k / 75k / 100k) — *the group add-on* |

You never call these tools directly from the frontend chat — Gemini reads
your message, chooses the tool(s), executes them, and writes the reply.
The dashboard on the right (progress ring + weekly "footprint trail")
reads the same data directly for a live view, without going through the LLM.

## Project structure

```
step-coach/
├── app.py              # Flask backend + API routes
├── agent.py            # Gemini tool-calling agent
├── storage.py           # Tools + JSON-file persistence (data.json, auto-created)
├── requirements.txt
├── templates/
│   └── index.html      # Frontend (chat + dashboard, vanilla HTML/CSS/JS)
└── README.md
```

## Setup (should take ~5 minutes)

**1. Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**2. Get a free Gemini API key**
Go to https://aistudio.google.com/apikey and create a key.

**3. Set the key as an environment variable:**
```bash
# macOS / Linux
export GEMINI_API_KEY="your-key-here"

# Windows (PowerShell)
$env:GEMINI_API_KEY="your-key-here"
```

**4. Run the server:**
```bash
python app.py
```

**5. Open the app:**
Go to http://localhost:5000 in your browser.

## Using it

- Type things like `I just walked 3200 steps` or hit a quick-add button.
- Ask `How am I doing today?` or `What's my week looking like?`
- Change your daily goal in the top-right field.
- Steps persist in `data.json` (created automatically next to `app.py`) so
  your progress survives a server restart.
- The weekly "footprint trail" shows the last 7 days at a glance, and a
  milestone banner celebrates crossing 10k / 25k / 50k / 75k / 100k steps
  in the rolling week.

## API endpoints (for reference / testing without the UI)

```
GET  /api/state          -> current dashboard state (no LLM call)
POST /api/chat            -> {"message": "I walked 2000 steps"} -> agent reply + fresh state
POST /api/goal             -> {"goal": 10000} -> updates the daily step goal
```

## Notes / things you could extend later

- Currently single-user (one shared `data.json`, one shared chat session)
  — fine for a demo/submission, would need per-user sessions for real use.
- Swap `data.json` for a real database if you need multi-user support.
- `gemini-2.0-flash` is used for speed/cost; swap the `MODEL_NAME` in
  `agent.py` for a different Gemini model if you like.
