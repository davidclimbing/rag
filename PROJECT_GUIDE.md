# Airflow MCP RAG 프로젝트 가이드

Apache Airflow 문서에 대한 RAG(Retrieval Augmented Generation) 기반 MCP(Model Context Protocol) 서버 프로젝트

## 📁 프로젝트 구조

```
airflow-mcp-rag/
├── config/                          # 설정 파일
│   └── config.yaml                  # 메인 설정 (임베딩, LLM, 벡터스토어 등)
│
├── src/                             # 소스 코드
│   ├── data/                        # 데이터 디렉토리
│   │   ├── raw/                     # 크롤링한 원본 문서
│   │   ├── processed/               # 처리된 데이터
│   │   │   └── airflow_vectors/     # FAISS 벡터 인덱스 저장 위치
│   │   └── cache/                   # 캐시 파일
│   │
│   ├── embeddings/                  # 임베딩 관련 모듈 (TODO)
│   │   └── __init__.py
│   │
│   ├── mcp_server/                  # MCP 서버 구현 (TODO)
│   │   └── __init__.py
│   │
│   ├── retrieval/                   # RAG 검색 로직 (TODO)
│   │   └── __init__.py
│   │
│   └── utils/                       # 유틸리티
│       ├── config.py                # ✅ 설정 로더 (완료)
│       └── models.py                # ✅ LLM/Embedding 모델 팩토리 (완료)
│
├── tests/                           # 테스트
│   └── test_setup.py                # ✅ 기본 설정 테스트 (완료)
│
├── .env                             # 환경 변수 (API 키, 경로 등)
├── pyproject.toml                   # 프로젝트 설정 및 의존성
└── main.py                          # 메인 엔트리포인트 (TODO)
```

---

## 🔑 핵심 파일 설명

### 1. 설정 파일

#### [config/config.yaml](config/config.yaml)
시스템 전체 설정을 관리하는 YAML 파일
- **embeddings**: Gemini embedding-001 모델 설정 (768차원)
- **text_splitter**: 문서 청킹 설정 (chunk_size=1000, overlap=200)
- **vector_store**: FAISS 벡터 스토어 경로 및 인덱스 타입
- **retrieval**: 검색 파라미터 (k=5, threshold=0.7)
- **llm**: Gemini 2.5-flash 모델 설정
- **airflow_docs**: 크롤링할 Airflow 문서 섹션 정의

#### [.env](.env)
민감한 정보 및 환경변수
- `GOOGLE_API_KEY`: Gemini API 키
- `EMBEDDING_MODEL`, `LLM_MODEL`: 모델 이름
- `VECTOR_STORE_PATH`: 벡터 DB 저장 경로
- RAG 파라미터들

---

### 2. 유틸리티 모듈 (완료 ✅)

#### [src/utils/config.py](src/utils/config.py:1-64)
Pydantic 기반 설정 관리
- `Config` 클래스: 전체 설정을 타입 안전하게 관리
- `load_config()`: YAML → Pydantic 모델 변환
- 환경변수 자동 로드 (dotenv)

**주요 클래스:**
- `EmbeddingsConfig`: 임베딩 모델 설정
- `TextSplitterConfig`: 텍스트 분할 전략
- `VectorStoreConfig`: 벡터 DB 경로/타입
- `RetrievalConfig`: 검색 파라미터
- `LLMConfig`: LLM 모델 설정
- `AirflowDocsConfig`: 크롤링 대상 문서

#### [src/utils/models.py](src/utils/models.py:1-27)
LLM 및 임베딩 모델 팩토리
- `get_embeddings()`: GoogleGenerativeAIEmbeddings 인스턴스 생성
- `get_llm()`: ChatGoogleGenerativeAI 인스턴스 생성
- config 기반 동적 모델 로딩

---

### 3. 테스트 (완료 ✅)

#### [tests/test_setup.py](tests/test_setup.py:1-42)
Gemini 통합 테스트
- `test_config()`: 설정 로드 확인
- `test_embeddings()`: 임베딩 API 동작 확인
- `test_llm()`: LLM API 동작 확인

**실행 방법:**
```bash
cd airflow-mcp-rag
python tests/test_setup.py
```

