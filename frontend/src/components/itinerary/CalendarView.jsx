import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Car,
  Bed,
  Zap,
  Utensils,
  Coffee,
  Download,
  Cloud,
  Wind,
  AlertCircle,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { downloadICS } from "../../utils/icsGenerator";

const TYPE_META = {
  travel:   { icon: Car,      color: "#00cec9",  bg: "rgba(0,206,201,0.15)",  border: "rgba(0,206,201,0.35)",  label: "Transit" },
  hotel:    { icon: Bed,      color: "#7c6df7",  bg: "rgba(124,109,247,0.15)",border: "rgba(124,109,247,0.35)",label: "Stay" },
  activity: { icon: Zap,      color: "#fdcb6e",  bg: "rgba(253,203,110,0.15)",border: "rgba(253,203,110,0.35)",label: "Activity" },
  meal:     { icon: Utensils, color: "#00b894",  bg: "rgba(0,184,148,0.15)",  border: "rgba(0,184,148,0.35)",  label: "Meal" },
  rest:     { icon: Coffee,   color: "#94a3b8",  bg: "rgba(148,163,184,0.1)", border: "rgba(148,163,184,0.2)", label: "Rest" },
};

const TRAFFIC_CONFIG = {
  low:      { color: "#00b894", label: "Light traffic" },
  moderate: { color: "#fdcb6e", label: "Moderate traffic" },
  high:     { color: "#e17055", label: "Heavy traffic" },
};

function timeToMinutes(t) {
  if (!t) return 0;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + (m || 0);
}

function formatDuration(start, end) {
  let diff = timeToMinutes(end) - timeToMinutes(start);
  if (diff < 0) diff += 1440;
  const h = Math.floor(diff / 60);
  const m = diff % 60;
  if (h > 0 && m > 0) return `${h}h ${m}m`;
  if (h > 0) return `${h}h`;
  return `${m}m`;
}

// Hours to show in the grid (06:00–22:00)
const DAY_START_H = 6;
const DAY_END_H = 22;
const HOURS = Array.from({ length: DAY_END_H - DAY_START_H + 1 }, (_, i) => DAY_START_H + i);
const TOTAL_MINUTES = (DAY_END_H - DAY_START_H) * 60;
const ROW_HEIGHT = 52; // px per hour

function pct(timeStr) {
  const mins = Math.max(timeToMinutes(timeStr), DAY_START_H * 60) - DAY_START_H * 60;
  return (mins / TOTAL_MINUTES) * 100;
}

function heightPct(start, end) {
  const s = Math.max(timeToMinutes(start), DAY_START_H * 60) - DAY_START_H * 60;
  const e = Math.min(timeToMinutes(end), DAY_END_H * 60) - DAY_START_H * 60;
  return Math.max(((e - s) / TOTAL_MINUTES) * 100, 2);
}

