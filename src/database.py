"""
数据库连接与操作模块
"""

from sqlalchemy import create_engine, text
from config import DB_CONFIG


def get_connection_string():
    """生成数据库连接字符串"""
    return (f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")


def get_engine():
    """获取SQLAlchemy引擎"""
    return create_engine(get_connection_string())


def test_connection():
    """测试数据库连接"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ 数据库连接成功")
            print(f"   PostgreSQL版本: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def execute_query(query, params=None):
    """执行SQL查询"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return result.fetchall()


def get_table_count(table_name):
    """获取表记录数"""
    result = execute_query(f"SELECT COUNT(*) FROM {table_name}")
    return result[0][0] if result else 0