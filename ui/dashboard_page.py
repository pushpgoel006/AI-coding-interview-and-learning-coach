import pandas as pd
import streamlit as st

from services.analytics import (
    get_theory_average,
    get_theory_trend,
    get_score_by_topic,
    get_resume_fit_score,
    get_weakest_topics,
    get_readiness_score,
    get_dsa_average,
    get_dsa_topic_scores,
)
from services.dsa_service import list_attempts as list_dsa_attempts
from agents.recommender import generate_recommendation
from ui.sidebar import DOC_TYPE_LABELS


def _score_color(score: float, max_score: float) -> str:
    ratio = score / max_score if max_score else 0
    if ratio >= 0.7:
        return "green"
    if ratio >= 0.4:
        return "orange"
    return "red"


def _clear_practice_state(session_id: str) -> None:
    for key in (
        f"interview_pending_{session_id}",
        f"interview_thread_{session_id}",
        f"interview_state_{session_id}",
    ):
        st.session_state.pop(key, None)


def render_dashboard_page(session_id: str) -> None:
    st.subheader("Dashboard")

    readiness = get_readiness_score(session_id)
    theory_average = get_theory_average(session_id)
    resume_fit = get_resume_fit_score(session_id)
    trend = get_theory_trend(session_id)
    by_topic = get_score_by_topic(session_id)
    weakest = get_weakest_topics(session_id, n=3)
    dsa_average = get_dsa_average(session_id)
    dsa_topics = get_dsa_topic_scores(session_id)
    dsa_attempts = list_dsa_attempts(session_id)

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Readiness", f"{readiness}/100" if readiness is not None else "—")
            st.caption("60% theory · 40% resume fit")

        with col2:
            st.metric(
                "Theory Average",
                f"{theory_average:.1f}/10" if theory_average is not None else "—",
            )
            st.caption(f"{len(trend)} scored answer{'s' if len(trend) != 1 else ''}")

        with col3:
            st.metric("Resume Fit", f"{resume_fit}/100" if resume_fit is not None else "—")
            st.caption("Latest check" if resume_fit is not None else "Not checked yet")

        with col4:
            st.metric("DSA", f"{dsa_average:.1f}/10" if dsa_average is not None else "—")
            st.caption(
                f"{len(dsa_attempts)} attempt{'s' if len(dsa_attempts) != 1 else ''}"
                if dsa_attempts
                else "Not attempted yet"
            )

    if readiness is None and not trend and resume_fit is None and dsa_average is None:
        st.info(
            "Not enough data yet -- run a theory round or a resume check "
            "in this session to populate the dashboard."
        )
        return

    st.divider()

    col_trend, col_topics = st.columns(2)

    with col_trend:
        st.markdown("**Score Trend**")
        if trend:
            trend_df = pd.DataFrame(trend).sort_values("date")
            trend_df["Attempt"] = range(1, len(trend_df) + 1)
            trend_df = trend_df.set_index("Attempt")
            st.line_chart(trend_df[["score"]], height=260)
        else:
            st.caption("No scored answers yet -- run a theory round to see a trend.")

    with col_topics:
        st.markdown("**Score by Topic**")
        if by_topic:
            for entry in sorted(by_topic, key=lambda item: item["average_score"]):
                color = _score_color(entry["average_score"], 10)
                st.markdown(
                    f":{color}[**{entry['topic']}**] — {entry['average_score']:.1f}/10"
                )
                st.progress(min(entry["average_score"] / 10, 1.0))
        else:
            st.caption("No topics scored yet -- try the theory round with a topic set.")

    st.divider()

    st.markdown("**Weakest Topics — Practice These**")

    if not weakest:
        st.caption("Not enough topic data yet to identify weak spots.")
    else:
        for entry in weakest:
            topic = entry["topic"]
            score = entry["average_score"]

            with st.container(border=True):
                color = _score_color(score, 10)
                st.markdown(f":{color}[**{topic}**] — average {score:.1f}/10")
                st.progress(min(score / 10, 1.0))

                col_practice, col_advice = st.columns(2)

                with col_practice:
                    if st.button(
                        "Practice this",
                        key=f"practice_{session_id}_{topic}",
                        use_container_width=True,
                    ):
                        st.session_state[f"interview_topic_{session_id}"] = topic
                        _clear_practice_state(session_id)
                        st.success(
                            f"Topic set to '{topic}' -- switch to the "
                            "Theory Round tab and click 'New Question'."
                        )

                with col_advice:
                    advice_key = f"dashboard_advice_{session_id}_{topic}"
                    if st.button(
                        "Get recommendation",
                        key=f"recommend_{session_id}_{topic}",
                        use_container_width=True,
                    ):
                        try:
                            with st.spinner("Generating advice..."):
                                result = generate_recommendation(session_id, topic)
                        except Exception as error:
                            st.error(f"Something went wrong: {error}")
                        else:
                            st.session_state[advice_key] = result

                advice = st.session_state.get(f"dashboard_advice_{session_id}_{topic}")
                if advice:
                    st.info(advice["advice"])
                    if advice.get("sources"):
                        with st.expander(
                            f"Sources ({len(advice['sources'])})", expanded=False
                        ):
                            for source in advice["sources"]:
                                label = DOC_TYPE_LABELS.get(
                                    source["doc_type"], source["doc_type"]
                                )
                                st.caption(
                                    f"{source['file_name']} · page {source['page']} · "
                                    f"{label}"
                                )

    st.divider()

    st.markdown("**DSA Performance by Topic**")
    if dsa_topics:
        for entry in sorted(dsa_topics, key=lambda item: item["average_score"]):
            color = _score_color(entry["average_score"], 10)
            st.markdown(
                f":{color}[**{entry['topic']}**] — {entry['average_score']:.1f}/10"
            )
            st.progress(min(entry["average_score"] / 10, 1.0))
    else:
        st.caption("No DSA attempts yet -- try the DSA round with a topic set.")
