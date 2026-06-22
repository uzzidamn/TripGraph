import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle, AlertTriangle, Edit3, Loader2, ClipboardCheck,
  ArrowLeft, Zap, PencilLine, RotateCcw,
} from "lucide-react";

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

function getConflictingFields(conflicts = []) {
  const fields = new Set();
  for (const c of conflicts) {
    if (/hotel.?tier|comfort|expedition/i.test(c)) fields.add("hotel_tier");
    if (/budget/i.test(c)) fields.add("budget_per_person");
    if (/avoid.?night.?driving/i.test(c)) fields.add("avoid_night_driving");
    if (/transport.?preference|self.?drive/i.test(c)) fields.add("transport_preference");
  }
  return [...fields];
}

const HOTEL_TIERS = ["budget", "comfort", "expedition"];

function ConflictFieldEditor({ fieldKey, value, onChange }) {
  if (fieldKey === "hotel_tier") {
    return (
      <select
        value={value ?? "budget"}
        onChange={(e) => onChange(e.target.value)}
        style={{
          background: "rgba(0,0,0,0.4)",
          border: "1px solid rgba(225,112,85,0.4)",
          borderRadius: "6px",
          color: "var(--platinum)",
          fontSize: "11px",
          padding: "4px 8px",
          fontFamily: "Inter, sans-serif",
          cursor: "pointer",
        }}
      >
        {HOTEL_TIERS.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>
    );
  }
  if (fieldKey === "budget_per_person") {
    return (
      <input
        type="number"
        value={value ?? ""}
        min={0}
        step={500}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          background: "rgba(0,0,0,0.4)",
          border: "1px solid rgba(225,112,85,0.4)",
          borderRadius: "6px",
          color: "var(--platinum)",
          fontSize: "11px",
          padding: "4px 8px",
          width: "110px",
          fontFamily: "Inter, sans-serif",
        }}
      />
    );
  }
  if (fieldKey === "avoid_night_driving") {
    return (
      <select
        value={value ? "true" : "false"}
        onChange={(e) => onChange(e.target.value === "true")}
        style={{
          background: "rgba(0,0,0,0.4)",
          border: "1px solid rgba(225,112,85,0.4)",
          borderRadius: "6px",
          color: "var(--platinum)",
          fontSize: "11px",
          padding: "4px 8px",
          fontFamily: "Inter, sans-serif",
          cursor: "pointer",
        }}
      >
        <option value="true">Yes</option>
        <option value="false">No</option>
      </select>
    );
  }
  if (fieldKey === "transport_preference") {
    const opts = ["cab", "self_drive", "train", "bus"];
    const current = Array.isArray(value) ? value : [];
    return (
      <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
        {opts.map((o) => (
          <button
            key={o}
            onClick={() => {
              const next = current.includes(o)
                ? current.filter((x) => x !== o)
                : [...current, o];
              onChange(next);
            }}
            style={{
              background: current.includes(o)
                ? "rgba(225,112,85,0.25)"
                : "rgba(255,255,255,0.05)",
              border: `1px solid ${current.includes(o) ? "rgba(225,112,85,0.5)" : "rgba(255,255,255,0.1)"}`,
              borderRadius: "5px",
              color: current.includes(o) ? "#e17055" : "var(--silver)",
              fontSize: "10px",
              padding: "3px 7px",
              cursor: "pointer",
              fontFamily: "Inter, sans-serif",
            }}
          >
            {o.replace("_", " ")}
          </button>
        ))}
      </div>
    );
  }
  return null;
}

