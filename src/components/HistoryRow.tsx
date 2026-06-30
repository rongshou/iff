import { formatDate } from "../utils/profile-utils";
import type { HistoryItem } from "../services/profile";

const TYPE_ICONS: Record<string, string> = {
  school: "🎓",
  essay: "📝",
  visa: "✈️",
  mbti: "🧠",
  chat_session: "💬",
  tianshu_report: "🧭",
};

function typeLabel(type: string, system: string): string {
  if (type === "mbti") return "🧠 MBTI 测评";
  if (type === "chat_session") return "💬 AI 对话";
  if (type === "tianshu_report") return system === "tianshu" ? "🧭 天枢测评" : "📄 测评报告";
  return "📄 记录";
}

interface Props {
  item: HistoryItem;
  onDelete: (id: string) => void;
  onViewDetail: (item: HistoryItem) => void;
}

export default function HistoryRow({ item, onDelete, onViewDetail }: Props) {
  const icon = TYPE_ICONS[item.type] || "📄";
  const date = formatDate(item.created_at);

  return (
    <div className="flex items-start gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors group">
      <span className="text-xl mt-0.5 shrink-0">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-700 truncate">
            {typeLabel(item.type, item.system)}
          </span>
          <span className="text-xs text-slate-400 shrink-0">{date}</span>
        </div>
        <p className="text-sm text-slate-600 truncate">{item.summary}</p>
        {item.subtitle && (
          <p className="text-xs text-slate-400 truncate">{item.subtitle}</p>
        )}
      </div>
      <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={() => onViewDetail(item)}
          className="text-xs px-2 py-1 rounded text-indigo-600 hover:bg-indigo-50"
        >
          查看
        </button>
        <button
          onClick={() => onDelete(item.id)}
          className="text-xs px-2 py-1 rounded text-red-500 hover:bg-red-50"
        >
          删除
        </button>
      </div>
    </div>
  );
}
