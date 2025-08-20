import os
from typing import Literal, Optional, Tuple, Dict
from src.constants.config import Config
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

class LLMBuilderFactory:
    """
    LLM Factory with intelligent caching and explicit client instantiation
    (avoids .with_options() for better stability across LangChain versions).
    """

    _cache: Dict[Tuple[str, str, int], BaseChatModel] = {}

    @staticmethod
    def get_llm_client(
        provider: Literal["openai", "gemini"],
        model_name: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0
    ) -> BaseChatModel:
        """
        Returns a cached or new instance of the LLM client based on input parameters.

        Args:
            provider: LLM provider key ("openai" or "gemini")
            model_name: Optional custom model name (default is provider-specific)
            max_tokens: Maximum token limit
            temperature: Temperature for output randomness

        Returns:
            A configured and cached BaseChatModel instance.
        """
        # Define defaults
        default_models = {
            "openai": "gpt-4o-mini",
            "gemini": "gemini-2.5-flash"
        }

        if provider not in default_models:
            raise ValueError(f"Unsupported provider: {provider}")

        final_model_name = model_name or default_models[provider]
        cache_key = (provider, final_model_name, max_tokens)

        if cache_key in LLMBuilderFactory._cache:
            return LLMBuilderFactory._cache[cache_key]

        if provider == "openai":
            client = ChatOpenAI(
                openai_api_key=Config.OPENAI_API_KEY,
                model=final_model_name,
                max_tokens=max_tokens,
                temperature=temperature
            )
        elif provider == "gemini":
            client = ChatGoogleGenerativeAI(
                google_api_key=Config.GOOGLE_API_KEY,
                model=final_model_name,
                max_tokens=max_tokens,
                temperature=temperature
            )

        # Cache and return
        LLMBuilderFactory._cache[cache_key] = client
        return client
