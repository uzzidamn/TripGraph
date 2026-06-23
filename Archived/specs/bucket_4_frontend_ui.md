# Bucket 4: Frontend UI & Visualization — LLM-Ready Spec

> **Generated for**: Distributed LLM execution (Claude / Gemini session)
> **Priority**: P1 — Can start immediately with mock data (no backend needed)
> **Reference**: This spec is self-contained. You may also read `specs/MASTER_SPEC.md` for full project context.

---

## Section A — Project Context

**TripGraph AI** is a GenAI-agentic group travel planner that converts WhatsApp-style group chat into structured, constraint-aware itineraries. It uses a Neo4j knowledge graph, a LangGraph agentic pipeline, a deterministic Python planning engine, and a React frontend.

**Your role (Bucket 4):** Build the **React frontend** — a polished, modern, dark-themed single-page application with smooth animations. Users paste group chat messages, see extracted preferences, view itinerary options with an interactive timeline, see the route on a Leaflet map with animated polylines, view animated cost breakdowns, and simulate delays. **The UI is the face of this project. It must be excellent.**

---

## Section B — 🔒 Frozen Interface Contracts

### B.1 API Endpoints

**Base URL:** `http://localhost:8000` (from `VITE_API_URL` in `.env`)

#### POST `/api/parse-chat`
**Request:**
```typescript
interface ParseChatRequest {
  chat_messages: string[];
}
```
**Response:**
```typescript
interface ParseChatResponse {
  extracted_constraints: {
    origin: string | null;
    destination: string | null;
    destination_type: string | null;
    budget_per_person: number | null;
    dates: string | null;
    trip_duration: string | null;
    transport_preference: string[];
    avoid_night_driving: boolean;
    must_include: string[];
    return_deadline: string | null;
    hotel_tier: string | null;
    risk_tolerance: string | null;
    group_size: number | null;
    special_requirements: string[];
  };
  missing_fields: string[];
  assumptions: Record<string, string>;
  conflict_report: {
    conflicts: Array<{field1: string; field2: string; reason: string}>;
  };
}
```

#### POST `/api/generate-itinerary`
**Request:**
```typescript
interface GenerateItineraryRequest {
  constraints: Record<string, any>;
}
```
**Response:**
```typescript
interface ItineraryResponse {
  recommended_itinerary: {
    route: { route_id: string; origin: string; destination: string; distance_km: number };
    transport: { mode: string; cost_total: number };
    hotel: { name: string; price_per_night: number };
    activities: Array<{ name: string; cost_per_person: number }>;
    total_cost_per_person: number;
    cost_breakdown: CostBreakdown;
  } | null;
  alternatives: any[];
  validation_report: {
    is_valid: boolean;
    hard_constraint_violations: string[];
    soft_constraint_warnings: string[];
  };
  score_breakdown: {
    preference_match: number;
    budget_efficiency: number;
    comfort: number;
    scenic: number;
    fatigue: number;
    risk: number;
    final_score: number;
  };
  timeline: TimelineEvent[];
  map_points: MapPoint[];
  cost_breakdown: CostBreakdown;
  explanation: string;
}

interface TimelineEvent {
  day: number;
  start_time: string;  // "HH:MM"
  end_time: string;
  title: string;
  type: "travel" | "meal" | "hotel" | "activity" | "rest";
  cost?: number;
}

interface MapPoint {
  lat: number;
  lng: number;
  label: string;
  type: "origin" | "waypoint" | "destination" | "hotel" | "activity";
}

interface CostBreakdown {
  transport: number;
  hotel: number;
  activities: number;
  food: number;
  miscellaneous: number;
  total: number;
  budget_limit?: number;
}
```

#### POST `/api/simulate-delay`
**Request:**
```typescript
interface SimulateDelayRequest {
  delay_type: string;
  delay_minutes: number;
  constraints?: Record<string, any>;
  selected_itinerary?: any;
}
```
**Response:**
```typescript
interface DelaySimulationResponse {
  updated_itinerary: any | null;
  changes: string[];
  validation_report: any;
  explanation: string;
}
```

### B.2 MOCK_DATA.js

Create this file at `frontend/src/api/mockData.js`. Import it in `tripApi.js` as a fallback when the backend is unavailable.

