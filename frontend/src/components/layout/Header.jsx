import { Map, RefreshCw } from "lucide-react";

export function Header({ step, onReset }) {
  const steps = [
    { id: "chat", label: "Chat" },
    { id: "preferences", label: "Preferences" },
    { id: "itinerary", label: "Itinerary" },
  ];

  return (
    <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-md border-b border-border shadow-sm">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Map size={20} className="text-primary" />
          <span className="font-semibold text-text-primary tracking-tight">
            TripGraph <span className="text-primary">AI</span>
          </span>
        </div>

        <nav className="flex items-center gap-1">
          {steps.map(({ id, label }, idx) => {
            const stepIdx = steps.findIndex((s) => s.id === step);
            const done = idx < stepIdx;
            const active = id === step;
            return (
              <div key={id} className="flex items-center gap-1">
                {idx > 0 && (
                  <div className={`h-px w-6 ${done ? "bg-primary" : "bg-border"}`} />
                )}
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full transition-colors ${
                    active
                      ? "bg-primary text-white"
                      : done
                      ? "text-primary"
                      : "text-text-muted"
                  }`}
                >
                  {label}
                </span>
              </div>
            );
          })}
        </nav>

        <button
          onClick={onReset}
          className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors"
        >
          <RefreshCw size={14} />
          Start over
        </button>
      </div>
    </header>
  );
}
