import os

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Variable d'environnement manquante : {key}")
    return value


ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_AGENT_ITERATIONS: int = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))
SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "15"))