```javascript
// frontend/src/api/mockData.js
// Hardcoded mock responses matching API contracts exactly.
// Use these for development when the backend is not running.

export const MOCK_PARSE_CHAT = {
  extracted_constraints: {
    origin: "Gurugram",
    destination: null,
    destination_type: "mountains",
    budget_per_person: 15000,
    dates: null,
    trip_duration: "weekend",
    transport_preference: [],
    avoid_night_driving: true,
    must_include: ["rafting", "cafes"],
    return_deadline: "Monday morning",
    hotel_tier: "comfort",
    risk_tolerance: "medium",
    group_size: 4,
    special_requirements: [],
  },
  missing_fields: [],
  assumptions: {
    group_size: "4 (default)",
    risk_tolerance: "medium (default)",
  },
  conflict_report: { conflicts: [] },
};

export const MOCK_ITINERARY = {
  recommended_itinerary: {
    route: {
      route_id: "gurugram_rishikesh_2d1n",
      origin: "Gurugram",
      destination: "Rishikesh",
      distance_km: 260,
    },
    transport: { mode: "cab_with_driver", cost_total: 9500 },
    hotel: { name: "Riverside Comfort Stay", price_per_night: 4200 },
    activities: [
      { name: "White Water Rafting (16 km)", cost_per_person: 1800 },
      { name: "Ganga Aarti at Triveni Ghat", cost_per_person: 0 },
    ],
    total_cost_per_person: 10275,
    cost_breakdown: {
      transport: 2375,
      hotel: 1050,
      activities: 1800,
      food: 1050,
      miscellaneous: 2000,
      total: 10275,
    },
  },
  alternatives: [
    {
      route: { route_id: "gurugram_tirthan_3d2n", destination: "Tirthan Valley" },
      total_cost_per_person: 14500,
    },
  ],
  validation_report: {
    is_valid: true,
    hard_constraint_violations: [],
    soft_constraint_warnings: [],
  },
  score_breakdown: {
    preference_match: 25,
    budget_efficiency: 6.3,
    comfort: 12,
    scenic: 7,
    fatigue: 10.5,
    risk: 6,
    final_score: 66.8,
  },
  timeline: [
    { day: 1, start_time: "06:00", end_time: "09:00", title: "Drive from Gurugram", type: "travel" },
    { day: 1, start_time: "09:00", end_time: "09:45", title: "Breakfast at Murthal Dhaba", type: "meal", cost: 250 },
    { day: 1, start_time: "09:45", end_time: "13:00", title: "Continue to Rishikesh", type: "travel" },
    { day: 1, start_time: "13:00", end_time: "14:15", title: "Lunch at Little Buddha Cafe", type: "meal", cost: 600 },
    { day: 1, start_time: "14:30", end_time: "16:00", title: "Check-in & Rest at Riverside Comfort Stay", type: "hotel", cost: 1050 },
    { day: 1, start_time: "16:30", end_time: "17:30", title: "Riverside Cafe Hopping", type: "activity", cost: 400 },
    { day: 1, start_time: "18:30", end_time: "19:30", title: "Ganga Aarti at Triveni Ghat", type: "activity", cost: 0 },
    { day: 1, start_time: "20:00", end_time: "21:00", title: "Dinner", type: "meal", cost: 500 },
    { day: 2, start_time: "07:30", end_time: "08:15", title: "Breakfast at Hotel", type: "meal", cost: 200 },
    { day: 2, start_time: "09:00", end_time: "12:00", title: "White Water Rafting (16 km)", type: "activity", cost: 1800 },
    { day: 2, start_time: "12:30", end_time: "13:30", title: "Freshen Up", type: "rest" },
    { day: 2, start_time: "13:30", end_time: "14:30", title: "Lunch", type: "meal", cost: 500 },
    { day: 2, start_time: "15:00", end_time: "21:30", title: "Return Drive to Gurugram", type: "travel" },
  ],
  map_points: [
    { lat: 28.4595, lng: 77.0266, label: "Gurugram", type: "origin" },
    { lat: 29.0281, lng: 77.0474, label: "Murthal Dhaba Belt", type: "waypoint" },
    { lat: 30.0869, lng: 78.2676, label: "Rishikesh", type: "destination" },
    { lat: 30.0869, lng: 78.2676, label: "Riverside Comfort Stay", type: "hotel" },
    { lat: 30.1159, lng: 78.3127, label: "White Water Rafting", type: "activity" },
    { lat: 30.1050, lng: 78.2950, label: "Ganga Aarti", type: "activity" },
  ],
  cost_breakdown: {
    transport: 2375,
    hotel: 1050,
    activities: 1800,
    food: 1050,
    miscellaneous: 2000,
    total: 10275,
    budget_limit: 15000,
  },
  explanation:
    "This itinerary was selected because it stays within the ₹15,000 budget at ₹10,275 per person, avoids night driving on both legs, includes white water rafting and riverside cafe hopping, and returns to Gurugram by 9:30 PM Sunday — well before Monday morning.",
};

export const MOCK_DELAY = {
  updated_itinerary: {
    ...MOCK_ITINERARY.recommended_itinerary,
    total_cost_per_person: 10275,
  },
  changes: [
    "Departure delayed from 06:00 to 07:30",
    "Breakfast shortened from 45 min to 25 min",
    "Rest period reduced from 90 min to 45 min",
    "Cafe hopping removed to save time",
  ],
  validation_report: {
    is_valid: true,
    hard_constraint_violations: [],
    soft_constraint_warnings: ["Rest time below recommended minimum"],
  },
  explanation:
    "The 90-minute departure delay was absorbed by compressing flexible events. Breakfast was shortened, the rest period was halved, and riverside cafe hopping was removed. Rafting, Ganga Aarti, and the return deadline are all preserved.",
};
```

