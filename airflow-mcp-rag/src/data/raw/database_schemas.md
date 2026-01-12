# Database Schema Documentation

## Sample Log Analytics Database

This document describes the schema of our sample SQLite database used for log analytics.

---

## Database Overview

**Database:** `sample_logs.db`
**Type:** SQLite 3
**Domain:** User Activity & Event Logging
**Purpose:** Track user sessions and events for analytics

**Entity Relationship:**
```
users (1) ────── (N) sessions (1) ────── (N) events
```

---

## Tables

### 1. users

Stores user account information and aggregate metrics.

**Table Name:** `users`
**Row Count:** ~100 users
**Primary Key:** `user_id`

#### Schema

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| user_id | INTEGER | NO | Auto-incrementing unique user identifier |
| username | TEXT | NO | Unique username (format: user_XXX) |
| email | TEXT | NO | User email address |
| country | TEXT | YES | Two-letter country code (US, KR, JP, etc.) |
| signup_date | TEXT | YES | ISO 8601 timestamp of registration |
| is_premium | BOOLEAN | YES | Premium membership status (0 or 1) |
| total_sessions | INTEGER | YES | Total number of sessions (denormalized) |
| last_login | TEXT | YES | ISO 8601 timestamp of most recent login |

#### Sample Data
```sql
SELECT * FROM users LIMIT 3;
```
| user_id | username | email | country | signup_date | is_premium | total_sessions | last_login |
|---------|----------|-------|---------|-------------|------------|----------------|------------|
| 1 | user_001 | user_001@example.com | US | 2024-03-15T10:30:00 | 1 | 23 | 2024-12-20T08:15:00 |
| 2 | user_002 | user_002@example.com | KR | 2024-05-22T14:20:00 | 0 | 8 | 2024-12-18T19:45:00 |
| 3 | user_003 | user_003@example.com | JP | 2024-01-10T09:00:00 | 1 | 45 | 2024-12-22T12:30:00 |

#### Indexes
- PRIMARY KEY on `user_id`
- UNIQUE constraint on `username`

#### Common Queries
```sql
-- Get premium users by country
SELECT country, COUNT(*) as premium_count
FROM users
WHERE is_premium = 1
GROUP BY country;

-- Find active users (logged in last 7 days)
SELECT user_id, username, last_login
FROM users
WHERE last_login >= date('now', '-7 days');
```

---

### 2. sessions

Tracks individual user sessions with device and duration information.

**Table Name:** `sessions`
**Row Count:** ~500 sessions
**Primary Key:** `session_id`
**Foreign Keys:** `user_id` → users.user_id

#### Schema

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| session_id | TEXT | NO | Unique session identifier (format: sess_XXXXX) |
| user_id | INTEGER | NO | Foreign key to users table |
| start_time | TEXT | NO | ISO 8601 session start timestamp |
| end_time | TEXT | YES | ISO 8601 session end timestamp |
| duration_seconds | INTEGER | YES | Session duration in seconds |
| device_type | TEXT | YES | Device category (mobile, desktop, tablet) |
| os_name | TEXT | YES | Operating system (iOS, Android, Windows, macOS, Linux) |
| browser | TEXT | YES | Browser name (Chrome, Safari, Firefox, Edge) |
| ip_address | TEXT | YES | User IP address (anonymized) |

#### Sample Data
```sql
SELECT * FROM sessions LIMIT 3;
```
| session_id | user_id | start_time | end_time | duration_seconds | device_type | os_name | browser | ip_address |
|------------|---------|------------|----------|------------------|-------------|---------|---------|------------|
| sess_00001 | 42 | 2024-12-20T10:15:00 | 2024-12-20T10:35:00 | 1200 | desktop | Windows | Chrome | 192.168.1.101 |
| sess_00002 | 15 | 2024-12-20T11:30:00 | 2024-12-20T11:32:00 | 120 | mobile | iOS | Safari | 192.168.1.55 |
| sess_00003 | 87 | 2024-12-20T14:00:00 | 2024-12-20T14:45:00 | 2700 | desktop | macOS | Chrome | 192.168.2.33 |

