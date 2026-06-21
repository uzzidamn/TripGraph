"""
Maps origin city → (currency_code, symbol, approx_usd_rate).
Used to display itinerary costs in the traveller's home currency.
"""

# (currency_code, symbol, 1 unit = X INR)
_CITY_CURRENCY: dict[str, tuple[str, str, float]] = {
    # India — all map to INR
    "gurugram": ("INR", "₹", 1.0),
    "gurgaon":  ("INR", "₹", 1.0),
    "delhi":    ("INR", "₹", 1.0),
    "new delhi":("INR", "₹", 1.0),
    "noida":    ("INR", "₹", 1.0),
    "mumbai":   ("INR", "₹", 1.0),
    "pune":     ("INR", "₹", 1.0),
    "bangalore":("INR", "₹", 1.0),
    "bengaluru":("INR", "₹", 1.0),
    "chennai":  ("INR", "₹", 1.0),
    "hyderabad":("INR", "₹", 1.0),
    "kolkata":  ("INR", "₹", 1.0),
    "ahmedabad":("INR", "₹", 1.0),
    "jaipur":   ("INR", "₹", 1.0),
    "lucknow":  ("INR", "₹", 1.0),
    "chandigarh":("INR","₹", 1.0),
    "kochi":    ("INR", "₹", 1.0),
    "surat":    ("INR", "₹", 1.0),
    "indore":   ("INR", "₹", 1.0),
    "bhopal":   ("INR", "₹", 1.0),
    "nagpur":   ("INR", "₹", 1.0),
    "goa":      ("INR", "₹", 1.0),

    # South-East Asia
    "bangkok":    ("THB", "฿",   0.24),
    "phuket":     ("THB", "฿",   0.24),
    "singapore":  ("SGD", "S$", 63.0),
    "kuala lumpur":("MYR","RM",  18.0),
    "bali":       ("IDR", "Rp",  0.0052),
    "jakarta":    ("IDR", "Rp",  0.0052),
    "ho chi minh":("VND", "₫",  0.0033),
    "hanoi":      ("VND", "₫",  0.0033),
    "manila":     ("PHP", "₱",   1.5),

    # East Asia
    "tokyo":      ("JPY", "¥",   0.56),
    "osaka":      ("JPY", "¥",   0.56),
    "seoul":      ("KRW", "₩",   0.063),
    "beijing":    ("CNY", "¥",  11.6),
    "shanghai":   ("CNY", "¥",  11.6),
    "hong kong":  ("HKD", "HK$", 10.8),

    # Middle East
    "dubai":      ("AED", "د.إ", 22.9),
    "abu dhabi":  ("AED", "د.إ", 22.9),
    "doha":       ("QAR", "﷼",   23.1),
    "riyadh":     ("SAR", "﷼",   22.4),

    # Europe
    "london":     ("GBP", "£",  107.0),
    "paris":      ("EUR", "€",   90.0),
    "amsterdam":  ("EUR", "€",   90.0),
    "berlin":     ("EUR", "€",   90.0),
    "rome":       ("EUR", "€",   90.0),
    "barcelona":  ("EUR", "€",   90.0),
    "zurich":     ("CHF", "Fr",  94.0),

    # Americas — full names and common abbreviations
    "new york":      ("USD", "$",   84.0),
    "new york city": ("USD", "$",   84.0),
    "nyc":           ("USD", "$",   84.0),
    "ny":            ("USD", "$",   84.0),
    "los angeles":   ("USD", "$",   84.0),
    "la":            ("USD", "$",   84.0),
    "san francisco": ("USD", "$",   84.0),
    "sf":            ("USD", "$",   84.0),
    "chicago":       ("USD", "$",   84.0),
    "houston":       ("USD", "$",   84.0),
    "miami":         ("USD", "$",   84.0),
    "boston":        ("USD", "$",   84.0),
    "seattle":       ("USD", "$",   84.0),
    "las vegas":     ("USD", "$",   84.0),
    "dallas":        ("USD", "$",   84.0),
    "washington":    ("USD", "$",   84.0),
    "dc":            ("USD", "$",   84.0),
    "toronto":       ("CAD", "CA$", 61.0),
    "vancouver":     ("CAD", "CA$", 61.0),
    "montreal":      ("CAD", "CA$", 61.0),
    "sao paulo":     ("BRL", "R$",  15.0),
    "rio de janeiro":("BRL", "R$",  15.0),

    # Oceania
    "sydney":     ("AUD", "A$",  54.0),
    "melbourne":  ("AUD", "A$",  54.0),
    "brisbane":   ("AUD", "A$",  54.0),
    "perth":      ("AUD", "A$",  54.0),
    "adelaide":   ("AUD", "A$",  54.0),
    "canberra":   ("AUD", "A$",  54.0),
    "gold coast": ("AUD", "A$",  54.0),
    "auckland":   ("NZD", "NZ$", 50.0),
    "wellington": ("NZD", "NZ$", 50.0),

    # Russia / CIS
    "moscow":     ("RUB", "₽",   0.93),
    "st petersburg": ("RUB", "₽", 0.93),

    # South Asia
    "colombo":    ("LKR", "Rs",  0.26),
    "dhaka":      ("BDT", "৳",   0.70),
    "kathmandu":  ("NPR", "Rs",  0.63),
    "karachi":    ("PKR", "Rs",  0.30),

    # Africa
    "nairobi":    ("KES", "Ksh", 0.65),
    "cairo":      ("EGP", "E£",  1.72),
    "cape town":  ("ZAR", "R",   4.60),
    "johannesburg": ("ZAR", "R", 4.60),
}

