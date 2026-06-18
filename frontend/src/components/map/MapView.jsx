import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";

// Fix default Leaflet marker icons broken by bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const TYPE_COLORS = {
  origin:      "#6c5ce7",
  destination: "#00cec9",
  waypoint:    "#fdcb6e",
  hotel:       "#00b894",
  activity:    "#e17055",
};

function colorIcon(color) {
  const svg = encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="36" viewBox="0 0 24 36">
      <path fill="${color}" d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z"/>
      <circle fill="white" cx="12" cy="12" r="5"/>
    </svg>`
  );
  return new L.Icon({
    iconUrl:    `data:image/svg+xml,${svg}`,
    iconSize:   [24, 36],
    iconAnchor: [12, 36],
    popupAnchor:[0, -36],
  });
}

export function MapView({ mapPoints }) {
  if (!mapPoints?.length) return null;

  const center = [
    mapPoints.reduce((s, p) => s + p.lat, 0) / mapPoints.length,
    mapPoints.reduce((s, p) => s + p.lng, 0) / mapPoints.length,
  ];

  const routeLine = mapPoints
    .filter((p) => ["origin", "waypoint", "destination"].includes(p.type))
    .map((p) => [p.lat, p.lng]);

  return (
    <div className="rounded-xl overflow-hidden border border-border" style={{ height: 340 }}>
      <MapContainer
        center={center}
        zoom={8}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
        />
        {routeLine.length > 1 && (
          <Polyline
            positions={routeLine}
            pathOptions={{ color: "#6c5ce7", weight: 3, dashArray: "6 4", opacity: 0.8 }}
          />
        )}
        {mapPoints.map((pt, i) => (
          <Marker
            key={i}
            position={[pt.lat, pt.lng]}
            icon={colorIcon(TYPE_COLORS[pt.type] ?? "#8b8fa3")}
          >
            <Popup>
              <strong>{pt.label}</strong>
              <br />
              <span style={{ textTransform: "capitalize" }}>{pt.type}</span>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
