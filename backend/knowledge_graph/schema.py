"""
Create Neo4j constraints and indexes for the knowledge graph.
Run once to initialize the database schema.
"""
from backend.knowledge_graph.connection import execute_write

SCHEMA_QUERIES = [
    # Uniqueness constraints
    "CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.route_id IS UNIQUE",
    "CREATE CONSTRAINT hotel_id IF NOT EXISTS FOR (h:Hotel) REQUIRE h.hotel_id IS UNIQUE",
    "CREATE CONSTRAINT activity_id IF NOT EXISTS FOR (a:Activity) REQUIRE a.activity_id IS UNIQUE",
    "CREATE CONSTRAINT restaurant_id IF NOT EXISTS FOR (r:Restaurant) REQUIRE r.restaurant_id IS UNIQUE",
    "CREATE CONSTRAINT transport_id IF NOT EXISTS FOR (t:TransportOption) REQUIRE t.transport_id IS UNIQUE",
    "CREATE CONSTRAINT waypoint_id IF NOT EXISTS FOR (w:Waypoint) REQUIRE w.waypoint_id IS UNIQUE",
    "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",

    # Performance indexes
    "CREATE INDEX city_type IF NOT EXISTS FOR (c:City) ON (c.type)",
    "CREATE INDEX hotel_tier IF NOT EXISTS FOR (h:Hotel) ON (h.tier)",
    "CREATE INDEX hotel_dest IF NOT EXISTS FOR (h:Hotel) ON (h.destination)",
    "CREATE INDEX activity_category IF NOT EXISTS FOR (a:Activity) ON (a.category)",
    "CREATE INDEX transport_tier IF NOT EXISTS FOR (t:TransportOption) ON (t.tier)",
]

def create_schema():
    for query in SCHEMA_QUERIES:
        try:
            execute_write(query)
        except Exception as e:
            print(f"Schema query warning: {e}")
    print("✅ Neo4j schema created/verified")

if __name__ == "__main__":
    create_schema()
