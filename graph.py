from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import ResearchState
from nodes import (
    planner_node,
    search_node,
    writer_node,
    reviewer_node,
    publisher_node,
)

def route_after_review(state: ResearchState):

    if state["is_approved"]:
        return "publisher"
    
    if state["attempt"] < state["max_attempts"]:
        return "writer"
        
    return "end"


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("search", search_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("publisher", publisher_node)

    graph.set_entry_point("planner")
    
    graph.add_edge("planner", "search")
    graph.add_edge("search", "writer")
    graph.add_edge("writer", "reviewer")
    
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "writer": "writer",
            "publisher": "publisher",
            "end": END,
        },
    )
    
    graph.add_edge("publisher", END)

    # Interrupt after web search for manual source review
    return graph.compile(
        checkpointer=MemorySaver(),
        interrupt_after=["search"],
    )