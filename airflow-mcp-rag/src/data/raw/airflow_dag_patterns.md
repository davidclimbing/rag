# Airflow DAG Patterns and Examples

## Basic DAG Structure

### Minimal DAG Template

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def my_task_function():
    """Task logic goes here"""
    print("Task executed!")
    return "success"

with DAG(
    dag_id='my_dag_name',
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['example']
) as dag:

    task = PythonOperator(
        task_id='my_task',
        python_callable=my_task_function
    )
```

**Key Components:**
- `dag_id`: Unique identifier for the DAG
- `start_date`: When the DAG becomes active
- `schedule`: Cron expression or None for manual
- `catchup=False`: Don't backfill past runs
- `tags`: Categorize DAGs in UI

---

## Database Operations

### SQLite to DuckDB Migration Pattern

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime

def migrate_sqlite_to_duckdb(**context):
    """
    Migrate specific columns from SQLite to DuckDB

    Args:
        source_db: Path to SQLite database
        source_table: Source table name
        columns: List of columns to extract
        target_db: Path to DuckDB database
        target_table: Target table name
    """
    # Get parameters from DAG config
    conf = context.get('dag_run').conf or {}
    source_db = conf.get('source_db', 'src/data/raw/sample_logs.db')
    source_table = conf.get('source_table', 'events')
    columns = conf.get('columns', ['event_id', 'user_id', 'event_type', 'timestamp'])
    target_db = conf.get('target_db', 'src/data/processed/analytics.duckdb')
    target_table = conf.get('target_table', 'events_migrated')

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(source_db)
    cursor = sqlite_conn.cursor()

    # Build SELECT query
    columns_str = ', '.join(columns)
    query = f"SELECT {columns_str} FROM {source_table}"

    # Fetch data
    cursor.execute(query)
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]
    sqlite_conn.close()

    print(f"Fetched {len(rows)} rows from SQLite")

    # Connect to DuckDB
    duck_conn = duckdb.connect(target_db)

    # Infer types and create table
    # Simple type mapping
    duck_conn.execute(f"DROP TABLE IF EXISTS {target_table}")

    # Create table from data
    placeholders = ', '.join(['?' for _ in columns])
    duck_conn.execute(f"""
        CREATE TABLE {target_table} AS
        SELECT * FROM (VALUES {placeholders}) AS t({columns_str})
        WHERE FALSE
    """)

    # Insert data
    for row in rows:
        duck_conn.execute(f"INSERT INTO {target_table} VALUES ({placeholders})", row)

    # Verify
    result = duck_conn.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()
    duck_conn.close()

    print(f"Inserted {result[0]} rows into DuckDB")
    return {'rows_migrated': result[0]}

with DAG(
    dag_id='sqlite_to_duckdb_migration',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['migration', 'database']
) as dag:

    migrate_task = PythonOperator(
        task_id='migrate_data',
        python_callable=migrate_sqlite_to_duckdb,
        provide_context=True
    )
```

**Usage:**
```bash
# Trigger with custom config
airflow dags trigger sqlite_to_duckdb_migration --conf '{
    "source_table": "events",
    "columns": ["event_id", "user_id", "timestamp"],
    "target_table": "events_core"
}'
```

---

## Common Patterns

### Pattern 1: Extract-Transform-Load (ETL)

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def extract_data(**context):
    """Extract from source"""
    # Read from source database
    data = {'raw_data': [1, 2, 3, 4, 5]}
    return data

def transform_data(**context):
    """Transform data"""
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract')
    # Apply transformations
    transformed = {'processed': [x * 2 for x in data['raw_data']]}
    return transformed

def load_data(**context):
    """Load to target"""
    ti = context['ti']
    data = ti.xcom_pull(task_ids='transform')
    # Write to target database
    print(f"Loading data: {data}")
    return {'status': 'success'}

with DAG(
    dag_id='etl_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False,
    tags=['etl']
) as dag:

    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
        provide_context=True
    )

    transform = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
        provide_context=True
    )

    load = PythonOperator(
        task_id='load',
        python_callable=load_data,
        provide_context=True
    )

    # Task dependencies
    extract >> transform >> load