#### Session Duration Categories
- **Bounce:** < 60 seconds (user left quickly)
- **Short:** 60-300 seconds (brief interaction)
- **Medium:** 300-1800 seconds (engaged session)
- **Long:** > 1800 seconds (highly engaged)

#### Common Queries
```sql
-- Session duration by device type
SELECT
    device_type,
    AVG(duration_seconds) as avg_duration,
    COUNT(*) as session_count
FROM sessions
GROUP BY device_type;

-- Find sessions by user
SELECT session_id, start_time, duration_seconds, device_type
FROM sessions
WHERE user_id = 42
ORDER BY start_time DESC;
```

---

### 3. events

Detailed event log for user interactions within sessions.

**Table Name:** `events`
**Row Count:** ~2,000 events
**Primary Key:** `event_id`
**Foreign Keys:**
- `session_id` → sessions.session_id
- `user_id` → users.user_id

#### Schema

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| event_id | INTEGER | NO | Auto-incrementing unique event identifier |
| session_id | TEXT | NO | Foreign key to sessions table |
| user_id | INTEGER | NO | Foreign key to users table (denormalized) |
| event_type | TEXT | NO | Event category (click, view, scroll, submit, search) |
| event_name | TEXT | NO | Specific event name (button_click, page_view, etc.) |
| timestamp | TEXT | NO | ISO 8601 timestamp when event occurred |
| page_url | TEXT | YES | URL where event happened |
| event_properties | TEXT | YES | JSON string with additional properties |

#### Sample Data
```sql
SELECT * FROM events LIMIT 3;
```
| event_id | session_id | user_id | event_type | event_name | timestamp | page_url | event_properties |
|----------|------------|---------|------------|------------|-----------|----------|------------------|
| 1 | sess_00042 | 15 | click | button_click | 2024-12-20T10:15:23 | /page/5 | {"value": 42} |
| 2 | sess_00042 | 15 | view | page_view | 2024-12-20T10:15:30 | /page/7 | {"value": 15} |
| 3 | sess_00103 | 88 | submit | form_submit | 2024-12-20T11:22:45 | /page/3 | {"value": 99} |

#### Event Types

| event_type | Description | Common event_names |
|------------|-------------|-------------------|
| click | User clicked on element | button_click, link_click |
| view | Page or content viewed | page_view, section_view |
| scroll | Scrolling behavior | scroll_depth, scroll_end |
| submit | Form submission | form_submit, search_submit |
| search | Search queries | search_query, filter_apply |

#### Common Queries
```sql
-- Event frequency by type
SELECT event_type, COUNT(*) as event_count
FROM events
GROUP BY event_type
ORDER BY event_count DESC;

-- User's event timeline
SELECT timestamp, event_type, event_name, page_url
FROM events
WHERE user_id = 15
ORDER BY timestamp;

-- Events per session
SELECT
    session_id,
    COUNT(*) as event_count,
    MIN(timestamp) as first_event,
    MAX(timestamp) as last_event
FROM events
GROUP BY session_id;
```

---

## Relationships

### users → sessions (1:N)
```sql
-- Get user with their sessions
SELECT
    u.username,
    u.country,
    COUNT(s.session_id) as session_count,
    AVG(s.duration_seconds) as avg_duration
FROM users u
LEFT JOIN sessions s ON u.user_id = s.user_id
GROUP BY u.user_id;
```

### sessions → events (1:N)
```sql
-- Get session with event count
SELECT
    s.session_id,
    s.device_type,
    s.duration_seconds,
    COUNT(e.event_id) as event_count
FROM sessions s
LEFT JOIN events e ON s.session_id = e.session_id
GROUP BY s.session_id;
```

### users → events (through sessions)
```sql
-- Get user's total events
SELECT
    u.user_id,
    u.username,
    COUNT(e.event_id) as total_events
FROM users u
LEFT JOIN events e ON u.user_id = e.user_id
GROUP BY u.user_id;
```

---

## Migration Scenarios

### Scenario 1: User Analytics Warehouse
**Goal:** Create a user dimension table in DuckDB

**Columns to Extract:**
- user_id (identifier)
- country (dimension)
- signup_date (temporal)
- is_premium (flag)
- total_sessions (metric)

