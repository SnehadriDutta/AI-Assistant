import asyncio
import logging
from typing import Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
from structures import AppState, ToolCallPlan, ToolResult
from tools import TOOL_MAP
from config import (
    TOOL_MAX_RETRIES,
    TOOL_RETRY_MAX_WAIT,
    TOOL_RETRY_MIN_WAIT
)

logger = logging.getLogger(__name__)

TRANSIENT_ERRORS = (TimeoutError, ConnectionError, OSError)

_ERROR_MAP: list[tuple[type, str]] = [
    (TimeoutError, 'service timed out'),
    (ConnectionError, 'service unavailable'),
    (KeyError, 'unexpected data format'),
    (ValueError, 'invalid input')
]


def _friendly_error(tool_name: str, exc: Exception) -> str:
    reason=next(
        (msg for cls, msg in _ERROR_MAP if isinstance(exc, cls)),
        'unexpected error'
    )
    return f"{tool_name}: {reason}"

def resolve_args(tool_fn, state: AppState,
                 upstream_results: dict[str, ToolResult] | None = None) -> dict:
    """
    Build kwargs for a tool call by
    :param tool_fn:
    :param state:
    :param upstream_results:
    :return:
    """

