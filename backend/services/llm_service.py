"""
LLMService — Wrapper for Groq/LangChain LLM with fallback mechanisms.
Simplified after LangGraph refactor — most LLM logic moved to agents.
"""
from backend.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE


class LLMService:
    """LLM service providing access to Groq/Llama 3.3 70B."""
    
    def __init__(self):
        self._llm = None
    
    def get_llm(self):
        """Get or create the LLM instance."""
        if self._llm is None:
            try:
                from langchain_groq import ChatGroq
                self._llm = ChatGroq(
                    api_key=GROQ_API_KEY,
                    model=LLM_MODEL,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=2000,
                )
            except Exception as e:
                print(f"⚠️ Failed to initialize Groq LLM: {e}")
                return None
        return self._llm
    
    def is_available(self) -> bool:
        """Check if LLM is configured and available."""
        return bool(GROQ_API_KEY and GROQ_API_KEY != "gsk_your-groq-api-key-here")
