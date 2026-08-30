import pandas as pd
import streamlit as st

from services.analytics import (
    get_theory_average,
    get_theory_trend,
    get_score_by_topic,
    get_resume_fit_score,
    get_weakest_topics,
    get_readiness_score,
)
from agents.recommender import generate_recommendation


def _score_badge(score: float, max_score: float) -> str:
    ratio = score / max_score if max_score else 0
    if ratio >= 0.7:
        return "🟢"
    if ratio >= 0.4:
        return "🟡"
    return "🔴"


def _clear_practice_state(session_id: str) -> None:
    for key in (
        f"interview_pending_{session_id}",
        f"interview_thread_{session_id}",
        f"interview_state_{session_id}",
    ):
        st.session_state.pop(key, None)


def render_dashboard_page(session_id: str) -> None:
    st.subheader("📊 Dashboard")

    readiness = get_readiness_score(session_id)
    theory_average = get_theory_average(session_id)
    resume_fit = get_resume_fit_score(session_id)
    trend = get_theory_trend(session_id)
    by_topic = get_score_by_topic(session_id)
    weakest = get_weakest_topics(session_id, n=3)

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("🎯 Readiness", f"{readiness}/100" if readiness is not None else "—")
            st.caption("60% theory · 40% resume fit")

        with col2:
            st.metric(
                "🎤 Theory Avg",
                f"{theory_average:.1f}/10" if theory_average is not None else "—",
            )
            st.caption(f"{len(trend)} scored answer{'s' if len(trend) != 1 else ''}")

        with col3:
            st.metric("🧾 Resume Fit", f"{resume_fit}/100" if resume_fit is not None else "—")
            st.caption("Latest check" if resume_fit is not None else "Not checked yet")

        with col4:
            st.metric("💻 DSA", "—")
            st.caption("Not built yet")

    if readiness is None and not trend and resume_fit is None:
        st.info(
            "Not enough data yet -- run a theory round or a resume check "
            "in this session to populate the dashboard."
        )
        return

    st.divider()

    col_trend, col_topics = st.columns(2)

    with col_trend:
        st.markdown("**📈 Score Trend**")
        if trend:
            trend_df = pd.DataFrame(trend).sort_values("date")
            trend_df["Attempt"] = range(1, len(trend_df) + 1)
            trend_df = trend_df.set_index("Attempt")
            st.line_chart(trend_df[["score"]], height=260)
        else:
            st.caption("No scored answers yet -- run a theory round to see a trend.")

    with col_topics:
        st.markdown("**📊 Score by Topic**")
        if by_topic:
            for entry in sorted(by_topic, key=lambda item: item["average_score"]):
                badge = _score_badge(entry["average_score"], 10)
                st.write(f"{badge} **{entry['topic']}** -- {entry['average_score']:.1f}/10")
                st.progress(min(entry["average_score"] / 10, 1.0))
        else:
            st.caption("No topics scored yet -- try the theory round with a topic set.")

    st.divider()

    st.markdown("**🎯 Weakest Topics -- Practice These**")

    if not weakest:
        st.caption("Not enough topic data yet to identify weak spots.")
    else:
        for entry in weakest:
            topic = entry["topic"]
            score = entry["average_score"]

            with st.container(border=True):
                st.write(f"{_score_badge(score, 10)} **{topic}** -- average {score:.1f}/10")
                st.progress(min(score / 10, 1.0))

                col_practice, col_advice = st.columns(2)

                with col_practice:
                    if st.button(
                        "🎯 Practice this",
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
                        "💡 Get recommendation",
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
                            f"📎 Sources ({len(advice['sources'])})", expanded=False
                        ):
                            for source in advice["sources"]:
                                st.caption(
                                    f"{source['file_name']} · page {source['page']} · "
                                    f"{source['doc_type']}"
                                )

    st.divider()

    with st.container(border=True):
        st.markdown("**💻 DSA Solve Rate**")
        st.caption(
            "Not available yet -- the DSA round is a separate module that "
            "hasn't been built for this project yet."
        )