/** Single event block inside a day column */
function EventBlock({ event, onClick, isActive }) {
  const meta = TYPE_META[event.type] ?? TYPE_META.rest;
  const Icon = meta.icon;
  const topPct = pct(event.start_time);
  const hPct = heightPct(event.start_time, event.end_time);
  const minH = (hPct / 100) * (HOURS.length * ROW_HEIGHT);

  return (
    <motion.div
      initial={{ opacity: 0, x: -4 }}
      animate={{ opacity: 1, x: 0 }}
      whileHover={{ scale: 1.02, zIndex: 20 }}
      onClick={() => onClick(event)}
      style={{
        position: "absolute",
        top: `${topPct}%`,
        height: `${hPct}%`,
        left: "3px",
        right: "3px",
        minHeight: "20px",
        background: meta.bg,
        border: `1px solid ${meta.border}`,
        borderLeft: `3px solid ${meta.color}`,
        borderRadius: "8px",
        cursor: "pointer",
        overflow: "hidden",
        zIndex: isActive ? 15 : 5,
        boxShadow: isActive
          ? `0 0 0 2px ${meta.color}, 0 4px 16px rgba(0,0,0,0.3)`
          : "0 2px 8px rgba(0,0,0,0.2)",
        transition: "box-shadow 0.2s",
      }}
    >
      <div
        style={{
          padding: "3px 6px",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
          gap: "1px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "3px" }}>
          <Icon size={9} style={{ color: meta.color, flexShrink: 0 }} />
          <span
            style={{
              fontSize: "9px",
              fontWeight: 700,
              color: meta.color,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {event.title}
          </span>
        </div>
        {minH > 30 && (
          <span
            style={{
              fontSize: "8px",
              color: "rgba(226,232,240,0.55)",
              whiteSpace: "nowrap",
            }}
          >
            {event.start_time} – {event.end_time}
          </span>
        )}
      </div>
    </motion.div>
  );
}

/** Active event detail panel */
function EventDetail({ event, onClose }) {
  if (!event) return null;
  const meta = TYPE_META[event.type] ?? TYPE_META.rest;
  const Icon = meta.icon;
  const trafficCfg = event.traffic ? TRAFFIC_CONFIG[event.traffic.level] : null;

  return (
    <motion.div
      key={event.title + event.start_time}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      style={{
        background: "rgba(14, 18, 38, 0.95)",
        border: `1px solid ${meta.border}`,
        borderRadius: "14px",
        padding: "12px 14px",
        marginBottom: "10px",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "10px",
              background: meta.bg,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Icon size={15} style={{ color: meta.color }} />
          </div>
          <div>
            <p style={{ fontWeight: 700, fontSize: "13px", color: "#e2e8f0", lineHeight: 1.2 }}>
              {event.title}
            </p>
            <p style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
              {event.start_time} – {event.end_time} · {formatDuration(event.start_time, event.end_time)}
            </p>
          </div>
        </div>
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <p style={{ fontSize: "10px", color: "#64748b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Cost
          </p>
          <p style={{ fontWeight: 800, fontSize: "14px", color: meta.color, marginTop: "1px" }}>
            {event.cost === 0 ? "Free" : event.cost != null ? `₹${event.cost.toLocaleString()}` : "Incl."}
          </p>
        </div>
      </div>

      {/* Weather & Traffic (only for travel events) */}
      {(event.weather || event.traffic) && (
        <div
          style={{
            marginTop: "10px",
            display: "flex",
            gap: "8px",
            flexWrap: "wrap",
          }}
        >
          {event.weather && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                background: "rgba(0,206,201,0.1)",
                border: "1px solid rgba(0,206,201,0.25)",
                borderRadius: "8px",
                padding: "4px 10px",
                fontSize: "10px",
                color: "#00cec9",
                fontWeight: 600,
              }}
            >
              <Cloud size={11} />
              <span>
                {event.weather.icon} {event.weather.temp}°C · {event.weather.condition}
              </span>
            </div>
          )}
          {event.traffic && trafficCfg && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                background: `${trafficCfg.color}18`,
                border: `1px solid ${trafficCfg.color}40`,
                borderRadius: "8px",
                padding: "4px 10px",
                fontSize: "10px",
                color: trafficCfg.color,
                fontWeight: 600,
              }}
            >
              <Wind size={11} />
              <span>{trafficCfg.label}</span>
            </div>
          )}
        </div>
      )}

      {event.traffic?.note && (
        <p
          style={{
            marginTop: "6px",
            fontSize: "10px",
            color: "#64748b",
            lineHeight: 1.5,
            fontStyle: "italic",
          }}
        >
          {event.traffic.note}
        </p>
      )}
    </motion.div>
  );
}

export function CalendarView({ timeline, tripName = "My Trip" }) {
  const [activeEvent, setActiveEvent] = useState(null);

  if (!timeline?.length) return null;

  const byDay = timeline.reduce((acc, ev) => {
    const d = ev.day ?? 1;
    (acc[d] = acc[d] ?? []).push(ev);
    return acc;
  }, {});
  const days = Object.keys(byDay).map(Number).sort((a, b) => a - b);

  const handleDownload = () => {
    downloadICS(timeline, tripName);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid rgba(255,255,255,0.07)",
          flexShrink: 0,
        }}
      >
        <div>
          <p style={{ fontSize: "11px", fontWeight: 700, color: "#7c6df7", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Calendar
          </p>
          <p style={{ fontSize: "10px", color: "#64748b", marginTop: "1px" }}>
            {days.length} day{days.length !== 1 ? "s" : ""} · {timeline.length} events
          </p>
        </div>
        <button
          onClick={handleDownload}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 12px",
            background: "rgba(124,109,247,0.15)",
            border: "1px solid rgba(124,109,247,0.3)",
            borderRadius: "8px",
            color: "#7c6df7",
            fontSize: "11px",
            fontWeight: 600,
            cursor: "pointer",
            transition: "background 0.2s",
            fontFamily: "Inter, sans-serif",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(124,109,247,0.25)")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(124,109,247,0.15)")}
          title="Download as .ics calendar file"
        >
          <Download size={12} />
          Export ICS
        </button>
      </div>

      {/* Active event detail */}
      <div style={{ padding: "10px 12px 0", flexShrink: 0 }}>
        <AnimatePresence mode="wait">
          {activeEvent ? (
            <EventDetail
              key={activeEvent.title + activeEvent.start_time}
              event={activeEvent}
              onClose={() => setActiveEvent(null)}
            />
          ) : (
            <motion.div
              key="hint"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                fontSize: "10px",
                color: "#64748b",
                textAlign: "center",
                padding: "6px 0 8px",
              }}
            >
              Click an event block to see details, weather & traffic
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Calendar grid — horizontal (Google Calendar week view style) */}
      <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        {/* Day header row */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "40px repeat(" + days.length + ", 1fr)",
            borderBottom: "1px solid rgba(255,255,255,0.07)",
            flexShrink: 0,
          }}
        >
          <div /> {/* spacer for time column */}
          {days.map((day) => (
            <div
              key={day}
              style={{
                textAlign: "center",
                padding: "6px 4px",
                borderLeft: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "#7c6df7",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                Day {day}
              </span>
            </div>
          ))}
        </div>

        {/* Scrollable time body */}
        <div style={{ flex: 1, overflowY: "auto", overflowX: "hidden" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "40px repeat(" + days.length + ", 1fr)",
              height: `${HOURS.length * ROW_HEIGHT}px`,
            }}
          >
            {/* Time labels (left column) */}
            <div style={{ position: "relative" }}>
              {HOURS.map((h) => (
                <div
                  key={h}
                  style={{
                    position: "absolute",
                    top: `${((h - DAY_START_H) / HOURS.length) * 100}%`,
                    right: "6px",
                    fontSize: "8px",
                    color: "rgba(255,255,255,0.25)",
                    fontWeight: 600,
                    lineHeight: 1,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {String(h).padStart(2, "0")}
                </div>
              ))}
            </div>

            {/* Day columns */}
            {days.map((day) => (
              <div
                key={day}
                style={{
                  position: "relative",
                  borderLeft: "1px solid rgba(255,255,255,0.06)",
                  height: `${HOURS.length * ROW_HEIGHT}px`,
                }}
              >
                {/* Hour grid lines */}
                {HOURS.map((h) => (
                  <div
                    key={h}
                    style={{
                      position: "absolute",
                      top: `${((h - DAY_START_H) / HOURS.length) * 100}%`,
                      left: 0,
                      right: 0,
                      borderTop: `1px solid rgba(255,255,255,${h % 6 === 0 ? "0.08" : "0.03"})`,
                    }}
                  />
                ))}

                {/* Events in this day */}
                {(byDay[day] || []).map((ev, i) => (
                  <EventBlock
                    key={i}
                    event={ev}
                    onClick={setActiveEvent}
                    isActive={
                      activeEvent &&
                      activeEvent.title === ev.title &&
                      activeEvent.start_time === ev.start_time
                    }
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
