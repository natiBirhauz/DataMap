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
const BACKEND_URL = "https://datamap-6vmr.onrender.com";
const API_KEY_STORAGE = 'datamap_openai_key';

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
        const mapLabel = mapData[0].label;

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
    const label = mapData[0].label;
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
            <h4>{label || 'Legend'}</h4>
            {grades.map((grade, idx) => (
                <div key={idx} className="legend-item">
                    <i style={{ background: getColor(grade + 1) }}></i>
                    {grade.toLocaleString()} {grades[idx + 1] ? `– ${grades[idx + 1].toLocaleString()}` : '+'}
                </div>
            ))}
        </div>
    );
};

// --- API Key Modal ---
const ApiKeyModal = ({ onClose }) => {
    const [inputKey, setInputKey] = useState(localStorage.getItem(API_KEY_STORAGE) || '');
    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        const trimmed = inputKey.trim();
        if (trimmed) {
            localStorage.setItem(API_KEY_STORAGE, trimmed);
        } else {
            localStorage.removeItem(API_KEY_STORAGE);
        }
        setSaved(true);
        setTimeout(() => {
            setSaved(false);
            onClose();
        }, 800);
    };

    const handleClear = () => {
        setInputKey('');
        localStorage.removeItem(API_KEY_STORAGE);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-box" onClick={e => e.stopPropagation()}>
                <h2>Your OpenAI API Key</h2>
                <p>
                    Your key is stored only in your browser and sent directly to the server for each request.
                    It is never logged or persisted on our end.
                </p>
                <input
                    type="password"
                    className="modal-input"
                    placeholder="sk-..."
                    value={inputKey}
                    onChange={e => setInputKey(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSave()}
                    autoFocus
                />
                <div className="modal-actions">
                    <button className="modal-btn-secondary" onClick={handleClear}>Clear</button>
                    <button className="modal-btn-primary" onClick={handleSave}>
                        {saved ? '✓ Saved!' : 'Save Key'}
                    </button>
                </div>
                <a
                    href="https://platform.openai.com/api-keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="modal-link"
                >
                    Get an API key from OpenAI →
                </a>
            </div>
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
    const [queryLocked, setQueryLocked] = useState(false);
    const [showKeyModal, setShowKeyModal] = useState(false);
    const [hasApiKey, setHasApiKey] = useState(!!localStorage.getItem(API_KEY_STORAGE));

    useEffect(() => {
        const lastQuery = localStorage.getItem('lastQueryDate');
        if (lastQuery) {
            const lastDate = new Date(lastQuery);
            if (lastDate.toDateString() === new Date().toDateString()) {
                setQueryLocked(true);
            }
        }
    }, []);

    const handleModalClose = () => {
        setShowKeyModal(false);
        setHasApiKey(!!localStorage.getItem(API_KEY_STORAGE));
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!user || loading) return;
        if (queryLocked) {
            setError('You can only use this feature once per day.');
            return;
        }

        const apiKey = localStorage.getItem(API_KEY_STORAGE);
        if (!apiKey) {
            setError('Please add your OpenAI API key first using the key icon.');
            setShowKeyModal(true);
            return;
        }

        setLoading(true);
        setError('');
        setMapData([]);

        try {
            const { data } = await axios.post(`${BACKEND_URL}/api/query/`, {
                query,
                user_id: user.sub,
                api_key: apiKey,
            });
            setMapData(data);
            localStorage.setItem('lastQueryDate', new Date().toISOString());
            setQueryLocked(true);
        } catch (err) {
            console.error("Full error object:", err);
            console.error("Response data:", err.response?.data);
            console.error("Response status:", err.response?.status);
            
            const detail = err.response?.data?.detail;
            let errorMsg;
            if (!detail) {
                errorMsg = "Unable to connect to server or no error details returned. Check the browser console for details.";
            } else if (typeof detail === 'string') {
                errorMsg = detail;
            } else if (detail.message) {
                errorMsg = detail.message;
            } else {
                errorMsg = JSON.stringify(detail);
            }
            setError(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <div className="app-container">
                <header className="app-header">
                    <h1 className="logo">DataMap</h1>

                    {user && (
                        <form className="search-form" onSubmit={handleSearch}>
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Ask a question about the world..."
                            />
                            <button type="submit" disabled={loading || queryLocked}>
                                {loading ? 'Analyzing...' : queryLocked ? 'Limit Reached' : 'Search'}
                            </button>
                        </form>
                    )}

                    <div className="login-area">
                        {user ? (
                            <div className="user-controls">
                                <button
                                    className={`key-btn ${hasApiKey ? 'key-btn--active' : 'key-btn--missing'}`}
                                    onClick={() => setShowKeyModal(true)}
                                    title={hasApiKey ? 'API key saved — click to update' : 'No API key — click to add'}
                                    aria-label="Manage OpenAI API key"
                                >
                                    <span className="key-icon">🔑</span>
                                    {hasApiKey ? 'Key saved' : 'Add API key'}
                                </button>
                                <div className="welcome-message">Welcome, {user.given_name}!</div>
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
                            attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>'
                            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                        />
                        <DataLayer mapData={mapData} />
                        <Legend mapData={mapData} />
                    </MapContainer>
                </main>

                {showKeyModal && <ApiKeyModal onClose={handleModalClose} />}
            </div>
        </GoogleOAuthProvider>
    );
}

export default App;
