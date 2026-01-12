"""
LLM 기반 Airflow DAG 생성기
사용자의 자연어 요청을 파싱하고 DAG 코드를 생성
"""
import time
from typing import Dict, Optional
from dataclasses import dataclass
from src.utils.models import get_llm


@dataclass
class MigrationConfig:
    """파싱된 마이그레이션 설정"""
    source_db: str
    source_table: str
    columns: list[str]
    target_db: str
    target_table: str
    where_clause: Optional[str] = None
    limit: Optional[int] = None


PARSER_PROMPT = """You are an expert at parsing database migration requests.

Parse the following user request and extract migration details:

User Request: {user_request}

Available source database: src/data/raw/sample_logs.db
Available tables: users, sessions, events

Extract and return ONLY a JSON object with these fields:
{{
  "source_table": "table name",
  "columns": ["column1", "column2", ...],
  "where_clause": "SQL WHERE condition (without WHERE keyword)" or null,
  "limit": number or null,
  "target_table": "suggested target table name"
}}

Examples:
- "events 테이블에서 event_id, user_id 컬럼만 가져와"
  → {{"source_table": "events", "columns": ["event_id", "user_id"], "where_clause": null, "limit": null, "target_table": "events_migrated"}}

- "users 테이블에서 is_premium이 1인 것만 가져와"
  → {{"source_table": "users", "columns": ["*"], "where_clause": "is_premium = 1", "limit": null, "target_table": "users_premium"}}

- "sessions에서 duration_seconds가 300 이상인 것 100개만"
  → {{"source_table": "sessions", "columns": ["*"], "where_clause": "duration_seconds >= 300", "limit": 100, "target_table": "sessions_long"}}

Return ONLY the JSON object, no additional text.
"""


DAG_GENERATION_PROMPT = """You are an expert Airflow DAG developer. Generate a COMPLETE, working Airflow DAG code.

Migration Details:
- Source DB: {source_db}
- Source Table: {source_table}
- Columns: {columns}
- Where Clause: {where_clause}
- Limit: {limit}
- Target DB: {target_db}
- Target Table: {target_table}

Generate COMPLETE Python code following this EXACT structure:

```python
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime
import pandas as pd
import time

def migrate_{target_table}(**context):
    # Configuration
    source_db = '{source_db}'
    source_table = '{source_table}'
    target_db = '{target_db}'
    target_table = '{target_table}'

    print(f"Starting migration: {{source_table}} -> {{target_table}}")

    # Extract from SQLite
    print("Step 1: Extracting from SQLite...")
    sqlite_conn = sqlite3.connect(source_db)

    # Build query with columns, WHERE, LIMIT
    columns_str = '{columns_str}'  # or '*'
    query = f"SELECT {{columns_str}} FROM {{source_table}}"

    # Add WHERE clause if provided
    where_clause = {where_clause_value}
    if where_clause:
        query += f" WHERE {{where_clause}}"

    # Add LIMIT if provided
    limit = {limit_value}
    if limit:
        query += f" LIMIT {{limit}}"

    df = pd.read_sql_query(query, sqlite_conn)
    sqlite_conn.close()

    row_count = len(df)
    print(f"✓ Extracted {{row_count}} rows")

    # Load to DuckDB
    print("Step 2: Loading to DuckDB...")
    duck_conn = duckdb.connect(target_db)
    duck_conn.execute(f"DROP TABLE IF EXISTS {{target_table}}")
    duck_conn.execute(f"CREATE TABLE {{target_table}} AS SELECT * FROM df")

    result = duck_conn.execute(f"SELECT COUNT(*) FROM {{target_table}}").fetchone()
    duck_conn.close()

    print(f"✓ Loaded {{result[0]}} rows")

    if result[0] != row_count:
        raise ValueError(f"Row count mismatch!")

    print("✅ Migration completed!")
    return {{'rows_migrated': result[0]}}

with DAG(
    dag_id='migration_{{target_table}}_' + str(int(time.time())),
    description='Migrate {source_table} to {target_table}',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['migration', 'sqlite', 'duckdb', 'llm-generated']
) as dag:
    migrate_task = PythonOperator(
        task_id='migrate_{target_table}',
        python_callable=migrate_{target_table}
    )
```

Return ONLY the complete Python code above, filling in the placeholders. NO markdown blocks, NO explanations."""


def parse_user_request(user_request: str) -> MigrationConfig:
    """
    LLM을 사용하여 사용자 요청 파싱

    Args:
        user_request: 사용자 자연어 요청

    Returns:
        MigrationConfig 객체
    """
    print(f"Parsing request: {user_request}")

    llm = get_llm()

    # LLM으로 요청 파싱
    prompt = PARSER_PROMPT.format(user_request=user_request)
    response = llm.invoke(prompt)

    print(f"LLM response: {response.content}")

    # JSON 파싱
    import json
    try:
        # JSON 추출 (코드 블록이 있을 수 있음)
        content = response.content.strip()
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        parsed = json.loads(content)

        # MigrationConfig 생성
        config = MigrationConfig(
            source_db='src/data/raw/sample_logs.db',
            source_table=parsed['source_table'],
            columns=parsed['columns'] if parsed['columns'] != ['*'] else None,
            target_db='src/data/processed/analytics.duckdb',
            target_table=parsed['target_table'],
            where_clause=parsed.get('where_clause'),
            limit=parsed.get('limit')
        )

        print(f"✓ Parsed config: {config}")
        return config

    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Response content: {response.content}")
        raise


