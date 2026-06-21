import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MapPin,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  Bed,
  Car,
  Zap,
  AlertTriangle,
  Lightbulb,
  Star,
  IndianRupee,
  Info,
} from "lucide-react";

function ScoreBar({ label, value, max = 30, color = "#cfd6e0" }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div style={{ marginBottom: "8px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
        <span style={{ fontSize: "11px", color: "#64748b" }}>{label}</span>
        <span style={{ fontSize: "11px", color: "#e2e8f0", fontWeight: 600 }}>
          {value}/{max}
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
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          style={{
            height: "100%",
            background: color,
            borderRadius: "999px",
          }}
        />
      </div>
    </div>
  );
}

function Collapsible({ title, icon: Icon, iconColor, children, defaultOpen = false, badge }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div
      style={{
        border: "1px solid rgba(255,255,255,0.07)",
        borderRadius: "12px",
        overflow: "hidden",
        marginBottom: "8px",
      }}
    >
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          padding: "10px 14px",
          background: "rgba(14, 18, 38, 0.6)",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
          fontFamily: "Inter, sans-serif",
        }}
      >
        {Icon && <Icon size={13} style={{ color: iconColor ?? "#cfd6e0", flexShrink: 0 }} />}
        <span
          style={{
            fontSize: "11px",
            fontWeight: 700,
            color: "#e2e8f0",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            flex: 1,
          }}
        >
          {title}
        </span>
        {badge != null && (
          <span
            style={{
              fontSize: "10px",
              fontWeight: 700,
              color: "#cfd6e0",
              background: "rgba(207,214,224,0.15)",
              padding: "1px 7px",
              borderRadius: "999px",
            }}
          >
            {badge}
          </span>
        )}
        {open ? (
          <ChevronUp size={13} style={{ color: "#64748b", flexShrink: 0 }} />
        ) : (
          <ChevronDown size={13} style={{ color: "#64748b", flexShrink: 0 }} />
        )}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            style={{ overflow: "hidden" }}
          >
            <div style={{ padding: "12px 14px", background: "rgba(8, 12, 26, 0.5)" }}>
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function AdvisoryItem({ item, idx }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: idx * 0.05 }}
      style={{
        background: "rgba(253,203,110,0.08)",
        border: "1px solid rgba(253,203,110,0.2)",
        borderLeft: "3px solid #fdcb6e",
        borderRadius: "8px",
        padding: "8px 12px",
        marginBottom: "6px",
      }}
    >
      <p style={{ fontSize: "11px", fontWeight: 700, color: "#fdcb6e", marginBottom: "2px" }}>
        {item.title}
      </p>
      <p style={{ fontSize: "10px", color: "#94a3b8", lineHeight: 1.5 }}>
        {item.description}
      </p>
    </motion.div>
  );
}

