/**
 * DayStrip — bottom-center day selector. Clicking a day focuses the map on
 * that day's events (zoom in, not zoom out to whole map).
 */
import { motion } from "framer-motion";
import { Sun, CloudRain, CloudSnow, Cloud, Zap, Wind, Calendar } from "lucide-react";
import { GlassPanel } from "../ui/Glass";

const W_ICON = {
  clear: Sun, sun: Sun, rain: CloudRain, drizzle: CloudRain, snow: CloudSnow,
  clouds: Cloud, thunderstorm: Zap, mist: Wind, haze: Wind, fog: Wind,
};

export function DayStrip({
  dayThemes = [],
  weatherForecast = {},
  selectedDay,
  onSelectDay,
  totalEvents = 0,
  timeline = [],
}) {
  if (!dayThemes.length) return null;

  const days = dayThemes.map((d) => d.day).sort((a, b) => a - b);
  const forecastDays = weatherForecast?.destination ? Object.keys(weatherForecast.destination).sort() : [];
  const weatherForDay = (d) => weatherForecast?.destination?.[forecastDays[(d || 1) - 1]];

  const active = dayThemes.find((d) => d.day === selectedDay) || dayThemes[0];

  const dayCost = (d) =>
    timeline.filter((ev) => ev.day === d && ev.cost).reduce((s, ev) => s + (Number(ev.cost) || 0), 0);

  return (
    <div style={{
      position: "absolute",
      bottom: 18,
      left: "50%",
      transform: "translateX(-50%)",
      zIndex: 38,
      pointerEvents: "auto",
      maxWidth: "min(880px, calc(100% - 380px))",
      width: "100%",
    }}>
      <GlassPanel strong style={{
        padding: "14px 18px",
        display: "flex", flexDirection: "column", gap: 12,
      }}>
        {/* Day pills row */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          justifyContent: "center", flexWrap: "wrap",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginRight: 4 }}>
            <Calendar size={13} style={{ color: "var(--silver)" }} />
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.12em",
              color: "var(--silver)", textTransform: "uppercase",
            }}>
              {totalEvents} stops · {dayThemes.length} days
            </span>
          </div>
          {days.map((d) => {
            const w = weatherForDay(d);
            const WIcon = w ? (W_ICON[w.summary] || Sun) : null;
            const isActive = d === active.day;
            const cost = dayCost(d);
            return (
              <motion.button
                key={d}
                onClick={() => onSelectDay(d)}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                style={{
                  display: "inline-flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 2,
                  padding: "8px 18px",
                  minWidth: 80,
                  borderRadius: 14,
                  cursor: "pointer",
                  border: `1px solid ${isActive ? "rgba(0,0,0,0.4)" : "var(--rim)"}`,
                  background: isActive
                    ? "linear-gradient(180deg, #3a3d44, #1d1f25)"
                    : "rgba(255,255,255,0.7)",
                  color: isActive ? "#f5f5f7" : "var(--chrome)",
                  transition: "background 0.2s, border-color 0.2s, transform 0.15s",
                  fontFamily: "Inter, sans-serif",
                  boxShadow: isActive
                    ? "inset 0 1px 0 rgba(255,255,255,0.18), 0 4px 12px rgba(20,22,28,0.18)"
                    : "0 1px 3px rgba(20,22,28,0.05)",
                }}
              >
                <span style={{ fontSize: 13, fontWeight: 800, letterSpacing: "0.02em" }}>
                  Day {d}
                </span>
                <div style={{
                  display: "flex", alignItems: "center", gap: 6,
                  fontSize: 10, opacity: 0.85,
                }}>
                  {WIcon && (
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 2 }}>
                      <WIcon size={11} />
                      {w?.temp_max != null && `${Math.round(w.temp_max)}°`}
                    </span>
                  )}
                  {cost > 0 && (
                    <span style={{ fontWeight: 600 }}>
                      ₹{cost.toLocaleString()}
                    </span>
                  )}
                </div>
              </motion.button>
            );
          })}
        </div>

        {/* Selected day theme + weather note */}
        <motion.div
          key={active.day}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: "center" }}
        >
          {active.theme && (
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--platinum)", marginBottom: 2 }}>
              {active.theme}
            </div>
          )}
          {active.summary && (
            <div style={{ fontSize: 11.5, color: "var(--chrome)", lineHeight: 1.45 }}>
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
