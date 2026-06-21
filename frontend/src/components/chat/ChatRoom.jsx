import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

const EXAMPLES = [
  {
    label: "Rishikesh weekend",
    text: "Guys Rishikesh this weekend?\nI can do ₹15k max\nBut no night driving please\nNeed rafting for sure, and good cafes\nBack by Monday morning",
  },
  {
    label: "Jaipur heritage",
    text: "Jaipur trip next week, budget ₹12k per head\nHeritage sites only, no adventure\nComfortable hotel please\n4 people, back by Sunday night",
  },
  {
    label: "Goa beach trip",
    text: "Goa trip for 5 days!\nFlight from Mumbai\nLuxury beach resort\n6 of us, budget ₹30k each\nWant water sports and nightlife",
  },
];

export function ChatRoom({ onSubmit, loading }) {
  const [text, setText] = useState("");

  function handleSubmit() {
    const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
    if (lines.length === 0) return;
    onSubmit(lines);
  }

  function handleKey(e) {
    if (e.key === "Enter" && e.metaKey) handleSubmit();
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="text-center space-y-1">
        <h1 className="text-2xl font-bold text-text-primary">Plan your group trip</h1>
        <p className="text-text-muted text-sm">
          Paste your WhatsApp chat or describe your trip — the AI extracts your preferences
        </p>
      </div>

      <div className="flex gap-2 justify-center flex-wrap">
        {EXAMPLES.map(({ label, text: t }) => (
          <button
            key={label}
            onClick={() => setText(t)}
            className="text-xs px-3 py-1.5 rounded-full border border-border text-text-muted hover:text-text-primary hover:border-primary transition-colors"
          >
            Try: {label}
          </button>
        ))}
      </div>

      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={handleKey}
        rows={8}
        placeholder={"Paste your group chat here, or type naturally…\n\nE.g.\n  planning a trip to Amsterdam next month\n  4 of us, budget €800 each\n  want museums and nightlife\n  flying from London"}
        className="w-full bg-surface border border-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary resize-none leading-relaxed"
      />

      <button
        onClick={handleSubmit}
        disabled={!text.trim() || loading}
        className="w-full py-3 rounded-xl bg-primary hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Analysing…
          </>
        ) : (
          <>
            <Sparkles size={16} />
            Plan my trip →
          </>
        )}
      </button>
    </div>
  );
}
