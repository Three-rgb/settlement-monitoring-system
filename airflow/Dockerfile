# Airflow 基础镜像（Python 3.10 与业务镜像版本一致）
FROM apache/airflow:2.10.0-python3.10

# 安装 Docker Provider（DockerOperator 依赖）
# 锁版本以保证构建可复现
RUN pip install --no-cache-dir \
    apache-airflow-providers-docker==3.14.0 \
    apache-airflow-providers-common-sql==1.17.0