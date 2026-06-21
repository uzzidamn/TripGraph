import { AnimatePresence, motion } from "framer-motion";
import { useItinerary } from "./hooks/useItinerary";
import { Header } from "./components/layout/Header";
import { ChatRoom } from "./components/chat/ChatRoom";
import { ExtractedPreferences } from "./components/preferences/ExtractedPreferences";
import { ItineraryOptions } from "./components/itinerary/ItineraryOptions";
import { ItineraryTimeline } from "./components/itinerary/ItineraryTimeline";
import { CalendarView } from "./components/itinerary/CalendarView";
import { MapView } from "./components/map/MapView";
import { CostBreakdown } from "./components/cost/CostBreakdown";
import { DelaySimulator } from "./components/delay/DelaySimulator";
import { ToastContainer } from "./components/ui/Toast";

function PageWrapper({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.25 }}
      className="max-w-6xl mx-auto px-4 py-8"
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  const {
    step, loading,
    constraints, assumptions, missingFields, conflictReport,
    itinerary, alternatives, timeline, mapPoints,
    costBreakdown, scoreBreakdown, explanation, webEnriched, webContext, currencySymbol, delayResult,
    toasts,
    submitChat, generatePlan, runDelaySimulation, resetToChat,
  } = useItinerary();

  return (
    <div className="min-h-screen bg-bg">
      <Header step={step} onReset={resetToChat} />

      <AnimatePresence mode="wait">
        {step === "chat" && (
          <PageWrapper key="chat">
            <ChatRoom onSubmit={submitChat} loading={loading} />
          </PageWrapper>
        )}

        {step === "preferences" && (
          <PageWrapper key="preferences">
            <ExtractedPreferences
              constraints={constraints}
              assumptions={assumptions}
              missingFields={missingFields}
              conflictReport={conflictReport}
              onConfirm={generatePlan}
              loading={loading}
            />
          </PageWrapper>
        )}

        {step === "itinerary" && (
          <PageWrapper key="itinerary">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 space-y-6">
                <ItineraryOptions
                  itinerary={itinerary}
                  alternatives={alternatives}
                  scoreBreakdown={scoreBreakdown}
                  currencySymbol={currencySymbol}
                />
                <CostBreakdown costBreakdown={costBreakdown} currencySymbol={currencySymbol} />
                <DelaySimulator
                  onSimulate={runDelaySimulation}
                  loading={loading}
                  delayResult={delayResult}
                />
              </div>

              <div className="lg:col-span-2 space-y-6">
                <MapView mapPoints={mapPoints} />

                {webEnriched && webContext && (
                  <div className="bg-surface border border-teal-500/40 rounded-xl p-4 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-400 bg-teal-400/10 px-2.5 py-1 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                        Live data
                      </span>
                      <span className="text-xs text-text-muted">Enriched with real-time web search</span>
                    </div>
                    {webContext.weather && (
                      <p className="text-xs text-text-secondary">
                        <span className="font-medium text-text-primary">Weather: </span>
                        {webContext.weather}
                      </p>
                    )}
                    {webContext.events && webContext.events.length > 0 && (
                      <p className="text-xs text-text-secondary">
                        <span className="font-medium text-text-primary">Upcoming: </span>
                        {webContext.events.slice(0, 3).join(" · ")}
                      </p>
                    )}
                  </div>
                )}

                {explanation && (
                  <div className="bg-surface border border-border rounded-xl p-5">
                    <p className="text-sm text-text-primary leading-relaxed">{explanation}</p>
                  </div>
                )}

                <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold text-text-primary">Calendar view</h3>
                  <CalendarView timeline={timeline} />
                </div>

                <div className="bg-surface border border-border rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold text-text-primary">Timeline</h3>
                  <ItineraryTimeline timeline={timeline} currencySymbol={currencySymbol} />
                </div>
              </div>
            </div>
          </PageWrapper>
        )}
      </AnimatePresence>

      <ToastContainer toasts={toasts} />
    </div>
  );
}
