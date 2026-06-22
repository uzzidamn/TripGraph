# HTML Content for the lightweight TripGraph AI Test Console
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TripGraph AI — Interactive Test Console</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0b0f19;
            --bg-surface: #131b2e;
            --bg-card: #1c2641;
            --border-color: #2e3c60;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #ef4444;
            --accent-violet: #8b5cf6;
            --font-display: 'Outfit', sans-serif;
            --font-sans: 'Plus Jakarta Sans', sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-sans);
            padding: 2rem;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        h1 {
            font-family: var(--font-display);
            font-size: 2.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }

        .badge {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .badge-active {
            border-color: var(--accent-green);
            color: var(--accent-green);
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1.5fr;
            gap: 2rem;
        }

        @media (max-width: 1024px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .card:hover {
            border-color: #435380;
        }

        .card-title {
            font-family: var(--font-display);
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Config Toggle Buttons */
        .pipeline-toggle {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            background: rgba(0, 0, 0, 0.2);
            padding: 0.35rem;
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }

        .toggle-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.6rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .toggle-btn.active {
            background: var(--primary);
            color: var(--text-primary);
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
        }

        /* Presets */
        .preset-buttons {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }

        .preset-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .preset-btn:hover {
            background: var(--border-color);
        }

        /* Forms */
        .form-group {
            margin-bottom: 1.25rem;
        }

        label {
            display: block;
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }

        textarea, input, select {
            width: 100%;
            background: rgba(0,0,0,0.3);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        textarea:focus, input:focus, select:focus {
            border-color: var(--primary);
        }

        .action-btn {
            background: var(--primary);
            border: none;
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
        }

        .action-btn:hover {
            background: var(--primary-hover);
        }

        .action-btn:disabled {
            background: var(--border-color);
            color: var(--text-secondary);
            cursor: not-allowed;
        }

        /* Output styles */
        .output-box {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            font-family: monospace;
            font-size: 0.85rem;
            overflow-x: auto;
            max-height: 250px;
        }

        /* Timeline styling */
        .timeline-container {
            position: relative;
            margin-top: 1rem;
            padding-left: 1.5rem;
            border-left: 2px solid var(--border-color);
        }

        .timeline-item {
            position: relative;
            margin-bottom: 1.5rem;
            padding: 0.75rem 1rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }

        .timeline-item::before {
            content: '';
            position: absolute;
            left: -2.05rem;
            top: 1.1rem;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--border-color);
            border: 2px solid var(--bg-surface);
        }

        .timeline-item.travel::before { background: var(--accent-violet); }
        .timeline-item.activity::before { background: var(--accent-green); }
        .timeline-item.meal::before { background: var(--accent-amber); }
        .timeline-item.hotel::before { background: var(--accent-rose); }
        
        .timeline-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 0.25rem;
        }

        .timeline-title {
            font-weight: 600;
            font-size: 0.95rem;
        }

        .timeline-meta {
            font-size: 0.8rem;
            margin-top: 0.25rem;
            color: var(--text-secondary);
            display: flex;
            gap: 1rem;
        }

        .badge-type {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-weight: 700;
        }
        .timeline-item.travel .badge-type { background: rgba(139, 92, 246, 0.2); color: #c084fc; }
        .timeline-item.activity .badge-type { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .timeline-item.meal .badge-type { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .timeline-item.hotel .badge-type { background: rgba(239, 68, 68, 0.2); color: #f87171; }
        .timeline-item.rest .badge-type { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; }

        /* Cost item */
        .cost-row {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .cost-row:last-child {
            border: none;
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--accent-green);
        }

        .spinner {
            border: 3px solid rgba(255,255,255,0.1);
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border-left-color: white;
            animation: spin 1s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .alert {
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border: 1px solid transparent;
            font-size: 0.9rem;
        }
        .alert-info {
            background: rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.3);
            color: #a5b4fc;
        }
        .alert-error {
            background: rgba(239, 68, 68, 0.15);
            border-color: rgba(239, 68, 68, 0.3);
            color: #f87171;
        }
        .alert-warning {
            background: rgba(245, 158, 11, 0.15);
            border-color: rgba(245, 158, 11, 0.3);
            color: #fbbf24;
        }

        /* Pipeline trace */
        .trace-step {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            padding: 0.6rem 0.75rem;
            border-radius: 8px;
            background: rgba(0,0,0,0.2);
            margin-bottom: 0.4rem;
        }
        .trace-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 0.1rem; }
        .trace-label { font-size: 0.8rem; font-weight: 700; color: var(--text-secondary); margin-right: 0.3rem; }
        .trace-value { font-size: 0.85rem; color: var(--text-primary); }
        .trace-detail { font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.2rem; font-style: italic; }
        .trace-step.trace-blocked { background: rgba(239,68,68,0.12); border-left: 2px solid var(--accent-rose); }
        .trace-step.trace-warn { background: rgba(245,158,11,0.1); border-left: 2px solid var(--accent-amber); }
        .trace-step.trace-ok { background: rgba(16,185,129,0.08); border-left: 2px solid var(--accent-green); }

        /* Clarification form */
        .clarify-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1rem; }
        /* Suggestion route cards */
        .suggestion-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.75rem; margin-top: 0.75rem; }
        .suggestion-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 0.85rem 1rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .suggestion-card:hover { border-color: var(--primary); background: rgba(99,102,241,0.1); }
        .suggestion-card .sc-route { font-weight: 700; font-size: 0.95rem; margin-bottom: 0.25rem; }
        .suggestion-card .sc-meta { font-size: 0.78rem; color: var(--text-secondary); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>TripGraph AI</h1>
                <div class="subtitle">GenAI Group Travel Planner — Interactive Testing Console</div>
            </div>
            <div style="display: flex; gap: 1rem; align-items: center;">
                <div id="mode-badge" class="badge">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; display: inline-block;"></span>
                    <span>Loading...</span>
                </div>
            </div>
        </header>

        <div class="dashboard-grid">
            <!-- Left Column: Controls & Input -->
            <div class="left-col">
                <!-- Config Card -->
                <div class="card">
                    <div class="card-title">
                        <span>1. Set Pipeline Mode</span>
                    </div>
                    <div class="pipeline-toggle">
                        <button id="btn-agentic" class="toggle-btn" onclick="setMode('agentic')">Agentic (LangGraph)</button>
                        <button id="btn-augmented" class="toggle-btn" onclick="setMode('augmented')">Augmented LLM (ReAct)</button>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.75rem; line-height: 1.4;">
                        Toggles how constraints are parsed and itineraries are planned. Agentic uses LangGraph's multi-agent graph. Augmented uses a single LLM with tools.
                    </div>
                </div>

                <!-- Chat Parse Card -->
                <div class="card">
                    <div class="card-title">
                        <span>2. Group Chat Input</span>
                    </div>
                    
                    <div class="preset-buttons">
                        <button class="preset-btn" onclick="loadPreset('rishikesh')">Rishikesh (Adventure)</button>
                        <button class="preset-btn" onclick="loadPreset('jaipur')">Jaipur (Heritage)</button>
                        <button class="preset-btn" onclick="loadPreset('tirthan')">Tirthan Valley (Expedition)</button>
                    </div>

                    <div class="form-group">
                        <label for="chat-input">Group Chat Messages (one message per line)</label>
                        <textarea id="chat-input" rows="8" placeholder="Enter messages here..."></textarea>
                    </div>

                    <button id="btn-parse" class="action-btn" onclick="parseChat()">
                        <span>Parse Group Chat</span>
                    </button>
                </div>

                <!-- Clarification Card -->
                <div class="card" id="clarify-card" style="display: none;">
                    <div class="card-title" style="color: var(--accent-amber);">
                        <span>⚠️ Clarify Missing Fields</span>
                    </div>
                    <p style="font-size:0.85rem; color: var(--text-secondary); margin-bottom:1rem;">
                        Some trip details are missing or unclear. Fill them in below to continue planning.
                    </p>
                    <div id="clarify-fields-container" class="clarify-grid"></div>
                    <button class="action-btn" style="background: var(--accent-amber); color: #000; font-weight: 700;" onclick="confirmClarification()">
                        <span>Confirm &amp; Generate Itinerary →</span>
                    </button>
                </div>

                <!-- Simulate Delay Card -->
                <div class="card" id="delay-card" style="display: none;">
                    <div class="card-title">
                        <span>4. Simulate Disruption & Replan</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.25rem;">
                        <div class="form-group" style="margin-bottom: 0;">
                            <label for="delay-type">Delay Type</label>
                            <select id="delay-type">
                                <option value="departure_delay">Departure Delay</option>
                                <option value="traffic_delay">Traffic Delay</option>
                                <option value="activity_delay">Activity Delay</option>
                            </select>
                        </div>
                        <div class="form-group" style="margin-bottom: 0;">
                            <label for="delay-mins">Duration (Minutes)</label>
                            <input type="number" id="delay-mins" value="90" min="15" max="300">
                        </div>
                    </div>
                    <button id="btn-replan" class="action-btn" style="background: var(--accent-violet);" onclick="simulateDelay()">
                        <span>Simulate Delay</span>
                    </button>
                </div>
            </div>

            <!-- Right Column: Output Displays -->
            <div class="right-col">
                <!-- Status/Alert Message -->
                <div id="status-message" style="display: none;"></div>

                <!-- Extracted Constraints Card -->
                <div class="card" id="constraints-card" style="display: none;">
                    <div class="card-title">
                        <span>Extracted Trip Constraints</span>
                        <span id="plan-ready-badge" class="badge"></span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                        <div>
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">Origin:</span>
                            <strong id="val-origin" style="display: block; margin-top: 0.15rem;">-</strong>
                        </div>
                        <div>
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">Destination:</span>
                            <strong id="val-destination" style="display: block; margin-top: 0.15rem;">-</strong>
                        </div>
                        <div>
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">Budget:</span>
                            <strong id="val-budget" style="display: block; margin-top: 0.15rem;">-</strong>
                        </div>
                        <div>
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">Duration / Group:</span>
                            <strong id="val-duration" style="display: block; margin-top: 0.15rem;">-</strong>
                        </div>
                    </div>

                    <div id="assumptions-box" style="margin-bottom: 1rem; display: none;">
                        <span style="font-size: 0.85rem; font-weight: 600; display: block; margin-bottom: 0.35rem; color: var(--accent-amber);">Assumptions made:</span>
                        <div id="assumptions-list" style="font-size: 0.85rem; line-height: 1.4; color: var(--text-secondary); padding-left: 1rem;"></div>
                    </div>

                    <div id="conflicts-box" style="margin-bottom: 1rem; display: none;" class="alert alert-error">
                        <span style="font-weight: 700; display: block; margin-bottom: 0.25rem;">Constraint Conflicts Detected:</span>
                        <div id="conflicts-list" style="font-size: 0.85rem;"></div>
                    </div>

                    <button id="btn-generate" class="action-btn" style="background: var(--accent-green);" onclick="generateItinerary()">
                        <span>Generate Itinerary</span>
                    </button>
                </div>

                <!-- Itinerary Result Card -->
                <div class="card" id="itinerary-card" style="display: none;">
                    <div class="card-title">
                        <span>Selected Itinerary & Timeline</span>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1.5rem;">
                        <!-- Left Details -->
                        <div>
                            <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;" id="res-title">Jaipur Heritage Trip</h3>
                            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.35rem;" id="res-hotel">Hotel: -</p>
                            <p style="font-size: 0.85rem; color: var(--text-secondary);" id="res-transport">Transport: -</p>
                        </div>
                        <!-- Right Cost -->
                        <div id="cost-box" style="background: rgba(0,0,0,0.2); padding: 0.75rem; border-radius: 8px;">
                            <div class="cost-row"><span>Transport</span><span id="cost-trans">-</span></div>
                            <div class="cost-row"><span>Hotel</span><span id="cost-hotel">-</span></div>
                            <div class="cost-row"><span>Activities</span><span id="cost-acts">-</span></div>
                            <div class="cost-row"><span>Total Per Person</span><span id="cost-total">-</span></div>
                        </div>
                    </div>

                    <!-- Timeline -->
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">Timeline:</div>
                    <div id="timeline-list" class="timeline-container"></div>

                    <!-- Explanation -->
                    <div style="margin-top: 1.5rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
                        <span style="font-size: 0.85rem; font-weight: 600; display: block; margin-bottom: 0.5rem; color: var(--accent-violet);">LLM Selection Rationale:</span>
                        <p id="res-explanation" style="font-size: 0.9rem; line-height: 1.5; color: var(--text-secondary); font-style: italic;"></p>
                    </div>
                </div>

                <!-- Replanned Output Card -->
                <div class="card" id="replanned-card" style="display: none;">
                    <div class="card-title" style="color: var(--accent-violet);">
                        <span>Replanned Itinerary (After Delay)</span>
                    </div>

                    <div id="replan-changes-box" class="alert alert-warning" style="margin-bottom: 1rem;">
                        <span style="font-weight: 700; display: block; margin-bottom: 0.25rem;">Adjustments Made:</span>
                        <ul id="replan-changes-list" style="padding-left: 1.25rem; font-size: 0.85rem;"></ul>
                    </div>

                    <div style="font-weight: 600; margin-bottom: 0.5rem;">Adjusted Timeline:</div>
                    <div id="replan-timeline-list" class="timeline-container"></div>

                    <div style="margin-top: 1.5rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
                        <span style="font-size: 0.85rem; font-weight: 600; display: block; margin-bottom: 0.5rem; color: var(--accent-violet);">LLM Replanning Explanation:</span>
                        <p id="replan-explanation" style="font-size: 0.9rem; line-height: 1.5; color: var(--text-secondary); font-style: italic;"></p>
                    </div>
                </div>

                <!-- Unsupported Route Card -->
                <div class="card" id="unsupported-route-card" style="display: none;">
                    <div class="card-title" style="color: var(--accent-amber);">
                        <span>🗺️ Route Not in Catalog</span>
                    </div>
                    <p id="unsupported-route-msg" style="font-size:0.9rem; margin-bottom:1rem; line-height:1.5;"></p>
                    <div style="font-size:0.85rem; font-weight:600; color:var(--text-secondary); margin-bottom:0.5rem;">Try one of these supported routes instead:</div>
                    <div id="suggestion-cards-container" class="suggestion-cards"></div>
                </div>

                <!-- Pipeline Trace Card -->
                <div class="card" id="pipeline-trace-card" style="display: none;">
                    <div class="card-title">
                        <span>🔬 Pipeline Agent Trace</span>
                    </div>
                    <div id="pipeline-trace-body"></div>
                </div>

                <!-- Raw JSON Card -->
                <div class="card" id="raw-json-card" style="display: none;">
                    <div class="card-title">
                        <span>Raw API JSON Response</span>
                    </div>
                    <pre class="output-box"><code id="raw-json-output"></code></pre>
                </div>
            </div>
        </div>
    </div>

    <script>
        // State variables
        let currentConstraints = null;
        let selectedItinerary = null;
        let activeMode = "augmented";

        const PRESETS = {
            rishikesh: [
                "Let's do a weekend trip from Gurugram",
                "Rishikesh please, I want to do rafting",
                "Budget under 15000 per person",
                "We are a group of 4 people",
                "No night driving please, avoid driving after dark",
                "Hotel preference is comfort tier",
                "Need rafting and good cafes"
            ],
            jaipur: [
                "Plan a heritage trip from Gurugram to Jaipur",
                "Comfort hotel tier preferred",
                "Budget 10000 per person max",
                "We need to return before Monday morning",
                "Must do Amer Fort Guided Tour",
                "We are a group of 4"
            ],
            tirthan: [
                "Long weekend trip to Tirthan Valley starting from Gurugram",
                "We have a budget of 20000 rupees per person",
                "Expedition hotel tier please",
                "We are a group of 4",
                "Avoid night driving",
                "Risk tolerance is high"
            ]
        };

        // Load config from server on start
        window.addEventListener('DOMContentLoaded', async () => {
            await fetchConfig();
            loadPreset('rishikesh');
        });

        async function fetchConfig() {
            try {
                const response = await fetch('/api/config');
                const data = await response.json();
                updateModeUI(data.pipeline_mode);
            } catch (err) {
                console.error("Failed to fetch configuration:", err);
                showStatus("Error loading pipeline config. Make sure server is running.", "error");
            }
        }

        function updateModeUI(mode) {
            activeMode = mode;
            
            // Buttons
            document.getElementById('btn-agentic').classList.remove('active');
            document.getElementById('btn-augmented').classList.remove('active');
            
            const badge = document.getElementById('mode-badge');
            const dot = badge.querySelector('span');
            const text = badge.querySelectorAll('span')[1];
            
            if (mode === 'agentic') {
                document.getElementById('btn-agentic').classList.add('active');
                badge.className = "badge badge-active";
                badge.style.borderColor = "var(--primary)";
                dot.style.backgroundColor = "var(--primary)";
                text.textContent = "Mode: Agentic LangGraph";
            } else {
                document.getElementById('btn-augmented').classList.add('active');
                badge.className = "badge badge-active";
                badge.style.borderColor = "var(--accent-green)";
                dot.style.backgroundColor = "var(--accent-green)";
                text.textContent = "Mode: Augmented LLM (ReAct)";
            }
        }

        async function setMode(mode) {
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pipeline_mode: mode })
                });
                const data = await response.json();
                updateModeUI(data.pipeline_mode);
                showStatus(`Pipeline mode switched to ${mode.toUpperCase()} successfully.`, "info");
            } catch (err) {
                showStatus("Failed to switch pipeline mode.", "error");
            }
        }

        function loadPreset(key) {
            const lines = PRESETS[key];
            document.getElementById('chat-input').value = lines.join('\\n');
        }

        function showStatus(msg, type = "info") {
            const el = document.getElementById('status-message');
            el.style.display = "block";
            el.className = `alert alert-${type}`;
            el.innerHTML = msg;
        }

        function hideStatus() {
            document.getElementById('status-message').style.display = "none";
        }

        function showLoading(btnId, show = true) {
            const btn = document.getElementById(btnId);
            if (show) {
                btn.disabled = true;
                btn.dataset.originalHtml = btn.innerHTML;
                btn.innerHTML = '<span class="spinner"></span> <span>Running Workflow...</span>';
            } else {
                btn.disabled = false;
                btn.innerHTML = btn.dataset.originalHtml;
            }
        }

        // 1. POST /api/parse-chat
        async function parseChat() {
            hideStatus();
            document.getElementById('constraints-card').style.display = "none";
            document.getElementById('itinerary-card').style.display = "none";
            document.getElementById('delay-card').style.display = "none";
            document.getElementById('replanned-card').style.display = "none";
            document.getElementById('raw-json-card').style.display = "none";
            document.getElementById('pipeline-trace-card').style.display = "none";
            document.getElementById('clarify-card').style.display = "none";
            document.getElementById('unsupported-route-card').style.display = "none";

            const chatText = document.getElementById('chat-input').value.trim();
            if (!chatText) {
                showStatus("Please enter some chat messages first.", "warning");
                return;
            }

            const messages = chatText.split('\\n').filter(line => line.trim() !== "");
            
            showLoading('btn-parse', true);
            try {
                const response = await fetch('/api/parse-chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chat_messages: messages })
                });

                const data = await response.json();
                showLoading('btn-parse', false);

                if (response.status !== 200) {
                    showStatus(`Error (${response.status}): ${data.detail || "Parse failed"}`, "error");
                    return;
                }

                // Show guardrail result if it blocked the pipeline
                const gr = data.guardrail_result || {};
                if (gr.action === 'ignore') {
                    showStatus(`🛡️ Guardrail: Message ignored — <strong>${gr.reason}</strong>. Not a valid trip request.`, "warning");
                    displayRawJson(data);
                    return;
                }
                if (gr.action === 'clarify') {
                    showStatus(`🛡️ Guardrail: Clarification needed — <strong>${gr.response}</strong>`, "warning");
                    displayRawJson(data);
                    return;
                }
                if (gr.action === 'confirm') {
                    showStatus(`🛡️ Guardrail: Similar trip found — <strong>${gr.response}</strong>`, "warning");
                    displayRawJson(data);
                    return;
                }

                currentConstraints = data.extracted_constraints || {};
                displayPipelineTrace(data);
                displayConstraints(data);
                if ((data.missing_fields || []).length > 0) {
                    showClarificationForm(data.missing_fields, currentConstraints);
                }
                displayRawJson(data);

            } catch (err) {
                showLoading('btn-parse', false);
                showStatus(`Connection failed: ${err.message}`, "error");
            }
        }

        function displayConstraints(data) {
            const constraints = data.extracted_constraints || {};
            const missing = data.missing_fields || [];
            const assumptions = data.assumptions || {};
            const conflicts = data.conflict_report || {};

            document.getElementById('constraints-card').style.display = "block";
            
            document.getElementById('val-origin').textContent = constraints.origin || '❓ Not provided';
            document.getElementById('val-destination').textContent = constraints.destination || (constraints.destination_type ? `Any ${constraints.destination_type}` : '❓ Not provided');
            document.getElementById('val-budget').textContent = constraints.budget_per_person ? `₹${constraints.budget_per_person.toLocaleString()}` : '❓ Not provided';
            document.getElementById('val-duration').textContent = `${constraints.trip_duration || '❓'} / Group of ${constraints.group_size || '❓'}`;

            // Ready badge
            const isReady = missing.length === 0;
            const badge = document.getElementById('plan-ready-badge');
            if (isReady) {
                badge.className = "badge badge-active";
                badge.style.borderColor = "var(--accent-green)";
                badge.style.color = "var(--accent-green)";
                badge.textContent = "Ready to Plan";
                document.getElementById('btn-generate').disabled = false;
            } else {
                badge.className = "badge";
                badge.style.borderColor = "var(--accent-amber)";
                badge.style.color = "var(--accent-amber)";
                badge.textContent = `Clarification Needed (${missing.length})`;
                document.getElementById('btn-generate').disabled = false; // let them click anyway to see fallback
                // Clarification form handles prompting — no warning needed here
            }

            // Assumptions
            const assumptionsBox = document.getElementById('assumptions-box');
            const assumptionsList = document.getElementById('assumptions-list');
            if (Object.keys(assumptions).length > 0) {
                assumptionsBox.style.display = "block";
                assumptionsList.innerHTML = Object.entries(assumptions)
                    .map(([k, v]) => `<div>&bull; <strong>${k.replace('_', ' ')}</strong>: ${v}</div>`)
                    .join('');
            } else {
                assumptionsBox.style.display = "none";
            }

            // Conflicts
            const conflictsBox = document.getElementById('conflicts-box');
            const conflictsList = document.getElementById('conflicts-list');
            const conflictsArr = conflicts.conflicts || [];
            if (conflicts.has_conflicts || conflictsArr.length > 0) {
                conflictsBox.style.display = "block";
                conflictsList.innerHTML = conflictsArr
                    .map(c => `<div>❌ Conflict: <strong>${c.field1}</strong> & <strong>${c.field2}</strong>: ${c.reason}</div>`)
                    .join('');
            } else {
                conflictsBox.style.display = "none";
            }
        }

        // 2. POST /api/generate-itinerary
        async function generateItinerary() {
            hideStatus();
            document.getElementById('itinerary-card').style.display = "none";
            document.getElementById('delay-card').style.display = "none";
            document.getElementById('replanned-card').style.display = "none";

            if (!currentConstraints) {
                showStatus("Please parse constraints first.", "warning");
                return;
            }

            showLoading('btn-generate', true);
            try {
                const response = await fetch('/api/generate-itinerary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ constraints: currentConstraints })
                });

                const data = await response.json();
                showLoading('btn-generate', false);

                if (response.status !== 200) {
                    showStatus(`Error (${response.status}): ${data.detail || "Itinerary generation failed"}`, "error");
                    return;
                }

                if (!data.recommended_itinerary) {
                    // Always update trace + raw JSON so the user can see what happened
                    displayPipelineTrace(data);
                    displayRawJson(data);

                    // Check if route had no catalog match
                    if (data.unsupported_route) {
                        displayUnsupportedRoute(data.unsupported_route, data.suggested_routes || []);
                        showStatus(`Route not supported yet — see suggestions below.`, "warning");
                        return;
                    }

                    // Check if guardrail blocked the pipeline
                    const gr = data.guardrail_result || {};
                    if (gr.action && gr.action !== 'proceed') {
                        showStatus(`🛡️ Guardrail blocked planning — action: <strong>${gr.action}</strong>. ${gr.response || gr.reason || ''}`, "warning");
                        return;
                    }

                    // Check if constraint validator blocked (missing required fields)
                    if (data.is_ready_to_plan === false) {
                        const cr = data.conflict_report || {};
                        const blocking = cr.blocking_conflicts || [];
                        const reasons = blocking.map(b => `&bull; ${b.description || b.field}`).join('<br>');
                        showStatus(`Cannot plan — required fields missing or conflicting:<br>${reasons || 'See Raw JSON for details.'}`, "error");
                        if ((data.missing_fields || []).length > 0) {
                            showClarificationForm(data.missing_fields, data.extracted_constraints);
                        }
                        return;
                    }

                    // Planner ran but all candidates violated hard constraints
                    const vr = data.validation_report || {};
                    const violations = vr.hard_constraint_violations || [];
                    const budgetInfo = (vr.budget_used != null && vr.budget_limit != null)
                        ? `<br>&bull; Budget used: ₹${Number(vr.budget_used).toLocaleString()} / limit ₹${Number(vr.budget_limit).toLocaleString()}`
                        : '';
                    const violationList = violations.map(v => `&bull; ${v}`).join('<br>');
                    showStatus(
                        `No valid itineraries could be generated. Hard constraints violated:<br>${violationList || 'No candidates matched the route catalog.'}${budgetInfo}`,
                        "error"
                    );
                    return;
                }

                selectedItinerary = data.recommended_itinerary;
                displayPipelineTrace(data);
                displayItinerary(data);
                displayRawJson(data);

                // Show replanning tools
                document.getElementById('delay-card').style.display = "block";

            } catch (err) {
                showLoading('btn-generate', false);
                showStatus(`Connection failed: ${err.message}`, "error");
            }
        }

        function displayItinerary(data) {
            const itin = data.recommended_itinerary;
            document.getElementById('itinerary-card').style.display = "block";

            document.getElementById('res-title').textContent = `${itin.destination} Trip (${itin.route.distance_km} km)`;
            document.getElementById('res-hotel').textContent = `Hotel: ${itin.hotel ? itin.hotel.name : 'None'} (₹${itin.hotel ? itin.hotel.price_per_night : 0}/night)`;
            document.getElementById('res-transport').textContent = `Transport: ${itin.transport ? itin.transport.mode.replace('_', ' ') : 'None'} (Cost: ₹${itin.transport ? itin.transport.cost_total : 0})`;

            // Cost details
            const cb = data.cost_breakdown || itin.cost_breakdown || {};
            document.getElementById('cost-trans').textContent = `₹${(cb.transport || 0).toLocaleString()}`;
            document.getElementById('cost-hotel').textContent = `₹${(cb.hotel || 0).toLocaleString()}`;
            document.getElementById('cost-acts').textContent = `₹${(cb.activities || 0).toLocaleString()}`;
            document.getElementById('cost-total').textContent = `₹${(cb.total || 0).toLocaleString()}`;

            // Timeline list
            const timelineList = document.getElementById('timeline-list');
            timelineList.innerHTML = '';
            
            const timeline = data.timeline || [];
            timeline.forEach(event => {
                const item = document.createElement('div');
                item.className = `timeline-item ${event.type}`;
                
                const costStr = event.cost ? ` &bull; Cost: ₹${event.cost}` : '';
                
                item.innerHTML = `
                    <div class="timeline-header">
                        <span class="badge-type">${event.type}</span>
                        <span>Day ${event.day} | ${event.start_time} - ${event.end_time}</span>
                    </div>
                    <div class="timeline-title">${event.title}</div>
                    ${costStr ? `<div class="timeline-meta">${costStr}</div>` : ''}
                `;
                timelineList.appendChild(item);
            });

            // Explanation
            document.getElementById('res-explanation').textContent = data.explanation || 'No rationale explanation returned.';
        }

        // 3. POST /api/simulate-delay
        async function simulateDelay() {
            hideStatus();
            document.getElementById('replanned-card').style.display = "none";

            if (!selectedItinerary) {
                showStatus("Please generate an itinerary first.", "warning");
                return;
            }

            const delayType = document.getElementById('delay-type').value;
            const delayMins = parseInt(document.getElementById('delay-mins').value);

            if (isNaN(delayMins) || delayMins < 15 || delayMins > 300) {
                showStatus("Please enter a valid delay between 15 and 300 minutes.", "warning");
                return;
            }

            showLoading('btn-replan', true);
            try {
                const response = await fetch('/api/simulate-delay', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        delay_type: delayType,
                        delay_minutes: delayMins,
                        constraints: currentConstraints,
                        selected_itinerary: selectedItinerary
                    })
                });

                const data = await response.json();
                showLoading('btn-replan', false);

                if (response.status !== 200) {
                    showStatus(`Error (${response.status}): ${data.detail || "Replanning failed"}`, "error");
                    return;
                }

                displayReplanned(data);
                displayRawJson(data);

            } catch (err) {
                showLoading('btn-replan', false);
                showStatus(`Connection failed: ${err.message}`, "error");
            }
        }

        function displayReplanned(data) {
            document.getElementById('replanned-card').style.display = "block";

            // Changes
            const changesList = document.getElementById('replan-changes-list');
            changesList.innerHTML = '';
            const changes = data.changes || [];
            if (changes.length > 0) {
                changes.forEach(c => {
                    const li = document.createElement('li');
                    li.textContent = c;
                    changesList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = "No visible changes needed; delay was absorbed within buffer times.";
                changesList.appendChild(li);
            }

            // Timeline
            const timelineList = document.getElementById('replan-timeline-list');
            timelineList.innerHTML = '';
            
            const updatedItin = data.updated_itinerary || {};
            const timeline = updatedItin.timeline || [];
            timeline.forEach(event => {
                const item = document.createElement('div');
                item.className = `timeline-item ${event.type}`;
                
                const costStr = event.cost ? ` &bull; Cost: ₹${event.cost}` : '';
                
                item.innerHTML = `
                    <div class="timeline-header">
                        <span class="badge-type">${event.type}</span>
                        <span>Day ${event.day} | ${event.start_time} - ${event.end_time}</span>
                    </div>
                    <div class="timeline-title">${event.title}</div>
                    ${costStr ? `<div class="timeline-meta">${costStr}</div>` : ''}
                `;
                timelineList.appendChild(item);
            });

            // Explanation
            document.getElementById('replan-explanation').textContent = data.explanation || 'No replanning explanation returned.';
        }

        function displayPipelineTrace(data) {
            const body = document.getElementById('pipeline-trace-body');
            if (!body) return;
            body.innerHTML = '';
            document.getElementById('pipeline-trace-card').style.display = 'block';

            function step(icon, label, value, detail, status = 'ok') {
                const d = document.createElement('div');
                d.className = `trace-step trace-${status}`;
                d.innerHTML = `
                    <span class="trace-icon">${icon}</span>
                    <div>
                        <div><span class="trace-label">${label}</span><span class="trace-value">${value}</span></div>
                        ${detail ? `<div class="trace-detail">${detail}</div>` : ''}
                    </div>`;
                body.appendChild(d);
            }

            // Agent 0: Guardrail
            const gr = data.guardrail_result || {};
            const grStatus = !gr.action ? 'ok' : (gr.action === 'proceed' ? 'ok' : (gr.action === 'ignore' ? 'blocked' : 'warn'));
            step('🛡️', 'Guardrail: ', `action=${gr.action || 'n/a'} | reason=${gr.reason || 'n/a'}`,
                gr.response ? `"${gr.response}"` : '', grStatus);
            if (gr.action && gr.action !== 'proceed') return;

            // Agent 1: Chat Parser
            const c = data.extracted_constraints || {};
            const filled = Object.values(c).filter(v => v !== null && v !== undefined && !(Array.isArray(v) && v.length === 0)).length;
            const missing = data.missing_fields || [];
            const assumps = data.assumptions || {};
            const aCount = Object.keys(assumps).length;
            const parserDetail = aCount > 0 ? `Assumptions: ${Object.entries(assumps).map(([k,v]) => `${k}→${v}`).join(', ')}` : '';
            step('📝', 'Chat Parser: ', `${filled}/14 fields extracted | ${missing.length} missing | ${aCount} assumptions`,
                parserDetail, missing.length > 0 ? 'warn' : 'ok');

            // Agent 2: Memory Agent
            const profile = data.user_profile || {};
            const memCtx = data.memory_context || {};
            const visited = data.visited_destinations || [];
            const profileKeys = Object.keys(profile).length;
            const memDetail = [
                visited.length > 0 ? `Visited: ${visited.join(', ')}` : '',
                Object.keys(memCtx).length > 0 ? `Context: ${JSON.stringify(memCtx)}` : 'No memory context applied',
            ].filter(Boolean).join(' | ');
            step('🧠', 'Memory Agent: ', `${profileKeys} profile fields | ${visited.length} visited destinations`, memDetail, 'ok');

            // Agent 3: Constraint Validator
            const cr = data.conflict_report || {};
            const blocking = (cr.blocking_conflicts || []).length;
            const warnings = (cr.warnings || []).length;
            const isReady = data.is_ready_to_plan;
            const cvDetail = blocking > 0 ? (cr.blocking_conflicts || []).map(x => x.description).join('; ') : '';
            step('✅', 'Constraint Validator: ', `ready=${isReady ? 'yes' : 'no'} | blocking=${blocking} | warnings=${warnings}`,
                cvDetail, blocking > 0 ? 'blocked' : (warnings > 0 ? 'warn' : 'ok'));
            if (!isReady) return;

            // Data Retrieval agents
            const rC = (data.route_candidates || []).length;
            const hC = (data.hotel_candidates || []).length;
            const aC = (data.activity_candidates || []).length;
            const tC = (data.transport_candidates || []).length;
            const fC = (data.food_candidates || []).length;
            const wC = (data.waypoint_candidates || []).length;
            if (rC + hC + aC + tC + fC + wC > 0) {
                step('🔍', 'Data Retrieval: ',
                    `${rC} routes | ${hC} hotels | ${tC} transport | ${aC} activities | ${fC} food | ${wC} waypoints`,
                    '', rC === 0 ? 'warn' : 'ok');
            }

            // Planner
            const candCount = (data.itinerary_candidates || []).length;
            const score = (data.score_breakdown || {}).final_score;
            if (candCount > 0 || data.recommended_itinerary) {
                step('📋', 'Planner: ', `${candCount} candidates | selected score: ${score != null ? score : 'n/a'}`, '', 'ok');
            }

            // Explainer
            if (data.explanation) {
                step('💬', 'Explainer: ', 'rationale generated', '', 'ok');
            }
        }

        const CLARIFY_FIELD_CONFIG = {
            'origin':            { label: 'Origin City',          type: 'text',   placeholder: 'e.g. Gurugram' },
            'destination':       { label: 'Destination',          type: 'text',   placeholder: 'e.g. Rishikesh' },
            'destination_type':  { label: 'Destination Type',     type: 'select', options: ['mountains', 'heritage', 'nature'] },
            'budget_per_person': { label: 'Budget Per Person (₹)', type: 'number', placeholder: 'e.g. 15000' },
            'trip_duration':     { label: 'Trip Duration',         type: 'text',   placeholder: 'e.g. 2D1N, 3 days' },
            'group_size':        { label: 'Group Size',            type: 'number', placeholder: 'e.g. 4' },
            'hotel_tier':        { label: 'Hotel Tier',            type: 'select', options: ['budget', 'comfort', 'expedition'] },
            'risk_tolerance':    { label: 'Risk Tolerance',        type: 'select', options: ['low', 'medium', 'high'] },
        };

        function showClarificationForm(missingFields, constraints) {
            if (!missingFields || missingFields.length === 0) {
                document.getElementById('clarify-card').style.display = 'none';
                return;
            }
            const container = document.getElementById('clarify-fields-container');
            container.innerHTML = '';

            // Normalize compound missing field strings like "budget_per_person / trip_duration"
            const fields = [];
            for (const f of missingFields) {
                f.split('/').forEach(part => {
                    const key = part.trim().replace(/ /g, '_');
                    if (CLARIFY_FIELD_CONFIG[key] && !fields.includes(key)) fields.push(key);
                });
            }
            if (fields.length === 0) {
                document.getElementById('clarify-card').style.display = 'none';
                return;
            }

            fields.forEach(key => {
                const cfg = CLARIFY_FIELD_CONFIG[key];
                const existing = (constraints || {})[key];
                const div = document.createElement('div');
                div.className = 'clarify-field';
                let inputHtml;
                if (cfg.type === 'select') {
                    const opts = cfg.options.map(o => `<option value="${o}"${existing === o ? ' selected' : ''}>${o}</option>`).join('');
                    inputHtml = `<select id="clarify-${key}"><option value="">-- select --</option>${opts}</select>`;
                } else {
                    inputHtml = `<input type="${cfg.type}" id="clarify-${key}" placeholder="${cfg.placeholder}" value="${existing != null ? existing : ''}">`;
                }
                div.innerHTML = `<label>${cfg.label}</label>${inputHtml}`;
                container.appendChild(div);
            });

            container.dataset.fields = JSON.stringify(fields);
            document.getElementById('clarify-card').style.display = 'block';
        }

        function confirmClarification() {
            const container = document.getElementById('clarify-fields-container');
            const fields = JSON.parse(container.dataset.fields || '[]');
            const updates = {};
            fields.forEach(key => {
                const el = document.getElementById(`clarify-${key}`);
                if (el && el.value.trim()) {
                    updates[key] = (key === 'budget_per_person' || key === 'group_size') ? parseInt(el.value) : el.value.trim();
                }
            });
            currentConstraints = Object.assign({}, currentConstraints, updates);
            document.getElementById('clarify-card').style.display = 'none';
            showStatus('Fields confirmed. Generating itinerary...', 'info');
            generateItinerary();
        }

        function displayUnsupportedRoute(unsupported, suggestions) {
            const card = document.getElementById('unsupported-route-card');
            const msg = document.getElementById('unsupported-route-msg');
            const container = document.getElementById('suggestion-cards-container');

            const origin = unsupported.origin || '?';
            const dest = unsupported.destination || unsupported.destination_type || '?';
            msg.innerHTML = `<strong>${origin} → ${dest}</strong> is not in our route catalog yet.<br>
                We'll try to add it soon! In the meantime, here are the routes we currently support:`;

            container.innerHTML = '';
            (suggestions || []).forEach(r => {
                const card = document.createElement('div');
                card.className = 'suggestion-card';
                card.innerHTML = `
                    <div class="sc-route">${r.origin} → ${r.destination}</div>
                    <div class="sc-meta">${r.destination_type || ''} &bull; ${r.distance_km} km</div>`;
                card.onclick = () => loadSuggestion(r);
                container.appendChild(card);
            });

            card.style.display = 'block';
        }

        function loadSuggestion(route) {
            // Pre-fill the chat input with the suggested route and re-parse
            const existing = document.getElementById('chat-input').value;
            // Replace origin/destination lines if present, else prepend
            const lines = existing.split('\\n').filter(l =>
                !l.match(/from|origin|travelling from/i) && !l.match(/go to|destination|trip to/i)
            );
            lines.unshift(`Trip from ${route.origin} to ${route.destination}`);
            document.getElementById('chat-input').value = lines.join('\\n');
            document.getElementById('unsupported-route-card').style.display = 'none';
            showStatus(`Loaded suggestion: ${route.origin} → ${route.destination}. Review input and click Parse.`, 'info');
        }

        function displayRawJson(data) {
            document.getElementById('raw-json-card').style.display = "block";
            document.getElementById('raw-json-output').textContent = JSON.stringify(data, null, 2);
        }
    </script>
</body>
</html>
"""
