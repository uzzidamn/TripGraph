import { useState, useCallback, useEffect } from "react";
import {
  parseChat,
  fetchRefinementQuestions,
  generateItinerary,
  simulateDelay,
  onApiFallback,
} from "../api/tripApi";

const INITIAL = {
  step: "chat",                  // chat | preferences | refine | itinerary
  loading: false,
  error: null,
  chatMessages: [],
  constraints: null,
  assumptions: {},
  missingFields: [],
  conflictReport: null,

  // Refinement step
  refinementQuestions: [],
  refinementAnswers: null,

  // Itinerary
  itinerary: null,
  alternatives: [],
  timeline: [],
  mapPoints: [],
  routePolyline: null,
  costBreakdown: null,
  scoreBreakdown: null,
  explanation: "",
  delayResult: null,

  // New backend payloads
  fatiguePerEvent: {},
  weatherForecast: {},
  traffic: {},
  flights: null,
  trains: null,
  hotelDeals: null,
  insightsPerPlace: {},
  review: null,
  architectPlan: null,
  retrievalSource: {},
  retrievalPasses: 0,

  toasts: [],
};

export function useItinerary() {
  const [state, setState] = useState(INITIAL);

  const patch = useCallback(
    (updates) => setState((prev) => ({ ...prev, ...updates })),
    []
  );

  const addToast = useCallback((message, type = "info") => {
    const id = Date.now() + Math.random();
    setState((prev) => ({ ...prev, toasts: [...prev.toasts, { id, message, type }] }));
    setTimeout(
      () =>
        setState((prev) => ({
          ...prev,
          toasts: prev.toasts.filter((t) => t.id !== id),
        })),
      6000
    );
  }, []);

  // Subscribe to silent mock fallbacks so the user actually sees when the
  // backend is unreachable instead of staring at fake "Gurugram" results.
  useEffect(() => {
    return onApiFallback(({ endpoint, detail }) =>
      addToast(`Backend unreachable for ${endpoint} (${detail}). Showing OFFLINE MOCK data — results are not real.`, "error")
    );
  }, [addToast]);

  // 1) parse chat → preferences step
  const submitChat = useCallback(
    async (messages) => {
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
    },
    [patch, addToast]
  );

  // 2) preferences confirmed → fetch refinement questions, move to refine step
  const confirmPreferences = useCallback(
    async (constraints) => {
      patch({ loading: true, error: null, constraints });
      try {
        const data = await fetchRefinementQuestions(constraints, state.assumptions);
        const questions = data.questions || [];
        if (questions.length === 0) {
          // No questions returned — skip refinement, go straight to plan
          await generatePlan(constraints, null);
          return;
        }
        patch({ loading: false, step: "refine", refinementQuestions: questions });
      } catch (err) {
        patch({ loading: false, error: err.message });
        addToast("Couldn't load refinements — proceeding without them.", "info");
        await generatePlan(constraints, null);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [patch, addToast, state.assumptions]
  );

  // 3) refine submitted (or skipped) → generate plan
  const generatePlan = useCallback(
    async (constraintsArg, refinementAnswers) => {
      const constraints = constraintsArg ?? state.constraints;
      patch({ loading: true, error: null, refinementAnswers });
      try {
        const data = await generateItinerary(constraints, refinementAnswers);
        patch({
          loading: false,
          step: "itinerary",
          constraints,
          itinerary: data.recommended_itinerary,
          alternatives: data.alternatives ?? [],
          timeline: data.timeline ?? [],
          mapPoints: data.map_points ?? [],
          routePolyline: data.recommended_itinerary?.route?.polyline ?? null,
          costBreakdown: data.cost_breakdown,
          scoreBreakdown: data.score_breakdown,
          explanation: data.explanation ?? "",
          fatiguePerEvent: data.fatigue_per_event ?? {},
          weatherForecast: data.weather_forecast ?? {},
          traffic: data.traffic ?? {},
          flights: data.flights ?? null,
          trains: data.trains ?? null,
          hotelDeals: data.hotel_deals ?? null,
          insightsPerPlace: data.insights_per_place ?? {},
          review: data.review ?? null,
          architectPlan: data.architect_plan ?? null,
          retrievalSource: data.retrieval_source ?? {},
          retrievalPasses: data.retrieval_passes ?? 0,
          delayResult: null,
        });
      } catch (err) {
        patch({ loading: false, error: err.message });
        addToast("Failed to generate itinerary. Please try again.", "error");
      }
    },
    [patch, addToast, state.constraints]
  );

  const submitRefinements = useCallback(
    (answers) => generatePlan(undefined, answers),
    [generatePlan]
  );

  const skipRefinements = useCallback(
    () => generatePlan(undefined, null),
    [generatePlan]
  );

  const runDelaySimulation = useCallback(
    async (delayMinutes) => {
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
    },
    [state, patch, addToast]
  );

  const resetToChat = useCallback(() => setState(INITIAL), []);

  return {
    ...state,
    submitChat,
    confirmPreferences,
    submitRefinements,
    skipRefinements,
    generatePlan,
    runDelaySimulation,
    resetToChat,
    addToast,
  };
}
