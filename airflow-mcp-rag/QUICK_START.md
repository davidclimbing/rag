# Quick Start Guide

바로 실행해볼 수 있는 Use Case들

## 사전 준비

```bash
cd airflow-mcp-rag
```

## Use Case 1: 기본 컬럼 선택 마이그레이션

**요청:**
```bash
.venv/bin/python -c "
from airflow_manager.llm_dag_generator import process_natural_language_request

result = process_natural_language_request(
    'events 테이블에서 event_id, user_id, event_type 컬럼만 DuckDB로 옮겨줘'
)

print('\n생성된 파일:', result['filepath'])
"
```

**실행:**
```bash
# 생성된 DAG 실행 (파일명은 위에서 출력된 것 사용)
.venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from dags.llm_generated_dag_XXXXX import migrate_events_migrated
result = migrate_events_migrated()
print(result)
"
```

## Use Case 2: WHERE 조건으로 필터링

**요청:**
```bash
.venv/bin/python -c "
from airflow_manager.llm_dag_generator import process_natural_language_request

result = process_natural_language_request(
    'users 테이블에서 country가 KR인 사용자만 DuckDB로 옮겨줘'
)

print('\n생성된 파일:', result['filepath'])
"
```

**실행:**
```bash
.venv/bin/python -c "
import sys
sys.path.insert(0, '.')
from dags.llm_generated_dag_XXXXX import migrate_users_kr
result = migrate_users_kr()
print(result)
"
```

## Use Case 3: 숫자 비교 조건

**요청:**
```bash
.venv/bin/python -c "
from airflow_manager.llm_dag_generator import process_natural_language_request

result = process_natural_language_request(
    'sessions에서 duration_seconds가 1000 이상인 것만 DuckDB로 옮겨줘'
)

print('\n생성된 파일:', result['filepath'])
"
```

## Use Case 4: LIMIT로 개수 제한

**요청:**
```bash
.venv/bin/python -c "
from airflow_manager.llm_dag_generator import process_natural_language_request

result = process_natural_language_request(
    'events에서 최근 데이터 100개만 DuckDB로 옮겨줘'
)

print('\n생성된 파일:', result['filepath'])
"
```

## Use Case 5: WHERE + LIMIT 조합

**요청:**
```bash
.venv/bin/python -c "
from airflow_manager.llm_dag_generator import process_natural_language_request

result = process_natural_language_request(
    'events에서 event_type이 click인 것만 50개 DuckDB로 옮겨줘'
)

print('\n생성된 파일:', result['filepath'])
"
```

## Use Case 6: 프리미엄 유저 분석

**요청:**
```bash
.venv/bin/python -c "
from airflow_manager.llm_dag_generator import process_natural_language_request

result = process_natural_language_request(
    'users에서 is_premium이 1이고 total_sessions가 20 이상인 사람들만 가져와'
)

print('\n생성된 파일:', result['filepath'])
"
```

## 올인원 실행 스크립트

한 번에 여러 use case 실행:

```bash
.venv/bin/python run_use_cases.py
```

## 결과 확인

생성된 모든 테이블 확인:
```bash
.venv/bin/python -c "
import duckdb
conn = duckdb.connect('src/data/processed/analytics.duckdb')

print('=== 생성된 테이블 목록 ===')
tables = conn.execute('SHOW TABLES').fetchall()
for table in tables:
    count = conn.execute(f'SELECT COUNT(*) FROM {table[0]}').fetchone()[0]
    print(f'{table[0]}: {count} rows')

    # 샘플 데이터
    print(f'  Sample:')
    sample = conn.execute(f'SELECT * FROM {table[0]} LIMIT 3').fetchall()
    for row in sample:
        print(f'    {row}')
    print()

conn.close()
"
```

## 특정 테이블 상세 확인

```bash
.venv/bin/python -c "
import duckdb
conn = duckdb.connect('src/data/processed/analytics.duckdb')

# 테이블명 지정
table_name = 'users_premium'

# 스키마 확인
print(f'=== {table_name} 스키마 ===')
schema = conn.execute(f'DESCRIBE {table_name}').fetchall()
for col in schema:
    print(f'{col[0]}: {col[1]}')

# 데이터 확인
print(f'\n=== {table_name} 데이터 (10개) ===')
import pandas as pd
df = conn.execute(f'SELECT * FROM {table_name} LIMIT 10').fetchdf()
print(df)

conn.close()
"
```

## SQLite 원본 데이터 확인

```bash
.venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('src/data/raw/sample_logs.db')

# 테이블 목록
print('=== SQLite 테이블 ===')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
for table in tables:
    count = conn.execute(f'SELECT COUNT(*) FROM {table[0]}').fetchone()[0]
    print(f'{table[0]}: {count} rows')

conn.close()
"
```

## 팁

1. **생성된 파일 찾기**
   ```bash
   ls -lt dags/ | head -10
   ```

2. **마지막 생성된 DAG 실행**
   ```bash
   LAST_DAG=$(ls -t dags/llm_generated_dag_*.py | head -1)
   echo "실행: $LAST_DAG"
   .venv/bin/python "$LAST_DAG"
   ```

3. **모든 생성된 DAG 목록**
   ```bash
   ls -lh dags/llm_generated_dag_*.py
   ```

4. **DAG 파일 내용 확인**
   ```bash
   cat dags/llm_generated_dag_XXXXX.py
   ```