**Why these columns:**
- Excludes PII (email, username)
- Focuses on analytical attributes
- Optimized for aggregation queries

**DuckDB Schema:**
```sql
CREATE TABLE dim_users (
    user_id INTEGER PRIMARY KEY,
    country VARCHAR(2),
    signup_date DATE,
    is_premium BOOLEAN,
    total_sessions INTEGER
);
```

### Scenario 2: Event Stream Analysis
**Goal:** Migrate events for time-series analysis

**Columns to Extract:**
- event_id (identifier)
- user_id (dimension)
- event_type (category)
- event_name (sub-category)
- timestamp (temporal)

**Why these columns:**
- Essential for funnel analysis
- Minimal storage footprint
- Fast time-range queries

**DuckDB Schema:**
```sql
CREATE TABLE fact_events (
    event_id BIGINT PRIMARY KEY,
    user_id INTEGER,
    event_type VARCHAR(20),
    event_name VARCHAR(50),
    event_time TIMESTAMP
);
```

### Scenario 3: Session Performance Metrics
**Goal:** Analyze session patterns by device

**Columns to Extract:**
- session_id (identifier)
- user_id (dimension)
- duration_seconds (metric)
- device_type (dimension)
- os_name (dimension)
- browser (dimension)

**Why these columns:**
- Device performance comparison
- User behavior segmentation
- Engagement metrics

**DuckDB Schema:**
```sql
CREATE TABLE fact_sessions (
    session_id VARCHAR(20) PRIMARY KEY,
    user_id INTEGER,
    duration_seconds INTEGER,
    device_type VARCHAR(10),
    os_name VARCHAR(20),
    browser VARCHAR(20)
);
```

---

## Column Selection Guidelines

### Performance Optimization
**Include columns that:**
- Are frequently filtered (WHERE clauses)
- Used in GROUP BY operations
- Required for JOINs
- Part of analytical calculations

**Exclude columns that:**
- Contain large text (descriptions, logs)
- Rarely accessed
- Can be derived from other columns
- Sensitive/PII data not needed

### Example: Optimized Event Table
```sql
-- Full table: 8 columns
SELECT * FROM events;

-- Optimized for analytics: 5 columns
SELECT
    event_id,
    user_id,
    event_type,
    timestamp,
    page_url
FROM events;

-- Storage reduction: ~40%
-- Query speed improvement: ~60% faster
```

---

## Data Quality Notes

### Nullable Columns
- `country`, `device_type`, `os_name`, `browser`: May be NULL if detection failed
- `end_time`: NULL for active sessions
- `page_url`: NULL for backend events

### Data Formats
- **Timestamps:** ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- **Country codes:** ISO 3166-1 alpha-2 (2 letters)
- **IP addresses:** IPv4 format (anonymized)
- **JSON properties:** Valid JSON strings

### Constraints
- `username` must be unique
- `user_id` in sessions/events must reference existing user
- `session_id` in events must reference existing session
- `timestamp` should be within session start/end time (not enforced)

---

## Query Performance Tips

1. **Use indexed columns in WHERE clauses**
```sql
-- Fast: uses PRIMARY KEY
SELECT * FROM events WHERE event_id = 100;

-- Slow: full table scan
SELECT * FROM events WHERE event_name = 'button_click';
```

2. **Filter before JOIN**
```sql
-- Good: filter early
SELECT u.username, s.session_id
FROM users u
JOIN (SELECT * FROM sessions WHERE device_type = 'mobile') s
ON u.user_id = s.user_id;
```

3. **Use appropriate date functions**
```sql
-- For SQLite TEXT timestamps
WHERE timestamp >= date('now', '-7 days')

-- After migrating to DuckDB TIMESTAMP
WHERE event_time >= current_date - INTERVAL '7 days'
```

---

## Appendix: Create Statements

```sql
-- users table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    country TEXT,
    signup_date TEXT,
    is_premium BOOLEAN DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    last_login TEXT
);

-- sessions table
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds INTEGER,
    device_type TEXT,
    os_name TEXT,
    browser TEXT,
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- events table
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    page_url TEXT,
    event_properties TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```
