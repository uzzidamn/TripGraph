/**
 * Silver/aluminum Leaflet map for TripGraph AI.
 *
 * Behaviours:
 *   - Defaults to Google "Uber-style" grey tiles when available; CartoDB light fallback
 *   - Numbered seq markers per day, dimmed on other days
 *   - Real ORS road polylines per segment (when segment_polylines present)
 *   - Flight segments dashed straight lines
 *   - Day click → animated zoom IN to that day's bounds (not fit-all)
 *   - Marker click → sets active pin + lat/lng for popover anchoring
 *   - Pixel tracker updates anchorPx on map move/zoom
 */
import { useEffect, useState, useCallback, Fragment } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
// eslint-disable-next-line no-unused-vars
import { GlassPanel } from "../ui/Glass";
import { useSelection } from "../../hooks/useSelection";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});


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
    iconUrl: `data:image/svg+xml,${svg}`,
    iconSize: [size, pinH],
    iconAnchor: [r, pinH],
    popupAnchor: [0, -pinH + 4],
    className: active ? "marker-pulse" : "",
  });
}

function seqIcon({ seq = 1, active = false, dimmed = false } = {}) {
  const size = active ? 36 : 30;
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
  return new L.DivIcon({
    html: `<div style="filter:drop-shadow(${shadow})"><img src="data:image/svg+xml,${svg}" style="display:block;width:${size}px;height:${size}px" /></div>`,
    className: active ? "marker-pulse" : "",
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor:[0, -size/2 - 4],
  });
}

