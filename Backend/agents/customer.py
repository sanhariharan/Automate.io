import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from langgraph.graph import MessagesState, START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv("Backend/.env")
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY required!")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0.0,
)

SYSTEM_PROMPT = """You are CompanyOS Customer Intake Agent. ONLY collect project requirements.

🚫 NEVER: Give marketing advice, explain strategies, make promises.
✅ ALWAYS: Ask simple questions, confirm understanding, stay friendly.

COLLECT 6 FIELDS:
1. PRODUCT_SERVICE - What are they selling?
2. TARGET_AUDIENCE - Who is it for? (age, profession, interests)
3. BUDGET - Approx marketing budget (₹ or range)
4. TIMELINE - When to start and for how long (weeks/months)
5. CHANNELS - Instagram, LinkedIn, Email, YouTube, etc.
6. GOALS - What success means (leads, sales, awareness)

RESPONSE PATTERN:
1) Briefly confirm: "Got it, you want to promote [PRODUCT] to [AUDIENCE]."
2) Status: "I have X/6 details. Missing: [LIST]"
3) Ask ONE follow-up: "What is your [MISSING]?"

RULES:
- One question per message
- If all 6 collected: "I have everything! Ready to plan?"
- Keep tone WhatsApp-friendly"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])

class ConversationStore:
    def __init__(self):
        self.conversations: Dict[str, Dict[str, Any]] = {}

    def create(self, conv_id: str):
        self.conversations[conv_id] = {
            "messages": [],
            "created_at": datetime.now().isoformat(),
        }

    def add_message(self, conv_id: str, role: str, text: str):
        if conv_id not in self.conversations:
            self.create(conv_id)
        self.conversations[conv_id]["messages"].append({
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat(),
        })

    def get(self, conv_id: str) -> Optional[Dict[str, Any]]:
        return self.conversations.get(conv_id)

store = ConversationStore()

def extract_requirements_from_text(text: str) -> Dict[str, Optional[str]]:
    t = text.lower()
    def present(words: List[str]) -> Optional[str]:
        return "mentioned" if any(w in t for w in words) else None
    
    return {
        "product_service": present(["product", "service", "sell", "launch", "ashwagandha", "supplement"]),
        "target_audience": present(["target", "audience", "customer", "professional", "age", "students", "parents"]),
        "budget": present(["budget", "₹", "lakh", "crore", "rs", "rupee", "price", "spend"]),
        "timeline": present(["week", "month", "timeline", "when", "launch", "start", "duration"]),
        "channels": present(["instagram", "insta", "linkedin", "email", "youtube", "facebook", "social"]),
        "goals": present(["lead", "leads", "sale", "sales", "awareness", "signup", "conversion"]),
    }

def compute_completeness(reqs: Dict[str, Optional[str]]) -> float:
    collected = sum(1 for v in reqs.values() if v)
    return collected / 6.0

class ConversationState(MessagesState):
    conversation_id: str
    requirements: Dict[str, Optional[str]]
    completeness: float

def intake_agent(state: ConversationState) -> ConversationState:
    messages = state["messages"]
    response = llm.invoke(prompt.format_messages(messages=messages))
    
    store.add_message(state["conversation_id"], "assistant", response.content)
    
    conv = store.get(state["conversation_id"])
    all_text = " ".join(m["text"] for m in conv["messages"]) if conv else ""
    reqs = extract_requirements_from_text(all_text)
    completeness = compute_completeness(reqs)
    
    new_messages = messages + [response]
    
    return {
        "messages": new_messages,
        "conversation_id": state["conversation_id"],
        "requirements": reqs,
        "completeness": completeness,
    }

builder = StateGraph(ConversationState)
builder.add_node("intake", intake_agent)
builder.add_edge(START, "intake")
builder.add_edge("intake", END)

graph = builder.compile(checkpointer=MemorySaver())

def process_customer_message(text: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    conv_id = conversation_id or str(uuid.uuid4())
    if not store.get(conv_id):
        store.create(conv_id)
    
    store.add_message(conv_id, "customer", text)
    
    conv = store.get(conv_id)
    messages = [
        HumanMessage(content=m["text"]) if m["role"] == "customer" else AIMessage(content=m["text"])
        for m in conv["messages"]
    ]
    
    result = graph.invoke(
        {
            "messages": messages,
            "conversation_id": conv_id,
            "requirements": {},
            "completeness": 0.0,
        },
        config={"configurable": {"thread_id": conv_id}},
    )
    
    last_ai = result["messages"][-1]
    requirements = result["requirements"]
    completeness = result["completeness"]
    
    return {
        "conversation_id": conv_id,
        "reply": last_ai.content,
        "requirements": requirements,
        "completeness": completeness,
        "ready_for_ceo": completeness >= 0.8,
    }

def get_conversation(conversation_id: str) -> Dict[str, Any]:
    conv = store.get(conversation_id)
    if not conv:
        raise KeyError("Conversation not found")
    
    all_text = " ".join(m["text"] for m in conv["messages"])
    reqs = extract_requirements_from_text(all_text)
    completeness = compute_completeness(reqs)
    
    return {
        "conversation_id": conversation_id,
        "messages": conv["messages"],
        "requirements": reqs,
        "completeness": completeness,
        "created_at": conv["created_at"],
    }

def export_for_ceo(conversation_id: str) -> Dict[str, Any]:
    conv = store.get(conversation_id)
    if not conv:
        raise KeyError("Conversation not found")
    
    all_text = " ".join(m["text"] for m in conv["messages"])
    reqs = extract_requirements_from_text(all_text)
    completeness = compute_completeness(reqs)
    
    return {
        "conversation_id": conversation_id,
        "status": "ready_for_ceo" if completeness >= 0.8 else "incomplete",
        "brief": reqs,
        "messages": conv["messages"],
        "created_at": conv["created_at"],
    }
