/**
 * Silver/aluminum Leaflet map for TripGraph AI.
 *
 * Key features:
 *   - Numbered sequence markers per day with dimming for other days
 *   - Per-segment polylines styled by transport mode (flight/train/cab)
 *   - Cost + time labels on connecting segments between stops
 *   - Pixel tracking for map-anchored popovers (updates on pan/zoom)
 *   - Google Uber-style tiles when available, CartoDB light fallback
 *   - Landing mode: slow east-to-west pan across a blurred world map
 */
import { useEffect, useRef, useState, useCallback } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  Popup,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import { GlassPanel, Pill } from "../ui/Glass";
import { useSelection } from "../../hooks/useSelection";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const TYPE_LABEL = {
  origin:      "Start",
  destination: "Destination",
  waypoint:    "Stop",
  hotel:       "Stay",
  activity:    "Activity",
  travel:      "Transit",
};

function silverIcon({ size = 24, active = false } = {}) {
  const r = size / 2;
  const pinH = size * 1.5;
  const dotR = r * 0.32;
  const stroke = active ? "#0a0c10" : "#2a2d33";
  const fill   = active ? "#1d1f25" : "#3a3d44";
  const svg = encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${pinH}" viewBox="0 0 ${size} ${pinH}">
      <defs>
        <radialGradient id="g" cx="35%" cy="30%">
          <stop offset="0%" stop-color="#ffffff" stop-opacity="0.55"/>
          <stop offset="60%" stop-color="${fill}" stop-opacity="0.96"/>
          <stop offset="100%" stop-color="#0a0c10" stop-opacity="1"/>
        </radialGradient>
      </defs>
      <path fill="url(#g)" stroke="${stroke}" stroke-width="0.9"
        d="M${r} 0C${r * 0.45} 0 0 ${r * 0.45} 0 ${r}c0 ${r * 0.75} ${r} ${pinH - r} ${r} ${pinH - r}s${r}-${pinH - r - r * 0.75} ${r}-${pinH - r}C${size} ${r * 0.45} ${size - r * 0.45} 0 ${r} 0z"/>
      <circle fill="#ffffff" cx="${r}" cy="${r}" r="${dotR * 1.4}"/>
      <circle fill="${active ? '#0a0c10' : '#2a2d33'}" cx="${r}" cy="${r}" r="${dotR * 0.6}"/>
    </svg>`
  );
  return new L.Icon({
    iconUrl:    `data:image/svg+xml,${svg}`,
    iconSize:   [size, pinH],
    iconAnchor: [r, pinH],
    popupAnchor:[0, -pinH + 4],
    className:  active ? "marker-pulse" : "",
  });
}

function seqIcon({ seq = 1, active = false, dimmed = false, cost = null } = {}) {
  const size = active ? 34 : 30;
  const bg = active ? "#0a0c10" : dimmed ? "#dde2eb" : "#2a2d33";
  const text = dimmed ? "#6e7382" : "#ffffff";
  const ring = active ? "#ffffff" : "rgba(255,255,255,0.95)";
  const shadow = active ? "0 6px 18px rgba(20,22,28,0.4)" : "0 3px 10px rgba(20,22,28,0.25)";
  const svg = encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
      <circle cx="${size/2}" cy="${size/2}" r="${size/2 - 2}" fill="${bg}" stroke="${ring}" stroke-width="2.5"/>
      <text x="50%" y="55%" font-family="Inter,system-ui,sans-serif" font-size="${size*0.5}" font-weight="800"
            text-anchor="middle" dominant-baseline="middle" fill="${text}">${seq}</text>
    </svg>`
  );
  const costTag = cost && !dimmed
    ? `<div style="position:absolute;top:${size + 2}px;left:50%;transform:translateX(-50%);
        background:#1d1f25;color:#f5f5f7;font-size:9px;font-weight:700;padding:1px 5px;
        border-radius:4px;white-space:nowrap;font-family:Inter,sans-serif;
        box-shadow:0 1px 4px rgba(0,0,0,0.3)">₹${cost.toLocaleString()}</div>`
    : "";
  return new L.DivIcon({
    html: `<div style="position:relative;filter:drop-shadow(${shadow})"><img src="data:image/svg+xml,${svg}" style="display:block;width:${size}px;height:${size}px" />${costTag}</div>`,
    className: active ? "marker-pulse" : "",
    iconSize: [size, size + (costTag ? 16 : 0)],
    iconAnchor: [size/2, size/2],
    popupAnchor:[0, -size/2 - 4],
  });
}

