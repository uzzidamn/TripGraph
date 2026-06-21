/**
 * Selection context — single source of truth for "which event/marker is active"
 * and WHERE on the screen the active marker sits (for map-anchored popovers).
 *
 * The map sets activePointId + anchorPx on marker click.
 * The calendar sets activePointId on card click (map then computes anchorPx).
 * EventPopover reads anchorPx to position itself at the pin.
 */
import { createContext, useCallback, useContext, useState } from "react";

const SelectionContext = createContext(null);

export function SelectionProvider({ children }) {
  const [activePointId, setActivePointIdRaw] = useState(null);
  const [anchorPx, setAnchorPx] = useState(null);
  const [activeLatLng, setActiveLatLng] = useState(null);

  const setActivePointId = useCallback((id, latLng = null, px = null) => {
    setActivePointIdRaw(id);
    if (latLng) setActiveLatLng(latLng);
    if (px) setAnchorPx(px);
    if (!id) {
      setAnchorPx(null);
      setActiveLatLng(null);
    }
  }, []);

  return (
    <SelectionContext.Provider value={{
      activePointId, setActivePointId,
      anchorPx, setAnchorPx,
      activeLatLng, setActiveLatLng,
    }}>
      {children}
    </SelectionContext.Provider>
  );
}

export function useSelection() {
  const ctx = useContext(SelectionContext);
  if (!ctx) {
    return {
      activePointId: null, setActivePointId: () => {},
      anchorPx: null, setAnchorPx: () => {},
      activeLatLng: null, setActiveLatLng: () => {},
    };
  }
  return ctx;
}
