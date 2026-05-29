from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Any, TypedDict


class OrderSlot(BaseModel):
    symbol: Optional[str] = None
    units: Optional[str] = None
    order_type: Optional[Literal['market','limit','stop']] = None
    price: Optional[float | int] = None
    sl: Optional[float|int] = None
    tp: Optional[float|int] = None

class WatchlistSlot(BaseModel):
    symbol: Optional[str] =None

class IntentResult(BaseModel):
    intent: Literal['place_order', 'add_watchlist','market_query','portfolio_query','general']
    slots: dict = Field(default_factory=dict)

class SlotExtractionResult(BaseModel):
    slots: dict = Field(default_factory=dict)

class AppState(TypedDict):
    messages: List[Any]
    intent: Optional[str]
    slots: dict
    awaiting_confirm: bool
    required_tools: list
    tool_results: dict

