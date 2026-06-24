/**
 * 轻量 Markdown 渲染器（仅支持 Chat 所需子集）：
 * - **粗体**、*斜体*、`行内代码`、```代码块```
 * - # / ## / ### 标题
 * - - / * / 1. 列表
 * - > 引用
 * - [text](url) 链接
 * - 空行 = 段落分隔
 * - 自动转义 HTML
 *
 * 设计原则：宁可保留换行也不要乱吃结构；未知语法按纯文本显示。
 */
import React from "react";

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** 把已转义字符串按内联规则二次处理为 React 节点 */
function renderInline(raw: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  // 顺序很重要：先 code，再 link，再 bold/italic
  const pattern =
    /(`[^`\n]+`)|(\[([^\]]+)\]\(([^)\s]+)\))|(\*\*([^*]+)\*\*)|(\*([^*]+)\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = pattern.exec(raw)) !== null) {
    if (m.index > last) {
      nodes.push(<span key={`${keyPrefix}-t${i++}`}>{raw.slice(last, m.index)}</span>);
    }
    if (m[1]) {
      // code
      nodes.push(<code key={`${keyPrefix}-c${i++}`}>{m[1].slice(1, -1)}</code>);
    } else if (m[2]) {
      // link
      const text = m[3];
      const url = m[4];
      nodes.push(
        <a
          key={`${keyPrefix}-l${i++}`}
          href={url}
          target="_blank"
          rel="noreferrer noopener"
        >
          {text}
        </a>
      );
    } else if (m[5]) {
      nodes.push(<strong key={`${keyPrefix}-b${i++}`}>{m[6]}</strong>);
    } else if (m[7]) {
      nodes.push(<em key={`${keyPrefix}-i${i++}`}>{m[8]}</em>);
    }
    last = m.index + m[0].length;
  }
  if (last < raw.length) {
    nodes.push(<span key={`${keyPrefix}-t${i++}`}>{raw.slice(last)}</span>);
  }
  return nodes;
}

export function renderMarkdown(src: string): React.ReactNode {
  const text = (src ?? "").replace(/\r\n?/g, "\n");
  const lines = text.split("\n");

  const blocks: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 空行
    if (/^\s*$/.test(line)) {
      i++;
      continue;
    }

    // 代码块 ```
    if (/^```/.test(line)) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) {
        buf.push(lines[i]);
        i++;
      }
      i++; // 跳过结尾 ```
      blocks.push(
        <pre key={`b-${key++}`}>
          <code>{buf.join("\n")}</code>
        </pre>
      );
      continue;
    }

    // 标题
    const h = /^(#{1,3})\s+(.*)$/.exec(line);
    if (h) {
      const level = h[1].length;
      const content = h[2];
      if (level === 1) blocks.push(<h1 key={`b-${key++}`}>{renderInline(escapeHtml(content), `h1-${key}`)}</h1>);
      else if (level === 2) blocks.push(<h2 key={`b-${key++}`}>{renderInline(escapeHtml(content), `h2-${key}`)}</h2>);
      else blocks.push(<h3 key={`b-${key++}`}>{renderInline(escapeHtml(content), `h3-${key}`)}</h3>);
      i++;
      continue;
    }

    // 引用（可连续多行）
    if (/^>\s?/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        buf.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      blocks.push(
        <blockquote key={`b-${key++}`}>
          {renderInline(escapeHtml(buf.join("\n")), `bq-${key}`)}
        </blockquote>
      );
      continue;
    }

    // 无序列表
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ""));
        i++;
      }
      blocks.push(
        <ul key={`b-${key++}`}>
          {items.map((it, idx) => (
            <li key={`li-${key}-${idx}`}>{renderInline(escapeHtml(it), `ul-${key}-${idx}`)}</li>
          ))}
        </ul>
      );
      continue;
    }

    // 有序列表
    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ""));
        i++;
      }
      blocks.push(
        <ol key={`b-${key++}`}>
          {items.map((it, idx) => (
            <li key={`oli-${key}-${idx}`}>{renderInline(escapeHtml(it), `ol-${key}-${idx}`)}</li>
          ))}
        </ol>
      );
      continue;
    }

    // 段落：连续非空行合并
    const buf: string[] = [];
    while (i < lines.length && !/^\s*$/.test(lines[i]) && !/^(#{1,3}\s|>\s?|[-*]\s+|\d+\.\s+|```)/.test(lines[i])) {
      buf.push(lines[i]);
      i++;
    }
    if (buf.length) {
      blocks.push(
        <p key={`b-${key++}`}>
          {renderInline(escapeHtml(buf.join("\n")), `p-${key}`)}
        </p>
      );
    }
  }

  return <div className="prose-chat">{blocks}</div>;
}
