import { useState, useCallback } from "react";
import { parseChat, generateItinerary, simulateDelay } from "../api/tripApi";

const INITIAL = {
  step: "chat",       // chat | preferences | itinerary
  loading: false,
  error: null,
  chatMessages: [],
  constraints: null,
  assumptions: {},
  missingFields: [],
  conflictReport: null,
  itinerary: null,
  alternatives: [],
  timeline: [],
  mapPoints: [],
  costBreakdown: null,
  scoreBreakdown: null,
  explanation: "",
  delayResult: null,
  toasts: [],
};

export function useItinerary() {
  const [state, setState] = useState(INITIAL);

  const patch = useCallback((updates) =>
    setState((prev) => ({ ...prev, ...updates })), []);

  const addToast = useCallback((message, type = "info") => {
    const id = Date.now();
    setState((prev) => ({
      ...prev,
      toasts: [...prev.toasts, { id, message, type }],
    }));
    setTimeout(() =>
      setState((prev) => ({
        ...prev,
        toasts: prev.toasts.filter((t) => t.id !== id),
      })), 4000);
  }, []);

  const submitChat = useCallback(async (messages) => {
    patch({ loading: true, error: null, chatMessages: messages });
    try {
      const data = await parseChat(messages);
      patch({
        loading: false,
        step: "preferences",
        constraints: data.extracted_constraints,
        assumptions: data.assumptions ?? {},
        missingFields: data.missing_fields ?? [],
        conflictReport: data.conflict_report ?? null,
      });
    } catch (err) {
      patch({ loading: false, error: err.message });
      addToast("Failed to parse chat. Please try again.", "error");
    }
  }, [patch, addToast]);

  const generatePlan = useCallback(async (constraints) => {
    patch({ loading: true, error: null });
    try {
      const data = await generateItinerary(constraints);
      patch({
        loading: false,
        step: "itinerary",
        constraints,
        itinerary: data.recommended_itinerary,
        alternatives: data.alternatives ?? [],
        timeline: data.timeline ?? [],
        mapPoints: data.map_points ?? [],
        costBreakdown: data.cost_breakdown,
        scoreBreakdown: data.score_breakdown,
        explanation: data.explanation ?? "",
        delayResult: null,
      });
    } catch (err) {
      patch({ loading: false, error: err.message });
      addToast("Failed to generate itinerary. Please try again.", "error");
    }
  }, [patch, addToast]);

  const runDelaySimulation = useCallback(async (delayMinutes) => {
    const { constraints, itinerary } = state;
    if (!constraints) return;
    patch({ loading: true, error: null });
    try {
      const data = await simulateDelay(constraints, delayMinutes, itinerary);
      patch({ loading: false, delayResult: data });
      addToast(`Delay of ${delayMinutes} min simulated successfully.`, "success");
    } catch (err) {
      patch({ loading: false, error: err.message });
      addToast("Delay simulation failed. Please try again.", "error");
    }
  }, [state, patch, addToast]);

  const resetToChat = useCallback(() => setState(INITIAL), []);

  return {
    ...state,
    submitChat,
    generatePlan,
    runDelaySimulation,
    resetToChat,
    addToast,
  };
}
