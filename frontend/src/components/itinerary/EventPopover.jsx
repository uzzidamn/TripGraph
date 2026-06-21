/**
 * EventPopover — single map-anchored glass card that consolidates ALL
 * per-event enrichment in one place.
 *
 * Surfaces:
 *  - Event header (day, type, title, time)
 *  - Tags
 *  - Fatigue & morale gauges + skippability badge + LLM context note
 *  - Weather chip for the day (with rain warning)
 *  - Hotel-specific: 3 alternatives + deals callout + decision rationale
 *  - Destination-specific: advisory items (logistics) + local tips
 *  - Activity-specific: why-this-pick reasoning
 *
 * Placement: anchored to the map pin via a Leaflet pixel-projection. The
 * parent passes `anchorPx` ({x, y}) and we offset ourselves to one side.
 */
import { motion, AnimatePresence } from "framer-motion";
import { X, BadgePercent, Info, Lightbulb, Search, Plane, Train, ExternalLink, Star } from "lucide-react";
import { GlassPanel, Pill, Gauge } from "../ui/Glass";
import { useSelection } from "../../hooks/useSelection";

const GMAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

/** Build a Google Places photo media URL from a photo resource name. */
function googlePhotoUrl(photoName, w = 420, h = 240) {
  if (!photoName || !GMAPS_KEY) return null;
  return `https://places.googleapis.com/v1/${photoName}/media?maxWidthPx=${w}&maxHeightPx=${h}&key=${GMAPS_KEY}`;
}

function activeEventFromTimeline(timeline, activeId) {
  if (!activeId) return null;
  // Match by point_id first (map-driven selection), else by event id (timeline-driven)
  return (
    timeline.find((ev) => ev.point_id === activeId) ||
    timeline.find((ev) => ev.id === activeId) ||
    null
  );
}

function hotelAlternatives(state, currentName, max = 3) {
  const list = state?.itinerary?.hotel_candidates || state?.hotelCandidates || state?.hotelAlternatives || [];
  return list.filter((h) => h?.name && h.name !== currentName).slice(0, max);
}

/** Resolve which insights record applies to this event (destination / hotel / activity). */
function insightsForEvent(event, itinerary, insightsPerPlace) {
  if (!event || !insightsPerPlace) return null;
  const dest = (itinerary?.route?.destination || "").toLowerCase();
  const type = (event.type || "").toLowerCase();
  const titleLower = (event.title || "").toLowerCase();

  // Hotel events → match the hotel insights record (keyed "hotel:<id-or-name>")
  if (["hotel", "stay", "checkin", "checkout"].includes(type)) {
    const hotel = itinerary?.hotel || {};
    const hid = hotel.hotel_id || hotel.name;
    if (hid && insightsPerPlace[`hotel:${hid}`]) return insightsPerPlace[`hotel:${hid}`];
  }
  // Activity events → match by activity id (keyed "activity:<id-or-name>")
  if (["activity", "experience"].includes(type)) {
    for (const [k, v] of Object.entries(insightsPerPlace)) {
      if (k.startsWith("activity:") && titleLower.includes(k.slice("activity:".length).toLowerCase().split(" ")[0])) {
        return v;
      }
    }
  }
  // Destination-titled events (e.g. "Continue drive to Manali")
  if (dest && titleLower.includes(dest)) {
    return insightsPerPlace[`destination:${itinerary?.route?.destination}`] || null;
  }
  return null;
}

