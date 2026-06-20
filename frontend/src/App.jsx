import { useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useItinerary } from "./hooks/useItinerary";
import { ChatRoom } from "./components/chat/ChatRoom";
import { ExtractedPreferences } from "./components/preferences/ExtractedPreferences";
import { ItineraryOptions } from "./components/itinerary/ItineraryOptions";
import { CalendarView } from "./components/itinerary/CalendarView";
import { MapView } from "./components/map/MapView";
import { CostBreakdown } from "./components/cost/CostBreakdown";
import { DelaySimulator } from "./components/delay/DelaySimulator";
import { ToastContainer } from "./components/ui/Toast";
import {
  Map,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Navigation,
  Loader2,
} from "lucide-react";

// ─── Floating minimal header ─────────────────────────────────────────────────
function FloatingHeader({ step, onReset }) {
  const stepIdx = ["chat", "preferences", "itinerary"].indexOf(step);
  const steps = [
    { id: "chat",        label: "Plan" },
    { id: "preferences", label: "Review" },
    { id: "itinerary",   label: "Explore" },
  ];

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 60,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "10px 20px",
        background: "linear-gradient(180deg, rgba(8,12,24,0.85) 0%, transparent 100%)",
        pointerEvents: "none",
      }}
    >
      {/* Logo */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          pointerEvents: "auto",
        }}
      >
        <div
          style={{
            width: "30px",
            height: "30px",
            borderRadius: "8px",
            background: "linear-gradient(135deg, #6c5ce7, #00cec9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Navigation size={15} style={{ color: "white" }} />
        </div>
        <span
          style={{
            fontWeight: 700,
            fontSize: "14px",
            color: "#e2e8f0",
            letterSpacing: "-0.02em",
          }}
        >
          TripGraph <span style={{ color: "#7c6df7" }}>AI</span>
        </span>
      </div>

      {/* Step indicators */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "4px",
          background: "rgba(8,12,26,0.7)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: "999px",
          padding: "4px 8px",
          pointerEvents: "none",
        }}
      >
        {steps.map(({ id, label }, i) => {
          const done = i < stepIdx;
          const active = id === step;
          return (
            <div key={id} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              {i > 0 && (
                <div
                  style={{
                    width: "18px",
                    height: "1px",
                    background: done
                      ? "rgba(124,109,247,0.6)"
                      : "rgba(255,255,255,0.1)",
                    transition: "background 0.4s",
                  }}
                />
              )}
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  letterSpacing: "0.05em",
                  textTransform: "uppercase",
                  padding: "3px 10px",
                  borderRadius: "999px",
                  transition: "all 0.3s",
                  background: active
                    ? "rgba(124,109,247,0.25)"
                    : "transparent",
                  color: active
                    ? "#7c6df7"
                    : done
                    ? "rgba(124,109,247,0.6)"
                    : "rgba(255,255,255,0.3)",
                  border: active
                    ? "1px solid rgba(124,109,247,0.35)"
                    : "1px solid transparent",
                }}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Reset */}
      <button
        onClick={onReset}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "5px",
          fontSize: "11px",
          color: "rgba(255,255,255,0.4)",
          background: "none",
          border: "none",
          cursor: "pointer",
          fontFamily: "Inter, sans-serif",
          pointerEvents: "auto",
          transition: "color 0.2s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = "#e2e8f0")}
        onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.4)")}
      >
        <RefreshCw size={12} />
        Start over
      </button>
    </div>
  );
}

// ─── Left Sliding Panel ───────────────────────────────────────────────────────
const LEFT_PANEL_W = 340;

function LeftPanel({ itinerary, alternatives, scoreBreakdown, costBreakdown, onSimulate, loading, delayResult, explanation }) {
  return (
    <motion.div
      initial={{ x: -LEFT_PANEL_W - 20 }}
      animate={{ x: 0 }}
      exit={{ x: -LEFT_PANEL_W - 20 }}
      transition={{ type: "spring", stiffness: 280, damping: 30 }}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: LEFT_PANEL_W,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        zIndex: 30,
        pointerEvents: "auto",
      }}
    >
      <div
        className="side-panel-left"
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          paddingTop: "64px",
          paddingBottom: "24px",
        }}
      >
        {/* Recommended Plan */}
        <div style={{ padding: "0 14px 8px" }}>
          <p
            style={{
              fontSize: "10px",
              fontWeight: 700,
              color: "#7c6df7",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              padding: "10px 0 6px",
            }}
          >
            Itinerary
          </p>
          <ItineraryOptions
            itinerary={itinerary}
            alternatives={alternatives}
            scoreBreakdown={scoreBreakdown}
          />
        </div>

        {/* Divider */}
        <div className="section-sep" style={{ margin: "4px 14px" }} />

        {/* Explanation */}
        {explanation && (
          <div style={{ padding: "4px 14px 10px" }}>
            <p
              style={{
                fontSize: "11px",
                color: "#64748b",
                lineHeight: 1.65,
                fontStyle: "italic",
                background: "rgba(124,109,247,0.06)",
                border: "1px solid rgba(124,109,247,0.12)",
                borderRadius: "10px",
                padding: "10px 12px",
              }}
            >
              {explanation}
            </p>
          </div>
        )}

        {/* Cost Breakdown */}
        {costBreakdown && (
          <div style={{ padding: "0 14px 10px" }}>
            <p
              style={{
                fontSize: "10px",
                fontWeight: 700,
                color: "#7c6df7",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                padding: "6px 0",
              }}
            >
              Cost Breakdown
            </p>
            <CostBreakdown costBreakdown={costBreakdown} />
          </div>
        )}

        {/* Delay Simulator */}
        <div style={{ padding: "0 14px 10px" }}>
          <p
            style={{
              fontSize: "10px",
              fontWeight: 700,
              color: "#7c6df7",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              padding: "6px 0",
            }}
          >
            Delay Simulator
          </p>
          <DelaySimulator
            onSimulate={onSimulate}
            loading={loading}
            delayResult={delayResult}
          />
        </div>
      </div>
    </motion.div>
  );
}