function segmentLabel(minutes, cost, mode) {
  const parts = [];
  if (minutes) parts.push(`${minutes} min`);
  if (cost) parts.push(`₹${cost.toLocaleString()}`);
  if (!parts.length) return null;
  const modeIcon = mode === "flight" ? "✈" : mode === "train" ? "🚆" : mode === "cab" ? "🚕" : "→";
  return new L.DivIcon({
    html: `<div style="background:rgba(255,255,255,0.95);backdrop-filter:blur(8px);
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

function PixelTracker() {
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
    move: updatePx, zoom: updatePx, moveend: updatePx, zoomend: updatePx,
  });

  useEffect(() => { updatePx(); }, [updatePx]);

  return null;
}

function MapController({ mapPoints, interactive, panning, activePointId, fitAllTick, selectedDay }) {
  const map = useMap();

  useEffect(() => { if (panning) map.setZoom(3); }, [panning, map]);

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

  // ── Day click → zoom IN to that day's stops, smooth mac-like flyToBounds ──
  useEffect(() => {
    if (!interactive || !mapPoints?.length || selectedDay == null) return;
    const dayPts = mapPoints.filter((p) => p.day === selectedDay);
    if (dayPts.length === 0) return;
    const nonOrigin = dayPts.filter((p) => p.type !== "origin");
    const pts = nonOrigin.length > 0 ? nonOrigin : dayPts;
    const bounds = L.latLngBounds(pts.map((p) => [p.lat, p.lng]));
    if (!bounds.isValid()) return;
    // flyToBounds gives a smooth eased animation
    map.flyToBounds(bounds, {
      padding: [120, 120],
      maxZoom: 14,
      duration: 0.9,
      easeLinearity: 0.25,
    });
  }, [selectedDay, mapPoints, interactive, map]);

  // Initial fit to all on first load
  useEffect(() => {
    if (!interactive || !mapPoints?.length) return;
    const bounds = L.latLngBounds(mapPoints.map((p) => [p.lat, p.lng]));
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [120, 120], maxZoom: 12, animate: false });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interactive]);

  // Marker fly-to
  useEffect(() => {
    if (!interactive || !mapPoints?.length || !activePointId) return;
    const target = mapPoints.find(
      (p) => (p.id || `${p.type}:${p.label}`) === activePointId
    );
    if (target) {
      map.flyTo([target.lat, target.lng], Math.max(map.getZoom(), 12), {
        duration: 0.7, easeLinearity: 0.3,
      });
    }
  }, [activePointId, mapPoints, interactive, map]);

  // Explicit "fit all" trigger
  useEffect(() => {
    if (!interactive || !mapPoints?.length || fitAllTick === 0) return;
    const bounds = L.latLngBounds(mapPoints.map((p) => [p.lat, p.lng]));
    if (bounds.isValid()) {
      map.flyToBounds(bounds, { padding: [120, 120], maxZoom: 12, duration: 0.6 });
    }
  }, [fitAllTick, mapPoints, interactive, map]);

  // Landing pan
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
  fitAllTick = 0,
  selectedDay = null,
  onSelectDay = null,
  transportMode = null,
  timeline = [],
  segmentPolylines = [],
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

  // Always prefer Google (uber-style) when available, no UI toggle
  const useGoogle = !!googleTiles?.tile_url_template;

  const center = hasPoints
    ? [
        mapPoints.reduce((s, p) => s + p.lat, 0) / mapPoints.length,
        mapPoints.reduce((s, p) => s + p.lng, 0) / mapPoints.length,
      ]
    : defaultCenter;

  const isFlight = transportMode === "flight";

  // For flight: the dashed long-haul line goes airport → airport.
  // Find the two "travel" events whose titles contain "airport" — the architect
  // creates these on Day 1 (departure) and last day (return). Falls back to
  // origin → destination city pins for non-flight road trips.
  const airportPts = mapPoints
    .filter((p) => p.day === 1 && /airport/i.test(p.label || ""))
    .sort((a, b) => (a.seq || 0) - (b.seq || 0));
  const departureAirport = airportPts[0];
  const arrivalAirport = airportPts[airportPts.length - 1];

  const mainPolyline =
    isFlight && departureAirport && arrivalAirport && departureAirport !== arrivalAirport
      ? [[departureAirport.lat, departureAirport.lng], [arrivalAirport.lat, arrivalAirport.lng]]
      : !isFlight && routePolyline && routePolyline.length > 1
      ? routePolyline
      : null;

  // Cost lookup by point_id
  const costByPointId = {};
  for (const ev of timeline) {
    if (ev.point_id && ev.cost) costByPointId[ev.point_id] = ev.cost;
  }

  // Build segments from segment_polylines (preferred — real ORS road geometry)
  // Falls back to straight lines for segments without a polyline
  const buildSegmentRenderables = () => {
    const segmentsByDay = new Map();
    for (const sp of segmentPolylines || []) {
      if (selectedDay != null && sp.day !== selectedDay) continue;
      const key = `${sp.day}-${sp.from_seq}-${sp.to_seq}`;
      segmentsByDay.set(key, sp);
    }

    // Build straight-line fallbacks for pairs not in segment_polylines
    const byDay = new Map();
    for (const p of mapPoints) {
      if (p.seq == null || p.day == null) continue;
      if (!byDay.has(p.day)) byDay.set(p.day, []);
      byDay.get(p.day).push(p);
    }
    const days = selectedDay != null ? [selectedDay] : [...byDay.keys()];
    const fallbackSegments = [];
    const midpoints = [];

    for (const d of days) {
      const pts = (byDay.get(d) || []).slice().sort((a, b) => (a.seq || 0) - (b.seq || 0));
      if (pts.length < 2) continue;

      for (let i = 0; i < pts.length - 1; i++) {
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const mode = (p2.mode || "").toLowerCase();
        const key = `${d}-${p1.seq}-${p2.seq}`;
        const hasRealPolyline = segmentsByDay.has(key);

        // Midpoint segment labels intentionally removed — they cluttered the map
        // and the same info (cost + duration) lives on the event pin / popover.

        if (!hasRealPolyline) {
          // Fallback straight line
          let pathOptions = { color: "#2a2d33", weight: 2, opacity: 0.55, dashArray: "6 6" };
          if (mode === "flight" || mode === "air") {
            pathOptions = { color: "var(--silver)", weight: 2.5, opacity: 0.8, dashArray: "4 6" };
          } else if (mode === "train" || mode === "rail") {
            pathOptions = { color: "#1d1f25", weight: 3.5, opacity: 0.8, dashArray: "8 4" };
          }
          fallbackSegments.push({
            key: `fb-${key}`,
            positions: [[p1.lat, p1.lng], [p2.lat, p2.lng]],
            pathOptions,
          });
        }
      }
    }

    // Render real polylines from segmentPolylines
    const realSegments = [...segmentsByDay.values()].map((sp) => ({
      key: `real-${sp.day}-${sp.from_seq}-${sp.to_seq}`,
      positions: sp.polyline,
      // Uber-style: dark line with subtle halo
      mode: sp.mode,
    }));

    return { realSegments, fallbackSegments, midpoints };
  };

  const { realSegments, fallbackSegments, midpoints } = interactive
    ? buildSegmentRenderables()
    : { realSegments: [], fallbackSegments: [], midpoints: [] };

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

        {interactive && <PixelTracker />}

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
            attribution='&copy; OSM &copy; CARTO'
            maxZoom={19}
          />
        )}

        {/* Main inter-city polyline (origin → destination) */}
        {mainPolyline && mainPolyline.length > 1 && (
          <>
            <Polyline
              positions={mainPolyline}
              pathOptions={
                isFlight
                  ? { color: "#2a2d33", weight: 6, opacity: 0.05, dashArray: "10 10" }
                  : { color: "#2a2d33", weight: 10, opacity: 0.08 }
              }
            />
            <Polyline
              positions={mainPolyline}
              pathOptions={
                isFlight
                  ? { color: "var(--silver)", weight: 2, opacity: 0.85, dashArray: "6 6", className: "route-polyline" }
                  : { color: "#1d1f25", weight: 2.6, opacity: 0.9, className: "route-polyline" }
              }
            />
          </>
        )}

        {/* Real ORS road polylines (Uber-style: halo + dark line) */}
        {realSegments.map((s) => (
          <Fragment key={s.key}>
            <Polyline
              positions={s.positions}
              pathOptions={{ color: "#2a2d33", weight: 7, opacity: 0.12 }}
            />
            <Polyline
              positions={s.positions}
              pathOptions={{
                color: s.mode === "cab" ? "#1d1f25" : "#3a3d44",
                weight: 3.5, opacity: 0.92,
                className: "route-polyline",
              }}
            />
          </Fragment>
        ))}

        {/* Fallback straight-line segments */}
        {fallbackSegments.map((s) => (
          <Polyline key={s.key} positions={s.positions} pathOptions={s.pathOptions} />
        ))}


        {/* Markers */}
        {mapPoints.map((pt, i) => {
          const id = pt.id || `${pt.type}:${pt.label}`;
          const active = id === activePointId;
          const isSeq = pt.seq != null;
          const dimmed = selectedDay != null && pt.day != null && pt.day !== selectedDay;
          const cost = costByPointId[id] || null;
          const icon = isSeq
            ? seqIcon({ seq: pt.seq, active, dimmed })
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
                  if (onSelectDay && pt.day != null && pt.day !== selectedDay) {
                    onSelectDay(pt.day);
                  }
                },
              }}
            />
          );
        })}
      </MapContainer>
    </div>
  );
}