export function EventPopover({
  timeline = [],
  itinerary,
  hotelCandidates = [],
  fatiguePerEvent = {},
  weatherForecast = {},
  hotelDeals = null,
  insightsPerPlace = {},
  flights = null,
  trains = null,
}) {
  const { activePointId, setActivePointId, anchorPx } = useSelection();
  const event = activeEventFromTimeline(timeline, activePointId);
  if (!event) return null;

  const fatigueInfo = fatiguePerEvent[event.id];
  const forecastDays = weatherForecast?.destination ? Object.keys(weatherForecast.destination).sort() : [];
  const w = weatherForecast?.destination?.[forecastDays[(event.day || 1) - 1]];

  const isHotel = ["hotel", "stay", "checkin", "checkout"].includes((event.type || "").toLowerCase());
  const isActivity = ["activity", "experience", "sightseeing"].includes((event.type || "").toLowerCase());
  const isDestination = (event.title || "").toLowerCase().includes(itinerary?.route?.destination?.toLowerCase() || "___never___");

  const advisory = itinerary?.advisory_items || [];
  const localTips = itinerary?.local_tips || [];
  const hotelReason = itinerary?.hotel_selection_reason;

  // Position: anchored to the map pin when pixel coords available, else top-right fallback
  const popoverStyle = anchorPx
    ? (() => {
        const w = 340;
        const pinRight = anchorPx.x + 20;
        const pinLeft = anchorPx.x - w - 20;
        const fitsRight = pinRight + w < window.innerWidth - 20;
        const left = fitsRight ? pinRight : Math.max(20, pinLeft);
        const top = Math.min(window.innerHeight - 300, Math.max(60, anchorPx.y - 100));
        return { position: "absolute", left, top, width: w, zIndex: 55, pointerEvents: "auto" };
      })()
    : { position: "absolute", right: 24, top: 80, width: 340, zIndex: 55, pointerEvents: "auto" };

  return (
    <AnimatePresence>
      <motion.div
        key={activePointId}
        initial={{ x: 24, opacity: 0, scale: 0.96 }}
        animate={{ x: 0, opacity: 1, scale: 1 }}
        exit={{ x: 24, opacity: 0, scale: 0.96 }}
        transition={{ type: "spring", stiffness: 320, damping: 32 }}
        style={popoverStyle}
      >
        <GlassPanel
          strong
          style={{
            padding: 14,
            maxHeight: "min(80vh, 640px)",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          {/* Header */}
          <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase" }}>
                Day {event.day || 1} · {event.type || "event"}
              </div>
              <div style={{ fontSize: 14.5, fontWeight: 700, color: "var(--platinum)", marginTop: 2, lineHeight: 1.3 }}>
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
                display: "grid", placeItems: "center",
                color: "var(--silver)",
                cursor: "pointer",
              }}
              aria-label="Close"
            >
              <X size={13} />
            </button>
          </div>

          {/* Per-event cost + transport mode badge */}
          {(event.cost || event.transport_mode) && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              {event.cost > 0 && (
                <div style={{
                  fontSize: 14, fontWeight: 800, color: "var(--platinum)",
                  background: "rgba(0,0,0,0.04)", padding: "4px 10px", borderRadius: 8,
                }}>
                  ₹{Number(event.cost).toLocaleString()} <span style={{ fontSize: 10, fontWeight: 500, color: "var(--silver)" }}>pp</span>
                </div>
              )}
              {event.transport_mode && (
                <Pill tone="muted">{event.transport_mode}</Pill>
              )}
              {event.skippability && (
                <Pill tone={event.skippability === "must" ? "must" : event.skippability === "optional" ? "muted" : "default"}>
                  {event.skippability === "must" ? "Don't skip" : event.skippability === "optional" ? "Skippable" : "Recommended"}
                </Pill>
              )}
            </div>
          )}

          {/* Google Place photo */}
          {(() => {
            const url = googlePhotoUrl(event.photo_name);
            if (!url) return null;
            return (
              <div style={{ borderRadius: 10, overflow: "hidden", border: "1px solid var(--rim)", lineHeight: 0 }}>
                <img
                  src={url}
                  alt={event.title}
                  loading="lazy"
                  style={{ width: "100%", height: 140, objectFit: "cover", display: "block" }}
                  onError={(e) => { e.currentTarget.parentElement.style.display = "none"; }}
                />
              </div>
            );
          })()}

          {/* Rating + "why visit" (Google editorial summary) */}
          {(event.rating || event.editorial_summary) && (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {event.rating && (
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <Star size={12} style={{ color: "#b8862f", fill: "#b8862f" }} />
                  <span style={{ fontSize: 12, fontWeight: 700, color: "var(--platinum)" }}>{event.rating}</span>
                  {event.rating_count && (
                    <span style={{ fontSize: 10.5, color: "var(--silver)" }}>
                      ({Number(event.rating_count).toLocaleString()} reviews)
                    </span>
                  )}
                </div>
              )}
              {event.editorial_summary && (
                <p style={{ fontSize: 11.5, color: "var(--chrome)", lineHeight: 1.5 }}>
                  {event.editorial_summary}
                </p>
              )}
            </div>
          )}

          {/* Architect's "why visit" — the hero reasoning */}
          {event.why && (
            <p style={{
              fontSize: 12.5, color: "var(--platinum)", fontWeight: 500,
              lineHeight: 1.55, padding: "8px 10px",
              background: "rgba(0,0,0,0.04)", borderRadius: 8,
              borderLeft: "2px solid var(--chrome)",
            }}>
              {event.why}
            </p>
          )}

          {/* Architect's pro tip */}
          {event.tips && (
            <div style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
              <Lightbulb size={11} style={{ color: "#b8862f", marginTop: 2, flexShrink: 0 }} />
              <p style={{ fontSize: 11, color: "var(--chrome)", lineHeight: 1.45 }}>
                {event.tips}
              </p>
            </div>
          )}

          {/* Opening hours — when known */}
          {Array.isArray(event.opening_hours) && event.opening_hours.length > 0 && (
            <details style={{ fontSize: 10.5, color: "var(--silver)" }}>
              <summary style={{ cursor: "pointer", fontWeight: 600, color: "var(--chrome)" }}>
                Hours
              </summary>
              <div style={{ marginTop: 4, padding: "4px 0", lineHeight: 1.55 }}>
                {event.opening_hours.slice(0, 7).map((h, i) => (
                  <div key={i}>{h}</div>
                ))}
              </div>
            </details>
          )}

          {/* Tags */}
          {Array.isArray(event.tags) && event.tags.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {event.tags.slice(0, 5).map((t) => (
                <Pill key={t} tone="muted">{t}</Pill>
              ))}
            </div>
          )}

          {/* Weather */}
          {w && (
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
          )}

          {/* Fatigue / morale gauges */}
          {fatigueInfo && (
            <div style={{ display: "flex", gap: 14, alignItems: "center", padding: "6px 0", borderTop: "1px solid var(--rim)", borderBottom: "1px solid var(--rim)" }}>
              <Gauge pct={(fatigueInfo.adjusted_fatigue / 10) * 100} label="FATIGUE" title={`${fatigueInfo.adjusted_fatigue}/10`} />
              <Gauge pct={(fatigueInfo.adjusted_morale / 10) * 100} label="MORALE" title={`${fatigueInfo.adjusted_morale}/10`} />
              <div style={{ flex: 1 }}>
                <Pill tone={fatigueInfo.skippability === "must" ? "must" : fatigueInfo.skippability === "optional" ? "muted" : "default"}>
                  {fatigueInfo.skippability === "must" ? "Don't skip" : fatigueInfo.skippability === "optional" ? "Skippable" : "Recommended"}
                </Pill>
                {fatigueInfo.note && (
                  <p style={{ fontSize: 10.5, color: "var(--silver)", marginTop: 4, fontStyle: "italic", lineHeight: 1.4 }}>
                    {fatigueInfo.note}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Hotel-specific section */}
          {isHotel && (
            <div>
              <SectionLabel>Why this hotel</SectionLabel>
              {hotelReason ? (
                <p style={{ fontSize: 11.5, color: "var(--chrome)", lineHeight: 1.5, fontStyle: "italic" }}>
                  {hotelReason}
                </p>
              ) : (
                <p style={{ fontSize: 11, color: "var(--silver)", fontStyle: "italic" }}>
                  Selected by KG ranking (best tier match + price).
                </p>
              )}

              <SectionLabel style={{ marginTop: 10 }}>Alternatives</SectionLabel>
              {hotelAlternatives({ itinerary, hotelCandidates }, event.title || event.name).length === 0 && (
                <p style={{ fontSize: 11, color: "var(--silver)" }}>No alternatives in the KG for this destination.</p>
              )}
              {hotelAlternatives({ itinerary, hotelCandidates }, event.title || event.name).map((h) => (
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
                      <div style={{ fontSize: 10, color: "var(--silver)" }}>{h.tier} tier</div>
                    )}
                  </div>
                  {h.price_per_night != null && (
                    <div style={{ fontSize: 12, color: "var(--chrome)", fontWeight: 700 }}>
                      ₹{Number(h.price_per_night).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}

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

          {/* Destination-specific: logistics + local tips */}
          {(isDestination || event.type === "destination") && (advisory.length > 0 || localTips.length > 0) && (
            <div>
              {advisory.length > 0 && (
                <>
                  <SectionLabel><Info size={10} style={{ marginRight: 4, verticalAlign: "middle" }} />Logistics &amp; advisories</SectionLabel>
                  {advisory.slice(0, 3).map((a, i) => (
                    <div
                      key={i}
                      style={{
                        padding: "8px 10px",
                        marginTop: 6,
                        borderRadius: 10,
                        background: "rgba(255,255,255,0.04)",
                        border: "1px solid var(--rim)",
                      }}
                    >
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--chrome)" }}>{a.title}</div>
                      <div style={{ fontSize: 10.5, color: "var(--silver)", lineHeight: 1.4, marginTop: 3 }}>{a.description}</div>
                      {a.estimated_cost && (
                        <Pill tone="muted" style={{ marginTop: 6 }}>{a.estimated_cost}</Pill>
                      )}
                    </div>
                  ))}
                </>
              )}
              {localTips.length > 0 && (
                <>
                  <SectionLabel style={{ marginTop: 10 }}>
                    <Lightbulb size={10} style={{ marginRight: 4, verticalAlign: "middle" }} />Local tips
                  </SectionLabel>
                  <ul style={{ listStyle: "none", padding: 0, marginTop: 6 }}>
                    {localTips.slice(0, 3).map((tip, i) => (
                      <li
                        key={i}
                        style={{
                          fontSize: 11, color: "var(--silver)", padding: "4px 0",
                          borderTop: i ? "1px solid var(--rim)" : "none",
                          lineHeight: 1.5,
                        }}
                      >
                        {tip}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          {/* Activity-specific: cost + duration recap */}
          {isActivity && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {event.cost ? <Pill tone="muted">₹{Number(event.cost).toLocaleString()} pp</Pill> : null}
              {event.duration_minutes ? <Pill tone="muted">{event.duration_minutes} min</Pill> : null}
            </div>
          )}

          {/* DuckDuckGo insights — show on every relevant event */}
          {(() => {
            const insight = insightsForEvent(event, itinerary, insightsPerPlace);
            if (!insight) return null;
            return (
              <div style={{ marginTop: 4 }}>
                <SectionLabel>
                  <Search size={10} style={{ marginRight: 4, verticalAlign: "middle" }} />
                  More info — DuckDuckGo
                </SectionLabel>
                {insight.abstract && (
                  <p style={{ fontSize: 11.5, color: "var(--chrome)", lineHeight: 1.55, marginBottom: 6 }}>
                    {insight.abstract.length > 320 ? `${insight.abstract.slice(0, 320)}…` : insight.abstract}
                  </p>
                )}
                {insight.related_topics?.length > 0 && (
                  <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                    {insight.related_topics.slice(0, 3).map((t, i) => (
                      <li key={i} style={{
                        fontSize: 10.5,
                        color: "var(--silver)",
                        lineHeight: 1.4,
                        padding: "4px 0",
                        borderTop: i ? "1px solid var(--rim)" : "none",
                      }}>
                        {t.url ? (
                          <a href={t.url} target="_blank" rel="noreferrer"
                             style={{ color: "var(--chrome)", textDecoration: "none" }}>
                            {t.text}
                            <ExternalLink size={9} style={{ marginLeft: 4, verticalAlign: "middle", opacity: 0.6 }} />
                          </a>
                        ) : t.text}
                      </li>
                    ))}
                  </ul>
                )}
                {insight.source_url && (
                  <a href={insight.source_url} target="_blank" rel="noreferrer"
                     style={{ fontSize: 10, color: "var(--silver)", marginTop: 6, display: "inline-flex", alignItems: "center", gap: 3 }}>
                    source <ExternalLink size={9} />
                  </a>
                )}
              </div>
            );
          })()}

          {/* Flight advisory — only on origin / destination / travel events of a long trip */}
          {flights?.advisory_available && flights.advisory && (event.type === "travel" || (itinerary?.route?.destination || "").toLowerCase().includes((event.title || "").toLowerCase().split(" ").pop())) && (
            <div style={{ marginTop: 4 }}>
              <SectionLabel>
                <Plane size={10} style={{ marginRight: 4, verticalAlign: "middle" }} />
                Consider flying
              </SectionLabel>
              <div style={{
                padding: 10,
                borderRadius: 10,
                background: "rgba(0,0,0,0.04)",
                border: "1px solid var(--rim)",
              }}>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 6 }}>
                  <Pill tone={flights.advisory.recommended_mode === "fly" ? "must" : "muted"}>
                    Mode: {flights.advisory.recommended_mode}
                  </Pill>
                  {Array.isArray(flights.advisory.typical_one_way_inr) && flights.advisory.typical_one_way_inr[0] && (
                    <Pill tone="muted">
                      ₹{flights.advisory.typical_one_way_inr[0]?.toLocaleString()}–{flights.advisory.typical_one_way_inr[1]?.toLocaleString()} one-way
                    </Pill>
                  )}
                  {(flights.advisory.carrier_hints || []).map((c) => (
                    <Pill key={c} tone="muted">{c}</Pill>
                  ))}
                </div>
                {flights.advisory.book_ahead_note && (
                  <p style={{ fontSize: 11, color: "var(--chrome)", lineHeight: 1.4, marginBottom: 4 }}>
                    {flights.advisory.book_ahead_note}
                  </p>
                )}
                {flights.advisory.rationale && (
                  <p style={{ fontSize: 10.5, color: "var(--silver)", lineHeight: 1.4, fontStyle: "italic" }}>
                    {flights.advisory.rationale}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Train advisory — nearest railhead + typical trains */}
          {trains?.advisory_available && trains.advisory && event.type === "travel" && (
            <div style={{ marginTop: 4 }}>
              <SectionLabel>
                <Train size={10} style={{ marginRight: 4, verticalAlign: "middle" }} />
                By train
              </SectionLabel>
              <div style={{
                padding: 10, borderRadius: 10,
                background: "rgba(0,0,0,0.04)", border: "1px solid var(--rim)",
              }}>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 6 }}>
                  {trains.advisory.nearest_railhead && (
                    <Pill tone="default">Railhead: {trains.advisory.nearest_railhead}</Pill>
                  )}
                  {Array.isArray(trains.advisory.typical_fare_inr) && trains.advisory.typical_fare_inr[0] && (
                    <Pill tone="muted">
                      ₹{trains.advisory.typical_fare_inr[0]?.toLocaleString()}–{trains.advisory.typical_fare_inr[1]?.toLocaleString()}
                    </Pill>
                  )}
                  {trains.advisory.typical_duration && <Pill tone="muted">{trains.advisory.typical_duration}</Pill>}
                </div>
                {(trains.advisory.typical_trains || []).length > 0 && (
                  <p style={{ fontSize: 11, color: "var(--chrome)", lineHeight: 1.4, marginBottom: 4 }}>
                    {trains.advisory.typical_trains.join(" · ")}
                  </p>
                )}
                {trains.advisory.onward_note && (
                  <p style={{ fontSize: 10.5, color: "var(--silver)", lineHeight: 1.4, fontStyle: "italic" }}>
                    {trains.advisory.onward_note}
                  </p>
                )}
                {trains.available && trains.live_trains?.length > 0 && (
                  <div style={{ marginTop: 6, fontSize: 10, color: "var(--silver)" }}>
                    {trains.live_trains.length} live trains from RailRadar
                  </div>
                )}
              </div>
            </div>
          )}
        </GlassPanel>
      </motion.div>
    </AnimatePresence>
  );
}

function SectionLabel({ children, style = {} }) {
  return (
    <div
      style={{
        fontSize: 9.5, fontWeight: 700, letterSpacing: "0.14em",
        color: "var(--silver)", textTransform: "uppercase",
        marginBottom: 4,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
