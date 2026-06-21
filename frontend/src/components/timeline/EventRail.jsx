/**
 * EventRail — vertical scrollable rail of timeline events (1 row per event).
 *
 * Bi-directional sync with the map via SelectionContext:
 *  - Scrolling / clicking a row sets activePointId → map flies to that pin
 *  - Clicking a pin scrolls the matching row into view
 *
 * Each row shows: day badge + icon + title + time + weather chip + fatigue gauge.
 * A "Show whole itinerary" button at the top resets the map to fit all points.
 *
 * Designed to be wider than a chip (240px) and a tall slim column on the left.
 */
import { useEffect, useRef } from "react";
import {
  Sun, CloudRain, CloudSnow, Cloud, Zap, Wind,
  Car, Footprints, UtensilsCrossed, Hotel, MapPin, Camera, Maximize2,
} from "lucide-react";
import { GlassPanel, Pill, Gauge, GhostButton } from "../ui/Glass";
import { useSelection } from "../../hooks/useSelection";

const WEATHER_ICON = {
  clear: Sun, sun: Sun,
  rain: CloudRain, drizzle: CloudRain,
  snow: CloudSnow,
  clouds: Cloud,
  thunderstorm: Zap,
  mist: Wind, haze: Wind, fog: Wind,
};

const EVENT_ICON = {
  travel: Car, drive: Car, transport: Car,
  activity: Camera, experience: Camera, sightseeing: Camera,
  meal: UtensilsCrossed, food: UtensilsCrossed, restaurant: UtensilsCrossed,
  hotel: Hotel, checkin: Hotel, checkout: Hotel, stay: Hotel,
  rest: Hotel,
  walk: Footprints,
};

function pickIcon(map, key, fallback) {
  const k = String(key || "").toLowerCase();
  return map[k] || fallback;
}

function EventRow({ ev, fatigueInfo, weatherForDay, isLast }) {
  const { activePointId, setActivePointId } = useSelection();
  const rowRef = useRef(null);
  const targetId = ev.point_id || ev.id;
  const isActive = activePointId === targetId;

  useEffect(() => {
    if (isActive && rowRef.current) {
      rowRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [isActive]);

  const Icon = pickIcon(EVENT_ICON, ev.type, MapPin);
  const WIcon = pickIcon(WEATHER_ICON, weatherForDay?.summary, null);

  const fatPct = fatigueInfo ? Math.round((fatigueInfo.adjusted_fatigue / 10) * 100) : 0;
  const moralePct = fatigueInfo ? Math.round((fatigueInfo.adjusted_morale / 10) * 100) : 0;

  return (
    <div
      ref={rowRef}
      onClick={() => setActivePointId(targetId)}
      style={{
        position: "relative",
        padding: "12px 12px 12px 36px",
        borderRadius: 10,
        cursor: "pointer",
        background: isActive
          ? "linear-gradient(180deg, rgba(244,246,250,0.10), rgba(244,246,250,0.04))"
          : "transparent",
        border: `1px solid ${isActive ? "var(--rim-bright)" : "transparent"}`,
        transition: "background 0.18s, border-color 0.18s",
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}
    >
      {/* Vertical timeline thread + day marker dot */}
      <div
        style={{
          position: "absolute",
          left: 14,
          top: 0,
          bottom: isLast ? "50%" : 0,
          width: 1,
          background: "var(--rim)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 8,
          top: 14,
          width: 13,
          height: 13,
          borderRadius: 999,
          background: isActive ? "var(--platinum)" : "var(--steel)",
          border: `2px solid ${isActive ? "var(--platinum)" : "var(--chrome)"}`,
          boxShadow: isActive ? "0 0 0 4px rgba(244,246,250,0.18)" : "none",
        }}
      />

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Icon size={12} style={{ color: "var(--silver)" }} />
        <span style={{ fontSize: 11.5, color: "var(--silver)", fontWeight: 600, letterSpacing: "0.02em" }}>
          {ev.start_time}{ev.end_time ? ` – ${ev.end_time}` : ""}
        </span>
        <Pill tone="muted">D{ev.day || 1}</Pill>
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--platinum)", lineHeight: 1.3 }}>
        {ev.title}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        {WIcon && (
          <Pill tone={weatherForDay?.summary === "rain" || weatherForDay?.summary === "thunderstorm" ? "rain" : "muted"}>
            <WIcon size={9} />
            {weatherForDay?.temp_max != null ? `${Math.round(weatherForDay.temp_max)}°` : (weatherForDay?.summary || "—")}
          </Pill>
        )}
        {ev.cost ? <Pill tone="muted">₹{Number(ev.cost).toLocaleString()}</Pill> : null}
        {fatigueInfo?.skippability === "must" && <Pill tone="must">Don't skip</Pill>}
        {fatigueInfo?.skippability === "optional" && <Pill tone="muted">Skippable</Pill>}
      </div>

      {fatigueInfo && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, paddingTop: 2 }}>
          <Gauge pct={fatPct} label="FATIGUE" title={`Fatigue ${fatigueInfo.adjusted_fatigue}/10`} />
          <Gauge pct={moralePct} label="MORALE" title={`Morale ${fatigueInfo.adjusted_morale}/10`} />
          {fatigueInfo.note && (
            <div style={{ fontSize: 10, color: "var(--silver)", lineHeight: 1.3, flex: 1, fontStyle: "italic" }}>
              {fatigueInfo.note}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function EventRail({
  timeline = [],
  fatiguePerEvent = {},
  weatherForecast = {},
  onFitAll,
}) {
  if (!timeline.length) return null;

  // Group label per day for the day-divider rows
  const forecastDays = weatherForecast?.destination
    ? Object.keys(weatherForecast.destination).sort()
    : [];
  const weatherForDay = (d) =>
    weatherForecast?.destination?.[forecastDays[d - 1]] || null;

  const totalDays = Math.max(...timeline.map((ev) => ev.day || 1));

  return (
    <GlassPanel
      strong
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        borderRadius: 16,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 14px",
          borderBottom: "1px solid var(--rim)",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase" }}>
            Timeline
          </span>
          <span style={{ fontSize: 11, color: "var(--chrome)", fontWeight: 500 }}>
            {timeline.length} events · {totalDays} day{totalDays > 1 ? "s" : ""}
          </span>
        </div>
        <GhostButton onClick={onFitAll} title="Fit whole itinerary on map">
          <Maximize2 size={11} style={{ marginRight: 5, verticalAlign: "middle" }} />
          Show all
        </GhostButton>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "8px 12px 16px",
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        {(() => {
          // Render day banner + events for that day
          const days = [...new Set(timeline.map((ev) => ev.day || 1))].sort((a, b) => a - b);
          return days.map((d) => {
            const dayEvents = timeline.filter((ev) => (ev.day || 1) === d);
            return (
              <div key={d}>
                <div
                  style={{
                    fontSize: 9.5,
                    fontWeight: 700,
                    letterSpacing: "0.18em",
                    color: "var(--chrome)",
                    textTransform: "uppercase",
                    padding: "8px 4px 6px 36px",
                  }}
                >
                  Day {d}
                </div>
                {dayEvents.map((ev, i) => (
                  <EventRow
                    key={ev.id || i}
                    ev={ev}
                    fatigueInfo={fatiguePerEvent[ev.id]}
                    weatherForDay={weatherForDay(d)}
                    isLast={i === dayEvents.length - 1 && d === days[days.length - 1]}
                  />
                ))}
              </div>
            );
          });
        })()}
      </div>
    </GlassPanel>
  );
}
