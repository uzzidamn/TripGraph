"""RailRadar client — Indian Railways train data.

RailRadar's public API schema isn't fully documented for our use, so this client
is defensive: it attempts a couple of plausible endpoints with the bearer key
and degrades gracefully (returns None) if the shape differs. The train_agent
pairs this with LLM rail knowledge so the user still gets useful guidance
(nearest railhead, typical trains) even when the live call doesn't land.

Key: RAILRADAR_API_KEY (format rg_...), sent as a Bearer token.
"""
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

RAILRADAR_API_KEY = os.getenv("RAILRADAR_API_KEY")
_BASE_CANDIDATES = [
    "https://railradar.in/api/v1",
    "https://api.railradar.in/v1",
]


class RailRadarClient:
    @classmethod
    def _headers(cls) -> dict:
        return {
            "Authorization": f"Bearer {RAILRADAR_API_KEY}",
            "x-api-key": RAILRADAR_API_KEY or "",
            "Accept": "application/json",
        }

    @classmethod
    def available(cls) -> bool:
        return bool(RAILRADAR_API_KEY)

    @classmethod
    def trains_between(cls, from_station: str, to_station: str) -> Optional[list[dict]]:
        """Attempt to fetch trains between two station codes/names.

        Returns a list of {train_no, train_name, departs, arrives, duration} or None.
        """
        if not RAILRADAR_API_KEY:
            return None
        params = {"from": from_station, "to": to_station}
        for base in _BASE_CANDIDATES:
            for path in ("/trains/between", "/trains/search", "/between-stations"):
                try:
                    r = requests.get(f"{base}{path}", params=params, headers=cls._headers(), timeout=8)
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    trains = data.get("data") or data.get("trains") or data
                    if isinstance(trains, list) and trains:
                        out = []
                        for t in trains[:6]:
                            out.append({
                                "train_no": t.get("train_no") or t.get("number") or t.get("trainNumber"),
                                "train_name": t.get("train_name") or t.get("name") or t.get("trainName"),
                                "departs": t.get("from_time") or t.get("departure") or t.get("departs"),
                                "arrives": t.get("to_time") or t.get("arrival") or t.get("arrives"),
                                "duration": t.get("duration") or t.get("travel_time"),
                            })
                        return out
                except Exception:
                    continue
        return None

    @classmethod
    def search_station(cls, query: str) -> Optional[dict]:
        """Best-effort station lookup; returns {code, name} or None."""
        if not RAILRADAR_API_KEY or not query:
            return None
        for base in _BASE_CANDIDATES:
            for path in ("/stations/search", "/station", "/stations"):
                try:
                    r = requests.get(f"{base}{path}", params={"q": query, "query": query},
                                     headers=cls._headers(), timeout=8)
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    items = data.get("data") or data.get("stations") or data
                    if isinstance(items, list) and items:
                        s = items[0]
                        return {"code": s.get("code") or s.get("station_code"),
                                "name": s.get("name") or s.get("station_name")}
                except Exception:
                    continue
        return None
