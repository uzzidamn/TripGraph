import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Clock, Loader2, ChevronDown, ChevronUp } from "lucide-react";

export function DelaySimulator({ onSimulate, loading, delayResult }) {
  const [minutes, setMinutes] = useState(90);
  const [showChanges, setShowChanges] = useState(true);

  return (
    <div
      style={{
        background: "rgba(255,255,255,0.55)",
        backdropFilter: "blur(20px)",
        border: "1px solid var(--rim)",
        borderRadius: 12,
        padding: 14,
        boxShadow: "0 1px 3px rgba(20,22,28,0.06)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
        <AlertTriangle size={13} style={{ color: "#b8862f" }} />
        <span style={{
          fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em",
          color: "var(--silver)", textTransform: "uppercase",
        }}>
          Delay Simulator
        </span>
      </div>

      <div style={{ marginBottom: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontSize: 10.5, color: "var(--chrome)" }}>Departure delay</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: "var(--platinum)" }}>
            {minutes} min
          </span>
        </div>
        <input
          type="range"
          min={15}
          max={300}
          step={15}
          value={minutes}
          onChange={(e) => setMinutes(Number(e.target.value))}
          style={{
            width: "100%",
            accentColor: "#2a2d33",
          }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
          <span style={{ fontSize: 9, color: "var(--silver)" }}>15 min</span>
          <span style={{ fontSize: 9, color: "var(--silver)" }}>5 hours</span>
        </div>
      </div>

      <button
        onClick={() => onSimulate(minutes)}
        disabled={loading}
        style={{
          width: "100%",
          padding: "9px 0",
          borderRadius: 8,
          background: loading
            ? "rgba(0,0,0,0.04)"
            : "linear-gradient(180deg, #3a3d44, #1d1f25)",
          border: "1px solid rgba(0,0,0,0.35)",
          color: loading ? "var(--silver)" : "#f5f5f7",
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "0.04em",
          cursor: loading ? "not-allowed" : "pointer",
          opacity: loading ? 0.55 : 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          fontFamily: "Inter, sans-serif",
          transition: "filter 0.2s, opacity 0.2s",
          boxShadow: "inset 0 1px 0 rgba(255,255,255,0.18), 0 2px 6px rgba(20,22,28,0.18)",
        }}
        onMouseEnter={(e) => {
          if (!loading) e.currentTarget.style.filter = "brightness(1.12)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.filter = "none";
        }}
      >
        {loading ? (
          <>
            <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />
            Replanning…
          </>
        ) : (
          <>
            <Clock size={12} />
            Simulate {minutes}-min delay
          </>
        )}
      </button>

      <AnimatePresence>
        {delayResult && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            style={{ overflow: "hidden", marginTop: 10 }}
          >
            <div style={{ borderTop: "1px solid var(--rim)", paddingTop: 10 }}>
              <div
                style={{
                  display: "flex", alignItems: "center",
                  justifyContent: "space-between", cursor: "pointer",
                  marginBottom: 8,
                }}
                onClick={() => setShowChanges((p) => !p)}
              >
                <span style={{
                  fontSize: 9.5, fontWeight: 700, letterSpacing: "0.1em",
                  color: "var(--silver)", textTransform: "uppercase",
                }}>
                  Changes ({delayResult.changes?.length ?? 0})
                </span>
                {showChanges ? (
                  <ChevronUp size={12} style={{ color: "var(--silver)" }} />
                ) : (
                  <ChevronDown size={12} style={{ color: "var(--silver)" }} />
                )}
              </div>

              {showChanges && delayResult.changes?.map((c, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  style={{
                    display: "flex", gap: 6, alignItems: "flex-start",
                    fontSize: 10.5, color: "var(--chrome)", marginBottom: 4,
                    lineHeight: 1.4,
                  }}
                >
                  <span style={{ color: "#b8862f", marginTop: 1, flexShrink: 0 }}>•</span>
                  {c}
                </motion.div>
              ))}

              {delayResult.explanation && (
                <p style={{
                  fontSize: 10.5, color: "var(--silver)",
                  background: "rgba(0,0,0,0.04)", borderRadius: 8,
                  padding: "8px 10px", lineHeight: 1.5,
                  marginTop: 6, fontStyle: "italic",
                }}>
                  {delayResult.explanation}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
