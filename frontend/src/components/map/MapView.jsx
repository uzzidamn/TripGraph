import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";

// Fix default Leaflet marker icons broken by bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const TYPE_META = {
  origin:      { color: "#4f46e5", label: "Origin" },
  destination: { color: "#0891b2", label: "Destination" },
  waypoint:    { color: "#d97706", label: "Waypoint" },
  hotel:       { color: "#059669", label: "Hotel" },
  activity:    { color: "#dc2626", label: "Activity" },
};

function colorIcon(color) {
  const svg = encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="40" viewBox="0 0 28 40">
      <filter id="s">
        <feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.3"/>
      </filter>
      <path filter="url(#s)" fill="${color}" d="M14 0C6.3 0 0 6.3 0 14c0 10.5 14 26 14 26S28 24.5 28 14C28 6.3 21.7 0 14 0z"/>
      <circle fill="white" cx="14" cy="14" r="6"/>
    </svg>`
  );
  return new L.Icon({
    iconUrl:    `data:image/svg+xml,${svg}`,
    iconSize:   [28, 40],
    iconAnchor: [14, 40],
    popupAnchor:[0, -42],
  });
}

function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (!points.length) return;
    if (points.length === 1) {
      map.setView([points[0].lat, points[0].lng], 10);
      return;
    }
    const bounds = L.latLngBounds(points.map((p) => [p.lat, p.lng]));
    map.fitBounds(bounds, { padding: [48, 48], maxZoom: 12 });
  }, [map, points]);
  return null;
}

export function MapView({ mapPoints }) {
  if (!mapPoints?.length) return null;

  // Use first point as initial center — FitBounds adjusts it after mount
  const initial = [mapPoints[0].lat, mapPoints[0].lng];

  const routeLine = mapPoints
    .filter((p) => ["origin", "waypoint", "destination"].includes(p.type))
    .map((p) => [p.lat, p.lng]);

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        height: 360,
        boxShadow: "0 4px 24px rgba(0,0,0,0.18), 0 1px 4px rgba(0,0,0,0.12)",
        border: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      <MapContainer
        center={initial}
        zoom={5}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
        zoomControl={true}
      >
        <FitBounds points={mapPoints} />
        {/* Voyager — warm, colourful, highly readable travel-style tiles */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
          maxZoom={19}
        />

        {routeLine.length > 1 && (
          <Polyline
            positions={routeLine}
            pathOptions={{
              color: "#4f46e5",
              weight: 4,
              dashArray: "8 5",
              opacity: 0.85,
              lineCap: "round",
              lineJoin: "round",
            }}
          />
        )}

        {mapPoints.map((pt, i) => {
          const meta = TYPE_META[pt.type] ?? { color: "#6b7280", label: pt.type };
          return (
            <Marker
              key={i}
              position={[pt.lat, pt.lng]}
              icon={colorIcon(meta.color)}
            >
              <Popup>
                <div style={{ fontFamily: "Inter, system-ui, sans-serif", minWidth: 120 }}>
                  <div style={{
                    display: "inline-block",
                    background: meta.color,
                    color: "#fff",
                    fontSize: 10,
                    fontWeight: 600,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    padding: "2px 7px",
                    borderRadius: 99,
                    marginBottom: 4,
                  }}>
                    {meta.label}
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 14, color: "#1e293b" }}>
                    {pt.label}
                  </div>
                  {pt.detail && (
                    <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>
                      {pt.detail}
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