```

### Pattern 2: Data Quality Check

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def validate_row_count(**context):
    """Check if migration succeeded"""
    import sqlite3
    import duckdb

    sqlite_conn = sqlite3.connect('src/data/raw/sample_logs.db')
    source_count = sqlite_conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    sqlite_conn.close()

    duck_conn = duckdb.connect('src/data/processed/analytics.duckdb')
    target_count = duck_conn.execute("SELECT COUNT(*) FROM events_migrated").fetchone()[0]
    duck_conn.close()

    if source_count != target_count:
        raise ValueError(f"Row count mismatch: {source_count} != {target_count}")

    print(f"✓ Validation passed: {target_count} rows")
    return {'validated': True}

with DAG(
    dag_id='migration_with_validation',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['migration', 'validation']
) as dag:

    migrate = PythonOperator(
        task_id='migrate',
        python_callable=migrate_sqlite_to_duckdb,
        provide_context=True
    )

    validate = PythonOperator(
        task_id='validate',
        python_callable=validate_row_count,
        provide_context=True
    )

    migrate >> validate
```

### Pattern 3: Parallel Processing

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def process_table(table_name, **context):
    """Process a single table"""
    print(f"Processing {table_name}")
    # Migration logic here
    return f"{table_name}_done"

with DAG(
    dag_id='parallel_migration',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['migration', 'parallel']
) as dag:

    # Process multiple tables in parallel
    tasks = []
    for table in ['users', 'sessions', 'events']:
        task = PythonOperator(
            task_id=f'migrate_{table}',
            python_callable=process_table,
            op_args=[table],
            provide_context=True
        )
        tasks.append(task)

    # All complete before final step
    def consolidate(**context):
        print("All migrations complete!")

    final = PythonOperator(
        task_id='consolidate',
        python_callable=consolidate,
        provide_context=True
    )

    tasks >> final
```

---

## Configuration Patterns

### Using DAG Parameters

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def configurable_migration(**context):
    """Migration with runtime config"""
    conf = context['dag_run'].conf or {}

    # Default values
    source_db = conf.get('source_db', 'default.db')
    source_table = conf.get('source_table', 'default_table')
    columns = conf.get('columns', ['*'])

    print(f"Config: {source_db} / {source_table} / {columns}")
    # Migration logic...

with DAG(
    dag_id='configurable_migration',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    params={
        'source_db': 'sample.db',
        'source_table': 'events',
        'columns': ['id', 'name']
    }
) as dag:

    task = PythonOperator(
        task_id='migrate',
        python_callable=configurable_migration,
        provide_context=True
    )
```

### Using Airflow Variables

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime

def use_variables(**context):
    """Use Airflow Variables for configuration"""
    # Set via: airflow variables set source_db_path /path/to/db
    source_db = Variable.get('source_db_path', default_var='sample.db')
    target_db = Variable.get('target_db_path', default_var='target.db')

    print(f"Using: {source_db} -> {target_db}")

with DAG(
    dag_id='dag_with_variables',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False
) as dag:

    task = PythonOperator(
        task_id='process',
        python_callable=use_variables,
        provide_context=True
    )
```

---

## Error Handling

### Retry Configuration

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def might_fail(**context):
    """Task that might need retries"""
    import random
    if random.random() < 0.5:
        raise Exception("Random failure!")
    print("Success!")

with DAG(
    dag_id='dag_with_retries',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    default_args={
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'retry_exponential_backoff': True,
        'max_retry_delay': timedelta(minutes=30)
    }
) as dag:

    task = PythonOperator(
        task_id='risky_task',
        python_callable=might_fail,
        provide_context=True
    )
```

### On Failure Callback

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def on_failure(context):
    """Called when task fails"""
    task_instance = context['task_instance']
    print(f"Task {task_instance.task_id} failed!")
    # Send alert, log, etc.

def my_task(**context):
    raise Exception("Something went wrong!")

with DAG(
    dag_id='dag_with_failure_callback',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False
) as dag:

    task = PythonOperator(
        task_id='task_that_fails',
        python_callable=my_task,
        provide_context=True,
        on_failure_callback=on_failure
    )
