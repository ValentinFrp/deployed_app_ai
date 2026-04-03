from app.tools.scraper import scrape_website
from app.tools.searcher import search_web


def execute_tool(name: str, inputs: dict) -> str:
    if name == "scrape_website":
        return scrape_website(**inputs)
    if name == "search_web":
        return search_web(**inputs)
    return f"Outil inconnu : {name}"
