import { motion } from "framer-motion";
import { CheckCircle, AlertTriangle, Edit3, Loader2 } from "lucide-react";

const FIELD_LABELS = {
  origin: "Origin",
  destination: "Destination",
  destination_type: "Destination type",
  budget_per_person: "Budget/person",
  group_size: "Group size",
  hotel_tier: "Hotel tier",
  transport_preference: "Transport",
  avoid_night_driving: "Avoid night driving",
  must_include: "Must include",
  return_deadline: "Return by",
  trip_duration: "Duration",
};

function formatValue(key, val) {
  if (val === null || val === undefined) return <span className="text-text-muted">—</span>;
  if (key === "budget_per_person") return `₹${val.toLocaleString()}`;
  if (key === "avoid_night_driving") return val ? "Yes" : "No";
  if (Array.isArray(val)) return val.join(", ") || "—";
  return String(val);
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
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="text-center space-y-1">
        <h2 className="text-xl font-bold text-text-primary">Extracted preferences</h2>
        <p className="text-text-muted text-sm">Review what the AI understood from your conversation</p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-surface border border-border rounded-xl overflow-hidden"
      >
        <div className="px-4 py-3 border-b border-border flex items-center gap-2">
          <CheckCircle size={15} className="text-success" />
          <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
            Constraints
          </span>
        </div>
        <div className="divide-y divide-border">
          {Object.entries(FIELD_LABELS).map(([key, label]) => (
            <div key={key} className="flex items-center justify-between px-4 py-2.5">
              <span className="text-xs text-text-muted w-40 flex-shrink-0">{label}</span>
              <span className="text-sm text-text-primary text-right">
                {formatValue(key, constraints?.[key])}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {Object.keys(assumptions).length > 0 && (
        <div className="bg-warning/10 border border-warning/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Edit3 size={14} className="text-warning" />
            <span className="text-xs font-medium text-warning uppercase tracking-wide">
              Assumptions made
            </span>
          </div>
          <ul className="space-y-1">
            {Object.entries(assumptions).map(([k, v]) => (
              <li key={k} className="text-xs text-text-muted">
                <span className="text-text-primary">{FIELD_LABELS[k] ?? k}</span>: {v}
              </li>
            ))}
          </ul>
        </div>
      )}

      {conflictReport?.has_conflicts && (
        <div className="bg-danger/10 border border-danger/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-danger" />
            <span className="text-xs font-medium text-danger uppercase tracking-wide">
              Conflicts detected
            </span>
          </div>
          <ul className="space-y-1">
            {conflictReport.conflicts.map((c, i) => (
              <li key={i} className="text-xs text-text-muted">• {c}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={() => onConfirm(constraints)}
        disabled={loading || conflictReport?.has_conflicts}
        className="w-full py-3 rounded-xl bg-primary hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Generating itinerary…
          </>
        ) : (
          "Generate itinerary →"
        )}
      </button>
    </div>
  );
}
