import streamlit as st

from graphs.resume_graph import resume_graph
from services.resume_service import get_latest_review


def _render_verdict_columns(verdicts: list[dict]) -> None:
    demonstrated = [v for v in verdicts if v["verdict"] == "clearly demonstrated"]
    partial = [v for v in verdicts if v["verdict"] == "partially demonstrated"]
    missing = [v for v in verdicts if v["verdict"] == "not demonstrated"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**✅ Clearly demonstrated ({len(demonstrated)})**")
        for verdict in demonstrated:
            st.markdown(f"- {verdict['requirement']}")
            if verdict.get("evidence"):
                st.caption(f"📎 {verdict['evidence']}")

    with col2:
        st.markdown(f"**🟡 Partially demonstrated ({len(partial)})**")
        for verdict in partial:
            st.markdown(f"- {verdict['requirement']}")
            if verdict.get("evidence"):
                st.caption(f"📎 {verdict['evidence']}")

    with col3:
        st.markdown(f"**❌ Not demonstrated ({len(missing)})**")
        for verdict in missing:
            st.markdown(f"- {verdict['requirement']}")


def _render_matched_missing(matched_skills: list[str], missing_skills: list[str]) -> None:
    st.caption(
        "Showing a previously saved review -- evidence lines are only shown "
        "right after running the check. Run it again to see them."
    )
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**✅ Matched ({len(matched_skills)})**")
        for skill in matched_skills:
            st.markdown(f"- {skill}")

    with col2:
        st.markdown(f"**❌ Missing ({len(missing_skills)})**")
        for skill in missing_skills:
            st.markdown(f"- {skill}")


def _render_review(review: dict) -> None:
    if "error" in review:
        st.warning(review["error"])
        return

    st.metric("Overall Fit Score", f"{review['overall_score']}/100")

    if "verdicts" in review:
        _render_verdict_columns(review["verdicts"])
    else:
        _render_matched_missing(review["matched_skills"], review["missing_skills"])

    if review.get("suggestions"):
        st.markdown("**Suggestions**")
        st.write(review["suggestions"])


def render_resume_page(session_id: str) -> None:
    st.subheader("🧾 Resume Check")

    existing_review = get_latest_review(session_id)
    if existing_review:
        st.caption(f"Last checked: {existing_review['created_at']}")
        _render_review(existing_review)
        st.divider()

    if st.button("🧾 Run Resume Check", use_container_width=True):
        try:
            with st.spinner("Analyzing resume against the job description..."):
                result = resume_graph.invoke({"session_id": session_id})
        except Exception as error:
            st.error(f"Something went wrong running the check: {error}")
            return

        _render_review(result["review"])