export function ItineraryOptions({ itinerary, alternatives, scoreBreakdown }) {
  if (!itinerary) return null;

  const {
    route,
    hotel,
    transport,
    activities,
    total_cost_per_person,
    destination,
    hotel_selection_reason,
    advisory_items,
    local_tips,
  } = itinerary;

  return (
    <div style={{ padding: "0" }}>
      {/* Route hero card */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: "linear-gradient(135deg, rgba(207,214,224,0.15) 0%, rgba(0,206,201,0.08) 100%)",
          border: "1px solid rgba(207,214,224,0.25)",
          borderRadius: "14px",
          padding: "16px",
          marginBottom: "10px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
              <MapPin size={14} style={{ color: "#cfd6e0" }} />
              <span style={{ fontWeight: 700, fontSize: "14px", color: "#e2e8f0" }}>
                {route?.origin} → {destination ?? route?.destination}
              </span>
            </div>
            <p style={{ fontSize: "11px", color: "#64748b" }}>
              {route?.distance_km} km · {route?.destination_type}
            </p>
          </div>
          <div style={{ textAlign: "right", flexShrink: 0 }}>
            <p style={{ fontSize: "18px", fontWeight: 800, color: "#cfd6e0", lineHeight: 1 }}>
              ₹{total_cost_per_person?.toLocaleString()}
            </p>
            <p style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>per person</p>
          </div>
        </div>

        {/* Hotel & Transport chips */}
        <div style={{ display: "flex", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
          {hotel && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                background: "rgba(0,184,148,0.12)",
                border: "1px solid rgba(0,184,148,0.25)",
                borderRadius: "8px",
                padding: "4px 10px",
                fontSize: "10px",
                color: "#00b894",
                fontWeight: 600,
              }}
            >
              <Bed size={10} />
              {hotel.name}
            </div>
          )}
          {transport && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                background: "rgba(0,206,201,0.12)",
                border: "1px solid rgba(0,206,201,0.25)",
                borderRadius: "8px",
                padding: "4px 10px",
                fontSize: "10px",
                color: "#00cec9",
                fontWeight: 600,
              }}
            >
              <Car size={10} />
              {transport.mode?.replace(/_/g, " ")} · {transport.tier}
            </div>
          )}
        </div>
      </motion.div>

      {/* Score breakdown */}
      {scoreBreakdown && (
        <Collapsible
          title={`Score: ${scoreBreakdown.final_score}/100`}
          icon={TrendingUp}
          iconColor="#00cec9"
          defaultOpen
        >
          <ScoreBar label="Preference match" value={scoreBreakdown.preference_match} max={30} color="#cfd6e0" />
          <ScoreBar label="Comfort" value={scoreBreakdown.comfort} max={20} color="#00b894" />
          <ScoreBar label="Fatigue management" value={scoreBreakdown.fatigue} max={15} color="#00cec9" />
          {scoreBreakdown.scenic != null && (
            <ScoreBar label="Scenic value" value={scoreBreakdown.scenic} max={15} color="#fdcb6e" />
          )}
        </Collapsible>
      )}

      {/* Activities */}
      {activities?.length > 0 && (
        <Collapsible
          title="Activities"
          icon={Zap}
          iconColor="#fdcb6e"
          badge={activities.length}
          defaultOpen
        >
          {activities.map((a, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "6px 0",
                borderBottom: i < activities.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div
                  style={{
                    width: "6px",
                    height: "6px",
                    borderRadius: "50%",
                    background: "#fdcb6e",
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: "12px", color: "#e2e8f0" }}>{a.name}</span>
              </div>
              <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 600, flexShrink: 0, marginLeft: "8px" }}>
                {a.cost_per_person === 0 ? "Free" : `₹${a.cost_per_person?.toLocaleString()}`}
              </span>
            </div>
          ))}
        </Collapsible>
      )}

      {/* Hotel note */}
      {hotel_selection_reason && (
        <Collapsible title="Why this hotel?" icon={Info} iconColor="#cfd6e0">
          <p
            style={{
              fontSize: "12px",
              color: "#94a3b8",
              lineHeight: 1.6,
              fontStyle: "italic",
            }}
          >
            "{hotel_selection_reason}"
          </p>
        </Collapsible>
      )}

      {/* Logistics & Advisories */}
      {advisory_items?.length > 0 && (
        <Collapsible
          title="Logistics & Advisories"
          icon={AlertTriangle}
          iconColor="#fdcb6e"
          badge={advisory_items.length}
          defaultOpen
        >
          {advisory_items.map((item, i) => (
            <AdvisoryItem key={i} item={item} idx={i} />
          ))}
        </Collapsible>
      )}

      {/* Local tips */}
      {local_tips?.length > 0 && (
        <Collapsible
          title="Local Tips"
          icon={Lightbulb}
          iconColor="#00cec9"
          badge={local_tips.length}
        >
          {local_tips.map((tip, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                gap: "8px",
                alignItems: "flex-start",
                marginBottom: "6px",
              }}
            >
              <span style={{ color: "#00cec9", fontSize: "12px", flexShrink: 0 }}>→</span>
              <span style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.5 }}>{tip}</span>
            </div>
          ))}
        </Collapsible>
      )}

      {/* Alternatives */}
      {alternatives?.length > 0 && (
        <Collapsible
          title="Alternative Plans"
          icon={Star}
          iconColor="#e17055"
          badge={alternatives.length}
        >
          {alternatives.map((alt, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 * i }}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.07)",
                borderRadius: "10px",
                padding: "10px 12px",
                marginBottom: "6px",
              }}
            >
              <div>
                <p style={{ fontSize: "13px", fontWeight: 600, color: "#e2e8f0" }}>
                  {alt.destination ?? alt.route?.destination}
                </p>
                <p style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                  {alt.route?.distance_km} km · {alt.hotel?.name}
                </p>
              </div>
              <p style={{ fontSize: "14px", fontWeight: 800, color: "#00cec9", flexShrink: 0, marginLeft: "8px" }}>
                ₹{alt.total_cost_per_person?.toLocaleString()}
              </p>
            </motion.div>
          ))}
        </Collapsible>
      )}
    </div>
  );
}
