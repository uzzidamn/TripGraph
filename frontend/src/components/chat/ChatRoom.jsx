import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Sparkles } from "lucide-react";
import { PalmCompass } from "../ui/PalmCompass";

const TRAVEL_QUOTES = [
  { q: "The world is a book, and those who do not travel read only one page.", a: "Augustine of Hippo" },
  { q: "Travel is the only thing you buy that makes you richer.", a: "Anonymous" },
  { q: "Not all those who wander are lost.", a: "J.R.R. Tolkien" },
  { q: "We travel not to escape life, but for life not to escape us.", a: "Anonymous" },
  { q: "Adventure is worthwhile in itself.", a: "Amelia Earhart" },
  { q: "Travel makes one modest. You see what a tiny place you occupy in the world.", a: "Gustave Flaubert" },
  { q: "The journey of a thousand miles begins with a single step.", a: "Lao Tzu" },
  { q: "Life is either a daring adventure or nothing at all.", a: "Helen Keller" },
  { q: "Once a year, go someplace you've never been before.", a: "Dalai Lama" },
  { q: "Wherever you go, go with all your heart.", a: "Confucius" },
  { q: "Take only memories, leave only footprints.", a: "Chief Seattle" },
  { q: "Travel is fatal to prejudice, bigotry, and narrow-mindedness.", a: "Mark Twain" },
  { q: "Jobs fill your pocket, adventures fill your soul.", a: "Jaime Lyn Beatty" },
  { q: "Travel far enough, you meet yourself.", a: "David Mitchell" },
  { q: "I haven't been everywhere, but it's on my list.", a: "Susan Sontag" },
  { q: "The real voyage of discovery consists not in seeking new landscapes, but in having new eyes.", a: "Marcel Proust" },
  { q: "To travel is to live.", a: "Hans Christian Andersen" },
  { q: "Two roads diverged in a wood, and I took the one less traveled by.", a: "Robert Frost" },
  { q: "Travelling — it leaves you speechless, then turns you into a storyteller.", a: "Ibn Battuta" },
  { q: "A ship in harbor is safe, but that is not what ships are built for.", a: "John A. Shedd" },
];

const PREBUILT_TRIPS = [
  {
    label: "Goa monsoon escape",
    icon: "🌴",
    messages: [
      "Looking at a Goa trip from Chandigarh, 5 days",
      "Budget about ₹50k per person",
      "Mix of beach, heritage, and good Goan food",
      "Comfortable hotel, group of 4",
      "Flying preferred — don't want a long drive",
    ],
  },
  {
    label: "Jaipur heritage weekend",
    icon: "🏰",
    messages: [
      "Jaipur weekend from Gurugram, 3 days",
      "Budget ₹15k per person",
      "Heritage sites, palaces, local food",
      "Mid-range hotel, 4 people",
      "Driving down is fine",
    ],
  },
  {
    label: "Manali backpacker",
    icon: "🏔️",
    messages: [
      "Manali trip from Delhi, 4 days on a tight budget",
      "₹10k per person, hostels are fine",
      "Hiking, cafés, Old Manali vibe",
      "2 people, taking overnight bus is OK",
      "Need rough idea of local transport costs too",
    ],
  },
  {
    label: "Kerala backwaters",
    icon: "🛶",
    messages: [
      "Kerala trip — Kochi, Alleppey, Munnar — 6 days",
      "Budget ₹35k per person",
      "Houseboat night is a must, want hill views too",
      "Mid-range hotels, 3 people",
      "Flying from Bangalore",
    ],
  },
];

const FIELD_LABELS = {
  origin: "Where you're travelling from",
  destination: "Where you want to go",
  destination_type: "Type of destination (beach, mountains, city…)",
  budget_per_person: "Budget per person",
  trip_duration: "How many days",
  group_size: "Number of people",
  dates: "Travel dates",
};

