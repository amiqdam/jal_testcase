"""
Profiler Agent — LLM-based entity extraction and lead profile building.
Extracts structured data from user messages to build/update lead profiles.
"""
import json
import time
from backend.agents.state import AdmissionState


PROFILER_SYSTEM_PROMPT = """Kamu adalah Profiler Agent untuk sistem admisi JAL University.

TUGAS: Ekstrak entitas dan informasi profil dari pesan user untuk membangun profil calon mahasiswa secara inkremental.

## ENTITAS YANG HARUS DIEKSTRAK:

1. **contact_type**: student | parent | counselor | unknown
   - "saya siswa/mahasiswa" → student
   - "saya orang tua dari..." → parent
   - "saya guru BK" → counselor
   
2. **name_mentioned**: Nama yang disebut dalam pesan (jika ada)

3. **school_origin**: Nama sekolah asal (jika disebut)

4. **school_type**: SMA | SMK | MA | International | unknown
   - Deteksi dari nama sekolah atau konteks

5. **kelas**: Kelas berapa (jika disebut) — "kelas 12", "kelas 3 SMA"

6. **umur**: Umur (jika disebut)

7. **interested_program**: Program studi yang diminati
   - "IT", "informatika", "komputer" → Teknik Informatika
   - "SI", "sistem informasi" → Sistem Informasi
   - "manajemen", "bisnis", "management" → Manajemen
   - "psikologi", "psychology" → Psikologi
   - "DKV", "desain", "design" → Desain Komunikasi Visual

8. **financial_concern**: true jika ada indikasi kekhawatiran biaya (kurang mampu, beasiswa, KIP, cicilan)

9. **academic_achievement**: Prestasi akademik jika disebut (juara, nilai, olimpiade)

10. **nationality**: Kebangsaan jika disebut (Indonesian default, atau foreign)

## OUTPUT FORMAT (JSON SAJA, tanpa markdown):
{
  "reasoning": "Jelaskan apa yang kamu temukan dari pesan ini...",
  "entities": {
    "contact_type": "student|parent|counselor|null",
    "name_mentioned": "nama|null",
    "school_origin": "nama sekolah|null",
    "school_type": "SMA|SMK|MA|International|null",
    "kelas": "kelas|null",
    "umur": null,
    "interested_program": "nama program|null",
    "financial_concern": false,
    "academic_achievement": "prestasi|null",
    "nationality": "Indonesian|null"
  }
}

PENTING:
- Hanya isi field yang JELAS disebutkan dalam pesan — jangan menebak
- Gunakan null untuk field yang tidak disebutkan
- "kak" = likely student, "Bapak/Ibu" = could be parent
"""


def profiler_agent(state: AdmissionState, llm) -> dict:
    """
    Extract entities from user message using LLM.
    Returns partial state updates.
    """
    start_time = time.time()
    message = state["message"]
    
    user_prompt = f"Ekstrak entitas dari pesan berikut:\n\nPESAN: \"{message}\""
    
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=PROFILER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        result = json.loads(content)
        entities = result.get("entities", {})
        elapsed = int((time.time() - start_time) * 1000)
        
        # Build profile updates (only non-null values)
        profile_updates = {}
        field_mapping = {
            "contact_type": "contact_type",
            "name_mentioned": "name",
            "school_origin": "school_origin",
            "school_type": "school_type",
            "kelas": "kelas",
            "umur": "umur",
            "interested_program": "interested_program",
            "academic_achievement": "academic_achievement",
            "nationality": "nationality",
        }
        
        for entity_key, db_column in field_mapping.items():
            value = entities.get(entity_key)
            if value and value != "null" and value != "unknown" and value != "N/A":
                profile_updates[db_column] = value
        
        if entities.get("financial_concern"):
            profile_updates["financial_concern"] = True
        
        return {
            "extracted_entities": entities,
            "profile_updates": profile_updates,
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Profiler Agent",
                "thought": result.get("reasoning", "Extracted entities from message"),
                "action": f"Entity Extraction → found {len(profile_updates)} profile fields",
                "observation": f"entities={json.dumps(entities, ensure_ascii=False)[:300]}",
                "confidence": 0.8 if profile_updates else 0.5,
                "time_ms": elapsed,
            }],
        }
    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        return {
            "extracted_entities": {},
            "profile_updates": {},
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Profiler Agent",
                "thought": f"Failed to extract entities: {str(e)}",
                "action": "Fallback → no entities extracted",
                "observation": f"Error: {str(e)[:100]}. Profile not updated.",
                "confidence": 0.0,
                "time_ms": elapsed,
            }],
        }
