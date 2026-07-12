"""
施工项目沉降监测数据管理系统 - 主程序
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import test_connection
from src.data_import import main as import_data
from src.analysis import generate_report
from src.visualization import main as generate_visualization
from src.training_dataset_export import export_training_datasets


def full_pipeline():
    """完整数据处理流程"""
    print("\n" + "=" * 60)
    print("施工项目沉降监测数据管理系统")
    print("=" * 60)

    # 1. 测试数据库连接
    print("\n【步骤1】测试数据库连接")
    if not test_connection():
        print("数据库连接失败，请检查配置")
        return False

    # 2. 数据导入
    print("\n【步骤2】导入数据到PostGIS")
    try:
        import_data()
    except Exception as e:
        print(f"数据导入失败: {e}")
        print("提示: 如果数据已存在，请检查是否重复导入")
        return False

    # 3. 数据分析
    print("\n【步骤3】数据分析")
    generate_report()

    # 4. 可视化
    print("\n【步骤4】生成可视化成果")
    generate_visualization()

    # 5. 导出训练/评测数据集（面试导向）
    print("\n【步骤5】导出训练/评测数据集")
    paths = export_training_datasets()
    print(f"[OK] SFT数据集: {paths['sft']}")
    print(f"[OK] Eval数据集: {paths['eval']}")

    print("\n" + "=" * 60)
    print("全部流程执行完成！")
    print("=" * 60)

    return True


if __name__ == '__main__':
    full_pipeline()