from pathlib import Path
from PIL import Image
from openai import AzureOpenAI
import os
import base64
from typing import List
import json
from dotenv import load_dotenv

load_dotenv()

APP_ROOT = Path(__file__).resolve().parent

API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
API_ENDPOINT = os.getenv("AZURE_OPENAI_API_ENDPOINT")

client = AzureOpenAI(
    api_key=API_KEY,
    api_version="2025-01-01-preview",
    azure_endpoint=API_ENDPOINT,
)


def describe_space(image1: Path, image2: Path) -> List[str]:
    with open(image1, "rb") as image:
        encoded1 = base64.b64encode(image.read()).decode("utf-8")
    with open(image2, "rb") as image:
        encoded2 = base64.b64encode(image.read()).decode("utf-8")
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "Please describe the space presented in the images in detail. Focus on factual details."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Image 1: {image1.name}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded1}"}},
                    {"type": "text", "text": f"Image 2: {image2.name}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded2}"}}
                ]
            }
        ]
    )
    return [choice.message.content for choice in response.choices]

def describe_poster(image: Path) -> List[str]:
    with open(image, "rb") as image:
        encoded = base64.b64encode(image.read()).decode("utf-8")
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "Please extract the information from the poster. Be faithful to the original details."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Image: {image.name}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
                ]
            }
        ]
    )
    return [choice.message.content for choice in response.choices]

documents = []

for image in (APP_ROOT / "etc" / "image\\physical").iterdir():
    documents.append({
        "url": f"{image.name}",
        "title": f"{image.name}",
        "texts": describe_space(image)
    })

for image in (APP_ROOT / "etc" / "image\\pitching").iterdir():
    documents.append({
        "url": f"{image.name.replace('\\', '/')}",
        "title": f"{image.name.replace('\\', '/').split('/')[-1]}",
        "texts": describe_poster(image)
    })

with open(APP_ROOT / "etc" / "data2.json", "w") as f:
    json.dump(documents, f, indent=2)