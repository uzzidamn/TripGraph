/**
 * CostPanel — collapsible cost breakdown.
 *
 * Collapsed (default): single bar with total + per-person + budget %.
 * Expanded: category totals on top, full line-item ledger below.
 */
import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wallet, ChevronUp, ChevronDown } from "lucide-react";
import { GlassPanel } from "../ui/Glass";

const CATEGORY_LABEL = {
  transport: "Transport",
  hotel: "Hotel",
  activities: "Activities",
  food: "Food",
  miscellaneous: "Misc",
};

const TYPE_TO_CATEGORY = {
  travel: "transport",
  hotel: "hotel",
  activity: "activities",
  meal: "food",
  rest: "miscellaneous",
};

const CATEGORY_COLORS = {
  transport: "#3b82a6",
  hotel: "#6e7382",
  activities: "#b8862f",
  food: "#3f8f6b",
  miscellaneous: "#8a8f9c",
};

export function CostPanel({ costBreakdown, timeline = [] }) {
  const [open, setOpen] = useState(true);
  if (!costBreakdown) return null;

  const { budget_limit, total } = costBreakdown;
  const usagePct = budget_limit ? Math.min(100, (total / budget_limit) * 100) : null;

  // Group line items by day for the ledger
  const ledgerByDay = useMemo(() => {
    const map = new Map();
    for (const ev of timeline) {
      if (!ev.cost || ev.cost <= 0) continue;
      const day = ev.day || 1;
      if (!map.has(day)) map.set(day, []);
      map.get(day).push(ev);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }, [timeline]);

  const categoryEntries = Object.entries(CATEGORY_LABEL)
    .filter(([k]) => costBreakdown[k] != null && costBreakdown[k] > 0);

  const hotelBreakdown = costBreakdown.hotel_breakdown || [];

  return (
    <GlassPanel strong style={{ overflow: "hidden" }}>
      {/* Collapsed header bar */}
      <div
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "flex", alignItems: "center", gap: 10, padding: "12px 14px",
          cursor: "pointer", userSelect: "none",
        }}
      >
        <Wallet size={14} style={{ color: "var(--chrome)", flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em",
            color: "var(--silver)", textTransform: "uppercase",
          }}>
            Cost breakdown
          </div>
          <div style={{ fontSize: 16, fontWeight: 800, color: "var(--platinum)", marginTop: 1 }}>
            ₹{(total || 0).toLocaleString()}
            <span style={{ fontSize: 10, fontWeight: 500, color: "var(--silver)", marginLeft: 6 }}>
              per person
            </span>
          </div>
        </div>
        {usagePct != null && (
          <div style={{ textAlign: "right" }}>
            <div style={{
              fontSize: 10.5, fontWeight: 700,
              color: usagePct > 90 ? "#b8862f" : "#3f8f6b",
            }}>
              {usagePct.toFixed(0)}% used
            </div>
            <div style={{ fontSize: 9, color: "var(--silver)" }}>
              of ₹{budget_limit.toLocaleString()}
            </div>
          </div>
        )}
        {open ? <ChevronUp size={14} style={{ color: "var(--silver)" }} /> :
                <ChevronDown size={14} style={{ color: "var(--silver)" }} />}
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden", borderTop: "1px solid var(--rim)" }}
          >
            {/* Category summary (top) */}
            <div style={{ padding: "10px 14px 4px" }}>
              <div style={{
                fontSize: 9, fontWeight: 700, letterSpacing: "0.12em",
                color: "var(--silver)", textTransform: "uppercase", marginBottom: 8,
              }}>
                By category
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {categoryEntries.map(([key, label]) => {
                  const val = costBreakdown[key] || 0;
                  const pct = total > 0 ? (val / total) * 100 : 0;
                  const color = CATEGORY_COLORS[key];
                  return (
                    <div key={key}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                        <span style={{ fontSize: 10.5, color: "var(--chrome)" }}>{label}</span>
                        <span style={{ fontSize: 10.5, color: "var(--platinum)", fontWeight: 700 }}>
                          ₹{val.toLocaleString()}
                        </span>
                      </div>
                      <div style={{
                        height: 3, background: "rgba(0,0,0,0.06)",
                        borderRadius: 999, overflow: "hidden",
                      }}>
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.4 }}
                          style={{ height: "100%", background: color, borderRadius: 999 }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Hotel breakdown — per-hotel cost when multiple stays */}
            {hotelBreakdown.length > 0 && (
              <div style={{ padding: "8px 14px 4px", borderTop: "1px solid var(--rim)" }}>
                <div style={{
                  fontSize: 9, fontWeight: 700, letterSpacing: "0.12em",
                  color: "var(--silver)", textTransform: "uppercase", marginBottom: 6,
                }}>
                  Hotels
                </div>
                {hotelBreakdown.map((h, i) => (
                  <div key={i} style={{
                    display: "flex", flexDirection: "column",
                    padding: "4px 0",
                    borderTop: i ? "1px solid var(--rim)" : "none",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ fontSize: 11, color: "var(--platinum)", fontWeight: 600 }}>
                        {h.name}
                      </span>
                      <span style={{ fontSize: 11, color: "var(--platinum)", fontWeight: 700 }}>
                        ₹{Number(h.total_pp).toLocaleString()}
                      </span>
                    </div>
                    {(h.nights || h.per_night) && (
                      <div style={{ fontSize: 10, color: "var(--silver)" }}>
                        {h.nights} night{h.nights !== 1 ? "s" : ""}
                        {h.per_night ? ` × ₹${Number(h.per_night).toLocaleString()}/night` : ""}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Line-item ledger (below) */}
            {ledgerByDay.length > 0 && (
              <div style={{ padding: "8px 14px 12px", borderTop: "1px solid var(--rim)" }}>
                <div style={{
                  fontSize: 9, fontWeight: 700, letterSpacing: "0.12em",
                  color: "var(--silver)", textTransform: "uppercase", marginBottom: 8,
                }}>
                  Line items
                </div>
                {ledgerByDay.map(([day, events]) => (
                  <div key={day} style={{ marginBottom: 8 }}>
                    <div style={{
                      fontSize: 10, fontWeight: 700, color: "var(--chrome)",
                      marginBottom: 4, marginTop: 2,
                    }}>
                      Day {day}
                    </div>
                    {events.map((ev) => {
                      const category = TYPE_TO_CATEGORY[ev.type] || "miscellaneous";
                      return (
                        <div key={ev.id} style={{
                          display: "flex", alignItems: "center", justifyContent: "space-between",
                          fontSize: 10.5, padding: "2px 0",
                        }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0, flex: 1 }}>
                            <span style={{
                              width: 6, height: 6, borderRadius: 999,
                              background: CATEGORY_COLORS[category], flexShrink: 0,
                            }} />
                            <span style={{
                              color: "var(--chrome)", overflow: "hidden",
                              textOverflow: "ellipsis", whiteSpace: "nowrap",
                            }}>
                              {ev.title}
                            </span>
                          </div>
                          <span style={{ color: "var(--platinum)", fontWeight: 600, marginLeft: 8 }}>
                            ₹{Number(ev.cost).toLocaleString()}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}

            {/* Total at the bottom */}
            <div style={{
              padding: "10px 14px",
              borderTop: "1px solid var(--rim)",
              background: "rgba(0,0,0,0.02)",
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: "var(--platinum)" }}>Grand total</span>
              <span style={{ fontSize: 15, fontWeight: 800, color: "var(--platinum)" }}>
                ₹{(total || 0).toLocaleString()}
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </GlassPanel>
  );
}
