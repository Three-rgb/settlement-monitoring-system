"""
数据分析模块
"""

import pandas as pd
from src.database import execute_query


def get_settlement_summary():
    """获取沉降统计摘要"""
    query = """
    SELECT 
        s.point_name,
        s.chainage,
        COUNT(o.id) as obs_count,
        ROUND(AVG(o.cumulative_settlement)::numeric, 2) as avg_settlement,
        ROUND(MAX(o.cumulative_settlement)::numeric, 2) as max_settlement,
        ROUND(MIN(o.cumulative_settlement)::numeric, 2) as final_settlement
    FROM survey_points s
    LEFT JOIN settlement_observations o ON s.point_name = o.point_name
    GROUP BY s.point_name, s.chainage
    ORDER BY max_settlement DESC
    """

    results = execute_query(query)

    df = pd.DataFrame(results, columns=[
        'point_name', 'chainage', 'obs_count',
        'avg_settlement', 'max_settlement', 'final_settlement'
    ])

    return df


def get_settlement_trend(point_name):
    """获取单个点的沉降趋势"""
    query = """
    SELECT obs_date, cumulative_settlement, settlement_rate
    FROM settlement_observations
    WHERE point_name = :name
    ORDER BY obs_date
    """

    from src.database import get_engine
    from sqlalchemy import text

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), {'name': point_name})
        rows = result.fetchall()

    df = pd.DataFrame(rows, columns=['obs_date', 'cumulative_settlement', 'settlement_rate'])
    return df


def find_nearby_points(point_name, distance_m=500):
    """查找附近点"""
    query = """
    SELECT 
        b.point_name,
        b.chainage,
        ROUND(ST_Distance(
            a.geom::geography, 
            b.geom::geography
        )::numeric, 2) as distance_m
    FROM survey_points a
    JOIN survey_points b ON a.point_name != b.point_name
    WHERE a.point_name = :name
      AND ST_DWithin(a.geom::geography, b.geom::geography, :distance)
    ORDER BY distance_m
    """

    from src.database import get_engine
    from sqlalchemy import text

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(query), {
            'name': point_name,
            'distance': distance_m
        })
        rows = result.fetchall()

    df = pd.DataFrame(rows, columns=['point_name', 'chainage', 'distance_m'])
    return df


def generate_report():
    """生成分析报告"""
    print("=" * 50)
    print("沉降监测数据分析报告")
    print("=" * 50)

    # 统计摘要
    summary = get_settlement_summary()
    print("\n【沉降量统计】（前10位）")
    print(summary.head(10).to_string(index=False))

    # 最大沉降点详情
    max_point = summary.iloc[0]['point_name']
    print(f"\n【最大沉降点详情】{max_point}")
    trend = get_settlement_trend(max_point)
    print(trend.to_string(index=False))

    # 空间分析示例
    print(f"\n【邻近点分析】{max_point} 附近500米")
    nearby = find_nearby_points(max_point, 500)
    print(nearby.to_string(index=False))

    print("=" * 50)

    return summary


if __name__ == '__main__':
    generate_report()