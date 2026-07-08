/**
 * StepRouter - 根据当前 state.step 渲染对应组件
 *
 * sub-3.1：所有 step 都是占位
 * sub-3.2~3.5：逐步替换占位
 * sub-3.6：替换为完整报告
 */

import { useTianshu } from "./TianshuContext";
import StepPlaceholder from "./PlaceholderStep";
import Step1BasicInfo from "./Step1BasicInfo";

export default function StepRouter() {
  const { state } = useTianshu();

  switch (state.step) {
    case 1:
      return <Step1BasicInfo />;
    case 2:
      return (
        <StepPlaceholder
          step={2}
          title="八字排盘"
          emoji="🌙"
          description="基于出生时间生成四柱八字 + 五行 + 喜用神（sub-3.3 即将上线）"
        />
      );
    case 3:
      return (
        <StepPlaceholder
          step={3}
          title="MBTI 测评"
          emoji="🧠"
          description="16 型人格测试，可选已知或现场测评（sub-3.4 即将上线）"
        />
      );
    case 4:
      return (
        <StepPlaceholder
          step={4}
          title="霍兰德测评"
          emoji="🎯"
          description="RIASEC 六维职业兴趣测评（sub-3.5 即将上线）"
        />
      );
    case 5:
      return (
        <StepPlaceholder
          step={5}
          title="综合测评报告"
          emoji="📊"
          description="八字 + 紫微 + MBTI + 霍兰德四维交叉验证 + 生涯路径（sub-3.6 即将上线）"
        />
      );
    default:
      return null;
  }
}