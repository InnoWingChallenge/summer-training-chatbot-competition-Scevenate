from pathlib import Path
from bs4 import BeautifulSoup
import json

APP_ROOT = Path(__file__).resolve().parent


documents = []

for html in (APP_ROOT / "data" / "text\\html; charset=UTF-8").iterdir():
    with open(html, "r") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    url = Path(f.name).name.replace("\\", "/")
    title = soup.title.string if soup.title else ""
    texts = [line.strip() for line in soup.get_text(separator="\n", strip=True).splitlines() if len(line.strip()) > 20 and not line.strip().startswith("Copyright")]
    # links = list(set([a.get('href')[8:] for a in soup.find_all('a', href=True) if not a.get('href').startswith("#") and a.get('href')[8:12] == "inno"]))
    # images = list(set([img.get('src')[8:] for img in soup.find_all('img', src=True) if img.get('src')[8:12] == "inno"]))
    documents.append({
        "url": url,
        "title": title,
        "texts": texts,
#         "links": links,
#         "images": images
    })

with open(APP_ROOT / "data" / "data.json", "w") as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)
