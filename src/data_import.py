import os
import pandas as pd
from sqlalchemy import text
from src.database import get_engine
from config import OUTPUT_DIR
from src.data_quality import (
    build_quality_report,
    clean_settlement_observations,
    clean_survey_points,
    write_quality_report,
)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def import_survey_points(csv_path=None):
    """导入测点表"""
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, 'data', 'survey_points.csv')

    print(f"导入测点数据: {csv_path}")
    df = pd.read_csv(csv_path)
    df, clean_notes = clean_survey_points(df)

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

        # 批量更新空间字段（executemany，避免 N 次往返）
        geom_params = [
            {'x': float(row['x_coord']), 'y': float(row['y_coord']), 'name': row['point_name']}
            for _, row in df.iterrows()
        ]
        if geom_params:
            conn.execute(
                text("""
                    UPDATE survey_points
                    SET geom = ST_SetSRID(ST_MakePoint(:x, :y), 4326)
                    WHERE point_name = :name
                """),
                geom_params,
            )

    print(f"   成功导入 {len(df)} 个测点")

    report = build_quality_report(
        dataset="survey_points",
        df=df,
        input_path=csv_path,
        primary_key=("point_name",),
        notes=clean_notes,
    )
    out = write_quality_report(report, os.path.join(OUTPUT_DIR, "reports"))
    print(f"   [OK] 质量报告已生成: {out}")
    return len(df)


def import_settlement_observations(csv_path=None):
    """导入观测记录表"""
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, 'data', 'settlement_observations.csv')

    print(f"导入观测数据: {csv_path}")
    df = pd.read_csv(csv_path)
    df, clean_notes = clean_settlement_observations(df)

    engine = get_engine()

    # 保障幂等：对业务主键(point_name, obs_date)做去重并写入；如已存在则更新
    with engine.begin() as conn:
        exists = conn.execute(
            text(
                """
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_settlement_point_date'
                LIMIT 1
                """
            )
        ).fetchone()
        if not exists:
            conn.execute(
                text(
                    """
                    ALTER TABLE settlement_observations
                    ADD CONSTRAINT uq_settlement_point_date
                    UNIQUE (point_name, obs_date)
                    """
                )
            )
        # 使用临时 staging 表批量导入，再 upsert 到正式表
        df.to_sql("stg_settlement_observations", conn, if_exists="replace", index=False)
        conn.execute(
            text(
                """
                INSERT INTO settlement_observations (
                    point_name, obs_date, period, settlement_rate, cumulative_settlement, remark
                )
                SELECT
                    point_name, obs_date, period, settlement_rate, cumulative_settlement, remark
                FROM stg_settlement_observations
                ON CONFLICT (point_name, obs_date) DO UPDATE SET
                    period = EXCLUDED.period,
                    settlement_rate = EXCLUDED.settlement_rate,
                    cumulative_settlement = EXCLUDED.cumulative_settlement,
                    remark = EXCLUDED.remark
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS stg_settlement_observations"))

    print(f"   成功导入 {len(df)} 条观测记录")

    report = build_quality_report(
        dataset="settlement_observations",
        df=df,
        input_path=csv_path,
        primary_key=("point_name", "obs_date"),
        notes=clean_notes,
    )
    out = write_quality_report(report, os.path.join(OUTPUT_DIR, "reports"))
    print(f"   [OK] 质量报告已生成: {out}")
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