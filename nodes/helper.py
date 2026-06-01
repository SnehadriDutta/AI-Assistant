import logging
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

from config import (
    INTENT_SLOTS,
    CONDITIONAL_SLOTS,
    LLM_MAX_RETRIES,
    LLM_RETRY_MAX_WAIT,
    LLM_RETRY_MIN_WAIT
)

logger = logging.getLogger(__name__)

def with_llm_retry(fn, *args, **kwargs):
    """
    Call an LLM function with exponential backoff.
    Raises RetryError after exhausting attempts - callers must handle it
    """
    @retry(
        stop=stop_after_attempt(LLM_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=1,
            min=LLM_RETRY_MIN_WAIT,
            max=LLM_RETRY_MAX_WAIT
        )
    )
    def _call():
        return fn(*args, **kwargs)
    return _call()

def get_missing_slots(intent: str, slots: dict) -> list[str]:
    """Return slot names still needed to fulfil the intent"""
    required = list(INTENT_SLOTS.get(intent, []))
    conditional = CONDITIONAL_SLOTS.get(intent, {})

    for field, conditions in conditional.items():
        value = slots.get(field)
        if value in conditions:
            required.extend(conditions[value])

    return [f for f in required if not slots.get(f)]


def normalise_slots(slots: dict) -> dict:
    """
    Lowercase string slot values and strip whitespace.
    Prevents CONDITIONAL_SLOTS matching failures from casing difference
    """
    return {
        k : (v.strip().lower() if isinstance(v, str) else v)
        for k, v in slots.items()
        if v is not None
    }














