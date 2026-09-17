import asyncio
import os
from tavily import AsyncTavilyClient

from state import ResearchState
from schema import ReviewResult
from llm import get_llm

tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


async def planner_node(state: ResearchState):

    prompt = f"""
    Topic: {state["topic"]}
    Generate exactly 4 web search queries to research this topic.
    Return only the queries, one per line. Do not number them.
    """
    
    response = get_llm(temperature=0.2).invoke(prompt)
    queries = [
        line.strip().lstrip("123456789.- ")
        for line in str(response.content).splitlines()
        if line.strip()
    ]
    
    return {"search_queries": queries[:4] or [state["topic"]]}


async def search_node(state: ResearchState):
    """Executes the search queries concurrently."""
    async def fetch_results(query):
        result = await tavily.search(query=query, search_depth="advanced", max_results=3)
        return result.get("results", [])

    results = await asyncio.gather(*(fetch_results(q) for q in state["search_queries"]))
    
    sources = []
    seen_urls = set()
    
    for result_list in results:
        for res in result_list:
            url = res.get("url")
            if not url or url in seen_urls:
                continue
                
            seen_urls.add(url)
            sources.append({
                "id": len(sources) + 1,
                "title": res.get("title", "No Title"),
                "content": res.get("content", "")[:10000],
                "url": url,
            })
    

    return {"web_results": sources}


async def writer_node(state: ResearchState):

    attempt = state.get("attempt", 0) + 1
    
    sources_text = "\n\n".join(
        f"Source [{s['id']}]\nTitle: {s['title']}\nContent: {s['content']}"
        for s in state["web_results"]
    )
    
    feedback = state.get("review_feedback", "")
    feedback_prompt = f"Reviewer Feedback to fix:\n{feedback}" if feedback else ""

    prompt = f"""
    Topic: {state["topic"]}
    Sources: {sources_text}
    {feedback_prompt}

    Write detailed research notes. 
    Rules:
    - Only use information from the provided sources.
    - Cite claims using the source ID, e.g., [1].
    - Do not invent facts or statistics.
    - Address the reviewer feedback if provided.
    """
    
    response = get_llm().invoke(prompt)
    return {"draft_text": str(response.content).strip(), "attempt": attempt}


async def reviewer_node(state: ResearchState):

    sources_text = "\n\n".join(
        f"Source [{s['id']}]\nContent: {s['content']}"
        for s in state["web_results"]
    )
    
    prompt = f"""
    Topic: {state["topic"]}
    Approved Sources: {sources_text}
    Draft Notes: {state["draft_text"]}

    Evaluate the draft notes.
    1. Are all factual claims supported by the cited sources?
    2. Are citations used correctly?
    
    Approve only if the draft is factually accurate based on the sources.
    """
    
    evaluator = get_llm().with_structured_output(ReviewResult)
    result = evaluator.invoke(prompt)
    
    is_approved = result.is_approved and result.quality_score >= 7
    
    return {
        "review_score": result.quality_score,
        "review_feedback": result.feedback,
        "review_suggestions": result.followup_queries,
        "is_approved": is_approved,
    }


async def publisher_node(state: ResearchState):

    prompt = f"""
    Format the following research notes into a final Markdown report.
    Include a title, an Executive Summary, and structured sections.
    Keep citation markers like [1]. Do not add new facts.

    Topic: {state["topic"]}
    Notes: {state["draft_text"]}
    """
    
    try:
        response = get_llm(temperature=0.2).invoke(prompt)
        report = str(response.content).strip()
        return {"final_report": report, "error_message": ""}
        
    except Exception as e:
        return {"final_report": "", "error_message": f"Formatting failed: {str(e)}"}