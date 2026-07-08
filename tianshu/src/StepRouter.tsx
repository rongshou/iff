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
import Step2BaziZiwei from "./Step2BaziZiwei";
import Step3MBTI from "./Step3MBTI";
import Step4Holland from "./Step4Holland";
import Step5Report from "./Step5Report";

export default function StepRouter() {
  const { state } = useTianshu();

  switch (state.step) {
    case 1:
      return <Step1BasicInfo />;
    case 2:
      return <Step2BaziZiwei />;
    case 3:
      return <Step3MBTI />;
    case 4:
      return <Step4Holland />;
    case 5:
      return <Step5Report />;
    default:
      return null;
  }
}