/**
 * Step2BaziZiwei - 八字 + 紫微排盘（sub-3.3）
 *
 * 迁移自 legacy/app.js 的 renderStep2() + renderZiwei() + nextStep2()
 * 调用全局 window.TianShuBazi 和 window.TianShuData 计算。
 */

import { useEffect, useState } from "react";
import { useTianshu } from "./TianshuContext";
import { TianShuBazi, TianShuData } from "./types";

interface BaziResult {
  error?: string;
  solar?: string;
  lunar?: string;
  yearZhu?: string;
  monthZhu?: string;
  dayZhu?: string;
  hourZhu?: string;
  dayMaster?: string;
  dayMasterWx?: string;
  wuxingCount?: Record<string, number>;
  xiZhong?: string[];
  jiZhong?: string[];
  personality?: string;
  careerFit?: string;
}

interface ZiweiResult {
  mingGong: { name: string; star: string; trait: string; fit: string; hourEffect?: string };
  shiyeGong: { name: string; star: string; trait: string; fit: string; hourEffect?: string };
  caiboGong: { name: string; star: string; trait: string; fit: string; hourEffect?: string };
  note: string;
}

export default function Step2BaziZiwei() {
  const { state, goNext, goPrev, setState } = useTianshu();
  const [loading, setLoading] = useState(true);
  const [bazi, setBazi] = useState<BaziResult | null>(null);
  const [ziwei, setZiwei] = useState<ZiweiResult | null>(null);

  useEffect(() => {
    // 模拟旧版的 200ms 延迟（让 loading 有显示）
    setLoading(true);
    const timer = setTimeout(() => {
      try {
        const b = TianShuBazi.getFourPillars(
          state.student.birthYear,
          state.student.birthMonth,
          state.student.birthDay,
          state.student.birthHour
        ) as BaziResult;
        if (b.error) {
          setBazi({ error: b.error });
          setLoading(false);
          return;
        }
        const z = TianShuData.getZiweiSummary(
          state.student.birthYear,
          state.student.birthMonth,
          state.student.birthHour
        ) as ZiweiResult;

        setBazi(b);
        setZiwei(z);
        // 保存到 state（供后续 step 使用）
        setState({ _bazi: b, _ziwei: z } as any);
      } catch (e: any) {
        setBazi({ error: e?.message || "排盘失败" });
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, []); // 只跑一次（进入 step 2 时）

  if (loading) {
    return (
      <div className="step-card-placeholder">
        <div className="loading-state">🔮 排盘计算中...</div>
      </div>
    );
  }

  if (bazi?.error) {
    return (
      <div className="step-card-placeholder">
        <div className="step-header">
          <span className="step-num">2/5</span>
          <h2>🔮 八字 + ⭐ 紫微排盘</h2>
        </div>
        <div className="error-state">❌ {bazi.error}</div>
        <div className="step-actions">
          <button onClick={goPrev} className="btn-secondary">← 上一步</button>
        </div>
      </div>
    );
  }

  return (
    <div className="step-card-placeholder">
      <div className="step-header">
        <span className="step-num">2/5</span>
        <h2>🔮 八字 + ⭐ 紫微排盘</h2>
      </div>

      <h3 className="section-title">📋 八字四柱</h3>
      <table className="data-table">
        <thead>
          <tr><th>项目</th><th>结果</th></tr>
        </thead>
        <tbody>
          <tr><td>公历</td><td>{bazi?.solar}</td></tr>
          <tr><td>农历</td><td>{bazi?.lunar}</td></tr>
          <tr><td>年柱</td><td><strong>{bazi?.yearZhu}</strong></td></tr>
          <tr><td>月柱</td><td><strong>{bazi?.monthZhu}</strong></td></tr>
          <tr><td>日柱</td><td><strong>{bazi?.dayZhu}</strong></td></tr>
          <tr><td>时柱</td><td><strong>{bazi?.hourZhu}</strong></td></tr>
          <tr><td>日主</td><td>{bazi?.dayMaster}({bazi?.dayMasterWx})</td></tr>
          <tr><td>五行统计</td><td>
            {bazi?.wuxingCount && Object.entries(bazi.wuxingCount).map(([k, v]) => `${k}:${v}`).join(" · ")}
          </td></tr>
          <tr><td>喜用神</td><td><span className="tag tag-primary">{bazi?.xiZhong?.join(" + ")}</span></td></tr>
          <tr><td>忌神</td><td><span className="tag tag-warning">{bazi?.jiZhong?.join(" + ")}</span></td></tr>
        </tbody>
      </table>

      <div className="info-block">
        <strong>核心性格:</strong>{bazi?.personality}<br />
        <strong>学业事业适配:</strong>{bazi?.careerFit}
      </div>

      <h3 className="section-title">⭐ 紫微简版</h3>
      {ziwei && (
        <>
          <div className="gong-grid">
            <ZiweiGong gong={ziwei.mingGong} />
            <ZiweiGong gong={ziwei.shiyeGong} />
            <ZiweiGong gong={ziwei.caiboGong} />
          </div>
          <p className="note">⚠️ {ziwei.note}</p>
        </>
      )}

      <div className="step-actions">
        <button onClick={goPrev} className="btn-secondary">← 上一步</button>
        <button onClick={goNext} className="btn-primary">下一步 →</button>
      </div>
    </div>
  );
}

function ZiweiGong({ gong }: { gong: { name: string; star: string; trait: string; fit: string; hourEffect?: string } }) {
  return (
    <div className="gong-card">
      <div className="gong-title">
        {gong.name}:<span className="tag tag-primary">{gong.star}</span>
      </div>
      <div><strong>特质:</strong>{gong.trait}</div>
      <div><strong>适配:</strong>{gong.fit}</div>
      {gong.hourEffect && <div className="hour-effect">⏰ {gong.hourEffect}</div>}
    </div>
  );
}