def generate_dag_code(config: MigrationConfig) -> str:
    """
    템플릿 기반으로 DAG 코드 생성 (LLM 대신)

    Args:
        config: MigrationConfig 객체

    Returns:
        생성된 DAG Python 코드
    """
    print(f"\nGenerating DAG code for: {config.source_table} -> {config.target_table}")

    # 컬럼 처리
    if config.columns:
        columns_str = ', '.join(config.columns)
    else:
        columns_str = '*'

    # WHERE 절 처리
    where_clause_str = f'"{config.where_clause}"' if config.where_clause else 'None'

    # LIMIT 처리
    limit_str = str(config.limit) if config.limit else 'None'

    # 타임스탬프
    timestamp = int(time.time())

    # DAG 코드 템플릿
    dag_code = f'''"""
LLM-generated DAG for database migration
Source: {config.source_table}
Target: {config.target_table}
Generated at: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime
import pandas as pd


def migrate_{config.target_table}(**context):
    """Migrate {config.source_table} to {config.target_table}"""

    # Configuration
    source_db = '{config.source_db}'
    source_table = '{config.source_table}'
    target_db = '{config.target_db}'
    target_table = '{config.target_table}'

    print(f"Starting migration: {{source_table}} -> {{target_table}}")

    # Extract from SQLite
    print("\\nStep 1: Extracting from SQLite...")
    sqlite_conn = sqlite3.connect(source_db)

    # Build query
    columns_str = '{columns_str}'
    query = f"SELECT {{columns_str}} FROM {{source_table}}"

    # Add WHERE clause if provided
    where_clause = {where_clause_str}
    if where_clause:
        query += f" WHERE {{where_clause}}"

    # Add LIMIT if provided
    limit = {limit_str}
    if limit:
        query += f" LIMIT {{limit}}"

    print(f"Query: {{query}}")

    df = pd.read_sql_query(query, sqlite_conn)
    sqlite_conn.close()

    row_count = len(df)
    print(f"✓ Extracted {{row_count}} rows")
    print(f"  Sample:\\n{{df.head()}}")

    # Load to DuckDB
    print("\\nStep 2: Loading to DuckDB...")
    duck_conn = duckdb.connect(target_db)

    duck_conn.execute(f"DROP TABLE IF EXISTS {{target_table}}")
    duck_conn.execute(f"CREATE TABLE {{target_table}} AS SELECT * FROM df")

    result = duck_conn.execute(f"SELECT COUNT(*) FROM {{target_table}}").fetchone()
    duck_conn.close()

    print(f"✓ Loaded {{result[0]}} rows to {{target_table}}")

    # Validation
    if result[0] != row_count:
        raise ValueError(f"Row count mismatch: {{row_count}} != {{result[0]}}")

    print("\\n✅ Migration completed successfully!")

    return {{
        'source': source_table,
        'target': target_table,
        'rows_migrated': result[0],
        'where_clause': where_clause,
        'limit': limit
    }}


with DAG(
    dag_id='llm_migration_{config.target_table}_{timestamp}',
    description='Migrate {config.source_table} to {config.target_table}',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['migration', 'sqlite', 'duckdb', 'llm-generated']
) as dag:

    migrate_task = PythonOperator(
        task_id='migrate_{config.target_table}',
        python_callable=migrate_{config.target_table}
    )
'''

    print(f"✓ Generated {len(dag_code)} characters of code")

    return dag_code


def save_dag(dag_code: str, filename: Optional[str] = None) -> str:
    """
    DAG 코드를 파일로 저장

    Args:
        dag_code: DAG Python 코드
        filename: 파일명 (None이면 자동 생성)

    Returns:
        저장된 파일 경로
    """
    if filename is None:
        filename = f"llm_generated_dag_{int(time.time())}.py"

    filepath = f"dags/{filename}"

    with open(filepath, 'w') as f:
        f.write(dag_code)

    print(f"✓ DAG saved to: {filepath}")
    return filepath


def process_natural_language_request(user_request: str) -> Dict[str, str]:
    """
    자연어 요청을 받아 DAG 생성까지 전체 파이프라인 실행

    Args:
        user_request: 사용자 자연어 요청

    Returns:
        결과 딕셔너리 (config, dag_code, filepath)
    """
    print("=" * 60)
    print("LLM-based DAG Generation Pipeline")
    print("=" * 60)

    # 1. 요청 파싱
    print("\n[Step 1/3] Parsing user request...")
    config = parse_user_request(user_request)

    # 2. DAG 코드 생성
    print("\n[Step 2/3] Generating DAG code...")
    dag_code = generate_dag_code(config)

    # 3. 파일 저장
    print("\n[Step 3/3] Saving DAG file...")
    filepath = save_dag(dag_code)

    print("\n" + "=" * 60)
    print("✅ Pipeline completed successfully!")
    print("=" * 60)

    return {
        'config': config,
        'dag_code': dag_code,
        'filepath': filepath
    }


if __name__ == "__main__":
    # 테스트 케이스들
    test_requests = [
        "events 테이블에서 event_id, user_id, timestamp 컬럼만 DuckDB로 옮겨줘",
        "users 테이블에서 is_premium이 1인 사람들만 가져와",
        "sessions에서 duration_seconds가 300 이상인 것만 100개 가져와"
    ]

    # 첫 번째 요청만 테스트
    result = process_natural_language_request(test_requests[0])

    print("\n" + "=" * 60)
    print("Result:")
    print("=" * 60)
    print(f"Config: {result['config']}")
    print(f"File: {result['filepath']}")
    print(f"\nGenerated code preview (first 500 chars):")
    print(result['dag_code'][:500] + "...")
