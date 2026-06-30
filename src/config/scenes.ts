export type SceneId = "school" | "essay" | "visa";

export interface Scene {
  id: SceneId;
  label: string;
  shortLabel: string;
  icon: string;
  greeting: string;
  intro: string;
  quickPrompts: { icon: string; text: string }[];
  followups: string[];
}

export const SCENES: Scene[] = [
  {
    id: "school",
    label: "选校定位",
    shortLabel: "选校",
    icon: "🎓",
    greeting: "选校定位 · 我来帮你参谋",
    intro: "",
    quickPrompts: [
      { icon: "🇬🇧", text: "英国硕士选校：北京邮电大学 通信工程 GPA：82/100 大三 目标专业：计算机" },
      { icon: "🇺🇸", text: "美国 CS 硕士：985 高校 计算机 GPA：3.4/4.0 已毕业 目标专业：CS" },
      { icon: "🇦🇺", text: "澳洲硕士选校：双非 金融 GPA：85/100 大四 目标专业：金融" },
      { icon: "📋", text: "先帮我评估选校，一步步问我的情况" },
    ],
    followups: [
      "推荐几所保底院校",
      "雅思/托福要考到多少？",
      "如何写一份有竞争力的 PS？",
    ],
  },
  {
    id: "essay",
    label: "文书写作",
    shortLabel: "文书",
    icon: "✍️",
    greeting: "文书写作 · 把故事讲好",
    intro: "PS / CV / 推荐信怎么开头？结构怎么排？亮点怎么挖？我可以给你思路与模板。",
    quickPrompts: [
      { icon: "📝", text: "我的 PS 第一段该怎么写？有什么开头模板？" },
      { icon: "📄", text: "帮我优化这段个人陈述：" },
      { icon: "📚", text: "推荐信应该找什么样的老师写？" },
      { icon: "🎯", text: "CV 怎么突出科研和项目经历？" },
    ],
    followups: [
      "PS 字数一般多少合适？",
      "如何把跨专业经历写成亮点？",
      "推荐信里要不要写缺点？",
    ],
  },
  {
    id: "visa",
    label: "签证与材料",
    shortLabel: "签证",
    icon: "🛂",
    greeting: "签证疑问 · 帮你梳理",
    intro: "F-1 / Tier 4 / 资金证明 / 面签准备，材料清单和流程都帮你梳理清楚。",
    quickPrompts: [
      { icon: "🇺🇸", text: "F-1 签证需要准备哪些材料？" },
      { icon: "🇬🇧", text: "英国学生签资金证明要存多久？" },
      { icon: "💰", text: "签证存款多少合适？冻结期怎么算？" },
      { icon: "🎤", text: "美国签证面签常问哪些问题？" },
    ],
    followups: [
      "签证最早什么时候办？",
      "面签被拒了还能再签吗？",
      "I-20 是什么？怎么用？",
    ],
  },
];
