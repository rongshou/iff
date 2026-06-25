"""
天枢 · 示例学生跑通脚本
虚拟示例学生:林小满 / 男 / 2010-05-15 14:30 / 北京 / 高一
测评结果:MBTI=INTJ-A,霍兰德=IRA 主导
跑完全流程,生成 HTML 报告。
"""
import sys
from datetime import datetime
from pathlib import Path

# 加入 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from bazi import get_four_pillars
from ziwei import get_ziwei_summary
from mbti import get_mbti_info
from holland import get_holland_info
from cross import cross_validate
from majors import recommend_majors
from career import generate_career_path
from report import generate_html_report


def run_demo():
    print("=" * 60)
    print("🎯 天枢 · 示例学生测评与规划")
    print("=" * 60)

    # ============ Step 1: 学生基础信息 ============
    student_info = {
        "姓名": "林小满",
        "性别": "男",
        "出生时间": datetime(2010, 5, 15, 14, 30),
        "出生地": "北京",
        "当前学段": "高一(北京某重点中学)",
        "MBTI": "INTJ-A",
        "霍兰德": {"R": 30, "I": 85, "A": 70, "S": 65, "E": 40, "C": 35},
        "家庭背景": "父母均为教师,家中重视教育,无经济压力",
        "个人偏好": "对计算机、AI 有浓厚兴趣,数学成绩年级前列,语文一般",
        "排斥领域": "纯销售、商务应酬、强体力劳动",
        "未来诉求": "希望进入硬核技术领域,做有长期价值的工作",
    }

    print(f"\n📋 学生信息")
    print(f"  姓名:{student_info['姓名']}")
    print(f"  性别:{student_info['性别']}")
    print(f"  出生:{student_info['出生时间'].strftime('%Y-%m-%d %H:%M')}({student_info['出生地']})")
    print(f"  学段:{student_info['当前学段']}")
    print(f"  MBTI:{student_info['MBTI']}")
    print(f"  霍兰德:{student_info['霍兰德']}")

    # ============ Step 2: 八字排盘 ============
    print(f"\n🔮 Step 1/7 · 八字排盘...")
    bazi = get_four_pillars(student_info["出生时间"])
    print(f"  ✅ 四柱:{bazi['年柱']} / {bazi['月柱']} / {bazi['日柱']} / {bazi['时柱']}")
    print(f"  ✅ 日主:{bazi['日主']}({bazi['日主五行']})")
    print(f"  ✅ 喜用神:{bazi['喜用神']}")

    # ============ Step 3: 紫微简版 ============
    print(f"\n⭐ Step 2/7 · 紫微斗数(简版)...")
    ziwei = get_ziwei_summary(student_info["出生时间"])
    print(f"  ✅ 命宫:{ziwei['命宫']['主星']}")
    print(f"  ✅ 事业宫:{ziwei['事业宫']['主星']}")
    print(f"  ✅ 财帛宫:{ziwei['财帛宫']['主星']}")

    # ============ Step 4: MBTI 解析 ============
    print(f"\n🧠 Step 3/7 · MBTI 解析...")
    mbti = get_mbti_info(student_info["MBTI"])
    print(f"  ✅ 类型:{mbti['完整类型']}({mbti['昵称']})")
    print(f"  ✅ 核心:{mbti['核心']}")

    # ============ Step 5: 霍兰德解析 ============
    print(f"\n🎯 Step 4/7 · 霍兰德解析...")
    holland = get_holland_info(student_info["霍兰德"])
    print(f"  ✅ 核心 3 位代码:{holland['核心3位代码']}")
    print(f"  ✅ 解析:{holland['代码解析']}")

    # ============ Step 6: 交叉验证 ============
    print(f"\n🔗 Step 5/7 · 多维度交叉验证...")
    cross = cross_validate(bazi, ziwei, mbti, holland)
    print(f"  ✅ 核心主题:{cross['核心定位标签']['主题']}")
    print(f"  ✅ 主方向:{cross['核心定位标签']['主方向']}")
    print(f"  ✅ 核心定位:{cross['核心定位标签']['标签']}")

    # ============ Step 7: 专业推荐 ============
    print(f"\n🎓 Step 6/7 · 专业选择推荐...")
    majors = recommend_majors(cross, bazi, mbti, holland)
    print(f"  ✅ 第一优先级:")
    for m in majors["第一优先级(核心适配)"]:
        print(f"     - {m['专业']}(匹配分:{m['匹配分']})")
    print(f"  ✅ 第二优先级:")
    for m in majors["第二优先级(次优适配)"]:
        print(f"     - {m['专业']}(匹配分:{m['匹配分']})")
    print(f"  ⚠️  风险规避:")
    for r in majors["风险规避清单"]:
        print(f"     - {r['专业']}")

    # ============ Step 8: 生涯路径 ============
    print(f"\n🛤️  Step 7/7 · 生涯路径生成...")
    career = generate_career_path(student_info, cross, majors)
    print(f"  ✅ 4 阶段路径已生成")
    print(f"  ✅ {len(career['关键节点行动指引'])} 个关键节点")

    # ============ Step 9: 生成 HTML 报告 ============
    print(f"\n📄 生成 HTML 报告...")
    all_results = {
        "bazi": bazi,
        "ziwei": ziwei,
        "mbti": mbti,
        "holland": holland,
        "cross": cross,
        "majors": majors,
        "career": career,
    }

    # 输出路径
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"示例学生_{student_info['姓名']}_{timestamp}.html"

    generate_html_report(student_info, all_results, str(output_file))

    file_size = output_file.stat().st_size

    print(f"\n" + "=" * 60)
    print(f"✅ 报告已生成:{output_file}")
    print(f"📦 文件大小:{file_size:,} 字节({file_size/1024:.1f} KB)")
    print(f"🌐 用浏览器打开:file://{output_file}")
    print(f"🖨️  浏览器打开后按 Ctrl+P 可打印为 PDF")
    print(f"=" * 60)


if __name__ == "__main__":
    run_demo()