/**
 * PalmCompass — a single-mark logo blending a compass rose with palm fronds.
 * Drawn as a monochrome SVG so it inherits color from CSS.
 *
 * The cardinal points become palm leaves at North/South while East/West stay
 * as sharp compass arrows. The center has a small ring to suggest a lens.
 */
export function PalmCompass({ size = 18, color = "#f5f5f7" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: "block" }}
    >
      {/* Outer thin ring */}
      <circle cx="32" cy="32" r="28" stroke={color} strokeOpacity="0.45" strokeWidth="1.2" />

      {/* Palm frond — North (top): central spine + curved leaves both sides */}
      <path d="M32 6 L32 28" stroke={color} strokeWidth="1.6" strokeLinecap="round" />
      <path d="M32 10 C 28 13, 25 16, 24 21" stroke={color} strokeWidth="1.3" strokeLinecap="round" fill="none" />
      <path d="M32 10 C 36 13, 39 16, 40 21" stroke={color} strokeWidth="1.3" strokeLinecap="round" fill="none" />
      <path d="M32 14 C 29 17, 27 20, 26 24" stroke={color} strokeWidth="1.1" strokeLinecap="round" fill="none" />
      <path d="M32 14 C 35 17, 37 20, 38 24" stroke={color} strokeWidth="1.1" strokeLinecap="round" fill="none" />
      <path d="M32 18 C 30 21, 29 23, 28.5 26" stroke={color} strokeWidth="0.9" strokeLinecap="round" fill="none" />
      <path d="M32 18 C 34 21, 35 23, 35.5 26" stroke={color} strokeWidth="0.9" strokeLinecap="round" fill="none" />

      {/* Palm frond — South (bottom): mirror */}
      <path d="M32 58 L32 36" stroke={color} strokeWidth="1.6" strokeLinecap="round" />
      <path d="M32 54 C 28 51, 25 48, 24 43" stroke={color} strokeWidth="1.3" strokeLinecap="round" fill="none" />
      <path d="M32 54 C 36 51, 39 48, 40 43" stroke={color} strokeWidth="1.3" strokeLinecap="round" fill="none" />
      <path d="M32 50 C 29 47, 27 44, 26 40" stroke={color} strokeWidth="1.1" strokeLinecap="round" fill="none" />
      <path d="M32 50 C 35 47, 37 44, 38 40" stroke={color} strokeWidth="1.1" strokeLinecap="round" fill="none" />

      {/* Compass East arrow */}
      <path d="M40 32 L56 32" stroke={color} strokeWidth="1.6" strokeLinecap="round" />
      <path d="M56 32 L52 29 L52 35 Z" fill={color} />

      {/* Compass West arrow */}
      <path d="M24 32 L8 32" stroke={color} strokeWidth="1.6" strokeLinecap="round" />
      <path d="M8 32 L12 29 L12 35 Z" fill={color} />

      {/* Center ring (lens / coconut) */}
      <circle cx="32" cy="32" r="3.5" fill={color} opacity="0.9" />
      <circle cx="32" cy="32" r="1.5" fill="rgba(0,0,0,0.35)" />
    </svg>
  );
}
