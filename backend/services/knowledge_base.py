"""
KnowledgeBase service — loads and queries JAL University information for LLM context injection.
"""
import json
import os
from typing import Optional


class KnowledgeBase:
    """JAL University information provider for LLM context injection."""
    
    def __init__(self, data_path: str = None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_path = os.path.join(base_dir, "knowledge_base", "campus_info.json")
        
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
    
    def get_context(self, micro_intent: str, program: str = None) -> str:
        """
        Return relevant campus info based on detected micro intent.
        Used to inject into LLM prompt for accurate responses.
        """
        sections = []
        
        # Always include university basic info
        uni = self.data["university"]
        sections.append(f"Universitas: {uni['name']} — {uni['tagline']}")
        sections.append(f"Akreditasi: {uni['accreditation']}, Lokasi: {uni['location']}")
        sections.append(f"Total mahasiswa: {uni['total_students']}, Rasio dosen: {uni['student_faculty_ratio']}")
        
        if micro_intent in ("academic_inquiry", "greeting_unclear"):
            if program:
                prog_info = self.get_program_info(program)
                if prog_info:
                    sections.append(self._format_program(prog_info))
                else:
                    sections.append(self._format_all_programs_summary())
            else:
                sections.append(self._format_all_programs_summary())
        
        if micro_intent == "financial_inquiry":
            if program:
                prog_info = self.get_program_info(program)
                if prog_info:
                    sections.append(f"Biaya {prog_info['name']}: Rp {prog_info['tuition_per_semester']:,}/semester")
                    sections.append(f"Biaya Pendaftaran: Rp {prog_info['registration_fee']:,}")
            sections.append(self._format_scholarships())
        
        if micro_intent == "registration_process":
            sections.append(self._format_registration())
        
        if micro_intent == "status_follow_up":
            contacts = self.data["contacts"]
            sections.append(f"Kontak Admisi: {contacts['admissions_phone']} | {contacts['admissions_email']}")
            sections.append(f"Jam Kerja: {contacts['office_hours']}")
        
        if micro_intent in ("technical_issue", "general_complaint"):
            contacts = self.data["contacts"]
            sections.append(f"Hubungi langsung: {contacts['admissions_phone']} | WA: {contacts['admissions_whatsapp']}")
            sections.append(f"Email: {contacts['admissions_email']}")
        
        if micro_intent == "general_inquiry":
            sections.append(self._format_facilities())
            sections.append(self._format_dormitory())
            sections.append(self._format_campus_life())
        
        return "\n".join(sections)
    
    def get_program_info(self, program_name: str) -> Optional[dict]:
        """Return specific program details by name or ID."""
        program_name_lower = program_name.lower()
        for prog in self.data["programs"]:
            if (prog["id"].lower() == program_name_lower or
                prog["name"].lower() == program_name_lower or
                program_name_lower in prog["name"].lower() or
                program_name_lower in prog["id"].lower()):
                return prog
        return None
    
    def get_all_programs(self) -> list:
        """Return all program data."""
        return self.data["programs"]
    
    def get_scholarship_info(self) -> list:
        """Return all scholarship information."""
        return self.data["scholarships"]
    
    def get_registration_info(self) -> dict:
        """Return registration process information."""
        return self.data["registration"]
    
    def get_contacts(self) -> dict:
        """Return contact information."""
        return self.data["contacts"]
    
    def get_faq(self, topic: str = None) -> list:
        """Return FAQ entries, optionally filtered by topic."""
        faqs = self.data.get("faq", [])
        if topic:
            topic_lower = topic.lower()
            return [faq for faq in faqs if topic_lower in faq["question"].lower() or topic_lower in faq["answer"].lower()]
        return faqs
    
    # --- Private formatting helpers ---
    
    def _format_program(self, prog: dict) -> str:
        """Format a single program for LLM context."""
        text = (
            f"Program: {prog['name']} ({prog['degree']})\n"
            f"Fakultas: {prog['faculty']}\n"
            f"Akreditasi: {prog['accreditation']}\n"
            f"Durasi: {prog['duration_semesters']} semester, {prog['total_credits']} SKS\n"
            f"Deskripsi: {prog['description']}\n"
            f"Prospek Karir: {', '.join(prog['career_prospects'])}\n"
            f"Biaya: Rp {prog['tuition_per_semester']:,}/semester\n"
            f"Highlight Kurikulum: {', '.join(prog['curriculum_highlights'])}"
        )
        # Add notable lecturers
        if prog.get("notable_lecturers"):
            text += "\nDosen Unggulan:"
            for lec in prog["notable_lecturers"][:2]:
                text += f"\n  - {lec['name']}: {lec['expertise']}"
        # Add concentrations
        if prog.get("concentrations"):
            text += f"\nKonsentrasi: {', '.join(prog['concentrations'])}"
        return text
    
    def _format_all_programs_summary(self) -> str:
        """Format summary of all programs."""
        lines = ["Program Studi yang Tersedia:"]
        for prog in self.data["programs"]:
            lines.append(
                f"- {prog['name']} ({prog['degree']}, {prog['faculty']}) — "
                f"Akreditasi {prog['accreditation']}, "
                f"Rp {prog['tuition_per_semester']:,}/semester"
            )
        return "\n".join(lines)
    
    def _format_scholarships(self) -> str:
        """Format scholarship information."""
        lines = ["Beasiswa yang Tersedia:"]
        for sch in self.data["scholarships"]:
            lines.append(
                f"- {sch['name']} ({sch['type']}): potongan {sch['discount_range']}\n"
                f"  Syarat: {'; '.join(sch['requirements'][:3])}\n"
                f"  Kuota: {sch['quota']} mahasiswa"
            )
        return "\n".join(lines)
    
    def _format_registration(self) -> str:
        """Format registration process."""
        reg = self.data["registration"]
        lines = ["Informasi Pendaftaran:"]
        for period in reg["intake_periods"]:
            lines.append(f"- {period['name']}: {period['period']} ({period['benefit']})")
        lines.append(f"Biaya Pendaftaran: Rp {reg['fee']:,}")
        lines.append("Persyaratan Umum: " + "; ".join(reg["requirements"]["general"][:4]))
        lines.append("Langkah Pendaftaran:")
        for step in reg["steps"]:
            lines.append(f"  {step}")
        return "\n".join(lines)
    
    def _format_facilities(self) -> str:
        """Format facilities information."""
        fac = self.data.get("facilities", {})
        lines = ["Fasilitas Kampus:"]
        for category, items in fac.items():
            lines.append(f"  {category.replace('_', ' ').title()}:")
            for item in items[:3]:
                lines.append(f"    - {item}")
        return "\n".join(lines)
    
    def _format_dormitory(self) -> str:
        """Format dormitory information."""
        dorm = self.data.get("dormitory", {})
        if not dorm:
            return ""
        lines = [f"Asrama: {dorm.get('name', 'Asrama Mahasiswa')} (kapasitas {dorm.get('capacity', 0)})"]
        for room in dorm.get("room_types", []):
            lines.append(f"  - {room['type']}: Rp {room['price_per_month']:,}/bulan — {room['facilities']}")
        return "\n".join(lines)
    
    def _format_campus_life(self) -> str:
        """Format campus life information."""
        life = self.data.get("campus_life", {})
        if not life:
            return ""
        orgs = life.get("student_organizations", [])
        lines = [f"Kehidupan Kampus ({len(orgs)} organisasi/UKM):"]
        for org in orgs[:5]:
            lines.append(f"  - {org['name']} ({org['category']})")
        events = life.get("annual_events", [])
        if events:
            lines.append("Event Tahunan:")
            for ev in events[:3]:
                lines.append(f"  - {ev['name']} ({ev['month']}): {ev['description'][:80]}")
        return "\n".join(lines)
