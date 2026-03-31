"""
数据库配置
注意：实际使用时请修改密码，或改为环境变量读取
"""

import os

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'construction_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '你的密码')  # 修改这里
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