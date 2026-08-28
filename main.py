import asyncio
import traceback
from dotenv import load_dotenv
from graph import build_graph

load_dotenv()

async def main():
    graph = build_graph()

    topic = input("Enter topic: ").strip()
    if not topic:
        print("Topic cannot be empty.")
        return

    config = {
        "configurable": {
            "thread_id": "cli_session_1"
        }
    }

    initial_state = {
        "topic": topic,
        "search_queries": [],
        "web_results": [],
        "draft_text": "",
        "review_score": 0,
        "review_feedback": "",
        "review_suggestions": [],
        "is_approved": False,
        "attempt": 0,
        "max_attempts": 3,
        "final_report": "",
        "error_message": "",
    }

    try:
        print("\n[+] Running Planner and Search...")
        
        await graph.ainvoke(initial_state, config=config)
        state = graph.get_state(config)

        print(f"=> Found {len(state.values.get('web_results', []))} sources.")

        # Resume from the HITL checkpoint.
        await graph.ainvoke(None, config=config)
        
        final_state = graph.get_state(config).values

        print("REVIEWER EVALUATION")        
        print(f"Score: {final_state.get('review_score')}/10")
        print(f"Approved: {final_state.get('is_approved')}")
        print(f"Attempt: {final_state.get('attempt')}/{final_state.get('max_attempts')}")

        if not final_state.get("is_approved"):
            print("\nReviewer Feedback:")
            print(final_state.get("review_feedback", ""))

            queries = final_state.get("review_suggestions", [])
            if queries:
                print("\nSuggested Follow-up Queries:")
                for query in queries:
                    print(f"- {query}")

        else:
            print("FINAL REPORT")

            report = final_state.get("final_report", "")
            if report:
                print(report)
            else:
                print("Try again later.")

    except Exception:
        tb = traceback.format_exc()
        print("\nERROR")
        print(tb)

if __name__ == "__main__":
    asyncio.run(main())