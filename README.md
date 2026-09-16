# DataMap 🗺️

DataMap is an interactive world map visualizer powered by free-to-use AI and OpenStreetMap.

Ask any global question in plain English (e.g., *"GDP per capita in Europe"*, *"Renewable energy share"*, *"Life expectancy"*, *"Coffee consumption"*), and the application synthesizes country-level estimates and renders a dynamic, color-coded choropleth map in real time.

---

## What It Does

1. **Natural Language Querying:** Type any topic or question about the world.
2. **AI Data Synthesis:** Generates accurate metric estimates across 80+ countries using free LLMs (Google Gemini / Groq) with an offline statistical fallback engine.
3. **Interactive Visualization:** Displays the dataset on an OpenStreetMap world map with color-coded country highlights, hover tooltips, and dynamic legends.

---

## Quick Start

### 1. Backend

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

*(Optional)* Add a free Google Gemini or Groq key in `backend/.env` for live AI generation. If omitted, the built-in offline engine handles all queries.

### 2. Frontend

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.
