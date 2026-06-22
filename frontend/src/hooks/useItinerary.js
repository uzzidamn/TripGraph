import { useState, useCallback, useEffect } from "react";
import {
  parseChat,
  fetchRefinementQuestions,
  generateItinerary,
  simulateDelay,
  onApiFallback,
} from "../api/tripApi";

const INITIAL = {
  step: "chat",                  // chat | preferences | refine | itinerary | unsupported
  loading: false,
  error: null,
  chatMessages: [],
  constraints: null,
  assumptions: {},
  missingFields: [],
  conflictReport: null,

  // Guardrail / Memory
  guardrailResult: null,
  userProfile: null,
  memoryContext: null,
  visitedDestinations: [],

  // Unsupported route
  unsupportedRoute: null,
  suggestedRoutes: [],

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
  segmentPolylines: [],
  retrievalSource: {},
  retrievalPasses: 0,

  // Pipeline trace (node → status)
  nodeStatus: {},

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

  // 1) parse chat → guardrail check → preferences step
  const submitChat = useCallback(
    async (messages) => {
      patch({ loading: true, error: null, chatMessages: messages, guardrailResult: null, nodeStatus: { guardrail: "running" } });
      try {
        const data = await parseChat(messages);

        // Guardrail gate (Agent 0)
        const guardrailAction = data.guardrail_result?.action;
        const guardrailResponse = data.guardrail_result?.response;
        if (guardrailAction === "clarify") {
          patch({
            loading: false,
            guardrailResult: data.guardrail_result,
            nodeStatus: { guardrail: "done" },
          });
          addToast(guardrailResponse || "I can only help plan trips. Please describe your travel plans!", "error");
          return;
        }
        if (guardrailAction === "confirm") {
          patch({
            loading: false,
            guardrailResult: data.guardrail_result,
            nodeStatus: { guardrail: "done" },
          });
          addToast(guardrailResponse || "Looks like you've planned this trip before. Confirm to replan it!", "info");
          // Still allow proceeding — just surface the notice
        }

        // OFF_TOPIC legacy fallback
        const specialReqs = data.extracted_constraints?.special_requirements ?? [];
        if (specialReqs.includes("OFF_TOPIC")) {
          patch({ loading: false, nodeStatus: { guardrail: "done" } });
          addToast("I can only help plan trips. Please describe your travel plans!", "error");
          return;
        }

        const missing = data.missing_fields ?? [];
        if (missing.length > 0) {
          patch({
            loading: false,
            guardrailResult: data.guardrail_result ?? null,
            userProfile: data.user_profile ?? null,
            memoryContext: data.memory_context ?? null,
            visitedDestinations: data.visited_destinations ?? [],
            constraints: data.extracted_constraints,
            assumptions: data.assumptions ?? {},
            missingFields: missing,
            conflictReport: data.conflict_report ?? null,
            nodeStatus: { guardrail: "done", chat_parser: "done", memory_agent: "done", constraint_validator: "done" },
          });
          return;
        }
        patch({
          loading: false,
          step: "preferences",
          guardrailResult: data.guardrail_result ?? null,
          userProfile: data.user_profile ?? null,
          memoryContext: data.memory_context ?? null,
          visitedDestinations: data.visited_destinations ?? [],
          constraints: data.extracted_constraints,
          assumptions: data.assumptions ?? {},
          missingFields: [],
          conflictReport: data.conflict_report ?? null,
          nodeStatus: { guardrail: "done", chat_parser: "done", memory_agent: "done", constraint_validator: "done" },
        });
      } catch (err) {
        patch({ loading: false, error: err.message, nodeStatus: {} });
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

        // Unsupported route
        if (data.unsupported_route) {
          patch({
            loading: false,
            step: "unsupported",
            unsupportedRoute: data.unsupported_route,
            suggestedRoutes: data.suggested_routes ?? [],
            nodeStatus: { guardrail: "done", chat_parser: "done", memory_agent: "done",
                          constraint_validator: "done", route_retriever: "done" },
          });
          return;
        }

        patch({
          loading: false,
          step: "itinerary",
          constraints,
          unsupportedRoute: null,
          suggestedRoutes: [],
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
          segmentPolylines: data.segment_polylines ?? [],
          retrievalSource: data.retrieval_source ?? {},
          retrievalPasses: data.retrieval_passes ?? 0,
          nodeStatus: {
            guardrail: "done", chat_parser: "done", memory_agent: "done",
            constraint_validator: "done", route_retriever: "done",
            hotel_retriever: "done", transport_retriever: "done",
            activity_retriever: "done", food_retriever: "done", waypoint_retriever: "done",
            planner_orchestrator: "done", explainer: "done", memory_updater: "done",
          },
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

  const handleSelectSuggestedRoute = useCallback(
    (route) => {
      // User picked a suggested route from unsupported screen — pre-fill constraints and go to preferences
      const newConstraints = {
        origin: route.origin,
        destination: route.destination,
        destination_type: route.destination_type,
      };
      patch({ step: "preferences", constraints: newConstraints, unsupportedRoute: null, suggestedRoutes: [] });
    },
    [patch]
  );

  return {
    ...state,
    submitChat,
    confirmPreferences,
    submitRefinements,
    skipRefinements,
    generatePlan,
    runDelaySimulation,
    resetToChat,
    handleSelectSuggestedRoute,
    addToast,
  };
}
