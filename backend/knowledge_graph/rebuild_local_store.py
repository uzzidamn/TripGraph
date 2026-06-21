"""Rebuild backend/data/local_kg_store.json from scratch using only seed files.

Use this when API hallucinations have polluted the cache (e.g. a wrong geocode
created a city node with bad coordinates).

Usage:
    PYTHONPATH=. python -m backend.knowledge_graph.rebuild_local_store
"""
from backend.knowledge_graph.connection import rebuild_local_store_from_seeds


if __name__ == "__main__":
    store = rebuild_local_store_from_seeds()
    print("\nCounts after rebuild:")
    for k, v in store.items():
        print(f"  {k:12s} {len(v)}")
