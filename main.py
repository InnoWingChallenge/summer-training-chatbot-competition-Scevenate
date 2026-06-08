from dotenv import load_dotenv
import os
from typing import List
from app.app import generate_prompt
from openai import AzureOpenAI
import json

# ====================== LOAD ENVIRONMENT ======================
load_dotenv()

API_Key = os.getenv("AZURE_OPENAI_API_KEY")
API_ENDPOINT = os.getenv("AZURE_OPENAI_API_ENDPOINT")

if not API_Key or not API_ENDPOINT:
    raise RuntimeError("Missing Azure OpenAI credentials. Set AZURE_OPENAI_API_KEY in .env or environment.")

client = AzureOpenAI(
    api_key=API_Key,
    api_version="2025-01-01-preview",
    azure_endpoint=API_ENDPOINT,
)


# ====================== CORE RAG FUNCTION ======================
def rag_answer(question: str) -> str:
    """
    Input: A single question (string)
    Output: A single answer (string)
    """
    
    #Implement your chatbot logic here.
    prompt = generate_prompt(question)
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=prompt
    )
    return response.choices[0].message.content

# ====================== PUBLIC API FUNCTION ======================
def generate_rag_answers(questions: List[str]) -> List[str]:
    """
    Input: List of questions (strings)
    Output: zip of (question, answer) pairs
    
    Example usage:
        from rag import generate_rag_answers
        answers = generate_rag_answers([
            "What are the current SIGs in InnoWings?",
            "Tell me about recent Tech Talks in InnoAcademy."
        ])
        print(answers)
    """
    answers = []
    for question in questions:
        print(f"🤖 Answering: {question[:80]}{'...' if len(question) > 80 else ''}")
        answer = rag_answer(question)
        answers.append(answer)
    return zip(questions, answers)

if __name__ == "__main__":
    with open("questions.json", "r") as f:
        questions = json.load(f)
    answers = generate_rag_answers(questions)
    with open("rag_results.json", "w") as f:
        json.dump(list(answers), f, indent=2)