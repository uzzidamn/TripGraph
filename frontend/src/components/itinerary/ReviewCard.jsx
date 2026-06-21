/**
 * ReviewCard — surfaces the final AI review of the itinerary.
 *
 * A second-pass LLM agent sanity-checks the plan (timing feasibility, mode
 * sense, cost sanity, constraint satisfaction) and returns a verdict + notes.
 * Rendered as a collapsible floating glass card with a clear "AI agent" disclaimer.
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, AlertTriangle, ChevronDown, Sparkles } from "lucide-react";
import { GlassPanel, Pill } from "../ui/Glass";

const VERDICT_META = {
  looks_good:      { label: "Looks good",      tone: "must",    icon: ShieldCheck },
  minor_issues:    { label: "Minor issues",    tone: "warning", icon: AlertTriangle },
  needs_attention: { label: "Needs attention", tone: "warning", icon: AlertTriangle },
};

const SEVERITY_DOT = { high: "#c0392b", medium: "#b8862f", low: "#6e7382" };

export function ReviewCard({ review }) {
  const [open, setOpen] = useState(true);
  if (!review) return null;

  const meta = VERDICT_META[review.verdict] || VERDICT_META.minor_issues;
  const Icon = meta.icon;
  const notes = review.notes || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      style={{
        position: "absolute",
        bottom: 120,
        left: "50%",
        transform: "translateX(-50%)",
        width: "min(560px, calc(100% - 380px))",
        zIndex: 36,
        pointerEvents: "auto",
      }}
    >
      <GlassPanel strong style={{ padding: "12px 16px" }}>
        <div
          style={{ display: "flex", alignItems: "center", gap: 10, cursor: notes.length ? "pointer" : "default" }}
          onClick={() => notes.length && setOpen((v) => !v)}
        >
          <div style={{
            width: 26, height: 26, borderRadius: 8,
            background: "rgba(0,0,0,0.05)", border: "1px solid var(--rim)",
            display: "grid", placeItems: "center", flexShrink: 0,
          }}>
            <Icon size={14} style={{ color: "var(--chrome)" }} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 9.5, fontWeight: 700, letterSpacing: "0.12em", color: "var(--silver)", textTransform: "uppercase" }}>
                <Sparkles size={9} style={{ marginRight: 4, verticalAlign: "middle" }} />
                AI Review
              </span>
              <Pill tone={meta.tone}>{meta.label}</Pill>
            </div>
            <p style={{ fontSize: 11.5, color: "var(--chrome)", lineHeight: 1.45, marginTop: 3 }}>
              {review.summary}
            </p>
          </div>
          {notes.length > 0 && (
            <ChevronDown
              size={16}
              style={{ color: "var(--silver)", transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s", flexShrink: 0 }}
            />
          )}
        </div>

        <AnimatePresence>
          {open && notes.length > 0 && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              style={{ overflow: "hidden" }}
            >
              <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
                {notes.map((n, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                    <span style={{
                      width: 7, height: 7, borderRadius: 999, marginTop: 5, flexShrink: 0,
                      background: SEVERITY_DOT[n.severity] || SEVERITY_DOT.low,
                    }} />
                    <div style={{ minWidth: 0 }}>
                      <p style={{ fontSize: 11.5, color: "var(--platinum)", fontWeight: 600, lineHeight: 1.4 }}>
                        {n.issue}
                      </p>
                      {n.recommendation && (
                        <p style={{ fontSize: 10.5, color: "var(--silver)", lineHeight: 1.4, marginTop: 2 }}>
                          → {n.recommendation}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <p style={{ fontSize: 9.5, color: "var(--silver)", marginTop: 10, fontStyle: "italic", opacity: 0.8 }}>
          {review.disclaimer || "Reviewed by an AI agent — verify critical details before booking."}
        </p>
      </GlassPanel>
    </motion.div>
  );
}
