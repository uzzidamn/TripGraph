/**
 * TripBrief — compact floating glass card (top-left) summarising the architect's
 * headline + gear checklist + booking lead times + excluded places.
 *
 * Replaces the old left-rail "ItineraryOptions" panel. Collapses to a single
 * pill button when not needed so the map stays uncluttered.
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ChevronDown, Backpack, ClipboardList, XCircle } from "lucide-react";
import { GlassPanel, Pill } from "../ui/Glass";

export function TripBrief({
  headline,
  costBreakdown,
  gearChecklist = [],
  bookingLeadTimes = [],
  localTips = [],
  excluded = [],
}) {
  const [open, setOpen] = useState(true);
  if (!headline && !gearChecklist.length && !bookingLeadTimes.length) return null;

  return (
    <motion.div
      initial={{ x: -40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 280, damping: 30 }}
      style={{
        position: "absolute",
        top: 60,
        left: 16,
        width: 320,
        maxHeight: "calc(100vh - 260px)",
        zIndex: 32,
        pointerEvents: "auto",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <GlassPanel
        strong
        style={{
          padding: 14,
          display: "flex",
          flexDirection: "column",
          gap: 10,
          overflow: "hidden",
        }}
      >
        <div
          style={{ display: "flex", alignItems: "flex-start", gap: 8, cursor: "pointer" }}
          onClick={() => setOpen((v) => !v)}
        >
          <Sparkles size={13} style={{ color: "var(--chrome)", marginTop: 2, flexShrink: 0 }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase" }}>
              The plan
            </div>
            <p style={{ fontSize: 12.5, fontWeight: 600, color: "var(--platinum)", lineHeight: 1.45, marginTop: 2 }}>
              {headline}
            </p>
          </div>
          <ChevronDown
            size={14}
            style={{
              color: "var(--silver)",
              transform: open ? "rotate(180deg)" : "none",
              transition: "transform 0.2s",
              flexShrink: 0,
              marginTop: 2,
            }}
          />
        </div>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              style={{ overflow: "hidden", display: "flex", flexDirection: "column", gap: 12 }}
            >
              {costBreakdown && (
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline",
                              padding: "8px 10px", background: "rgba(0,0,0,0.04)", borderRadius: 8 }}>
                  <span style={{ fontSize: 11, color: "var(--silver)" }}>Per person</span>
                  <span style={{ fontSize: 16, fontWeight: 800, color: "var(--platinum)" }}>
                    ₹{(costBreakdown.total || 0).toLocaleString()}
                  </span>
                </div>
              )}

              {gearChecklist.length > 0 && (
                <section>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                    <Backpack size={11} style={{ color: "var(--chrome)" }} />
                    <span style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em",
                                   color: "var(--silver)", textTransform: "uppercase" }}>
                      Pack this
                    </span>
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {gearChecklist.slice(0, 8).map((g, i) => (
                      <Pill key={i} tone="muted">{g}</Pill>
                    ))}
                  </div>
                </section>
              )}

              {bookingLeadTimes.length > 0 && (
                <section>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                    <ClipboardList size={11} style={{ color: "var(--chrome)" }} />
                    <span style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em",
                                   color: "var(--silver)", textTransform: "uppercase" }}>
                      Book ahead
                    </span>
                  </div>
                  <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex",
                               flexDirection: "column", gap: 6 }}>
                    {bookingLeadTimes.slice(0, 4).map((b, i) => (
                      <li key={i} style={{ fontSize: 11, color: "var(--chrome)", lineHeight: 1.4 }}>
                        <strong style={{ color: "var(--platinum)" }}>{b.item}</strong>
                        {b.how_far && <span style={{ color: "var(--silver)" }}> — {b.how_far}</span>}
                        {b.where && (
                          <div style={{ fontSize: 10, color: "var(--silver)", fontStyle: "italic" }}>
                            {b.where}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {localTips.length > 0 && (
                <section>
                  <div style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em",
                                color: "var(--silver)", textTransform: "uppercase", marginBottom: 6 }}>
                    Local tips
                  </div>
                  <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                    {localTips.slice(0, 3).map((t, i) => (
                      <li key={i} style={{
                        fontSize: 11, color: "var(--chrome)", lineHeight: 1.5, padding: "4px 0",
                        borderTop: i ? "1px solid var(--rim)" : "none",
                      }}>
                        {t}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {excluded.length > 0 && (
                <details>
                  <summary style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
                    <XCircle size={11} style={{ color: "var(--silver)" }} />
                    <span style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em",
                                   color: "var(--silver)", textTransform: "uppercase" }}>
                      Why we didn't pick ({excluded.length})
                    </span>
                  </summary>
                  <ul style={{ listStyle: "none", padding: "6px 0 0", margin: 0 }}>
                    {excluded.slice(0, 5).map((e, i) => (
                      <li key={i} style={{ fontSize: 10.5, color: "var(--silver)", lineHeight: 1.45, marginTop: 4 }}>
                        <strong style={{ color: "var(--chrome)" }}>{e.name}</strong>: {e.reason}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </GlassPanel>
    </motion.div>
  );
}
