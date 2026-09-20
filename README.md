# 🔎 AI Research Agent

Type a topic, get a sourced research report. One CrewAI agent, free DuckDuckGo
search, Groq for inference, Streamlit for the UI.

**Cost: $0.** Groq's free tier and DuckDuckGo both need no payment.

---

## Files

| File | What it does |
|---|---|
| `streamlit_app.py` | The UI. This is what Streamlit Cloud runs. |
| `research_crew.py` | The agent, the task, the crew. The brain. |
| `tools.py` | `web_search` (DuckDuckGo) and `read_page` (fetch a URL). |
| `requirements.txt` | Dependencies. |
| `runtime.txt` | Tells Streamlit Cloud to use Python 3.12. |

---

## Part 1 — Run it on your computer

### Step 1: Get a free Groq key

Go to <https://console.groq.com/keys>, sign in, create a key. It starts with `gsk_`.
Copy it now — Groq only shows it once.

### Step 2: Set up the project

```bash
mkdir ai-research-agent && cd ai-research-agent
# put the project files in this folder

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Installing takes a few minutes. CrewAI pulls in a lot.

### Step 3: Add your key

Create a file named `.env` in the project folder:

```
GROQ_API_KEY=gsk_paste_your_key_here
```

No quotes, no spaces around the `=`.

### Step 4: Run

```bash
streamlit run streamlit_app.py
```

Your browser opens at `localhost:8501`. Type a topic, hit **Run research**.
A report takes 1–3 minutes. Watch your terminal — you'll see the agent's
thinking, every search it runs, and every page it opens. That terminal output
is the single most useful thing for understanding what your agent is doing.

---

## Part 2 — Put it on GitHub

```bash
git init
git add .
git commit -m "AI research agent"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ai-research-agent.git
git push -u origin main
```

**Before pushing, check that `.env` is NOT in the list.** Run `git status`.
If you see `.env`, stop — `.gitignore` isn't working, and you're about to
publish your API key. A leaked Groq key gets scraped and abused within hours.

---

## Part 3 — Deploy to Streamlit Cloud

1. Go to <https://share.streamlit.io> and sign in with GitHub.
2. **Create app** → pick your repo → branch `main` → main file `streamlit_app.py`.
3. Before clicking Deploy, open **Advanced settings**:
   - Python version: **3.12**
   - Secrets: paste this, with your real key:
     ```toml
     GROQ_API_KEY = "gsk_your_key_here"
     ```
4. **Deploy.** First build takes 5–10 minutes.

To change secrets later: your app dashboard → ⋮ → Settings → Secrets.

---

## Two things that break most tutorials

These are recent and will bite you if you copy code from a blog post or a
YouTube video made before mid-2026.

**1. The DuckDuckGo package was renamed.**
`duckduckgo-search` became `ddgs`. The old import raises `ImportError` or a
rename warning:

```python
from duckduckgo_search import DDGS   # ❌ old, broken
from ddgs import DDGS                # ✅ current
```

Also, `max_results` is now keyword-only — `DDGS().text("query", 5)` errors out.

**2. The usual Groq models no longer exist.**
Groq deprecated `llama-3.3-70b-versatile` and `llama-3.1-8b-instant`, and they
were decommissioned on **16 August 2026**. Requests using them fail. Nearly every
CrewAI + Groq tutorial still uses `llama-3.3-70b-versatile`.

Currently working, set in `research_crew.py`:

| Model | Use it for |
|---|---|
| `groq/openai/gpt-oss-120b` | Default. Better reasoning, better reports. |
| `groq/openai/gpt-oss-20b` | Faster, cheaper on rate limits, thinner output. |

The `groq/` prefix tells LiteLLM (which CrewAI uses under the hood) which
provider to route to. The rest is Groq's own model ID — which is why it looks
odd with two slashes.

Model lineups change. If you get a "model not found" error, check
<https://console.groq.com/docs/models> for what's live and update
`AVAILABLE_MODELS` in `research_crew.py`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: ddgs` | `pip install -r requirements.txt` again, with your venv active. |
| `No GROQ_API_KEY found` | Local: is the file named exactly `.env`? Deployed: check Settings → Secrets. |
| Report is short / says search failed | DuckDuckGo rate-limited you. Wait a minute. It happens more on Streamlit Cloud because DDG throttles cloud IPs. |
| `RateLimitError` from Groq | Free tier limit. Wait 60s, or switch to GPT-OSS 20B. |
| Dependency conflict on deploy | You added `openai` or `litellm` to `requirements.txt`. Remove them — CrewAI pins its own versions. |
| App sleeps after a few days | Normal for the free tier. Open it to wake it. |

---

## How it actually works

```
Your topic
    ↓
Task description  ("search 4 different angles, read the best pages, then write")
    ↓
Agent  ──uses──>  web_search  (DuckDuckGo)
       ──uses──>  read_page   (requests + BeautifulSoup)
    ↓
Groq LLM writes the final markdown
    ↓
Streamlit renders it + download button
```

The agent decides on its own how many times to search and which pages to open.
The `max_iter` setting in `research_crew.py` caps that loop so a confused agent
can't run forever.

**Report quality is controlled almost entirely by the `expected_output` string
in `research_crew.py`, not by the model.** If reports come back vague, edit that
text before reaching for a bigger model — ask for specific numbers, demand a
sources section, set a word count.

---

## Ideas for v2

- Show the agent's live progress in the UI instead of just a spinner.
- Cache results with `@st.cache_data` so the same topic doesn't re-run.
- Add a second agent — a fact-checker that reviews the draft. Change `Crew` to
  two agents and two tasks, keep `Process.sequential`.
- Swap DuckDuckGo for Tavily or Serper (both have free tiers) if DDG
  rate-limiting gets annoying.
