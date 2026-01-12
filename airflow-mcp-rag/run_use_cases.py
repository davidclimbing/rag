"""
모든 Use Case를 한 번에 실행하는 스크립트
"""
from airflow_manager.llm_dag_generator import process_natural_language_request
import sys
import importlib


# Use Case 정의
USE_CASES = [
    {
        "name": "UC1: 기본 컬럼 선택",
        "request": "events 테이블에서 event_id, user_id, event_type 컬럼만 DuckDB로 옮겨줘"
    },
    {
        "name": "UC2: WHERE 조건 (국가 필터)",
        "request": "users 테이블에서 country가 'KR'인 사용자만 DuckDB로 옮겨줘"
    },
    {
        "name": "UC3: 숫자 비교 조건",
        "request": "sessions에서 duration_seconds가 1000 이상인 것만 DuckDB로 옮겨줘"
    },
    {
        "name": "UC4: LIMIT 제한",
        "request": "events에서 최근 데이터 100개만 DuckDB로 옮겨줘"
    },
    {
        "name": "UC5: WHERE + LIMIT",
        "request": "events에서 event_type이 'click'인 것 50개만 DuckDB로 옮겨줘"
    }
]


def run_use_case(idx, use_case):
    """단일 use case 실행"""
    print("\n" + "=" * 80)
    print(f"{use_case['name']}")
    print("=" * 80)
    print(f"요청: {use_case['request']}\n")

    try:
        # 1. DAG 생성
        result = process_natural_language_request(use_case['request'])

        print(f"\n✓ DAG 생성 완료: {result['filepath']}")
        print(f"  Config: {result['config']}")

        # 2. DAG 실행
        print(f"\n실행 중...")

        # 동적 import
        module_path = result['filepath'].replace('.py', '').replace('/', '.')
        function_name = f"migrate_{result['config'].target_table}"

        # import 및 실행
        sys.path.insert(0, '.')
        module = importlib.import_module(module_path)
        migrate_func = getattr(module, function_name)

        exec_result = migrate_func()

        print(f"\n✅ {use_case['name']} 완료!")
        print(f"   결과: {exec_result}")

        return True, exec_result

    except Exception as e:
        print(f"\n❌ {use_case['name']} 실패!")
        print(f"   에러: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def show_results():
    """전체 결과 확인"""
    import duckdb

    print("\n\n" + "=" * 80)
    print("최종 결과 확인")
    print("=" * 80)

    conn = duckdb.connect('src/data/processed/analytics.duckdb')

    tables = conn.execute('SHOW TABLES').fetchall()

    print(f"\n총 {len(tables)}개 테이블 생성됨:\n")

    for table in tables:
        table_name = table[0]
        count = conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]

        # 컬럼 정보
        columns = conn.execute(f'DESCRIBE {table_name}').fetchall()
        col_names = [col[0] for col in columns]

        print(f"📊 {table_name}")
        print(f"   - Rows: {count:,}")
        print(f"   - Columns: {', '.join(col_names)}")

        # 샘플 데이터
        sample = conn.execute(f'SELECT * FROM {table_name} LIMIT 2').fetchall()
        if sample:
            print(f"   - Sample: {sample[0]}")
        print()

    conn.close()


if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Airflow MCP RAG - Use Case 실행")
    print("=" * 80)

    results = []

    for idx, use_case in enumerate(USE_CASES, 1):
        success, result = run_use_case(idx, use_case)
        results.append((use_case['name'], success, result))

    # 전체 결과 출력
    print("\n\n" + "=" * 80)
    print("실행 요약")
    print("=" * 80)

    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)

    for name, success, result in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
        if success and result:
            print(f"   → {result.get('rows_migrated', 0)} rows 마이그레이션")

    print(f"\n성공: {success_count}/{total_count}")

    # 결과 확인
    if success_count > 0:
        show_results()

    print("\n" + "=" * 80)
    print("✨ 완료!")
    print("=" * 80)
