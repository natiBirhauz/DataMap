# DataMap 🗺️

Interactive World Choropleth Map Visualizer powered by **Free-to-Use LLMs** and **OpenStreetMap**.

DataMap visualizes global datasets on an interactive world map. Ask any question in plain English (e.g. *"GDP per capita in Europe"*, *"Share of electricity from renewables"*, *"Life expectancy"*, *"Coffee consumption"*), and the AI synthesizes country-level estimates and renders a dynamic colored choropleth map.

---

## ✨ Features

- **100% Free & Unlimited Usage:** No API key modals, no daily search quotas, no user account required to search.
- **Clean Map Display:** Powered by standard OpenStreetMap tiles with zero "API KEY REQUIRED" watermarks.
- **Multi-Tier Free LLM Architecture:**
  1. **Tier 1 — Google Gemini Free Tier:** Up to 1,500 requests/day, 15 RPM using `gemini-2.0-flash` / `gemini-1.5-flash` (`GEMINI_API_KEY`).
  2. **Tier 2 — Groq Free Tier:** 14,400 requests/day, 30 RPM using `llama-3.3-70b-versatile` / `llama-3.1-8b-instant` (`GROQ_API_KEY`).
  3. **Tier 3 — OpenAI Fallback:** Server-level key fallback if configured (`OPENAI_API_KEY`).
  4. **Tier 4 — Zero-Crash Offline Synthesizer:** Deterministic baseline engine for 80+ ISO countries that guarantees 100% uptime and zero crashes even if external APIs hit rate limits or network issues.

---

## 📁 Project Structure

```
DataMap/
├── main.py                   # Root FastAPI entrypoint proxy
├── Procfile                  # Production process definition
├── render.yaml               # Render.com deployment configuration
├── railway.json              # Railway deployment configuration
├── vercel.json               # Vercel deployment configuration
├── package.json              # Root npm scripts (delegates to frontend)
├── requirements.txt          # Python dependencies (UTF-8)
├── backend/                  # Backend application
│   ├── main.py               # Core FastAPI app & multi-tier LLM engine
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

## 🚀 Quick Start (Running Locally)

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Install Dependencies

**Python Dependencies:**
```bash
pip install -r requirements.txt
```

**Frontend Dependencies:**
```bash
cd datamap-frontend
npm install
cd ..
```

---

### 2. Configure Free API Keys (Optional)

Create a `.env` file in `backend/.env` (or set environment variables in your deployment):

```env
# Google AI Studio Free Tier (1,500 req/day, $0 cost)
# Get a free key: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_free_gemini_api_key

# Groq Cloud Free Tier (14,400 req/day, $0 cost)
# Get a free key: https://console.groq.com/keys
GROQ_API_KEY=your_free_groq_api_key
```

*Note: If no keys are configured, DataMap automatically uses its built-in offline data synthesizer for 100% uptime.*

---

### 3. Start the Application

**Terminal 1 — Backend:**
```bash
uvicorn main:app --reload --port 8000
```
*Backend runs on `http://localhost:8000`*

**Terminal 2 — Frontend:**
From the project root:
```bash
# Point to local backend and launch React dev server
npm start
```
*Frontend opens at `http://localhost:3000`*

---

## 🧪 Testing

**Run Backend Tests:**
```bash
python backend/test_free_llm.py
```

**Run Frontend Tests:**
```bash
npm test
```

**Build Frontend Production Bundle:**
```bash
npm run build
```

---

## 🌐 Deployment

### Render (`render.yaml`)
1. Connect your GitHub repository on [Render](https://render.com).
2. Create a Web Service using the repository.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add `GEMINI_API_KEY` or `GROQ_API_KEY` in Environment Variables.

### Vercel / Railway
- **Railway:** Configured via `railway.json`.
- **Vercel:** Configured via `vercel.json` for the frontend build.

---

## 🛡️ License

MIT License
