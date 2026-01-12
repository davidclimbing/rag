# Airflow MCP RAG Agent - Architecture

## 개요

Airflow DAG를 자동으로 생성하고 관리하는 RAG 기반 MCP 서버

## 핵심 컨셉

사용자가 자연어로 데이터 파이프라인 작업을 요청하면:
1. RAG가 Airflow 문서에서 관련 패턴 검색
2. LLM이 적절한 DAG 코드 생성
3. Airflow에 배포 및 실행
4. 결과 모니터링 및 리턴

## 시스템 아키텍처

```
┌─────────────────┐
│   User Request  │  "SQLite 테이블을 DuckDB로 옮겨줘"
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│              MCP Server                         │
│  ┌───────────────────────────────────────────┐ │
│  │         RAG Agent                         │ │
│  │  ┌─────────────┐    ┌─────────────────┐  │ │
│  │  │  Retriever  │───▶│   LLM (Gemini)  │  │ │
│  │  │  (FAISS)    │    │   DAG Generator │  │ │
│  │  └─────────────┘    └─────────────────┘  │ │
│  └───────────────────────────────────────────┘ │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         Airflow Management Layer                │
│  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ DAG Writer   │  │   Airflow REST API      │ │
│  │ (File I/O)   │  │   (Trigger/Monitor)     │ │
│  └──────────────┘  └─────────────────────────┘ │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│           Apache Airflow                        │
│  ┌──────────────────────────────────────────┐  │
│  │  Generated DAGs (dags/*.py)              │  │
│  │  - sqlite_to_duckdb_migration.py         │  │
│  │  - data_quality_check.py                 │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## 컴포넌트 상세

### 1. RAG Context (Knowledge Base)

**문서 소스:**
- Airflow 공식 문서 (Concepts, Operators, Best Practices)
- Database 작업 패턴 (SQLite, DuckDB, PostgreSQL 등)
- DAG 예제 템플릿
- 에러 핸들링 가이드

**저장 위치:**
- `src/data/raw/` - 마크다운 문서
- `src/data/processed/airflow_vectors/` - FAISS 벡터 인덱스

### 2. Vector Store

**기술 스택:**
- Embeddings: Google Gemini embedding-001 (768 dim)
- Vector DB: FAISS (IndexFlatL2)
- Text Splitter: RecursiveCharacterTextSplitter (chunk_size=1000)

**검색 전략:**
- Similarity search (k=5)
- Score threshold: 0.7
- Metadata filtering (doc_type, category)

### 3. LLM Agent

**모델:**
- Google Gemini 2.5-flash (cost-effective)
- Temperature: 0 (deterministic)
- Max tokens: 2048

**Agent 역할:**
1. **Intent Understanding**: 사용자 요청 분석
2. **Context Retrieval**: 관련 문서 검색
3. **Code Generation**: DAG Python 코드 생성
4. **Validation**: 생성된 코드 검증
5. **Execution Planning**: 실행 순서 결정

### 4. DAG Generator

**입력:**
- 사용자 요청 (자연어)
- 검색된 RAG 컨텍스트
- 데이터베이스 스키마 정보

**출력:**
- 완전한 Airflow DAG 코드 (Python)
- DAG 메타데이터 (schedule, tags, 등)

**생성 패턴:**
```python
# Template structure
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def task_function():
    # Generated logic here
    pass

with DAG(
    dag_id='generated_dag_name',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['generated', 'rag']
) as dag:
    task = PythonOperator(
        task_id='task_name',
        python_callable=task_function
    )