/** Segment cost/time label placed at the midpoint of a polyline. */
function segmentLabel(minutes, cost, mode) {
  const parts = [];
  if (minutes) parts.push(`${minutes} min`);
  if (cost) parts.push(`₹${cost.toLocaleString()}`);
  if (!parts.length) return null;

  const modeIcon = mode === "flight" ? "✈" : mode === "train" ? "🚆" : mode === "cab" ? "🚕" : "→";

  return new L.DivIcon({
    html: `<div style="background:rgba(255,255,255,0.92);backdrop-filter:blur(8px);
      border:1px solid rgba(0,0,0,0.12);border-radius:6px;padding:2px 7px;
      font-size:9px;font-weight:600;color:#2a2d33;white-space:nowrap;
      font-family:Inter,sans-serif;box-shadow:0 1px 4px rgba(0,0,0,0.12);
      display:flex;align-items:center;gap:3px">
      <span>${modeIcon}</span><span>${parts.join(" · ")}</span></div>`,
    className: "segment-label",
    iconSize: [0, 0],
    iconAnchor: [0, 0],
  });
}

/** Tracks active marker pixel position on map move/zoom for anchored popovers. */
function PixelTracker({ mapPoints }) {
  const map = useMap();
  const { activePointId, activeLatLng, setAnchorPx } = useSelection();

  const updatePx = useCallback(() => {
    if (!activeLatLng || !activePointId) return;
    try {
      const px = map.latLngToContainerPoint([activeLatLng[0], activeLatLng[1]]);
      setAnchorPx({ x: px.x, y: px.y });
    } catch {}
  }, [map, activeLatLng, activePointId, setAnchorPx]);

  useMapEvents({
    move: updatePx,
    zoom: updatePx,
    moveend: updatePx,
    zoomend: updatePx,
  });

  useEffect(() => { updatePx(); }, [updatePx]);

  return null;
}

