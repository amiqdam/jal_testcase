"""
KnowledgeBase service — loads and queries campus information for LLM context injection.
"""
import json
import os
from typing import Optional


class KnowledgeBase:
    """Campus information provider for LLM context injection."""
    
    def __init__(self, data_path: str = None):
        if data_path is None:
            # Resolve relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_path = os.path.join(base_dir, "knowledge_base", "campus_info.json")
        
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
    
    def get_context(self, intent: str, program: str = None) -> str:
        """
        Return relevant campus info based on detected intent.
        Used to inject into LLM prompt for accurate responses.
        """
        sections = []
        
        # Always include university basic info
        uni = self.data["university"]
        sections.append(f"Universitas: {uni['name']} — {uni['tagline']}")
        sections.append(f"Akreditasi: {uni['accreditation']}, Lokasi: {uni['location']}")
        
        if intent in ("inquiry_prodi", "ambiguous"):
            if program:
                prog_info = self.get_program_info(program)
                if prog_info:
                    sections.append(self._format_program(prog_info))
                else:
                    # Return all programs summary
                    sections.append(self._format_all_programs_summary())
            else:
                sections.append(self._format_all_programs_summary())
        
        if intent in ("inquiry_biaya", "scholarship"):
            if program:
                prog_info = self.get_program_info(program)
                if prog_info:
                    sections.append(f"Biaya {prog_info['name']}: Rp {prog_info['tuition_per_semester']:,}/semester")
                    sections.append(f"Biaya Pendaftaran: Rp {prog_info['registration_fee']:,}")
            sections.append(self._format_scholarships())
        
        if intent == "registration":
            sections.append(self._format_registration())
        
        if intent == "followup_status":
            contacts = self.data["contacts"]
            sections.append(f"Kontak Admisi: {contacts['admissions_phone']} | {contacts['admissions_email']}")
            sections.append(f"Jam Kerja: {contacts['office_hours']}")
        
        if intent == "complaint":
            contacts = self.data["contacts"]
            sections.append(f"Hubungi langsung: {contacts['admissions_phone']} | WA: {contacts['admissions_whatsapp']}")
            sections.append(f"Email: {contacts['admissions_email']}")
        
        if intent == "partnership":
            contacts = self.data["contacts"]
            sections.append(f"Kunjungan kampus / kerjasama: {contacts['admissions_email']}")
            sections.append(f"Telepon: {contacts['admissions_phone']}")
        
        return "\n".join(sections)
    
    def get_program_info(self, program_name: str) -> Optional[dict]:
        """Return specific program details by name or ID."""
        program_name_lower = program_name.lower()
        for prog in self.data["programs"]:
            if (prog["id"].lower() == program_name_lower or
                prog["name"].lower() == program_name_lower or
                program_name_lower in prog["name"].lower()):
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
        return (
            f"Program: {prog['name']} ({prog['degree']})\n"
            f"Fakultas: {prog['faculty']}\n"
            f"Akreditasi: {prog['accreditation']}\n"
            f"Durasi: {prog['duration_semesters']} semester, {prog['total_credits']} SKS\n"
            f"Deskripsi: {prog['description']}\n"
            f"Prospek Karir: {', '.join(prog['career_prospects'])}\n"
            f"Biaya: Rp {prog['tuition_per_semester']:,}/semester\n"
            f"Highlight Kurikulum: {', '.join(prog['curriculum_highlights'])}"
        )
    
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
