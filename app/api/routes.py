from fastapi import APIRouter

from app.agent.core import run_agent
from app.models.schemas import RunRequest, RunResponse, ToolCallOut

router = APIRouter()


@router.post("/run", response_model=RunResponse)
def run_task(request: RunRequest) -> RunResponse:
    result = run_agent(request.task)
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
