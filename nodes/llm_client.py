from langchain_groq import ChatGroq
from config import MODEL_NAME
from structures import IntentResult, SlotExtractionResult, GuardrailResult
from dotenv import load_dotenv

load_dotenv()


_base_llm = ChatGroq(model=MODEL_NAME)

#Structured output
intent_llm = _base_llm.with_structured_output(IntentResult)
slot_llm = _base_llm.with_structured_output(SlotExtractionResult)
guardrail_llm = _base_llm.with_structured_output(GuardrailResult)

#Plain llm
chat_llm = _base_llm