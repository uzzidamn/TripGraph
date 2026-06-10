# Task 4: Frontend UI & Visualization — Mini Spec

> **Owner**: Task 4 assignee
> **Priority**: P1 — Can start Day 1 with mock data; connect to real API later
> **Estimated effort**: 12-16 days
> **Reference**: Read `MASTER_SPEC.md` (same folder) for full project context

> [!NOTE]
> This mini-spec is **extra-detailed** because the team may be less experienced with JavaScript/React. Every step includes setup commands, file templates, and explanations.

---

## Overview

Your job is to build the **React frontend** that lets users interact with TripGraph AI. Users paste group chat messages, see extracted preferences, view itinerary options with a timeline, see the route on a Leaflet map, view cost breakdowns, and simulate delays.

The frontend communicates with the Python backend via HTTP (JSON). You do NOT need to know Python — you only need to call REST API endpoints and render the responses.

---

## What You Deliver

| # | Deliverable | File |
|---|------------|------|
| 1 | React + Vite app setup | `frontend/package.json`, `vite.config.js`, `index.html` |
| 2 | App layout | `src/App.jsx`, `src/main.jsx` |
| 3 | Global styles | `src/index.css` |
| 4 | API client | `src/api/tripApi.js` |
| 5 | Chat Room component | `src/components/chat/ChatRoom.jsx` |
| 6 | Chat Message component | `src/components/chat/ChatMessage.jsx` |
| 7 | Extracted Preferences | `src/components/preferences/ExtractedPreferences.jsx` |
| 8 | Itinerary Options | `src/components/itinerary/ItineraryOptions.jsx` |
| 9 | Itinerary Timeline | `src/components/itinerary/ItineraryTimeline.jsx` |
| 10 | Calendar View | `src/components/itinerary/CalendarView.jsx` |
| 11 | Map View (Leaflet) | `src/components/map/MapView.jsx` |
| 12 | Cost Breakdown | `src/components/cost/CostBreakdown.jsx` |
| 13 | Delay Simulator | `src/components/delay/DelaySimulator.jsx` |
| 14 | Layout components | `src/components/layout/Header.jsx`, `AppLayout.jsx` |
| 15 | Custom hook | `src/hooks/useItinerary.js` |

---

## Step-by-Step Instructions

### Step 1: Create React App with Vite

```bash
# From the project root (TripGraph/)
npm create vite@latest frontend -- --template react
cd frontend
npm install

# Install dependencies
npm install axios react-leaflet leaflet react-icons

# Start dev server (should open http://localhost:5173)
npm run dev
```

> **What is Vite?** Vite is a fast build tool for modern web apps. It replaces Create React App (which is deprecated). It gives you instant hot-reload — save a file and see changes immediately in the browser.

### Step 2: Fix Leaflet CSS Import

Leaflet needs its CSS loaded. Add this to `index.html` inside `<head>`:

```html
<!-- In frontend/index.html -->
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TripGraph AI — Group Travel Planner</title>
  <meta name="description" content="AI-powered group travel planner that converts chat to itineraries" />
  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <!-- Google Font -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
</head>
```

### Step 3: Create `src/index.css` — Global Design System

```css
/* === TripGraph AI Design System === */

:root {
  /* Color palette */
  --color-bg: #0f1117;
  --color-surface: #1a1d2e;
  --color-surface-hover: #242842;
  --color-border: #2a2e45;
  --color-text: #e4e6f0;
  --color-text-muted: #8b8fa3;
  --color-primary: #6c5ce7;
  --color-primary-hover: #7d6ff0;
  --color-accent: #00cec9;
  --color-success: #00b894;
  --color-warning: #fdcb6e;
  --color-danger: #e17055;

  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 2rem;

  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-2xl: 3rem;

  /* Border radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.4);

  /* Transitions */
  --transition: all 0.2s ease;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family);
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
  min-height: 100vh;
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--color-bg); }
::-webkit-scrollbar-thumb { background: var(--color-border); border-radius: var(--radius-full); }
::-webkit-scrollbar-thumb:hover { background: var(--color-text-muted); }

/* Utility classes */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  transition: var(--transition);
}
.card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: var(--transition);
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}
.btn-primary:hover {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 92, 231, 0.4);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
}
.badge-success { background: rgba(0, 184, 148, 0.15); color: var(--color-success); }
.badge-warning { background: rgba(253, 203, 110, 0.15); color: var(--color-warning); }
.badge-danger  { background: rgba(225, 112, 85, 0.15);  color: var(--color-danger); }

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 700;
  margin-bottom: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

/* Loading spinner */
.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

### Step 4: Create `src/api/tripApi.js` — API Client

```javascript
/**
 * API client for TripGraph backend.
 * All API calls go through this file.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000, // 2 minutes (LLM calls can be slow on free tier)
});

/**
 * Parse group chat messages and extract constraints.
 * @param {string[]} chatMessages - Array of chat message strings
 * @returns {Promise<{extracted_constraints, missing_fields, assumptions, conflict_report}>}
 */