function FieldRow({ label, value }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "8px 14px",
        borderBottom: "1px solid var(--rim)",
      }}
    >
      <span style={{ fontSize: "11px", color: "var(--silver)", flexShrink: 0, width: "140px" }}>
        {label}
      </span>
      <span
        style={{
          fontSize: "12px",
          color: value === "—" ? "var(--silver)" : "var(--platinum)",
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
  onBack,
  loading,
}) {
  const hasConflicts = !!conflictReport?.has_conflicts;
  const conflictingFields = hasConflicts ? getConflictingFields(conflictReport.conflicts) : [];

  // Local edits for conflicting fields only
  const [localEdits, setLocalEdits] = useState({});
  const [editingConflicts, setEditingConflicts] = useState(false);

  const mergedConstraints = { ...constraints, ...localEdits };

  const setField = (key, val) =>
    setLocalEdits((prev) => ({ ...prev, [key]: val }));

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
            color: "var(--platinum)",
            letterSpacing: "-0.02em",
            marginBottom: "4px",
          }}
        >
          Extracted preferences
        </h2>
        <p style={{ fontSize: "12px", color: "var(--silver)" }}>
          Review what AI understood from your conversation
        </p>
      </div>

      {/* Constraints table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: "rgba(0,0,0,0.03)",
          border: "1px solid var(--rim)",
          borderRadius: "12px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "10px 14px",
            borderBottom: "1px solid var(--rim)",
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
              color: "var(--silver)",
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
            value={formatValue(key, mergedConstraints?.[key])}
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
              <li key={k} style={{ fontSize: "11px", color: "var(--silver)" }}>
                <span style={{ color: "var(--platinum)", fontWeight: 600 }}>
                  {FIELD_LABELS[k] ?? k}
                </span>
                : {v}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Conflicts + resolution panel */}
      <AnimatePresence>
        {hasConflicts && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            style={{
              background: "rgba(225,112,85,0.07)",
              border: "1px solid rgba(225,112,85,0.3)",
              borderRadius: "12px",
              overflow: "hidden",
            }}
          >
            {/* Conflict header */}
            <div
              style={{
                padding: "10px 14px",
                borderBottom: "1px solid rgba(225,112,85,0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <AlertTriangle size={13} style={{ color: "#e17055" }} />
                <span
                  style={{
                    fontSize: "10px",
                    fontWeight: 700,
                    color: "#e17055",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                  }}
                >
                  Conflicts detected — action required
                </span>
              </div>
              {conflictingFields.length > 0 && (
                <button
                  onClick={() => {
                    setEditingConflicts((v) => !v);
                    setLocalEdits({});
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#e17055",
                    fontSize: "10px",
                    fontWeight: 600,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                    padding: "2px 6px",
                    fontFamily: "Inter, sans-serif",
                  }}
                >
                  {editingConflicts ? (
                    <><RotateCcw size={11} /> Reset</>
                  ) : (
                    <><PencilLine size={11} /> Edit fields</>
                  )}
                </button>
              )}
            </div>

            {/* Conflict list */}
            <div style={{ padding: "10px 14px" }}>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "6px", marginBottom: "12px" }}>
                {conflictReport.conflicts.map((c, i) => (
                  <li key={i} style={{ fontSize: "11px", color: "rgba(225,112,85,0.85)", lineHeight: 1.5 }}>
                    ⚠ {c}
                  </li>
                ))}
              </ul>

              {/* Inline field editors for conflicting fields */}
              <AnimatePresence>
                {editingConflicts && conflictingFields.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    style={{ overflow: "hidden" }}
                  >
                    <div
                      style={{
                        background: "rgba(0,0,0,0.2)",
                        borderRadius: "8px",
                        padding: "10px 12px",
                        marginBottom: "12px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "10px",
                      }}
                    >
                      <span style={{ fontSize: "10px", color: "var(--silver)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                        Change conflicting fields
                      </span>
                      {conflictingFields.map((key) => (
                        <div key={key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                          <span style={{ fontSize: "11px", color: "var(--silver)", flexShrink: 0 }}>
                            {FIELD_LABELS[key] ?? key}
                          </span>
                          <ConflictFieldEditor
                            fieldKey={key}
                            value={localEdits[key] ?? mergedConstraints?.[key]}
                            onChange={(val) => setField(key, val)}
                          />
                        </div>
                      ))}
                    </div>
                    {/* Save & proceed after editing */}
                    <button
                      onClick={() => onConfirm(mergedConstraints)}
                      disabled={loading}
                      className="btn-primary"
                      style={{
                        width: "100%",
                        padding: "10px 0",
                        borderRadius: "9px",
                        border: "none",
                        color: "white",
                        fontSize: "12px",
                        fontWeight: 700,
                        cursor: loading ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "7px",
                        fontFamily: "Inter, sans-serif",
                        marginBottom: "8px",
                      }}
                    >
                      {loading ? (
                        <><Loader2 size={13} style={{ animation: "spin 1s linear infinite" }} /> Generating…</>
                      ) : (
                        "Save changes & generate itinerary →"
                      )}
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Resolution buttons */}
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  onClick={onBack}
                  disabled={loading}
                  style={{
                    flex: 1,
                    padding: "10px 0",
                    borderRadius: "9px",
                    border: "1px solid rgba(255,255,255,0.12)",
                    background: "rgba(255,255,255,0.05)",
                    color: "var(--silver)",
                    fontSize: "11px",
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "5px",
                    fontFamily: "Inter, sans-serif",
                  }}
                >
                  <ArrowLeft size={12} /> Go back to chat
                </button>
                <button
                  onClick={() => onConfirm(mergedConstraints)}
                  disabled={loading}
                  style={{
                    flex: 1,
                    padding: "10px 0",
                    borderRadius: "9px",
                    border: "1px solid rgba(225,112,85,0.35)",
                    background: "rgba(225,112,85,0.12)",
                    color: "#e17055",
                    fontSize: "11px",
                    fontWeight: 700,
                    cursor: loading ? "not-allowed" : "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "5px",
                    fontFamily: "Inter, sans-serif",
                  }}
                >
                  {loading ? (
                    <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />
                  ) : (
                    <Zap size={12} />
                  )}
                  Plan anyway
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Normal CTA — only shown when no conflicts */}
      {!hasConflicts && (
        <button
          onClick={() => onConfirm(constraints)}
          disabled={loading}
          className="btn-primary"
          style={{
            width: "100%",
            padding: "13px 0",
            borderRadius: "12px",
            border: "none",
            color: "white",
            fontSize: "13px",
            fontWeight: 700,
            cursor: loading ? "not-allowed" : "pointer",
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
      )}
    </div>
  );
}
