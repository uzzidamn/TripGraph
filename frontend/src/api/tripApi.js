import axios from "axios";
import { MOCK_PARSE_CHAT, MOCK_ITINERARY, MOCK_DELAY } from "./mockData";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 180000,  // 3 min — web search + LLM can take ~90s for unseeded destinations
  headers: { "Content-Type": "application/json" },
});

async function withMockFallback(apiFn, mockValue) {
  try {
    const res = await apiFn();
    return res.data;
  } catch (err) {
    // If the server responded with an error status, surface it — don't hide behind mock data
    if (err?.response) {
      const detail = err.response.data?.detail ?? err.message;
      throw new Error(detail);
    }
    // Network / CORS / timeout — backend unreachable, fall back to mock
    console.warn("[TripGraph] API unavailable — using mock data", err?.message);
    return mockValue;
  }
}

// Backend expects { chat_messages: [...] }
export const parseChat = (messages) =>
  withMockFallback(
    () => client.post("/api/parse-chat", { chat_messages: messages }),
    MOCK_PARSE_CHAT
  );

export const generateItinerary = (constraints) =>
  withMockFallback(
    () => client.post("/api/generate-itinerary", { constraints }),
    MOCK_ITINERARY
  );

// Backend requires delay_type; selected_itinerary enables real replanning
export const simulateDelay = (constraints, delay_minutes, selected_itinerary = null) =>
  withMockFallback(
    () => client.post("/api/simulate-delay", {
      delay_type: "departure_delay",
      delay_minutes,
      constraints,
      selected_itinerary,
    }),
    MOCK_DELAY
  );
