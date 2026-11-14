from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)
    provider: str = Field(default="Local simulator", max_length=80)
    mode: Literal["hardened", "vulnerable"] = "hardened"
    allow_tools: bool = False


class AgentRead(AgentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: str | None = None


class EvaluationCreate(BaseModel):
    agent_id: int
    scenario_ids: list[str] | None = None
