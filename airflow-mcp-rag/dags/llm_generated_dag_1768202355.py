from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import sqlite3
import duckdb
from datetime import datetime
import pandas as pd
import os

def migrate_data(**context):
    """
    Performs data migration from a SQLite source database to a DuckDB target database
    using pandas for data handling. Includes row count validation