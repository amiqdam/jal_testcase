"""
Supervisor Agent — LangGraph StateGraph orchestrator.
Defines the deterministic pipeline: Classifier → Profiler → Funnel Stager → Response → NBA.
Each agent reads from and writes to the shared AdmissionState.
"""
import time
from typing import Any
from langgraph.graph import StateGraph, END

from backend.agents.state import AdmissionState
from backend.agents.classifier_agent import classifier_agent
from backend.agents.profiler_agent import profiler_agent
from backend.agents.funnel_stager import funnel_stager_agent
from backend.agents.response_agent import response_agent
from backend.agents.nba_agent import nba_agent
from backend.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE


def _get_llm():
    """Get the LLM instance (Groq/Llama 3.3 70B)."""
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=GROQ_API_KEY,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=2000,
        )
    except Exception as e:
        print(f"⚠️ Failed to initialize Groq LLM: {e}")
        return None


# --- Node functions (wrap agents to match LangGraph signature) ---

def classifier_node(state: AdmissionState) -> dict:
    """LangGraph node: Classifier Agent."""
    llm = _get_llm()
    if llm is None:
        from backend.agents.classifier_agent import _rule_based_classify
        result = _rule_based_classify(state.get("message", ""))
        result["reasoning_trace"] = state.get("reasoning_trace", []) + [{
            "agent": "Classifier Agent",
            "thought": "LLM unavailable. Using rule-based fallback.",
            "action": f"Rule-based → {result['macro_intent']}/{result['micro_intent']}",
            "observation": "No LLM API key configured.",
            "confidence": result.get("classifier_confidence", 0.3),
            "time_ms": 0,
        }]
        return result
    return classifier_agent(state, llm)


def profiler_node(state: AdmissionState) -> dict:
    """LangGraph node: Profiler Agent."""
    llm = _get_llm()
    if llm is None:
        return {
            "extracted_entities": {},
            "profile_updates": {},
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Profiler Agent",
                "thought": "LLM unavailable. Skipping entity extraction.",
                "action": "No-op (LLM not configured)",
                "observation": "No entities extracted.",
                "confidence": 0.0,
                "time_ms": 0,
            }],
        }
    return profiler_agent(state, llm)


def funnel_node(state: AdmissionState) -> dict:
    """LangGraph node: Funnel Stager Agent (rule-based)."""
    return funnel_stager_agent(state)


def response_node(state: AdmissionState) -> dict:
    """LangGraph node: Response Agent."""
    llm = _get_llm()
    if llm is None:
        from backend.agents.response_agent import _fallback_response
        lang = state.get("detected_language", "id")
        micro = state.get("micro_intent", "greeting_unclear")
        fallback = _fallback_response(state.get("macro_intent", "AMBIGUOUS"), micro, lang)
        return {
            "ai_response": fallback,
            "personalization_signals": ["fallback"],
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Response Agent",
                "thought": "LLM unavailable. Using template fallback.",
                "action": f"Fallback template for {micro}",
                "observation": "Template response generated.",
                "confidence": 0.3,
                "time_ms": 0,
            }],
        }
    return response_agent(state, llm)


def nba_node(state: AdmissionState) -> dict:
    """LangGraph node: NBA Agent (rule-based)."""
    return nba_agent(state)


def build_admission_graph() -> StateGraph:
    """
    Build the LangGraph deterministic pipeline.
    
    Flow: START → Classifier → Profiler → Funnel Stager → Response → NBA → END
    """
    graph = StateGraph(AdmissionState)
    
    # Add nodes
    graph.add_node("classifier", classifier_node)
    graph.add_node("profiler", profiler_node)
    graph.add_node("funnel_stager", funnel_node)
    graph.add_node("response_generator", response_node)
    graph.add_node("nba", nba_node)
    
    # Define edges (deterministic linear flow)
    graph.set_entry_point("classifier")
    graph.add_edge("classifier", "profiler")
    graph.add_edge("profiler", "funnel_stager")
    graph.add_edge("funnel_stager", "response_generator")
    graph.add_edge("response_generator", "nba")
    graph.add_edge("nba", END)
    
    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def get_admission_graph():
    """Get the singleton compiled admission graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_admission_graph()
    return _compiled_graph


async def run_admission_pipeline(
    message: str,
    email: str,
    name: str,
    lead_profile: dict,
    conversation_history: list,
    knowledge_context: str,
    quick_start_intent: str = "",
) -> AdmissionState:
    """
    Run the full admission pipeline asynchronously.
    Returns the final state with all agent outputs.
    """
    start_time = time.time()
    
    initial_state: AdmissionState = {
        "message": message,
        "email": email,
        "name": name,
        "lead_profile": lead_profile,
        "conversation_history": conversation_history,
        "knowledge_context": knowledge_context,
        "quick_start_intent": quick_start_intent,
        "reasoning_trace": [],
        "total_processing_time_ms": 0,
    }
    
    graph = get_admission_graph()
    
    # LangGraph invoke is synchronous
    final_state = graph.invoke(initial_state)
    
    # Set total processing time
    final_state["total_processing_time_ms"] = int((time.time() - start_time) * 1000)
    
    return final_state
