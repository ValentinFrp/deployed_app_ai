from fastapi import APIRouter

from app.agent.core import run_agent
from app.models.schemas import RunRequest, RunResponse, ToolCallOut
from app.monitoring.cost_tracker import get_stats, record_run

router = APIRouter()


@router.post("/run", response_model=RunResponse)
def run_task(request: RunRequest) -> RunResponse:
    result = run_agent(request.task)
    record_run(
        task=result.task,
        status=result.status,
        iterations=result.iterations,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.estimated_cost_usd,
    )
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
    return {"status": "ok"}


@router.get("/costs")
def costs() -> dict:
    return get_stats()
