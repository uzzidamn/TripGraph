import { useState } from "react";
import { motion } from "framer-motion";
import { Send, MessageCircle, Loader2, Navigation } from "lucide-react";

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

const AVATARS = ["A", "B", "C", "D"];

const AVATAR_COLORS = [
  "rgba(124,109,247,0.3)",
  "rgba(0,206,201,0.3)",
  "rgba(253,203,110,0.3)",
  "rgba(0,184,148,0.3)",
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

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Hero heading */}
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "12px",
          }}
        >
          <div
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #6c5ce7, #00cec9)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Navigation size={18} style={{ color: "white" }} />
          </div>
        </div>
        <h1
          style={{
            fontSize: "24px",
            fontWeight: 800,
            color: "#e2e8f0",
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            marginBottom: "6px",
          }}
        >
          Plan your group trip
        </h1>
        <p style={{ fontSize: "13px", color: "#64748b", lineHeight: 1.5 }}>
          Paste your WhatsApp conversation — AI extracts preferences instantly
        </p>
      </div>

      {/* Example chips */}
      <div style={{ display: "flex", gap: "8px", justifyContent: "center", flexWrap: "wrap" }}>
        {EXAMPLE_CHATS.map(({ label, messages: msgs }) => (
          <button
            key={label}
            onClick={() => setMessages(msgs)}
            style={{
              padding: "5px 14px",
              borderRadius: "999px",
              border: "1px solid rgba(255,255,255,0.1)",
              background: "rgba(255,255,255,0.04)",
              color: "#94a3b8",
              fontSize: "11px",
              fontWeight: 600,
              cursor: "pointer",
              fontFamily: "Inter, sans-serif",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(124,109,247,0.15)";
              e.currentTarget.style.color = "#7c6df7";
              e.currentTarget.style.borderColor = "rgba(124,109,247,0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.04)";
              e.currentTarget.style.color = "#94a3b8";
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
            }}
          >
            Try: {label}
          </button>
        ))}
      </div>

      {/* Chat window */}
      <div
        style={{
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: "14px",
          overflow: "hidden",
        }}
      >
        {/* Chat header */}
        <div
          style={{
            padding: "10px 14px",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <MessageCircle size={13} style={{ color: "#7c6df7" }} />
          <span
            style={{
              fontSize: "10px",
              fontWeight: 700,
              color: "#64748b",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Group Chat
          </span>
          {messages.length > 0 && (
            <span style={{ marginLeft: "auto", fontSize: "10px", color: "#64748b" }}>
              {messages.length} message{messages.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {/* Messages */}
        <div
          style={{
            minHeight: "150px",
            maxHeight: "240px",
            overflowY: "auto",
            padding: "12px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          {messages.length === 0 ? (
            <p
              style={{
                textAlign: "center",
                color: "#64748b",
                fontSize: "12px",
                marginTop: "40px",
                fontStyle: "italic",
              }}
            >
              Type a message or try an example above
            </p>
          ) : (
            messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.02 }}
                style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}
              >
                <div
                  style={{
                    width: "24px",
                    height: "24px",
                    borderRadius: "50%",
                    background: AVATAR_COLORS[i % 4],
                    flexShrink: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "10px",
                    fontWeight: 700,
                    color: "#e2e8f0",
                  }}
                >
                  {AVATARS[i % 4]}
                </div>
                <div
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.07)",
                    borderRadius: "10px",
                    padding: "7px 12px",
                    fontSize: "12px",
                    color: "#e2e8f0",
                    lineHeight: 1.5,
                    maxWidth: "85%",
                  }}
                >
                  {msg}
                </div>
              </motion.div>
            ))
          )}
        </div>

        {/* Input row */}
        <div
          style={{
            padding: "10px 14px",
            borderTop: "1px solid rgba(255,255,255,0.06)",
            display: "flex",
            gap: "8px",
            alignItems: "center",
          }}
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Type a message and press Enter…"
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              fontSize: "12px",
              color: "#e2e8f0",
              fontFamily: "Inter, sans-serif",
            }}
          />
          <button
            onClick={() => addMessage(draft)}
            disabled={!draft.trim()}
            style={{
              background: "none",
              border: "none",
              cursor: draft.trim() ? "pointer" : "not-allowed",
              opacity: draft.trim() ? 1 : 0.3,
              color: "#7c6df7",
              display: "flex",
              alignItems: "center",
              transition: "opacity 0.2s",
            }}
          >
            <Send size={15} />
          </button>
        </div>
      </div>

      {/* Submit */}
      <button
        onClick={() => onSubmit(messages)}
        disabled={messages.length === 0 || loading}
        className="btn-primary"
        style={{
          width: "100%",
          padding: "13px 0",
          borderRadius: "12px",
          border: "none",
          color: "white",
          fontSize: "13px",
          fontWeight: 700,
          cursor: messages.length === 0 || loading ? "not-allowed" : "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          fontFamily: "Inter, sans-serif",
          letterSpacing: "-0.01em",
        }}
      >
        {loading ? (
          <>
            <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} />
            Analysing conversation…
          </>
        ) : (
          "Extract preferences →"
        )}
      </button>
    </div>
  );
}
