import random
from langchain_core.tools import tool
from duckduckgo_search import DDGS

@tool
def get_prices(symbol: str) -> str:
    """Fetch current market price for a stock symbol"""
    price = random.random()
    return f"{symbol} is trading at {price:.2f}"

@tool
def get_news(query: str):
    """Fetch recent news headlines for a stock symbol"""
    results = DDGS().text(query, max_results=2, timelimit='1d')
    return results

@tool
def get_portfolio() -> str:
    """Fetch the user's current portfolio holdings."""
    return "AAPL: 10 shares, TSLA: 5 shares, INFY: 20 shares"

available_tools = [get_prices, get_news, get_portfolio]