function MapController({ mapPoints, interactive, panning, activePointId, fitAllTick, selectedDay }) {
  const map = useMap();

  useEffect(() => {
    if (panning) map.setZoom(3);
  }, [panning, map]);

  useEffect(() => {
    if (interactive) {
      map.scrollWheelZoom.enable();
      map.dragging.enable();
      map.touchZoom.enable();
      map.doubleClickZoom.enable();
      map.keyboard.enable();
    } else {
      map.scrollWheelZoom.disable();
      map.doubleClickZoom.disable();
      if (panning) map.dragging.disable();
    }
  }, [interactive, panning, map]);

  useEffect(() => {
    if (!interactive || !mapPoints?.length) return;
    let pts = mapPoints;
    if (selectedDay !== null) {
      const dayPts = mapPoints.filter(p => p.day === selectedDay);
      if (dayPts.length > 0) {
        const nonOrigin = dayPts.filter(p => p.type !== "origin");
        pts = nonOrigin.length > 0 ? nonOrigin : dayPts;
      }
    }
    const bounds = L.latLngBounds(pts.map((p) => [p.lat, p.lng]));
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [120, 120], maxZoom: 12 });
    }
  }, [mapPoints, interactive, selectedDay, map]);

  useEffect(() => {
    if (!interactive || !mapPoints?.length || !activePointId) return;
    const target = mapPoints.find(
      (p) => (p.id || `${p.type}:${p.label}`) === activePointId
    );
    if (target) {
      map.flyTo([target.lat, target.lng], Math.max(map.getZoom(), 10), {
        duration: 0.8,
        easeLinearity: 0.4,
      });
    }
  }, [activePointId, mapPoints, interactive, map]);

  useEffect(() => {
    if (!interactive || !mapPoints?.length || fitAllTick === 0) return;
    const bounds = L.latLngBounds(mapPoints.map((p) => [p.lat, p.lng]));
    if (bounds.isValid()) {
      map.flyToBounds(bounds, { padding: [120, 120], maxZoom: 12, duration: 0.6 });
    }
  }, [fitAllTick, mapPoints, interactive, map]);

  useEffect(() => {
    if (!panning) return;
    let raf;
    const start = performance.now();
    const periodMs = 360000;
    const startCenter = map.getCenter();
    const startLng = startCenter.lng;
    const tick = (t) => {
      const elapsed = (t - start) % periodMs;
      const lng = startLng - (elapsed / periodMs) * 360;
      const lat = 22 + Math.sin(elapsed / 90000) * 8;
      map.setView([lat, lng], map.getZoom(), { animate: false });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [panning, map]);

  return null;
}

export function MapView({
  mapPoints = [],
  routePolyline = null,
  interactive = false,
  panning = false,
  engine = "classic",
  onEngineChange,
  fitAllTick = 0,
  selectedDay = null,
  transportMode = null,
  timeline = [],
  costBreakdown = null,
}) {
  const { activePointId, setActivePointId } = useSelection();
  const defaultCenter = [22, 78];
  const hasPoints = mapPoints.length > 0;

  const [googleTiles, setGoogleTiles] = useState(null);
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8001";
  useEffect(() => {
    let cancelled = false;
    fetch(`${baseUrl}/api/maptiles-session`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (!cancelled && d?.available) setGoogleTiles(d); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [baseUrl]);

  const useGoogle = engine !== "classic" && !!googleTiles?.tile_url_template;

  const center = hasPoints
    ? [
        mapPoints.reduce((s, p) => s + p.lat, 0) / mapPoints.length,
        mapPoints.reduce((s, p) => s + p.lng, 0) / mapPoints.length,
      ]
    : defaultCenter;

  const isFlight = transportMode === "flight";
  const originPt = mapPoints.find((p) => p.type === "origin");
  const destPt = mapPoints.find((p) => p.type === "destination") || mapPoints.find((p) => p.type === "hotel");

  const polylinePositions =
    isFlight && originPt && destPt
      ? [[originPt.lat, originPt.lng], [destPt.lat, destPt.lng]]
      : routePolyline && routePolyline.length > 1
      ? routePolyline
      : mapPoints
          .filter((p) => ["origin", "waypoint", "destination"].includes(p.type))
          .map((p) => [p.lat, p.lng]);

  // Build a cost lookup from timeline: event point_id → cost
  const costByPointId = {};
  for (const ev of timeline) {
    if (ev.point_id && ev.cost) costByPointId[ev.point_id] = ev.cost;
  }

  // Build segment info: for each consecutive pair of stops in a day,
  // compute midpoint + travel time/cost for the label
  const buildSegments = () => {
    const byDay = new Map();
    for (const p of mapPoints) {
      if (p.seq == null || p.day == null) continue;
      if (!byDay.has(p.day)) byDay.set(p.day, []);
      byDay.get(p.day).push(p);
    }
    const days = selectedDay ? [selectedDay] : [...byDay.keys()];
    const segments = [];
    const midpoints = [];

    for (const d of days) {
      const pts = (byDay.get(d) || []).slice().sort((a, b) => (a.seq || 0) - (b.seq || 0));
      if (pts.length < 2) continue;

      for (let i = 0; i < pts.length - 1; i++) {
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const mode = (p2.mode || "").toLowerCase();

        let pathOptions = { color: "#2a2d33", weight: 2, opacity: 0.55, dashArray: "6 6" };
        if (mode === "flight") {
          pathOptions = { color: "var(--silver)", weight: 2.5, opacity: 0.8, dashArray: "4 6" };
        } else if (mode === "train" || mode === "rail") {
          pathOptions = { color: "#1d1f25", weight: 3.5, opacity: 0.8, dashArray: "8 4" };
        } else if (mode === "cab" || mode === "drive" || mode === "car") {
          pathOptions = { color: "#3a3d44", weight: 2.2, opacity: 0.7, dashArray: "6 4" };
        }

        segments.push({ key: `day-${d}-seg-${i}`, positions: [[p1.lat, p1.lng], [p2.lat, p2.lng]], pathOptions });

        // Find the travel event between these stops to get cost/time
        const travelEv = timeline.find(ev =>
          ev.day === d && ev.type === "travel" && ev.seq != null &&
          ev.seq > (p1.seq || 0) && ev.seq <= (p2.seq || 999)
        ) || timeline.find(ev =>
          ev.day === d && ev.type === "travel" &&
          ((ev.title || "").toLowerCase().includes((p2.label || "").toLowerCase().split(" ")[0]))
        );

        const tMin = travelEv?.duration_minutes || null;
        const tCost = travelEv?.cost || null;
        const tMode = travelEv?.transport_mode || mode || null;

        // Compute midpoint for the label
        const midLat = (p1.lat + p2.lat) / 2;
        const midLng = (p1.lng + p2.lng) / 2;

        // Only show labels for non-trivial segments
        if (tMin || tCost) {
          const icon = segmentLabel(tMin, tCost, tMode);
          if (icon) {
            midpoints.push({ key: `mid-${d}-${i}`, lat: midLat, lng: midLng, icon });
          }
        }
      }
    }
    return { segments, midpoints };
  };

  const { segments: daySegments, midpoints: segmentMidpoints } = interactive ? buildSegments() : { segments: [], midpoints: [] };

  return (
    <div className={`map-fullscreen ${useGoogle ? "map-google" : ""}`}>
      <MapContainer
        center={center}
        zoom={hasPoints ? 7 : 5}
        minZoom={2}
        worldCopyJump
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
        zoomControl={interactive}
        attributionControl={false}
      >
        <MapController
          mapPoints={mapPoints}
          interactive={interactive}
          panning={panning}
          activePointId={activePointId}
          fitAllTick={fitAllTick}
          selectedDay={selectedDay}
        />

        {interactive && <PixelTracker mapPoints={mapPoints} />}

        {useGoogle ? (
          <TileLayer
            key="google"
            url={googleTiles.tile_url_template}
            attribution='&copy; Google'
            maxZoom={20}
            tileSize={256}
          />
        ) : (
          <TileLayer
            key="carto"
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
            maxZoom={19}
          />
        )}

        {/* Main route polyline */}
        {polylinePositions.length > 1 && (
          <>
            <Polyline
              positions={polylinePositions}
              pathOptions={
                isFlight
                  ? { color: "#2a2d33", weight: 6, opacity: 0.05, dashArray: "10 10" }
                  : { color: "#2a2d33", weight: 10, opacity: 0.08 }
              }
            />
            <Polyline
              positions={polylinePositions}
              pathOptions={
                isFlight
                  ? { color: "var(--silver)", weight: 2, opacity: 0.8, dashArray: "6 6", className: "route-polyline" }
                  : { color: "#1d1f25", weight: 2.4, opacity: 0.88, className: "route-polyline" }
              }
            />
          </>
        )}

        {/* Per-day sequence polylines with transport mode styling */}
        {daySegments.map(s => (
          <Polyline key={s.key} positions={s.positions} pathOptions={s.pathOptions} />
        ))}

        {/* Segment cost/time labels at midpoints */}
        {segmentMidpoints.map(m => (
          <Marker key={m.key} position={[m.lat, m.lng]} icon={m.icon} interactive={false} />
        ))}

        {/* Markers */}
        {mapPoints.map((pt, i) => {
          const id = pt.id || `${pt.type}:${pt.label}`;
          const active = id === activePointId;
          const isSeq = pt.seq != null;
          const dimmed = selectedDay != null && pt.day != null && pt.day !== selectedDay;
          const cost = costByPointId[id] || null;
          const icon = isSeq
            ? seqIcon({ seq: pt.seq, active, dimmed, cost: dimmed ? null : cost })
            : silverIcon({ active });
          return (
            <Marker
              key={id || i}
              position={[pt.lat, pt.lng]}
              icon={icon}
              opacity={dimmed ? 0.45 : 1}
              eventHandlers={{
                click: () => {
                  setActivePointId(id, [pt.lat, pt.lng]);
                },
              }}
            >
              <Popup>
                <div style={{ fontFamily: "Inter, sans-serif", minWidth: 160 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <div
                      style={{
                        width: 10, height: 10, borderRadius: 999,
                        background: "var(--chrome)",
                        boxShadow: "0 0 6px rgba(0,0,0,0.18)",
                      }}
                    />
                    <span style={{ fontWeight: 700, fontSize: 13, color: "var(--platinum)" }}>
                      {pt.label}
                    </span>
                  </div>
                  <Pill tone="muted">{TYPE_LABEL[pt.type] || pt.type}</Pill>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Floating cost summary on map (bottom-right, above zoom controls) */}
      {interactive && costBreakdown && costBreakdown.total > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: 16,
            right: 16,
            zIndex: 1000,
            pointerEvents: "auto",
          }}
        >
          <GlassPanel strong style={{
            padding: "10px 14px",
            borderRadius: 12,
            display: "flex",
            flexDirection: "column",
            gap: 6,
            minWidth: 150,
          }}>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase" }}>
              Cost per person
            </div>
            <div style={{ fontSize: 20, fontWeight: 800, color: "var(--platinum)", lineHeight: 1 }}>
              ₹{(costBreakdown.total || 0).toLocaleString()}
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 3 }}>
              {costBreakdown.transport > 0 && (
                <span style={{ fontSize: 9, color: "var(--silver)" }}>🚗 ₹{costBreakdown.transport.toLocaleString()}</span>
              )}
              {costBreakdown.hotel > 0 && (
                <span style={{ fontSize: 9, color: "var(--silver)" }}>🏨 ₹{costBreakdown.hotel.toLocaleString()}</span>
              )}
              {costBreakdown.activities > 0 && (
                <span style={{ fontSize: 9, color: "var(--silver)" }}>⚡ ₹{costBreakdown.activities.toLocaleString()}</span>
              )}
              {costBreakdown.food > 0 && (
                <span style={{ fontSize: 9, color: "var(--silver)" }}>🍽 ₹{costBreakdown.food.toLocaleString()}</span>
              )}
            </div>
          </GlassPanel>
        </div>
      )}

      {/* Engine toggle pill */}
      {!panning && (
        <div style={{ position: "absolute", top: 14, right: 16, zIndex: 1000, pointerEvents: "auto" }}>
          <GlassPanel style={{ display: "inline-flex", alignItems: "center", gap: 2, padding: 4, borderRadius: 999 }}>
            {[
              { id: "classic", label: "Classic" },
              { id: "uber",    label: "Uber", disabled: !googleTiles },
            ].map((opt) => (
              <button
                key={opt.id}
                type="button"
                disabled={opt.disabled}
                onClick={() => !opt.disabled && onEngineChange && onEngineChange(opt.id)}
                title={opt.disabled ? "Google Maps tiles unavailable (check key)" : "Google Maps — Uber-style"}
                style={{
                  padding: "5px 12px",
                  borderRadius: 999,
                  background: engine === opt.id
                    ? "linear-gradient(180deg, #3a3d44, #1d1f25)"
                    : "transparent",
                  color: engine === opt.id ? "#f5f5f7" : opt.disabled ? "var(--silver)" : "var(--chrome)",
                  fontSize: 10.5,
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  cursor: opt.disabled ? "not-allowed" : "pointer",
                  border: "none",
                  opacity: opt.disabled ? 0.55 : 1,
                  transition: "background 0.2s",
                }}
              >
                {opt.label}
              </button>
            ))}
          </GlassPanel>
        </div>
      )}
    </div>
  );
}
