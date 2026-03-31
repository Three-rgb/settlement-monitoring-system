"""
基于OSM道路数据生成模拟沉降监测数据
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from datetime import datetime, timedelta
import os


def load_osm_roads(shp_path):
    """加载OSM道路数据"""
    print(f"加载道路数据: {shp_path}")
    roads = gpd.read_file(shp_path)
    print(f"   共 {len(roads)} 条道路")
    return roads


def select_main_road(roads, min_length=100):
    """选择一条主干道路"""
    # 筛选主要道路
    road_types = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']
    main_roads = roads[roads['fclass'].isin(road_types)].copy()

    print(f"   筛选后剩余 {len(main_roads)} 条主干道路")

    if len(main_roads) == 0:
        raise ValueError("未找到合适的主干道路")

    # 转换到投影坐标系计算真实长度（米）
    try:
        # 先设置CRS（OSM数据通常是WGS84）
        if main_roads.crs is None:
            main_roads.set_crs(epsg=4326, inplace=True)
            print(f"   已设置CRS为WGS84(EPSG:4326)")

        # 使用UTM Zone 48N（适合108-114°E）
        main_roads_proj = main_roads.to_crs(epsg=32648)
        lengths = main_roads_proj.geometry.length
        print(f"   使用UTM投影计算长度")
    except Exception as e:
        print(f"   投影转换失败({e})，使用原始坐标")
        lengths = main_roads.geometry.length

    # 选择长度足够的
    valid_roads = main_roads[lengths > min_length]

    if len(valid_roads) == 0:
        print(f"   警告：没有长度>{min_length}m的道路，选择最长的")
        longest_idx = lengths.idxmax()
        selected = main_roads.loc[longest_idx]
        actual_length = lengths.max()
    else:
        # 返回最长的
        longest_idx = lengths.idxmax()
        selected = main_roads.loc[longest_idx]
        actual_length = lengths.max()

    road_name = selected.get('name', '未命名')
    road_type = selected.get('fclass', 'unknown')
    print(f"   选定道路: {road_name} ({road_type}), 长度: {actual_length:.0f}米")

    return selected


def generate_survey_points(road_geom, interval=50, start_chainage=0):
    """沿道路生成沉降监测点"""
    # 转换到投影坐标系计算长度
    try:
        import pyproj
        from shapely.ops import transform

        # 定义投影转换（WGS84 -> UTM 48N）
        project = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32648", always_xy=True).transform
        road_geom_proj = transform(project, road_geom)
        total_length = int(road_geom_proj.length)
        print(f"   投影后长度: {total_length}米")
    except Exception as e:
        # 如果转换失败，使用原始几何估算
        total_length = int(road_geom.length * 111000)  # 粗略估算：1度≈111km
        print(f"   警告：投影失败({e})，使用估算长度: {total_length}米")

    # 限制测点数量（最多50个，避免数据量过大）
    max_points = 50
    n_points = min(max_points, max(1, total_length // interval))

    points = []
    for i in range(n_points):
        # 使用比例插值
        ratio = i / max(n_points - 1, 1) if n_points > 1 else 0
        point_geom = road_geom.interpolate(ratio, normalized=True)

        distance = int(ratio * total_length) + start_chainage
        chainage = f"K0+{distance:03d}"

        points.append({
            'point_name': f'SP-{i + 1:02d}',
            'chainage': chainage,
            'x_coord': round(point_geom.x, 6),
            'y_coord': round(point_geom.y, 6),
            'h_initial': round(100 + np.random.uniform(-5, 5), 2),
            'point_type': '沉降观测点',
            'geometry': point_geom
        })

    df = gpd.GeoDataFrame(points, crs='EPSG:4326')
    actual_coverage = n_points * interval
    print(f"   生成 {len(df)} 个测点，间距 {interval} 米，覆盖 {actual_coverage} 米")
    return df


def generate_settlement_data(points_df, start_date='2024-01-01', periods=12):
    """生成沉降观测数据"""
    start = datetime.strptime(start_date, '%Y-%m-%d')

    observations = []
    for _, point in points_df.iterrows():
        cumulative = 0

        for period in range(periods):
            obs_date = start + timedelta(days=30 * period)

            # 沉降规律：前6期快（施工期），后6期慢（稳定期）
            if period < 6:
                rate = np.random.uniform(3, 8) + np.random.normal(0, 1)
            else:
                rate = np.random.uniform(0.5, 2) + np.random.normal(0, 0.3)

            rate = max(0.1, rate)
            cumulative += rate

            observations.append({
                'point_name': point['point_name'],
                'obs_date': obs_date.strftime('%Y-%m-%d'),
                'period': period + 1,
                'settlement_rate': round(rate, 2),
                'cumulative_settlement': round(cumulative, 2),
                'remark': '正常' if rate < 5 else '需关注'
            })

    df = pd.DataFrame(observations)
    print(f"   生成 {len(df)} 条观测记录（{periods}期×{len(points_df)}点）")
    return df


def save_data(points_df, obs_df, output_dir='data'):
    """保存数据到CSV"""
    os.makedirs(output_dir, exist_ok=True)

    # 保存测点（不含geometry字段）
    points_csv = os.path.join(output_dir, 'survey_points.csv')
    points_df[['point_name', 'chainage', 'x_coord', 'y_coord',
               'h_initial', 'point_type']].to_csv(points_csv, index=False, encoding='utf-8-sig')

    # 保存观测记录
    obs_csv = os.path.join(output_dir, 'settlement_observations.csv')
    obs_df.to_csv(obs_csv, index=False, encoding='utf-8-sig')

    print(f"   数据已保存:")
    print(f"      - {points_csv}")
    print(f"      - {obs_csv}")

    return points_csv, obs_csv


def main(shp_path=r'F:\settlement_monitoring_system\data\raw\gis_osm_roads_free_1.shp'):
    """主函数：生成完整数据集"""
    print("=" * 50)
    print("沉降监测数据生成")
    print("=" * 50)

    # 加载OSM数据
    roads = load_osm_roads(shp_path)
    road = select_main_road(roads)

    # 生成测点
    points_df = generate_survey_points(road.geometry, interval=50)

    # 生成观测数据
    obs_df = generate_settlement_data(points_df, periods=12)

    # 保存
    save_data(points_df, obs_df, 'data')

    print("=" * 50)
    print("数据生成完成")
    print("=" * 50)

    return points_df, obs_df


if __name__ == '__main__':
    main()