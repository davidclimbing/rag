# src/utils/config.py
import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

class EmbeddingsConfig(BaseModel):
    provider: str = "google"
    model: str = "models/embedding-001"
    dimension: int = 768

class TextSplitterConfig(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: List[str] = ["\n\n", "\n", " ", ""]

class VectorStoreConfig(BaseModel):
    type: str = "faiss"
    path: str = "src/data/processed/airflow_vectors"
    index_type: str = "IndexFlatL2"

class RetrievalConfig(BaseModel):
    k: int = 5
    score_threshold: float = 0.7
    search_type: str = "similarity"

class LLMConfig(BaseModel):
    provider: str = "google"
    model: str = "gemini-1.5-flash"
    temperature: float = 0.0
    max_tokens: int = 2048

class AirflowDocsConfig(BaseModel):
    base_url: str = "https://airflow.apache.org/docs/"
    version: str = "apache-airflow/stable"
    sections: List[str] = ["concepts", "tutorial", "howto"]

class Config(BaseModel):
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    text_splitter: TextSplitterConfig = Field(default_factory=TextSplitterConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    airflow_docs: AirflowDocsConfig = Field(default_factory=AirflowDocsConfig)
    
    # API Keys
    google_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))

def load_config(config_path: str = "config/config.yaml") -> Config:
    """YAML 설정 파일 로드"""
    config_file = Path(config_path)
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config_dict = yaml.safe_load(f)
        return Config(**config_dict)
    
    return Config()

config = load_config()