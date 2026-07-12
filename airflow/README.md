# Airflow 编排使用指南

把 `main.py` 的 `full_pipeline()` 拆成 4 个 Airflow Task，由 Airflow 调度，每个 Task 通过 `DockerOperator` 启动一个临时容器跑对应模块。

## 架构图

```
┌──────────────────────────────────────────────────────────┐
│  airflow/docker-compose.yml                              │
│                                                          │
│   postgres ── airflow-webserver ── airflow-scheduler     │
│                  (UI @ :8080)     (调度任务)              │
│                       │                                  │
│                       │ 挂载 Docker socket                │
│                       ↓                                  │
│                /var/run/docker.sock                       │
│                       │                                  │
└───────────────────────┼──────────────────────────────────┘
                        ↓ 通过 Docker daemon 启动
┌──────────────────────────────────────────────────────────┐
│  任务容器（settlement-app:latest，按需创建销毁）            │
│                                                          │
│  Task 1: python -m src.data_import                       │
│  Task 2: python -m src.analysis                          │
│  Task 3: python -m src.visualization                     │
│  Task 4: python -m src.training_dataset_export           │
│                                                          │
│  ↳ 通过 host.docker.internal:5432 访问 db 服务             │
└──────────────────────────────────────────────────────────┘
```

## 一次性安装（10 分钟）

### Step 1 · 启动业务数据库 + 构建应用镜像

```bash
cd <仓库根目录>
docker compose up -d db              # 启 PostgreSQL+PostGIS，自动初始化 schema
docker compose build monitoring-app  # 构建 settlement-app:latest 镜像
```

> 验证：浏览器访问 `localhost:8081`（PostGIS 端口，可选 pgAdmin 查看数据）

### Step 2 · 配置 Airflow 环境变量

```bash
cd airflow
cp .env.example .env
```

编辑 `airflow/.env`：

```ini
# Windows 示例（注意正斜杠或双反斜杠）
HOST_REPO_ROOT=C:/settlement_monitoring_system
DB_PASSWORD=123456
```

### Step 3 · 启动 Airflow

```bash
cd airflow
docker compose up -d
```

首次启动会拉取 `apache/airflow:2.10.0-python3.10` 镜像（约 1.5GB），并构建自定义层。

### Step 4 · 等待 Webserver 就绪

```bash
docker compose logs -f airflow-webserver
```

看到 `Listening at: http://0.0.0.0:8080` 即就绪。

### Step 5 · 访问 UI

浏览器打开 [http://localhost:8080](http://localhost:8080)

- 用户名：`airflow`
- 密码：`airflow`

## 触发 DAG

UI 操作：
1. 左侧导航 **DAGs**
2. 找到 `settlement_pipeline`（可能需要取消 Pause）
3. 点击右侧 ▶️ 按钮触发一次手动运行
4. 进入 **Grid** 视图查看每个 Task 的运行状态

CLI 操作：

```bash
docker compose exec airflow-scheduler airflow dags trigger settlement_pipeline
```

## 查看日志与输出

| 想看什么 | 位置 |
|---|---|
| DAG 运行日志 | Airflow UI → Task Instance → Logs |
| 业务输出文件 | 宿主机 `<HOST_REPO_ROOT>/output/` |
| Airflow 元数据日志 | `docker compose logs airflow-scheduler` |

## 故障排查

### ❌ Task 容器报 `connection refused: 5432`

- **原因**：db 服务没启动，或 `host.docker.internal` 解析失败
- **修复**：确认 `docker compose ps` 中 db 状态 healthy；Linux 上需改用共享网络方案

### ❌ Task 报 `image not found: settlement-app:latest`

- **原因**：业务镜像未构建
- **修复**：回到仓库根目录 `docker compose build monitoring-app`

### ❌ Task 报 `bind: address already in use`

- **原因**：本机 8080 端口被占用
- **修复**：修改 `airflow/docker-compose.yml` 中 `"8080:8080"` 为 `"8088:8080"`

### ❌ UI 看不到 DAG

- **原因**：DAG 文件没被 Airflow 识别
- **修复**：检查 `../dags/settlement_pipeline_dag.py` 是否存在且无语法错误
- 查看：`docker compose logs airflow-scheduler | grep -i "dag"`

### ❌ Linux 用户 `host.docker.internal` 不可用

Linux 默认不支持 `host.docker.internal`，需要切换到共享网络方案：

```bash
# 在仓库根目录创建外部网络
docker network create settlement_net

# 在 docker-compose.yml 把 db 服务加入该网络
# networks:
#   settlement_net:
#     external: true
```

然后在 `dags/settlement_pipeline_dag.py` 把 `DB_HOST` 改为 `"db"`。

## 调整调度频率

编辑 `dags/settlement_pipeline_dag.py`：

```python
schedule_interval="@daily"     # 每天一次（默认）
schedule_interval="0 2 * * *"  # 每天凌晨 2 点
schedule_interval="@hourly"    # 每小时
schedule_interval=None         # 只手动触发
```

修改后等 30 秒让 scheduler 自动 reload。

## 回退到非 Airflow 模式

```bash
# 业务流水线仍可独立运行
cd <仓库根目录>
docker compose run --rm app    # 走默认完整流水线（entrypoint.sh 无参数模式）

# 或跑单个模块
docker compose run --rm app python -m src.data_import
```

## 文件结构

```
settlement_monitoring_system/
├── dags/                          # Airflow DAG 目录
│   └── settlement_pipeline_dag.py # 流水线 DAG
├── airflow/                       # Airflow 编排（独立 compose）
│   ├── docker-compose.yml         # Airflow 服务定义
│   ├── Dockerfile                 # 自定义 Airflow 镜像（含 DockerProvider）
│   ├── .env.example               # 环境变量模板
│   └── README.md                  # 本文件
├── docker/
│   └── entrypoint.sh              # 已修改：支持参数透传（Task 模式）
├── docker-compose.yml             # 已修改：添加 image tag
├── Dockerfile                     # 业务应用镜像（Task 复用）
└── src/
    └── *.py                       # 业务模块（已支持 python -m 运行）
```