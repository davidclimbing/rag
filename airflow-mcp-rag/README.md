# Airflow MCP RAG

자연어로 Airflow DAG를 생성하고 데이터베이스 마이그레이션을 자동화하는 시스템

## 🚀 빠른 시작

### 1. 모든 Use Case 한 번에 실행

```bash
cd airflow-mcp-rag
.venv/bin/python run_use_cases.py
```

이 명령어로 5가지 use case가 자동으로 실행됩니다:
- ✅ 기본 컬럼 선택
- ✅ WHERE 조건 필터링
- ✅ 숫자 비교
- ✅ LIMIT 제한
- ✅ WHERE + LIMIT 조합

### 2. 개별 Use Case 실행

자연어 요청으로 DAG 생성:

```bash
.venv/bin/python -c "
from airflow_manager.llm_dag_generator import process_natural_language_request

result = process_natural_language_request(
    'events 테이블에서 event_id, user_id 컬럼만 DuckDB로 옮겨줘'
)

print('생성된 파일:', result['filepath'])
"
```

생성된 DAG 실행:

```bash
.venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from dags.llm_generated_dag_XXXXX import migrate_XXXXX
result = migrate_XXXXX()
print(result)
"
```

### 3. 결과 확인

```bash
.venv/bin/python -c "
import duckdb
conn = duckdb.connect('src/data/processed/analytics.duckdb')

tables = conn.execute('SHOW TABLES').fetchall()
for table in tables:
    count = conn.execute(f'SELECT COUNT(*) FROM {table[0]}').fetchone()[0]
    print(f'{table[0]}: {count} rows')

conn.close()
"
```

## 📚 상세 가이드

더 많은 예제와 상세 설명은 다음 문서를 참고하세요:
- [QUICK_START.md](QUICK_START.md) - 다양한 use case 예제
- [ARCHITECTURE.md](../ARCHITECTURE.md) - 시스템 아키텍처
- [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) - 프로젝트 전체 구조

## 🎯 지원 기능

### 자연어 요청 예제

**컬럼 선택:**
```
"events 테이블에서 event_id, user_id, timestamp 컬럼만 가져와"
```

**WHERE 조건:**
```
"users에서 is_premium이 1인 사람들만 가져와"
"sessions에서 duration_seconds가 300 이상인 것만 가져와"
```

**LIMIT:**
```
"events에서 100개만 가져와"
```

**조합:**
```
"events에서 event_type이 'click'인 것 50개만 가져와"
```

## 🗄️ 데이터베이스 정보

### SQLite (원본)
- 위치: `src/data/raw/sample_logs.db`
- 테이블:
  - `users` - 100 rows
  - `sessions` - 500 rows
  - `events` - 2,000 rows

### DuckDB (타겟)
- 위치: `src/data/processed/analytics.duckdb`
- 자동 생성된 테이블들

## 🛠️ 기술 스택

- **LLM**: Google Gemini Flash (자연어 파싱)
- **Workflow**: Apache Airflow (DAG 생성 및 실행)
- **Database**: SQLite → DuckDB
- **Language**: Python 3.11+

## 📁 프로젝트 구조

```
airflow-mcp-rag/
├── airflow_manager/          # DAG 생성기
│   ├── dag_generator.py      # 템플릿 기반
│   └── llm_dag_generator.py  # LLM 기반
├── dags/                     # 생성된 Airflow DAG
├── src/
│   ├── data/                 # 샘플 데이터
│   │   ├── raw/             # SQLite DB + RAG 문서
│   │   └── processed/       # DuckDB 결과
│   ├── embeddings/          # RAG 벡터 스토어
│   └── utils/               # 설정 및 모델
├── run_use_cases.py         # 올인원 실행 스크립트
└── QUICK_START.md           # 빠른 시작 가이드
```

## 🧪 테스트 결과

| Use Case | 요청 | 결과 |
|----------|------|------|
| UC1 | 컬럼 선택 | ✅ 2,000 rows |
| UC2 | WHERE (boolean) | ✅ 44 rows |
| UC3 | WHERE (numeric) | ✅ 필터링 성공 |
| UC4 | LIMIT | ✅ 100 rows |
| UC5 | WHERE + LIMIT | ✅ 50 rows |

## 💡 다음 단계

- [ ] MCP 서버 구현
- [ ] Airflow REST API 통합
- [ ] RAG 벡터 스토어 활성화
- [ ] 복잡한 SQL 변환 지원
- [ ] Multi-step DAG 생성

## 🤝 기여

이슈나 개선 사항은 GitHub Issues로 제출해주세요.

## 📄 라이센스

MIT License
