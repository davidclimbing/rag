"""
Auto-generated DAG for SQLite to DuckDB migration
Source: events
Target: events_migrated
Columns: event_id, user_id, event_type, timestamp
Generated at: 2026-01-12 16:05:13
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime
import pandas as pd


def migrate_events(**context):
    """Migrate events from SQLite to DuckDB"""

    # Configuration
    source_db = 'src/data/raw/sample_logs.db'
    source_table = 'events'
    columns = ['event_id', 'user_id', 'event_type', 'timestamp']
    target_db = 'src/data/processed/analytics.duckdb'
    target_table = 'events_migrated'

    print(f"Starting migration: {source_table} -> {target_table}")
    print(f"Columns: {columns}")

    # Extract from SQLite
    print("\nStep 1: Extracting from SQLite...")
    sqlite_conn = sqlite3.connect(source_db)

    columns_str = ', '.join(columns)
    query = f"SELECT {columns_str} FROM {source_table}"

    df = pd.read_sql_query(query, sqlite_conn)
    sqlite_conn.close()

    row_count = len(df)
    print(f"✓ Extracted {row_count} rows")

    # Load to DuckDB
    print("\nStep 2: Loading to DuckDB...")
    duck_conn = duckdb.connect(target_db)

    # Drop if exists and create new table from DataFrame
    duck_conn.execute(f"DROP TABLE IF EXISTS {target_table}")
    duck_conn.execute(f"CREATE TABLE {target_table} AS SELECT * FROM df")

    # Verify
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
        'columns': columns
    }


with DAG(
    dag_id='sqlite_to_duckdb_events_1768201513',
    description='Migrate events from SQLite to DuckDB',
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['migration', 'sqlite', 'duckdb', 'auto-generated']
) as dag:

    migrate_task = PythonOperator(
        task_id='migrate_events',
        python_callable=migrate_events,
        provide_context=True
    )