export async function parseChat(chatMessages) {
  const response = await api.post('/api/parse-chat', {
    chat_messages: chatMessages,
  });
  return response.data;
}

/**
 * Generate itinerary from constraints.
 * @param {object} constraints - Extracted constraints object
 * @returns {Promise<{recommended_itinerary, alternatives, timeline, map_points, cost_breakdown, explanation}>}
 */
export async function generateItinerary(constraints) {
  const response = await api.post('/api/generate-itinerary', {
    constraints,
  });
  return response.data;
}

/**
 * Simulate a delay and get updated itinerary.
 * @param {string} delayType - e.g. "departure_delay"
 * @param {number} delayMinutes - e.g. 90
 * @param {object} constraints - Current constraints
 * @param {object} selectedItinerary - Current itinerary
 * @returns {Promise<{updated_itinerary, changes, explanation}>}
 */
export async function simulateDelay(delayType, delayMinutes, constraints, selectedItinerary) {
  const response = await api.post('/api/simulate-delay', {
    delay_type: delayType,
    delay_minutes: delayMinutes,
    constraints,
    selected_itinerary: selectedItinerary,
  });
  return response.data;
}
```

### Step 5: Create `src/hooks/useItinerary.js` — State Management Hook

```javascript
/**
 * Custom hook to manage the itinerary planning flow state.
 * Centralizes all API calls and state transitions.
 */
import { useState, useCallback } from 'react';
import { parseChat, generateItinerary, simulateDelay } from '../api/tripApi';

