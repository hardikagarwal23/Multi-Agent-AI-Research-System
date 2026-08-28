import asyncio
import streamlit as st
from graph import build_graph

# Configure UI
st.set_page_config(page_title=" Multi-Agent AI Research Assistant", layout="wide")


if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session_01"

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

if "awaiting_review" not in st.session_state:
    st.session_state.awaiting_review = False


graph = st.session_state.graph
config = {"configurable": {"thread_id": st.session_state.thread_id}}

st.title("🧠 Multi-Agent AI Research Assistant")

topic = st.text_input("Enter Topic:")

# Step 1: Start

if st.button("Start", disabled=st.session_state.awaiting_review or not topic.strip()):
    initial_state = {
        "topic": topic.strip(),
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

   
    with st.spinner("Planning and searching the web..."):
        asyncio.run(graph.ainvoke(initial_state, config=config))


    st.session_state.awaiting_review = True
    st.rerun()
    
    
# Step 2: Source Review

if st.session_state.awaiting_review:
    current_state = graph.get_state(config)

    if current_state.next == ("writer",):
        st.subheader("Review Retrieved Sources")
        web_results = current_state.values.get("web_results", [])
        approved_results = []


        with st.form("source_review_form"):
            for source in web_results:
                preview = source["content"][:200] + "..." if len(source["content"]) > 200 else source["content"]
                keep = st.checkbox(
                    f"**{source['title']}**\n\n_{preview}_\n\n[Link]({source['url']})",
                    value=True,
                    key=f"chk_{source['id']}"
                )

                if keep:
                    approved_results.append(source)
                    
           
            if st.form_submit_button("Approve & Generate Report", type="primary"):
                # Update graph state with selected sources
                graph.update_state(config, {"web_results": approved_results}, as_node="search")
                st.session_state.awaiting_review = False

                with st.spinner("Drafting and reviewing report..."):
                    asyncio.run(graph.ainvoke(None, config=config))
                    
                st.rerun()


# Step 3: Final Output

final_state = graph.get_state(config).values
if final_state and final_state.get("attempt", 0) > 0:
    st.divider()

    is_approved = final_state.get("is_approved", False)

    if is_approved:
        st.success(f"Report completed successfully after {final_state['attempt']} attempts.")
        st.markdown(final_state.get("final_report", ""))
    else:
        st.error("Report failed quality review. Max attempts reached.")
        st.write("**Feedback:**", final_state.get("review_feedback", ""))


    # Display Sources
    sources = final_state.get("web_results", [])
    if sources:
        st.divider()
        st.subheader("Sources Used")
        for s in sources:
            st.markdown(f"[{s['id']}] [{s['title']}]({s['url']})")    
    