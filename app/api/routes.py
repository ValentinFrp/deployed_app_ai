import time

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.agent.core import run_agent
from app.config.settings import ANTHROPIC_API_KEY
from app.models.schemas import RunRequest, RunResponse, ToolCallOut
from app.monitoring.cost_tracker import get_stats, record_run
from app.monitoring.metrics import (
    AGENT_COST_USD_TOTAL,
    AGENT_RUNS_TOTAL,
    AGENT_TOKENS_TOTAL,
    HTTP_REQUEST_DURATION,
)

router = APIRouter()


@router.post("/run", response_model=RunResponse)
def run_task(request: RunRequest) -> RunResponse:
    start = time.time()
    result = run_agent(request.task)
    duration = time.time() - start

    record_run(
        task=result.task,
        status=result.status,
        iterations=result.iterations,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.estimated_cost_usd,
    )

    AGENT_RUNS_TOTAL.labels(status=result.status).inc()
    HTTP_REQUEST_DURATION.labels(endpoint="/run").observe(duration)
    AGENT_TOKENS_TOTAL.labels(type="input").inc(result.input_tokens)
    AGENT_TOKENS_TOTAL.labels(type="output").inc(result.output_tokens)
    AGENT_COST_USD_TOTAL.inc(result.estimated_cost_usd)

    return RunResponse(
        task=result.task,
        status=result.status,
        iterations=result.iterations,
        summary=result.summary,
        tool_calls=[
            ToolCallOut(tool=tc.name, inputs=tc.inputs, output_preview=tc.output[:200])
            for tc in result.tool_calls
        ],
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        estimated_cost_usd=result.estimated_cost_usd,
    )


@router.get("/health")
def health() -> dict:
    checks: dict[str, str] = {}

    try:
        get_stats()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    checks["api_key"] = "ok" if ANTHROPIC_API_KEY else "missing"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


@router.get("/costs")
def costs() -> dict:
    return get_stats()


@router.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
