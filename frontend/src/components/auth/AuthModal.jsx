import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, Loader2, Mail, Lock, User } from "lucide-react";
import { login, register } from "../../api/authApi";
import { useAuth } from "../../hooks/useAuth";

const inputStyle = {
  width: "100%",
  padding: "10px 12px 10px 36px",
  borderRadius: 10,
  border: "1px solid var(--rim-bright)",
  background: "rgba(255,255,255,0.7)",
  fontSize: 13,
  color: "var(--platinum)",
  outline: "none",
  fontFamily: "Inter, sans-serif",
  transition: "border-color 0.15s, box-shadow 0.15s",
};

function Field({ icon: Icon, type = "text", placeholder, value, onChange, onFocus, onBlur }) {
  return (
    <div style={{ position: "relative" }}>
      <Icon
        size={14}
        style={{
          position: "absolute", left: 11, top: "50%", transform: "translateY(-50%)",
          color: "var(--silver)", pointerEvents: "none",
        }}
      />
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onFocus={onFocus}
        onBlur={onBlur}
        autoComplete={type === "password" ? "current-password" : type === "email" ? "email" : "name"}
        style={inputStyle}
        onFocusCapture={(e) => { e.target.style.borderColor = "var(--chrome)"; e.target.style.boxShadow = "0 0 0 2px rgba(42,45,51,0.10)"; }}
        onBlurCapture={(e) => { e.target.style.borderColor = "var(--rim-bright)"; e.target.style.boxShadow = "none"; }}
      />
    </div>
  );
}

export function AuthModal({ onClose }) {
  const { signIn } = useAuth();
  const [tab, setTab] = useState("login"); // "login" | "register"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const reset = () => { setError(""); setEmail(""); setPassword(""); setDisplayName(""); };

  const switchTab = (t) => { setTab(t); reset(); };

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      let data;
      if (tab === "login") {
        data = await login({ email, password });
        signIn(data.access_token, { email, display_name: data.display_name || email.split("@")[0] });
      } else {
        data = await register({ email, password, displayName });
        signIn(data.access_token, { email, display_name: displayName || email.split("@")[0] });
      }
      onClose();
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.18 }}
      style={{
        position: "fixed", inset: 0, zIndex: 200,
        display: "flex", alignItems: "center", justifyContent: "center",
        background: "rgba(245,245,247,0.55)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        padding: 24,
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <motion.div
        initial={{ scale: 0.94, y: 16 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.92, y: 12 }}
        transition={{ type: "spring", stiffness: 320, damping: 28 }}
        style={{
          width: "100%", maxWidth: 380,
          background: "linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,249,251,0.92))",
          backdropFilter: "blur(36px)",
          WebkitBackdropFilter: "blur(36px)",
          border: "1px solid var(--rim)",
          borderRadius: 22,
          boxShadow: "inset 0 1px 0 rgba(255,255,255,0.9), 0 24px 64px rgba(20,22,28,0.18)",
          padding: "28px 28px 24px",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: "var(--platinum)" }}>
            {tab === "login" ? "Sign in" : "Create account"}
          </span>
          <button
            onClick={onClose}
            style={{
              background: "transparent", border: "none", cursor: "pointer",
              color: "var(--silver)", padding: 4, borderRadius: 6,
              display: "flex", alignItems: "center",
              transition: "color 0.15s",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--platinum)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--silver)"; }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Tab switcher */}
        <div style={{
          display: "flex", gap: 4,
          background: "rgba(0,0,0,0.05)", borderRadius: 10,
          padding: 4, marginBottom: 20,
        }}>
          {["login", "register"].map((t) => (
            <button
              key={t}
              onClick={() => switchTab(t)}
              style={{
                flex: 1, padding: "7px 0", borderRadius: 8,
                fontSize: 12, fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s",
                border: "none",
                background: tab === t
                  ? "linear-gradient(180deg, #3a3d44, #1d1f25)"
                  : "transparent",
                color: tab === t ? "#f5f5f7" : "var(--silver)",
                boxShadow: tab === t ? "0 2px 8px rgba(20,22,28,0.18)" : "none",
              }}
            >
              {t === "login" ? "Sign in" : "Register"}
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <AnimatePresence>
            {tab === "register" && (
              <motion.div
                key="displayName"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                style={{ overflow: "hidden" }}
              >
                <Field
                  icon={User}
                  placeholder="Display name (optional)"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
              </motion.div>
            )}
          </AnimatePresence>

          <Field
            icon={Mail}
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Field
            icon={Lock}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && (
            <p style={{ fontSize: 11.5, color: "#a83232", padding: "6px 10px", background: "rgba(168,50,50,0.08)", borderRadius: 8 }}>
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !email || !password}
            style={{
              marginTop: 4,
              padding: "11px 0",
              borderRadius: 999,
              border: "1px solid rgba(0,0,0,0.35)",
              background: "linear-gradient(180deg, #3a3d44, #1d1f25)",
              color: "#f5f5f7",
              fontSize: 13,
              fontWeight: 600,
              cursor: loading || !email || !password ? "not-allowed" : "pointer",
              opacity: loading || !email || !password ? 0.5 : 1,
              display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
              transition: "opacity 0.2s, filter 0.2s",
              boxShadow: "inset 0 1px 0 rgba(255,255,255,0.18), 0 6px 16px rgba(20,22,28,0.20)",
              fontFamily: "Inter, sans-serif",
            }}
          >
            {loading && <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />}
            {tab === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        {/* Footer switch */}
        <p style={{ textAlign: "center", marginTop: 16, fontSize: 11.5, color: "var(--silver)" }}>
          {tab === "login" ? "No account yet? " : "Already have an account? "}
          <button
            onClick={() => switchTab(tab === "login" ? "register" : "login")}
            style={{
              background: "none", border: "none", cursor: "pointer",
              color: "var(--chrome)", fontWeight: 600, fontSize: 11.5,
              fontFamily: "Inter, sans-serif",
              textDecoration: "underline",
            }}
          >
            {tab === "login" ? "Register" : "Sign in"}
          </button>
        </p>
      </motion.div>
    </motion.div>
  );
}