### B.3 Exact Field Paths (Frontend Must Read These)

```
response.extracted_constraints.origin
response.extracted_constraints.budget_per_person
response.extracted_constraints.must_include[0]
response.recommended_itinerary.route.destination
response.recommended_itinerary.total_cost_per_person
response.recommended_itinerary.cost_breakdown.transport
response.timeline[0].day
response.timeline[0].start_time
response.timeline[0].end_time
response.timeline[0].title
response.timeline[0].type
response.map_points[0].lat
response.map_points[0].lng
response.map_points[0].label
response.map_points[0].type
response.cost_breakdown.total
response.cost_breakdown.budget_limit
response.explanation
response.changes[0]
```

### B.4 Leaflet Map Coordinate Format

```javascript
{ lat: 28.4595, lng: 77.0266, label: "Gurugram", type: "origin" }
```

Map center default: `[28.5, 77.5]`, zoom: `7`

Marker colors by type:
- `origin` → 🟢 green
- `destination` → 🔴 red
- `hotel` → 🔵 blue
- `activity` → 🟡 yellow/gold
- `waypoint` → ⚪ gray

---

## Section C — Decisions & Defaults (Pre-Made)

| # | Decision | Value |
|---|----------|-------|
| 1 | Framework | React 18 + Vite 5 |
| 2 | CSS Framework | Tailwind CSS v3 (`tailwindcss@3`) |
| 3 | Animation library | Framer Motion (`framer-motion`) |
| 4 | Icon library | Lucide React (`lucide-react`) |
| 5 | Component base | shadcn/ui patterns (copy component code, do NOT use CLI — build manually) |
| 6 | HTTP client | Axios |
| 7 | Map library | react-leaflet + leaflet |
| 8 | Google Font | Inter — `https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap` |
| 9 | Theme | Dark mode only. No light mode toggle. |
| 10 | Background color | `#0f1117` |
| 11 | Surface/card color | `#1a1d2e` |
| 12 | Surface hover | `#242842` |
| 13 | Border color | `#2a2e45` |
| 14 | Text primary | `#e4e6f0` |
| 15 | Text muted | `#8b8fa3` |
| 16 | Primary accent | `#6c5ce7` (purple) |
| 17 | Secondary accent | `#00cec9` (teal) |
| 18 | Success | `#00b894` |
| 19 | Warning | `#fdcb6e` |
| 20 | Danger | `#e17055` |
| 21 | API URL env var | `VITE_API_URL` (from `.env`) — default `http://localhost:8000` |
| 22 | Mock mode | If API call fails, fallback to `mockData.js` and show a toast: "Using demo data (backend unavailable)" |
| 23 | Responsive breakpoints | mobile: 375px, tablet: 768px, desktop: 1280px |
| 24 | No `console.log` | Remove all debug logging before committing |
| 25 | App title | "TripGraph AI — Group Travel Planner" |
| 26 | Meta description | "AI-powered group travel planner that converts chat to optimized itineraries" |

