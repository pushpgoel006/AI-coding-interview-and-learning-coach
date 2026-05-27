import streamlit as st
import requests
st.title("AI interview Assistant")
jd=st.text_area("Enter Job Description ")
if(st.button)("Generate Question"):
        with st.spinner("Generating response"):
            response = requests.post(
            "http://127.0.0.1:8000/generate-question",
            json={"jd": jd}
            )
            data= response.json()
            st.subheader("Generated Question")
            st.write(data["question"])
            st.session_state["session_id"] = data["session_id"]
            
answer = st.text_area("Enter Your Answer")
if(st.button)("Evaluate Question"):
        with st.spinner("Evaluating response"):
            response=requests.post(
            "http://127.0.0.1:8000/evaluate-answer",
            json={
                "session_id": st.session_state["session_id"],
                "answer": answer
            }
            )
            result=response.json()
            st.subheader("Evaluation")
            evaluation = result["evaluation"]
            st.success(f"Score: {evaluation['score']}/10")

            st.write("### Strengths")
            st.write(evaluation["strengths"])

            st.write("### Weaknesses")
            st.write(evaluation["weaknesses"])

            st.write("### Ideal Answer")
            st.write(evaluation["ideal_answer"])

        