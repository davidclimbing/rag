# Database Migration Guide

Complete guide for migrating data between different database systems.

## Table of Contents
1. [SQLite to DuckDB Migration](#sqlite-to-duckdb-migration)
2. [Data Type Mappings](#data-type-mappings)
3. [Column Selection Strategies](#column-selection-strategies)
4. [Best Practices](#best-practices)
5. [Common Patterns](#common-patterns)

---

## SQLite to DuckDB Migration

### Overview
DuckDB is an embedded analytical database designed for fast analytics. It's ideal for migrating SQLite data when you need:
- Faster analytical queries
- Better support for complex aggregations
- Columnar storage benefits
- OLAP workloads

### Basic Migration Steps

#### 1. Read Source Schema
First, understand your SQLite table structure:

```sql
-- Get table schema in SQLite
PRAGMA table_info(table_name);

-- Get all tables
SELECT name FROM sqlite_master WHERE type='table';
```

#### 2. Select Columns
Choose columns based on your requirements:

```sql
-- Extract specific columns from SQLite
SELECT column1, column2, column3
FROM source_table
WHERE condition;
```

#### 3. Create Target Table in DuckDB
```sql
-- Create table in DuckDB
CREATE TABLE target_table (
    column1 TYPE1,
    column2 TYPE2,
    column3 TYPE3
);
```

#### 4. Transfer Data
```sql
-- Insert data into DuckDB
INSERT INTO target_table
SELECT column1, column2, column3
FROM sqlite_scan('source.db', 'source_table');
```

---

## Data Type Mappings

### SQLite to DuckDB Type Conversion

| SQLite Type | DuckDB Type | Notes |
|-------------|-------------|-------|
| INTEGER | INTEGER, BIGINT | Use BIGINT for large numbers |
| REAL | DOUBLE, FLOAT | DOUBLE for higher precision |
| TEXT | VARCHAR, TEXT | VARCHAR(n) for fixed length |
| BLOB | BLOB | Binary data |
| BOOLEAN | BOOLEAN | Native boolean in DuckDB |
| NULL | NULL | Nullability preserved |

### Type Selection Guidelines

**For Timestamps:**
```sql
-- SQLite stores as TEXT
stored_at TEXT  -- "2024-01-15T10:30:00"

-- DuckDB recommends TIMESTAMP
stored_at TIMESTAMP  -- Native timestamp type
```

**For IDs:**
```sql
-- Small datasets (< 2B rows)
user_id INTEGER

-- Large datasets
user_id BIGINT
```

**For Text:**
```sql
-- Fixed-length strings
country_code VARCHAR(2)

-- Variable-length text
description TEXT
```

---

## Column Selection Strategies

### Strategy 1: Essential Columns Only
Extract only the columns needed for analysis:

```sql
-- Example: User analytics
SELECT
    user_id,           -- Identifier
    country,           -- Dimension
    signup_date,       -- Temporal
    is_premium         -- Metric
FROM users;
```

**When to use:**
- Reducing data volume for faster queries
- Privacy/compliance (excluding PII)
- Cost optimization in cloud storage

### Strategy 2: Denormalization
Flatten related tables for analytical queries:

```sql
-- Combine users and sessions
SELECT
    u.user_id,
    u.username,
    u.country,
    s.session_id,
    s.start_time,
    s.device_type
FROM users u
JOIN sessions s ON u.user_id = s.user_id;
```

**When to use:**
- Avoiding complex JOINs in analytics
- Creating data warehouse fact tables
- Optimizing for read-heavy workloads

### Strategy 3: Aggregated Metrics
Pre-calculate metrics during migration:

```sql
-- User activity summary
SELECT
    user_id,
    COUNT(*) as total_events,
    MIN(timestamp) as first_event,
    MAX(timestamp) as last_event,
    COUNT(DISTINCT session_id) as session_count
FROM events
GROUP BY user_id;
```

**When to use:**
- Dashboard requirements
- Reducing computation in queries
- Creating summary tables

---

## Best Practices

### 1. Schema Validation
Always validate schema before migration:

```python
# Check column compatibility
sqlite_schema = get_sqlite_schema('table_name')
duckdb_types = map_to_duckdb_types(sqlite_schema)
validate_types(duckdb_types)
```

### 2. Batch Processing
For large tables, process in batches:

```sql
-- Process 100k rows at a time
SELECT * FROM source_table
LIMIT 100000 OFFSET 0;
```

### 3. Data Validation
Verify row counts and sample data:

```sql
-- Compare counts
SELECT COUNT(*) FROM sqlite_scan('source.db', 'table');
SELECT COUNT(*) FROM duckdb_table;

-- Sample comparison
SELECT * FROM source_table LIMIT 10;
SELECT * FROM target_table LIMIT 10;
```

### 4. Index Strategy
Create indexes after data load:

```sql
-- Create indexes in DuckDB for frequently filtered columns
CREATE INDEX idx_user_id ON events(user_id);
CREATE INDEX idx_timestamp ON events(timestamp);
```

### 5. Handle NULL Values
Explicitly handle nulls during migration:

```sql
SELECT
    COALESCE(column1, default_value) as column1,
    COALESCE(column2, 0) as column2
FROM source_table;
```

---

## Common Patterns

### Pattern 1: Event Log Migration
**Use Case:** Migrate event logs for time-series analysis

```sql
-- Select events from last 90 days with essential columns
CREATE TABLE events_analytics AS
SELECT
    event_id,
    user_id,
    event_type,
    event_name,
    timestamp::TIMESTAMP as event_time,
    page_url
FROM sqlite_scan('logs.db', 'events')
WHERE timestamp >= date_sub('day', 90, current_date);
```

### Pattern 2: User Dimension Table
**Use Case:** Create a user dimension for analytics

```sql
-- Extract user attributes excluding sensitive data
CREATE TABLE dim_users AS
SELECT
    user_id,
    country,
    signup_date::DATE as signup_date,
    is_premium::BOOLEAN as is_premium,
    total_sessions
FROM sqlite_scan('logs.db', 'users');
```

### Pattern 3: Session Fact Table
**Use Case:** Analytical fact table with session metrics

```sql
-- Session data with computed metrics
CREATE TABLE fact_sessions AS
SELECT
    session_id,
    user_id,
    start_time::TIMESTAMP as session_start,
    duration_seconds,
    device_type,
    os_name,
    CASE
        WHEN duration_seconds < 60 THEN 'bounce'
        WHEN duration_seconds < 300 THEN 'short'
        ELSE 'engaged'
    END as session_category
FROM sqlite_scan('logs.db', 'sessions');
```

### Pattern 4: Incremental Updates
**Use Case:** Add only new records

```sql
-- Get max timestamp from target
SET max_migrated_time = (SELECT MAX(timestamp) FROM target_table);

-- Insert only newer records
INSERT INTO target_table
SELECT * FROM sqlite_scan('source.db', 'source_table')
WHERE timestamp > $max_migrated_time;
```

---

## Migration Checklist

- [ ] Analyze source schema (`PRAGMA table_info`)
- [ ] Identify required columns
- [ ] Map data types (SQLite → DuckDB)
- [ ] Create target schema in DuckDB
- [ ] Test with small sample (LIMIT 100)
- [ ] Perform full migration
- [ ] Validate row counts
- [ ] Verify data quality (NULLs, types)
- [ ] Create necessary indexes
- [ ] Document migration logic

---

## Troubleshooting

### Issue: Type Mismatch
```
Error: Cannot convert TEXT to TIMESTAMP
```
**Solution:**
```sql
-- Use explicit casting
SELECT timestamp::TIMESTAMP FROM source;
```

### Issue: Character Encoding
```
Error: Invalid UTF-8 encoding
```
**Solution:**
```sql
-- Handle encoding issues
SELECT CAST(column AS VARCHAR) FROM source;
```

### Issue: NULL Constraints
```
Error: NOT NULL constraint violated
```
**Solution:**
```sql
-- Provide defaults for NULLs
SELECT COALESCE(column, 'default') FROM source;
```

---

## Performance Tips

1. **Use DuckDB's sqlite_scan() extension** - Direct read without intermediate files
2. **Create tables before INSERT** - Faster than CREATE TABLE AS SELECT for large data
3. **Disable transactions for bulk loads** - Use `BEGIN TRANSACTION` strategically
4. **Partition large tables** - Split by date or other dimensions
5. **Compress infrequently accessed columns** - DuckDB's columnar format benefits from compression

---

## Example: Complete Migration Script

```python
import duckdb
import sqlite3

def migrate_table(
    sqlite_db: str,
    source_table: str,
    columns: list[str],
    duckdb_path: str,
    target_table: str
):
    """
    Migrate specific columns from SQLite to DuckDB

    Args:
        sqlite_db: Path to SQLite database
        source_table: Source table name
        columns: List of columns to migrate
        duckdb_path: Path to DuckDB database
        target_table: Target table name
    """
    # Connect to DuckDB
    conn = duckdb.connect(duckdb_path)

    # Install and load sqlite extension
    conn.execute("INSTALL sqlite;")
    conn.execute("LOAD sqlite;")

    # Build column selection
    cols = ", ".join(columns)

    # Create and populate table
    query = f"""
    CREATE TABLE {target_table} AS
    SELECT {cols}
    FROM sqlite_scan('{sqlite_db}', '{source_table}');
    """

    conn.execute(query)

    # Verify
    count = conn.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0]
    print(f"Migrated {count} rows to {target_table}")

    conn.close()

# Usage
migrate_table(
    sqlite_db='src/data/raw/sample_logs.db',
    source_table='events',
    columns=['event_id', 'user_id', 'event_type', 'timestamp'],
    duckdb_path='src/data/processed/analytics.duckdb',
    target_table='events_core'
)
```

---

## References

- [DuckDB Documentation](https://duckdb.org/docs/)
- [DuckDB SQLite Extension](https://duckdb.org/docs/extensions/sqlite)
- [SQLite Data Types](https://www.sqlite.org/datatype3.html)
- [DuckDB Data Types](https://duckdb.org/docs/sql/data_types/overview)
