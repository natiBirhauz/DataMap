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
const BACKEND_URL = "http://localhost:8000";

const DataLayer = ({ mapData }) => {
    const map = useMap();
    const geoJsonLayerRef = useRef(null);

    useEffect(() => {
        if (geoJsonLayerRef.current) {
            map.removeLayer(geoJsonLayerRef.current);
        }

        if (!mapData || mapData.length === 0) {
            return;
        }

        const dataMap = new Map(mapData.map(item => [item.country_code, item.value]));
        const validValues = mapData.map(item => item.value || 0).filter(v => isFinite(v));
        const maxValue = validValues.length > 0 ? Math.max(...validValues) : 0;
        const mapLabel = mapData[0].label;

        const getColor = (value) => {
            if (value === null || value === undefined || maxValue === 0) return '#BFBFBF';
            const intensity = value / maxValue;
            if (intensity > 0.8) return '#800026';
            if (intensity > 0.6) return '#BD0026';
            if (intensity > 0.4) return '#E31A1C';
            if (intensity > 0.2) return '#FC4E2A';
            return '#FED976';
        };

        const getCountryCode = (feature) => feature.properties.iso_a3;

        const newLayer = L.geoJSON(worldGeoJSON, {
            style: (feature) => {
                const code = getCountryCode(feature);
                const value = dataMap.get(code);
                return {
                    fillColor: getColor(value),
                    weight: 1, opacity: 1, color: '#333', dashArray: '3', fillOpacity: 0.7
                };
            },
            onEachFeature: (feature, layer) => {
                const code = getCountryCode(feature);
                const value = dataMap.get(code);
                layer.bindPopup(`<strong>${feature.properties.name}</strong><br/>${mapLabel}: ${value !== undefined ? value.toLocaleString() : 'No data'}`);
            }
        });

        newLayer.addTo(map);
        geoJsonLayerRef.current = newLayer;

    }, [mapData, map]);

    return null;
};

const Legend = ({ mapData }) => {
    if (!mapData || mapData.length === 0) return null;
    const validValues = mapData.map(item => item.value || 0).filter(v => isFinite(v));
    const max = validValues.length > 0 ? Math.max(...validValues) : 0;
    const label = mapData[0].label;
    if (!max) return null;

    const getColor = (value) => {
        const intensity = value / max;
        if (intensity > 0.8) return '#800026'; if (intensity > 0.6) return '#BD0026'; if (intensity > 0.4) return '#E31A1C'; if (intensity > 0.2) return '#FC4E2A'; return '#FED976';
    };
    const grades = [0, 0.2, 0.4, 0.6, 0.8].map(p => Math.round(p * max));

    return (
        <div className="legend">
            <h4>{label || 'Legend'}</h4>
            {grades.map((grade, index) => (
                <div key={index} className="legend-item">
                    <i style={{ background: getColor(grade + 1) }}></i>
                    {grade.toLocaleString()} {grades[index + 1] ? `– ${grades[index + 1].toLocaleString()}` : '+'}
                </div>
            ))}
        </div>
    );
};

function App() {
    const [user, setUser] = useState(null);
    const [query, setQuery] = useState('');
    const [mapData, setMapData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [queryLocked, setQueryLocked] = useState(false);

    useEffect(() => {
        const lastQuery = localStorage.getItem('lastQueryDate');
        if (lastQuery) {
            const lastDate = new Date(lastQuery);
            const now = new Date();
            if (lastDate.toDateString() === now.toDateString()) {
                setQueryLocked(true);
            }
        }
    }, []);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!user || loading) return;

        if (queryLocked) {
            setError('You can only use this feature once per day.');
            return;
        }

        setLoading(true);
        setError('');
        setMapData([]);

        try {
            const response = await axios.post(`${BACKEND_URL}/api/query`, { query, user_id: user.sub });
            console.log("Final data check:", JSON.stringify(response.data, null, 2));
            setMapData(response.data);
            localStorage.setItem('lastQueryDate', new Date().toISOString());
            setQueryLocked(true);
        } catch (err) {
            const errorMsg = err.response?.data?.detail || "An unexpected error occurred.";
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
                            <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ask a question about the world..." />
                            <button type="submit" disabled={loading || queryLocked}>
                                {loading ? 'Analyzing...' : queryLocked ? 'Limit Reached' : 'Search'}
                            </button>
                        </form>
                    )}
                    <div className="login-area">
                        {user ? (
                            <div className="welcome-message">Welcome, {user.given_name}!</div>
                        ) : (
                            <GoogleLogin onSuccess={(res) => setUser(jwtDecode(res.credential))} onError={() => console.log('Login Failed')} theme="filled_black" shape="pill" />
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
            </div>
        </GoogleOAuthProvider>
    );
}

export default App;