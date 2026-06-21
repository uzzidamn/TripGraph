/**
 * DayStrip — minimal bottom-center selector that picks which day is "focused"
 * on the map. Replaces the vertical EventRail (left column).
 *
 * It does NOT list events. Events live on the map as numbered pins; clicking a
 * pin opens the rich popover. The strip exists only so the user can switch
 * which day's pins/polyline are highlighted.
 *
 * Also shows the day's theme + weather note from the architect.
 */
import { motion } from "framer-motion";
import { Sun, CloudRain, CloudSnow, Cloud, Zap, Wind, Calendar } from "lucide-react";
import { GlassPanel, Pill } from "../ui/Glass";

const W_ICON = {
  clear: Sun, sun: Sun, rain: CloudRain, drizzle: CloudRain, snow: CloudSnow,
  clouds: Cloud, thunderstorm: Zap, mist: Wind, haze: Wind, fog: Wind,
};

export function DayStrip({
  dayThemes = [],          // [{ day, theme, summary, weather_note }]
  weatherForecast = {},
  selectedDay,
  onSelectDay,
  totalEvents = 0,
  costBreakdown = null,
  timeline = [],
}) {
  if (!dayThemes.length) return null;

  const days = dayThemes.map((d) => d.day).sort((a, b) => a - b);
  const forecastDays = weatherForecast?.destination ? Object.keys(weatherForecast.destination).sort() : [];
  const weatherForDay = (d) => weatherForecast?.destination?.[forecastDays[(d || 1) - 1]];

  const active = dayThemes.find((d) => d.day === selectedDay) || dayThemes[0];

  // Per-day cost from timeline events
  const dayCost = (d) => {
    return timeline
      .filter(ev => ev.day === d && ev.cost)
      .reduce((sum, ev) => sum + (Number(ev.cost) || 0), 0);
  };

  return (
    <div
      style={{
        position: "absolute",
        bottom: 16,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 38,
        pointerEvents: "auto",
        maxWidth: "min(720px, calc(100% - 380px))",
        width: "100%",
      }}
    >
      <GlassPanel strong style={{ padding: "10px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
        {/* Day pills row */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center" }}>
          <Calendar size={12} style={{ color: "var(--silver)" }} />
          <span style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase" }}>
            {totalEvents} stops · {dayThemes.length} days
          </span>
          <div style={{ width: 1, height: 14, background: "var(--rim)", margin: "0 4px" }} />
          {days.map((d) => {
            const w = weatherForDay(d);
            const WIcon = w ? (W_ICON[w.summary] || Sun) : null;
            const isActive = d === active.day;
            return (
              <motion.button
                key={d}
                onClick={() => onSelectDay(d)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "6px 14px",
                  borderRadius: 999,
                  fontSize: 11.5,
                  fontWeight: 700,
                  letterSpacing: "0.02em",
                  cursor: "pointer",
                  border: `1px solid ${isActive ? "rgba(0,0,0,0.35)" : "var(--rim)"}`,
                  background: isActive
                    ? "linear-gradient(180deg, #3a3d44, #1d1f25)"
                    : "rgba(255,255,255,0.6)",
                  color: isActive ? "#f5f5f7" : "var(--chrome)",
                  transition: "background 0.18s, border-color 0.18s",
                  fontFamily: "Inter, sans-serif",
                }}
              >
                Day {d}
                {WIcon && (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 3, opacity: 0.85 }}>
                    <WIcon size={10} />
                    {w?.temp_max != null && `${Math.round(w.temp_max)}°`}
                  </span>
                )}
                {dayCost(d) > 0 && (
                  <span style={{ fontSize: 9, opacity: 0.75, fontWeight: 600 }}>
                    ₹{dayCost(d).toLocaleString()}
                  </span>
                )}
              </motion.button>
            );
          })}
        </div>

        {/* Selected day's theme + weather note */}
        <motion.div
          key={active.day}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: "center" }}
        >
          {active.theme && (
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--platinum)", marginBottom: 2 }}>
              {active.theme}
            </div>
          )}
          {active.summary && (
            <div style={{ fontSize: 11, color: "var(--chrome)", lineHeight: 1.45 }}>
              {active.summary}
            </div>
          )}
          {active.weather_note && (
            <div style={{ fontSize: 10.5, color: "var(--silver)", fontStyle: "italic", marginTop: 4 }}>
              {active.weather_note}
            </div>
          )}
        </motion.div>
      </GlassPanel>
    </div>
  );
}