_DEFAULT = ("INR", "₹", 1.0)

# Country code → currency fallback (used when city isn't in _CITY_CURRENCY)
_COUNTRY_CURRENCY: dict[str, tuple[str, str, float]] = {
    "IN": ("INR", "₹",    1.0),
    "US": ("USD", "$",   84.0),
    "CA": ("CAD", "CA$", 61.0),
    "GB": ("GBP", "£",  107.0),
    "EU": ("EUR", "€",   90.0),
    "DE": ("EUR", "€",   90.0),
    "FR": ("EUR", "€",   90.0),
    "AU": ("AUD", "A$",  54.0),
    "NZ": ("NZD", "NZ$", 50.0),
    "JP": ("JPY", "¥",    0.56),
    "KR": ("KRW", "₩",   0.063),
    "CN": ("CNY", "¥",   11.6),
    "SG": ("SGD", "S$",  63.0),
    "TH": ("THB", "฿",    0.24),
    "AE": ("AED", "د.إ", 22.9),
    "MY": ("MYR", "RM",  18.0),
    "ID": ("IDR", "Rp",   0.0052),
    "VN": ("VND", "₫",   0.0033),
    "PH": ("PHP", "₱",    1.5),
    "RU": ("RUB", "₽",    0.93),
    "BR": ("BRL", "R$",  15.0),
    "MX": ("MXN", "MX$",  4.8),
    "ZA": ("ZAR", "R",    4.6),
    "EG": ("EGP", "E£",   1.72),
    "KE": ("KES", "Ksh",  0.65),
}


def get_currency(origin: str) -> tuple[str, str, float]:
    """Return (currency_code, symbol, inr_rate) for the given origin city.

    Resolution order:
      1. Exact city match
      2. Prefix city match (handles partial / misspelled names)
      3. Country-code fallback via web_enricher's _resolve_country()
      4. Default INR
    """
    key = (origin or "").lower().strip()

    if key in _CITY_CURRENCY:
        return _CITY_CURRENCY[key]

    for city, val in _CITY_CURRENCY.items():
        if city.startswith(key) or key.startswith(city):
            return val

    # Country-based fallback — covers any state, region, or unlisted city
    try:
        from backend.agents.nodes.web_enricher import _resolve_country
        country = _resolve_country(key)
        if country and country in _COUNTRY_CURRENCY:
            return _COUNTRY_CURRENCY[country]
    except Exception:
        pass

    return _DEFAULT


def inr_to_currency(amount_inr: float, inr_rate: float) -> int:
    """Convert an INR amount to the target currency using inr_rate.

    inr_rate: 1 unit of target = inr_rate INR  →  target = inr / inr_rate
    """
    if not inr_rate or inr_rate <= 0:
        return int(amount_inr)
    return int(round(amount_inr / inr_rate))