```

---

## Best Practices

### 1. Use Meaningful Task IDs
```python
# Good
task_id='extract_user_data'
task_id='validate_row_counts'

# Bad
task_id='task1'
task_id='t'
```

### 2. Add Documentation
```python
with DAG(
    dag_id='well_documented_dag',
    description='Migrates user events from SQLite to DuckDB for analytics',
    doc_md="""
    ## Purpose
    This DAG handles daily migration of event data.

    ## Schedule
    Runs manually via trigger

    ## Owner
    Data Engineering Team
    """,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False
) as dag:
    pass
```

### 3. Use Tags for Organization
```python
tags=['migration', 'database', 'duckdb', 'analytics']
```

### 4. Set Appropriate Timeouts
```python
task = PythonOperator(
    task_id='long_running_task',
    python_callable=my_function,
    execution_timeout=timedelta(hours=2)
)
```

### 5. Clean Up Resources
```python
def safe_migration(**context):
    """Ensure connections are closed"""
    conn = None
    try:
        conn = sqlite3.connect('db.sqlite')
        # Do work...
    finally:
        if conn:
            conn.close()
```

---

## Template Generation Guidelines

When generating DAG code based on user requests:

1. **Parse the request** for:
   - Source database and table
   - Target database and table
   - Columns to migrate
   - Any transformations needed

2. **Choose appropriate pattern**:
   - Simple migration: Basic template
   - With validation: Add quality check task
   - Multiple tables: Use parallel pattern
   - Complex transform: Use ETL pattern

3. **Set sensible defaults**:
   - `schedule=None` (manual trigger)
   - `catchup=False`
   - Add descriptive tags
   - Include error handling

4. **Generate unique DAG ID**:
   ```python
   # Format: {source}_{target}_{operation}_{timestamp}
   dag_id = f"sqlite_to_duckdb_migration_{int(time.time())}"
   ```

5. **Add logging**:
   ```python
   print(f"Starting migration from {source} to {target}")
   print(f"Migrated {count} rows successfully")
   ```

---

## Example: Complete Generated DAG

User request: "Migrate events table (event_id, user_id, timestamp columns) from SQLite to DuckDB"

Generated code:
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime
import time

def migrate_events(**context):
    """Migrate events table from SQLite to DuckDB"""

    # Configuration
    source_db = 'src/data/raw/sample_logs.db'
    source_table = 'events'
    columns = ['event_id', 'user_id', 'timestamp']
    target_db = 'src/data/processed/analytics.duckdb'
    target_table = 'events_migrated'

    # Extract from SQLite
    print(f"Extracting from {source_table}...")
    sqlite_conn = sqlite3.connect(source_db)
    cursor = sqlite_conn.cursor()

    columns_str = ', '.join(columns)
    cursor.execute(f"SELECT {columns_str} FROM {source_table}")
    rows = cursor.fetchall()
    sqlite_conn.close()

    print(f"✓ Extracted {len(rows)} rows")

    # Load to DuckDB
    print(f"Loading to {target_table}...")
    duck_conn = duckdb.connect(target_db)

    duck_conn.execute(f"DROP TABLE IF EXISTS {target_table}")
    duck_conn.execute(f"""
        CREATE TABLE {target_table} (
            event_id INTEGER,
            user_id INTEGER,
            timestamp VARCHAR
        )
    """)

    for row in rows:
        duck_conn.execute(
            f"INSERT INTO {target_table} VALUES (?, ?, ?)",
            row
        )

    # Verify
    count = duck_conn.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0]
    duck_conn.close()

    print(f"✓ Loaded {count} rows")

    return {
        'source': source_table,
        'target': target_table,
        'rows_migrated': count
    }

# Generate unique DAG ID
dag_id = f"sqlite_to_duckdb_events_{int(time.time())}"

with DAG(
    dag_id=dag_id,
    description='Migrate events table from SQLite to DuckDB',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=['migration', 'sqlite', 'duckdb', 'rag-generated']
) as dag:

    migrate_task = PythonOperator(
        task_id='migrate_events',
        python_callable=migrate_events,
        provide_context=True
    )
```

This DAG can be directly saved to `$AIRFLOW_HOME/dags/` and will be picked up by Airflow automatically.
