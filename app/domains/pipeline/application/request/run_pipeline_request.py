from pydantic import BaseModel, Field


class RunPipelineRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
