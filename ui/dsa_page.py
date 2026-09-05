import streamlit as st

from graphs.dsa_graph import dsa_graph

TOPIC_LABELS = {
    "array": "Array",
    "hash-table": "Hash Table",
    "two-pointers": "Two Pointers",
    "dynamic-programming": "Dynamic Programming",
    "binary-search": "Binary Search",
    "tree": "Tree",
    "graph": "Graph",
    "linked-list": "Linked List",
    "stack": "Stack",
    "greedy": "Greedy",
    "backtracking": "Backtracking",
    "sorting": "Sorting",
    "string": "String",
    "heap-priority-queue": "Heap / Priority Queue",
    "sliding-window": "Sliding Window",
}
TOPIC_VALUES = {label: value for value, label in TOPIC_LABELS.items()}

LANGUAGES = ["python", "javascript", "java", "cpp"]


def render_dsa_page(session_id: str) -> None:
    st.subheader("DSA Round")

    problem_key = f"dsa_problem_{session_id}"
    result_key = f"dsa_result_{session_id}"

    col1, col2 = st.columns(2)
    with col1:
        topic_label = st.selectbox(
            "Topic", list(TOPIC_LABELS.values()), key=f"dsa_topic_{session_id}"
        )
    with col2:
        difficulty = st.selectbox(
            "Difficulty", ["easy", "medium", "hard"], key=f"dsa_difficulty_{session_id}"
        )

    topic = TOPIC_VALUES[topic_label]

    if st.button("New Problem", use_container_width=True):
        try:
            with st.spinner("Fetching a problem..."):
                result = dsa_graph.invoke(
                    {"session_id": session_id, "topic": topic, "difficulty": difficulty}
                )
        except Exception as error:
            st.error(f"Something went wrong fetching a problem: {error}")
        else:
            st.session_state[problem_key] = result
            st.session_state.pop(result_key, None)

    problem = st.session_state.get(problem_key)

    if not problem:
        st.info("Click 'New Problem' to get started.")
        return

    st.markdown(f"**{problem['title']}** ({problem.get('difficulty', difficulty)})")
    st.markdown(problem["statement"])
    st.markdown(
        f"[View on LeetCode](https://leetcode.com/problems/{problem['slug']}/) -- via LeetCode"
    )

    if problem.get("source") == "fallback":
        st.caption(
            "Live fetch from LeetCode wasn't available -- showing a local problem instead."
        )

    st.divider()

    language = st.selectbox("Language", LANGUAGES, key=f"dsa_language_{session_id}")
    code = st.text_area(
        "Your solution",
        height=250,
        key=f"dsa_code_{session_id}_{problem['slug']}",
    )

    if st.button("Submit Solution", use_container_width=True):
        if not code.strip():
            st.warning("Write some code before submitting.")
        else:
            try:
                with st.spinner("Evaluating your solution..."):
                    result = dsa_graph.invoke(
                        {
                            **problem,
                            "session_id": session_id,
                            "topic": topic,
                            "difficulty": difficulty,
                            "code": code,
                            "language": language,
                        }
                    )
            except Exception as error:
                st.error(f"Something went wrong evaluating that: {error}")
            else:
                evaluation = result.get("evaluation") or {}
                if "error" in evaluation:
                    st.error(evaluation["error"])
                else:
                    st.session_state[result_key] = evaluation

    evaluation = st.session_state.get(result_key)
    if evaluation:
        st.divider()
        st.metric("Score", f"{evaluation.get('score', 0)}/10")
        st.markdown("**Correctness**")
        st.write(evaluation.get("correctness_notes", ""))
        st.markdown("**Complexity**")
        st.write(evaluation.get("complexity_notes", ""))
        st.markdown("**Suggestions**")
        st.write(evaluation.get("suggestions", ""))
