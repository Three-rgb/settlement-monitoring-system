"""
数据可视化模块
"""
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.database import get_engine


def plot_settlement_curves(output_path='output/figures/settlement_curves.png'):
    """绘制沉降曲线图"""
    # 读取数据
    engine = get_engine()
    df_obs = pd.read_sql("SELECT * FROM settlement_observations ORDER BY point_name, obs_date", engine)
    df_points = pd.read_sql("SELECT * FROM survey_points", engine)

    # 转换日期
    df_obs['obs_date'] = pd.to_datetime(df_obs['obs_date'])

    # 选择前6个点展示
    sample_points = df_points['point_name'].head(6).tolist()

    # 创建子图
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()

    for idx, point in enumerate(sample_points):
        ax = axes[idx]
        point_data = df_obs[df_obs['point_name'] == point]
        chainage = df_points[df_points['point_name'] == point]['chainage'].values[0]

        # 绘制曲线
        ax.plot(point_data['obs_date'], point_data['cumulative_settlement'],
                marker='o', linewidth=2, markersize=5, color='steelblue')
        ax.fill_between(point_data['obs_date'], 0, point_data['cumulative_settlement'],
                        alpha=0.3, color='steelblue')

        # 设置标题和标签
        ax.set_title(f'{point} ({chainage})', fontsize=11, fontweight='bold')
        ax.set_xlabel('观测日期', fontsize=9)
        ax.set_ylabel('累计沉降(mm)', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45, labelsize=8)

        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        # 添加最终值标注
        final_value = point_data['cumulative_settlement'].iloc[-1]
        ax.axhline(y=final_value, color='r', linestyle='--', alpha=0.5, linewidth=1)
        ax.text(0.02, 0.95, f'最终: {final_value:.1f}mm',
                transform=ax.transAxes, fontsize=9,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 隐藏多余子图
    for idx in range(len(sample_points), len(axes)):
        axes[idx].axis('off')

    plt.suptitle('施工期沉降观测曲线', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 沉降曲线图已保存: {output_path}")
    plt.show()

    return output_path


def plot_settlement_distribution(output_path='output/figures/settlement_distribution.png'):
    """绘制沉降分布统计图"""
    from src.analysis import get_settlement_summary

    summary = get_settlement_summary()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 左图：最大沉降量分布
    ax1.hist(summary['max_settlement'], bins=10, color='steelblue', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('最大沉降量(mm)', fontsize=11)
    ax1.set_ylabel('测点数量', fontsize=11)
    ax1.set_title('最大沉降量分布', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # 右图：沉降量排序
    summary_sorted = summary.sort_values('max_settlement', ascending=True)
    y_pos = range(len(summary_sorted))
    ax2.barh(y_pos, summary_sorted['max_settlement'], color='coral', alpha=0.7)
    ax2.set_yticks(y_pos[::5])  # 每5个显示一个
    ax2.set_yticklabels(summary_sorted['point_name'].iloc[::5], fontsize=8)
    ax2.set_xlabel('最大沉降量(mm)', fontsize=11)
    ax2.set_title('各测点最大沉降量', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 沉降分布图已保存: {output_path}")
    plt.show()

    return output_path


def main():
    """生成所有可视化成果"""
    print("=" * 50)
    print("生成可视化成果")
    print("=" * 50)

    plot_settlement_curves()
    plot_settlement_distribution()

    print("=" * 50)
    print("可视化完成")
    print("=" * 50)


if __name__ == '__main__':
    main()