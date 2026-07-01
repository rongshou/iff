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
      // link — 只允许 http/https/mailto 协议，防止 javascript: XSS
      const text = m[3];
      const url = m[4];
      const allowed = /^(https?:\/\/|mailto:)/i;
      nodes.push(
        <a
          key={`${keyPrefix}-l${i++}`}
          href={allowed.test(url) ? url : "#"}
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

/** 拆分一行表格为单元格：去掉首尾 | 后按 | 切分并 trim */
function splitTableRow(line: string): string[] {
  let s = line.trim();
  if (s.startsWith("|")) s = s.slice(1);
  if (s.endsWith("|")) s = s.slice(0, -1);
  return s.split("|").map((c) => c.trim());
}

/** 表格分隔行：| --- | :---: | ---: | 形式 */
const TABLE_SEP =
  /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$/;

/** 从分隔行解析每列对齐方式：left | center | right | undefined(默认) */
function parseAligns(sepRow: string): ("left" | "center" | "right" | undefined)[] {
  return splitTableRow(sepRow).map((cell) => {
    const left = cell.startsWith(":");
    const right = cell.endsWith(":");
    if (left && right) return "center";
    if (right) return "right";
    if (left) return "left";
    return undefined;
  });
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

    // 表格：表头行 + 分隔行 + 数据行（至少三行）
    if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && TABLE_SEP.test(lines[i + 1])) {
      const header = splitTableRow(line);
      const aligns = parseAligns(lines[i + 1]);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
        rows.push(splitTableRow(lines[i]));
        i++;
      }
      blocks.push(
        <div key={`b-${key++}`} className="table-wrap">
          <table>
            <thead>
              <tr>
                {header.map((c, idx) => (
                  <th
                    key={`th-${key}-${idx}`}
                    style={aligns[idx] ? { textAlign: aligns[idx] as "left" | "center" | "right" } : undefined}
                  >
                    {renderInline(escapeHtml(c), `th-${key}-${idx}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, ri) => (
                <tr key={`tr-${key}-${ri}`}>
                  {r.map((c, ci) => (
                    <td
                      key={`td-${key}-${ri}-${ci}`}
                      style={aligns[ci] ? { textAlign: aligns[ci] as "left" | "center" | "right" } : undefined}
                    >
                      {renderInline(escapeHtml(c), `td-${key}-${ri}-${ci}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    // 段落：连续非空行合并
    const buf: string[] = [];
    while (i < lines.length && !/^\s*$/.test(lines[i]) && !/^(#{1,3}\s|>\s?|[-*]\s+|\d+\.\s+|```|\|.*\|\s*$)/.test(lines[i])) {
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
