"""
Neo4j connection manager. Singleton driver for the application.
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "tripgraph123")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver

def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None

def execute_query(cypher: str, parameters: dict = None) -> list[dict]:
    """Execute a Cypher query and return results as list of dicts."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, parameters or {})
        return [record.data() for record in result]

def execute_write(cypher: str, parameters: dict = None):
    """Execute a write Cypher query."""
    driver = get_driver()
    with driver.session() as session:
        session.run(cypher, parameters or {})
