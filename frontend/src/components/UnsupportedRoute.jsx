import { motion } from "framer-motion";
import { MapPin, ArrowRight, ArrowLeft, Navigation } from "lucide-react";

export default function UnsupportedRoute({ unsupportedRoute, suggestedRoutes = [], onSelectRoute, onBack }) {
  if (!unsupportedRoute) return null;

  const { origin, destination } = unsupportedRoute;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ display: "flex", flexDirection: "column", gap: "20px" }}
    >
      <div style={{ textAlign: "center" }}>
        <div style={{ width:"44px",height:"44px",borderRadius:"12px",background:"rgba(253,203,110,0.15)",border:"1px solid rgba(253,203,110,0.35)",display:"flex",alignItems:"center",justifyContent:"center",margin:"0 auto 14px" }}>
          <Navigation size={20} style={{ color: "#fdcb6e" }} />
        </div>
        <h2 style={{ fontSize:"18px",fontWeight:800,color:"var(--platinum)",letterSpacing:"-0.02em",marginBottom:"8px" }}>
          Route not in catalog
        </h2>
        <p style={{ fontSize:"12px",color:"var(--silver)",lineHeight:1.6,maxWidth:"360px",margin:"0 auto 6px" }}>
          This route is currently not supported. We are constantly striving to add all routes possible.
        </p>
        <p style={{ fontSize:"11px",color:"rgba(253,203,110,0.7)",fontStyle:"italic" }}>
          {origin && destination
            ? `${origin} → ${destination} is not yet in our catalog.`
            : origin
            ? `No departures from ${origin} yet.`
            : "That route is not available yet."}
        </p>
      </div>

      {suggestedRoutes.length > 0 ? (
        <div>
          <div style={{ fontSize:"10px",fontWeight:700,color:"var(--silver)",textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:"10px",textAlign:"center" }}>
            Meanwhile, here are the best alternatives you have
          </div>
          <div style={{ display:"grid",gridTemplateColumns:"repeat(2, 1fr)",gap:"8px" }}>
            {suggestedRoutes.slice(0, 4).map((route, i) => (
              <motion.button
                key={route.route_id ?? `${route.origin}-${route.destination}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                onClick={() => onSelectRoute && onSelectRoute(route)}
                style={{ background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.1)",borderRadius:"10px",padding:"12px",textAlign:"left",cursor:"pointer",fontFamily:"Inter, sans-serif" }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor="rgba(0,184,148,0.4)"; e.currentTarget.style.background="rgba(0,184,148,0.07)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor="rgba(255,255,255,0.1)"; e.currentTarget.style.background="rgba(255,255,255,0.04)"; }}
              >
                <div style={{ display:"flex",alignItems:"center",gap:"5px",marginBottom:"4px" }}>
                  <MapPin size={10} style={{ color:"#00b894",flexShrink:0 }} />
                  <span style={{ fontSize:"12px",fontWeight:700,color:"var(--platinum)" }}>{route.origin}</span>
                  <ArrowRight size={10} style={{ color:"var(--silver)" }} />
                  <span style={{ fontSize:"12px",fontWeight:700,color:"#00b894" }}>{route.destination}</span>
                </div>
                <div style={{ display:"flex",gap:"6px",flexWrap:"wrap" }}>
                  {route.destination_type && (
                    <span style={{ fontSize:"9px",color:"var(--silver)",background:"rgba(255,255,255,0.06)",borderRadius:"4px",padding:"1px 5px",textTransform:"capitalize" }}>
                      {route.destination_type}
                    </span>
                  )}
                  {route.distance_km && (
                    <span style={{ fontSize:"9px",color:"var(--silver)" }}>{route.distance_km} km</span>
                  )}
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      ) : (
        <p style={{ textAlign:"center",fontSize:"12px",color:"var(--silver)" }}>
          No alternative routes available right now.
        </p>
      )}

      <button
        onClick={onBack}
        style={{ background:"none",border:"1px solid rgba(255,255,255,0.12)",borderRadius:"9px",color:"var(--silver)",fontSize:"11px",fontWeight:600,padding:"10px 0",cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",gap:"6px",fontFamily:"Inter, sans-serif" }}
      >
        <ArrowLeft size={12} /> Back to chat
      </button>
    </motion.div>
  );
}
