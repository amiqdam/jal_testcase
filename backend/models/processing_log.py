"""
ProcessingLog model — structured logging for multi-agent ReAct-style pipeline.
Updated for LangGraph architecture with reasoning traces per agent.
"""
from pydantic import BaseModel
from typing import Optional, Any, List


class ReasoningStep(BaseModel):
    """A single ReAct reasoning step from an agent in the LangGraph pipeline."""
    agent: str  # e.g., "Classifier Agent", "Profiler Agent"
    thought: str  # Agent's reasoning
    action: str  # What the agent did
    observation: str  # Result of the action
    confidence: Optional[float] = None  # 0.0–1.0
    time_ms: int = 0  # Processing time in milliseconds


class ProcessingResult(BaseModel):
    """Complete result of processing a message through the LangGraph pipeline."""
    message_id: str
    timestamp: str
    raw_input: str
    total_processing_time_ms: int = 0
    reasoning_trace: List[ReasoningStep] = []
    
    # Classification outputs
    detected_language: str = "id"
    macro_intent: str = "AMBIGUOUS"
    micro_intent: str = "greeting_unclear"
    urgency: str = "low"
    extracted_keywords: List[str] = []
    classifier_confidence: float = 0.0
    
    # Profiling outputs
    extracted_entities: dict = {}
    profile_updates: dict = {}
    
    # Funnel outputs
    funnel_stage: str = "awareness"
    funnel_reasoning: str = ""
    
    # Response outputs
    ai_response: str = ""
    personalization_signals: List[str] = []
    
    # NBA outputs
    next_best_action: dict = {}
