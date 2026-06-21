import { AnimatePresence, motion } from "framer-motion";
import { Navigation, RefreshCw, Loader2, AlertTriangle, X } from "lucide-react";
import { useEffect, useState, useRef } from "react";

import { useItinerary } from "./hooks/useItinerary";
import { SelectionProvider } from "./hooks/useSelection";

import { ChatRoom } from "./components/chat/ChatRoom";
import { ExtractedPreferences } from "./components/preferences/ExtractedPreferences";
import { RefineQuestions } from "./components/refine/RefineQuestions";
import { CalendarView } from "./components/itinerary/CalendarView";
import { EventPopover } from "./components/itinerary/EventPopover";
import { ReviewCard } from "./components/itinerary/ReviewCard";
import { TripBrief } from "./components/itinerary/TripBrief";
import { MapView } from "./components/map/MapView";
import { CostBreakdown } from "./components/cost/CostBreakdown";
import { DelaySimulator } from "./components/delay/DelaySimulator";
import { DayStrip } from "./components/timeline/DayStrip";
import { ToastContainer } from "./components/ui/Toast";
import { GlassPanel, MetalText, Pill, GhostButton } from "./components/ui/Glass";

const LEFT_W = 340;
const RIGHT_W = 320;
const BOTTOM_LEFT_H = 240; // Cost + delay panel

// ─── Floating header ─────────────────────────────────────────────────────────
function FloatingHeader({ step, onReset }) {
  const stepIdx = ["chat", "preferences", "refine", "itinerary"].indexOf(step);
  const steps = [
    { id: "chat",        label: "Plan" },
    { id: "preferences", label: "Review" },
    { id: "refine",      label: "Refine" },
    { id: "itinerary",   label: "Explore" },
  ];

  return (
    <div
      style={{
        position: "absolute",
        top: 0, left: 0, right: 0,
        zIndex: 60,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 20px",
        background: "linear-gradient(180deg, rgba(245,245,247,0.78) 0%, transparent 100%)",
        pointerEvents: "none",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, pointerEvents: "auto" }}>
        <div
          style={{
            width: 30, height: 30,
            borderRadius: 8,
            background: "linear-gradient(135deg, #2a2d33, #0a0c10)",
            display: "grid",
            placeItems: "center",
            boxShadow: "inset 0 1px 0 rgba(255,255,255,0.18), 0 4px 12px rgba(20,22,28,0.18)",
          }}
        >
          <Navigation size={14} style={{ color: "#f5f5f7" }} />
        </div>
        <MetalText style={{ fontWeight: 700, fontSize: 14 }}>
          TripGraph <span style={{ color: "var(--silver)", fontWeight: 500 }}>AI</span>
        </MetalText>
      </div>

      <GlassPanel
        style={{
          display: "flex",
          alignItems: "center",
          gap: 4,
          padding: "4px 8px",
          borderRadius: 999,
          pointerEvents: "auto",
        }}
      >
        {steps.map(({ id, label }, i) => {
          const done = i < stepIdx;
          const active = id === step;
          return (
            <div key={id} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              {i > 0 && (
                <div
                  style={{
                    width: 14, height: 1,
                    background: done ? "var(--chrome)" : "var(--rim)",
                    transition: "background 0.4s",
                  }}
                />
              )}
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  padding: "3px 10px",
                  borderRadius: 999,
                  transition: "all 0.3s",
                  background: active
                    ? "linear-gradient(180deg, #3a3d44, #1d1f25)"
                    : "transparent",
                  color: active ? "#f5f5f7" : done ? "var(--chrome)" : "var(--silver)",
                  border: active ? "1px solid rgba(0,0,0,0.35)" : "1px solid transparent",
                }}
              >
                {label}
              </span>
            </div>
          );
        })}
      </GlassPanel>

      <button
        onClick={onReset}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 5,
          fontSize: 11,
          color: "var(--silver)",
          background: "none",
          border: "none",
          cursor: "pointer",
          fontFamily: "Inter, sans-serif",
          pointerEvents: "auto",
          transition: "color 0.2s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = "var(--platinum)")}
        onMouseLeave={(e) => (e.currentTarget.style.color = "var(--silver)")}
      >
        <RefreshCw size={12} />
        Start over
      </button>
    </div>
  );
}

