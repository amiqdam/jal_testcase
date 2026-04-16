"""
ProcessingLog model — structured logging for each pipeline step.
"""
from pydantic import BaseModel
from typing import Optional, Any, List


class StepResult(BaseModel):
    """Result of a single pipeline processing step."""
    step: str
    order: int
    result: Any
    confidence: Optional[float] = None
    reasoning: str = ""
    time_ms: int = 0


class ProcessingResult(BaseModel):
    """Complete result of processing a message through the pipeline."""
    message_id: str
    timestamp: str
    raw_input: str
    total_processing_time_ms: int = 0
    steps: List[StepResult] = []
    
    # Extracted outputs
    language: str = "id"
    intent: str = "ambiguous"
    intent_confidence: float = 0.0
    entities: dict = {}
    sentiment: str = "neutral"
    funnel_stage: str = "awareness"
    urgency: str = "low"
    draft_response: str = ""
    next_best_action: dict = {}
