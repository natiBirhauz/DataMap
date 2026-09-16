// src/App.js
import React, { useState, useEffect, useRef } from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from "jwt-decode";
import axios from 'axios';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';
import worldGeoJSON from './world.geo.json';

const GOOGLE_CLIENT_ID = "569893946999-hlv7lda6iquvtn13b3icnf9ldu5o3ici.apps.googleusercontent.com";

// Backend URL: custom env var, localhost for dev, or production Render backend
const BACKEND_URL =
    process.env.REACT_APP_BACKEND_URL ||
    (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? 'http://localhost:8000'
        : 'https://datamap-6vmr.onrender.com');

// --- Map Data Layer ---
const DataLayer = ({ mapData }) => {
    const map = useMap();
    const geoJsonLayerRef = useRef(null);

    useEffect(() => {
        if (geoJsonLayerRef.current) map.removeLayer(geoJsonLayerRef.current);
        if (!mapData || mapData.length === 0) return;

        const dataMap = new Map(mapData.map(item => [item.country_code, item.value]));
        const validValues = mapData.map(item => item.value || 0).filter(isFinite);
        const maxValue = validValues.length > 0 ? Math.max(...validValues) : 0;
        const mapLabel = mapData[0]?.label || 'Value';

        const getColor = (value) => {
            if (value == null || maxValue === 0) return '#BFBFBF';
            const intensity = value / maxValue;
            if (intensity > 0.8) return '#800026';
            if (intensity > 0.6) return '#BD0026';
            if (intensity > 0.4) return '#E31A1C';
            if (intensity > 0.2) return '#FC4E2A';
            return '#FED976';
        };

        const newLayer = L.geoJSON(worldGeoJSON, {
            style: feature => {
                const code = feature.properties.iso_a3;
                const value = dataMap.get(code);
                return {
                    fillColor: getColor(value),
                    weight: 1,
                    opacity: 1,
                    color: '#333',
                    dashArray: '3',
                    fillOpacity: 0.7
                };
            },
            onEachFeature: (feature, layer) => {
                const code = feature.properties.iso_a3;
                const value = dataMap.get(code);
                layer.bindPopup(`<strong>${feature.properties.name}</strong><br/>${mapLabel}: ${value !== undefined ? value.toLocaleString() : 'No data'}`);
            }
        });

        newLayer.addTo(map);
        geoJsonLayerRef.current = newLayer;
    }, [mapData, map]);

    return null;
};

// --- Legend ---
const Legend = ({ mapData }) => {
    if (!mapData || mapData.length === 0) return null;

    const validValues = mapData.map(item => item.value || 0).filter(isFinite);
    const max = validValues.length > 0 ? Math.max(...validValues) : 0;
    const label = mapData[0]?.label || 'Legend';
    if (!max) return null;

    const getColor = (value) => {
        const intensity = value / max;
        if (intensity > 0.8) return '#800026';
        if (intensity > 0.6) return '#BD0026';
        if (intensity > 0.4) return '#E31A1C';
        if (intensity > 0.2) return '#FC4E2A';
        return '#FED976';
    };

    const grades = [0, 0.2, 0.4, 0.6, 0.8].map(p => Math.round(p * max));

    return (
        <div className="legend">
            <h4>{label}</h4>
            {grades.map((grade, idx) => (
                <div key={idx} className="legend-item">
                    <i style={{ background: getColor(grade + 1) }}></i>
                    {grade.toLocaleString()} {grades[idx + 1] ? `– ${grades[idx + 1].toLocaleString()}` : '+'}
                </div>
            ))}
        </div>
    );
};

// --- Main App ---
function App() {
    const [user, setUser] = useState(null);
    const [query, setQuery] = useState('');
    const [mapData, setMapData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSearch = async (e) => {
        e.preventDefault();
        const trimmed = query.trim();
        if (!trimmed || loading) return;

        setLoading(true);
        setError('');

        let fetchedData = null;
        let lastErrorMessage = '';

        const endpoint = `${BACKEND_URL}/api/query/`;
        try {
            console.log(`Querying backend: ${endpoint}`);
            const { data } = await axios.post(endpoint, {
                query: trimmed,
                user_id: user?.sub || null,
            });
            if (Array.isArray(data) && data.length > 0) {
                fetchedData = data;
            }
        } catch (err) {
            console.warn("Backend error:", err.response?.status, err.message);
            lastErrorMessage = err.response?.data?.detail || err.message;
        }

        if (fetchedData && fetchedData.length > 0) {
            setMapData(fetchedData);
        } else {
            setError(lastErrorMessage ? `Error: ${lastErrorMessage}` : "Unable to generate dataset for this query. Please try again.");
        }

        setLoading(false);
    };

    return (
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <div className="app-container">
                <header className="app-header">
                    <h1 className="logo">DataMap</h1>

                    <form className="search-form" onSubmit={handleSearch}>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Ask a question about the world (e.g. GDP, renewable energy, population)..."
                        />
                        <button type="submit" disabled={loading || !query.trim()}>
                            {loading ? 'Analyzing...' : 'Search'}
                        </button>
                    </form>

                    <div className="login-area">
                        {user ? (
                            <div className="user-controls">
                                <span className="welcome-message">Welcome, {user.given_name || 'Explorer'}!</span>
                                <button className="logout-btn" onClick={() => setUser(null)}>Sign out</button>
                            </div>
                        ) : (
                            <GoogleLogin
                                onSuccess={(res) => setUser(jwtDecode(res.credential))}
                                onError={() => console.log('Login Failed')}
                                theme="filled_black"
                                shape="pill"
                            />
                        )}
                    </div>
                </header>

                <main className="map-area">
                    {error && <div className="error-banner">{error}</div>}
                    <MapContainer center={[30, 0]} zoom={2.5} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <DataLayer mapData={mapData} />
                        <Legend mapData={mapData} />
                    </MapContainer>
                </main>
            </div>
        </GoogleOAuthProvider>
    );
}

export default App;
