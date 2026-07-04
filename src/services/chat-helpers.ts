import { getSchoolAbbrevMap } from "./school";
import { loadProfile } from "./profile";
import type { SceneId } from "../config/scenes";


/* =========================================================================
 * 场景（Tab）定义
 * 把留学问答拆成 4 个独立场景：每个场景有独立的对话历史 & 独立的开场白，
 * 避免 AI 在不同主题间串台（比如聊完选校去问签证，AI 还在选校语境里）。
 * ========================================================================= */


/* ---------- 工具函数 ---------- */

export function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

export const ts = () => Date.now();

/* =========================================================================
 * 信息收集（首次消息的字段完整性检查）
 * ========================================================================= */

export interface InfoField {
  key: string;
  label: string;
  prompt: string;
  hint: string;
}

export const SCENE_INFO: Record<SceneId, InfoField[]> = {
  school: [
    { key: "school", label: "毕业院校", prompt: "你的毕业院校是哪所？", hint: "例如 北京邮电大学 / 985" },
    { key: "major", label: "目前专业", prompt: "你目前读什么专业？", hint: "例如 通信工程 / 计算机" },
    { key: "gpa", label: "GPA/均分", prompt: "你的 GPA 或均分是多少？", hint: "例如 82/100 或 3.4/4.0" },
    { key: "targetCountry", label: "目标国家", prompt: "你想去哪个国家留学？", hint: "例如 英国 / 美国 / 澳洲" },
    { key: "targetMajor", label: "目标专业", prompt: "你想申请什么专业？", hint: "例如 本专业相关 / 跨专业" },
  ],
  essay: [
    { key: "docType", label: "文书类型", prompt: "你需要写什么类型的文书？", hint: "个人陈述 PS / 简历 CV / 推荐信" },
    { key: "target", label: "目标院校", prompt: "目标院校和专业是？", hint: "例如 帝国理工 CS" },
  ],
  visa: [
    { key: "targetCountry", label: "目标国家", prompt: "你要去哪个国家留学？", hint: "例如 美国 / 英国 / 澳洲" },
    { key: "visaType", label: "签证类型", prompt: "需要什么类型的签证？", hint: "例如 F-1 / Tier 4" },
  ],
};

/** 判断用户消息是否像选校推荐请求（而不是通用问答） */
export function looksLikeSchoolRequest(text: string): boolean {
  // 选校关键词
  const recommendKeywords = [
    "选校", "推荐", "匹配", "能申", "冲刺", "保底", "主申",
    "定位", "案例", "录取概率", "录取几率", "成功几率",
    "什么学校", "哪些学校", "哪所", "求推荐",
  ];
  if (recommendKeywords.some((k) => text.includes(k))) return true;

  // 包含 GPA/GRE/TOEFL/IELTS 分数模式（学生正在提供背景信息）
  if (/[Gg][Pp][Aa]|均分|绩点|GRE|托福|TOEFL|雅思|IELTS/.test(text)) return true;

  // 包含 "X/Y" 分数格式（如 82/100, 3.5/4.0）
  if (/\d+\.?\d*\s*\/\s*\d+/.test(text)) return true;

  // 包含学校+专业信息组合（如 "北邮 通信工程 GPA 82"）
  if (/(大学|学院)\s*.{1,20}(专业|GPA|均分)/.test(text)) return true;

  // 包含 "本科"+"硕士" 等学位关键词的组合
  if (/(本科|硕士|博士)\s*.{1,20}(申请|留学|选校)/.test(text)) return true;

  return false;
}

/* ----- 简称 → 全称映射：从后端 /api/school/abbreviations 动态加载 ----- */
/* （原硬编码 SCHOOL_ABBREV 已迁移到 backend/app/services/school_abbrev.py） */