// ─── Integrations banner — warns when API keys are missing ──────────────────
function IntegrationsBanner() {
  const [status, setStatus] = useState(null);
  const [dismissed, setDismissed] = useState(false);
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8001";

  useEffect(() => {
    fetch(`${baseUrl}/api/integrations`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setStatus)
      .catch(() => {});
  }, [baseUrl]);

  if (!status || dismissed) return null;
  const critical = ["ors", "geoapify", "openweather"].filter((k) => !status[k]?.configured);
  if (critical.length === 0) return null;

  return (
    <motion.div
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.4 }}
      style={{
        position: "absolute",
        top: 60,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 70,
        pointerEvents: "auto",
        maxWidth: 540,
        width: "calc(100% - 48px)",
      }}
    >
      <GlassPanel strong style={{ padding: "10px 14px", display: "flex", alignItems: "flex-start", gap: 10 }}>
        <AlertTriangle size={14} style={{ color: "var(--chrome)", marginTop: 2, flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--platinum)", marginBottom: 2 }}>
            Planner running in degraded mode
          </div>
          <div style={{ fontSize: 10.5, color: "var(--silver)", lineHeight: 1.5 }}>
            {critical.length} API key{critical.length > 1 ? "s" : ""} missing —{" "}
            {critical.map((k) => k.toUpperCase()).join(", ")}.{" "}
            Trips outside Gurugram → Jaipur / Rishikesh / Tirthan fall back to seeded routes.
            Add keys to <code style={{ color: "var(--chrome)" }}>.env</code> and restart.
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--silver)",
            cursor: "pointer",
            padding: 2,
          }}
        >
          <X size={12} />
        </button>
      </GlassPanel>
    </motion.div>
  );
}

// ─── Itinerary summary chip (top-center on map) ──────────────────────────────
function ItinerarySummaryOverlay({ itinerary, retrievalSource }) {
  if (!itinerary) return null;
  const route = itinerary.route || {};
  const transport = itinerary.transport || {};
  const cost = itinerary.total_cost_per_person;
  return (
    <motion.div
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.3, type: "spring", stiffness: 280, damping: 30 }}
      style={{
        position: "absolute",
        top: 64,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 35,
        pointerEvents: "auto",
        maxWidth: 460,
      }}
    >
      <GlassPanel
        strong
        style={{
          padding: "10px 18px",
          display: "flex",
          alignItems: "center",
          gap: 14,
          borderRadius: 999,
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
          <div style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase" }}>
            Recommended
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--platinum)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {route.origin || "Origin"} → {route.destination || itinerary.destination}
          </div>
        </div>
        <div style={{ width: 1, height: 28, background: "var(--rim)" }} />
        {transport.mode && (
          <Pill tone="muted">{String(transport.mode).replace(/_/g, " ")}</Pill>
        )}
        {cost != null && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
            <div style={{ fontSize: 9.5, color: "var(--silver)", letterSpacing: "0.08em" }}>P.P.</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--chrome)" }}>
              ₹{Number(cost).toLocaleString()}
            </div>
          </div>
        )}
        {retrievalSource && Object.values(retrievalSource).some((s) => s === "api+kg") && (
          <Pill tone="default" title="Live API data enriched the KG for this trip">Live</Pill>
        )}
      </GlassPanel>
    </motion.div>
  );
}

// ─── Delay panel (bottom-left, slim — cost now lives in TripBrief) ────────────
function BottomLeftPanel({ onSimulate, loading, delayResult }) {
  return (
    <motion.div
      initial={{ y: 80 }}
      animate={{ y: 0 }}
      exit={{ y: 80 }}
      transition={{ type: "spring", stiffness: 260, damping: 28 }}
      style={{
        position: "absolute",
        left: 16,
        bottom: 16,
        width: LEFT_W - 32,
        zIndex: 32,
        pointerEvents: "auto",
      }}
    >
      <GlassPanel style={{ padding: 0, overflow: "hidden" }}>
        <DelaySimulator onSimulate={onSimulate} loading={loading} delayResult={delayResult} />
      </GlassPanel>
    </motion.div>
  );
}

const centerCardVariants = {
  initial: { opacity: 0, scale: 0.94, y: 20 },
  animate: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
  exit:    { opacity: 0, scale: 0.9, y: -24, transition: { duration: 0.3 } },
};

