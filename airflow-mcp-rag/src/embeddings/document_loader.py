"""
문서 로더 및 청킹
"""
from pathlib import Path
from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.utils.config import config


def load_documents(directory: str = "src/data/raw") -> List[Document]:
    """
    마크다운 문서를 로드

    Args:
        directory: 문서가 있는 디렉토리

    Returns:
        Document 객체 리스트
    """
    print(f"Loading documents from {directory}...")

    # 마크다운 파일만 로드
    loader = DirectoryLoader(
        directory,
        glob="**/*.md",
        loader_cls=TextLoader,
        show_progress=True
    )

    documents = loader.load()
    print(f"✓ Loaded {len(documents)} documents")

    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    """
    문서를 청크로 분할

    Args:
        documents: 원본 Document 리스트

    Returns:
        청크로 나눠진 Document 리스트
    """
    print("Splitting documents into chunks...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.text_splitter.chunk_size,
        chunk_overlap=config.text_splitter.chunk_overlap,
        separators=config.text_splitter.separators,
        length_function=len
    )

    chunks = text_splitter.split_documents(documents)
    print(f"✓ Created {len(chunks)} chunks")

    return chunks


def load_and_split(directory: str = "src/data/raw") -> List[Document]:
    """
    문서 로드 및 청킹 전체 파이프라인

    Args:
        directory: 문서 디렉토리

    Returns:
        청크로 나눠진 Document 리스트
    """
    documents = load_documents(directory)
    chunks = split_documents(documents)
    return chunks


if __name__ == "__main__":
    # 테스트
    chunks = load_and_split()

    print("\n" + "=" * 60)
    print("Sample chunks:")
    print("=" * 60)
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i + 1}:")
        print(f"Source: {chunk.metadata.get('source', 'unknown')}")
        print(f"Length: {len(chunk.page_content)} chars")
        print(f"Content preview: {chunk.page_content[:200]}...")
