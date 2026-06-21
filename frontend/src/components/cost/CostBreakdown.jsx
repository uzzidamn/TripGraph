import { motion } from "framer-motion";
import { IndianRupee, Wallet } from "lucide-react";

const LABELS = {
  transport:     "Transport",
  hotel:         "Hotel",
  activities:    "Activities",
  food:          "Food",
  miscellaneous: "Misc",
};

// Monochrome silver palette — distinct enough for a stacked breakdown,
// no saturated accents.
const COLORS = ["#eef1f6", "#cfd6e0", "#9aa3b2", "#6b7382", "#4a525e"];

export function CostBreakdown({ costBreakdown }) {
  if (!costBreakdown) return null;

  const { budget_limit, total, ...items } = costBreakdown;
  const entries = Object.entries(LABELS).filter(([k]) => items[k] != null);
  const usagePct = budget_limit ? Math.min(100, (total / budget_limit) * 100) : null;

  return (
    <div
      style={{
        background: "transparent",
        border: "none",
        borderRadius: "12px",
        padding: "14px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          marginBottom: "12px",
        }}
      >
        <Wallet size={13} style={{ color: "var(--chrome)" }} />
        <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--platinum)" }}>Cost breakdown</span>
        <span style={{ marginLeft: "auto", fontSize: "10px", color: "var(--silver)" }}>per person</span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {entries.map(([key, label], i) => {
          const val = items[key];
          const pct = total > 0 ? (val / total) * 100 : 0;
          return (
            <div key={key}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: "3px",
                }}
              >
                <span style={{ fontSize: "11px", color: "var(--silver)" }}>{label}</span>
                <span style={{ fontSize: "11px", color: "var(--platinum)", fontWeight: 600 }}>
                  ₹{val.toLocaleString()}
                </span>
              </div>
              <div
                style={{
                  height: "3px",
                  background: "rgba(0,0,0,0.08)",
                  borderRadius: "999px",
                  overflow: "hidden",
                }}
              >
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.6, delay: i * 0.07 }}
                  style={{
                    height: "100%",
                    background: COLORS[i % COLORS.length],
                    borderRadius: "999px",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          borderTop: "1px solid var(--rim)",
          marginTop: "12px",
          paddingTop: "10px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "12px", color: "var(--platinum)", fontWeight: 600 }}>Total</span>
          <span style={{ fontSize: "16px", color: "var(--platinum)", fontWeight: 800 }}>
            ₹{total?.toLocaleString()}
          </span>
        </div>

        {budget_limit && usagePct != null && (
          <div style={{ marginTop: "8px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "4px",
              }}
            >
              <span style={{ fontSize: "10px", color: "var(--silver)" }}>Budget utilization</span>
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  color: usagePct > 90 ? "#b8862f" : "#3f8f6b",
                }}
              >
                {usagePct.toFixed(0)}% of ₹{budget_limit.toLocaleString()}
              </span>
            </div>
            <div
              style={{
                height: "4px",
                background: "rgba(0,0,0,0.08)",
                borderRadius: "999px",
                overflow: "hidden",
              }}
            >
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${usagePct}%` }}
                transition={{ duration: 0.7 }}
                style={{
                  height: "100%",
                  background: usagePct > 90 ? "#b8862f" : "#3f8f6b",
                  borderRadius: "999px",
                }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
