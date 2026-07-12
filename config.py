"""
数据库与路径配置

约定：
- 敏感字段（DB_PASSWORD 等）通过环境变量注入，不要提交真实凭据
- 本地开发请复制 .env.example 为 .env 并填写实际值（.env 已加入 .gitignore）
- 若未配置关键字段，导入本模块会立即抛出 ValueError，避免运行时静默失败
"""

import os

# 加载 .env（可选依赖）。未安装 python-dotenv 时回退到系统环境变量。
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(
            f"环境变量 {name} 未设置。请在 .env 或系统环境中配置后重试。"
        )
    return value


def _optional(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


# 数据库配置
DB_CONFIG = {
    'host': _optional('DB_HOST', 'localhost'),
    'port': _optional('DB_PORT', '5432'),
    'database': _required('DB_NAME'),
    'user': _optional('DB_USER', 'postgres'),
    'password': _required('DB_PASSWORD'),
}

# 数据文件路径
DATA_DIR = 'data'
OUTPUT_DIR = 'output'

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(f'{DATA_DIR}/raw', exist_ok=True)
os.makedirs(f'{DATA_DIR}/processed', exist_ok=True)
os.makedirs(f'{OUTPUT_DIR}/figures', exist_ok=True)
os.makedirs(f'{OUTPUT_DIR}/reports', exist_ok=True)
os.makedirs(f'{OUTPUT_DIR}/training', exist_ok=True)