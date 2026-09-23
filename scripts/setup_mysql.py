"""
MySQL Database Setup Utility.

Reads database credentials from .env, creates the database if not present,
and applies schema.sql and seed.sql automatically.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "zeek_monitor")

try:
    import pymysql
except ImportError:
    print("[!] PyMySQL is required. Run: pip install pymysql")
    sys.exit(1)


def setup_mysql():
    print(f"[*] Attempting to connect to MySQL on {DB_HOST}:{DB_PORT} as user '{DB_USER}'...")
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        )
    except Exception as e:
        print(f"\n[X] Failed to connect to MySQL server:\n    {e}")
        print("\nPrerequisites:")
        print("1. Ensure MySQL daemon is running: sudo service mysql start")
        print("2. Verify credentials in .env match your MySQL setup.")
        sys.exit(1)

    cursor = conn.cursor()

    # 1. Create database
    print(f"[*] Creating database '{DB_NAME}' if not exists...")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cursor.execute(f"USE {DB_NAME};")

    # 2. Execute schema.sql
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    print(f"[*] Executing schema from: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    for statement in schema_sql.split(";"):
        stmt = statement.strip()
        if stmt:
            cursor.execute(stmt)
    print("[+] Schema applied successfully: tables 'network_logs', 'alerts', and 'system_metrics' created.")

    # 3. Execute seed.sql
    seed_path = os.path.join(os.path.dirname(__file__), "..", "database", "seed.sql")
    if os.path.exists(seed_path):
        print(f"[*] Seeding baseline data from: {seed_path}")
        with open(seed_path, "r", encoding="utf-8") as f:
            seed_sql = f.read()
        for statement in seed_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        print("[+] Seed records inserted successfully.")

    cursor.close()
    conn.close()
    print("\n[✔] MySQL Database Setup Complete! Restart your backend to use live MySQL persistence.")


if __name__ == "__main__":
    setup_mysql()
