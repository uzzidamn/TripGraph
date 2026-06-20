import { motion } from "framer-motion";
import { IndianRupee, Wallet } from "lucide-react";

const LABELS = {
  transport:     "Transport",
  hotel:         "Hotel",
  activities:    "Activities",
  food:          "Food",
  miscellaneous: "Misc",
};

const COLORS = ["#7c6df7", "#00cec9", "#fdcb6e", "#00b894", "#e17055"];

export function CostBreakdown({ costBreakdown }) {
  if (!costBreakdown) return null;

  const { budget_limit, total, ...items } = costBreakdown;
  const entries = Object.entries(LABELS).filter(([k]) => items[k] != null);
  const usagePct = budget_limit ? Math.min(100, (total / budget_limit) * 100) : null;

  return (
    <div
      style={{
        background: "rgba(14, 18, 38, 0.6)",
        border: "1px solid rgba(255,255,255,0.07)",
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
        <Wallet size={13} style={{ color: "#00cec9" }} />
        <span style={{ fontSize: "12px", fontWeight: 700, color: "#e2e8f0" }}>Cost breakdown</span>
        <span style={{ marginLeft: "auto", fontSize: "10px", color: "#64748b" }}>per person</span>
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
                <span style={{ fontSize: "11px", color: "#64748b" }}>{label}</span>
                <span style={{ fontSize: "11px", color: "#e2e8f0", fontWeight: 600 }}>
                  ₹{val.toLocaleString()}
                </span>
              </div>
              <div
                style={{
                  height: "3px",
                  background: "rgba(255,255,255,0.07)",
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
          borderTop: "1px solid rgba(255,255,255,0.07)",
          marginTop: "12px",
          paddingTop: "10px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "12px", color: "#e2e8f0", fontWeight: 600 }}>Total</span>
          <span style={{ fontSize: "16px", color: "#7c6df7", fontWeight: 800 }}>
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
              <span style={{ fontSize: "10px", color: "#64748b" }}>Budget utilization</span>
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  color: usagePct > 90 ? "#fdcb6e" : "#00b894",
                }}
              >
                {usagePct.toFixed(0)}% of ₹{budget_limit.toLocaleString()}
              </span>
            </div>
            <div
              style={{
                height: "4px",
                background: "rgba(255,255,255,0.07)",
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
                  background: usagePct > 90 ? "#fdcb6e" : "#00b894",
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
