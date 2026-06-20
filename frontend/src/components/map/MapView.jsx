import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet";
import L from "leaflet";

// Fix bundler-broken default icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const TYPE_COLORS = {
  origin:      "#7c6df7",
  destination: "#00cec9",
  waypoint:    "#fdcb6e",
  hotel:       "#00b894",
  activity:    "#e17055",
};

const TYPE_LABELS = {
  origin:      "Starting Point",
  destination: "Destination",
  waypoint:    "Stop",
  hotel:       "Stay",
  activity:    "Activity",
};

function colorIcon(color, size = 26) {
  const r = size / 2;
  const pinH = size * 1.5;
  const dotR = r * 0.38;
  const svg = encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${pinH}" viewBox="0 0 ${size} ${pinH}">
      <defs>
        <filter id="g" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="2.5" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <radialGradient id="rg" cx="38%" cy="30%">
          <stop offset="0%" stop-color="white" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <path filter="url(#g)" fill="${color}"
        d="M${r} 0C${r * 0.45} 0 0 ${r * 0.45} 0 ${r}c0 ${r * 0.75} ${r} ${pinH - r} ${r} ${pinH - r}s${r}-${pinH - r - r * 0.75} ${r}-${pinH - r}C${size} ${r * 0.45} ${size - r * 0.45} 0 ${r} 0z"/>
      <circle fill="white" cx="${r}" cy="${r}" r="${dotR * 1.1}"/>
      <circle fill="${color}" cx="${r}" cy="${r}" r="${dotR * 0.55}"/>
      <ellipse fill="url(#rg)" cx="${r * 0.75}" cy="${r * 0.7}" rx="${r * 0.55}" ry="${r * 0.4}"/>
    </svg>`
  );
  return new L.Icon({
    iconUrl:    `data:image/svg+xml,${svg}`,
    iconSize:   [size, pinH],
    iconAnchor: [r, pinH],
    popupAnchor:[0, -pinH + 4],
  });
}

/** Reactively enables/disables scroll-wheel zoom and fits map bounds */
function MapController({ mapPoints, interactive }) {
  const map = useMap();

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
    }
  }, [interactive, map]);

  useEffect(() => {
    if (mapPoints && mapPoints.length > 0) {
      const bounds = L.latLngBounds(mapPoints.map((p) => [p.lat, p.lng]));
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [100, 100], maxZoom: 13 });
      }
    }
  }, [mapPoints, map]);

  return null;
}

/**
 * Full-screen map component.
 *
 * Props:
 *   mapPoints  – array of { lat, lng, label, type }
 *   interactive – boolean — enables scroll-zoom / double-click when true
 *   onMarkerClick – optional callback(point) when a marker is clicked
 */
export function MapView({ mapPoints, interactive = false, onMarkerClick }) {
  const defaultCenter = [28.6139, 77.209];
  const hasPoints = Array.isArray(mapPoints) && mapPoints.length > 0;

  const center = hasPoints
    ? [
        mapPoints.reduce((s, p) => s + p.lat, 0) / mapPoints.length,
        mapPoints.reduce((s, p) => s + p.lng, 0) / mapPoints.length,
      ]
    : defaultCenter;

  /** Route line uses origin → waypoints → destination only */
  const routeLine = hasPoints
    ? mapPoints
        .filter((p) => ["origin", "waypoint", "destination"].includes(p.type))
        .map((p) => [p.lat, p.lng])
    : [];

  return (
    <div className="map-fullscreen">
      <MapContainer
        center={center}
        zoom={hasPoints ? 7 : 5}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
        zoomControl={interactive}
        attributionControl={false}
      >
        <MapController mapPoints={mapPoints} interactive={interactive} />

        {/* Dark CartoDB tiles — no black corners since bg matches */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          maxZoom={19}
        />

        {/* Attribution in bottom-right */}
        {/* Zoom control rendered by MapController via interactive prop */}

        {/* Route — glow shadow + sharp line */}
        {routeLine.length > 1 && (
          <>
            <Polyline
              positions={routeLine}
              pathOptions={{
                color: "#7c6df7",
                weight: 12,
                opacity: 0.12,
              }}
            />
            <Polyline
              positions={routeLine}
              pathOptions={{
                color: "#7c6df7",
                weight: 2.5,
                opacity: 0.85,
                dashArray: "10 7",
              }}
            />
          </>
        )}

        {/* Markers */}
        {hasPoints &&
          mapPoints.map((pt, i) => {
            const color = TYPE_COLORS[pt.type] ?? "#7c6df7";
            return (
              <Marker
                key={i}
                position={[pt.lat, pt.lng]}
                icon={colorIcon(color)}
                eventHandlers={{
                  click: () => onMarkerClick && onMarkerClick(pt),
                }}
              >
                <Popup>
                  <div
                    style={{
                      fontFamily: "Inter, system-ui, sans-serif",
                      minWidth: "160px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        marginBottom: "6px",
                      }}
                    >
                      <div
                        style={{
                          width: "10px",
                          height: "10px",
                          borderRadius: "50%",
                          background: color,
                          flexShrink: 0,
                          boxShadow: `0 0 6px ${color}`,
                        }}
                      />
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: "13px",
                          color: "#e2e8f0",
                          lineHeight: 1.2,
                        }}
                      >
                        {pt.label}
                      </span>
                    </div>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 600,
                        letterSpacing: "0.08em",
                        color: color,
                        textTransform: "uppercase",
                        padding: "2px 8px",
                        background: `${color}22`,
                        borderRadius: "999px",
                      }}
                    >
                      {TYPE_LABELS[pt.type] ?? pt.type}
                    </span>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>

      {/* Zoom controls rendered manually when interactive */}
      {interactive && (
        <div
          style={{
            position: "absolute",
            bottom: "100px",
            right: "20px",
            zIndex: 1000,
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          {/* Zoom controls are already part of Leaflet - they appear via zoomControl */}
        </div>
      )}
    </div>
  );
}
