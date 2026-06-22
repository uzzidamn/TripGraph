import { useRef, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Car, Bed, Zap, Utensils, Coffee, Download, Calendar as CalIcon } from "lucide-react";
import { downloadICS } from "../../utils/icsGenerator";
import { useSelection } from "../../hooks/useSelection";

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

// One day fills the column; each hour gets HOUR_ROW px so text is readable.
const DAY_START_H = 6;
const DAY_END_H = 23;
const HOURS = Array.from({ length: DAY_END_H - DAY_START_H + 1 }, (_, i) => DAY_START_H + i);
const HOUR_ROW = 70;
const DAY_HEIGHT = (HOURS.length - 1) * HOUR_ROW;

function topPx(timeStr) {
  const mins = Math.max(timeToMinutes(timeStr), DAY_START_H * 60) - DAY_START_H * 60;
  return (mins / 60) * HOUR_ROW;
}
function heightPx(start, end) {
  const s = Math.max(timeToMinutes(start), DAY_START_H * 60);
  let e = Math.min(timeToMinutes(end), DAY_END_H * 60);
  if (e <= s) e = s + 30;
  return Math.max(((e - s) / 60) * HOUR_ROW, 40);
}

function eventSyncId(ev) {
  return ev.point_id || ev.id;
}

function EventBlock({ event, onSelectDay }) {
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
        if (onSelectDay && event.day != null) onSelectDay(event.day);
      }}
      title={`${event.title} · ${event.start_time}–${event.end_time}`}
      style={{
        position: "absolute",
        top: `${top}px`,
        height: `${h}px`,
        left: 6,
        right: 6,
        background: isActive ? "#ffffff" : "rgba(255,255,255,0.92)",
        border: `1px solid ${isActive ? meta.accent : "var(--rim)"}`,
        borderLeft: `3px solid ${meta.accent}`,
        borderRadius: 8,
        cursor: "pointer",
        overflow: "hidden",
        zIndex: isActive ? 15 : 5,
        boxShadow: isActive
          ? `0 4px 14px rgba(20,22,28,0.18)`
          : "0 1px 3px rgba(20,22,28,0.08)",
        transition: "box-shadow 0.18s, background 0.18s, border-color 0.18s",
        padding: "6px 9px",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 5, flexShrink: 0 }}>
        <Icon size={11} style={{ color: meta.accent, flexShrink: 0 }} />
        <span style={{
          fontSize: 12, fontWeight: 700, color: "var(--platinum)",
          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1,
        }}>
          {event.title}
        </span>
        {event.cost > 0 && (
          <span style={{ fontSize: 10, fontWeight: 700, color: "var(--chrome)", flexShrink: 0 }}>
            ₹{Number(event.cost).toLocaleString()}
          </span>
        )}
      </div>
      {h > 40 && (
        <span style={{ fontSize: 9.5, color: "var(--silver)", whiteSpace: "nowrap" }}>
          {event.start_time} – {event.end_time}
        </span>
      )}
      {h > 70 && event.why && (
        <span style={{
          fontSize: 10, color: "var(--chrome)", lineHeight: 1.35,
          overflow: "hidden", textOverflow: "ellipsis",
          display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
        }}>
          {event.why}
        </span>
      )}
    </motion.div>
  );
}

/** Auto-filled grey "Free time" block in calendar gaps >60 min between events. */
function FreeTimeBlock({ start, end }) {
  const top = topPx(start);
  const h = heightPx(start, end);
  if (h < 60) return null;
  return (
    <div style={{
      position: "absolute",
      top: `${top}px`, height: `${h}px`,
      left: 6, right: 6,
      background: "repeating-linear-gradient(45deg, rgba(0,0,0,0.025), rgba(0,0,0,0.025) 6px, rgba(0,0,0,0.04) 6px, rgba(0,0,0,0.04) 12px)",
      border: "1px dashed var(--rim)",
      borderRadius: 6,
      display: "flex", alignItems: "center", justifyContent: "center",
      pointerEvents: "none",
    }}>
      <span style={{
        fontSize: 10, color: "var(--silver)", fontWeight: 600,
        letterSpacing: "0.06em", textTransform: "uppercase",
      }}>
        Free time
      </span>
    </div>
  );
}

