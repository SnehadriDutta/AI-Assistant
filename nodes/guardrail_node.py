import logging
from tenacity import RetryError
from config import  LLM_ERROR_RESPONSE, _GUARDRAIL_SYSTEM, REJECT_MESSAGES
from structures import AppState
from llm_client import guardrail_llm
from helper import with_llm_retry

logger = logging.getLogger(__name__)

def guardrail_node(state: AppState) -> AppState:
    user_msg = state['messages'][-1]['content']

    try:
        result = with_llm_retry(
            guardrail_llm.invoke,
            [
                {'role': 'system', 'content': _GUARDRAIL_SYSTEM},
                {'role': 'user', 'content': user_msg}
            ]
        )
        verdict = result.verdict
        logger.info(f"Guardrail verdict={result.verdict}, reason={result.reason}")
    except (Exception, RetryError) as exc:
        logger.error(f"Guardrail LLM failed: {exc} ")
        verdict = 'unsafe'
    return {**state, 'guardrail_verdict': verdict}

def reject_node(state: AppState) -> AppState:
    """Return a fixed, non LLM generated rejection message"""
    verdict = state.get('guardrail_verdict', 'unsafe')
    content = REJECT_MESSAGES.get(verdict, REJECT_MESSAGES['unsafe'])
    return{
        **state,
        'messages': state['messages'] + [{'role': 'assistant', 'content': content}]
    }