```

### 5. Airflow Interface

**DAG 배포:**
- DAG 파일 작성: `$AIRFLOW_HOME/dags/`
- 자동 로드 대기 (dag_dir_list_interval)
- 또는 API로 즉시 트리거

**REST API 연동:**
- `POST /dags/{dag_id}/dagRuns` - DAG 실행
- `GET /dags/{dag_id}/dagRuns/{dag_run_id}` - 상태 조회
- `GET /dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances` - 태스크 로그
- `PATCH /dags/{dag_id}` - DAG 활성화/비활성화

### 6. MCP Server

**Protocol:**
- Model Context Protocol (MCP)
- Stdio transport

**Tools 노출:**
```typescript
{
  "create_dag": {
    "description": "Create and deploy an Airflow DAG",
    "inputSchema": {
      "task_description": "string",
      "source_db": "string",
      "target_db": "string"
    }
  },
  "run_dag": {
    "description": "Execute a DAG",
    "inputSchema": {
      "dag_id": "string"
    }
  },
  "check_dag_status": {
    "description": "Monitor DAG execution",
    "inputSchema": {
      "dag_id": "string",
      "run_id": "string"
    }
  }
}
```

## 데이터 플로우

### 케이스: SQLite → DuckDB 마이그레이션

**1. 사용자 요청:**
```
"SQLite의 events 테이블에서 event_id, user_id, event_type, timestamp
컬럼만 선택해서 DuckDB의 analytics.duckdb 파일로 옮겨줘"
```

**2. RAG 검색:**
```
Query: "SQLite DuckDB migration Airflow"
Retrieved Docs:
- database_migration_guide.md (score: 0.92)
- database_schemas.md (score: 0.88)
- airflow_database_operators.md (score: 0.85)
```

**3. LLM 생성 (DAG 코드):**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime

def migrate_sqlite_to_duckdb():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('src/data/raw/sample_logs.db')

    # Extract data
    query = """
    SELECT event_id, user_id, event_type, timestamp
    FROM events
    """
    df = pd.read_sql_query(query, sqlite_conn)
    sqlite_conn.close()

    # Connect to DuckDB
    duck_conn = duckdb.connect('src/data/processed/analytics.duckdb')

    # Create table and insert
    duck_conn.execute("""
        CREATE TABLE IF NOT EXISTS events_core (
            event_id BIGINT PRIMARY KEY,
            user_id INTEGER,
            event_type VARCHAR(20),
            event_time TIMESTAMP
        )
    """)

    duck_conn.execute("INSERT INTO events_core SELECT * FROM df")
    duck_conn.close()

with DAG(
    dag_id='sqlite_to_duckdb_migration',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['migration', 'rag-generated']
) as dag:
    migrate_task = PythonOperator(
        task_id='migrate_events',
        python_callable=migrate_sqlite_to_duckdb
    )
```

**4. DAG 배포:**
- 파일 저장: `$AIRFLOW_HOME/dags/sqlite_to_duckdb_migration.py`
- Airflow가 자동 감지 (30초 이내)

**5. 실행 및 모니터링:**
```python
# Trigger via API
POST /api/v1/dags/sqlite_to_duckdb_migration/dagRuns
{
  "conf": {},
  "logical_date": "2024-01-12T15:00:00Z"
}

# Monitor
GET /api/v1/dags/sqlite_to_duckdb_migration/dagRuns/{run_id}
Response: {"state": "success"}
```

**6. 결과 리턴:**
```
✅ Migration completed successfully!
- DAG ID: sqlite_to_duckdb_migration
- Run ID: manual__2024-01-12T15:00:00+00:00
- Duration: 2.3 seconds
- Rows migrated: 2,000
- Target: src/data/processed/analytics.duckdb
```

## 기술 스택

### Backend
- **Language**: Python 3.11+
- **RAG Framework**: LangChain
- **Vector Store**: FAISS
- **LLM**: Google Gemini (via langchain-google-genai)
- **Workflow Engine**: Apache Airflow
- **MCP**: mcp Python package

### Dependencies
```toml
langchain >= 0.1.0
langchain-google-genai >= 4.1.3
faiss-cpu >= 1.7.4
apache-airflow >= 2.8.0
mcp >= 0.9.0
duckdb >= 0.9.0
```

### Infrastructure
- **Airflow Deployment**: Local (standalone) / Docker
- **Storage**: Local filesystem
- **Database**: SQLite (source), DuckDB (target)

## 확장성 고려사항

### 1. 다양한 소스/타겟 지원
```python
# 현재: SQLite → DuckDB
# 확장: PostgreSQL, MySQL, Snowflake, BigQuery 등

SUPPORTED_SOURCES = ['sqlite', 'postgresql', 'mysql']
SUPPORTED_TARGETS = ['duckdb', 'postgresql', 'bigquery']
```

### 2. 복잡한 변환 로직
```python
# 단순 컬럼 선택
SELECT col1, col2 FROM table

# 복잡한 변환
SELECT
    col1,
    UPPER(col2) as col2_normalized,
    CAST(col3 AS DATE) as col3_date,
    col4 * 1.1 as col4_adjusted
FROM table
WHERE col5 > threshold
```

### 3. Multi-step DAG
```python
# Sequential tasks
extract >> transform >> load >> validate

# Parallel tasks
[extract_source1, extract_source2] >> merge >> load
```

