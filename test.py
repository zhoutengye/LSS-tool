
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as mpath
import matplotlib.font_manager as fm
import os

# ==========================================
# 🍎 Mac 中文乱码终极解决方案：指定字体路径
# ==========================================
def get_mac_chinese_font():
    # 优先尝试 Arial Unicode MS (Mac最稳的中文支持)
    p1 = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    # 其次尝试 华文黑体
    p2 = '/System/Library/Fonts/STHeiti Light.ttc'
    # 最后尝试 苹方 (有时候 .ttc 格式 matplotlib 支持不好)
    p3 = '/System/Library/Fonts/PingFang.ttc'
    
    for p in [p1, p2, p3]:
        if os.path.exists(p):
            return fm.FontProperties(fname=p)
    return None

# 获取字体对象
my_font = get_mac_chinese_font()
if my_font is None:
    print("警告：未找到常用的 Mac 中文字体文件，请检查路径！")
else:
    print(f"成功加载字体: {my_font.get_name()}")

# 解决负号显示问题
plt.rcParams['axes.unicode_minus'] = False

def draw_house_architecture():
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 12)
    ax.axis('off')

    def draw_block(xy, width, height, color, title, keywords, shape='rect'):
        x, y = xy
        center_x = x + width / 2
        center_y = y + height / 2
        
        if shape == 'rect':
            rect = patches.Rectangle((x, y), width, height, linewidth=1.5, edgecolor='#333', facecolor=color, alpha=0.9)
            ax.add_patch(rect)
        elif shape == 'roof':
            path_data = [
                (mpath.Path.MOVETO, (x, y)),
                (mpath.Path.LINETO, (x + width, y)),
                (mpath.Path.LINETO, (x + width / 2, y + height)),
                (mpath.Path.CLOSEPOLY, (x, y)),
            ]
            codes, verts = zip(*path_data)
            path = mpath.Path(verts, codes)
            patch = patches.PathPatch(path, linewidth=1.5, edgecolor='#333', facecolor=color, alpha=0.9)
            ax.add_patch(patch)
            center_y = y + height * 0.35 

        # --- 关键修改：在这里显式指定 fontproperties=my_font ---
        # 1. 标题
        ax.text(center_x, center_y + 0.2, title, ha='center', va='center', 
                fontsize=14, fontweight='bold', color='#222', fontproperties=my_font)
        # 2. 关键词
        ax.text(center_x, center_y - 0.3, keywords, ha='center', va='center', 
                fontsize=10, color='#555', fontproperties=my_font)

    # --- 绘图内容保持不变 ---
    # 1. 地基
    draw_block((1, 0.5), 3.2, 1.5, '#CFD8DC', "机器人硬件系统构成", "物理载体 | 传感器 | 洁净模组")
    draw_block((4.4, 0.5), 3.2, 1.5, '#CFD8DC', "多层级智能软件体系", "RTOS | 算法库 | 认知引擎")
    draw_block((7.8, 0.5), 3.2, 1.5, '#CFD8DC', "开放式分布式系统架构", "云边端协同 | 分布式拓扑")

    # 2. 地板
    draw_block((1.5, 2.5), 9, 1.5, '#BBDEFB', "专用机构设计与驱动技术", "洁净本体 | 柔性执行器 | 精密驱动 | VHP耐受")

    # 3. 支柱
    draw_block((2, 4.5), 3.5, 2.5, '#C8E6C9', "智能感知与定位技术", "多模态融合 | SLAM导航\n过程PAT检测 | 环境重构")
    draw_block((6.5, 4.5), 3.5, 2.5, '#C8E6C9', "运动规划与控制技术", "高维避障 | 柔顺控制\n伺服动力学 | 防抖算法")

    # 4. 横梁
    draw_block((1.5, 7.5), 9, 1.5, '#E1BEE7', "智能认知与决策技术", "AI决策 | 知识图谱推理 | 任务规划 | 自主学习")

    # 5. 屋顶
    draw_block((1, 9.2), 10, 2.5, '#FFECB3', "软件机器人(RPA)与具身智能", "业务自动化 | 人机共融 | 主动安全 | 技能泛化", shape='roof')

    # 6. 箭头
    style = "Simple, tail_width=0.5, head_width=4, head_length=8"
    kw = dict(arrowstyle=style, color="#666")
    ax.add_patch(patches.FancyArrowPatch((2.6, 2.0), (2.6, 2.5), connectionstyle="arc3,rad=0", **kw))
    ax.add_patch(patches.FancyArrowPatch((6.0, 2.0), (6.0, 4.5), connectionstyle="arc3,rad=-0.2", linestyle="--", **kw))
    ax.add_patch(patches.FancyArrowPatch((6.0, 2.0), (6.0, 7.5), connectionstyle="arc3,rad=0.3", linestyle="--", **kw))
    ax.add_patch(patches.FancyArrowPatch((9.4, 2.0), (9.0, 9.5), connectionstyle="arc3,rad=-0.4", linestyle="--", **kw))

    # 图注
    ax.text(11, 6, "↑\n数\n字\n智\n能\n演\n进", fontsize=12, color="#888", va='center', fontproperties=my_font)
    ax.text(6, 0.2, "系统基础底座 (Foundation Layer)", ha='center', fontsize=11, fontweight='bold', fontproperties=my_font)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    draw_house_architecture()
