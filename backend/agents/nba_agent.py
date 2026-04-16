"""
NBA (Next Best Action) Agent — Rule-based deterministic action recommendation.
Matrix: funnel_stage × urgency → action_type.
"""
import time
from backend.agents.state import AdmissionState


# NBA Matrix: (funnel_stage, urgency) → (action_type, action_detail)
NBA_MATRIX = {
    # Awareness
    ("awareness", "low"): ("auto_respond", "Auto-respond + schedule follow-up 3 hari"),
    ("awareness", "medium"): ("send_brochure", "Kirim brosur digital + follow-up 2 hari"),
    ("awareness", "critical"): ("escalate", "Eskalasi ke supervisor. Resolusi dalam 4 jam."),
    
    # Interest
    ("interest", "low"): ("send_brochure", "Kirim info program spesifik + follow-up 3 hari"),
    ("interest", "medium"): ("invite_tour", "Undang campus tour / webinar terdekat"),
    ("interest", "critical"): ("escalate", "Eskalasi ke supervisor. Resolusi dalam 4 jam."),
    
    # Consideration
    ("consideration", "low"): ("connect_alumni", "Hubungkan dengan alumni/mahasiswa aktif"),
    ("consideration", "medium"): ("assign_counselor", "Assign konselor dedicated + hubungi dalam 24 jam"),
    ("consideration", "critical"): ("escalate", "Eskalasi ke supervisor + tim terkait. Resolusi dalam 4 jam."),
    
    # Decision
    ("decision", "low"): ("fast_track", "Fast-track pendaftaran + bantuan personal"),
    ("decision", "medium"): ("fast_track", "Fast-track pendaftaran + bantuan personal + priority processing"),
    ("decision", "critical"): ("escalate", "Eskalasi ke supervisor + resolusi dalam 4 jam + fast-track"),
    
    # Enrolled
    ("enrolled", "low"): ("auto_respond", "Auto-respond + welcome package"),
    ("enrolled", "medium"): ("schedule_call", "Jadwalkan call untuk onboarding"),
    ("enrolled", "critical"): ("escalate", "Eskalasi ke supervisor. Resolusi dalam 4 jam."),
}

# NBA reference items to increase conversion
NBA_CONVERSION_BOOSTERS = {
    "awareness": [
        "Kirim video profil kampus (2 menit)",
        "Share link virtual campus tour",
        "Kirim infografis program studi populer",
    ],
    "interest": [
        "Undang ke webinar Q&A dengan dosen",
        "Kirim kurikulum detail program yang diminati",
        "Share testimoni alumni yang relevan",
    ],
    "consideration": [
        "Kirim simulasi biaya + skema beasiswa",
        "Hubungkan dengan mahasiswa aktif untuk sharing",
        "Tawarkan konsultasi 1-on-1 dengan konselor",
    ],
    "decision": [
        "Bantu langkah pendaftaran step-by-step",
        "Ingatkan deadline gelombang pendaftaran",
        "Kirim checklist dokumen yang harus disiapkan",
    ],
    "enrolled": [
        "Kirim welcome kit digital",
        "Info grup WhatsApp mahasiswa baru",
        "Panduan daftar asrama & orientasi",
    ],
}


def nba_agent(state: AdmissionState) -> dict:
    """
    Determine Next Best Action using rule-based matrix.
    Returns partial state updates.
    """
    start_time = time.time()
    
    funnel = state.get("funnel_stage", "awareness")
    urgency = state.get("urgency", "low")
    macro = state.get("macro_intent", "AMBIGUOUS")
    micro = state.get("micro_intent", "greeting_unclear")
    
    # Look up in matrix
    key = (funnel, urgency)
    action_type, action_detail = NBA_MATRIX.get(key, ("auto_respond", "Auto-respond + schedule follow-up 3 hari"))
    
    # Override for SUPPORT complaints — always escalate
    if macro == "SUPPORT" and urgency == "critical":
        action_type = "escalate"
        if micro == "technical_issue":
            action_detail = "Eskalasi ke supervisor + tim IT. Resolusi teknis dalam 4 jam."
        else:
            action_detail = "Eskalasi ke supervisor. Resolusi keluhan dalam 4 jam."
    
    # Get conversion boosters
    boosters = NBA_CONVERSION_BOOSTERS.get(funnel, [])
    
    # Build reasoning
    reasoning_parts = [
        f"Funnel: {funnel}, Urgency: {urgency}",
        f"Matrix lookup: ({funnel}, {urgency}) → {action_type}",
        f"Detail: {action_detail}",
    ]
    if boosters:
        reasoning_parts.append(f"Conversion boosters: {', '.join(boosters[:2])}")
    
    elapsed = int((time.time() - start_time) * 1000)
    
    return {
        "next_best_action": {
            "action_type": action_type,
            "action_detail": action_detail,
            "priority": urgency,
            "conversion_boosters": boosters,
            "reasoning": " | ".join(reasoning_parts),
        },
        "reasoning_trace": state.get("reasoning_trace", []) + [{
            "agent": "NBA Agent",
            "thought": f"Looking up NBA matrix for funnel={funnel}, urgency={urgency}, macro={macro}",
            "action": f"Rule-based matrix → {action_type}",
            "observation": f"Action: {action_type} — {action_detail}. Boosters: {boosters[:2]}",
            "confidence": 0.95,
            "time_ms": elapsed,
        }],
    }
