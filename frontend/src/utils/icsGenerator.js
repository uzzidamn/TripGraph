/**
 * Generates an ICS calendar file string from a trip timeline.
 * @param {Array} timeline - Array of timeline event objects
 * @param {Date} startDate - The start date of the trip (defaults to today)
 * @param {string} tripName - Name of the trip for the calendar
 * @returns {string} ICS file content
 */
export function generateICS(timeline, startDate = new Date(), tripName = "TripGraph AI Trip") {
  if (!timeline || !timeline.length) return "";

  function padTwo(n) {
    return String(n).padStart(2, "0");
  }

  function formatDateTime(date, timeStr) {
    // timeStr is "HH:MM"
    const [h, m] = (timeStr || "00:00").split(":").map(Number);
    const d = new Date(date);
    d.setHours(h, m || 0, 0, 0);
    return (
      d.getFullYear().toString() +
      padTwo(d.getMonth() + 1) +
      padTwo(d.getDate()) +
      "T" +
      padTwo(d.getHours()) +
      padTwo(d.getMinutes()) +
      "00"
    );
  }

  function escapeICS(str) {
    return String(str || "")
      .replace(/\\/g, "\\\\")
      .replace(/;/g, "\\;")
      .replace(/,/g, "\\,")
      .replace(/\n/g, "\\n");
  }

  const TYPE_CATEGORY = {
    travel: "TRAVEL",
    hotel: "ACCOMMODATION",
    activity: "ACTIVITY",
    meal: "MEAL",
    rest: "LEISURE",
  };

  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//TripGraph AI//TripGraph//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    `X-WR-CALNAME:${escapeICS(tripName)}`,
    "X-WR-TIMEZONE:Asia/Kolkata",
  ];

  timeline.forEach((event, idx) => {
    const dayOffset = (event.day ?? 1) - 1;
    const eventDate = new Date(startDate);
    eventDate.setDate(eventDate.getDate() + dayOffset);

    const dtStart = formatDateTime(eventDate, event.start_time);
    const dtEnd = formatDateTime(eventDate, event.end_time);

    const uid = `tripgraph-${Date.now()}-${idx}@tripgraph.ai`;
    const costStr = event.cost === 0
      ? "Free"
      : event.cost != null
      ? `₹${event.cost.toLocaleString()}`
      : "Included";

    const category = TYPE_CATEGORY[event.type] ?? "TRIP";
    const desc = `Type: ${category}\\nCost: ${costStr}`;

    lines.push(
      "BEGIN:VEVENT",
      `UID:${uid}`,
      `DTSTART:${dtStart}`,
      `DTEND:${dtEnd}`,
      `SUMMARY:${escapeICS(event.title)}`,
      `DESCRIPTION:${desc}`,
      `CATEGORIES:${category}`,
      "STATUS:CONFIRMED",
      "END:VEVENT"
    );
  });

  lines.push("END:VCALENDAR");
  return lines.join("\r\n");
}

/**
 * Triggers a browser download of an ICS file.
 */
export function downloadICS(timeline, tripName = "TripGraph AI Trip") {
  const ics = generateICS(timeline, new Date(), tripName);
  if (!ics) return;

  const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${tripName.replace(/\s+/g, "_")}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
