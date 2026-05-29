from agents.question_generator import stream_question

for chunk in stream_question(
    "Python backend developer"
):
    print(chunk, end="", flush=True)