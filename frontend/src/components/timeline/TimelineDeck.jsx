/**
 * Horizontal "aviation gauge" timeline pinned to the bottom of the screen.
 *
 * One lane per trip day. Each event is a glass card with:
 *  - icon + title + time range
 *  - weather chip (if forecast for this day)
 *  - traffic chip (if traffic agent returned data)
 *  - fatigue gauge + skippability badge
 *
 * Bi-directional sync with the map via SelectionContext:
 *  - Clicking a card sets activeEventId → map flies to that point
 *  - When map marker is clicked, activeEventId changes → card scrolls into view
 *
 * Layout: collapsible (default open). Day labels on the left. Smooth horizontal
 * scroll within each lane (native scroll, custom thin chrome scrollbar).
 */
import { useEffect, useRef } from "react";
import {
  Sun, CloudRain, CloudSnow, Cloud, Zap, Wind,
  Car, Footprints, UtensilsCrossed, Hotel, MapPin, Camera,
} from "lucide-react";
import { GlassPanel, Pill, Gauge } from "../ui/Glass";
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
  walk: Footprints,
};

function pickIcon(map, key, fallback) {
  const k = String(key || "").toLowerCase();
  return map[k] || fallback;
}

function eventId(ev, i) {
  return ev.id || ev.event_id || `${ev.day || 1}-${ev.start_time || i}-${ev.title || i}`;
}

function eventPointId(ev) {
  // Sync key the map uses: prefer explicit id, else type:label
  if (!ev) return null;
  if (ev.point_id) return ev.point_id;
  if (ev.label && ev.type) return `${ev.type}:${ev.label}`;
  if (ev.title && ev.lat) return `activity:${ev.title}`;
  return null;
}

