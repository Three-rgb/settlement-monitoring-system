# 施工项目沉降监测数据管理系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.6+-green.svg)](https://postgis.net/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于OSM真实道路数据，构建施工期沉降监测空间数据库，实现数据自动化处理、空间分析与可视化展示。

<img src="F:\settlement_monitoring_system\output\figures\settlement_curves.png" alt="settlement_curves" style="zoom: 25%;" />

## 项目背景

**针对施工期沉降监测数据管理效率低、可视化难的问题，设计并开发空间数据管理系统。适用于路基、桥梁、隧道等工程的沉降监测数据分析。**

## 技术架构
**数据采集 → 数据清洗 → PostGIS存储 → 空间分析 → 可视化展示**
**(OSM)      (Python)    (空间数据库)   (SQL/Python)  (matplotlib)**

## 核心功能

- ✅ **空间数据库设计**：测点表（空间字段）+ 观测记录表，支持地理信息查询
- ✅ **数据自动化处理**：OSM数据解析、测点布设、沉降数据生成
- ✅ **空间分析**：邻近点查询、沉降统计、趋势分析、预警判断
- ✅ **可视化展示**：沉降时间曲线、分布统计图表

## 数据规模

| 指标 | 数值 |
|-----|------|
| 道路长度 | 73,395 米 |
| 监测测点 | 50 个（50米间距） |
| 观测期数 | 12 期（月度观测） |
| 数据记录 | 600 条 |
| 覆盖时间 | 2024年1月-12月 |

## 技术栈

- **数据库**：PostgreSQL 16 + PostGIS 3.6
- **数据处理**：Python 3.8+, pandas, SQLAlchemy, GeoPandas
- **可视化**：matplotlib
- **数据源**：OpenStreetMap (OSM)

## 快速开始

### 1. 环境要求
- Python 3.8+
- PostgreSQL 16+
- PostGIS 3.6+

### 2. 安装依赖
**pip install -r requirements.txt**

### 3. 数据库配置
- **复制示例配置**
- **cp config.example.py config.py**
- **编辑 config.py，修改数据库密码**

### 4. 初始化数据库
## 创建数据库并启用PostGIS
- **psql -U postgres -c "CREATE DATABASE construction_db;"**
- **psql -U postgres -d construction_db -c "CREATE EXTENSION postgis;"**

- **执行初始化脚本**
- **psql -U postgres -d construction_db -f sql/init_database.sql**

### 5. 运行项目
- **完整流程**
- **python main.py**
- **或分步执行：**
- **python -m src.data_generator    # 生成数据**
- **python -m src.data_import       # 导入数据库**
- **python -m src.analysis          # 数据分析**
- **python -m src.visualization     # 生成图表**

## 项目结构

### settlement_monitoring_system/
**├── config.py                 # 数据库配置（需自行创建）**
**├── main.py                   # 主程序入口**
**├── requirements.txt          # 依赖清单**
**├── src/                      # 源代码**
**│   ├── database.py          # 数据库连接**
**│   ├── data_generator.py    # 数据生成**
**│   ├── data_import.py       # 数据导入**
**│   ├── analysis.py          # 数据分析**
**│   └── visualization.py     # 可视化**
**├── sql/**
**│   └── init_database.sql    # 数据库初始化**
**├── data/                    # 数据目录**
**│   ├── survey_points.csv**
**│   └── settlement_observations.csv**
**└── output/                  # 输出成果**
    **└── figures/**
        **├── settlement_curves.png**
        └── **settlement_distribution.png**

## 核心SQL示例
```sql
-- 空间查询：查找某点附近500米内的测点
SELECT 
    a.point_name,
    b.point_name as nearby_point,
    ST_Distance(a.geom::geography, b.geom::geography) as distance_m
FROM survey_points a
JOIN survey_points b ON a.point_name != b.point_name
WHERE a.point_name = 'SP-01'
  AND ST_DWithin(a.geom::geography, b.geom::geography, 500);

-- 沉降统计：最大沉降量前10位
SELECT 
    s.point_name,
    s.chainage,
    MAX(o.cumulative_settlement) as max_settlement
FROM survey_points s
JOIN settlement_observations o ON s.point_name = o.point_name
GROUP BY s.point_name, s.chainage
ORDER BY max_settlement DESC
LIMIT 10;
```

## 成果展示
- **沉降时间曲线**
- **settlement_curves.png**
- **沉降分布统计**
- **settlement_distribution.png**

## 数据分析亮点
- **最大沉降点：SP-26 (K0+37445)，累计沉降 52.42mm**
- **沉降规律：前期快（施工期月均5-8mm），后期慢（稳定期月均1-2mm）**
- **数据质量：12期观测无缺失，符合工程监测规范**

## 应用场景
- **路基沉降监测**
- **桥梁健康监测**
- **隧道变形分析**
- **智慧城市基础设施管理**
- **许可证:MIT License**
- **作者:GitHub: @Three-rgb**
- **项目链接: https://github.com/Three-rgb/settlement-monitoring-system**