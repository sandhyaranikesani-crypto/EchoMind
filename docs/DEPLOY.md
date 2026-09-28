# Deploying EchoMind

The app is a Streamlit front end that talks to two remote APIs (Hindsight Cloud
and Groq), so there is almost nothing heavy to host. Deployment is optional; the
hackathon only requires a live demo, which you can also run locally.

The SQLite demo database is seeded automatically on first load, so a fresh
deploy comes up with data and no manual step.

---

## Option A: Streamlit Community Cloud (recommended, free)

Prerequisite: the repo is already on GitHub
(`sandhyaranikesani-crypto/EchoMind`).

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **Create app** and select this repository and the `main` branch.
3. Set **Main file path** to:
   ```
   ui/app.py
   ```
4. Open **Advanced settings** and choose **Python 3.12** (3.14 lacks some
   prebuilt wheels).
5. In **Secrets**, paste your keys in TOML form:
   ```toml
   HINDSIGHT_API_KEY = "your-hindsight-cloud-key"
   LLM_API_KEY = "your-groq-key"
   # Optional overrides:
   # HINDSIGHT_BASE_URL = "https://api.hindsight.vectorize.io"
   # LLM_MODEL = "openai/gpt-oss-120b"
   ```
   Streamlit exposes these secrets as environment variables, which is exactly
   what `config/settings.py` reads. No code change needed.
6. Click **Deploy**. First build takes a few minutes.
7. When it opens, the database auto-seeds. In the sidebar choose the
   **Hindsight server** backend, click **Seed demo brand memory** once, and
   you are ready to demo.

Notes:
- Never put keys in the repo. `.env` is gitignored; use the Secrets UI instead.
- The container filesystem is ephemeral: the SQLite file resets on restart, but
  it re-seeds automatically. Hindsight memory itself lives in Hindsight Cloud,
  so it persists across restarts.

---

## Option B: Docker (Render, Railway, Fly.io, or self-host)

A `Dockerfile` is included.

```bash
# Build
docker build -t echomind .

# Run (pass secrets as environment variables)
docker run -p 8501:8501 \
  -e HINDSIGHT_API_KEY=your-hindsight-cloud-key \
  -e LLM_API_KEY=your-groq-key \
  echomind
```

Then open http://localhost:8501.

On a PaaS (Render/Railway/Fly), point the service at this repo's Dockerfile and
set `HINDSIGHT_API_KEY` and `LLM_API_KEY` as environment variables in the
platform dashboard. If the platform injects its own `$PORT`, set the start
command to:

```
streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

---

## Post-deploy checklist

- [ ] App loads and dashboard shows both demo brands.
- [ ] Sidebar shows **Memory online: Hindsight server** (keys are set).
- [ ] Recommendation tab shows the Without vs With memory contrast.
- [ ] Watch it learn changes the recommendation after a rejection.
- [ ] Memory tab loads the ledger; switching brands shows a different bank.
