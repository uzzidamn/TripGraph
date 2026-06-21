/**
 * Glass primitives — Apple-aluminum aesthetic.
 *
 * Use these instead of raw divs whenever a surface needs the blurred-glass
 * look. Two strengths:
 *   <GlassPanel>   subtle, used for inline cards on top of the map
 *   <GlassPanel strong> heavier, used for side rails and modal-like overlays
 *
 * MetalText renders text with the Apple-logo chrome gradient.
 * Pill is the silver chip used for badges (weather, traffic, fatigue level).
 */
import React from "react";

export function GlassPanel({ strong = false, className = "", style = {}, children, ...rest }) {
  const base = strong ? "glass-strong" : "glass";
  return (
    <div className={`${base} ${className}`} style={style} {...rest}>
      {children}
    </div>
  );
}

export function MetalText({ as: Tag = "span", className = "", children, ...rest }) {
  return (
    <Tag className={`metal-text ${className}`} {...rest}>
      {children}
    </Tag>
  );
}

export function Pill({ tone = "default", className = "", children, ...rest }) {
  const toneClass = {
    default: "chip",
    muted:   "chip chip-muted",
    must:    "chip chip-must",
    warning: "chip chip-warning",
    rain:    "chip chip-rain",
  }[tone] || "chip";
  return (
    <span className={`${toneClass} ${className}`} {...rest}>
      {children}
    </span>
  );
}

/**
 * Radial gauge for fatigue/morale.
 * pct: 0-100. label: short text shown beneath the ring.
 */
export function Gauge({ pct = 0, label, title }) {
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <div
      style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3, minWidth: 56 }}
      title={title}
    >
      <div className="gauge-ring" style={{ "--pct": clamped }} />
      {label && (
        <span
          style={{
            fontSize: 8.5,
            color: "var(--silver)",
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </span>
      )}
    </div>
  );
}

/**
 * Buttonised metal pill — primary call-to-action.
 */
export function MetalButton({ children, className = "", style = {}, ...rest }) {
  return (
    <button
      className={`btn-primary ${className}`}
      style={{
        padding: "10px 18px",
        borderRadius: 999,
        fontSize: 13,
        cursor: "pointer",
        ...style,
      }}
      {...rest}
    >
      {children}
    </button>
  );
}

/**
 * Ghost variant for secondary actions.
 */
export function GhostButton({ children, className = "", style = {}, ...rest }) {
  return (
    <button
      className={`btn-ghost ${className}`}
      style={{
        padding: "8px 14px",
        borderRadius: 999,
        fontSize: 12,
        cursor: "pointer",
        ...style,
      }}
      {...rest}
    >
      {children}
    </button>
  );
}
