import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Car, Bed, Zap, Utensils, Coffee, Download } from "lucide-react";
import { downloadICS } from "../../utils/icsGenerator";
import { useSelection } from "../../hooks/useSelection";

// Muted, Google-Calendar-style type accents (thin left border + soft tint on a
// light card). No saturated fills — keeps the light theme calm.
const TYPE_META = {
  travel:   { icon: Car,      accent: "#3b82a6", label: "Transit" },
  hotel:    { icon: Bed,      accent: "#6e7382", label: "Stay" },
  activity: { icon: Zap,      accent: "#b8862f", label: "Activity" },
  meal:     { icon: Utensils, accent: "#3f8f6b", label: "Meal" },
  rest:     { icon: Coffee,   accent: "#8a8f9c", label: "Rest" },
};

function timeToMinutes(t) {
  if (!t) return 0;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + (m || 0);
}

// Grid spans 05:00–23:00, one event per real start/end.
const DAY_START_H = 5;
const DAY_END_H = 23;
const HOURS = Array.from({ length: DAY_END_H - DAY_START_H + 1 }, (_, i) => DAY_START_H + i);
const ROW_HEIGHT = 46; // px per hour — taller so it scrolls like Google Calendar
const GRID_H = (HOURS.length - 1) * ROW_HEIGHT;

function topPx(timeStr) {
  const mins = Math.max(timeToMinutes(timeStr), DAY_START_H * 60) - DAY_START_H * 60;
  return (mins / 60) * ROW_HEIGHT;
}
function heightPx(start, end) {
  const s = Math.max(timeToMinutes(start), DAY_START_H * 60);
  let e = Math.min(timeToMinutes(end), DAY_END_H * 60);
  if (e <= s) e = s + 30; // guard against zero/negative
  return Math.max(((e - s) / 60) * ROW_HEIGHT, 22);
}

function eventSyncId(ev) {
  return ev.point_id || ev.id;
}

function EventBlock({ event }) {
  const { activePointId, setActivePointId } = useSelection();
  const meta = TYPE_META[event.type] ?? TYPE_META.rest;
  const Icon = meta.icon;
  const top = topPx(event.start_time);
  const h = heightPx(event.start_time, event.end_time);
  const syncId = eventSyncId(event);
  const isActive = activePointId === syncId;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      onClick={() => {
        const latLng = event.lat != null && event.lng != null ? [event.lat, event.lng] : null;
        setActivePointId(syncId, latLng);
      }}
      title={`${event.title} · ${event.start_time}–${event.end_time}`}
      style={{
        position: "absolute",
        top: `${top}px`,
        height: `${h}px`,
        left: "3px",
        right: "3px",
        background: isActive ? "#ffffff" : "rgba(255,255,255,0.85)",
        border: `1px solid ${isActive ? meta.accent : "var(--rim)"}`,
        borderLeft: `3px solid ${meta.accent}`,
        borderRadius: "7px",
        cursor: "pointer",
        overflow: "hidden",
        zIndex: isActive ? 15 : 5,
        boxShadow: isActive
          ? `0 4px 14px rgba(20,22,28,0.16)`
          : "0 1px 3px rgba(20,22,28,0.08)",
        transition: "box-shadow 0.2s, background 0.2s, border-color 0.2s",
        padding: "3px 6px",
        display: "flex",
        flexDirection: "column",
        gap: "1px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
        <Icon size={9} style={{ color: meta.accent, flexShrink: 0 }} />
        <span
          style={{
            fontSize: "9.5px",
            fontWeight: 700,
            color: "var(--platinum)",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {event.title}
        </span>
      </div>
      {h > 30 && (
        <span style={{ fontSize: "8px", color: "var(--silver)", whiteSpace: "nowrap" }}>
          {event.start_time} – {event.end_time}
        </span>
      )}
    </motion.div>
  );
}

export function CalendarView({ timeline, tripName = "My Trip" }) {
  const scrollRef = useRef(null);

  // Auto-scroll so the first event is in view (~07:00).
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = Math.max(0, (7 - DAY_START_H) * ROW_HEIGHT - 20);
    }
  }, [timeline]);

  if (!timeline?.length) return null;

  const byDay = timeline.reduce((acc, ev) => {
    const d = ev.day ?? 1;
    (acc[d] = acc[d] ?? []).push(ev);
    return acc;
  }, {});
  const days = Object.keys(byDay).map(Number).sort((a, b) => a - b);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 14px",
          borderBottom: "1px solid var(--rim)",
          flexShrink: 0,
        }}
      >
        <div>
          <p style={{ fontSize: "10px", fontWeight: 700, color: "var(--silver)", textTransform: "uppercase", letterSpacing: "0.12em" }}>
            Calendar
          </p>
          <p style={{ fontSize: "11px", color: "var(--chrome)", marginTop: "1px", fontWeight: 500 }}>
            {days.length} day{days.length !== 1 ? "s" : ""} · {timeline.length} events
          </p>
        </div>
        <button
          onClick={() => downloadICS(timeline, tripName)}
          className="btn-ghost"
          style={{
            display: "flex", alignItems: "center", gap: "6px",
            padding: "6px 12px", borderRadius: "999px",
            fontSize: "11px", fontWeight: 600, cursor: "pointer",
          }}
          title="Download as .ics calendar file"
        >
          <Download size={12} />
          Export ICS
        </button>
      </div>

      {/* Sticky day-header row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `38px repeat(${days.length}, 1fr)`,
          borderBottom: "1px solid var(--rim)",
          flexShrink: 0,
          background: "rgba(255,255,255,0.4)",
        }}
      >
        <div />
        {days.map((day) => (
          <div
            key={day}
            style={{
              textAlign: "center",
              padding: "8px 4px",
              borderLeft: "1px solid var(--rim)",
            }}
          >
            <span style={{ fontSize: "10.5px", fontWeight: 700, color: "var(--chrome)", letterSpacing: "0.04em" }}>
              Day {day}
            </span>
          </div>
        ))}
      </div>

      {/* Scrollable time body */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", overflowX: "hidden" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: `38px repeat(${days.length}, 1fr)`,
            height: `${GRID_H}px`,
            position: "relative",
          }}
        >
          {/* Time labels */}
          <div style={{ position: "relative" }}>
            {HOURS.map((h, i) => (
              <div
                key={h}
                style={{
                  position: "absolute",
                  top: `${i * ROW_HEIGHT - 5}px`,
                  right: "5px",
                  fontSize: "8.5px",
                  color: "var(--silver)",
                  fontWeight: 600,
                  lineHeight: 1,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {String(h).padStart(2, "0")}:00
              </div>
            ))}
          </div>

          {/* Day columns */}
          {days.map((day) => (
            <div
              key={day}
              style={{
                position: "relative",
                borderLeft: "1px solid var(--rim)",
                height: `${GRID_H}px`,
              }}
            >
              {/* Hour gridlines (visible on light bg) */}
              {HOURS.map((h, i) => (
                <div
                  key={h}
                  style={{
                    position: "absolute",
                    top: `${i * ROW_HEIGHT}px`,
                    left: 0,
                    right: 0,
                    borderTop: `1px solid rgba(0,0,0,${i % 6 === 0 ? "0.10" : "0.045"})`,
                  }}
                />
              ))}
              {(byDay[day] || []).map((ev, i) => (
                <EventBlock key={ev.id || i} event={ev} />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
