import { motion } from "framer-motion";
import { DollarSign } from "lucide-react";

const LABELS = {
  transport:     "Transport",
  hotel:         "Hotel",
  activities:    "Activities",
  food:          "Food",
  miscellaneous: "Misc",
};

const COLORS = ["#6c5ce7", "#00cec9", "#fdcb6e", "#00b894", "#e17055"];

export function CostBreakdown({ costBreakdown, currencySymbol = "{currencySymbol}" }) {
  if (!costBreakdown) return null;

  const { budget_limit, total, ...items } = costBreakdown;
  const entries = Object.entries(LABELS).filter(([k]) => items[k] != null);
  const usagePct = budget_limit ? Math.min(100, (total / budget_limit) * 100) : null;

  return (
    <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
      <div className="flex items-center gap-2">
        <DollarSign size={15} className="text-primary" />
        <h3 className="text-sm font-semibold text-text-primary">Cost breakdown</h3>
        <span className="ml-auto text-xs text-text-muted">per person</span>
      </div>

      <div className="space-y-2.5">
        {entries.map(([key, label], i) => {
          const val = items[key];
          const pct = total > 0 ? (val / total) * 100 : 0;
          return (
            <div key={key} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">{label}</span>
                <span className="text-text-primary">{currencySymbol}{val.toLocaleString()}</span>
              </div>
              <div className="h-1.5 bg-border rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.6, delay: i * 0.08 }}
                  className="h-full rounded-full"
                  style={{ background: COLORS[i % COLORS.length] }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-border pt-3">
        <div className="flex justify-between font-semibold">
          <span className="text-sm text-text-primary">Total</span>
          <span className="text-base text-primary">{currencySymbol}{total?.toLocaleString()}</span>
        </div>

        {budget_limit && (
          <div className="mt-2 space-y-1">
            <div className="flex justify-between text-xs text-text-muted">
              <span>Budget utilization</span>
              <span className={usagePct > 90 ? "text-warning" : "text-success"}>
                {usagePct?.toFixed(0)}% of {currencySymbol}{budget_limit.toLocaleString()}
              </span>
            </div>
            <div className="h-1.5 bg-border rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${usagePct}%` }}
                transition={{ duration: 0.7 }}
                className={`h-full rounded-full ${usagePct > 90 ? "bg-warning" : "bg-success"}`}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
