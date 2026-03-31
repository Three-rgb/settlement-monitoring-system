-- =====================================================
-- 施工项目沉降监测数据库初始化脚本
-- =====================================================

-- 创建扩展（如不存在）
CREATE EXTENSION IF NOT EXISTS postgis;

-- 删除旧表（如存在）
DROP TABLE IF EXISTS settlement_observations;
DROP TABLE IF EXISTS survey_points;

-- 创建测量点表（空间表）
CREATE TABLE survey_points (
    id SERIAL PRIMARY KEY,
    point_name VARCHAR(20) UNIQUE NOT NULL,
    chainage VARCHAR(10),
    x_coord DOUBLE PRECISION,
    y_coord DOUBLE PRECISION,
    h_initial DOUBLE PRECISION,
    point_type VARCHAR(20),
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 空间索引
CREATE INDEX idx_survey_points_geom ON survey_points USING GIST(geom);

-- 创建沉降观测记录表
CREATE TABLE settlement_observations (
    id SERIAL PRIMARY KEY,
    point_name VARCHAR(20) REFERENCES survey_points(point_name),
    obs_date DATE NOT NULL,
    period INTEGER,
    settlement_rate DOUBLE PRECISION,
    cumulative_settlement DOUBLE PRECISION,
    remark VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 普通索引
CREATE INDEX idx_settlement_point ON settlement_observations(point_name);
CREATE INDEX idx_settlement_date ON settlement_observations(obs_date);

-- 验证创建
SELECT 'survey_points' as table_name, COUNT(*) as count FROM survey_points
UNION ALL
SELECT 'settlement_observations', COUNT(*) FROM settlement_observations;