import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Clock, Loader2, ChevronDown, ChevronUp } from "lucide-react";

export function DelaySimulator({ onSimulate, loading, delayResult }) {
  const [minutes, setMinutes] = useState(90);
  const [showChanges, setShowChanges] = useState(true);

  return (
    <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
      <div className="flex items-center gap-2">
        <AlertTriangle size={15} className="text-warning" />
        <h3 className="text-sm font-semibold text-text-primary">Delay simulator</h3>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-text-muted">Departure delay</span>
          <span className="text-text-primary font-medium">{minutes} min</span>
        </div>
        <input
          type="range"
          min={15}
          max={300}
          step={15}
          value={minutes}
          onChange={(e) => setMinutes(Number(e.target.value))}
        />
        <div className="flex justify-between text-xs text-text-muted">
          <span>15 min</span>
          <span>5 hours</span>
        </div>
      </div>

      <button
        onClick={() => onSimulate(minutes)}
        disabled={loading}
        className="w-full py-2.5 rounded-lg bg-warning/10 border border-warning/30 hover:border-warning text-warning text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-40"
      >
        {loading ? (
          <>
            <Loader2 size={14} className="animate-spin" />
            Replanning…
          </>
        ) : (
          <>
            <Clock size={14} />
            Simulate {minutes}-min delay
          </>
        )}
      </button>

      <AnimatePresence>
        {delayResult && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="border-t border-border pt-4 space-y-3">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setShowChanges((p) => !p)}
              >
                <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
                  Changes ({delayResult.changes?.length ?? 0})
                </span>
                {showChanges ? (
                  <ChevronUp size={14} className="text-text-muted" />
                ) : (
                  <ChevronDown size={14} className="text-text-muted" />
                )}
              </div>

              {showChanges && delayResult.changes?.map((c, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-start gap-2 text-xs text-text-muted"
                >
                  <span className="text-warning mt-0.5">•</span>
                  {c}
                </motion.div>
              ))}

              {delayResult.explanation && (
                <p className="text-xs text-text-muted bg-surface-hover rounded-lg p-3 leading-relaxed">
                  {delayResult.explanation}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
