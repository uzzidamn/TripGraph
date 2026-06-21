"""DuckDuckGo HTML search — scrape snippets for grounded price discovery.

The Instant Answer API only covers well-known entities. For arbitrary queries
like "flights from Chandigarh to Pune December price" we hit the HTML SERP
and pull the first ~5 result snippets. The LLM then extracts a fare band from
those snippets — far more grounded than pure LLM hallucination.

This is a respectful, low-volume scrape: one query per trip, cached by query.
We send a normal User-Agent and obey DDG's redirect chain.
"""
import re
from typing import Optional
from urllib.parse import urlencode

import requests

_URL = "https://html.duckduckgo.com/html/"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"

# Strip basic HTML tags from snippet text
_TAG = re.compile(r"<[^>]+>")
# DDG result snippet container
_RESULT = re.compile(
    r'<a[^>]+class="result__a"[^>]*>(?P<title>.*?)</a>.*?'
    r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
    re.DOTALL,
)


class DuckDuckGoSearchClient:
    @classmethod
    def snippets(cls, query: str, max_results: int = 5) -> Optional[list[dict]]:
        """Return [{title, snippet}, ...] for a query. None on failure."""
        if not (query or "").strip():
            return None
        try:
            r = requests.post(
                _URL,
                data=urlencode({"q": query}),
                headers={"User-Agent": _UA, "Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
                allow_redirects=True,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"  ⚠️  DDG search error for {query!r}: {e}")
            return None

        html = r.text
        out = []
        for m in _RESULT.finditer(html):
            title = _TAG.sub("", m.group("title")).strip()
            snippet = _TAG.sub("", m.group("snippet")).strip()
            # Decode common HTML entities cheaply
            for ent, ch in (("&amp;", "&"), ("&quot;", '"'), ("&#x27;", "'"), ("&#39;", "'"),
                            ("&lt;", "<"), ("&gt;", ">"), ("&nbsp;", " ")):
                title = title.replace(ent, ch)
                snippet = snippet.replace(ent, ch)
            if title or snippet:
                out.append({"title": title, "snippet": snippet})
            if len(out) >= max_results:
                break
        return out or None
