import logging
from typing import cast
from tenacity import RetryError

from structures import AppState, IntentResult
from llm_client import intent_llm
from helper import with_llm_retry, normalise_slots
from config import LLM_ERROR_RESPONSE, _INTENT_SYSTEM_TEMPLATE
from tools import build_tool_prompt_section

logger = logging.getLogger(__name__)

_TOOL_SECTION = build_tool_prompt_section()

_INTENT_SYSTEM = _INTENT_SYSTEM_TEMPLATE.format(tool_section=_TOOL_SECTION)

def intent_node(state: AppState) -> AppState:
    user_message = state['messages'][-1]['content']
    try:
        result = cast(
            IntentResult,
            with_llm_retry(
                intent_llm.invoke,
                [
                    {'role': 'system', 'content': _INTENT_SYSTEM},
                    {'role': 'user', 'content': user_message}
                ]
            )
        )
    except RetryError as exc:
        logger.error(f"Intent LLM failed after retries: {exc}")
        return{
            **state,
            'intent': "__llm_error__",
            'messages': state['messages'] + [{'role': 'assistant', 'content': LLM_ERROR_RESPONSE}]

        }

    slots = normalise_slots({**state["slots"], **result.slots})
    tool_plan = [t.model_dump() for t in result.tool_plan]

    logger.info(f"Intent={result.intent} slots={slots} tool_plan={tool_plan}")

    return{
        **state,
        'intent': result.intent,
        'slots': slots,
        'awaiting_confirm': False,
        'tool_plan': tool_plan
    }