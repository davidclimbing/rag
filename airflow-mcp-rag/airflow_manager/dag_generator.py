"""
템플릿 기반 Airflow DAG 생성기
RAG 없이 빠르게 테스트하기 위한 간단한 버전
"""
import time
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class MigrationRequest:
    """마이그레이션 요청 정보"""
    source_db: str
    source_table: str
    columns: List[str]
    target_db: str
    target_table: str


def generate_migration_dag(request: MigrationRequest) -> str:
    """
    SQLite → DuckDB 마이그레이션 DAG 코드 생성

    Args:
        request: 마이그레이션 요청 정보

    Returns:
        생성된 DAG Python 코드
    """
    # 고유한 DAG ID 생성
    timestamp = int(time.time())
    dag_id = f"sqlite_to_duckdb_{request.source_table}_{timestamp}"

    # 컬럼 리스트 문자열화
    columns_str = ', '.join(request.columns)
    columns_python_list = repr(request.columns)

    # DAG 코드 생성
    dag_code = f'''"""
Auto-generated DAG for SQLite to DuckDB migration
Source: {request.source_table}
Target: {request.target_table}
Columns: {columns_str}
Generated at: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime
import pandas as pd


def migrate_{request.source_table}(**context):
    """Migrate {request.source_table} from SQLite to DuckDB"""

    # Configuration
    source_db = '{request.source_db}'
    source_table = '{request.source_table}'
    columns = {columns_python_list}
    target_db = '{request.target_db}'
    target_table = '{request.target_table}'

    print(f"Starting migration: {{source_table}} -> {{target_table}}")
    print(f"Columns: {{columns}}")

    # Extract from SQLite
    print("\\nStep 1: Extracting from SQLite...")
    sqlite_conn = sqlite3.connect(source_db)

    columns_str = ', '.join(columns)
    query = f"SELECT {{columns_str}} FROM {{source_table}}"

    df = pd.read_sql_query(query, sqlite_conn)
    sqlite_conn.close()

    row_count = len(df)
    print(f"✓ Extracted {{row_count}} rows")

    # Load to DuckDB
    print("\\nStep 2: Loading to DuckDB...")
    duck_conn = duckdb.connect(target_db)

    # Drop if exists and create new table from DataFrame
    duck_conn.execute(f"DROP TABLE IF EXISTS {{target_table}}")
    duck_conn.execute(f"CREATE TABLE {{target_table}} AS SELECT * FROM df")

    # Verify
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
        'columns': columns
    }}


with DAG(
    dag_id='{dag_id}',
    description='Migrate {request.source_table} from SQLite to DuckDB',
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['migration', 'sqlite', 'duckdb', 'auto-generated']
) as dag:

    migrate_task = PythonOperator(
        task_id='migrate_{request.source_table}',
        python_callable=migrate_{request.source_table},
        provide_context=True
    )
'''

    return dag_code


def parse_user_request(user_input: str) -> MigrationRequest:
    """
    사용자 요청을 파싱 (간단한 버전)

    Example input:
    "SQLite의 events 테이블에서 event_id, user_id, timestamp 컬럼을 DuckDB로 옮겨줘"

    Args:
        user_input: 사용자 자연어 요청

    Returns:
        MigrationRequest 객체
    """
    # 간단한 휴리스틱 파싱 (실제로는 LLM이 해야 함)
    # 여기서는 데모용 하드코딩

    return MigrationRequest(
        source_db='src/data/raw/sample_logs.db',
        source_table='events',
        columns=['event_id', 'user_id', 'event_type', 'timestamp'],
        target_db='src/data/processed/analytics.duckdb',
        target_table='events_migrated'
    )


if __name__ == "__main__":
    # 테스트
    print("=" * 60)
    print("DAG Generator Test")
    print("=" * 60)

    # 마이그레이션 요청 생성
    request = MigrationRequest(
        source_db='src/data/raw/sample_logs.db',
        source_table='events',
        columns=['event_id', 'user_id', 'event_type', 'timestamp'],
        target_db='src/data/processed/analytics.duckdb',
        target_table='events_migrated'
    )

    # DAG 코드 생성
    dag_code = generate_migration_dag(request)

    print("\\nGenerated DAG code:")
    print("-" * 60)
    print(dag_code)
    print("-" * 60)

    # 파일로 저장
    output_file = f"dags/sqlite_to_duckdb_{request.source_table}_{int(time.time())}.py"
    with open(output_file, 'w') as f:
        f.write(dag_code)

    print(f"\\n✓ DAG saved to: {output_file}")