---

## UI Excellence Requirements

These are **mandatory**. The frontend must implement ALL of the following:

1. **Skeleton loaders** on every data fetch — show animated placeholder shapes (not blank screens) while APIs load
2. **Animated number counters** in the cost breakdown — numbers count up from 0 to final value over 1.5 seconds when the card enters viewport
3. **Smooth polyline drawing** on the Leaflet map — the route line animates from origin to destination (not instant)
4. **Toast notifications** for errors — use a toast component (top-right), auto-dismiss after 5 seconds, with error icon and message
5. **Timeline item entrance animations** — each timeline event fades in and slides up staggered by 100ms
6. **Hover card effects** — cards lift slightly (`translateY(-4px)`) and border glows on hover
7. **Tab/section transitions** — switching between views (Timeline/Map/Cost/Calendar) has a cross-fade animation
8. **Chat message bubbles** — messages appear one by one with a typing effect (staggered 200ms per message)
9. **Score breakdown radar/bar chart** — visualize the scoring dimensions (preference, comfort, scenic, etc.) as colored bars or a radar chart
10. **Budget progress bar** — show a horizontal progress bar: "₹10,275 of ₹15,000 used" with color shifting from green (< 60%) to yellow (60-85%) to red (> 85%)
11. **Responsive layout** — all 8 components work at 375px width. Use single-column on mobile, multi-column on desktop.
12. **Empty states** — if no data yet, show a centered illustration/icon with text like "Paste your group chat to get started"

---

## Fallback Option

> [!NOTE]
> If the Tailwind + Framer Motion + shadcn approach produces code that is too complex to replicate or run:
> **Fallback:** Use vanilla CSS with CSS custom properties (matching the color palette above) and CSS `@keyframes` for animations. The existing `index.css` design system in the original spec already provides this foundation. Drop Tailwind and Framer Motion but keep Leaflet and Axios.

---

## Section D — Step-by-Step Build Instructions

### Step 1: Create React + Vite App

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install axios react-leaflet leaflet framer-motion lucide-react
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p
```

### Step 2: Configure Tailwind (`tailwind.config.js`)

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0f1117",
        surface: "#1a1d2e",
        "surface-hover": "#242842",
        border: "#2a2e45",
        "text-primary": "#e4e6f0",
        "text-muted": "#8b8fa3",
        primary: "#6c5ce7",
        "primary-hover": "#7d6ff0",
        accent: "#00cec9",
        success: "#00b894",
        warning: "#fdcb6e",
        danger: "#e17055",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
```

### Step 3: Update `index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TripGraph AI — Group Travel Planner</title>
  <meta name="description" content="AI-powered group travel planner that converts chat to optimized itineraries" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```

### Step 4: Create `src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', system-ui, sans-serif;
  background: #0f1117;
  color: #e4e6f0;
  min-height: 100vh;
  line-height: 1.6;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2a2e45; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #8b8fa3; }