export function ChatRoom({ onSubmit, loading, missingFields = [], guardrailMessage = null, duplicateResult = null, onDuplicateAction, initialMessages = [] }) {
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState(initialMessages);
  const [quoteIdx, setQuoteIdx] = useState(() => Math.floor(Math.random() * TRAVEL_QUOTES.length));

  // Rotate quotes every 6 seconds — pauses if the user has started typing
  useEffect(() => {
    if (messages.length > 0 || draft.length > 0) return;
    const timer = setInterval(() => {
      setQuoteIdx((i) => (i + 1) % TRAVEL_QUOTES.length);
    }, 6000);
    return () => clearInterval(timer);
  }, [messages.length, draft.length]);

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

  const currentQuote = TRAVEL_QUOTES[quoteIdx];
  const isEmpty = messages.length === 0 && draft.length === 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Prebuilt trips — top row */}
      <div>
        <div style={{
          fontSize: 9.5, fontWeight: 700, letterSpacing: "0.14em",
          color: "var(--silver)", textTransform: "uppercase",
          textAlign: "center", marginBottom: 10,
        }}>
          Try a prebuilt plan
        </div>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: 8,
        }}>
          {PREBUILT_TRIPS.map(({ label, icon, messages: msgs }) => (
            <motion.button
              key={label}
              whileHover={{ scale: 1.02, y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setMessages(msgs)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "9px 12px",
                borderRadius: 10,
                border: "1px solid var(--rim)",
                background: "rgba(255,255,255,0.6)",
                color: "var(--chrome)",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                fontFamily: "Inter, sans-serif",
                textAlign: "left",
                transition: "background 0.15s, border-color 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.95)";
                e.currentTarget.style.borderColor = "var(--chrome)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.6)";
                e.currentTarget.style.borderColor = "var(--rim)";
              }}
            >
              <span style={{ fontSize: 16 }}>{icon}</span>
              <span style={{ flex: 1 }}>{label}</span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Divider */}
      <div style={{
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <div style={{ flex: 1, height: 1, background: "var(--rim)" }} />
        <span style={{
          fontSize: 9.5, fontWeight: 700, letterSpacing: "0.14em",
          color: "var(--silver)", textTransform: "uppercase",
        }}>
          or tell us your trip
        </span>
        <div style={{ flex: 1, height: 1, background: "var(--rim)" }} />
      </div>

      {/* Chat / input box with rotating quotes as the empty-state */}
      <div style={{
        background: "rgba(255,255,255,0.7)",
        border: "1px solid var(--rim)",
        borderRadius: 16,
        overflow: "hidden",
        boxShadow: "0 4px 14px rgba(20,22,28,0.04)",
      }}>
        {/* Messages list / quote */}
        <div style={{
          minHeight: 170, maxHeight: 240,
          overflowY: "auto",
          padding: "20px 18px",
          display: "flex", flexDirection: "column", gap: 10,
          justifyContent: isEmpty && missingFields.length === 0 ? "center" : "flex-start",
        }}>
          {isEmpty && missingFields.length === 0 ? (
            <AnimatePresence mode="wait">
              <motion.div
                key={quoteIdx}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                style={{
                  display: "flex", flexDirection: "column", alignItems: "center",
                  gap: 8, textAlign: "center", padding: "0 12px",
                }}
              >
                <PalmCompass size={20} color="var(--silver)" />
                <p style={{
                  fontSize: 14, fontWeight: 500, lineHeight: 1.55,
                  color: "var(--platinum)", letterSpacing: "-0.01em",
                  fontStyle: "italic", maxWidth: 380,
                }}>
                  "{currentQuote.q}"
                </p>
                <span style={{
                  fontSize: 10.5, color: "var(--silver)",
                  letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 600,
                }}>
                  — {currentQuote.a}
                </span>
              </motion.div>
            </AnimatePresence>
          ) : (
            <>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  style={{
                    alignSelf: "flex-end",
                    background: "linear-gradient(180deg, #3a3d44, #1d1f25)",
                    color: "#f5f5f7",
                    borderRadius: 14,
                    padding: "8px 14px",
                    fontSize: 12.5,
                    lineHeight: 1.5,
                    maxWidth: "85%",
                    boxShadow: "inset 0 1px 0 rgba(255,255,255,0.12), 0 1px 3px rgba(20,22,28,0.18)",
                  }}
                >
                  {msg}
                </motion.div>
              ))}
              {!duplicateResult && guardrailMessage && (
                <motion.div
                  key="guardrail-bubble"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                  style={{
                    alignSelf: "flex-start",
                    background: "rgba(255,240,240,0.92)",
                    border: "1px solid rgba(220,80,80,0.22)",
                    borderRadius: 14,
                    padding: "10px 14px",
                    fontSize: 12.5,
                    lineHeight: 1.6,
                    maxWidth: "90%",
                    color: "#7a2020",
                    boxShadow: "0 1px 4px rgba(180,40,40,0.08)",
                  }}
                >
                  {guardrailMessage}
                </motion.div>
              )}
              {missingFields.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                  style={{
                    alignSelf: "flex-start",
                    background: "rgba(255,255,255,0.85)",
                    border: "1px solid var(--rim)",
                    borderRadius: 14,
                    padding: "10px 14px",
                    fontSize: 12.5,
                    lineHeight: 1.6,
                    maxWidth: "90%",
                    color: "var(--chrome)",
                    boxShadow: "0 1px 4px rgba(20,22,28,0.07)",
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: 6 }}>
                    I need a few more details to plan your trip:
                  </div>
                  <ul style={{ margin: 0, padding: "0 0 0 16px", display: "flex", flexDirection: "column", gap: 3 }}>
                    {missingFields.map((f) => (
                      <li key={f} style={{ fontSize: 12 }}>
                        {FIELD_LABELS[f] || f}
                      </li>
                    ))}
                  </ul>
                  <div style={{ marginTop: 8, fontSize: 11.5, color: "var(--silver)" }}>
                    Add them above and click <strong>Plan my trip</strong> again.
                  </div>
                </motion.div>
              )}
            </>
          )}
        </div>

        {/* Input row */}
        <div style={{
          padding: "11px 16px",
          borderTop: "1px solid var(--rim)",
          display: "flex", gap: 10, alignItems: "center",
          background: "rgba(255,255,255,0.4)",
        }}>
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Where to? Tell us what you're after…"
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              fontSize: 13.5,
              color: "var(--platinum)",
              fontFamily: "Inter, sans-serif",
              fontWeight: 500,
            }}
          />
          <button
            onClick={() => addMessage(draft)}
            disabled={!draft.trim()}
            style={{
              background: draft.trim() ? "linear-gradient(180deg, #3a3d44, #1d1f25)" : "rgba(0,0,0,0.04)",
              border: "1px solid rgba(0,0,0,0.18)",
              borderRadius: 999,
              cursor: draft.trim() ? "pointer" : "not-allowed",
              color: draft.trim() ? "#f5f5f7" : "var(--silver)",
              width: 32, height: 32,
              display: "grid",
              placeItems: "center",
              transition: "background 0.15s, opacity 0.15s",
            }}
          >
            <Send size={14} />
          </button>
        </div>
      </div>

      {/* Duplicate trip notice — rendered outside scroll area so it's always visible */}
      <AnimatePresence>
        {duplicateResult && (
          <motion.div
            key="duplicate-notice"
            initial={{ opacity: 0, y: 8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.3 }}
            style={{
              background: "rgba(255,248,225,0.97)",
              border: "1px solid rgba(210,155,30,0.35)",
              borderRadius: 14,
              padding: "14px 16px",
              fontSize: 12.5,
              lineHeight: 1.6,
              color: "#5c3d00",
              boxShadow: "0 2px 10px rgba(180,120,0,0.10)",
            }}
          >
            <div style={{ marginBottom: 12 }}>{duplicateResult.response}</div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={() => onDuplicateAction?.("proceed")}
                style={{
                  padding: "8px 20px", borderRadius: 999, fontSize: 12.5, fontWeight: 600,
                  cursor: "pointer", fontFamily: "Inter, sans-serif",
                  background: "linear-gradient(180deg, #3a3d44, #1d1f25)",
                  color: "#f5f5f7", border: "1px solid rgba(0,0,0,0.35)",
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.12), 0 2px 6px rgba(20,22,28,0.18)",
                  transition: "opacity 0.15s",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.opacity = "0.82"; }}
                onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
              >
                Yes, plan it
              </button>
              <button
                onClick={() => onDuplicateAction?.("cancel")}
                style={{
                  padding: "8px 20px", borderRadius: 999, fontSize: 12.5, fontWeight: 600,
                  cursor: "pointer", fontFamily: "Inter, sans-serif",
                  background: "transparent", color: "#5c3d00",
                  border: "1px solid rgba(180,120,0,0.32)",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(180,120,0,0.09)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
              >
                Cancel
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Submit */}
      <motion.button
        whileHover={messages.length > 0 && !loading ? { scale: 1.01 } : {}}
        whileTap={messages.length > 0 && !loading ? { scale: 0.99 } : {}}
        onClick={() => onSubmit(messages)}
        disabled={messages.length === 0 || loading}
        className="btn-primary"
        style={{
          width: "100%",
          padding: "14px 0",
          borderRadius: 13,
          border: "none",
          color: "#f5f5f7",
          fontSize: 13.5,
          fontWeight: 700,
          cursor: messages.length === 0 || loading ? "not-allowed" : "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          fontFamily: "Inter, sans-serif",
          letterSpacing: "0.01em",
          opacity: messages.length === 0 ? 0.55 : 1,
          transition: "opacity 0.2s",
        }}
      >
        {loading ? (
          <>
            <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} />
            Reading the room…
          </>
        ) : (
          <>
            <Sparkles size={14} />
            Plan my trip
          </>
        )}
      </motion.button>
    </div>
  );
}