export function useItinerary() {
  const [step, setStep] = useState('chat'); // chat | preferences | itinerary | delay
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Data state
  const [chatMessages, setChatMessages] = useState([]);
  const [constraints, setConstraints] = useState(null);
  const [itineraryData, setItineraryData] = useState(null);
  const [delayResult, setDelayResult] = useState(null);

  const handleParseChat = useCallback(async (messages) => {
    setLoading(true);
    setError(null);
    try {
      const result = await parseChat(messages);
      setChatMessages(messages);
      setConstraints(result);
      setStep('preferences');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleGenerateItinerary = useCallback(async () => {
    if (!constraints?.extracted_constraints) return;
    setLoading(true);
    setError(null);
    try {
      const result = await generateItinerary(constraints.extracted_constraints);
      setItineraryData(result);
      setStep('itinerary');
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [constraints]);

  const handleSimulateDelay = useCallback(async (delayType, delayMinutes) => {
    if (!itineraryData?.recommended_itinerary) return;
    setLoading(true);
    setError(null);
    try {
      const result = await simulateDelay(
        delayType,
        delayMinutes,
        constraints.extracted_constraints,
        itineraryData.recommended_itinerary,
      );
      setDelayResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [constraints, itineraryData]);

  const resetFlow = useCallback(() => {
    setStep('chat');
    setChatMessages([]);
    setConstraints(null);
    setItineraryData(null);
    setDelayResult(null);
    setError(null);
  }, []);

  return {
    step, loading, error,
    chatMessages, constraints, itineraryData, delayResult,
    handleParseChat, handleGenerateItinerary, handleSimulateDelay, resetFlow,
  };
}
```

### Step 6: Create `src/App.jsx` — Root Component

```jsx
import { useItinerary } from './hooks/useItinerary';
import Header from './components/layout/Header';
import ChatRoom from './components/chat/ChatRoom';
import ExtractedPreferences from './components/preferences/ExtractedPreferences';
import ItineraryTimeline from './components/itinerary/ItineraryTimeline';
import ItineraryOptions from './components/itinerary/ItineraryOptions';
import MapView from './components/map/MapView';
import CostBreakdown from './components/cost/CostBreakdown';
import DelaySimulator from './components/delay/DelaySimulator';
import CalendarView from './components/itinerary/CalendarView';

function App() {
  const {
    step, loading, error,
    chatMessages, constraints, itineraryData, delayResult,
    handleParseChat, handleGenerateItinerary, handleSimulateDelay, resetFlow,
  } = useItinerary();

  return (
    <div className="app">
      <Header onReset={resetFlow} />

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => {}}>Dismiss</button>
        </div>
      )}

      <main className="app-main">
        {/* Left Column: Chat + Preferences */}
        <section className="app-sidebar">
          <ChatRoom
            onSubmit={handleParseChat}
            loading={loading}
            disabled={step !== 'chat'}
            messages={chatMessages}
          />
          {constraints && (
            <ExtractedPreferences
              constraints={constraints}
              onGenerate={handleGenerateItinerary}
              loading={loading}
            />
          )}
        </section>

        {/* Right Column: Results */}
        <section className="app-content">
          {itineraryData && (
            <>
              <ItineraryOptions
                recommended={itineraryData.recommended_itinerary}
                alternatives={itineraryData.alternatives}
                explanation={itineraryData.explanation}
              />
              <div className="app-grid">
                <ItineraryTimeline timeline={itineraryData.timeline} />
                <MapView mapPoints={itineraryData.map_points} />
              </div>
              <div className="app-grid">
                <CostBreakdown costData={itineraryData.cost_breakdown} />
                <CalendarView timeline={itineraryData.timeline} />
              </div>
              <DelaySimulator
                onSimulate={handleSimulateDelay}
                result={delayResult}
                loading={loading}
              />
            </>
          )}

          {!itineraryData && step === 'chat' && (
            <div className="empty-state">
              <h2>🗺️ Plan Your Group Trip</h2>
              <p>Paste your group chat on the left to get started.</p>
            </div>
          )}

          {loading && (
            <div className="loading-overlay">
              <div className="spinner" />
              <p>AI is planning your trip...</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
```

Add these layout styles to `index.css`:

```css
/* App Layout */
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: var(--space-lg);
  padding: var(--space-lg);
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
  flex: 1;
}

.app-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.app-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.app-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  text-align: center;
  color: var(--color-text-muted);
}

.empty-state h2 {
  font-size: var(--font-size-2xl);
  margin-bottom: var(--space-md);
  color: var(--color-text);
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-2xl);
  color: var(--color-text-muted);
}

.error-banner {
  background: rgba(225, 112, 85, 0.1);
  border: 1px solid var(--color-danger);
  padding: var(--space-sm) var(--space-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--color-danger);
}

@media (max-width: 1024px) {
  .app-main { grid-template-columns: 1fr; }
  .app-grid { grid-template-columns: 1fr; }
}
```

### Step 7: Create Components

Below are **starter templates** for each component. Build on these.

#### `components/layout/Header.jsx`
```jsx
export default function Header({ onReset }) {
  return (
    <header className="header">
      <div className="header-brand">
        <span className="header-logo">🗺️</span>
        <h1>TripGraph AI</h1>
        <span className="badge badge-success">v0.1</span>
      </div>
      <button className="btn btn-primary" onClick={onReset}>New Trip</button>
      <style>{`
        .header {
          display: flex; align-items: center; justify-content: space-between;
          padding: var(--space-md) var(--space-xl);
          background: var(--color-surface);
          border-bottom: 1px solid var(--color-border);
        }
        .header-brand { display: flex; align-items: center; gap: var(--space-sm); }
        .header-brand h1 { font-size: var(--font-size-xl); font-weight: 700; }
        .header-logo { font-size: 1.5rem; }
      `}</style>
    </header>
  );
}
```

#### `components/chat/ChatRoom.jsx`
```jsx
import { useState } from 'react';

export default function ChatRoom({ onSubmit, loading, disabled, messages }) {
  const [input, setInput] = useState('');

  // Default sample chat for quick testing
  const sampleChat = `Ujjwal: Let's do a weekend trip from Gurugram
Aman: Budget under 15k per person
Priya: Mountains please, not Jaipur
Meenal: No night driving
Kushagra: I want rafting and good cafes
Ujjwal: We need to be back by Monday morning`;

  const handleSubmit = () => {
    const text = input.trim() || sampleChat;
    const msgs = text.split('\n').filter(line => line.trim());
    onSubmit(msgs);
  };

  return (
    <div className="card">
      <h3 className="section-title">💬 Group Chat</h3>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={sampleChat}
        rows={10}
        disabled={disabled || loading}
        style={{
          width: '100%',
          background: 'var(--color-bg)',
          color: 'var(--color-text)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-md)',
          fontFamily: 'var(--font-family)',
          fontSize: 'var(--font-size-sm)',
          resize: 'vertical',
        }}
      />
      <button
        className="btn btn-primary"
        onClick={handleSubmit}
        disabled={loading || disabled}
        style={{ marginTop: 'var(--space-md)', width: '100%' }}
      >
        {loading ? <><div className="spinner" /> Analyzing...</> : '🔍 Parse Chat'}
      </button>

      {messages.length > 0 && (
        <div style={{ marginTop: 'var(--space-md)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
          ✅ {messages.length} messages parsed
        </div>
      )}
    </div>
  );
}
```

#### `components/preferences/ExtractedPreferences.jsx`
```jsx
export default function ExtractedPreferences({ constraints, onGenerate, loading }) {
  const c = constraints?.extracted_constraints || {};
  const missing = constraints?.missing_fields || [];
  const assumptions = constraints?.assumptions || {};

  const items = [
    { label: 'Origin', value: c.origin },
    { label: 'Destination Type', value: c.destination_type },
    { label: 'Budget/Person', value: c.budget_per_person ? `₹${c.budget_per_person.toLocaleString()}` : null },
    { label: 'Night Driving', value: c.avoid_night_driving ? '❌ Avoided' : '✅ Allowed' },
    { label: 'Must Include', value: c.must_include?.join(', ') },
    { label: 'Return By', value: c.return_deadline },
    { label: 'Hotel Tier', value: c.hotel_tier },
    { label: 'Group Size', value: c.group_size },
  ].filter(item => item.value);

  return (
    <div className="card">
      <h3 className="section-title">📋 Extracted Preferences</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
        {items.map(item => (
          <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', padding: 'var(--space-xs) 0', borderBottom: '1px solid var(--color-border)' }}>
            <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>{item.label}</span>
            <span style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>{item.value}</span>
          </div>
        ))}
      </div>

      {Object.keys(assumptions).length > 0 && (
        <div style={{ marginTop: 'var(--space-md)', padding: 'var(--space-sm)', background: 'rgba(108, 92, 231, 0.1)', borderRadius: 'var(--radius-sm)', fontSize: 'var(--font-size-xs)' }}>
          <strong>Assumptions:</strong> {Object.entries(assumptions).map(([k, v]) => `${k}: ${v}`).join(' | ')}
        </div>
      )}

      <button
        className="btn btn-primary"
        onClick={onGenerate}
        disabled={loading || missing.length > 0}
        style={{ marginTop: 'var(--space-lg)', width: '100%' }}
      >
        {loading ? <><div className="spinner" /> Generating...</> : '✨ Generate Itinerary'}
      </button>
    </div>
  );
}
```

#### `components/map/MapView.jsx` — Leaflet Integration

```jsx
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';

// Fix Leaflet default icon issue with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Fallback points if API returns empty
const FALLBACK_POINTS = [
  { lat: 28.4595, lng: 77.0266, label: 'Gurugram', type: 'origin' },
  { lat: 30.0869, lng: 78.2676, label: 'Rishikesh', type: 'destination' },
];

export default function MapView({ mapPoints = [] }) {
  const points = mapPoints.length > 0 ? mapPoints : FALLBACK_POINTS;
  const center = points.length > 0 ? [points[0].lat, points[0].lng] : [28.5, 77.5];
  const positions = points.map(p => [p.lat, p.lng]);

  // Color markers by type
  const getIcon = (type) => {
    const colors = {
      origin: '#6c5ce7',
      destination: '#00cec9',
      hotel: '#fdcb6e',
      activity: '#e17055',
      restaurant: '#00b894',
      waypoint: '#8b8fa3',
    };
    const color = colors[type] || '#6c5ce7';
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="background:${color};width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });
  };

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <h3 className="section-title" style={{ padding: 'var(--space-lg) var(--space-lg) 0' }}>🗺️ Route Map</h3>
      <div style={{ height: 400 }}>
        <MapContainer center={center} zoom={7} style={{ height: '100%', width: '100%', borderRadius: '0 0 var(--radius-lg) var(--radius-lg)' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; OpenStreetMap contributors &copy; CARTO'
          />
          {points.map((point, i) => (
            <Marker key={i} position={[point.lat, point.lng]} icon={getIcon(point.type)}>
              <Popup>
                <strong>{point.label}</strong><br />
                <span style={{ textTransform: 'capitalize' }}>{point.type}</span>
              </Popup>
            </Marker>
          ))}
          {positions.length > 1 && (
            <Polyline positions={positions} color="#6c5ce7" weight={3} opacity={0.7} dashArray="8 8" />
          )}
        </MapContainer>
      </div>
    </div>
  );
}
```

#### `components/itinerary/ItineraryTimeline.jsx`
```jsx
export default function ItineraryTimeline({ timeline = [] }) {
  const typeIcons = {
    travel: '🚗', meal: '🍽️', hotel: '🏨', activity: '🎯',
    rest: '😴', sightseeing: '📸', return: '🏠',
  };

  const typeColors = {
    travel: 'var(--color-primary)', meal: 'var(--color-success)',
    hotel: 'var(--color-warning)', activity: 'var(--color-danger)',
    rest: 'var(--color-text-muted)', sightseeing: 'var(--color-accent)',
    return: 'var(--color-primary)',
  };

  // Group by day
  const days = {};
  timeline.forEach(event => {
    const day = event.day || 1;
    if (!days[day]) days[day] = [];
    days[day].push(event);
  });

  return (
    <div className="card">
      <h3 className="section-title">📅 Timeline</h3>
      {Object.entries(days).map(([day, events]) => (
        <div key={day} style={{ marginBottom: 'var(--space-lg)' }}>
          <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-accent)', marginBottom: 'var(--space-sm)' }}>
            Day {day}
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)', borderLeft: '2px solid var(--color-border)', paddingLeft: 'var(--space-lg)', marginLeft: 'var(--space-sm)' }}>
            {events.map((event, i) => (
              <div key={i} style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start', padding: 'var(--space-sm) 0' }}>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', minWidth: 90, fontFamily: 'monospace' }}>
                  {event.start_time} – {event.end_time}
                </span>
                <span style={{ fontSize: '1.1rem' }}>{typeIcons[event.type] || '📍'}</span>
                <div>
                  <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 500 }}>{event.title}</div>
                  {event.cost && (
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>₹{event.cost}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      {timeline.length === 0 && (
        <p style={{ color: 'var(--color-text-muted)', textAlign: 'center' }}>No timeline data yet</p>
      )}
    </div>
  );
}
```

#### `components/cost/CostBreakdown.jsx`
```jsx
export default function CostBreakdown({ costData = {} }) {
  const items = Object.entries(costData).filter(([k]) => k !== 'total' && k !== 'budget_limit');
  const total = costData.total || items.reduce((sum, [, v]) => sum + (v || 0), 0);
  const budget = costData.budget_limit;

  return (
    <div className="card">
      <h3 className="section-title">💰 Cost Breakdown</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
        {items.map(([label, value]) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: 'var(--space-xs) 0', borderBottom: '1px solid var(--color-border)' }}>
            <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)', textTransform: 'capitalize' }}>
              {label.replace(/_/g, ' ')}
            </span>
            <span style={{ fontWeight: 500, fontSize: 'var(--font-size-sm)' }}>₹{(value || 0).toLocaleString()}</span>
          </div>
        ))}
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: 'var(--space-sm) 0', fontWeight: 700, fontSize: 'var(--font-size-base)', borderTop: '2px solid var(--color-primary)' }}>
          <span>Total / Person</span>
          <span>₹{total.toLocaleString()}</span>
        </div>
        {budget && (
          <div style={{ textAlign: 'right' }}>
            <span className={`badge ${total <= budget ? 'badge-success' : 'badge-danger'}`}>
              {total <= budget ? '✅ Within Budget' : '⚠️ Over Budget'}
              {' (limit: ₹' + budget.toLocaleString() + ')'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
```

#### `components/delay/DelaySimulator.jsx`
```jsx
import { useState } from 'react';

export default function DelaySimulator({ onSimulate, result, loading }) {
  const [delayType, setDelayType] = useState('departure_delay');
  const [delayMinutes, setDelayMinutes] = useState(90);

  const delayTypes = [
    { value: 'departure_delay', label: '🚗 Departure Delay' },
    { value: 'traffic_delay', label: '🚦 Traffic Delay' },
    { value: 'activity_delay', label: '🎯 Activity Delay' },
  ];

  return (
    <div className="card">
      <h3 className="section-title">⏱️ Delay Simulator</h3>
      <div style={{ display: 'flex', gap: 'var(--space-md)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div>
          <label style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Delay Type</label>
          <select value={delayType} onChange={e => setDelayType(e.target.value)}
            style={{ display: 'block', padding: 'var(--space-sm)', background: 'var(--color-bg)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', marginTop: 4 }}>
            {delayTypes.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div>
          <label style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Minutes</label>
          <input type="number" value={delayMinutes} onChange={e => setDelayMinutes(+e.target.value)} min={15} max={300} step={15}
            style={{ display: 'block', padding: 'var(--space-sm)', background: 'var(--color-bg)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', width: 80, marginTop: 4 }} />
        </div>
        <button className="btn btn-primary" onClick={() => onSimulate(delayType, delayMinutes)} disabled={loading}>
          {loading ? 'Replanning...' : '⚡ Simulate'}
        </button>
      </div>

      {result && (
        <div style={{ marginTop: 'var(--space-lg)' }}>
          <h4 style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-warning)', marginBottom: 'var(--space-sm)' }}>Changes Made:</h4>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
            {(result.changes || []).map((change, i) => (
              <li key={i} style={{ fontSize: 'var(--font-size-sm)', padding: 'var(--space-xs) var(--space-sm)', background: 'rgba(253, 203, 110, 0.1)', borderRadius: 'var(--radius-sm)' }}>
                ↳ {change}
              </li>
            ))}
          </ul>
          {result.explanation && (
            <p style={{ marginTop: 'var(--space-md)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
              {result.explanation}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
```

> **Remaining components** (`ItineraryOptions.jsx`, `CalendarView.jsx`): Follow the same patterns above. `ItineraryOptions` shows the recommended plan and alternatives as cards. `CalendarView` renders a day/hour grid.

---

## Mock Data for Early Development

Before the API is ready, import mock data directly to build and test your components:

```javascript
// src/mockData.js — use this during development
export const mockConstraints = {
  extracted_constraints: {
    origin: "Gurugram", destination_type: "mountains", budget_per_person: 15000,
    avoid_night_driving: true, must_include: ["rafting", "cafes"],
    return_deadline: "Monday morning", hotel_tier: "comfort", group_size: 4,
  },
  missing_fields: [],
  assumptions: { group_size: "4 (default)" },
  conflict_report: { conflicts: [] },
};

export const mockItinerary = {
  recommended_itinerary: {
    route: "Gurugram to Rishikesh", tier: "comfort", total_cost_per_person: 10275,
  },
  alternatives: [
    { route: "Gurugram to Tirthan", tier: "budget", total_cost_per_person: 14800, status: "warning" },
    { route: "Gurugram to Jaipur", tier: "comfort", total_cost_per_person: 9500, status: "rejected", reason: "Not mountains" },
  ],
  timeline: [
    { day: 1, start_time: "06:00", end_time: "09:00", title: "Drive from Gurugram", type: "travel" },
    { day: 1, start_time: "09:00", end_time: "09:45", title: "Breakfast at Highway Stop", type: "meal" },
    { day: 1, start_time: "09:45", end_time: "13:00", title: "Continue to Rishikesh", type: "travel" },
    { day: 1, start_time: "14:00", end_time: "15:00", title: "Hotel check-in", type: "hotel" },
    { day: 1, start_time: "16:30", end_time: "17:30", title: "Riverside Cafe", type: "meal" },
    { day: 1, start_time: "18:30", end_time: "20:00", title: "Ganga Aarti", type: "activity" },
    { day: 2, start_time: "09:00", end_time: "12:00", title: "River Rafting", type: "activity", cost: 1800 },
    { day: 2, start_time: "15:00", end_time: "21:30", title: "Return to Gurugram", type: "travel" },
  ],
  map_points: [
    { lat: 28.4595, lng: 77.0266, label: "Gurugram", type: "origin" },
    { lat: 29.0281, lng: 77.0474, label: "Murthal Breakfast", type: "waypoint" },
    { lat: 30.0869, lng: 78.2676, label: "Rishikesh", type: "destination" },
    { lat: 30.0872, lng: 78.2680, label: "Riverside Hotel", type: "hotel" },
    { lat: 30.1256, lng: 78.3152, label: "Rafting Point", type: "activity" },
  ],
  cost_breakdown: {
    transport: 2375, hotel: 2100, food: 2000, activities: 1800, miscellaneous: 2000, total: 10275, budget_limit: 15000,
  },
  explanation: "This itinerary was selected because it stays within ₹15,000 budget, avoids night driving...",
};
```

In `App.jsx`, you can temporarily use:
```javascript
// import { mockConstraints, mockItinerary } from './mockData';
// Then pass these directly to components instead of calling the API
```

---

## Testing Checklist

- [ ] `npm run dev` starts without errors on `http://localhost:5173`
- [ ] ChatRoom accepts text input and parses on submit
- [ ] ExtractedPreferences displays constraint key-value pairs
- [ ] ItineraryTimeline renders day-grouped events
- [ ] MapView shows Leaflet map with markers and polyline
- [ ] CostBreakdown shows itemized costs with budget badge
- [ ] DelaySimulator triggers simulation and shows changes
- [ ] Layout is responsive (works on narrow screens)
- [ ] API calls work when backend is running (CORS passes)
- [ ] Dark theme looks polished (no white backgrounds, no default fonts)

---

## Coordination with Other Tasks

| You need from | What |
|--------------|------|
| Task 3 (Backend API) | API endpoint URLs and response JSON shapes |
| Task 3 (Backend API) | CORS enabled for `http://localhost:5173` |

| Others need from you | What |
|---------------------|------|
| Nobody — you are the final consumer | — |

> **Start with mock data immediately.** Build all components with mock data first. Connect to real API later — just swap `mockData` imports for actual `tripApi.js` calls.

---

## Git Workflow

```bash
git checkout -b bucket-4/react-vite-setup
# npm create vite, install deps, index.css
git commit -m "Task 4: React + Vite setup with design system"

git checkout -b bucket-4/chat-preferences
# ChatRoom, ExtractedPreferences
git commit -m "Task 4: Chat and preferences components"

git checkout -b bucket-4/itinerary-views
# Timeline, ItineraryOptions, CalendarView
git commit -m "Task 4: Itinerary display components"

git checkout -b bucket-4/map-leaflet
# MapView with Leaflet
git commit -m "Task 4: Leaflet map integration"

git checkout -b bucket-4/delay-cost
# CostBreakdown, DelaySimulator
git commit -m "Task 4: Cost breakdown and delay simulator"
```
