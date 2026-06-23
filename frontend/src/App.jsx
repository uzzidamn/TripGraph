import { AnimatePresence, motion } from "framer-motion";
import { RefreshCw, Loader2, AlertTriangle, X } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { PalmCompass } from "./components/ui/PalmCompass";

import { useItinerary } from "./hooks/useItinerary";
import { SelectionProvider } from "./hooks/useSelection";

import { ChatRoom } from "./components/chat/ChatRoom";
import { ExtractedPreferences } from "./components/preferences/ExtractedPreferences";
import { RefineQuestions } from "./components/refine/RefineQuestions";
import { CalendarView } from "./components/itinerary/CalendarView";
import { EventPopover } from "./components/itinerary/EventPopover";
import { TripBrief } from "./components/itinerary/TripBrief";
import { MapView } from "./components/map/MapView";
import { CostPanel } from "./components/cost/CostPanel";
import { DelaySimulator } from "./components/delay/DelaySimulator";
import { DayStrip } from "./components/timeline/DayStrip";
import { ToastContainer } from "./components/ui/Toast";
import { GlassPanel, MetalText, Pill } from "./components/ui/Glass";

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
        height: 56,
        padding: "12px 20px",
        background: "linear-gradient(180deg, rgba(245,245,247,0.78) 0%, transparent 100%)",
        pointerEvents: "none",
      }}
    >
      {/* TripGraph logo — absolute top-left */}
      <div style={{
        position: "absolute", top: 12, left: 20,
        display: "flex", alignItems: "center", gap: 10, pointerEvents: "auto",
      }}>
        <div style={{
          width: 32, height: 32, borderRadius: 9,
          background: "linear-gradient(135deg, #2a2d33, #0a0c10)",
          display: "grid", placeItems: "center",
          boxShadow: "inset 0 1px 0 rgba(255,255,255,0.18), 0 4px 12px rgba(20,22,28,0.18)",
        }}>
          <PalmCompass size={20} color="#f5f5f7" />
        </div>
        <MetalText style={{ fontWeight: 700, fontSize: 14 }}>
          TripGraph <span style={{ color: "var(--silver)", fontWeight: 500 }}>AI</span>
        </MetalText>
      </div>

      {/* Steps pill — absolute top-center */}
      <GlassPanel
        style={{
          position: "absolute",
          top: 12,
          left: "50%",
          transform: "translateX(-50%)",
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
function ItinerarySummaryOverlay({ itinerary, onReset }) {
  if (!itinerary) return null;
  const route = itinerary.route || {};
  const transport = itinerary.transport || {};
  return (
    <motion.div
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.3, type: "spring", stiffness: 280, damping: 30 }}
      style={{
        position: "absolute",
        top: 70,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        zIndex: 35,
        pointerEvents: "none",
      }}
    >
      <GlassPanel
        strong
        style={{
          padding: "10px 22px 12px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 6,
          borderRadius: 18,
          pointerEvents: "auto",
        }}
      >
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          fontSize: 14, fontWeight: 700, color: "var(--platinum)",
          whiteSpace: "nowrap",
        }}>
          <span>{route.origin || "Origin"}</span>
          <span style={{ color: "var(--silver)", fontSize: 12 }}>→</span>
          <span>{route.destination || itinerary.destination}</span>
          {transport.mode && (
            <Pill tone="muted" style={{ marginLeft: 4 }}>
              {String(transport.mode).replace(/_/g, " ")}
            </Pill>
          )}
        </div>
        <button
          onClick={onReset}
          style={{
            display: "inline-flex", alignItems: "center", gap: 5,
            padding: "4px 14px", borderRadius: 999,
            fontSize: 10, fontWeight: 700, letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "var(--chrome)",
            background: "rgba(255,255,255,0.6)",
            border: "1px solid var(--rim)",
            cursor: "pointer",
            fontFamily: "Inter, sans-serif",
            transition: "background 0.15s, color 0.15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "linear-gradient(180deg, #3a3d44, #1d1f25)";
            e.currentTarget.style.color = "#f5f5f7";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.6)";
            e.currentTarget.style.color = "var(--chrome)";
          }}
        >
          <RefreshCw size={10} />
          Start Over
        </button>
      </GlassPanel>
    </motion.div>
  );
}

// ─── Bottom-left: DelaySimulator only (cost panel moved into calendar) ───────
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
        bottom: 18,
        width: LEFT_W - 32,
        zIndex: 32,
        pointerEvents: "auto",
      }}
    >
      <DelaySimulator onSimulate={onSimulate} loading={loading} delayResult={delayResult} />
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
    fatiguePerEvent, weatherForecast, traffic, hotelDeals, insightsPerPlace, retrievalSource, flights, trains, review, architectPlan, segmentPolylines,
    toasts,
    submitChat, confirmPreferences, submitRefinements, skipRefinements,
    runDelaySimulation, resetToChat,
  } = useItinerary();

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
          fitAllTick={fitTick}
          selectedDay={isItinerary ? selectedDay : null}
          onSelectDay={setSelectedDay}
          transportMode={itinerary?.transport?.mode}
          timeline={timeline}
          segmentPolylines={segmentPolylines}
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

                {/* BOTTOM-LEFT: Delay simulator alone (cost moved into calendar) */}
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
                  onSelectDay={(d) => setSelectedDay(d)}
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
                    display: "flex",
                    flexDirection: "column",
                    gap: 10,
                  }}
                >
                  {/* Cost panel above the calendar — cost lives next to the itinerary it describes */}
                  <CostPanel costBreakdown={costBreakdown} timeline={timeline} />

                  <GlassPanel strong style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
                    <CalendarView
                      timeline={timeline}
                      tripName={`${itinerary?.route?.origin} → ${itinerary?.route?.destination || itinerary?.destination}`}
                      onSelectDay={setSelectedDay}
                    />
                  </GlassPanel>
                </motion.div>

                {/* Floating itinerary summary chip (top-center) */}
                <ItinerarySummaryOverlay itinerary={itinerary} onReset={resetToChat} />

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
