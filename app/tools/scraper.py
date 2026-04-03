import requests
from bs4 import BeautifulSoup
from app.config.settings import SCRAPER_TIMEOUT

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def scrape_website(url: str) -> str:
    try:
        response = requests.get(url, headers=HEADERS, timeout=SCRAPER_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        return f"Erreur lors du scraping de {url} : {e}"

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    return "\n".join(lines)[:8000]
