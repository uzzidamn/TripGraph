import { motion } from "framer-motion";
import { CheckCircle, AlertTriangle, Edit3, Loader2, ClipboardCheck } from "lucide-react";

const FIELD_LABELS = {
  origin:               "Origin",
  destination:          "Destination",
  destination_type:     "Destination type",
  budget_per_person:    "Budget / person",
  group_size:           "Group size",
  hotel_tier:           "Hotel tier",
  transport_preference: "Transport",
  avoid_night_driving:  "Avoid night driving",
  must_include:         "Must include",
  return_deadline:      "Return by",
  trip_duration:        "Duration",
};

function formatValue(key, val) {
  if (val === null || val === undefined) return "—";
  if (key === "budget_per_person") return `₹${val.toLocaleString()}`;
  if (key === "avoid_night_driving") return val ? "Yes" : "No";
  if (Array.isArray(val)) return val.join(", ") || "—";
  return String(val);
}

function FieldRow({ label, value }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "8px 14px",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      <span style={{ fontSize: "11px", color: "#64748b", flexShrink: 0, width: "140px" }}>
        {label}
      </span>
      <span
        style={{
          fontSize: "12px",
          color: value === "—" ? "#64748b" : "#e2e8f0",
          fontWeight: value === "—" ? 400 : 600,
          textAlign: "right",
          fontStyle: value === "—" ? "italic" : "normal",
        }}
      >
        {value}
      </span>
    </div>
  );
}

export function ExtractedPreferences({
  constraints,
  assumptions,
  missingFields,
  conflictReport,
  onConfirm,
  loading,
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Header */}
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            width: "38px",
            height: "38px",
            borderRadius: "10px",
            background: "rgba(0,184,148,0.2)",
            border: "1px solid rgba(0,184,148,0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 12px",
          }}
        >
          <ClipboardCheck size={18} style={{ color: "#00b894" }} />
        </div>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: 800,
            color: "#e2e8f0",
            letterSpacing: "-0.02em",
            marginBottom: "4px",
          }}
        >
          Extracted preferences
        </h2>
        <p style={{ fontSize: "12px", color: "#64748b" }}>
          Review what AI understood from your conversation
        </p>
      </div>

      {/* Constraints table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: "12px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "10px 14px",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <CheckCircle size={12} style={{ color: "#00b894" }} />
          <span
            style={{
              fontSize: "10px",
              fontWeight: 700,
              color: "#64748b",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Constraints
          </span>
        </div>
        {Object.entries(FIELD_LABELS).map(([key, label]) => (
          <FieldRow
            key={key}
            label={label}
            value={formatValue(key, constraints?.[key])}
          />
        ))}
      </motion.div>

      {/* Assumptions */}
      {Object.keys(assumptions || {}).length > 0 && (
        <div
          style={{
            background: "rgba(253,203,110,0.07)",
            border: "1px solid rgba(253,203,110,0.2)",
            borderRadius: "10px",
            padding: "12px 14px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
            <Edit3 size={12} style={{ color: "#fdcb6e" }} />
            <span
              style={{
                fontSize: "10px",
                fontWeight: 700,
                color: "#fdcb6e",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              Assumptions made
            </span>
          </div>
          <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "4px" }}>
            {Object.entries(assumptions).map(([k, v]) => (
              <li key={k} style={{ fontSize: "11px", color: "#94a3b8" }}>
                <span style={{ color: "#e2e8f0", fontWeight: 600 }}>
                  {FIELD_LABELS[k] ?? k}
                </span>
                : {v}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Conflicts */}
      {conflictReport?.has_conflicts && (
        <div
          style={{
            background: "rgba(225,112,85,0.08)",
            border: "1px solid rgba(225,112,85,0.25)",
            borderRadius: "10px",
            padding: "12px 14px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
            <AlertTriangle size={12} style={{ color: "#e17055" }} />
            <span
              style={{
                fontSize: "10px",
                fontWeight: 700,
                color: "#e17055",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              Conflicts detected
            </span>
          </div>
          <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "4px" }}>
            {conflictReport.conflicts.map((c, i) => (
              <li key={i} style={{ fontSize: "11px", color: "#94a3b8" }}>
                • {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* CTA */}
      <button
        onClick={() => onConfirm(constraints)}
        disabled={loading || conflictReport?.has_conflicts}
        className="btn-primary"
        style={{
          width: "100%",
          padding: "13px 0",
          borderRadius: "12px",
          border: "none",
          color: "white",
          fontSize: "13px",
          fontWeight: 700,
          cursor: loading || conflictReport?.has_conflicts ? "not-allowed" : "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          fontFamily: "Inter, sans-serif",
          letterSpacing: "-0.01em",
        }}
      >
        {loading ? (
          <>
            <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} />
            Generating itinerary…
          </>
        ) : (
          "Generate itinerary →"
        )}
      </button>
    </div>
  );
}
