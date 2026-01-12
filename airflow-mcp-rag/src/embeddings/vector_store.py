"""
FAISS 벡터 스토어 생성 및 관리
"""
from pathlib import Path
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from src.embeddings.document_loader import load_and_split
from src.utils.models import get_embeddings
from src.utils.config import config


def create_vector_store(
    documents: Optional[List[Document]] = None,
    save_path: Optional[str] = None
) -> FAISS:
    """
    문서로부터 FAISS 벡터 스토어 생성

    Args:
        documents: Document 리스트 (None이면 자동 로드)
        save_path: 저장 경로 (None이면 config 사용)

    Returns:
        FAISS 벡터 스토어
    """
    # 문서 로드
    if documents is None:
        print("Loading documents from raw data...")
        documents = load_and_split()

    if not documents:
        raise ValueError("No documents to process!")

    # 임베딩 모델 로드
    print("Initializing embeddings model...")
    embeddings = get_embeddings()

    # 벡터 스토어 생성
    print("Creating vector store...")
    vector_store = FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )

    print(f"✓ Vector store created with {len(documents)} documents")

    # 저장
    if save_path is None:
        save_path = config.vector_store.path

    save_vector_store(vector_store, save_path)

    return vector_store


def save_vector_store(vector_store: FAISS, path: str):
    """
    벡터 스토어를 디스크에 저장

    Args:
        vector_store: FAISS 벡터 스토어
        path: 저장 경로
    """
    save_dir = Path(path)
    save_dir.mkdir(parents=True, exist_ok=True)

    vector_store.save_local(str(save_dir))
    print(f"✓ Vector store saved to {path}")


def load_vector_store(path: Optional[str] = None) -> FAISS:
    """
    저장된 벡터 스토어 로드

    Args:
        path: 저장 경로 (None이면 config 사용)

    Returns:
        FAISS 벡터 스토어
    """
    if path is None:
        path = config.vector_store.path

    if not Path(path).exists():
        raise FileNotFoundError(f"Vector store not found at {path}")

    print(f"Loading vector store from {path}...")
    embeddings = get_embeddings()

    vector_store = FAISS.load_local(
        str(path),
        embeddings,
        allow_dangerous_deserialization=True
    )

    print("✓ Vector store loaded")
    return vector_store


def get_or_create_vector_store(
    force_rebuild: bool = False,
    path: Optional[str] = None
) -> FAISS:
    """
    벡터 스토어를 로드하거나 없으면 생성

    Args:
        force_rebuild: True면 기존 것을 무시하고 재생성
        path: 저장 경로

    Returns:
        FAISS 벡터 스토어
    """
    if path is None:
        path = config.vector_store.path

    if force_rebuild or not Path(path).exists():
        print("Building new vector store...")
        return create_vector_store(save_path=path)
    else:
        print("Loading existing vector store...")
        return load_vector_store(path)


if __name__ == "__main__":
    import sys

    # 사용법: python -m src.embeddings.vector_store [--rebuild]
    rebuild = "--rebuild" in sys.argv

    print("=" * 60)
    print("Vector Store Setup")
    print("=" * 60)

    # 벡터 스토어 생성 또는 로드
    vector_store = get_or_create_vector_store(force_rebuild=rebuild)

    # 테스트 쿼리
    print("\n" + "=" * 60)
    print("Testing vector store with sample query...")
    print("=" * 60)

    test_query = "How do I migrate data from SQLite to DuckDB using Airflow?"
    results = vector_store.similarity_search(test_query, k=3)

    print(f"\nQuery: {test_query}\n")
    for i, doc in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Source: {doc.metadata.get('source', 'unknown')}")
        print(f"  Content: {doc.page_content[:200]}...")
        print()

    print("✅ Vector store is ready!")
