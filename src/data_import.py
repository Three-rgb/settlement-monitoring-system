import os
import pandas as pd
from sqlalchemy import text
from src.database import get_engine

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def import_survey_points(csv_path=None):
    """导入测点表"""
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, 'data', 'survey_points.csv')

    print(f"导入测点数据: {csv_path}")
    df = pd.read_csv(csv_path)

    engine = get_engine()

    with engine.begin() as conn:
        # 先清空表
        conn.execute(text("TRUNCATE TABLE survey_points CASCADE"))
        print("   已清空旧数据")

        # 导入基础字段
        df[['point_name', 'chainage', 'x_coord', 'y_coord',
            'h_initial', 'point_type']].to_sql(
            'survey_points', conn, if_exists='append', index=False
        )

        # 更新空间字段
        for _, row in df.iterrows():
            sql = text("""
                UPDATE survey_points 
                SET geom = ST_SetSRID(ST_MakePoint(:x, :y), 4326)
                WHERE point_name = :name
            """)
            conn.execute(sql, {
                'x': row['x_coord'],
                'y': row['y_coord'],
                'name': row['point_name']
            })

    print(f"   成功导入 {len(df)} 个测点")
    return len(df)


def import_settlement_observations(csv_path=None):
    """导入观测记录表"""
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, 'data', 'settlement_observations.csv')

    print(f"导入观测数据: {csv_path}")
    df = pd.read_csv(csv_path)

    engine = get_engine()
    df.to_sql('settlement_observations', engine, if_exists='append', index=False)

    print(f"   成功导入 {len(df)} 条观测记录")
    return len(df)


def verify_import():
    """验证导入结果"""
    from src.database import execute_query

    point_count = execute_query("SELECT COUNT(*) FROM survey_points")[0][0]
    obs_count = execute_query("SELECT COUNT(*) FROM settlement_observations")[0][0]

    print("\n导入验证:")
    print(f"   测点表: {point_count} 条")
    print(f"   观测记录表: {obs_count} 条")

    return point_count, obs_count


def main():
    """主函数"""
    print("=" * 50)
    print("数据导入PostGIS")
    print("=" * 50)

    import_survey_points()  # 不传参数，使用默认路径
    import_settlement_observations()  # 不传参数，使用默认路径
    verify_import()

    print("=" * 50)
    print("数据导入完成")
    print("=" * 50)


if __name__ == '__main__':
    main()