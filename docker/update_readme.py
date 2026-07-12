"""Add Docker section to README.md (run this script to update README)"""

import os

README_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md")

DOCKER_SECTION = """### ⚡ Docker（推荐）

确保已安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)。

```bash
# 1. 构建并启动数据库服务
docker compose up -d

# 2. 运行完整数据流水线
docker compose run --rm app

# 3. 查看输出结果（在 host 的 output/ 目录下）
ls output/figures/
ls output/reports/
ls output/training/

# 4. 单独运行某个模块
docker compose run --rm app python -m src.analysis
docker compose run --rm app python -m src.visualization
docker compose run --rm app python -m src.training_dataset_export

# 5. 停止并清理
docker compose down
```

> **注意**：`docker compose up -d` 启动数据库后，使用 `docker compose run --rm app` 运行完整数据流水线。输出文件保存在 `output/` 目录下，可在宿主机直接查看。

"""


def main():
    with open(README_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find insertion point
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## 快速开始":
            insert_idx = i + 2
            break

    if insert_idx is None:
        print("ERROR: Could not find insertion point")
        return False

    lines.insert(insert_idx, DOCKER_SECTION)

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)

    print(f"README.md updated. Inserted Docker section at line {insert_idx + 1}.")
    print(f"Total lines: {len(lines)}")
    return True


if __name__ == "__main__":
    main()
