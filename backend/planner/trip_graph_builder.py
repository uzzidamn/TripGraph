"""
Builds a trip graph (DAG) from the retrieved travel data.
Each node is a trip event (departure, stop, hotel, activity, return).
Each edge carries cost, duration, and constraints.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TripNode:
    node_id: str
    node_type: str  # origin, waypoint, hotel, activity, restaurant, return
    name: str
    day: int
    time_window: tuple[str, str] | None = None  # (earliest_start, latest_start)
    duration_minutes: int = 0
    cost_per_person: float = 0
    lat: float = 0.0
    lng: float = 0.0
    is_mandatory: bool = True
    is_flexible: bool = True
    data: dict = field(default_factory=dict)  # raw entity data


@dataclass
class TripEdge:
    from_node: str
    to_node: str
    mode: str  # drive, walk, wait
    duration_minutes: int = 0
    cost: float = 0
    distance_km: float = 0


@dataclass
class TripGraph:
    nodes: dict[str, TripNode] = field(default_factory=dict)
    edges: list[TripEdge] = field(default_factory=list)
    adjacency: dict[str, list[str]] = field(default_factory=dict)

    def add_node(self, node: TripNode):
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []

    def add_edge(self, edge: TripEdge):
        self.edges.append(edge)
        if edge.from_node not in self.adjacency:
            self.adjacency[edge.from_node] = []
        self.adjacency[edge.from_node].append(edge.to_node)

    def get_ordered_nodes(self) -> list[TripNode]:
        """Topological sort of the DAG."""
        # Simple: return nodes sorted by day and time
        return sorted(self.nodes.values(), key=lambda n: (n.day, n.time_window[0] if n.time_window else "00:00"))


def build_trip_graph(route: dict, transport: dict, hotel: dict,
                     activities: list[dict], restaurants: list[dict],
                     waypoints: list[dict], constraints: dict) -> TripGraph:
    """
    Construct a trip DAG from selected entities.
    This is the core graph construction logic.
    """
    graph = TripGraph()
    group_size = constraints.get("group_size", 4)

    # Day 1: Origin → Waypoints → Destination → Hotel → Activities → Dinner
    graph.add_node(TripNode(
        node_id="origin",
        node_type="origin",
        name=route.get("origin", "Gurugram"),
        day=1,
        time_window=("05:00", "07:00"),
        lat=constraints.get("origin_lat", 28.4595),
        lng=constraints.get("origin_lng", 77.0266),
    ))

    # Add waypoints (highway stops)
    for i, wp in enumerate(waypoints):
        graph.add_node(TripNode(
            node_id=f"waypoint_{i}",
            node_type="waypoint",
            name=wp.get("name", f"Stop {i+1}"),
            day=1,
            duration_minutes=wp.get("typical_stop_minutes", 30),
            cost_per_person=0,
            lat=wp.get("lat", 0),
            lng=wp.get("lng", 0),
            is_mandatory=False,
            data=wp,
        ))

    # Hotel check-in
    graph.add_node(TripNode(
        node_id="hotel_checkin",
        node_type="hotel",
        name=hotel.get("name", "Hotel"),
        day=1,
        time_window=(hotel.get("checkin_time", "14:00"), "16:00"),
        duration_minutes=90,  # rest time
        cost_per_person=hotel.get("price_per_night", 0) / group_size,
        lat=hotel.get("lat", 0),
        lng=hotel.get("lng", 0),
        data=hotel,
    ))

    # Activities
    for i, act in enumerate(activities):
        graph.add_node(TripNode(
            node_id=f"activity_{i}",
            node_type="activity",
            name=act.get("name", f"Activity {i+1}"),
            day=1 if i == 0 else 2,  # Spread across days
            duration_minutes=act.get("duration_minutes", 120),
            cost_per_person=act.get("cost_per_person", 0),
            lat=act.get("lat", 0),
            lng=act.get("lng", 0),
            is_mandatory="must_include" in str(constraints.get("must_include", [])),
            data=act,
        ))

    # Meals
    for i, rest in enumerate(restaurants):
        meal_type = rest.get("meal_types", ["lunch"])[0] if rest.get("meal_types") else "meal"
        graph.add_node(TripNode(
            node_id=f"meal_{i}",
            node_type="restaurant",
            name=rest.get("name", f"Meal {i+1}"),
            day=1 if i < 2 else 2,
            duration_minutes=rest.get("avg_duration_minutes", 60),
            cost_per_person=rest.get("avg_cost_per_person", 0),
            lat=rest.get("lat", 0),
            lng=rest.get("lng", 0),
            is_mandatory=False,
            is_flexible=True,
            data=rest,
        ))

    # Return
    graph.add_node(TripNode(
        node_id="return",
        node_type="return",
        name=f"Return to {route.get('origin', 'Gurugram')}",
        day=2,
        duration_minutes=route.get("base_drive_minutes", 300),
        lat=constraints.get("origin_lat", 28.4595),
        lng=constraints.get("origin_lng", 77.0266),
    ))

    # Build edges (sequential for now — you can add more complex routing later)
    ordered = graph.get_ordered_nodes()
    for i in range(len(ordered) - 1):
        graph.add_edge(TripEdge(
            from_node=ordered[i].node_id,
            to_node=ordered[i+1].node_id,
            mode=transport.get("mode", "cab"),
            duration_minutes=30,  # estimated transition time
        ))

    return graph
