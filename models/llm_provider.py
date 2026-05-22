import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
load_dotenv()
provider=os.getenv("LLM_PROVIDER","groq")
def get_llm():
    if provider =="groq":
        return ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )
    else:
        raise ValueError("Unsupported")