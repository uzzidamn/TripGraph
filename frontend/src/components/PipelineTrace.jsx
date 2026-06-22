import React, { useState } from "react";

const NODES = [
  { key: "guardrail",            label: "Guardrail",            icon: "🛡️" },
  { key: "chat_parser",          label: "Chat Parser",          icon: "💬" },
  { key: "memory_agent",         label: "Memory",               icon: "🧠" },
  { key: "constraint_validator", label: "Validator",            icon: "✅" },
  { key: "route_retriever",      label: "Route Retriever",      icon: "🗺️" },
  { key: "hotel_retriever",      label: "Hotels",               icon: "🏨" },
  { key: "transport_retriever",  label: "Transport",            icon: "🚗" },
  { key: "activity_retriever",   label: "Activities",           icon: "🧗" },
  { key: "food_retriever",       label: "Food",                 icon: "🍜" },
  { key: "waypoint_retriever",   label: "Waypoints",            icon: "📍" },
  { key: "planner_orchestrator", label: "Planner",              icon: "📋" },
  { key: "explainer",            label: "Explainer",            icon: "📖" },
  { key: "memory_updater",       label: "Memory Update",        icon: "💾" },
];

const STATUS_COLORS = {
  done:    "bg-green-500",
  running: "bg-yellow-400 animate-pulse",
  waiting: "bg-gray-300",
  error:   "bg-red-500",
};

export default function PipelineTrace({ nodeStatus = {} }) {
  const [open, setOpen] = useState(false);

  const anyActive = Object.keys(nodeStatus).length > 0;
  if (!anyActive) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={() => setOpen(o => !o)}
        className="bg-slate-800 text-white text-xs px-3 py-1.5 rounded-full shadow-lg hover:bg-slate-700 transition"
      >
        {open ? "Hide" : "Show"} Pipeline Trace
      </button>

      {open && (
        <div className="mt-2 bg-slate-900 text-white rounded-xl shadow-2xl p-4 w-72">
          <p className="text-xs text-slate-400 mb-3 font-semibold tracking-wide uppercase">
            14-Node Pipeline
          </p>
          <div className="space-y-1.5">
            {NODES.map(n => {
              const status = nodeStatus[n.key] ?? "waiting";
              return (
                <div key={n.key} className="flex items-center gap-2 text-sm">
                  <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${STATUS_COLORS[status] ?? STATUS_COLORS.waiting}`} />
                  <span className="text-base leading-none">{n.icon}</span>
                  <span className={status === "done" ? "text-slate-300" : status === "running" ? "text-yellow-300" : "text-slate-500"}>
                    {n.label}
                  </span>
                  {status === "running" && (
                    <span className="ml-auto text-yellow-400 text-xs animate-pulse">●</span>
                  )}
                  {status === "done" && (
                    <span className="ml-auto text-green-400 text-xs">✓</span>
                  )}
                  {status === "error" && (
                    <span className="ml-auto text-red-400 text-xs">✗</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
