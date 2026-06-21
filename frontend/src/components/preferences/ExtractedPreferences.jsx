import { useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle, AlertTriangle, Edit3, Loader2, Users, Car, Train, Bus, Plane, Wallet, Hotel, Calendar, MapPin } from "lucide-react";

const FIELD_LABELS = {
  origin: "Origin",
  destination: "Destination",
  destination_type: "Destination type",
  budget_per_person: "Budget/person",
  group_size: "Group size",
  hotel_tier: "Hotel tier",
  transport_preference: "Transport",
  avoid_night_driving: "Avoid night driving",
  must_include: "Must include",
  return_deadline: "Return by",
  trip_duration: "Duration",
};

function formatValue(key, val, currencySymbol = "₹") {
  if (val === null || val === undefined) return <span className="text-text-muted">—</span>;
  if (key === "budget_per_person") return `${currencySymbol}${val.toLocaleString()}`;
  if (key === "avoid_night_driving") return val ? "Yes" : "No";
  if (Array.isArray(val)) return val.join(", ") || "—";
  return String(val);
}

// City → symbol — mirrors backend/utils/currency.py
const CITY_CURRENCY = {
  // India
  gurugram:"₹",gurgaon:"₹",delhi:"₹","new delhi":"₹",noida:"₹",mumbai:"₹",
  pune:"₹",bangalore:"₹",bengaluru:"₹",chennai:"₹",hyderabad:"₹",kolkata:"₹",
  ahmedabad:"₹",jaipur:"₹",lucknow:"₹",chandigarh:"₹",kochi:"₹",surat:"₹",
  indore:"₹",bhopal:"₹",nagpur:"₹",goa:"₹",ranchi:"₹",patna:"₹",
  // SE Asia
  bangkok:"฿",phuket:"฿",singapore:"S$","kuala lumpur":"RM",bali:"Rp",
  jakarta:"Rp","ho chi minh":"₫",hanoi:"₫",manila:"₱",
  // East Asia
  tokyo:"¥",osaka:"¥",seoul:"₩",beijing:"¥",shanghai:"¥","hong kong":"HK$",hk:"HK$",
  // Middle East
  dubai:"د.إ","abu dhabi":"د.إ",doha:"﷼",riyadh:"﷼",
  // Europe
  london:"£",paris:"€",amsterdam:"€",berlin:"€",rome:"€",barcelona:"€",zurich:"Fr",
  // Americas — full names + common abbreviations
  "new york":"$","los angeles":"$","san francisco":"$",chicago:"$",houston:"$",
  miami:"$",boston:"$",seattle:"$","las vegas":"$",dallas:"$",washington:"$",
  "new york city":"$",nyc:"$",ny:"$",la:"$",sf:"$",dc:"$",
  toronto:"CA$",vancouver:"CA$",montreal:"CA$",
  "sao paulo":"R$","rio de janeiro":"R$",
  // Oceania
  sydney:"A$",melbourne:"A$",brisbane:"A$",perth:"A$",adelaide:"A$",
  canberra:"A$","gold coast":"A$",auckland:"NZ$",wellington:"NZ$",
  // Russia / CIS
  moscow:"₽","st petersburg":"₽",
  // South Asia
  colombo:"Rs",dhaka:"৳",kathmandu:"Rs",
  // Africa
  nairobi:"Ksh",cairo:"E£","cape town":"R",johannesburg:"R",
};

// Country code → currency symbol fallback
const COUNTRY_CURRENCY_SYM = {
  IN:"₹", US:"$", CA:"CA$", GB:"£", EU:"€", DE:"€", FR:"€",
  AU:"A$", NZ:"NZ$", JP:"¥", KR:"₩", CN:"¥", SG:"S$", TH:"฿",
  AE:"د.إ", MY:"RM", ID:"Rp", VN:"₫", PH:"₱", RU:"₽",
  BR:"R$", MX:"MX$", ZA:"R", EG:"E£", KE:"Ksh",
};

function getCurrencySymbol(city) {
  if (!city) return "₹";
  const key = city.toLowerCase().trim();
  if (CITY_CURRENCY[key]) return CITY_CURRENCY[key];
  // Prefix match for partial input / typos
  for (const [name, sym] of Object.entries(CITY_CURRENCY)) {
    if (name.startsWith(key) || key.startsWith(name)) return sym;
  }
  // Country-based fallback — covers any state, region, or unlisted city
  const cc = _resolveCountry(city);
  if (cc && COUNTRY_CURRENCY_SYM[cc]) return COUNTRY_CURRENCY_SYM[cc];
  return "₹";
}

