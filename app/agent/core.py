from dataclasses import dataclass, field
from typing import Any

import anthropic

from app.config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_AGENT_ITERATIONS
from app.tools.definitions import TOOLS_DEFINITION
from app.tools.executor import execute_tool

INPUT_COST_PER_MTOK = 3.0
OUTPUT_COST_PER_MTOK = 15.0

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Tu es un agent IA autonome. Tu reçois une tâche et tu l'accomplis en utilisant les outils à ta disposition.

Stratégie :
1. Analyse la tâche et détermine les étapes nécessaires.
2. Utilise les outils pour collecter les informations.
3. Enchaîne les appels d'outils si nécessaire (recherche → scraping → analyse).
4. Quand tu as suffisamment d'informations, rédige un rapport final structuré en français.

Le rapport final doit contenir : un résumé exécutif, les points clés découverts, et une conclusion."""


@dataclass
class ToolCall:
    name: str
    inputs: dict[str, Any]
    output: str = ""


@dataclass
class AgentResult:
    task: str
    summary: str
    status: str
    iterations: int
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


def _compute_cost(input_tokens: int, output_tokens: int) -> float:
    return round(
        (input_tokens * INPUT_COST_PER_MTOK + output_tokens * OUTPUT_COST_PER_MTOK) / 1_000_000,
        6,
    )


def run_agent(task: str) -> AgentResult:
    messages = [{"role": "user", "content": task}]
    tool_calls_history: list[ToolCall] = []
    iterations = 0
    total_input_tokens = 0
    total_output_tokens = 0

    while iterations < MAX_AGENT_ITERATIONS:
        iterations += 1

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS_DEFINITION,
            messages=messages,
        )

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            summary = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "Aucun résumé généré.",
            )
            return AgentResult(
                task=task,
                summary=summary,
                status="completed",
                iterations=iterations,
                tool_calls=tool_calls_history,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                estimated_cost_usd=_compute_cost(total_input_tokens, total_output_tokens),
            )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                output = execute_tool(block.name, block.input)
                tool_calls_history.append(ToolCall(name=block.name, inputs=block.input, output=output))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
            messages.append({"role": "user", "content": tool_results})

    return AgentResult(
        task=task,
        summary="Limite d'itérations atteinte sans conclusion.",
        status="failed",
        iterations=iterations,
        tool_calls=tool_calls_history,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        estimated_cost_usd=_compute_cost(total_input_tokens, total_output_tokens),
    )
