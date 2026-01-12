"""
샘플 SQLite 데이터베이스 생성 스크립트
로그 분석 시나리오: Users, Sessions, Events 테이블
"""
import sqlite3
from datetime import datetime, timedelta
import random
from pathlib import Path

def create_sample_database(db_path: str = "src/data/raw/sample_logs.db"):
    """로그 분석용 샘플 SQLite 데이터베이스 생성"""

    # 디렉토리 생성
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # 기존 DB 삭제
    if Path(db_path).exists():
        Path(db_path).unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Users 테이블 생성
    cursor.execute("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            country TEXT,
            signup_date TEXT,
            is_premium BOOLEAN DEFAULT 0,
            total_sessions INTEGER DEFAULT 0,
            last_login TEXT
        )
    """)

    # 2. Sessions 테이블 생성
    cursor.execute("""
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
        )
    """)

    # 3. Events 테이블 생성
    cursor.execute("""
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
        )
    """)

    # 샘플 데이터 생성
    countries = ["US", "KR", "JP", "UK", "DE", "FR", "CA"]
    devices = ["mobile", "desktop", "tablet"]
    os_list = ["iOS", "Android", "Windows", "macOS", "Linux"]
    browsers = ["Chrome", "Safari", "Firefox", "Edge"]
    event_types = ["click", "view", "scroll", "submit", "search"]
    event_names = ["button_click", "page_view", "scroll_depth", "form_submit", "search_query"]

    # Users 데이터 삽입 (100명)
    users_data = []
    for i in range(1, 101):
        username = f"user_{i:03d}"
        email = f"{username}@example.com"
        country = random.choice(countries)
        signup_date = (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
        is_premium = random.choice([0, 1])
        total_sessions = random.randint(1, 50)
        last_login = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()

        users_data.append((username, email, country, signup_date, is_premium, total_sessions, last_login))

    cursor.executemany("""
        INSERT INTO users (username, email, country, signup_date, is_premium, total_sessions, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # Sessions 데이터 삽입 (500개)
    sessions_data = []
    for i in range(1, 501):
        session_id = f"sess_{i:05d}"
        user_id = random.randint(1, 100)
        start_time = (datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))).isoformat()
        duration = random.randint(30, 3600)
        end_time = (datetime.fromisoformat(start_time) + timedelta(seconds=duration)).isoformat()
        device_type = random.choice(devices)
        os_name = random.choice(os_list)
        browser = random.choice(browsers)
        ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

        sessions_data.append((session_id, user_id, start_time, end_time, duration, device_type, os_name, browser, ip_address))

    cursor.executemany("""
        INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sessions_data)

    # Events 데이터 삽입 (2000개)
    events_data = []
    for i in range(1, 2001):
        session_id = f"sess_{random.randint(1, 500):05d}"
        # session에서 user_id 가져오기
        cursor.execute("SELECT user_id FROM sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        user_id = result[0] if result else random.randint(1, 100)

        event_type = random.choice(event_types)
        event_name = random.choice(event_names)
        timestamp = (datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))).isoformat()
        page_url = f"/page/{random.randint(1, 20)}"
        event_properties = f'{{"value": {random.randint(1, 100)}}}'

        events_data.append((session_id, user_id, event_type, event_name, timestamp, page_url, event_properties))

    cursor.executemany("""
        INSERT INTO events (session_id, user_id, event_type, event_name, timestamp, page_url, event_properties)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, events_data)

    conn.commit()

    # 통계 출력
    print("=" * 60)
    print("SQLite 샘플 데이터베이스 생성 완료!")
    print("=" * 60)
    print(f"경로: {db_path}\n")

    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"Users 테이블: {cursor.fetchone()[0]:,} rows")

    cursor.execute("SELECT COUNT(*) FROM sessions")
    print(f"Sessions 테이블: {cursor.fetchone()[0]:,} rows")

    cursor.execute("SELECT COUNT(*) FROM events")
    print(f"Events 테이블: {cursor.fetchone()[0]:,} rows")

    print("\n스키마 정보:")
    print("-" * 60)

    for table in ["users", "sessions", "events"]:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"\n{table.upper()} 테이블:")
        for col in columns:
            print(f"  - {col[1]:20s} {col[2]:10s} {'NOT NULL' if col[3] else ''}")

    conn.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    create_sample_database()
