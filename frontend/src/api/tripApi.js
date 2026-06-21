import axios from "axios";
import { MOCK_PARSE_CHAT, MOCK_ITINERARY, MOCK_DELAY } from "./mockData";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

// Print to the browser console so it's obvious which backend the frontend will hit.
// Catches the common "I edited .env but forgot to restart Vite" failure mode.
console.info(`%c[TripGraph] API base URL = ${BASE_URL}`, "color:#cfd6e0;font-weight:bold");

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

// Subscribers (e.g. useItinerary's addToast) that want to know when the API
// silently falls back to mock data. Without this, the user sees fake results
// and assumes the planner is broken.
const _fallbackListeners = new Set();
export function onApiFallback(listener) {
  _fallbackListeners.add(listener);
  return () => _fallbackListeners.delete(listener);
}
function _notifyFallback(endpoint, err) {
  const detail = err?.response?.status
    ? `HTTP ${err.response.status}`
    : (err?.message || "network error");
  console.warn(`[TripGraph] ${endpoint} failed (${detail}) — using offline MOCK data. Results are not real.`);
  _fallbackListeners.forEach((fn) => {
    try { fn({ endpoint, detail }); } catch (_) {}
  });
}

async function withMockFallback(endpoint, apiFn, mockValue) {
  try {
    const res = await apiFn();
    return res.data;
  } catch (err) {
    _notifyFallback(endpoint, err);
    return { ...mockValue, _isMock: true, _mockReason: err?.message || "network error" };
  }
}

export const parseChat = (messages) =>
  withMockFallback(
    "/api/parse-chat",
    () => client.post("/api/parse-chat", { chat_messages: messages }),
    MOCK_PARSE_CHAT
  );

export const fetchRefinementQuestions = (constraints, assumptions = {}) =>
  withMockFallback(
    "/api/refinement-questions",
    () => client.post("/api/refinement-questions", { constraints, assumptions }),
    { questions: [] }
  );

export const generateItinerary = (constraints, refinementAnswers = null) =>
  withMockFallback(
    "/api/generate-itinerary",
    () => client.post("/api/generate-itinerary", {
      constraints,
      refinement_answers: refinementAnswers,
    }),
    MOCK_ITINERARY
  );

export const simulateDelay = (constraints, delay_minutes, selected_itinerary = null) =>
  withMockFallback(
    "/api/simulate-delay",
    () => client.post("/api/simulate-delay", {
      delay_type: "departure_delay",
      delay_minutes,
      constraints,
      selected_itinerary,
    }),
    MOCK_DELAY
  );
