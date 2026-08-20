"""用标量偏好间隔演示 DPO 目标的方向与 reference policy 作用。"""

from __future__ import annotations

import math


def softplus(x: float) -> float:
    """数值稳定的 log(1 + exp(x))。"""
    return max(x, 0.0) + math.log1p(math.exp(-abs(x)))


def dpo_loss(policy_margin: float, reference_margin: float, beta: float) -> float:
    # -log sigmoid(beta * (policy_margin - reference_margin))
    return softplus(-beta * (policy_margin - reference_margin))


def dpo_gradient(policy_margin: float, reference_margin: float, beta: float) -> float:
    z = beta * (policy_margin - reference_margin)
    sigmoid_negative_z = 1.0 / (1.0 + math.exp(z))
    return -beta * sigmoid_negative_z


def train() -> None:
    reference_margin = 0.20
    policy_margin = -0.35  # 初始时，策略反而更偏向 rejected 回答。
    beta = 0.8
    learning_rate = 0.6

    print("chosen: 先运行失败测试，再做最小修改并复测")
    print("rejected: 直接重写整个模块，不运行测试")
    print(f"reference margin = {reference_margin:+.3f}")
    print("\nstep policy_margin preference_prob loss gradient")
    print("---- ------------- --------------- ---- --------")
    for step in range(7):
        z = beta * (policy_margin - reference_margin)
        preference_probability = 1.0 / (1.0 + math.exp(-z))
        loss = dpo_loss(policy_margin, reference_margin, beta)
        gradient = dpo_gradient(policy_margin, reference_margin, beta)
        print(
            f"{step:>4} {policy_margin:>+13.3f} "
            f"{preference_probability:>15.3f} {loss:>4.3f} {gradient:>+8.3f}"
        )
        policy_margin -= learning_rate * gradient

    print("\n观察：chosen 相对 rejected 的策略间隔逐步增大，损失下降。")
    print("注意：偏好标签只说明两者谁更好，不自动说明答案事实正确。")


if __name__ == "__main__":
    train()
