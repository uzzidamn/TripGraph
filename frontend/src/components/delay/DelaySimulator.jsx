import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Clock, Loader2, ChevronDown, ChevronUp } from "lucide-react";

export function DelaySimulator({ onSimulate, loading, delayResult }) {
  const [minutes, setMinutes] = useState(90);
  const [showChanges, setShowChanges] = useState(true);

  return (
    <div
      style={{
        background: "rgba(14, 18, 38, 0.6)",
        border: "1px solid rgba(255,255,255,0.07)",
        borderRadius: "12px",
        padding: "14px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "12px" }}>
        <AlertTriangle size={13} style={{ color: "#fdcb6e" }} />
        <span style={{ fontSize: "12px", fontWeight: 700, color: "#e2e8f0" }}>
          Delay Simulator
        </span>
      </div>

      <div style={{ marginBottom: "12px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
          <span style={{ fontSize: "11px", color: "#64748b" }}>Departure delay</span>
          <span style={{ fontSize: "11px", fontWeight: 700, color: "#fdcb6e" }}>
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
        />
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "4px" }}>
          <span style={{ fontSize: "9px", color: "rgba(255,255,255,0.25)" }}>15 min</span>
          <span style={{ fontSize: "9px", color: "rgba(255,255,255,0.25)" }}>5 hours</span>
        </div>
      </div>

      <button
        onClick={() => onSimulate(minutes)}
        disabled={loading}
        style={{
          width: "100%",
          padding: "9px 0",
          borderRadius: "8px",
          background: "rgba(253,203,110,0.1)",
          border: "1px solid rgba(253,203,110,0.25)",
          color: "#fdcb6e",
          fontSize: "11px",
          fontWeight: 600,
          cursor: loading ? "not-allowed" : "pointer",
          opacity: loading ? 0.5 : 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
          fontFamily: "Inter, sans-serif",
          transition: "border-color 0.2s, background 0.2s",
        }}
        onMouseEnter={(e) => {
          if (!loading) e.currentTarget.style.borderColor = "rgba(253,203,110,0.5)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "rgba(253,203,110,0.25)";
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
            style={{ overflow: "hidden", marginTop: "10px" }}
          >
            <div
              style={{
                borderTop: "1px solid rgba(255,255,255,0.07)",
                paddingTop: "10px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  cursor: "pointer",
                  marginBottom: "8px",
                }}
                onClick={() => setShowChanges((p) => !p)}
              >
                <span style={{ fontSize: "10px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  Changes ({delayResult.changes?.length ?? 0})
                </span>
                {showChanges ? (
                  <ChevronUp size={12} style={{ color: "#64748b" }} />
                ) : (
                  <ChevronDown size={12} style={{ color: "#64748b" }} />
                )}
              </div>

              {showChanges && delayResult.changes?.map((c, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  style={{
                    display: "flex",
                    gap: "6px",
                    alignItems: "flex-start",
                    fontSize: "11px",
                    color: "#94a3b8",
                    marginBottom: "4px",
                  }}
                >
                  <span style={{ color: "#fdcb6e", marginTop: "1px" }}>•</span>
                  {c}
                </motion.div>
              ))}

              {delayResult.explanation && (
                <p
                  style={{
                    fontSize: "10px",
                    color: "#64748b",
                    background: "rgba(255,255,255,0.03)",
                    borderRadius: "8px",
                    padding: "8px 10px",
                    lineHeight: 1.6,
                    marginTop: "6px",
                    fontStyle: "italic",
                  }}
                >
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