export default function App() {
  const {
    step, loading,
    constraints, assumptions, missingFields, conflictReport,
    refinementQuestions,
    itinerary, alternatives, timeline, mapPoints, routePolyline,
    costBreakdown, scoreBreakdown, explanation, delayResult,
    fatiguePerEvent, weatherForecast, traffic, hotelDeals, insightsPerPlace, retrievalSource, flights, trains, review, architectPlan,
    toasts,
    submitChat, confirmPreferences, submitRefinements, skipRefinements,
    runDelaySimulation, resetToChat,
  } = useItinerary();

  const [mapEngine, setMapEngine] = useState("uber"); // prefer Google Uber-style tiles; falls back to CartoDB
  const [fitTick, setFitTick] = useState(0);     // bump to ask MapView to fit-all
  const [selectedDay, setSelectedDay] = useState(1);

  // Reset selected day whenever a new plan loads
  useEffect(() => {
    if (architectPlan?.days?.length) {
      setSelectedDay(architectPlan.days[0].day);
    }
  }, [architectPlan]);

  const isItinerary = step === "itinerary";
  const showLanding = step !== "itinerary";

  return (
    <SelectionProvider>
      <div
        style={{
          position: "fixed",
          inset: 0,
          overflow: "hidden",
          background: "var(--ink)",
          userSelect: "none",
        }}
      >
        <MapView
          mapPoints={mapPoints || []}
          routePolyline={routePolyline}
          interactive={isItinerary}
          panning={showLanding}
          engine={mapEngine}
          onEngineChange={setMapEngine}
          fitAllTick={fitTick}
          selectedDay={isItinerary ? selectedDay : null}
          transportMode={itinerary?.transport?.mode}
          timeline={timeline}
          costBreakdown={costBreakdown}
        />

        <AnimatePresence>
          {showLanding && (
            <>
              <motion.div
                key="veil"
                className="landing-blur-veil"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.6 }}
              />
              <motion.div
                key="vignette"
                className="map-vignette"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.6 }}
                style={{ zIndex: 2 }}
              />
            </>
          )}
        </AnimatePresence>

        <FloatingHeader step={step} onReset={resetToChat} />

        {/* API-key warning banner — shown on every step until dismissed */}
        <IntegrationsBanner />

        <div style={{ position: "absolute", inset: 0, zIndex: 20, pointerEvents: "none" }}>
          <AnimatePresence mode="wait">
            {step === "chat" && (
              <motion.div key="chat" variants={centerCardVariants} initial="initial" animate="animate" exit="exit" style={centerStageStyle}>
                <div className="hero-card" style={heroBoxStyle}>
                  <ChatRoom onSubmit={submitChat} loading={loading} />
                </div>
              </motion.div>
            )}

            {step === "preferences" && (
              <motion.div key="preferences" variants={centerCardVariants} initial="initial" animate="animate" exit="exit" style={centerStageStyle}>
                <div className="hero-card" style={heroBoxStyle}>
                  <ExtractedPreferences
                    constraints={constraints}
                    assumptions={assumptions}
                    missingFields={missingFields}
                    conflictReport={conflictReport}
                    onConfirm={confirmPreferences}
                    loading={loading}
                  />
                </div>
              </motion.div>
            )}

            {step === "refine" && (
              <motion.div key="refine" variants={centerCardVariants} initial="initial" animate="animate" exit="exit" style={centerStageStyle}>
                <div className="hero-card" style={heroBoxStyle}>
                  <RefineQuestions
                    questions={refinementQuestions}
                    onSubmit={submitRefinements}
                    onSkip={skipRefinements}
                    loading={loading}
                  />
                </div>
              </motion.div>
            )}

            {step === "itinerary" && (
              <motion.div
                key="itinerary"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
              >
                {/* LEFT: compact TripBrief (headline + gear + book-ahead + tips) */}
                <TripBrief
                  headline={itinerary?.headline || architectPlan?.headline}
                  costBreakdown={costBreakdown}
                  gearChecklist={itinerary?.gear_checklist || architectPlan?.gear_checklist || []}
                  bookingLeadTimes={itinerary?.booking_lead_times || architectPlan?.booking_lead_times || []}
                  localTips={itinerary?.local_tips || architectPlan?.local_tips || []}
                  excluded={itinerary?.excluded_places || architectPlan?.excluded || []}
                />

                {/* BOTTOM-LEFT: Delay simulator (cost lives inside TripBrief now) */}
                <BottomLeftPanel
                  onSimulate={runDelaySimulation}
                  loading={loading}
                  delayResult={delayResult}
                />

                {/* BOTTOM-CENTER: Day strip — switches focus day on the map */}
                <DayStrip
                  dayThemes={architectPlan?.days?.map(d => ({
                    day: d.day, theme: d.theme,
                    summary: d.day_summary, weather_note: d.weather_note,
                  })) || itinerary?.day_themes || []}
                  weatherForecast={weatherForecast}
                  selectedDay={selectedDay}
                  onSelectDay={(d) => { setSelectedDay(d); setFitTick(t => t + 1); }}
                  totalEvents={timeline.length}
                  costBreakdown={costBreakdown}
                  timeline={timeline}
                />

                {/* RIGHT: Calendar */}
                <motion.div
                  initial={{ x: RIGHT_W + 20 }}
                  animate={{ x: 0 }}
                  exit={{ x: RIGHT_W + 20 }}
                  transition={{ type: "spring", stiffness: 280, damping: 30 }}
                  style={{
                    position: "absolute",
                    top: 60,
                    right: 16,
                    width: RIGHT_W - 32,
                    bottom: 16,
                    zIndex: 30,
                    pointerEvents: "auto",
                  }}
                >
                  <GlassPanel strong style={{ height: "100%", overflow: "hidden", display: "flex", flexDirection: "column" }}>
                    <CalendarView
                      timeline={timeline}
                      tripName={`${itinerary?.route?.origin} → ${itinerary?.route?.destination || itinerary?.destination}`}
                    />
                  </GlassPanel>
                </motion.div>

                {/* Floating itinerary summary chip (top-center) */}
                <ItinerarySummaryOverlay itinerary={itinerary} retrievalSource={retrievalSource} />

                {/* Map-anchored popover for the active event */}
                <EventPopover
                  timeline={timeline}
                  itinerary={itinerary}
                  hotelCandidates={itinerary?.hotel_candidates || []}
                  fatiguePerEvent={fatiguePerEvent}
                  weatherForecast={weatherForecast}
                  hotelDeals={hotelDeals}
                  insightsPerPlace={insightsPerPlace}
                  flights={flights}
                  trains={trains}
                />

                {/* (Architect headline lives in TripBrief; no separate chip needed) */}
                {false && explanation && (
                  <motion.div
                    initial={{ y: 16, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.55 }}
                    style={{
                      position: "absolute",
                      top: 124,
                      left: "50%",
                      transform: "translateX(-50%)",
                      maxWidth: 540,
                      width: "calc(100% - 48px)",
                      zIndex: 34,
                      pointerEvents: "auto",
                    }}
                  >
                    <GlassPanel style={{ padding: "8px 14px" }}>
                      <p style={{ fontSize: 11, color: "var(--chrome)", lineHeight: 1.55, fontStyle: "italic", margin: 0 }}>
                        {explanation}
                      </p>
                    </GlassPanel>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <AnimatePresence>
          {loading && (step === "itinerary" || step === "refine") && (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{
                position: "absolute",
                inset: 0,
                zIndex: 80,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "rgba(245,245,247,0.65)",
                backdropFilter: "blur(6px)",
                pointerEvents: "auto",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
                <Loader2 size={36} style={{ color: "var(--chrome)", animation: "spin 1s linear infinite" }} />
                <p style={{ color: "var(--silver)", fontSize: 13, fontWeight: 500 }}>
                  {step === "refine" ? "Planning…" : "Replanning…"}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div
          style={{
            position: "absolute",
            bottom: 24,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 100,
            pointerEvents: "auto",
          }}
        >
          <ToastContainer toasts={toasts} />
        </div>

        <style>{`
          @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        `}</style>
      </div>
    </SelectionProvider>
  );
}

const centerStageStyle = {
  position: "absolute",
  inset: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "80px 24px 40px",
  pointerEvents: "none",
  zIndex: 25,
  overflowY: "auto",
};

const heroBoxStyle = {
  width: "100%",
  maxWidth: 580,
  padding: "40px 36px 32px",
  pointerEvents: "auto",
  userSelect: "text",
};
