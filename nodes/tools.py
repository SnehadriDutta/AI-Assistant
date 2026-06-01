from dataclasses import dataclass, field
from typing import Any
from langchain_core.tools import tool

@dataclass
class ToolMeta:
    name: str
    critical: bool
    retryable: bool
    depends_on: list[str]
    usage_hint: str


@tool
def get_prices(symbol: str) -> dict:
    """Get current stock price for a symbol."""
    # Replace with real API call (e.g. Alpha Vantage, Yahoo Finance)
    return {"symbol": symbol, "price": 142.5, "change_pct": 1.2}


@tool
def get_news(symbol: str) -> list:
    """Get latest news headlines for a stock symbol."""
    # Replace with real API call (e.g. Finnhub, NewsAPI)
    return [
        {"headline": f"Analysts upgrade {symbol} target", "source": "Reuters"},
        {"headline": f"{symbol} Q3 earnings beat estimates", "source": "Bloomberg"},
    ]


@tool
def get_portfolio(user_id: str) -> dict:
    """Get user's current portfolio holdings."""
    # Replace with real DB / brokerage API call
    return {
        "user_id": user_id,
        "holdings": [
            {"symbol": "AAPL", "units": 10, "avg_cost": 135.0},
            {"symbol": "TSLA", "units": 5, "avg_cost": 210.0},
        ],
    }


@tool
def get_historical(symbol: str, period: str = "1mo") -> dict:
    """Get historical OHLCV data for a symbol."""
    # Replace with real API call
    return {
        "symbol": symbol,
        "period": period,
        "data": [{"date": "2024-01-01", "close": 140.0}],
    }


TOOL_METADATA: list[ToolMeta] = [
ToolMeta(
        name="get_prices",
        critical=True,
        retryable=True,
        depends_on=[],
        usage_hint="get current price for a symbol. Use after get_portfolio when analysing holdings.",
    ),
    ToolMeta(
        name="get_news",
        critical=False,
        retryable=True,
        depends_on=[],
        usage_hint="get latest news for a symbol. Independent — run in parallel with other symbol tools.",
    ),
    ToolMeta(
        name="get_portfolio",
        critical=True,
        retryable=True,
        depends_on=[],
        usage_hint="get user's holdings. Always run first when the query is about the user's portfolio.",
    ),
    ToolMeta(
        name="get_historical",
        critical=True,
        retryable=True,
        depends_on=[],
        usage_hint="get historical OHLCV data for a symbol. Independent — run in parallel with get_news.",
    ),
]


ALL_TOOLS = [get_prices, get_historical, get_news, get_portfolio]
TOOL_MAP: dict[str, Any] = {t.name: t for t in ALL_TOOLS}
META_MAP: dict[str, ToolMeta] = {m.name: m for m in TOOL_METADATA}


def build_tool_prompt_section() -> str:
    """
    Auto-generate the tool reference block for the intent system prompt.
    Called once at import time in intent_node - stays in sync with the registry
    automatically whenever tools are added or removed
    :return: Tools details
    """
    lines = ['Available tools (name | args | critical | retryable | usage): ']
    for fn in ALL_TOOLS:
        meta = META_MAP[fn.name]
        schema = fn.args_schema.model_json_schema()
        args = ", ".join(schema.get('properties', {}).keys())
        lines.append(
            f"- {fn.name:<16} | args: {args:<20} "
            f"| critical: {str(meta.critical).lower():<5} "
            f"| retryable: {str(meta.retryable).lower():<5} "
            f"| {meta.usage_hint}"
        )
    return "\n".join(lines)









