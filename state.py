from typing import TypedDict, List, Dict

class ResearchState(TypedDict):
    topic: str    
    search_queries: List[str]
    web_results: List[Dict]
    draft_text: str
    review_score: int
    review_feedback: str
    review_suggestions: List[str]
    is_approved: bool
    attempt: int
    max_attempts: int
    final_report: str
    error_message: str