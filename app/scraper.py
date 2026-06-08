import httpx
import asyncio
from bs4 import BeautifulSoup
import urllib.parse
from collections import deque
from pathlib import Path

type netloc = str
type path = str

APP_ROOT = Path(__file__).resolve().parent

NON_NAVIGABLE_HREF_PREFIXES = (
    "javascript:",
    "mailto:",
    "tel:",
    "sms:",
    "data:",
)

class Page:
    def __init__(self, netloc: netloc, path: path):
        self.netloc: netloc = netloc
        self.path: path = path
    
    @classmethod
    def from_relative(cls, page: "Page", href: str):
        if not href:
            return None
        lowered = href.lower()
        if not lowered or lowered.startswith(NON_NAVIGABLE_HREF_PREFIXES) or lowered.startswith("#"):
            return None
        url = urllib.parse.urljoin(f"https://{page.netloc}{page.path}", href)
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        return cls(parsed.netloc, parsed.path)

    def __str__(self):
        return f"{self.netloc}{self.path}"

    def __repr__(self):
        return f"Page(netloc={self.netloc}, path={self.path})"

    def __eq__(self, other):
        return self.netloc == other.netloc and self.path == other.path

MAX_CONNECTIONS = 100

client: httpx.AsyncClient = httpx.AsyncClient(limits=httpx.Limits(max_connections=MAX_CONNECTIONS, max_keepalive_connections=2, keepalive_expiry=0), timeout=httpx.Timeout(connect=10, read=10, write=10, pool=10))

connections = asyncio.Semaphore(MAX_CONNECTIONS)

SCRAPE_INTERVAL = 1.0

sources = [
    "innowings.engg.hku.hk",
    "innoacademy.engg.hku.hk",
]

class Scraper:
    def __init__(self, netloc: netloc):
        if netloc not in sources:
            raise ValueError(f"Invalid source: {netloc}")
        self.netloc = netloc
        self.pages: dict[path, Page] = {}
        self.tasks: deque[Page] = deque()
        self.running: bool = False

    def add_page(self, page: Page):
        self.pages[page.path] = page
        self.tasks.append(page)
        if not self.running:
            self.running = True
            asyncio.create_task(self.run())

    async def run(self):
        while True:
            if not self.tasks:
                self.running = False
                return
            page = self.tasks.popleft()
            async with connections:
                try:
                    response = (await asyncio.gather(client.get(f"https://{page.netloc}{page.path}"), asyncio.sleep(SCRAPE_INTERVAL)))[0]
                except Exception as e:
                    print(f"{e.__class__.__name__} | {page.netloc}{page.path}")
                    continue
            print(f"{response.status_code} | {page.netloc}{page.path}")
            if response.status_code < 200:
                continue
            elif response.status_code < 300:
                pass
            elif response.status_code < 400:
                link = Page.from_relative(page, response.headers.get('Location'))
                if not link:
                    continue
                elif link.netloc == page.netloc:
                    self.add_page(link)
                else:
                    add_page(link)
                continue
            else:
                continue

            page.response = response
            save(page, response)
            if response.headers.get('Content-Type').startswith('text/html'):
                soup = BeautifulSoup(response.text, 'html.parser')
                for a in soup.find_all('a', href=True) + soup.find_all('img', src=True):
                    link = Page.from_relative(page, a.get('href') or a.get('src'))
                    if not link:
                        continue
                    elif link.netloc == page.netloc and link.path not in self.pages.keys():
                        self.add_page(link)
                    else:
                        add_page(link)

scrapers: dict[netloc, Scraper] = {}

def add_page(page: Page):
    scraper = scrapers.get(page.netloc)
    if not scraper:
        try:
            scraper = Scraper(page.netloc)
        except ValueError:
            return
        scrapers[page.netloc] = scraper
    if page.path in scraper.pages.keys():
        return
    scraper.add_page(page)


def save(page: Page, response: httpx.Response):
    path = APP_ROOT / "data" / f"{response.headers.get('Content-Type').replace('/', '\\') or 'unknown'}/{page.netloc}{page.path.replace('/', '\\')}"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(response.text)


async def cancel_pending_tasks() -> None:
    current = asyncio.current_task()
    pending = [task for task in asyncio.all_tasks() if task is not current and not task.done()]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

async def main(seeds: list[Page]) -> None:
    for seed in seeds:
        add_page(seed)
    while any(scraper.running for scraper in scrapers.values()):
        await asyncio.sleep(0.1)
    await cancel_pending_tasks()
    await client.aclose()
    print("Done")


seeds = [
    Page("innowings.engg.hku.hk", "/"),
    Page("innoacademy.engg.hku.hk", "/"),
]


if __name__ == "__main__":
    asyncio.run(main(seeds))