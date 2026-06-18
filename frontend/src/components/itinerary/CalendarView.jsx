import { motion } from "framer-motion";

const COLORS = {
  travel:   "bg-accent/20   border-accent/40   text-accent",
  hotel:    "bg-primary/20  border-primary/40  text-primary",
  activity: "bg-warning/20  border-warning/40  text-warning",
  meal:     "bg-success/20  border-success/40  text-success",
  rest:     "bg-border       border-border       text-text-muted",
};

function timeToMinutes(t) {
  if (!t) return 0;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + (m || 0);
}

const DAY_START = 6 * 60;
const DAY_END   = 23 * 60;
const TOTAL_MINS = DAY_END - DAY_START;

export function CalendarView({ timeline }) {
  if (!timeline?.length) return null;

  const byDay = timeline.reduce((acc, ev) => {
    const d = ev.day ?? 1;
    (acc[d] = acc[d] ?? []).push(ev);
    return acc;
  }, {});

  const hourMarks = Array.from({ length: 8 }, (_, i) => 6 + i * 2.5);

  return (
    <div className="space-y-4 overflow-x-auto">
      {Object.entries(byDay).map(([day, events]) => (
        <div key={day}>
          <p className="text-xs font-medium text-text-muted mb-2">Day {day}</p>
          <div className="relative bg-surface border border-border rounded-xl h-24 overflow-hidden">
            {hourMarks.map((h) => (
              <div
                key={h}
                className="absolute top-0 h-full border-l border-border/40"
                style={{ left: `${((h * 60 - DAY_START) / TOTAL_MINS) * 100}%` }}
              >
                <span className="absolute bottom-1 left-1 text-[10px] text-text-muted">
                  {String(Math.floor(h)).padStart(2, "0")}:00
                </span>
              </div>
            ))}

            {events.map((ev, i) => {
              const start = Math.max(timeToMinutes(ev.start_time), DAY_START);
              const end   = Math.min(timeToMinutes(ev.end_time),   DAY_END);
              const left  = ((start - DAY_START) / TOTAL_MINS) * 100;
              const width = Math.max(((end - start) / TOTAL_MINS) * 100, 1.5);
              const cls   = COLORS[ev.type] ?? COLORS.rest;

              return (
                <motion.div
                  key={i}
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ delay: i * 0.04, origin: "left" }}
                  title={`${ev.title}\n${ev.start_time} – ${ev.end_time}`}
                  className={`absolute top-3 h-10 rounded border text-[10px] font-medium flex items-center px-1.5 overflow-hidden cursor-default select-none ${cls}`}
                  style={{ left: `${left}%`, width: `${width}%` }}
                >
                  <span className="truncate">{ev.title}</span>
                </motion.div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
