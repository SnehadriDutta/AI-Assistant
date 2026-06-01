import logging
from typing import cast
from tenacity import RetryError

from structures import AppState, SlotExtractionResult
from llm_client import slot_llm
from helper import with_llm_retry, normalise_slots, get_missing_slots
from config import LLM_ERROR_RESPONSE, _COLLECT_SYSTEM_TEMPLATE

logger = logging.getLogger(__name__)

def collect_node(state: AppState) -> AppState:
    user_msg = state['messages'][-1]['content']
    intent = state['intent']
    slots = state['slots']

    _COLLECT_SYSTEM = _COLLECT_SYSTEM_TEMPLATE.format(intent=intent, slots=slots)
    try:
        result = cast(
            SlotExtractionResult,
            with_llm_retry(
                slot_llm.invoke,
                [
                    {'role': 'system', 'content': _COLLECT_SYSTEM},
                    {'role': 'user', 'content': user_msg}
                ]
            )
        )
        new_slots= normalise_slots(result.slots)
    except RetryError as exc:
        logger.error(f"Slot LLM failed after retries: {exc}")
        return {
            **state,
            'awaiting_confirm': False,
            'messages': state['messages'] + [{'role': 'assistant', }]
        }

    merged = normalise_slots({**slots, **new_slots})
    missing_slots = get_missing_slots(intent, merged)

    logger.info(f'Collect: merged_slots={merged} missing={missing_slots}')
    if missing_slots:
        ask = f"Please provide the following details: {', '.join(missing_slots) }"
        return {
            **state,
            'slots': merged,
            'awaiting_confirm': False,
            'messages': state['messages'] + [{'role': 'assistant', 'content': ask}]
        }

    return {**state, 'slots': merged, 'awaiting_confirm': True}