// Transport options shown for same-country trips
const TRANSPORT_OPTIONS = [
  { value: "cab_with_driver", label: "Cab", icon: Car },
  { value: "self_drive",      label: "Self-drive", icon: Car },
  { value: "bus",             label: "Bus", icon: Bus },
  { value: "train",           label: "Train", icon: Train },
  { value: "flight",          label: "Flight", icon: Plane },
];

// city → country-code; used for same-country detection
const CITY_COUNTRY = {};
const _CC = [
  ["IN", ["gurugram","gurgaon","delhi","new delhi","noida","faridabad","ghaziabad",
          "mumbai","pune","nagpur","nashik","aurangabad","surat","ahmedabad","vadodara",
          "rajkot","bhavnagar","bangalore","bengaluru","mysore","mysuru","mangalore","hubli",
          "chennai","coimbatore","madurai","trichy","salem","vellore",
          "hyderabad","secunderabad","warangal","visakhapatnam","vijayawada",
          "kolkata","siliguri","durgapur","asansol","howrah",
          "jaipur","jodhpur","udaipur","ajmer","kota","bikaner","alwar",
          "lucknow","kanpur","agra","varanasi","allahabad","prayagraj","meerut",
          "bhopal","indore","gwalior","jabalpur",
          "chandigarh","amritsar","ludhiana","jalandhar","patiala",
          "kochi","thiruvananthapuram","kozhikode","thrissur",
          "rishikesh","haridwar","dehradun","mussoorie","nainital","almora",
          "manali","shimla","dharamshala","mcleod ganj","kullu","kasol",
          "darjeeling","gangtok","kalimpong","leh","ladakh","srinagar","jammu","kargil",
          "goa","panaji","margao","vasco","ooty","kodaikanal","coorg","madikeri","chikmagalur",
          "tirthan valley","spiti","lahaul","ziro","shillong","cherrapunji",
          "bhubaneswar","puri","cuttack","raipur","ranchi","patna","guwahati","imphal"]],
  ["AU", ["sydney","melbourne","brisbane","perth","adelaide","canberra","gold coast",
          "hobart","darwin","cairns","townsville","geelong","newcastle"]],
  ["NZ", ["auckland","wellington","christchurch","hamilton","dunedin"]],
  ["GB", ["london","manchester","birmingham","edinburgh","glasgow","bristol","leeds"]],
  ["EU", ["paris","lyon","marseille","amsterdam","rotterdam","brussels","antwerp",
          "berlin","munich","hamburg","frankfurt","cologne","vienna","zurich","geneva",
          "rome","milan","florence","venice","barcelona","madrid","lisbon","athens",
          "prague","warsaw","budapest","stockholm","oslo","copenhagen","dublin"]],
  ["US", ["new york","new york city","nyc","ny","los angeles","la","chicago",
          "houston","phoenix","san francisco","sf","seattle","boston","miami",
          "washington","dc","las vegas","dallas","new orleans","denver","atlanta",
          "portland","austin","nashville","minneapolis","detroit","philadelphia",
          // US states
          "california","texas","florida","illinois","pennsylvania","ohio","georgia",
          "north carolina","michigan","new jersey","virginia","arizona","massachusetts",
          "tennessee","indiana","missouri","maryland","wisconsin","colorado","minnesota",
          "south carolina","alabama","louisiana","kentucky","oregon","oklahoma",
          "connecticut","utah","iowa","nevada","arkansas","mississippi","kansas",
          "new mexico","nebraska","idaho","west virginia","hawaii","maine",
          "new hampshire","montana","rhode island","delaware","south dakota",
          "north dakota","alaska","vermont","wyoming"]],
  ["CA", ["toronto","vancouver","montreal","calgary","ottawa","edmonton"]],
  ["DE", ["berlin","munich","hamburg","frankfurt","cologne","stuttgart"]],
  ["FR", ["paris","lyon","marseille","bordeaux","nice","toulouse"]],
  ["JP", ["tokyo","osaka","kyoto","yokohama","nagoya","sapporo","fukuoka"]],
  ["SG", ["singapore"]],
  ["TH", ["bangkok","phuket","chiang mai","pattaya","krabi"]],
  ["AE", ["dubai","abu dhabi","sharjah"]],
  ["RU", ["moscow","st petersburg","novosibirsk","yekaterinburg"]],
  ["ZA", ["cape town","johannesburg","durban","pretoria"]],
];
_CC.forEach(([code, cities]) => cities.forEach(c => { CITY_COUNTRY[c] = code; }));

