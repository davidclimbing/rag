# src/utils/models.py
from typing import Union
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from src.utils.config import config

def get_embeddings():
    """Gemini 임베딩 모델 반환"""
    if config.embeddings.provider == "google":
        return GoogleGenerativeAIEmbeddings(
            model=config.embeddings.model,
            google_api_key=config.google_api_key
        )
    else:
        raise ValueError(f"Unknown embeddings provider: {config.embeddings.provider}")

def get_llm():
    """Gemini LLM 모델 반환"""
    if config.llm.provider == "google":
        return ChatGoogleGenerativeAI(
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_output_tokens=config.llm.max_tokens,
            google_api_key=config.google_api_key,
            convert_system_message_to_human=True  # Gemini는 system message를 지원하지 않음
        )
    else:
        raise ValueError(f"Unknown LLM provider: {config.llm.provider}")