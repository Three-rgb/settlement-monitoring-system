"""
Settlement Monitoring Pipeline DAG

将原 main.py full_pipeline() 的步骤拆成独立的 Airflow Task，每个 Task 通过
DockerOperator 启动一个临时容器跑对应的 Python 模块。

设计要点：
- 所有 Task 共享同一镜像 settlement-app:latest（由项目根 Dockerfile 构建）
- Task 容器通过 host.docker.internal:5432 访问宿主机上的 PostgreSQL（db 服务
  已通过 docker-compose.yml 把 5432 端口暴露到宿主机）
- 数据 / 输出 / SQL 目录通过 bind mount 共享，Task 写出的文件直接在宿主机可见
- DockerOperator 通过挂载 /var/run/docker.sock 与宿主机 Docker daemon 通信，
  这是 Airflow + Docker 的常见模式（注意：等效于给 Airflow 容器 root 权限）
"""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


# ========== 配置：镜像 / 网络 / 卷 ==========

# 任务镜像（与 docker-compose.yml 中 monitoring-app.image 一致）
APP_IMAGE = "settlement-app:latest"

# PostgreSQL 主机名：容器内通过宿主机回环访问 db 服务的 5432 端口
# 仅在 Docker Desktop（Mac/Windows）下生效；Linux 上需改成共享网络方案
DB_HOST = "host.docker.internal"

# 共享环境变量（DB 连接 + Python 输出行为）
ENV_BASE = {
    "DB_HOST": DB_HOST,
    "DB_PORT": "5432",
    "DB_NAME": "construction_db",
    "DB_USER": "postgres",
    "DB_PASSWORD": os.getenv("DB_PASSWORD", "123456"),
}

# 宿主机仓库根目录（由 airflow/.env 注入；Task 容器据此 bind-mount 数据/输出/SQL）
# DockerOperator 看到的 mount source 路径是宿主机视角
HOST_REPO_ROOT = os.environ.get("HOST_REPO_ROOT", os.getcwd())

# 新版 DockerProvider（>=3.x）要求用 Mount 对象而非字符串
MOUNTS = [
    Mount(source=f"{HOST_REPO_ROOT}/data", target="/app/data", type="bind", read_only=False),
    Mount(source=f"{HOST_REPO_ROOT}/output", target="/app/output", type="bind", read_only=False),
    Mount(source=f"{HOST_REPO_ROOT}/sql", target="/app/sql", type="bind", read_only=True),
]


# ========== DAG 定义 ==========

default_args = {
    "owner": "settlement",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="settlement_pipeline",
    default_args=default_args,
    description="施工沉降监测数据流水线（导入→分析→可视化→训练数据导出）",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["settlement", "monitoring"],
) as dag:

    # ---------- Task 1: 数据导入 ----------
    t_import = DockerOperator(
        task_id="import_data",
        image=APP_IMAGE,
        command="python -m src.data_import",
        environment=ENV_BASE,
        mounts=MOUNTS,
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        tty=False,
    )

    # ---------- Task 2: 数据分析 ----------
    t_analyze = DockerOperator(
        task_id="analyze",
        image=APP_IMAGE,
        command="python -m src.analysis",
        environment=ENV_BASE,
        mounts=MOUNTS,
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        tty=False,
    )

    # ---------- Task 3: 可视化 ----------
    t_visualize = DockerOperator(
        task_id="visualize",
        image=APP_IMAGE,
        command="python -m src.visualization",
        environment=ENV_BASE,
        mounts=MOUNTS,
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        tty=False,
    )

    # ---------- Task 4: 训练/评测数据集导出 ----------
    t_export_training = DockerOperator(
        task_id="export_training_datasets",
        image=APP_IMAGE,
        command="python -m src.training_dataset_export",
        environment=ENV_BASE,
        mounts=MOUNTS,
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        tty=False,
    )

    # ---------- 依赖关系 ----------
    # 串行：import → analyze → (visualize ∥ export_training)
    # 可视化与训练数据导出互不依赖，可并行执行
    t_import >> t_analyze >> [t_visualize, t_export_training]