function _resolveCountry(city) {
  if (!city) return null;
  const key = city.toLowerCase().trim();
  if (CITY_COUNTRY[key]) return CITY_COUNTRY[key];
  // Prefix match for partial / misspelled input
  for (const [name, code] of Object.entries(CITY_COUNTRY)) {
    if (name.startsWith(key) || key.startsWith(name)) return code;
  }
  return null;
}

function isSameCountry(origin, destination) {
  if (!origin || !destination) return true;
  const oc = _resolveCountry(origin);
  const dc = _resolveCountry(destination);
  // Both cities known → compare country codes
  if (oc && dc) return oc === dc;
  // One or both unknown → assume domestic so the user sees the transport picker.
  // The backend will apply flight if the actual distance warrants it.
  return true;
}

const HOTEL_TIERS = [
  { value: "budget",  label: "Budget" },
  { value: "comfort", label: "Comfort" },
  { value: "luxury",  label: "Luxury" },
];

const DURATION_OPTIONS = [
  { value: "2D1N",    label: "2 days" },
  { value: "3D2N",    label: "3 days" },
  { value: "4D3N",    label: "4 days" },
  { value: "5D4N",    label: "5 days" },
  { value: "7D6N",    label: "1 week" },
  { value: "10D9N",   label: "10 days" },
  { value: "14D13N",  label: "2 weeks" },
];

function HotelTierPicker({ value, onChange }) {
  return (
    <div className="flex gap-2">
      {HOTEL_TIERS.map(({ value: v, label }) => (
        <button key={v} type="button" onClick={() => onChange(v)}
          className={`flex-1 py-2 rounded-lg border text-xs font-medium transition-all ${
            value === v
              ? "border-primary bg-primary/10 text-primary"
              : "border-border bg-surface hover:border-primary/40 text-text-muted"
          }`}>
          {label}
        </button>
      ))}
    </div>
  );
}

function DurationPicker({ value, onChange }) {
  return (
    <div className="grid grid-cols-4 gap-2">
      {DURATION_OPTIONS.map(({ value: v, label }) => (
        <button key={v} type="button" onClick={() => onChange(v)}
          className={`py-2 rounded-lg border text-xs font-medium transition-all ${
            value === v
              ? "border-primary bg-primary/10 text-primary"
              : "border-border bg-surface hover:border-primary/40 text-text-muted"
          }`}>
          {label}
        </button>
      ))}
    </div>
  );
}

function BudgetInput({ value, onChange, currencySymbol = "₹" }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-text-muted">{currencySymbol}</span>
      <input
        type="number"
        min={1}
        step={1}
        value={value || ""}
        onChange={e => onChange(parseInt(e.target.value) || null)}
        placeholder="e.g. 500"
        className="flex-1 bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
      />
      <span className="text-xs text-text-muted whitespace-nowrap">per person</span>
    </div>
  );
}

function TransportPicker({ value, onChange }) {
  return (
    <div className="grid grid-cols-5 gap-2">
      {TRANSPORT_OPTIONS.map(({ value: v, label, icon: Icon }) => (
        <button
          key={v}
          type="button"
          onClick={() => onChange(v)}
          className={`flex flex-col items-center gap-1.5 p-2.5 rounded-lg border text-xs font-medium transition-all ${
            value === v
              ? "border-primary bg-primary/10 text-primary"
              : "border-border bg-surface hover:border-primary/40 text-text-muted"
          }`}
        >
          <Icon size={16} />
          {label}
        </button>
      ))}
    </div>
  );
}