export function CalendarView({ timeline, tripName = "My Trip", onSelectDay = null }) {
  const scrollRef = useRef(null);
  const { activePointId } = useSelection();

  const byDay = useMemo(() => {
    const map = new Map();
    for (const ev of timeline || []) {
      const d = ev.day ?? 1;
      if (!map.has(d)) map.set(d, []);
      map.get(d).push(ev);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }, [timeline]);

  // Compute auto-filled gaps per day
  const gapsByDay = useMemo(() => {
    const map = new Map();
    for (const [day, events] of byDay) {
      const sorted = [...events].sort((a, b) =>
        timeToMinutes(a.start_time) - timeToMinutes(b.start_time)
      );
      const gaps = [];
      for (let i = 0; i < sorted.length - 1; i++) {
        const endA = timeToMinutes(sorted[i].end_time);
        const startB = timeToMinutes(sorted[i + 1].start_time);
        if (startB - endA >= 60) {
          gaps.push({
            start: `${String(Math.floor(endA / 60)).padStart(2, "0")}:${String(endA % 60).padStart(2, "0")}`,
            end: `${String(Math.floor(startB / 60)).padStart(2, "0")}:${String(startB % 60).padStart(2, "0")}`,
          });
        }
      }
      map.set(day, gaps);
    }
    return map;
  }, [byDay]);

  // Scroll active event into view
  useEffect(() => {
    if (!activePointId || !scrollRef.current) return;
    const node = scrollRef.current.querySelector(`[data-sync-id="${activePointId}"]`);
    if (node) {
      node.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activePointId]);

  if (!timeline?.length) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 14px", borderBottom: "1px solid var(--rim)", flexShrink: 0,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <CalIcon size={13} style={{ color: "var(--chrome)" }} />
          <div>
            <p style={{
              fontSize: 9.5, fontWeight: 700, color: "var(--silver)",
              textTransform: "uppercase", letterSpacing: "0.12em",
            }}>
              Calendar
            </p>
            <p style={{ fontSize: 11, color: "var(--chrome)", marginTop: 1, fontWeight: 500 }}>
              {byDay.length} day{byDay.length !== 1 ? "s" : ""} · {timeline.length} events
            </p>
          </div>
        </div>
        <button
          onClick={() => downloadICS(timeline, tripName)}
          className="btn-ghost"
          style={{
            display: "flex", alignItems: "center", gap: 5,
            padding: "5px 10px", borderRadius: 999,
            fontSize: 10.5, fontWeight: 600, cursor: "pointer",
          }}
          title="Download as .ics calendar file"
        >
          <Download size={11} />
          Export
        </button>
      </div>

      {/* Vertically scrollable: days stacked, one column each */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", overflowX: "hidden" }}>
        {byDay.map(([day, events]) => (
          <div key={day} style={{ borderBottom: "1px solid var(--rim)" }}>
            {/* Sticky day header */}
            <div style={{
              position: "sticky", top: 0, zIndex: 20,
              background: "rgba(255,255,255,0.92)",
              backdropFilter: "blur(10px)",
              padding: "8px 14px",
              borderBottom: "1px solid var(--rim)",
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span style={{
                fontSize: 11, fontWeight: 800, color: "var(--platinum)",
                letterSpacing: "0.04em",
              }}>
                Day {day}
              </span>
              <span style={{ fontSize: 9.5, color: "var(--silver)" }}>
                {events.length} stop{events.length !== 1 ? "s" : ""}
              </span>
            </div>

            {/* Day timeline body */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "42px 1fr",
              height: DAY_HEIGHT,
              position: "relative",
              background: "rgba(255,255,255,0.4)",
            }}>
              {/* Time labels column */}
              <div style={{ position: "relative", borderRight: "1px solid var(--rim)" }}>
                {HOURS.map((h, i) => (
                  <div key={h} style={{
                    position: "absolute",
                    top: `${i * HOUR_ROW - 5}px`,
                    right: 6,
                    fontSize: 9.5, color: "var(--silver)",
                    fontWeight: 600, lineHeight: 1,
                    fontVariantNumeric: "tabular-nums",
                  }}>
                    {String(h).padStart(2, "0")}:00
                  </div>
                ))}
              </div>

              {/* Events column */}
              <div style={{ position: "relative", height: DAY_HEIGHT }}>
                {/* Hour gridlines */}
                {HOURS.map((h, i) => (
                  <div key={h} style={{
                    position: "absolute",
                    top: `${i * HOUR_ROW}px`,
                    left: 0, right: 0,
                    borderTop: `1px solid rgba(0,0,0,${i % 6 === 0 ? 0.10 : 0.045})`,
                  }} />
                ))}
                {/* Auto-fill grey "Free time" gaps */}
                {(gapsByDay.get(day) || []).map((g, i) => (
                  <FreeTimeBlock key={`gap-${day}-${i}`} start={g.start} end={g.end} />
                ))}
                {/* Event blocks */}
                {events.map((ev, i) => (
                  <div key={ev.id || i} data-sync-id={eventSyncId(ev)} style={{
                    position: "absolute", top: 0, left: 0, right: 0, height: "100%",
                  }}>
                    <EventBlock event={ev} onSelectDay={onSelectDay} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
