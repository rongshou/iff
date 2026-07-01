"""知识库内容过滤规则 —— 多层防线阻止垃圾信息进入知识库。

过滤层级：
1. 内容质量门槛（纯文本长度、中文字符占比）
2. 时间衰减（过期文章不索引）
3. 分类黑名单（"综合资讯"中非留学内容过滤）
4. 自动排除记录（写入 excluded_articles 表供人工审查）
"""
import re
import time
from typing import Optional


# =====================================================================
# 过滤阈值（可调参数）
# =====================================================================

MIN_CLEAN_TEXT_LENGTH = 200       # 清洗后纯文本最少字数
MIN_CHINESE_RATIO = 0.30          # 中文字符最低占比
MAX_ARTICLE_AGE_DAYS = 730        # 文章最大年龄（2年），超过不索引
OLD_ARTICLE_DAYS = 180            # 超过此天数标记为"旧文"，搜索时降权

# =====================================================================
# 留学核心关键词 —— 用于"综合资讯"分类的二次过滤
# =====================================================================

STUDY_ABROAD_KEYWORDS = [
    # 通用
    "留学", "出国", "海外", "境外", "国际学校", "海外升学",
    # 申请
    "申请", "院校", "大学", "学院", "专业", "硕士", "本科", "博士",
    "研究生", "本科", "MBA", "EMBA",
    # 考试
    "雅思", "托福", "GRE", "GMAT", "IELTS", "TOEFL", "PTE", "DET",
    "语言考试", "语言成绩",
    # 成绩
    "GPA", "gpa", "均分", "绩点", "成绩", "分数",
    # 录取
    "offer", "录取", "录取率", "录取案例", "入学",
    # 签证
    "签证", "I-20", "CAS", "COE", "出入境",
    # 费用
    "学费", "奖学金", "生活费", "费用",
    # 文书
    "文书", "PS", "个人陈述", "推荐信", "简历",
    # 选校
    "选校", "择校", "定位", "冲刺", "保底", "主申",
    # 排名
    "QS", "USNews", "THE", "排名", "榜单",
    # 国家/地区
    "英国", "美国", "澳洲", "澳大利亚", "加拿大", "香港", "新加坡",
    "日本", "德国", "法国", "新西兰", "爱尔兰", "韩国", "马来西亚",
    # 就业
    "就业", "实习", "OPT", "CPT", "求职",
    # 其他
    "毕业", "学位", "课程", "招生", "入学要求", "语言要求",
]


# =====================================================================
# 过滤函数
# =====================================================================

def check_quality(text_clean: str) -> tuple[bool, Optional[str]]:
    """检查内容质量是否达标。

    Args:
        text_clean: 清洗后的纯文本

    Returns:
        (通过, 失败原因)
    """
    if not text_clean:
        return False, "quality_low"

    if len(text_clean) < MIN_CLEAN_TEXT_LENGTH:
        return False, "quality_low"

    chinese_chars = sum(1 for c in text_clean if '\u4e00' <= c <= '\u9fff')
    total_chars = len(text_clean.strip())
    if total_chars > 0 and chinese_chars / total_chars < MIN_CHINESE_RATIO:
        return False, "quality_low"

    return True, None


def check_freshness(publish_time: int | None) -> tuple[bool, Optional[str]]:
    """检查文章是否过期。

    Returns:
        (通过, 失败原因)
    """
    if not publish_time:
        return True, None  # 无时间信息不过滤

    age_days = (time.time() - publish_time) / 86400
    if age_days > MAX_ARTICLE_AGE_DAYS:
        return False, "outdated"

    return True, None


def is_old_article(publish_time: int | None) -> bool:
    """判断文章是否为"旧文"（超过 6 个月但未满 2 年）。"""
    if not publish_time:
        return False
    age_days = (time.time() - publish_time) / 86400
    return age_days > OLD_ARTICLE_DAYS


def check_category_relevance(
    category: str, title: str, content: str
) -> tuple[bool, Optional[str]]:
    """检查文章内容是否与其分类相关。

    目前仅对"综合资讯"做二次过滤：
    如果标题+内容不含任何留学核心关键词，视为 off_topic。
    """
    if category != "综合资讯":
        return True, None

    combined = f"{title} {content[:500]}"
    for kw in STUDY_ABROAD_KEYWORDS:
        if kw.lower() in combined.lower():
            return True, None

    return False, "off_topic"


def should_index_article(
    title: str,
    content_clean: str,
    category: str,
    publish_time: int | None = None,
) -> tuple[bool, Optional[str]]:
    """综合判断文章是否应被索引。

    按优先级依次检查：质量 → 时效 → 分类相关性。

    Args:
        title: 文章标题
        content_clean: 清洗后的纯文本（已由 _clean_html + _prepare_for_index 处理）
        category: ai_category
        publish_time: 发布时间戳（Unix seconds）

    Returns:
        (应索引, 排除原因)
    """
    # 1. 质量门槛
    ok, reason = check_quality(content_clean)
    if not ok:
        return False, reason

    # 2. 时间过滤
    ok, reason = check_freshness(publish_time)
    if not ok:
        return False, reason

    # 3. 分类相关性
    ok, reason = check_category_relevance(category, title, content_clean)
    if not ok:
        return False, reason

    return True, None
