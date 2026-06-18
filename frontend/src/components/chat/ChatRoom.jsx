import { useState } from "react";
import { motion } from "framer-motion";
import { Send, MessageCircle, Loader2 } from "lucide-react";

const PLACEHOLDER_MESSAGES = [
  "Guys Rishikesh this weekend? I can do ₹15k max",
  "Yes! But I can't do night driving please",
  "Need rafting for sure, and good cafes",
  "Back by Monday morning sharp",
];

const EXAMPLE_CHATS = [
  { label: "Rishikesh weekend", messages: PLACEHOLDER_MESSAGES },
  {
    label: "Jaipur heritage",
    messages: [
      "Jaipur trip next week, budget ₹12k per head",
      "Heritage sites only please, no adventure",
      "Comfortable hotel, not budget",
      "4 people, back by Sunday night",
    ],
  },
];

export function ChatRoom({ onSubmit, loading }) {
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState([]);

  const addMessage = (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setMessages((prev) => [...prev, trimmed]);
    setDraft("");
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      addMessage(draft);
    }
  };

  const loadExample = (msgs) => setMessages(msgs);

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="text-center space-y-1">
        <h1 className="text-2xl font-bold text-text-primary">
          Plan your group trip
        </h1>
        <p className="text-text-muted text-sm">
          Paste your WhatsApp conversation or type naturally — the AI will extract your preferences
        </p>
      </div>

      <div className="flex gap-2 justify-center flex-wrap">
        {EXAMPLE_CHATS.map(({ label, messages: msgs }) => (
          <button
            key={label}
            onClick={() => loadExample(msgs)}
            className="text-xs px-3 py-1.5 rounded-full border border-border text-text-muted hover:text-text-primary hover:border-primary transition-colors"
          >
            Try: {label}
          </button>
        ))}
      </div>

      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center gap-2">
          <MessageCircle size={15} className="text-accent" />
          <span className="text-xs text-text-muted font-medium uppercase tracking-wide">
            Group Chat
          </span>
          {messages.length > 0 && (
            <span className="ml-auto text-xs text-text-muted">
              {messages.length} message{messages.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        <div className="min-h-[160px] max-h-72 overflow-y-auto p-4 space-y-2">
          {messages.length === 0 ? (
            <p className="text-text-muted text-sm text-center mt-8">
              Add messages or try an example above
            </p>
          ) : (
            messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex gap-2 items-start"
              >
                <div className="w-6 h-6 rounded-full bg-primary/20 flex-shrink-0 flex items-center justify-center text-xs text-primary font-medium">
                  {String.fromCharCode(65 + (i % 4))}
                </div>
                <div className="bg-surface-hover rounded-lg px-3 py-2 text-sm text-text-primary max-w-[85%]">
                  {msg}
                </div>
              </motion.div>
            ))
          )}
        </div>

        <div className="px-4 py-3 border-t border-border flex gap-2">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Type a message and press Enter..."
            className="flex-1 bg-transparent text-sm text-text-primary placeholder-text-muted outline-none"
          />
          <button
            onClick={() => addMessage(draft)}
            disabled={!draft.trim()}
            className="text-primary disabled:opacity-40 hover:text-primary-hover transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>

      <button
        onClick={() => onSubmit(messages)}
        disabled={messages.length === 0 || loading}
        className="w-full py-3 rounded-xl bg-primary hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Analysing conversation…
          </>
        ) : (
          "Extract preferences →"
        )}
      </button>
    </div>
  );
}
