import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle, AlertCircle, Info } from "lucide-react";

const TYPE_CONFIG = {
  success: { icon: CheckCircle, color: "#00b894", bg: "rgba(0,184,148,0.12)", border: "rgba(0,184,148,0.25)" },
  error:   { icon: AlertCircle, color: "#e17055", bg: "rgba(225,112,85,0.12)", border: "rgba(225,112,85,0.25)" },
  info:    { icon: Info,        color: "#7c6df7", bg: "rgba(124,109,247,0.12)", border: "rgba(124,109,247,0.25)" },
};

function ToastItem({ toast }) {
  const cfg = TYPE_CONFIG[toast.type] ?? TYPE_CONFIG.info;
  const Icon = cfg.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.94 }}
      transition={{ duration: 0.22 }}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "10px",
        padding: "10px 16px",
        background: cfg.bg,
        border: `1px solid ${cfg.border}`,
        borderRadius: "12px",
        backdropFilter: "blur(20px)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        minWidth: "260px",
        maxWidth: "360px",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <Icon size={15} style={{ color: cfg.color, flexShrink: 0 }} />
      <span style={{ fontSize: "12px", color: "#e2e8f0", flex: 1, lineHeight: 1.4 }}>
        {toast.message}
      </span>
    </motion.div>
  );
}

export function ToastContainer({ toasts }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", alignItems: "center" }}>
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} />
        ))}
      </AnimatePresence>
    </div>
  );
}
