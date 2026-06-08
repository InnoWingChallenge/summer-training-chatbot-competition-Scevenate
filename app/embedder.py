import chromadb
from pathlib import Path
import json

APP_ROOT = Path(__file__).resolve().parent

CHROMA_DB_DIR = APP_ROOT / "chroma_db"

client = chromadb.PersistentClient(path=CHROMA_DB_DIR, settings=chromadb.Settings(allow_reset=True))

client.reset()

collection = client.create_collection("documents")

documents = []

with open(APP_ROOT / "data" / "data.json", "r") as f:
    documents.extend(json.load(f))

with open(APP_ROOT / "etc" / "data.json", "r") as f:
    documents.extend(json.load(f))

collection.add(
    ids=[document["url"] for document in documents],
    documents=[document["title"] for document in documents],
    metadatas=[{"texts": document["texts"] if document["texts"] else ["None"]} for document in documents],
)
