"""
天枢 · HTML 报告生成模块
把所有测评 + 规划结果汇总成一份精美的 HTML 报告。
样式:简洁专业、深蓝主色 + 浅灰背景,易打印。
"""

from datetime import datetime

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{student_name} · 天枢综合特质测评与生涯规划报告</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
    line-height: 1.7;
    color: #2c3e50;
    background: #f5f7fa;
    padding: 40px 20px;
}}
.container {{
    max-width: 900px;
    margin: 0 auto;
    background: #fff;
    padding: 50px 60px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-radius: 8px;
}}
header {{
    border-bottom: 3px solid #2c5282;
    padding-bottom: 25px;
    margin-bottom: 35px;
}}
h1 {{
    color: #2c5282;
    font-size: 28px;
    margin-bottom: 8px;
    letter-spacing: 2px;
}}
h2 {{
    color: #2c5282;
    font-size: 20px;
    margin: 30px 0 15px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
}}
h3 {{
    color: #4a5568;
    font-size: 16px;
    margin: 18px 0 10px 0;
    font-weight: 600;
}}
h4 {{
    color: #718096;
    font-size: 14px;
    margin: 12px 0 8px 0;
    font-weight: 600;
}}
.meta {{
    color: #718096;
    font-size: 14px;
    margin-top: 10px;
}}
.meta span {{ margin-right: 20px; }}
.section {{
    margin-bottom: 35px;
}}
.callout {{
    background: #ebf8ff;
    border-left: 4px solid #3182ce;
    padding: 18px 22px;
    margin: 18px 0;
    border-radius: 4px;
}}
.callout-title {{
    color: #2c5282;
    font-weight: 600;
    margin-bottom: 8px;
}}
.tag {{
    display: inline-block;
    background: #edf2f7;
    color: #2d3748;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 13px;
    margin: 2px;
}}
.tag-primary {{
    background: #2c5282;
    color: #fff;
}}
.tag-warning {{
    background: #fef5e7;
    color: #c05621;
}}
.tag-danger {{
    background: #fed7d7;
    color: #c53030;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 14px;
}}
th, td {{
    border: 1px solid #e2e8f0;
    padding: 10px 14px;
    text-align: left;
}}
th {{
    background: #2c5282;
    color: #fff;
    font-weight: 600;
}}
tr:nth-child(even) {{ background: #f7fafc; }}
ul, ol {{
    margin: 10px 0 10px 25px;
}}
li {{ margin: 6px 0; }}
.major-card {{
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 15px 20px;
    margin: 12px 0;
    background: #fafbfc;
}}
.major-title {{
    color: #2c5282;
    font-weight: 600;
    font-size: 16px;
    margin-bottom: 6px;
}}
.major-meta {{
    color: #718096;
    font-size: 13px;
    margin-bottom: 10px;
}}
.risk {{
    border-left: 4px solid #e53e3e;
    padding: 12px 18px;
    margin: 12px 0;
    background: #fff5f5;
    border-radius: 4px;
}}
.career-stage {{
    border: 1px solid #cbd5e0;
    border-radius: 6px;
    padding: 18px 22px;
    margin: 15px 0;
    background: #fff;
}}
.stage-title {{
    color: #2c5282;
    font-weight: 600;
    font-size: 17px;
    margin-bottom: 10px;
}}
.disclaimer {{
    margin-top: 50px;
    padding: 20px;
    background: #fffaf0;
    border-left: 4px solid #ed8936;
    border-radius: 4px;
    font-size: 13px;
    color: #744210;
}}
footer {{
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #e2e8f0;
    color: #a0aec0;
    font-size: 12px;
    text-align: center;
}}
@media print {{
    body {{ background: #fff; padding: 0; }}
    .container {{ box-shadow: none; padding: 20px; }}
}}
</style>
</head>
<body>
<div class="container">

<header>
    <h1>🎯 {student_name} · 综合特质测评与生涯规划报告</h1>
    <div class="meta">
        <span>📅 生成时间:{date}</span>
        <span>🔧 天枢系统 v0.1</span>
        <span>📚 基于东方命理 + 西方心理测评</span>
    </div>
</header>

<!-- 一、综合定位 -->
<div class="section">
    <h2>一、综合定位</h2>
    <div class="callout">
        <div class="callout-title">🎯 核心定位标签</div>
        <p>{position_label}</p>
        <p style="margin-top:8px;"><strong>主方向:</strong>{main_direction}</p>
    </div>

    <h3>核心竞争力组合</h3>
    <ul>
        {competitive_advantages}
    </ul>

    <h3>核心短板与风险</h3>
    <ul>
        {shortcomings}
    </ul>
</div>

<!-- 二、八字命理 -->
<div class="section">
    <h2>二、八字命理分析</h2>
    <table>
        <tr><th>项目</th><th>结果</th></tr>
        <tr><td>公历</td><td>{bazi_solar}</td></tr>
        <tr><td>农历</td><td>{bazi_lunar}</td></tr>
        <tr><td>年柱</td><td>{bazi_year}</td></tr>
        <tr><td>月柱</td><td>{bazi_month}</td></tr>
        <tr><td>日柱</td><td>{bazi_day}</td></tr>
        <tr><td>时柱</td><td>{bazi_hour}</td></tr>
        <tr><td>日主</td><td>{bazi_day_master}({bazi_day_wuxing})</td></tr>
        <tr><td>五行统计</td><td>{bazi_wuxing}</td></tr>
        <tr><td>喜用神</td><td>{bazi_xishen}</td></tr>
        <tr><td>忌神</td><td>{bazi_jishen}</td></tr>
    </table>

    <h3>核心性格</h3>
    <p>{bazi_personality}</p>

    <h3>学业事业先天适配</h3>
    <p>{bazi_career_fit}</p>
</div>

<!-- 三、紫微斗数 -->
<div class="section">
    <h2>三、紫微斗数简版</h2>
    {ziwei_content}
    <p style="color:#718096; font-size:13px; margin-top:15px;">⚠️ {ziwei_note}</p>
</div>

<!-- 四、MBTI -->
<div class="section">
    <h2>四、MBTI 人格类型</h2>
    <div class="callout">
        <div class="callout-title">🧠 {mbti_type} · {mbti_nick}</div>
        <p>{mbti_core}</p>
        <p style="margin-top:8px;"><strong>倾向:</strong>{mbti_tendency}</p>
    </div>

    <h3>认知模式</h3>
    <p>{mbti_cognition}</p>

    <h3>行为风格</h3>
    <p>{mbti_behavior}</p>

    <h3>优势与短板</h3>
    <table>
        <tr><th>优势</th><td>{mbti_strength}</td></tr>
        <tr><th>短板</th><td style="color:#c53030;">{mbti_weakness}</td></tr>
    </table>
</div>

<!-- 五、霍兰德 -->
<div class="section">
    <h2>五、霍兰德职业兴趣</h2>
    <div class="callout">
        <div class="callout-title">🎯 核心 3 位代码:{holland_code}</div>
        <p>{holland_explain}</p>
    </div>

    <h3>6 维度得分</h3>
    <table>
        <tr><th>维度</th><th>名称</th><th>得分</th><th>适配方向</th></tr>
        {holland_dim_table}
    </table>
</div>

<!-- 六、专业推荐 -->
<div class="section">
    <h2>六、专业选择推荐</h2>

    <h3>第一优先级(核心适配)</h3>
    {first_priority}

    <h3>第二优先级(次优适配)</h3>
    {second_priority}

    <h3>第三优先级(潜力适配)</h3>
    {third_priority}

    <h3>风险规避清单</h3>
    {risk_avoid}
</div>

<!-- 七、生涯路径 -->
<div class="section">
    <h2>七、生涯发展全路径</h2>
    {career_stages}

    <h3>关键节点行动指引</h3>
    <table>
        <tr><th>节点</th><th>时间</th><th>核心行动</th><th>注意事项</th></tr>
        {key_nodes}
    </table>

    <h3>健康与状态管理</h3>
    <ul>
        {health_tips}
    </ul>
</div>

<!-- 八、总结建议 -->
<div class="section">
    <h2>八、核心建议与避坑提醒</h2>
    <h3>核心发展建议(3-5 条)</h3>
    <ol>
        <li><strong>充分发挥 INTJ + IAS 的「研究型系统思考者」优势</strong>:在计算机科学/AI 等硬核技术领域深耕,前 5 年打造扎实的技术深度,后续向系统架构或研究专家方向发展。</li>
        <li><strong>针对性补足短板</strong>:社交与商务能力不足是显著风险,需刻意练习 — 通过技术分享、开源协作、小型团队项目等方式渐进式提升。</li>
        <li><strong>长期主义 + 动态调整</strong>:每 2-3 年做一次复盘,根据行业变化(尤其是 AI 行业的快速迭代)调整方向,但保持核心研究主题的连贯性。</li>
        <li><strong>平衡身心,避免内耗</strong>:内向型 + 高敏感倾向,长期高压工作易出现心理问题,需建立规律运动 + 兴趣释放的稳定机制。</li>
    </ol>

    <h3>核心避坑提醒(3-5 条)</h3>
    <ol>
        <li style="color:#c53030;">🚫 避免盲目追求院校排名而忽视专业适配度 — 选错专业代价远大于选低一档学校</li>
        <li style="color:#c53030;">🚫 避免进入高社交强度赛道(纯销售、商务 BD、客户经理)— 与核心特质冲突,长期易倦怠</li>
        <li style="color:#c53030;">🚫 避免只看短期薪资选择岗位 — 应优先考虑与核心特质匹配 + 长期成长性</li>
        <li style="color:#c53030;">🚫 避免孤立学习 — INTJ 易陷入「独立思考但不协作」陷阱,需主动建立导师 + 同伴网络</li>
        <li style="color:#c53030;">🚫 避免被 AI 行业快速迭代带来的焦虑裹挟 — 持续学习核心能力,不要追每一个热点</li>
    </ol>
</div>

<div class="disclaimer">
    <strong>⚠️ 重要声明</strong><br>
    1. 本报告基于「东方命理(八字、紫微)+ 西方心理测评(MBTI、霍兰德)」交叉生成,命理部分无科学证据支持,仅作为文化参考。<br>
    2. 紫微斗数为简版排盘(仅取核心三宫),完整分析建议使用专业排盘软件。<br>
    3. 测评结果会随时间、经历变化,建议每 2-3 年做一次复盘调整。<br>
    4. 重大人生决策(高考志愿、长期职业规划)请结合实际能力测试、行业调研、家庭情况综合判断。
</div>

<footer>
    天枢 · 综合特质测评与生涯规划系统 v0.1 · 生成于 {date}
</footer>

</div>
</body>
</html>
"""


def generate_html_report(student_info: dict, all_results: dict, output_path: str) -> str:
    """
    生成 HTML 报告并写入文件。
    输入:
        student_info: {姓名, 出生时间, 学段, ...}
        all_results: {
            "bazi": 八字结果, "ziwei": 紫微结果, "mbti": MBTI结果, "holland": 霍兰德结果,
            "cross": 交叉验证, "majors": 专业推荐, "career": 生涯路径
        }
        output_path: 输出文件路径
    """
    bazi = all_results["bazi"]
    ziwei = all_results["ziwei"]
    mbti = all_results["mbti"]
    holland = all_results["holland"]
    cross = all_results["cross"]
    majors = all_results["majors"]
    career = all_results["career"]

    # 紫微 HTML
    ziwei_html = ""
    for gong in ["命宫", "事业宫", "财帛宫"]:
        if gong in ziwei:
            g = ziwei[gong]
            ziwei_html += f'<h4>{g["宫位"]}:主星 {g["主星"]}</h4>'
            ziwei_html += f'<p><strong>特质:</strong>{g["特质"]}</p>'
            ziwei_html += f'<p><strong>适配:</strong>{g["适配"]}</p>'

    # 霍兰德维度表
    holland_dim_html = ""
    sorted_dims = holland["排序"]
    for code, score in sorted_dims:
        info = holland["各维度详情"][code]
        holland_dim_html += f'<tr><td>{code}</td><td>{info["名"]}</td><td>{score}</td><td>{info["适配"]}</td></tr>'

    # 专业推荐 HTML
    def render_major(m):
        html = f'<div class="major-card">'
        html += f'<div class="major-title">{m["专业"]}'
        if "匹配分" in m:
            html += f' <span class="tag tag-primary">匹配分 {m["匹配分"]}</span>'
        html += '</div>'
        if "细分方向" in m:
            html += f'<div class="major-meta">细分方向:{" · ".join(m["细分方向"])}</div>'
        if "匹配逻辑" in m:
            html += f'<p><strong>匹配逻辑:</strong>{m["匹配逻辑"]}</p>'
        if "核心课程" in m:
            html += f'<p><strong>核心课程:</strong>{" · ".join(m["核心课程"])}</p>'
        if "院校梯队" in m:
            html += f'<p><strong>院校梯队:</strong>{" / ".join(m["院校梯队"][:6])}</p>'
        html += '</div>'
        return html

    first_p_html = "".join([render_major(m) for m in majors["第一优先级(核心适配)"]])
    second_p_html = "".join([render_major(m) for m in majors["第二优先级(次优适配)"]]) or "<p>无</p>"
    third_p_html = "".join([render_major(m) for m in majors["第三优先级(潜力适配)"]]) or "<p>无</p>"

    risk_html = ""
    for r in majors["风险规避清单"]:
        risk_html += f'<div class="risk"><strong>{r["专业"]}</strong><br>{r["风险"]}<br>'
        if "替代" in r:
            risk_html += f'<span style="color:#2c5282;">替代方案:</span>{r["替代"]}'
        risk_html += '</div>'

    # 生涯阶段 HTML
    career_html = ""
    for stage in career["4阶段路径"]:
        career_html += f'<div class="career-stage">'
        career_html += f'<div class="stage-title">{stage["阶段"]}</div>'
        career_html += f'<p><strong>核心目标:</strong>{stage["核心目标"]}</p>'

        # 不同阶段有不同字段
        for key in stage:
            if key in ["阶段", "核心目标"]:
                continue
            val = stage[key]
            if isinstance(val, list):
                career_html += f'<h4>{key}</h4><ul>'
                for item in val:
                    if isinstance(item, dict):
                        career_html += f'<li><strong>{item.get("路径", item.get("方向", ""))}</strong>:{item.get("说明", "")}</li>'
                    else:
                        career_html += f'<li>{item}</li>'
                career_html += '</ul>'
        career_html += '</div>'

    # 关键节点表
    nodes_html = ""
    for n in career["关键节点行动指引"]:
        nodes_html += f'<tr><td><strong>{n["节点"]}</strong></td><td>{n["时间"]}</td><td>{n["核心行动"]}</td><td>{n["注意"]}</td></tr>'

    # 填空
    html = REPORT_TEMPLATE.format(
        student_name=student_info["姓名"],
        date=datetime.now().strftime("%Y-%m-%d"),
        position_label=cross["核心定位标签"]["标签"],
        main_direction=cross["核心定位标签"]["主方向"],
        competitive_advantages="".join([f"<li>{a}</li>" for a in cross["核心竞争力组合"]]),
        shortcomings="".join([f"<li>{s}</li>" for s in cross["核心短板"]]),
        bazi_solar=bazi["阳历"],
        bazi_lunar=bazi["农历"],
        bazi_year=bazi["年柱"],
        bazi_month=bazi["月柱"],
        bazi_day=bazi["日柱"],
        bazi_hour=bazi["时柱"],
        bazi_day_master=bazi["日主"],
        bazi_day_wuxing=bazi["日主五行"],
        bazi_wuxing=" · ".join([f"{k}:{v}" for k, v in bazi["五行统计"].items()]),
        bazi_xishen=" · ".join(bazi["喜用神"]),
        bazi_jishen=" · ".join(set(bazi["忌神"])),
        bazi_personality=bazi["核心性格"],
        bazi_career_fit=bazi["学业事业适配"],
        ziwei_content=ziwei_html,
        ziwei_note=ziwei["说明"],
        mbti_type=mbti["完整类型"],
        mbti_nick=mbti["昵称"],
        mbti_core=mbti["核心"],
        mbti_tendency=mbti["倾向"],
        mbti_cognition=mbti["认知"],
        mbti_behavior=mbti["行为"],
        mbti_strength=mbti["优势"],
        mbti_weakness=mbti["短板"],
        holland_code=holland["核心3位代码"],
        holland_explain=holland["代码解析"],
        holland_dim_table=holland_dim_html,
        first_priority=first_p_html,
        second_priority=second_p_html,
        third_priority=third_p_html,
        risk_avoid=risk_html,
        career_stages=career_html,
        key_nodes=nodes_html,
        health_tips="".join([f"<li>{t}</li>" for t in career["健康与状态管理"]]),
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path