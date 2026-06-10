from dotenv import load_dotenv
import os
from pathlib import Path
from openai import AzureOpenAI
import chromadb
from typing import List, Dict
import json

APP_ROOT = Path(__file__).resolve().parent

load_dotenv()

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
API_ENDPOINT = os.getenv("AZURE_OPENAI_API_ENDPOINT")

agent_client = AzureOpenAI(
    api_key=API_KEY,
    api_version="2025-01-01-preview",
    azure_endpoint=API_ENDPOINT,
)

chroma_client = chromadb.PersistentClient(path=APP_ROOT / "chroma_db", settings=chromadb.Settings(allow_reset=True))
collection = chroma_client.get_collection("documents")

def search(prompt: str) -> List[Dict[str, str]]:
    results = collection.query(
        query_texts=[prompt],
        n_results=10
    )
    relevant_count = len([1 for distance in results["distances"][0] if float(distance) < 0.8])
    if relevant_count <= 4:
        relevant_count = 5
    relevant_documents = []
    for i in range(relevant_count):
        relevant_documents.append({
            "url": results["ids"][0][i],
            "title": results["documents"][0][i],
            "data": results["metadatas"][0][i]
        })
    return relevant_documents

def generate_prompt(user_prompt: str):
    system_prompt = "You're an ambassador of the HKU Innowing who knows all the details and ongoing events regarding the Innowing. Please answer the following question asked by the visitor. Try your best to give an correct answer."
    context_prompt = search(user_prompt)
    return [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        },
        {
            "role": "system",
            "content": "Context:\n" + json.dumps(context_prompt, ensure_ascii=False, indent=2)
        }
    ]
