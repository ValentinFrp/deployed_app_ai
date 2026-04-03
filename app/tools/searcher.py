from duckduckgo_search import DDGS


def search_web(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        return f"Erreur lors de la recherche : {e}"

    if not results:
        return "Aucun résultat trouvé."

    lines = []
    for i, result in enumerate(results, start=1):
        lines.append(f"[{i}] {result.get('title', 'Sans titre')}")
        lines.append(f"    URL : {result.get('href', '')}")
        lines.append(f"    {result.get('body', '')}")
        lines.append("")

    return "\n".join(lines)
