import { motion } from "framer-motion";
import { Car, Bed, Zap, Utensils, Coffee, Clock } from "lucide-react";

const TYPE_META = {
  travel:   { icon: Car,      color: "text-accent",   bg: "bg-accent/10"   },
  hotel:    { icon: Bed,      color: "text-primary",  bg: "bg-primary/10"  },
  activity: { icon: Zap,      color: "text-warning",  bg: "bg-warning/10"  },
  meal:     { icon: Utensils, color: "text-success",  bg: "bg-success/10"  },
  rest:     { icon: Coffee,   color: "text-text-muted", bg: "bg-surface-hover" },
};

function TimelineEvent({ event, idx }) {
  const meta = TYPE_META[event.type] ?? TYPE_META.rest;
  const Icon = meta.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: idx * 0.04 }}
      className="flex gap-3 items-start"
    >
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${meta.bg}`}>
          <Icon size={14} className={meta.color} />
        </div>
        <div className="w-px flex-1 bg-border mt-1 min-h-[16px]" />
      </div>
      <div className="pb-3 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-sm font-medium text-text-primary leading-tight">
              {event.title}
            </p>
            <p className="text-xs text-text-muted mt-0.5">
              {event.start_time} – {event.end_time}
            </p>
          </div>
          {event.cost !== undefined && (
            <span className="text-xs text-text-muted flex-shrink-0">
              {event.cost === 0 ? "Free" : `₹${event.cost.toLocaleString()}`}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export function ItineraryTimeline({ timeline }) {
  if (!timeline?.length) return null;

  const byDay = timeline.reduce((acc, ev) => {
    const d = ev.day ?? 1;
    (acc[d] = acc[d] ?? []).push(ev);
    return acc;
  }, {});

  return (
    <div className="space-y-5">
      {Object.entries(byDay).map(([day, events]) => (
        <div key={day}>
          <div className="flex items-center gap-2 mb-3">
            <Clock size={13} className="text-primary" />
            <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide">
              Day {day}
            </h4>
          </div>
          <div>
            {events.map((ev, i) => (
              <TimelineEvent key={i} event={ev} idx={i} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