/* ----- 国家别名（与后端 COUNTRY_ALIASES 保持一致） ----- */
export const COUNTRY_ALIASES: Record<string, string> = {
  "英国": "英国", "美国": "美国", "澳洲": "澳洲", "澳大利亚": "澳洲",
  "加拿大": "加拿大", "枫叶国": "加拿大",
  "香港": "香港", "新加坡": "新加坡",
  "日本": "日本", "韩国": "韩国",
  "德国": "德国", "法国": "法国",
  "新西兰": "新西兰", "爱尔兰": "爱尔兰",
  "荷兰": "荷兰", "瑞士": "瑞士",
  "意大利": "意大利", "西班牙": "西班牙",
  "瑞典": "瑞典", "丹麦": "丹麦",
  "芬兰": "芬兰", "挪威": "挪威",
  "马来西亚": "马来西亚", "澳门": "澳门",
};
/** 从用户输入中提取已有信息 */
export async function extractInfo(text: string): Promise<Record<string, string>> {
  const info: Record<string, string> = {};

  // --- GPA（可选冒号，支持空格 "GPA 82/100" 和 "均分82"）---
  const mGpa = text.match(/(?:GPA|均分|绩点)\s*[:：]?\s*([\d.]+(?:\s*\/\s*[\d.]+)?)/i);
  if (mGpa) info.gpa = mGpa[1];

  // --- 学校（简称优先，再查 "大学/学院" 全名）---
  const SCHOOL_ABBREV = await getSchoolAbbrevMap();
  for (const [abbr, full] of Object.entries(SCHOOL_ABBREV)) {
    if (text.includes(abbr)) {
      info.school = full;
      break;
    }
  }
  if (!info.school) {
    const mSchool = text.match(/(?:大学|学院)/);
    if (mSchool) {
      const parts = text.split(/[\s\n\r]+/);
      for (const p of parts) {
        if (/大学|学院/.test(p)) {
          const idx = parts.indexOf(p);
          info.school = (idx > 0 ? parts[idx - 1] + " " : "") + p;
          break;
        }
      }
    }
  }

  // --- 目标国家（别名 → 标准名）---
  for (const [alias, standard] of Object.entries(COUNTRY_ALIASES)) {
    if (text.includes(alias)) {
      info.targetCountry = standard;
      break;
    }
  }

  // --- 目标专业（"目标专业：计算机" / "目标专业：Computer Science"）---
  const mTargetMajor = text.match(/目标专业[：:是为]?\s*([^，。,.!！?？\n]{1,30})/);
  if (mTargetMajor && !["其他","其它","不限","不确定","还没想好","未定"].includes(mTargetMajor[1].trim())) {
    info.targetMajor = mTargetMajor[1].trim();
  }

  // --- 目前专业 — 先移除"目标专业xxx"避免误匹配，再匹配多种自然表达 ---
  const textForMajor = text.replace(/目标专业[：:是为]?\s*[^，。,.!！?？\n]{1,30}/g, "");
  let mMajor = textForMajor.match(/(?:本科|在读|目前)[\s]*(?:读|学|专业)[：:是为]?\s*([^，。,.!！?？\n]{2,30})/);
  if (!mMajor) mMajor = textForMajor.match(/专业[：:是为]?\s*([^，。,.!！?？\n]{2,30})/);
  if (!mMajor) mMajor = textForMajor.match(/(?:读|学)\s*([^，。,.!！?？\n]{2,30})/);
  if (!mMajor) mMajor = textForMajor.match(/([^，。,.!！?？\s\n]{2,8})专业(?!课|课目|课表|课成绩|课老师)/);
  if (mMajor && !info.major) info.major = mMajor[1].trim();

  // --- 文书 / 签证类型 ---
  const mDoc = text.match(/PS|个人陈述|CV|简历|推荐信/);
  if (mDoc) info.docType = mDoc[0];
  const mVisa = text.match(/F-1|Tier 4|学生签/);
  if (mVisa) info.visaType = mVisa[0];

  // --- 兜底：简短回答（用户直接说 "计算机" / "金融" / "CS" 等）---
  // 仅在以上规则都没提取到 major/targetMajor 时触发
  if (!info.major && !info.targetMajor) {
    const trimmed = text.trim();
    // 2~30 字，只含中文/英文/数字/连字符，无标点/换行
    if (trimmed.length >= 2 && trimmed.length <= 30 && /^[\u4e00-\u9fffA-Za-z0-9\s\-+]+$/.test(trimmed)) {
      // 排除国家/地区名、学校名
      const notMajor = new Set([
        ...Object.values(COUNTRY_ALIASES),
        "本科","硕士","博士","申请","留学","选校",
      ]);
      if (!notMajor.has(trimmed) && !/(大学|学院)$/.test(trimmed) && !/^\d+$/.test(trimmed)) {
        // 如果能匹配到已知的专业分类关键词，当成目前专业
        const MAJOR_CATEGORIES = [
          "计算机","金融","商科","工程","教育","传媒","法律","医学","数学","艺术",
          "CS","EE","BA","DS","MBA","LLM",
          "经济","会计","管理","市场","营销","心理","社会","历史","哲学","文学",
          "物理","化学","生物","材料","机械","电子","电气","土木","建筑",
          "护理","药学","公卫","统计","应数","纯数","交互","设计","时尚",
          "英语","翻译","日语","法语","德语","小语种",
        ];
        const lower = trimmed.toLowerCase();
        const isKnownMajor = MAJOR_CATEGORIES.some(cat => lower.includes(cat.toLowerCase()) || cat.toLowerCase().includes(lower));
        if (isKnownMajor || trimmed.length <= 6) {
          // 短词或匹配到已知专业类别 → 作为目前专业
          info.major = trimmed;
        }
      }
    }
  }

  return info;
}

export function getMissingFields(info: Record<string, string>, fields: InfoField[]): InfoField[] {
  return fields.filter((f) => !info[f.key]);
}

/** 从个人档案预填信息收集字段，避免追问已设置的内容 */
export function profileToInfo(profile: NonNullable<ReturnType<typeof loadProfile>>): Record<string, string> {
  const info: Record<string, string> = {};
  if (profile.school) info.school = profile.school;
  if (profile.original_major) info.major = profile.original_major;
  if (profile.gpa_score != null) {
    const fmt = profile.gpa_format ? `/${profile.gpa_format}` : "";
    info.gpa = `${profile.gpa_score}${fmt}`;
  }
  if (profile.target_countries?.length) info.targetCountry = profile.target_countries[0];
  if (profile.target_major) info.targetMajor = profile.target_major;
  return info;
}

/** 把已有信息转为一段描述文字 */
export function infoToDescription(info: Record<string, string>): string {
  const parts: string[] = [];
  if (info.school) parts.push(`学校：${info.school}`);
  if (info.major) parts.push(`专业：${info.major}`);
  if (info.gpa) parts.push(`GPA：${info.gpa}`);
  if (info.targetCountry) parts.push(`目标国家：${info.targetCountry}`);
  if (info.targetMajor) parts.push(`目标专业：${info.targetMajor}`);
  if (info.docType) parts.push(`文书类型：${info.docType}`);
  if (info.visaType) parts.push(`签证类型：${info.visaType}`);
  return parts.join("，");
}

/* =========================================================================
 * 主组件
 * ========================================================================= */



