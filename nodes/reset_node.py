from structures import AppState

def reset_node(state: AppState) -> AppState:
    """Clear all per-intent state after an action intent complete"""
    return{
        **state,
        'intent': None,
        'slots': {},
        'awaiting_confirm': False,
        'tool_plan': [],
        'tool_results': {},
        'guardrail_verdict': None
    }