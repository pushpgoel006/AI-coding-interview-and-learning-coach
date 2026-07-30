import streamlit as st
import requests
st.title("AI interview Assistant")
jd=st.text_area("Enter Job Description ")
if "followup_id" not in st.session_state:
    st.session_state["followup_id"] = None

if "followup_question" not in st.session_state:
    st.session_state["followup_question"] = None

if "followup_number" not in st.session_state:
    st.session_state["followup_number"] = None    
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

#this button is for treaming purposes
if st.button("Generate Question (Streaming Demo)"):

    session_response=requests.post(
         "http://127.0.0.1:8000/create-session",
         json={"jd":jd}
    )
    st.write(session_response.status_code)
    st.write(session_response.json())
    session_id = session_response.json()["session_id"]
    st.session_state["session_id"] = session_id
    placeholder = st.empty()
    response = requests.post(
        "http://127.0.0.1:8000/stream-question",
        json={
             "session_id":session_id,
             "jd": jd
             },
        stream=True
    )

    streamed_text = ""

    for chunk in response.iter_content(
        chunk_size=None,
        decode_unicode=True
    ):

        streamed_text += chunk

        placeholder.markdown(streamed_text)
            
answer = st.text_area("Enter Your Answer")
if st.button("Evaluate Answer"):

    if st.session_state["session_id"] is None:
        st.error("Generate a question first.")

    else:

        with st.spinner("Evaluating response"):

            response = requests.post(
                "http://127.0.0.1:8000/evaluate-answer",
                json={
                    "session_id": st.session_state["session_id"],
                    "answer": answer
                }
            )

            result = response.json()

            if "error" in result:
                st.error(result["error"])
            else:
                evaluation = result["evaluation"]

                st.success(f"Score: {evaluation['score']}/10")

                st.write("### Strengths")
                st.write(evaluation["strengths"])

                st.write("### Weaknesses")
                st.write(evaluation["weaknesses"])

                st.write("### Ideal Answer")
                st.write(evaluation["ideal_answer"])

if st.button("Stream Evaluation"):
    response = requests.post(
    "http://127.0.0.1:8000/stream-evaluation",
    json={
        "session_id": st.session_state["session_id"],
        "answer": answer
    },
    stream=True
    )
    placeholder = st.empty()

    evaluation_text = ""

    for chunk in response.iter_content(
        chunk_size=None,
        decode_unicode=True
    ):

        evaluation_text += chunk

        placeholder.markdown(evaluation_text)

if st.button("Generate FollowUp"):
    response= requests.post(
        "http://127.0.0.1:8000/followup-question",
        json={
            "session_id":st.session_state["session_id"]
        }
    )
    data = response.json()
    st.session_state["followup_id"]=data["followup_id"]
    st.session_state["followup_question"] = data["question"]
    st.session_state["followup_number"] = data["followup_number"]

if "followup_question" in st.session_state:

    st.subheader(
        f"Followup Question #{st.session_state['followup_number']}"
    )

    st.write(
        st.session_state["followup_question"]
    )

    followup_answer = st.text_area(
        "Enter Followup Answer"
    )

    if st.button("Evaluate Followup"):
        

        response = requests.post(
            "http://127.0.0.1:8000/stream-followup-evaluation",
            json={
                "followup_id": st.session_state["followup_id"],
                "answer": followup_answer
            },
            stream=True
        )
        
        st.write("Response Text:")

        placeholder = st.empty()

        evaluation_text = ""

        for chunk in response.iter_content(
            chunk_size=None,
            decode_unicode=True
        ):
            evaluation_text += chunk

            placeholder.markdown(
                evaluation_text
            )

        