function GroupSizePicker({ value, onChange }) {
  const count = value || 2;
  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={() => onChange(Math.max(1, count - 1))}
        className="w-8 h-8 rounded-lg border border-border bg-surface text-text-primary hover:border-primary/40 font-bold transition-colors"
      >
        −
      </button>
      <div className="flex items-center gap-1.5 min-w-[60px] justify-center">
        <Users size={14} className="text-primary" />
        <span className="text-sm font-semibold text-text-primary">{count}</span>
        <span className="text-xs text-text-muted">people</span>
      </div>
      <button
        type="button"
        onClick={() => onChange(Math.min(20, count + 1))}
        className="w-8 h-8 rounded-lg border border-border bg-surface text-text-primary hover:border-primary/40 font-bold transition-colors"
      >
        +
      </button>
    </div>
  );
}

function CityInput({ value, onChange, placeholder }) {
  return (
    <input
      type="text"
      value={value || ""}
      onChange={e => onChange(e.target.value || null)}
      placeholder={placeholder}
      className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary"
    />
  );
}

export function ExtractedPreferences({
  constraints,
  assumptions,
  missingFields,
  conflictReport,
  onConfirm,
  loading,
}) {
  const needsOrigin      = !constraints?.origin;
  const needsDestination = !constraints?.destination;
  const needsGroupSize   = !constraints?.group_size;
  const needsHotelTier   = !constraints?.hotel_tier;
  const needsBudget      = !constraints?.budget_per_person;
  const needsDuration    = !constraints?.trip_duration;

  const [origin,      setOrigin]      = useState(constraints?.origin ?? null);
  const [destination, setDestination] = useState(constraints?.destination ?? null);
  const [transport,   setTransport]   = useState(constraints?.transport_preference?.[0] ?? null);
  const [groupSize,   setGroupSize]   = useState(constraints?.group_size  ?? 2);
  const [hotelTier,   setHotelTier]   = useState(constraints?.hotel_tier  ?? null);
  const [budget,      setBudget]      = useState(constraints?.budget_per_person ?? null);
  const [duration,    setDuration]    = useState(constraints?.trip_duration ?? null);

  // Recompute international/domestic dynamically as user fills in origin/destination
  const effectiveOrigin      = origin      || constraints?.origin      || "";
  const effectiveDestination = destination || constraints?.destination || "";
  const international = effectiveOrigin && effectiveDestination &&
                        !isSameCountry(effectiveOrigin, effectiveDestination);

  // Currency symbol derived from current origin
  const currencySymbol = getCurrencySymbol(effectiveOrigin);

  // Only ask for transport on domestic trips where it's not already set
  const needsTransport = !constraints?.transport_preference?.length && !international &&
                         !!effectiveOrigin && !!effectiveDestination;

  const showClarification = needsOrigin || needsDestination || needsTransport ||
                            needsGroupSize || needsHotelTier || needsBudget || needsDuration;

  const canGenerate = (!needsOrigin      || (origin      && origin.trim()))      &&
                      (!needsDestination || (destination && destination.trim())) &&
                      (!needsTransport   || transport !== null);

  function handleConfirm() {
    const enriched = {
      ...constraints,
      ...(needsOrigin      && origin       ? { origin }                            : {}),
      ...(needsDestination && destination  ? { destination }                       : {}),
      ...(international                    ? { transport_preference: ["flight"] }  : {}),
      ...(needsTransport   && transport    ? { transport_preference: [transport] } : {}),
      ...(needsGroupSize   && groupSize    ? { group_size: groupSize }             : {}),
      ...(needsHotelTier   && hotelTier    ? { hotel_tier: hotelTier }             : {}),
      ...(needsBudget      && budget       ? { budget_per_person: budget }         : {}),
      ...(needsDuration    && duration     ? { trip_duration: duration }           : {}),
    };
    onConfirm(enriched);
  }

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="text-center space-y-1">
        <h2 className="text-xl font-bold text-text-primary">Extracted preferences</h2>
        <p className="text-text-muted text-sm">Review what the AI understood from your conversation</p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-surface border border-border rounded-xl overflow-hidden"
      >
        <div className="px-4 py-3 border-b border-border flex items-center gap-2">
          <CheckCircle size={15} className="text-success" />
          <span className="text-xs font-medium text-text-muted uppercase tracking-wide">
            Constraints
          </span>
        </div>
        <div className="divide-y divide-border">
          {Object.entries(FIELD_LABELS).map(([key, label]) => (
            <div key={key} className="flex items-center justify-between px-4 py-2.5">
              <span className="text-xs text-text-muted w-40 flex-shrink-0">{label}</span>
              <span className="text-sm text-text-primary text-right">
                {formatValue(key, constraints?.[key], currencySymbol)}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Inline clarification for missing key fields */}
      {showClarification && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-surface border border-primary/30 rounded-xl p-5 space-y-5"
        >
          <div className="flex items-center gap-2">
            <Edit3 size={14} className="text-primary" />
            <span className="text-xs font-semibold text-primary uppercase tracking-wide">
              A few more details
            </span>
          </div>

          {needsOrigin && (
            <div className="space-y-2.5">
              <label className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                <MapPin size={14} className="text-primary" /> Where are you travelling from?
              </label>
              <CityInput value={origin} onChange={setOrigin} placeholder="e.g. Mumbai, Bangalore, Delhi…" />
              {!origin?.trim() && (
                <p className="text-xs text-warning">Please enter your departure city to continue.</p>
              )}
            </div>
          )}

          {needsDestination && (
            <div className="space-y-2.5">
              <label className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                <MapPin size={14} className="text-primary" /> Where do you want to go?
              </label>
              <CityInput value={destination} onChange={setDestination} placeholder="e.g. Goa, Bangkok, Amsterdam…" />
              {!destination?.trim() && (
                <p className="text-xs text-warning">Please enter your destination to continue.</p>
              )}
            </div>
          )}

          {needsDuration && (
            <div className="space-y-2.5">
              <label className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                <Calendar size={14} className="text-primary" /> Trip duration
              </label>
              <DurationPicker value={duration} onChange={setDuration} />
            </div>
          )}

          {needsGroupSize && (
            <div className="space-y-2.5">
              <label className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                <Users size={14} className="text-primary" /> How many people are travelling?
              </label>
              <GroupSizePicker value={groupSize} onChange={setGroupSize} />
            </div>
          )}

          {needsBudget && (
            <div className="space-y-2.5">
              <label className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                <Wallet size={14} className="text-primary" /> Budget per person
              </label>
              <BudgetInput value={budget} onChange={setBudget} currencySymbol={currencySymbol} />
            </div>
          )}

          {needsHotelTier && (
            <div className="space-y-2.5">
              <label className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                <Hotel size={14} className="text-primary" /> Hotel preference
              </label>
              <HotelTierPicker value={hotelTier} onChange={setHotelTier} />
            </div>
          )}

          {international && (
            <div className="space-y-2.5">
              <label className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                <Plane size={14} className="text-primary" /> Mode of transport
              </label>
              <div className="flex gap-2">
                <div className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg border-2
                                border-primary bg-primary/10 text-primary text-sm font-semibold">
                  <Plane size={15} />
                  Flight
                </div>
              </div>
              <p className="text-xs text-text-muted">
                International trip — only flight is available as transport.
              </p>
            </div>
          )}

          {needsTransport && (
            <div className="space-y-2.5">
              <label className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                <Car size={14} className="text-primary" /> How would you like to travel?
              </label>
              <TransportPicker value={transport} onChange={setTransport} />
              {!transport && (
                <p className="text-xs text-warning">Please select a travel mode to continue.</p>
              )}
            </div>
          )}
        </motion.div>
      )}

      {Object.keys(assumptions).length > 0 && (
        <div className="bg-warning/10 border border-warning/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Edit3 size={14} className="text-warning" />
            <span className="text-xs font-medium text-warning uppercase tracking-wide">
              Assumptions made
            </span>
          </div>
          <ul className="space-y-1">
            {Object.entries(assumptions).map(([k, v]) => (
              <li key={k} className="text-xs text-text-muted">
                <span className="text-text-primary">{FIELD_LABELS[k] ?? k}</span>: {v}
              </li>
            ))}
          </ul>
        </div>
      )}

      {conflictReport?.has_conflicts && (
        <div className="bg-warning/10 border border-warning/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-warning" />
            <span className="text-xs font-medium text-warning uppercase tracking-wide">
              Heads up
            </span>
          </div>
          <ul className="space-y-1">
            {conflictReport.conflicts.map((c, i) => (
              <li key={i} className="text-xs text-text-muted">• {c}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={handleConfirm}
        disabled={loading || !canGenerate}
        className="w-full py-3 rounded-xl bg-primary hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Generating itinerary…
          </>
        ) : (
          "Generate itinerary →"
        )}
      </button>
    </div>
  );
}
