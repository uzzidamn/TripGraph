"""DuckDuckGo Instant Answer API client.

Free, no API key needed. Returns the "AbstractText" (Wikipedia-style summary)
+ "RelatedTopics" for a search query. We use it to enrich destination /
hotel / activity nodes with additional context the KG and LLM don't have.

Endpoint: https://api.duckduckgo.com/?q=<query>&format=json&no_html=1&skip_disambig=1

Note: the Instant Answer API is quite sparse — only well-known entities have
an Abstract. For everything else we fall back to RelatedTopics' first entry.
"""
from typing import Optional
import requests


class DuckDuckGoClient:
    BASE_URL = "https://api.duckduckgo.com/"

    @classmethod
    def search(cls, query: str, max_related: int = 3) -> Optional[dict]:
        """Return {abstract, source_url, image, related_topics: [...] } or None.

        Result shape (frozen — UI relies on this):
            {
              "abstract":       str | None,    # the short summary
              "source_url":     str | None,    # canonical Wikipedia / source link
              "image":          str | None,    # thumbnail url (if any)
              "related_topics": [               # 0-N related entities
                  {"text": str, "url": str | None}, ...
              ],
              "query":          str            # echoed
            }
        """
        if not (query or "").strip():
            return None
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
            "t": "tripgraph",   # required by ToS — identifies the client
        }
        try:
            r = requests.get(cls.BASE_URL, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  ⚠️  DuckDuckGo error for {query!r}: {e}")
            return None

        abstract = (data.get("AbstractText") or "").strip() or None
        source_url = (data.get("AbstractURL") or "").strip() or None
        image = (data.get("Image") or "").strip() or None

        related = []
        for item in (data.get("RelatedTopics") or [])[:max_related * 2]:
            # Some entries are dicts with Text+FirstURL, others are categories
            # with a "Topics" list — skip those.
            text = (item.get("Text") or "").strip()
            url = (item.get("FirstURL") or "").strip()
            if not text:
                continue
            related.append({"text": text, "url": url or None})
            if len(related) >= max_related:
                break

        # If we got nothing useful, return None so the agent can skip caching.
        if not abstract and not related:
            return None

        return {
            "abstract": abstract,
            "source_url": source_url,
            "image": image,
            "related_topics": related,
            "query": query,
        }