---

## 🚀 다음 구현 단계

### Phase 1: 데이터 수집 (src/data/)
**파일 생성 예정:**
- `src/data/crawler.py`: Airflow 문서 크롤러
  - BeautifulSoup4 + requests 사용
  - config.yaml의 `airflow_docs.sections` 기반 크롤링
  - 결과 저장: `src/data/raw/`

### Phase 2: 임베딩 & 벡터화 (src/embeddings/)
**파일 생성 예정:**
- `src/embeddings/document_processor.py`: 문서 전처리 및 청킹
  - LangChain의 RecursiveCharacterTextSplitter 사용
  - config의 `text_splitter` 설정 적용
- `src/embeddings/vector_store.py`: FAISS 벡터 스토어 생성
  - `get_embeddings()` 사용
  - 인덱스 저장: `src/data/processed/airflow_vectors/`

### Phase 3: RAG 검색 시스템 (src/retrieval/)
**파일 생성 예정:**
- `src/retrieval/retriever.py`: 벡터 검색 로직
  - FAISS similarity search
  - config의 `retrieval.k`, `score_threshold` 적용
- `src/retrieval/rag_chain.py`: LangChain RAG 체인
  - Retriever + LLM 연결
  - Prompt 템플릿 정의

### Phase 4: MCP 서버 (src/mcp_server/)
**파일 생성 예정:**
- `src/mcp_server/server.py`: MCP 프로토콜 서버
  - mcp 패키지 활용
  - RAG chain 통합
  - Tool/Resource 노출

### Phase 5: 메인 통합
**수정 예정:**
- `main.py`: MCP 서버 실행 엔트리포인트

---

## 📦 의존성

현재 설치된 주요 패키지:
```toml
langchain >= 0.1.0                # RAG 프레임워크
langchain-google-genai >= 4.1.3   # Gemini 통합
faiss-cpu >= 1.7.4                # 벡터 검색
beautifulsoup4 >= 4.12.3          # 웹 크롤링
mcp >= 0.9.0                      # MCP 서버
pydantic >= 2.5.3                 # 설정 관리
```

**설치 확인:**
```bash
cd airflow-mcp-rag
uv sync  # 또는 pip install -e .
```

---

## 🔍 빠른 파일 찾기

### 설정 관련
```bash
# 설정 파일
airflow-mcp-rag/config/config.yaml
airflow-mcp-rag/.env

# 설정 로더
airflow-mcp-rag/src/utils/config.py
```

### 모델 관련
```bash
# 임베딩/LLM 팩토리
airflow-mcp-rag/src/utils/models.py
```

### 데이터 저장 경로
```bash
# 원본 문서
airflow-mcp-rag/src/data/raw/

# 벡터 인덱스
airflow-mcp-rag/src/data/processed/airflow_vectors/

# 캐시
airflow-mcp-rag/src/data/cache/
```

### 테스트
```bash
# 설정 테스트
airflow-mcp-rag/tests/test_setup.py
```

---

## 💡 개발 팁

1. **설정 변경**: `config/config.yaml` 수정 후 재실행
2. **API 키 관리**: `.env` 파일 (절대 커밋하지 말 것!)
3. **테스트 우선**: 각 단계마다 `tests/` 에 테스트 추가
4. **타입 체크**: Pydantic 덕분에 설정 타입 안전성 보장
5. **모듈화**: 각 기능을 독립적인 모듈로 분리

---

## ⚡ 현재 상태

✅ **완료:**
- 프로젝트 구조 설정
- 의존성 관리 (pyproject.toml)
- 설정 시스템 (config.py)
- 모델 팩토리 (models.py)
- Gemini API 연동 테스트

🚧 **TODO:**
- [ ] Airflow 문서 크롤러
- [ ] 문서 전처리 및 청킹
- [ ] FAISS 벡터 스토어 생성
- [ ] RAG 검색 로직
- [ ] MCP 서버 구현
- [ ] 통합 테스트

---

## 📖 참고 링크

- [LangChain 문서](https://python.langchain.com/)
- [Gemini API](https://ai.google.dev/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Airflow 문서](https://airflow.apache.org/docs/)
