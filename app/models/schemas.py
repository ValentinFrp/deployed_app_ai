from typing import Any
from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    task: str = Field(..., min_length=1)


class ToolCallOut(BaseModel):
    tool: str
    inputs: dict[str, Any]
    output_preview: str


class RunResponse(BaseModel):
    task: str
    status: str
    iterations: int
    summary: str
    tool_calls: list[ToolCallOut]
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
