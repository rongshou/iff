import type { MBTIMajorResult, ChatMessage } from "../types";
import type { HistoryItem } from "../services/profile";

export function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    const hour = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return `${month}/${day} ${hour}:${min}`;
  } catch {
    return iso;
  }
}

export function viewDetail(item: HistoryItem) {
  const data = item.data as Record<string, unknown>;

  if (item.type === "mbti") {
    const m = data.result as MBTIMajorResult || data as unknown as MBTIMajorResult;
    window.alert(
      `🧠 ${m.type} · ${m.name}\n\n` +
      `✅ 推荐: ${(m.top_majors || []).join("、")}\n` +
      `⚠️ 慎重: ${(m.avoid_majors || []).join("、")}\n\n` +
      `💼 职业: ${m.career_path || ""}\n` +
      `💡 建议: ${m.study_tips || ""}`
    );
  } else if (item.type === "chat_session") {
    const msgs = (data.messages || []) as ChatMessage[];
    const sceneLabels: Record<string, string> = { school: "选校", essay: "文书", visa: "签证" };
    const sceneLabel = sceneLabels[data.scene as string] || data.scene as string;
    const text = msgs.map((m) =>
      `${m.role === "user" ? "🧑" : "🤖"}: ${m.content.slice(0, 120)}`
    ).join("\n\n");
    window.alert(`💬 ${sceneLabel} · ${msgs.length} 轮\n\n${text}`);
  } else if (item.type === "tianshu_report") {
    window.alert("🧭 天枢综合测评报告\n\n完整报告请在天枢中查看。\n测评结果已保存在档案的「天枢测评结果」区块。");
  }
}
