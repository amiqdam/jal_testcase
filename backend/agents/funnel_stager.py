"""
Funnel Stager Agent — Rule-based deterministic funnel stage assignment.
Forward-only progression (awareness → interest → consideration → decision → enrolled).
"""
import time
from backend.agents.state import AdmissionState
from backend.config import FUNNEL_STAGES


def funnel_stager_agent(state: AdmissionState) -> dict:
    """
    Determine funnel stage using deterministic rules.
    Stage can only move forward, never backward.
    Returns partial state updates.
    """
    start_time = time.time()
    
    macro = state.get("macro_intent", "AMBIGUOUS")
    micro = state.get("micro_intent", "greeting_unclear")
    urgency = state.get("urgency", "low")
    profile = state.get("lead_profile", {})
    current_stage = profile.get("funnel_stage", "awareness")
    message = state.get("message", "").lower()
    
    # Determine new stage based on rules
    new_stage = current_stage
    reasoning_parts = []
    
    # Rule 1: ENROLLED — mentions acceptance/admission
    enrolled_keywords = ["sudah diterima", "accepted", "enrolled", "sudah terdaftar", "sudah lulus seleksi", "sudah bayar semester"]
    if any(kw in message for kw in enrolled_keywords):
        new_stage = "enrolled"
        reasoning_parts.append(f"Message contains enrollment indicator keyword → enrolled")
    
    # Rule 2: DECISION — registration intent or explicit "mau daftar"
    elif macro == "TRANSACTIONAL" and micro == "registration_process":
        new_stage = "decision"
        reasoning_parts.append(f"TRANSACTIONAL/registration_process → decision")
    elif any(kw in message for kw in ["mau daftar", "saya mau daftar", "saya ingin daftar", "i want to apply", "i'd like to apply"]):
        new_stage = "decision"
        reasoning_parts.append(f"Explicit registration intent detected → decision")
    
    # Rule 3: DECISION — follow-up status (already in process)
    elif macro == "TRANSACTIONAL" and micro == "status_follow_up":
        new_stage = "decision"
        reasoning_parts.append(f"TRANSACTIONAL/status_follow_up → user already applied → decision")
    
    # Rule 4: CONSIDERATION — financial inquiry or comparison
    elif macro == "INQUIRY" and micro == "financial_inquiry":
        new_stage = "consideration"
        reasoning_parts.append(f"INQUIRY/financial_inquiry → evaluating costs → consideration")
    
    # Rule 5: CONSIDERATION — support issues (user is engaged)
    elif macro == "SUPPORT":
        new_stage = "consideration"
        reasoning_parts.append(f"SUPPORT intent → user is engaged enough to complain → minimum consideration")
    
    # Rule 6: INTEREST — specific academic inquiry
    elif macro == "INQUIRY" and micro == "academic_inquiry":
        new_stage = "interest"
        reasoning_parts.append(f"INQUIRY/academic_inquiry → specific program interest → interest")
    
    # Rule 7: AWARENESS — general inquiry or ambiguous
    elif macro in ("INQUIRY", "AMBIGUOUS") and micro in ("general_inquiry", "greeting_unclear"):
        new_stage = "awareness"
        reasoning_parts.append(f"{macro}/{micro} → general/unclear → awareness")
    
    # Enforce forward-only progression
    current_idx = FUNNEL_STAGES.index(current_stage) if current_stage in FUNNEL_STAGES else 0
    new_idx = FUNNEL_STAGES.index(new_stage) if new_stage in FUNNEL_STAGES else 0
    
    if new_idx < current_idx:
        final_stage = current_stage
        reasoning_parts.append(f"⚠️ Stage regression blocked: {new_stage} < {current_stage}. Keeping {current_stage}.")
    else:
        final_stage = new_stage
        if new_idx > current_idx:
            reasoning_parts.append(f"✅ Stage advanced: {current_stage} → {final_stage}")
        else:
            reasoning_parts.append(f"Stage unchanged: {final_stage}")
    
    elapsed = int((time.time() - start_time) * 1000)
    full_reasoning = " | ".join(reasoning_parts)
    
    return {
        "funnel_stage": final_stage,
        "funnel_reasoning": full_reasoning,
        "reasoning_trace": state.get("reasoning_trace", []) + [{
            "agent": "Funnel Stager Agent",
            "thought": f"Current stage: {current_stage}. Macro: {macro}, Micro: {micro}. Evaluating rules...",
            "action": f"Rule-based staging → {final_stage}",
            "observation": full_reasoning,
            "confidence": 0.95,
            "time_ms": elapsed,
        }],
    }
