"""
LLM-generated DAG for database migration
Source: sessions
Target: sessions_long
Generated at: 2026-01-12 16:21:32
"""
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime
import pandas as pd


def migrate_sessions_long(**context):
    """Migrate sessions to sessions_long"""

    # Configuration
    source_db = 'src/data/raw/sample_logs.db'
    source_table = 'sessions'
    target_db = 'src/data/processed/analytics.duckdb'
    target_table = 'sessions_long'

    print(f"Starting migration: {source_table} -> {target_table}")

    # Extract from SQLite
    print("\nStep 1: Extracting from SQLite...")
    sqlite_conn = sqlite3.connect(source_db)

    # Build query
    columns_str = '*'
    query = f"SELECT {columns_str} FROM {source_table}"

    # Add WHERE clause if provided
    where_clause = "duration_seconds >= 300"
    if where_clause:
        query += f" WHERE {where_clause}"

    # Add LIMIT if provided
    limit = 50
    if limit:
        query += f" LIMIT {limit}"

    print(f"Query: {query}")

    df = pd.read_sql_query(query, sqlite_conn)
    sqlite_conn.close()

    row_count = len(df)
    print(f"✓ Extracted {row_count} rows")
    print(f"  Sample:\n{df.head()}")

    # Load to DuckDB
    print("\nStep 2: Loading to DuckDB...")
    duck_conn = duckdb.connect(target_db)

    duck_conn.execute(f"DROP TABLE IF EXISTS {target_table}")
    duck_conn.execute(f"CREATE TABLE {target_table} AS SELECT * FROM df")

    result = duck_conn.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()
    duck_conn.close()

    print(f"✓ Loaded {result[0]} rows to {target_table}")

    # Validation
    if result[0] != row_count:
        raise ValueError(f"Row count mismatch: {row_count} != {result[0]}")

    print("\n✅ Migration completed successfully!")

    return {
        'source': source_table,
        'target': target_table,
        'rows_migrated': result[0],
        'where_clause': where_clause,
        'limit': limit
    }


with DAG(
    dag_id='llm_migration_sessions_long_1768202492',
    description='Migrate sessions to sessions_long',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['migration', 'sqlite', 'duckdb', 'llm-generated']
) as dag:

    migrate_task = PythonOperator(
        task_id='migrate_sessions_long',
        python_callable=migrate_sessions_long
    )
