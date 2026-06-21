/**
 * RefineQuestions — renders 4 LLM-tailored follow-up questions (yes/no toggles
 * or checkbox grids) and collects answers into a single object keyed by question id.
 *
 * Used as the "refine" step, sitting between "preferences" and "itinerary".
 */
import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Sparkles, ChevronRight, SkipForward } from "lucide-react";
import { GlassPanel, MetalText, MetalButton, GhostButton, Pill } from "../ui/Glass";

function BooleanToggle({ value, onChange }) {
  return (
    <div
      style={{
        display: "inline-flex",
        background: "rgba(255,255,255,0.04)",
        border: "1px solid var(--rim)",
        borderRadius: 999,
        padding: 3,
      }}
    >
      {[{ k: true, label: "Yes" }, { k: false, label: "No" }].map(({ k, label }) => (
        <button
          key={String(k)}
          onClick={() => onChange(k)}
          style={{
            padding: "5px 16px",
            borderRadius: 999,
            border: "none",
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            background: value === k
              ? "linear-gradient(180deg, rgba(207,214,224,0.95), rgba(154,163,178,0.78))"
              : "transparent",
            color: value === k ? "var(--ink)" : "var(--chrome)",
            cursor: "pointer",
            transition: "background 0.18s",
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function CheckboxGrid({ options = [], value = [], onChange }) {
  const set = new Set(value);
  const toggle = (opt) => {
    const next = new Set(set);
    if (next.has(opt)) next.delete(opt);
    else next.add(opt);
    onChange([...next]);
  };
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
      {options.map((opt) => {
        const selected = set.has(opt);
        return (
          <button
            key={opt}
            onClick={() => toggle(opt)}
            style={{
              padding: "6px 12px",
              borderRadius: 999,
              fontSize: 11,
              fontWeight: 600,
              border: `1px solid ${selected ? "rgba(255,255,255,0.5)" : "var(--rim)"}`,
              background: selected
                ? "linear-gradient(180deg, rgba(207,214,224,0.85), rgba(154,163,178,0.7))"
                : "rgba(255,255,255,0.03)",
              color: selected ? "var(--ink)" : "var(--chrome)",
              cursor: "pointer",
              transition: "background 0.18s, border-color 0.18s",
            }}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

export function RefineQuestions({ questions = [], onSubmit, onSkip, loading }) {
  // Seed answers with each question's `default`.
  const initial = useMemo(() => {
    const init = {};
    for (const q of questions) {
      init[q.id] = q.default;
    }
    return init;
  }, [questions]);
  const [answers, setAnswers] = useState(initial);

  const setAns = (id, val) => setAnswers((p) => ({ ...p, [id]: val }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      style={{ display: "flex", flexDirection: "column", gap: 18 }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <Sparkles size={16} style={{ color: "var(--chrome)" }} />
        <MetalText as="h2" style={{ fontSize: 22, fontWeight: 700 }}>
          A few quick refinements
        </MetalText>
      </div>
      <p style={{ fontSize: 12.5, color: "var(--silver)", marginTop: -8 }}>
        Four short questions that meaningfully shape your plan. Defaults are pre-selected — skip
        to take them as-is.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {questions.map((q, i) => (
          <GlassPanel key={q.id || i} style={{ padding: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 13.5, fontWeight: 600, color: "var(--platinum)", marginBottom: 4 }}>
                  {q.prompt}
                </p>
                {q.why_it_matters && (
                  <p style={{ fontSize: 10.5, color: "var(--silver)", fontStyle: "italic" }}>
                    {q.why_it_matters}
                  </p>
                )}
              </div>
              <Pill tone="muted">#{i + 1}</Pill>
            </div>
            <div style={{ marginTop: 10 }}>
              {q.kind === "boolean" ? (
                <BooleanToggle value={answers[q.id]} onChange={(v) => setAns(q.id, v)} />
              ) : (
                <CheckboxGrid
                  options={q.options || []}
                  value={Array.isArray(answers[q.id]) ? answers[q.id] : []}
                  onChange={(v) => setAns(q.id, v)}
                />
              )}
            </div>
          </GlassPanel>
        ))}
      </div>

      <div style={{ display: "flex", gap: 10, alignItems: "center", justifyContent: "flex-end", paddingTop: 4 }}>
        <GhostButton onClick={onSkip} disabled={loading}>
          <SkipForward size={12} style={{ marginRight: 6, verticalAlign: "middle" }} />
          Skip refinements
        </GhostButton>
        <MetalButton onClick={() => onSubmit(answers)} disabled={loading}>
          {loading ? "Generating…" : "Generate trip"}
          <ChevronRight size={14} style={{ marginLeft: 6, verticalAlign: "middle" }} />
        </MetalButton>
      </div>
    </motion.div>
  );
}