// ─── Right Sliding Panel ──────────────────────────────────────────────────────
const RIGHT_PANEL_W = 360;

function RightPanel({ timeline, itinerary }) {
  return (
    <motion.div
      initial={{ x: RIGHT_PANEL_W + 20 }}
      animate={{ x: 0 }}
      exit={{ x: RIGHT_PANEL_W + 20 }}
      transition={{ type: "spring", stiffness: 280, damping: 30 }}
      style={{
        position: "absolute",
        top: 0,
        right: 0,
        width: RIGHT_PANEL_W,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        zIndex: 30,
        pointerEvents: "auto",
      }}
    >
      <div
        className="side-panel-right"
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          paddingTop: "52px",
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        <CalendarView
          timeline={timeline}
          tripName={`${itinerary?.route?.origin} → ${itinerary?.route?.destination || itinerary?.destination}`}
        />
      </div>
    </motion.div>
  );
}

// ─── Chat step center card ────────────────────────────────────────────────────
const centerCardVariants = {
  initial: { opacity: 0, scale: 0.94, y: 20 },
  animate: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
  exit:    { opacity: 0, scale: 0.9, y: -24, transition: { duration: 0.3 } },
};

// ─── App root ─────────────────────────────────────────────────────────────────
export default function App() {
  const {
    step, loading,
    constraints, assumptions, missingFields, conflictReport,
    itinerary, alternatives, timeline, mapPoints,
    costBreakdown, scoreBreakdown, explanation, delayResult,
    toasts,
    submitChat, generatePlan, runDelaySimulation, resetToChat,
  } = useItinerary();

  const isItinerary = step === "itinerary";

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        overflow: "hidden",
        background: "#080c18",
        userSelect: "none",
      }}
    >
      {/* ── Full-screen map (always behind) ────── */}
      <MapView
        mapPoints={mapPoints || []}
        interactive={isItinerary}
      />

      {/* ── Vignette overlay on landing/preferences ── */}
      <AnimatePresence>
        {!isItinerary && (
          <motion.div
            key="vignette"
            className="map-vignette"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            style={{ zIndex: 2, pointerEvents: "none" }}
          />
        )}
      </AnimatePresence>

      {/* ── Floating header ─────────────────────── */}
      <FloatingHeader step={step} onReset={resetToChat} />

      {/* ── Main UI overlay ─────────────────────── */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 20,
          pointerEvents: "none",
        }}
      >
        <AnimatePresence mode="wait">
          {/* CHAT step */}
          {step === "chat" && (
            <motion.div
              key="chat"
              variants={centerCardVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "80px 24px 40px",
                pointerEvents: "none",
                zIndex: 25,
              }}
            >
              <div
                className="hero-card"
                style={{
                  width: "100%",
                  maxWidth: "580px",
                  padding: "40px 36px 32px",
                  pointerEvents: "auto",
                  userSelect: "text",
                }}
              >
                <ChatRoom onSubmit={submitChat} loading={loading} />
              </div>
            </motion.div>
          )}

          {/* PREFERENCES step */}
          {step === "preferences" && (
            <motion.div
              key="preferences"
              variants={centerCardVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "80px 24px 40px",
                pointerEvents: "none",
                zIndex: 25,
                overflowY: "auto",
              }}
            >
              <div
                className="hero-card"
                style={{
                  width: "100%",
                  maxWidth: "580px",
                  padding: "40px 36px 32px",
                  pointerEvents: "auto",
                  userSelect: "text",
                }}
              >
                <ExtractedPreferences
                  constraints={constraints}
                  assumptions={assumptions}
                  missingFields={missingFields}
                  conflictReport={conflictReport}
                  onConfirm={generatePlan}
                  loading={loading}
                />
              </div>
            </motion.div>
          )}

          {/* ITINERARY step — map-centric with side panels */}
          {step === "itinerary" && (
            <motion.div
              key="itinerary"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: "absolute",
                inset: 0,
                pointerEvents: "none",
              }}
            >
              <LeftPanel
                itinerary={itinerary}
                alternatives={alternatives}
                scoreBreakdown={scoreBreakdown}
                costBreakdown={costBreakdown}
                onSimulate={runDelaySimulation}
                loading={loading}
                delayResult={delayResult}
                explanation={explanation}
              />
              <RightPanel
                timeline={timeline}
                itinerary={itinerary}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Loading overlay when generating ────── */}
      <AnimatePresence>
        {loading && step === "itinerary" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: "absolute",
              inset: 0,
              zIndex: 80,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(8,12,24,0.5)",
              backdropFilter: "blur(4px)",
              pointerEvents: "auto",
            }}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <Loader2
                size={40}
                style={{
                  color: "#7c6df7",
                  animation: "spin 1s linear infinite",
                }}
              />
              <p style={{ color: "#94a3b8", fontSize: "13px", fontWeight: 500 }}>
                Replanning…
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Toast notifications ──────────────────── */}
      <div
        style={{
          position: "absolute",
          bottom: "24px",
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 100,
          pointerEvents: "auto",
        }}
      >
        <ToastContainer toasts={toasts} />
      </div>

      {/* Spin keyframe via inline style */}
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
