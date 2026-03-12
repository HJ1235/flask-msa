import os
import pymysql.cursors

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '192.168.0.13'),
    'user': os.getenv('DB_USER', 'flask_user'),
    'password': os.getenv('DB_PASSWORD', 'P@ssw0rd'),
    'db': os.getenv('DB_NAME', 'flask_auth_db'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """데이터베이스 연결을 설정하고 반환합니다."""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        print(f"DB Connection Error: {e}")
        raise
