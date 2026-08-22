import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
load_dotenv()

def get_llm():
    provider=os.getenv("LLM_PROVIDER","groq")
    if provider =="groq":
        return ChatGroq(
            model="openai/gpt-oss-120b",
            api_key=os.getenv("GROQ_API_KEY")
        )
    else:
        raise ValueError("Unsupported")