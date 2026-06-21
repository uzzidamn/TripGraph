/**
 * EventDetailOverlay — slide-in glass card anchored to the right edge of the map.
 * Appears when a timeline/marker selection is made. Shows:
 *   - event header + tags
 *   - weather chip for the day
 *   - fatigue + morale gauges
 *   - hotel/restaurant alternatives (if the event is a stay or meal)
 *   - hotel-deal callout (if HotelDealsClient is wired up; silent otherwise)
 *
 * Closes when the user clears the selection (clicks the close button OR
 * clicks an empty area of the map).
 */
import { motion, AnimatePresence } from "framer-motion";
import { X, BadgePercent } from "lucide-react";
import { GlassPanel, Pill, Gauge, GhostButton } from "../ui/Glass";
import { useSelection } from "../../hooks/useSelection";

function findEvent(timeline, id) {
  if (!id) return null;
  return timeline.find((ev, i) => {
    const eid = ev.id || ev.event_id || `${ev.day || 1}-${ev.start_time || i}-${ev.title || i}`;
    const pid = ev.point_id || (ev.label && ev.type ? `${ev.type}:${ev.label}` : null);
    return eid === id || pid === id;
  });
}

function findHotelAlternatives(itinerary, hotelCandidates, currentName) {
  const all = hotelCandidates || itinerary?.hotel_candidates || [];
  return all
    .filter((h) => h && h.name && h.name !== currentName)
    .slice(0, 3);
}

export function EventDetailOverlay({
  timeline = [],
  itinerary,
  hotelCandidates = [],
  fatiguePerEvent = {},
  weatherForecast = {},
  hotelDeals = null,
}) {
  const { activePointId, setActivePointId } = useSelection();
  const event = findEvent(timeline, activePointId);

  return (
    <AnimatePresence>
      {event && (
        <motion.div
          key={activePointId}
          initial={{ x: 380, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 380, opacity: 0 }}
          transition={{ type: "spring", stiffness: 280, damping: 30 }}
          style={{
            position: "absolute",
            top: 70,
            right: 16,
            width: 320,
            zIndex: 55,
            pointerEvents: "auto",
          }}
        >
          <GlassPanel strong style={{ padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase" }}>
                  Day {event.day || 1} · {event.type || "event"}
                </div>
                <div style={{ fontSize: 15, fontWeight: 700, color: "var(--platinum)", marginTop: 2 }}>
                  {event.title}
                </div>
                {(event.start_time || event.end_time) && (
                  <div style={{ fontSize: 11, color: "var(--silver)", marginTop: 2 }}>
                    {event.start_time}{event.end_time ? ` – ${event.end_time}` : ""}
                  </div>
                )}
              </div>
              <button
                onClick={() => setActivePointId(null)}
                style={{
                  background: "transparent",
                  border: "1px solid var(--rim)",
                  borderRadius: 999,
                  width: 26, height: 26,
                  display: "grid",
                  placeItems: "center",
                  color: "var(--silver)",
                  cursor: "pointer",
                }}
                aria-label="Close"
              >
                <X size={13} />
              </button>
            </div>

            {/* Tags */}
            {Array.isArray(event.tags) && event.tags.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {event.tags.slice(0, 5).map((t) => (
                  <Pill key={t} tone="muted">{t}</Pill>
                ))}
              </div>
            )}

            {/* Fatigue / morale gauges */}
            {(() => {
              const eid = event.id || event.event_id || `${event.day || 1}-${event.start_time}-${event.title}`;
              const f = fatiguePerEvent[eid];
              if (!f) return null;
              const fPct = Math.round((f.adjusted_fatigue / 10) * 100);
              const mPct = Math.round((f.adjusted_morale / 10) * 100);
              return (
                <div>
                  <div style={{ display: "flex", gap: 14, alignItems: "center", padding: "8px 0" }}>
                    <Gauge pct={fPct} label="FATIGUE" title={`${f.adjusted_fatigue}/10`} />
                    <Gauge pct={mPct} label="MORALE" title={`${f.adjusted_morale}/10`} />
                    <div style={{ flex: 1 }}>
                      <Pill tone={f.skippability === "must" ? "must" : f.skippability === "optional" ? "muted" : "default"}>
                        {f.skippability === "must" ? "Don't skip" : f.skippability === "optional" ? "Skippable" : "Recommended"}
                      </Pill>
                      {f.note && (
                        <p style={{ fontSize: 10.5, color: "var(--silver)", marginTop: 4, fontStyle: "italic", lineHeight: 1.4 }}>
                          {f.note}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Weather chip (uses first-day forecast as proxy) */}
            {(() => {
              const days = weatherForecast?.destination ? Object.keys(weatherForecast.destination).sort() : [];
              const w = weatherForecast?.destination?.[days[(event.day || 1) - 1]];
              if (!w) return null;
              return (
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <Pill tone={w.summary === "rain" ? "rain" : "muted"}>
                    {w.summary || "—"}
                  </Pill>
                  {w.temp_max != null && (
                    <span style={{ fontSize: 11, color: "var(--silver)" }}>
                      {Math.round(w.temp_min)}° / {Math.round(w.temp_max)}°
                    </span>
                  )}
                  {w.pop_max > 0.3 && (
                    <span style={{ fontSize: 10.5, color: "var(--chrome)" }}>
                      {Math.round(w.pop_max * 100)}% rain
                    </span>
                  )}
                </div>
              );
            })()}

            {/* Hotel alternatives (only for hotel/stay events) */}
            {["hotel", "stay", "checkin"].includes((event.type || "").toLowerCase()) && (
              <div>
                <div style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase", marginBottom: 6 }}>
                  Alternatives
                </div>
                {findHotelAlternatives(itinerary, hotelCandidates, event.title).map((h) => (
                  <div
                    key={h.hotel_id || h.name}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "6px 0",
                      borderTop: "1px solid var(--rim)",
                      gap: 8,
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: 12, color: "var(--platinum)", fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {h.name}
                      </div>
                      {h.tier && (
                        <div style={{ fontSize: 10, color: "var(--silver)" }}>
                          {h.tier} tier
                        </div>
                      )}
                    </div>
                    {h.price_per_night != null && (
                      <div style={{ fontSize: 12, color: "var(--chrome)", fontWeight: 700 }}>
                        ₹{Number(h.price_per_night).toLocaleString()}
                      </div>
                    )}
                  </div>
                ))}

                {/* Hotel deals callout (silent until API key configured) */}
                {hotelDeals?.available && hotelDeals.data?.deals?.length > 0 && (
                  <div
                    style={{
                      marginTop: 10,
                      padding: 8,
                      borderRadius: 10,
                      border: "1px solid var(--rim-bright)",
                      background: "rgba(255,255,255,0.04)",
                      display: "flex",
                      gap: 8,
                      alignItems: "center",
                    }}
                  >
                    <BadgePercent size={14} style={{ color: "var(--chrome)" }} />
                    <div style={{ fontSize: 11, color: "var(--chrome)" }}>
                      {hotelDeals.data.deals.length} live deal{hotelDeals.data.deals.length > 1 ? "s" : ""} below typical price
                    </div>
                  </div>
                )}
              </div>
            )}
          </GlassPanel>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
