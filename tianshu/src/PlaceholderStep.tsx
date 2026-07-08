/**
 * StepPlaceholder - 占位组件（sub-3.1）
 *
 * 后续 sub-step (3.2~3.6) 会替换为真正的表单/报告组件。
 */

interface StepPlaceholderProps {
  step: 1 | 2 | 3 | 4 | 5;
  title: string;
  emoji: string;
  description: string;
}

export default function StepPlaceholder({ step, title, emoji, description }: StepPlaceholderProps) {
  return (
    <div className="step-card-placeholder">
      <div className="step-header">
        <span className="step-num">{step}/5</span>
        <h2>
          {emoji} {title}
        </h2>
      </div>
      <div className="step-body">
        <p className="step-description">{description}</p>
        <div className="migration-badge">
          <span>🚧 迁移中</span>
          <small>sub-3.{step} 即将上线 · 当前请访问旧测评</small>
        </div>
      </div>
      <div className="step-actions">
        <a href="/tianshu/legacy/" className="btn-secondary">
          ← 访问旧版测评
        </a>
      </div>
    </div>
  );
}