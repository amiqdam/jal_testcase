"""
Knowledge Base Admin API — CRUD operations on campus_info.json.
Allows admin to view and update the knowledge base that the AI uses.
"""
import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
from backend.services.knowledge_base import KnowledgeBase

router = APIRouter()

# Singleton KB instance shared with the pipeline
_kb_instance = None


def get_kb() -> KnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance


class KBSectionUpdate(BaseModel):
    data: Any


class KBFullUpdate(BaseModel):
    data: dict


@router.get("")
async def get_knowledge_base():
    """Return the full knowledge base JSON."""
    kb = get_kb()
    return kb.get_raw_data()


@router.get("/sections")
async def get_sections():
    """Return list of top-level sections in the knowledge base."""
    kb = get_kb()
    data = kb.get_raw_data()
    sections = []
    section_icons = {
        "university": "🏫",
        "programs": "📚",
        "scholarships": "🎓",
        "registration": "📝",
        "facilities": "🏗️",
        "dormitory": "🏠",
        "campus_life": "🎉",
        "alumni_stories": "👤",
        "academic_calendar": "📅",
        "student_portal": "💻",
        "contacts": "📞",
        "faq": "❓",
    }
    for key in data.keys():
        sections.append({
            "key": key,
            "icon": section_icons.get(key, "📄"),
            "label": key.replace("_", " ").title(),
            "item_count": len(data[key]) if isinstance(data[key], list) else None,
        })
    return {"sections": sections}


@router.get("/{section}")
async def get_section(section: str):
    """Return a specific section of the knowledge base."""
    kb = get_kb()
    data = kb.get_raw_data()
    if section not in data:
        raise HTTPException(status_code=404, detail=f"Section '{section}' not found")
    return {"section": section, "data": data[section]}


@router.put("/{section}")
async def update_section(section: str, body: KBSectionUpdate):
    """Update a specific section of the knowledge base and reload."""
    kb = get_kb()
    try:
        kb.update_section(section, body.data)
        return {"status": "ok", "message": f"Section '{section}' updated successfully"}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Section '{section}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("")
async def update_full(body: KBFullUpdate):
    """Replace the entire knowledge base and reload."""
    kb = get_kb()
    try:
        kb.update_full(body.data)
        return {"status": "ok", "message": "Knowledge base fully updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
