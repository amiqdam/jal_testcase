"""
AdmissionState — Shared state passed between agents in the LangGraph pipeline.
Uses TypedDict for type-safe state management.
"""
from typing import TypedDict, Optional


class ReasoningStep(TypedDict, total=False):
    """A single ReAct reasoning step from an agent."""
    agent: str
    thought: str
    action: str
    observation: str
    confidence: float
    time_ms: int


class AdmissionState(TypedDict, total=False):
    """Shared state passed through the LangGraph supervisor pipeline."""
    
    # --- Input (set by processor before graph invocation) ---
    message: str
    email: str
    name: str
    lead_profile: dict  # Current lead profile from DB
    conversation_history: list  # Recent messages for context
    knowledge_context: str  # Injected knowledge base text
    quick_start_intent: str  # Pre-classified intent from quick-start button
    
    # --- Classifier Agent outputs ---
    detected_language: str
    macro_intent: str
    micro_intent: str
    urgency: str
    extracted_keywords: list
    classifier_confidence: float
    
    # --- Profiler Agent outputs ---
    extracted_entities: dict
    profile_updates: dict  # Fields to update in lead profile
    
    # --- Funnel Stager outputs ---
    funnel_stage: str
    funnel_reasoning: str
    
    # --- Response Agent outputs ---
    ai_response: str
    personalization_signals: list
    
    # --- NBA Agent outputs ---
    next_best_action: dict
    
    # --- Reasoning trace (collected from all agents) ---
    reasoning_trace: list  # List[ReasoningStep]
    
    # --- Meta ---
    total_processing_time_ms: int
    error: str