function TimelineCard({ ev, idx, fatigueInfo, weatherForDay, trafficForRoute }) {
  const { activePointId, setActivePointId } = useSelection();
  const cardRef = useRef(null);
  const eid = eventId(ev, idx);
  const pid = eventPointId(ev);
  const isActive = activePointId && (activePointId === pid || activePointId === eid);

  // Scroll into view when this becomes active via map click
  useEffect(() => {
    if (isActive && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    }
  }, [isActive]);

  const Icon = pickIcon(EVENT_ICON, ev.type, MapPin);
  const WIcon = pickIcon(WEATHER_ICON, weatherForDay?.summary, null);

  // 0-10 → 0-100 for gauge
  const fatPct = Math.round(((fatigueInfo?.adjusted_fatigue ?? 0) / 10) * 100);
  const moralePct = Math.round(((fatigueInfo?.adjusted_morale ?? 0) / 10) * 100);
  const skip = fatigueInfo?.skippability;

  const skipTone = skip === "must" ? "must" : skip === "optional" ? "muted" : "default";
  const skipLabel = skip === "must" ? "Don't skip" : skip === "optional" ? "Skippable" : "Recommended";

  const onClick = () => {
    if (pid) setActivePointId(pid);
    else setActivePointId(eid);
  };

  return (
    <div
      ref={cardRef}
      className={`tl-event glass ${isActive ? "is-active" : ""}`}
      style={{
        padding: "10px 12px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        scrollSnapAlign: "start",
        flexShrink: 0,
      }}
      onClick={onClick}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div
          style={{
            width: 24, height: 24, borderRadius: 8,
            background: "rgba(255,255,255,0.06)",
            border: "1px solid var(--rim)",
            display: "grid", placeItems: "center",
            flexShrink: 0,
          }}
        >
          <Icon size={13} style={{ color: "var(--chrome)" }} />
        </div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div
            style={{
              fontSize: 12.5,
              fontWeight: 600,
              color: "var(--platinum)",
              lineHeight: 1.2,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
            title={ev.title}
          >
            {ev.title || "Event"}
          </div>
          {(ev.start_time || ev.end_time) && (
            <div style={{ fontSize: 10, color: "var(--silver)", fontWeight: 500, letterSpacing: "0.04em" }}>
              {ev.start_time}{ev.end_time ? ` – ${ev.end_time}` : ""}
            </div>
          )}
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        {WIcon && (
          <Pill tone={weatherForDay?.summary === "rain" || weatherForDay?.summary === "thunderstorm" ? "rain" : "muted"}>
            <WIcon size={10} />
            {weatherForDay?.temp_max ? `${Math.round(weatherForDay.temp_max)}°` : weatherForDay?.summary || "—"}
          </Pill>
        )}
        {trafficForRoute?.available && (
          <Pill tone="warning">
            +{trafficForRoute.data?.expected_delay_minutes ?? 0}m traffic
          </Pill>
        )}
        {skip && <Pill tone={skipTone}>{skipLabel}</Pill>}
      </div>

      {fatigueInfo && (
        <div style={{ display: "flex", alignItems: "center", gap: 12, paddingTop: 2 }}>
          <Gauge pct={fatPct} label="FATIGUE" title={`Fatigue ${fatigueInfo.adjusted_fatigue}/10`} />
          <Gauge pct={moralePct} label="MORALE" title={`Morale ${fatigueInfo.adjusted_morale}/10`} />
          {fatigueInfo.note && (
            <div style={{ fontSize: 9.5, color: "var(--silver)", lineHeight: 1.3, flex: 1, fontStyle: "italic" }}>
              {fatigueInfo.note}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function TimelineDeck({
  timeline = [],
  fatiguePerEvent = {},
  weatherForecast = {},
  traffic = {},
  collapsed = false,
  onToggle,
}) {
  if (!timeline.length) return null;

  // Group events by day
  const byDay = new Map();
  timeline.forEach((ev) => {
    const d = ev.day || 1;
    if (!byDay.has(d)) byDay.set(d, []);
    byDay.get(d).push(ev);
  });
  const days = [...byDay.keys()].sort((a, b) => a - b);

  // Resolve weather by day index — backend keys forecast.destination by date.
  // Mapping ordinal day (1, 2, 3...) → nth forecast entry as a best-effort.
  const forecastDays = weatherForecast?.destination
    ? Object.keys(weatherForecast.destination).sort()
    : [];
  const weatherForDay = (d) =>
    weatherForecast?.destination?.[forecastDays[d - 1]] || null;

  const trafficDefault = traffic?._default || (Object.values(traffic)[0] ?? null);

  return (
    <div className="timeline-deck">
      <GlassPanel
        strong
        style={{
          borderBottomLeftRadius: 0,
          borderBottomRightRadius: 0,
          borderBottom: "none",
          padding: "10px 16px 14px",
          maxHeight: collapsed ? 38 : 240,
          overflow: "hidden",
          transition: "max-height 0.3s ease",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: collapsed ? 0 : 10,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              style={{
                fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em",
                color: "var(--silver)", textTransform: "uppercase",
              }}
            >
              Timeline
            </span>
            <Pill tone="muted">{timeline.length} events · {days.length} day{days.length > 1 ? "s" : ""}</Pill>
          </div>
          {onToggle && (
            <button
              onClick={onToggle}
              className="btn-ghost"
              style={{ padding: "4px 10px", borderRadius: 999, fontSize: 10.5 }}
            >
              {collapsed ? "Expand" : "Collapse"}
            </button>
          )}
        </div>

        {!collapsed && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {days.map((d) => (
              <div key={d} style={{ display: "flex", gap: 10, alignItems: "stretch" }}>
                <div
                  style={{
                    minWidth: 48,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-start",
                    justifyContent: "center",
                    paddingTop: 4,
                  }}
                >
                  <span style={{ fontSize: 9, fontWeight: 700, color: "var(--silver)", letterSpacing: "0.12em" }}>
                    DAY
                  </span>
                  <span style={{ fontSize: 18, fontWeight: 700, color: "var(--platinum)", lineHeight: 1, marginTop: 2 }}>
                    {d}
                  </span>
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    overflowX: "auto",
                    paddingBottom: 4,
                    scrollSnapType: "x proximity",
                    flex: 1,
                  }}
                >
                  {byDay.get(d).map((ev, i) => (
                    <TimelineCard
                      key={eventId(ev, i)}
                      ev={ev}
                      idx={i}
                      fatigueInfo={fatiguePerEvent[eventId(ev, i)]}
                      weatherForDay={weatherForDay(d)}
                      trafficForRoute={trafficDefault}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassPanel>
    </div>
  );
}
