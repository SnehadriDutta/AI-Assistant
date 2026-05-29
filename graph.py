from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, cast
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import json
from structures import *
from func_tools import available_tools
from langchain_core.messages import AIMessage, ToolMessage
load_dotenv()

llm = ChatGroq(model='llama-3.3-70b-versatile')

intent_llm = llm.with_structured_output(IntentResult)
slot_llm = llm.with_structured_output(SlotExtractionResult)
respond_llm = llm.bind_tools(available_tools)

INTENT_SLOT = {
    'place_order': ['symbol', 'units', 'order_type'],
    'add_watchlist': ['symbol']
}

CONDITIONAL_SLOT = {
    'place_order': {
        "order_type" : {
            'limit' : ['price'],
            'stop' : ['price'],
            'market' : []
        }
    }
}

TOOL_MAP = {t.name: t for t in available_tools}

INTENT_PROMPT = """
You are a financial assistant. Classify the user intent and extract any slot values already present in the message.
Intents: place_order, add_watchlist, market_query, portfolio_query, general.
"""

COLLECT_PROMPT = """
Extract slot values from the user message for intent: '{intent}'.
Known slots so far: {slots}.
Only return fields explicitly present in the message.
Valid slot names are: symbol (stock ticker or company name), units, order_type, price, sl, tp.
Always use 'symbol' for any stock, company name, or ticker mentioned.
"""


def get_missing_fields(intent: str, slots: dict) -> list[str]:
    required = list(INTENT_SLOT.get(intent, []))
    conditionals = CONDITIONAL_SLOT.get(intent, {})
    for field, conditions in conditionals.items():
        if slots.get(field) in conditions:
            required.extend(conditions[slots[field]])

    # Missing Fields
    missing = [f for f in required if not slots.get(f)]

    return missing



#------Intent Node ------------------------------------

def entry_router(state: AppState)->str:
    print(f"DEBUG entry_router intent: {state['intent']}, slots: {state['slots']}")
    if state['intent'] in INTENT_SLOT:
        return 'collect'
    return 'intent'

def reset_node(state: AppState) -> AppState:
    return {
        **state,
        'intent': None,
        'slots': {},
        'awaiting_confirm': False
    }

def tool_node(state: AppState) -> AppState:
    results = {}
    for tool_name in state.get('required_tools', []):
        fn = TOOL_MAP.get(tool_name)
        if fn:
            results[tool_name] = fn.invoke({'symbol': state['slots'].get('symbol', '')})
    return {**state, 'tool_results': results}

def intent_node(state: AppState):
    user_message = state['messages'][-1]['content']

    result = cast(IntentResult, intent_llm.invoke([
        {'role': 'system', 'content': INTENT_PROMPT},
        {'role': 'user', 'content': user_message}]))

    return {
        **state,
        'intent': result.intent,
        'slots': {**state['slots'], **{k:v for k, v in result.slots.items() if v is not None}}
    }

def collect_node(state: AppState):

    user_message = state['messages'][-1]['content']
    intent: str = state['intent']
    slots = state['slots']
    result = cast(SlotExtractionResult, slot_llm.invoke([
        {'role': 'system', 'content': COLLECT_PROMPT.format(intent=intent, slots=json.dumps(slots))},
        {'role': 'user', 'content': user_message}]
    ))

    slots = {**slots, **{k: v for k, v in result.slots.items() if v is not None}}
    missing = get_missing_fields(intent, slots)

    if missing:
        ask = f"Please provide the following details: {', '.join(missing) }"
        return {
            **state,
            "messages": state['messages'] + [{
                'role': 'assistant',
                'content': ask
            }],
            'slots': slots,
            'awaiting_confirm': False
        }
    return {**state, 'slots': slots, 'awaiting_confirm': True}


def respond_node(state: AppState):
    system=(
            "You are a financial assistant. Never simulate, execute, or fabricate order results. "
            "If slots are collected, only confirm the details and say the ticket is being opened."
    )

    messages = [{'role': 'system', 'content': system}, *state['messages']]

    while True:
        response = respond_llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            fn = {t.name: t for t in available_tools}[tc['name']]
            result = fn.invoke(tc['name'])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc['id']))

        print(f"DEBUG response: {response}")
        print(f"DEBUG tool_calls: {response.tool_calls}")
        print(f"DEBUG all messages: {messages}")

        final_content = next(
            (m.content for m in reversed(messages) if hasattr(m, 'content') and not getattr(m, 'tool_calls', None)),
            None)


        return {
            **state,
            'awaiting_confirm': False,
            'messages': state['messages'] + [{'role': 'assistant', 'content': final_content}]

        }



#----Router-------------------------------------

def route_after_intent(state: AppState):
    if state['intent'] in INTENT_SLOT:
        return 'collect'
    return 'respond'

def route_after_collect(state: AppState):
    if state.get('awaiting_confirm'):
        return "respond"
    return END

def route_after_respond(state: AppState) -> str:
    if state["intent"] in INTENT_SLOT:
        return "reset"
    return END

#---Graph--------------------

graph = StateGraph(AppState)
graph.add_node('router', lambda s: s)
graph.add_node('intent', intent_node)
graph.add_node('collect', collect_node)
graph.add_node('respond', respond_node)
graph.add_node('reset', reset_node)

graph.set_entry_point('router')

graph.add_conditional_edges('router', entry_router, {
    'collect': 'collect',
    'intent' : 'intent'
})

graph.add_conditional_edges('intent', route_after_intent, {
    "collect": "collect",
    "respond": 'respond'
})

graph.add_conditional_edges('collect', route_after_collect, {
    'respond': 'respond',
    END: END
})

graph.add_conditional_edges('respond', route_after_respond,{
    'reset': 'reset',
    END: END
})

graph.add_edge('reset', END)

app = graph.compile()

if __name__ == "__main__":
    state: AppState = {
        "messages": [],
        "intent": None,
        "slots": {},
        "awaiting_confirm": False,
    }

    print("Trading Assistant (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            break

        state = {
            **state,
            'messages': state['messages'] + [{'role': 'user', 'content': user_input}]
        }

        result = app.invoke(state)
        state = result

        # Print last assistant message
        last_assistant = next((m for m in reversed(state["messages"]) if m["role"] == "assistant"), None)
        if last_assistant:
            print(f"Bot: {last_assistant['content']}\n")









