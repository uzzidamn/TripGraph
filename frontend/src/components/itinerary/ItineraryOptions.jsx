import { motion } from "framer-motion";
import { MapPin, Star, TrendingUp } from "lucide-react";

function ScoreBar({ label, value, max = 30 }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-text-muted">
        <span>{label}</span>
        <span className="text-text-primary">{value}</span>
      </div>
      <div className="h-1.5 bg-border rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ItineraryOptions({ itinerary, alternatives, scoreBreakdown }) {
  if (!itinerary) return null;

  const { route, hotel, transport, activities, total_cost_per_person, destination } = itinerary;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-text-primary uppercase tracking-wide">
        Recommended plan
      </h3>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-surface border border-primary/40 rounded-xl p-5 space-y-4 card-hover"
      >
        <div className="flex items-start justify-between">
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5">
              <MapPin size={14} className="text-primary" />
              <span className="font-semibold text-text-primary">
                {route?.origin} → {destination ?? route?.destination}
              </span>
            </div>
            <p className="text-xs text-text-muted">
              {route?.distance_km} km · {route?.destination_type}
            </p>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold text-primary">
              ₹{total_cost_per_person?.toLocaleString()}
            </p>
            <p className="text-xs text-text-muted">per person</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-surface-hover rounded-lg p-3 space-y-0.5">
            <p className="text-text-muted">Hotel</p>
            <p className="text-text-primary font-medium">{hotel?.name}</p>
            <p className="text-text-muted">₹{hotel?.price_per_night?.toLocaleString()}/night</p>
          </div>
          <div className="bg-surface-hover rounded-lg p-3 space-y-0.5">
            <p className="text-text-muted">Transport</p>
            <p className="text-text-primary font-medium capitalize">
              {transport?.mode?.replace(/_/g, " ")}
            </p>
            <p className="text-text-muted capitalize">{transport?.tier}</p>
          </div>
        </div>

        {activities?.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs text-text-muted uppercase tracking-wide font-medium">Activities</p>
            {activities.map((a, i) => (
              <div key={i} className="flex justify-between text-xs">
                <span className="text-text-primary">{a.name}</span>
                <span className="text-text-muted">
                  {a.cost_per_person === 0 ? "Free" : `₹${a.cost_per_person?.toLocaleString()}`}
                </span>
              </div>
            ))}
          </div>
        )}

        {scoreBreakdown && (
          <div className="pt-3 border-t border-border space-y-2">
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp size={13} className="text-accent" />
              <span className="text-xs text-text-muted uppercase tracking-wide font-medium">
                Score: {scoreBreakdown.final_score}/100
              </span>
            </div>
            <ScoreBar label="Preference match" value={scoreBreakdown.preference_match} max={30} />
            <ScoreBar label="Comfort" value={scoreBreakdown.comfort} max={20} />
            <ScoreBar label="Fatigue" value={scoreBreakdown.fatigue} max={15} />
          </div>
        )}
      </motion.div>

      {alternatives?.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-medium text-text-muted uppercase tracking-wide">
            Alternatives
          </h3>
          {alternatives.map((alt, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * (i + 1) }}
              className="bg-surface border border-border rounded-xl p-4 flex items-center justify-between card-hover"
            >
              <div>
                <p className="text-sm font-medium text-text-primary">
                  {alt.destination ?? alt.route?.destination}
                </p>
                <p className="text-xs text-text-muted">
                  {alt.route?.distance_km} km · {alt.hotel?.name}
                </p>
              </div>
              <p className="text-sm font-semibold text-accent">
                ₹{alt.total_cost_per_person?.toLocaleString()}
              </p>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