### 4. 스케줄링
```python
# 현재: Manual trigger (schedule=None)
# 확장: Cron expressions

schedule='@daily'
schedule='0 */4 * * *'  # Every 4 hours
```

### 5. 에러 핸들링
```python
# Retry logic
retries=3
retry_delay=timedelta(minutes=5)

# Alerts
on_failure_callback=send_slack_alert
```

## 보안 고려사항

1. **Credential Management**
   - Airflow Connections로 DB 인증 정보 관리
   - `.env` 파일은 절대 커밋 안 함
   - Secret Backend 통합 (HashiCorp Vault, AWS Secrets Manager)

2. **Code Injection Prevention**
   - LLM 생성 코드는 항상 validation
   - Sandboxed execution 환경
   - Whitelist 기반 operator 제한

3. **Access Control**
   - MCP 서버 인증
   - Airflow RBAC 활용
   - API rate limiting

## 성능 최적화

1. **Vector Search**
   - FAISS IVF index (대규모 문서)
   - Caching frequently accessed docs

2. **LLM Inference**
   - Prompt caching (similar requests)
   - Batch processing for multiple DAGs

3. **Airflow**
   - Connection pooling
   - Parallelism configuration
   - XCom alternative (S3, NFS)

## 모니터링

1. **RAG Quality**
   - Retrieval relevance score
   - LLM generation success rate
   - User feedback loop

2. **DAG Execution**
   - Success/failure rate
   - Execution duration
   - Resource usage

3. **System Health**
   - MCP server uptime
   - Airflow scheduler lag
   - Vector store query latency

## 개발 로드맵

### Phase 1: MVP (Current)
- [x] 기본 프로젝트 구조
- [x] 샘플 데이터 생성
- [ ] RAG 문서 작성 (Airflow patterns)
- [ ] Vector store 구축
- [ ] 기본 DAG generator
- [ ] SQLite → DuckDB 검증

### Phase 2: Core Features
- [ ] Airflow REST API 통합
- [ ] DAG 실행 모니터링
- [ ] 에러 핸들링
- [ ] MCP server 구현

### Phase 3: Production Ready
- [ ] 다양한 DB 지원
- [ ] Complex transformations
- [ ] Multi-step DAGs
- [ ] Scheduling support
- [ ] Comprehensive testing

### Phase 4: Advanced
- [ ] DAG 수정/삭제
- [ ] Version control integration
- [ ] CI/CD pipeline
- [ ] Web UI dashboard
- [ ] Multi-tenancy

## 디렉토리 구조

```
airflow-mcp-rag/
├── config/
│   └── config.yaml              # RAG/LLM 설정
├── src/
│   ├── data/
│   │   ├── raw/                 # RAG 문서 (마크다운)
│   │   │   ├── database_migration_guide.md
│   │   │   ├── database_schemas.md
│   │   │   ├── airflow_dag_patterns.md      # TODO
│   │   │   └── sample_logs.db  # 샘플 SQLite DB
│   │   ├── processed/
│   │   │   ├── airflow_vectors/ # FAISS 인덱스
│   │   │   └── analytics.duckdb # 마이그레이션 결과
│   │   └── cache/
│   ├── embeddings/
│   │   ├── document_loader.py   # 문서 로드 및 청킹
│   │   └── vector_store.py      # FAISS 인덱스 생성/로드
│   ├── retrieval/
│   │   ├── retriever.py         # RAG retriever
│   │   └── rag_chain.py         # LangChain RAG chain
│   ├── airflow_manager/         # NEW
│   │   ├── dag_generator.py     # DAG 코드 생성
│   │   ├── dag_writer.py        # DAG 파일 쓰기
│   │   └── api_client.py        # Airflow REST API
│   ├── mcp_server/
│   │   └── server.py            # MCP protocol server
│   └── utils/
│       ├── config.py            # ✅ 설정 로더
│       └── models.py            # ✅ LLM/Embedding 팩토리
├── tests/
│   ├── test_setup.py            # ✅ 기본 테스트
│   ├── test_rag.py              # TODO
│   └── test_dag_generation.py  # TODO
├── dags/                        # Airflow DAG 저장소
│   └── .gitkeep
├── .env
├── pyproject.toml
└── main.py
```

## 참고 자료

- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [LangChain RAG](https://python.langchain.com/docs/use_cases/question_answering/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [FAISS](https://github.com/facebookresearch/faiss)