/* Leaflet dark theme overrides */
.leaflet-container { background: #1a1d2e; }
.leaflet-control-zoom a { background: #1a1d2e !important; color: #e4e6f0 !important; border-color: #2a2e45 !important; }
.leaflet-popup-content-wrapper { background: #1a1d2e; color: #e4e6f0; border: 1px solid #2a2e45; }
.leaflet-popup-tip { background: #1a1d2e; }
```

### Step 5: Create `src/api/tripApi.js`

```javascript
import axios from "axios";
import { MOCK_PARSE_CHAT, MOCK_ITINERARY, MOCK_DELAY } from "./mockData";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 60000, // 60s — LLM calls can be slow
});

export async function parseChat(chatMessages) {
  try {
    const res = await api.post("/api/parse-chat", { chat_messages: chatMessages });
    return res.data;
  } catch (err) {
    console.warn("API unavailable, using mock data:", err.message);
    return MOCK_PARSE_CHAT;
  }
}

export async function generateItinerary(constraints) {
  try {
    const res = await api.post("/api/generate-itinerary", { constraints });
    return res.data;
  } catch (err) {
    console.warn("API unavailable, using mock data:", err.message);
    return MOCK_ITINERARY;
  }
}

export async function simulateDelay(delayType, delayMinutes, constraints, selectedItinerary) {
  try {
    const res = await api.post("/api/simulate-delay", {
      delay_type: delayType,
      delay_minutes: delayMinutes,
      constraints,
      selected_itinerary: selectedItinerary,
    });
    return res.data;
  } catch (err) {
    console.warn("API unavailable, using mock data:", err.message);
    return MOCK_DELAY;
  }
}
```

### Step 6: Create `src/hooks/useItinerary.js`

Custom React hook that manages the full application state:
- `chatMessages` — array of input messages
- `isLoading` / `loadingStep` — loading state with step name ("Parsing chat...", "Generating itinerary...")
- `parsedConstraints` — from `/parse-chat`
- `itinerary` — from `/generate-itinerary`
- `delayResult` — from `/simulate-delay`
- `error` — error message string
- `currentView` — "chat" | "results"

Functions:
- `submitChat(messages)` — calls parseChat → generateItinerary in sequence
- `simulateDelay(type, minutes)` — calls simulateDelay
- `reset()` — clear all state

### Step 7: Create Components

Build the following 8 components. Each should be its own `.jsx` file.

**Component List with Prop Interfaces:**

#### `ChatRoom` (`src/components/chat/ChatRoom.jsx`)
```
Props: { onSubmit: (messages: string[]) => void, isLoading: boolean }
```
- Textarea for pasting chat messages (one per line)
- Sample chat button that fills textarea with demo messages
- Submit button with loading spinner

#### `ExtractedPreferences` (`src/components/preferences/ExtractedPreferences.jsx`)
```
Props: { constraints: object, assumptions: object, missingFields: string[] }
```
- Display extracted constraints as labeled badges/chips
- Show assumptions with a muted "assumed" label
- Highlight missing fields in warning color

#### `ItineraryOptions` (`src/components/itinerary/ItineraryOptions.jsx`)
```
Props: { recommended: object, alternatives: object[], explanation: string, scoreBreakdown: object }
```
- Show recommended itinerary as a highlighted card
- List alternatives (if any) below
- Show explanation text
- Visualize score breakdown as colored horizontal bars

#### `ItineraryTimeline` (`src/components/itinerary/ItineraryTimeline.jsx`)
```
Props: { timeline: TimelineEvent[] }
```
- Vertical timeline grouped by day
- Each event shows: time range, title, type icon, cost (if any)
- Events animate in on mount (staggered)
- Color-code by type: travel=blue, meal=orange, activity=green, hotel=purple, rest=gray

#### `CalendarView` (`src/components/itinerary/CalendarView.jsx`)
```
Props: { timeline: TimelineEvent[] }
```
- Day/hour grid (like Google Calendar)
- Events rendered as colored blocks spanning their duration
- Hours on Y-axis, days on X-axis

#### `MapView` (`src/components/map/MapView.jsx`)
```
Props: { mapPoints: MapPoint[] }
```
- Leaflet map with OpenStreetMap tiles
- Colored markers per point type (see Section B.4)
- Popup on click showing label
- Polyline connecting all points in order
- Animated polyline drawing on mount
- Auto-fit bounds to show all markers

#### `CostBreakdown` (`src/components/cost/CostBreakdown.jsx`)
```
Props: { costBreakdown: CostBreakdown, groupSize: number }
```
- Animated number counters (count up from 0)
- Budget progress bar with color coding
- Category breakdown (transport, hotel, activities, food, misc)
- Per-person and total cost display

#### `DelaySimulator` (`src/components/delay/DelaySimulator.jsx`)
```
Props: { onSimulate: (type: string, minutes: number) => void, result: object | null, isLoading: boolean }
```
- Dropdown for delay type (departure_delay, traffic_delay, activity_delay)
- Slider or number input for minutes (15-300)
- Simulate button
- Show result: changes list, explanation, validation status

### Step 8: Create `src/App.jsx`

Main app layout:
1. **Header** — Logo, title "TripGraph AI"
2. **Chat phase**: Show `ChatRoom` centered. On submit, show loading skeleton.
3. **Results phase**: Multi-panel layout with tabs:
   - Tab 1: Timeline + Preferences
   - Tab 2: Map
   - Tab 3: Cost Breakdown
   - Tab 4: Calendar
   - Always visible: Explanation card, Delay Simulator

Use Framer Motion `AnimatePresence` for smooth transitions between phases.

---

## Section E — File Manifest

```
frontend/package.json                          — Dependencies
frontend/vite.config.js                        — Vite config
frontend/tailwind.config.js                    — Tailwind custom theme
frontend/postcss.config.js                     — PostCSS with Tailwind
frontend/index.html                            — HTML entry with Leaflet CSS + Google Font
frontend/src/main.jsx                          — React entry point
frontend/src/App.jsx                           — Main app component with routing
frontend/src/index.css                         — Global styles + Tailwind directives
frontend/src/api/tripApi.js                    — Axios API client with mock fallback
frontend/src/api/mockData.js                   — Hardcoded mock API responses
frontend/src/hooks/useItinerary.js             — Custom hook for app state
frontend/src/components/layout/Header.jsx      — App header with logo
frontend/src/components/chat/ChatRoom.jsx      — Chat input interface
frontend/src/components/preferences/ExtractedPreferences.jsx — Constraint display
frontend/src/components/itinerary/ItineraryOptions.jsx — Itinerary cards
frontend/src/components/itinerary/ItineraryTimeline.jsx — Vertical timeline
frontend/src/components/itinerary/CalendarView.jsx — Calendar grid view
frontend/src/components/map/MapView.jsx        — Leaflet map with markers
frontend/src/components/cost/CostBreakdown.jsx — Animated cost display
frontend/src/components/delay/DelaySimulator.jsx — Delay simulation UI
frontend/src/components/ui/Toast.jsx           — Toast notification component
frontend/src/components/ui/Skeleton.jsx        — Skeleton loader component
specs/logs/bucket_4_decisions.md               — Decisions & assumptions log
```

---

## Section F — Integration Verification Checklist

### Pre-Commit Checklist
- [ ] `npm run dev` starts without errors at `http://localhost:5173`
- [ ] `npm run build` succeeds with no errors
- [ ] All 8 core components render with mock data (no backend needed)
- [ ] Chat input accepts text and triggers the submit flow
- [ ] Extracted preferences display all constraint fields
- [ ] Timeline shows all events grouped by day with animations
- [ ] Map renders with markers and polyline
- [ ] Cost breakdown shows animated counters and budget progress bar
- [ ] Delay simulator sends request and shows results
- [ ] Calendar view renders events as blocks
- [ ] Skeleton loaders appear during loading states
- [ ] Toast notifications appear on API errors
- [ ] All components are responsive at 375px width
- [ ] No `console.log` in committed code
- [ ] Dark theme is consistent across all components
- [ ] All interactive elements have unique IDs
- [ ] `specs/logs/bucket_4_decisions.md` is created

### Visual Checklist (Manual)
- [ ] First impression is "wow, this looks professional"
- [ ] No blank/white screens at any point
- [ ] Animations are smooth (60fps)
- [ ] Colors are harmonious and high-contrast
- [ ] Typography is clean and readable

---

## Section G — 📋 Assumptions & Decisions Log (Output File)

**You MUST create:** `specs/logs/bucket_4_decisions.md`

```markdown
# Bucket 4 — Decisions & Assumptions Log
Generated by: [Model Name] on [Date]

## Pre-Specified Decisions Applied
## Unspecified Decisions Made During Build
## Deviations from Spec
## External Assumptions
## Validation Results
```

---

## Git Commit Protocol

```
1. Stage all files listed in File Manifest (Section E)
2. Stage specs/logs/bucket_4_decisions.md
3. Commit message: "Bucket 4: React frontend with full UI, mock API, animations — [date]"
4. Branch: bucket-4/implementation
5. Push to origin
6. Do NOT merge to main
```

---

## Quality Bar Reminder

- The UI is the **face of this project**. It must be excellent.
- Dark theme everywhere. No white backgrounds. No unstyled browser defaults.
- Every loading state has a skeleton. No blank screens ever.
- Every error has a human-readable toast with retry action.
- The Leaflet map must animate the polyline drawing.
- Timeline events must animate in with staggered entrance.
- Cost numbers must count up from 0.
- Mobile-responsive at 375px.
- A bucket without `specs/logs/bucket_4_decisions.md` is incomplete.
