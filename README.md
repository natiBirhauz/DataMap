# DataMap

Interactive World Choropleth Map powered by **Free-to-Use LLMs** and **OpenStreetMap**.

DataMap visualizes global datasets on an interactive world map. Ask any question in plain English (e.g. *"GDP per capita in Europe"*, *"Share of electricity from renewables"*, *"Life expectancy"*, *"Coffee consumption"*), and the AI synthesizes country-level estimates and renders a dynamic colored choropleth map.

---

## Key Features

- **100% Free & Unlimited Usage:** No API key prompts, no daily search limits, no lockouts.
- **Clean Map Display:** Powered by official OpenStreetMap tiles with zero "API KEY REQUIRED" watermarks.
- **Multi-Tier Free LLM Architecture:**
  1. **Tier 1 — Google Gemini (Free Tier):** Up to 1,500 requests/day, 15 RPM using `gemini-2.0-flash` / `gemini-1.5-flash` (`GEMINI_API_KEY`).
  2. **Tier 2 — Groq (Free Tier):** 14,400 requests/day, 30 RPM using `llama-3.3-70b-versatile` / `llama-3.1-8b-instant` (`GROQ_API_KEY`).
  3. **Tier 3 — OpenAI Fallback:** Server-level key fallback if configured (`OPENAI_API_KEY`).
  4. **Tier 4 — Zero-Crash Offline Synthesizer:** Deterministic baseline engine for 80+ ISO countries that guarantees 100% uptime and zero crashes even if external APIs hit rate limits or network issues.

---

## Project Structure

```
DataMap/
├── backend/                  # FastAPI backend
│   ├── main.py               # API endpoints & multi-tier LLM engine
│   ├── test_free_llm.py      # Automated test suite
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment variables template
├── datamap-frontend/         # React + Leaflet frontend
│   ├── src/
│   │   ├── App.js            # Main application & OpenStreetMap layer
│   │   ├── App.css           # Styling
│   │   ├── App.test.js       # Frontend unit test
│   │   └── world.geo.json    # GeoJSON world boundaries
│   └── package.json
└── README.md
```

---

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

*(Optional)* Configure free API keys in `backend/.env`:
```env
GEMINI_API_KEY=your_free_gemini_key_here
GROQ_API_KEY=your_free_groq_key_here
```

### 2. Frontend Setup

```bash
cd datamap-frontend
npm install
npm start
```

### 3. Run Backend Tests

```bash
python backend/test_free_llm.py
```
