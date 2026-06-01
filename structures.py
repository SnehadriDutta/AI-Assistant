from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Any, TypedDict
from enum import Enum

class ToolResult(TypedDict):
    status: Literal['ok', 'failed', 'cancelled']
    data: Any
    error: Optional[str]

class ToolCallPlan(TypedDict):
    name: str
    depends_on: list[str]
    critical: bool
    retryable: bool

class AppState(TypedDict):
    messages: List[Any]
    intent: Optional[str]
    slots: dict
    awaiting_confirm: bool
    tool_plan: list[ToolCallPlan]
    tool_results: dict[str, ToolResult]
    user_id: str
    guardrail_verdict: Optional[str]

class GuardrailVerdict(str, Enum):
    PASS = 'pass'
    OFF_DOMAIN = 'off_domain'
    UNSAFE = 'unsafe'

class GuardrailResult(BaseModel):
    verdict: GuardrailVerdict
    reason: str

class ToolCallPlanSchema(BaseModel):
    name: str
    depends_on: list[str] = Field(default_factory=list)
    critical: bool = True
    retryable: bool = True

class IntentResult(BaseModel):
    intent: Literal['place_order', 'add_watchlist','market_query','portfolio_query','general']
    slots: dict = Field(default_factory=dict)
    tool_plan: list[ToolCallPlanSchema] = Field(default_factory=list)

class SlotExtractionResult(BaseModel):
    slots: dict = Field(default_factory=dict)

