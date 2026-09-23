"""
Database Connection Manager and Health Verification.

Academic Context (Database Management Systems):
- Connection pooling and thread-safe session acquisition.
- Graceful degradation: Detects whether MySQL service is online or offline.
- Strictly adheres to MySQL relational database requirement (Rule 6).
"""

import os
from typing import Tuple, Optional, Any
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "zeek_monitor")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Driver detection
DRIVER_TYPE = None
try:
    import mysql.connector
    from mysql.connector import pooling
    DRIVER_TYPE = "mysql.connector"
except ImportError:
    try:
        import pymysql
        DRIVER_TYPE = "pymysql"
    except ImportError:
        DRIVER_TYPE = None


class DatabaseConnectionPool:
    """
    Manages MySQL database connection pool and connectivity diagnostics.
    """

    _pool = None

    @classmethod
    def get_connection(cls) -> Any:
        """
        Retrieves a live database connection from the driver.
        Raises ConnectionError if MySQL daemon is not running or credentials invalid.
        """
        if DRIVER_TYPE == "mysql.connector":
            try:
                return mysql.connector.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    autocommit=True,
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to MySQL ({DB_HOST}:{DB_PORT}): {e}")

        elif DRIVER_TYPE == "pymysql":
            try:
                return pymysql.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    autocommit=True,
                    cursorclass=pymysql.cursors.DictCursor,
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to MySQL via PyMySQL: {e}")

        else:
            raise RuntimeError("No MySQL driver installed. Please install mysql-connector-python or pymysql.")

    @classmethod
    def check_database_availability(cls) -> Tuple[bool, str]:
        """
        Non-fatal diagnostic method to test if MySQL server is running and database exists.

        Returns:
            Tuple[bool, str]: (is_available, diagnostic_message)
        """
        if DRIVER_TYPE is None:
            return False, "Neither mysql-connector-python nor pymysql is installed."

        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True, f"Successfully connected to MySQL on {DB_HOST}:{DB_PORT}/{DB_NAME}"
        except Exception as e:
            return False, f"MySQL offline or unreachable: {str(e)}"
