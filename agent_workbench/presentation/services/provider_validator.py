"""presentation/services/provider_validator.py — Provider 配置验证器。

v6.10.0-alpha Provider Integration Foundation。

设计原则：
  ✓ 静态验证 Provider 配置（不发起网络请求）
  ✓ 独立于 Runtime（可在 UI 客户端校验后再下发到 Runtime）
  ✓ 不修改 Foundation Protocol（接受 ProviderEndpoint 输入）

边界：
  - 仅检查配置完整性
  - 不调用任何 Provider 实现（避免网络依赖 / API key 泄露）
  - 不发起任何 Runtime 修改
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from agent_workbench.presentation.protocols.foundation.gateway import (
    ProviderEndpoint,
    ProviderProtocol,
)


@dataclass
class ValidationIssue:
    """单条验证问题。"""

    code: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __post_init__(self) -> None:
        if self.severity not in {"error", "warning"}:
            self.severity = "error"


@dataclass
class ValidationResult:
    """Provider 配置验证结果。"""

    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.issues is None:
            self.issues = []

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def add_error(self, code: str, message: str) -> None:
        self.issues.append(ValidationIssue(code=code, message=message, severity="error"))
        self.valid = False

    def add_warning(self, code: str, message: str) -> None:
        self.issues.append(ValidationIssue(code=code, message=message, severity="warning"))


class ProviderValidator:
    """Provider 配置验证器。

    验证项（静态，不发起网络请求）：
      - provider_id 非空、唯一
      - protocol 属于 ProviderProtocol 枚举
      - api_key 完整性（除 echo 外）
      - base_url 格式（http/https）
      - models 至少有一个
    """

    _PROTOCOLS_NEED_API_KEY = frozenset({
        ProviderProtocol.OPENAI,
        ProviderProtocol.ANTHROPIC,
        ProviderProtocol.DEEPSEEK,
        ProviderProtocol.GEMINI,
        ProviderProtocol.QWEN,
        ProviderProtocol.KIMI,
        ProviderProtocol.CUSTOM,
    })

    def validate(self, endpoint: ProviderEndpoint) -> ValidationResult:
        """验证单个 ProviderEndpoint 配置。

        Args:
            endpoint: Foundation Protocol ProviderEndpoint。

        Returns:
            ValidationResult 包含 valid 状态与 issues 列表。
        """
        result = ValidationResult(valid=True)

        if not endpoint.provider_id or not endpoint.provider_id.strip():
            result.add_error("EMPTY_PROVIDER_ID", "provider_id 不能为空")

        if not isinstance(endpoint.protocol, ProviderProtocol):
            result.add_error(
                "INVALID_PROTOCOL",
                f"protocol '{endpoint.protocol}' 不在 ProviderProtocol 枚举内",
            )

        if endpoint.protocol in self._PROTOCOLS_NEED_API_KEY and not endpoint.api_key:
            result.add_error(
                "MISSING_API_KEY",
                f"protocol '{endpoint.protocol.value}' 需要 api_key",
            )

        if endpoint.base_url and not (
            endpoint.base_url.startswith("http://")
            or endpoint.base_url.startswith("https://")
        ):
            result.add_error(
                "INVALID_BASE_URL",
                "base_url 必须以 http:// 或 https:// 开头",
            )

        if not endpoint.models:
            result.add_warning(
                "NO_MODELS",
                "models 列表为空，Provider 可能无法调用",
            )

        if endpoint.enabled is False:
            result.add_warning(
                "PROVIDER_DISABLED",
                "Provider 已禁用，不会被使用",
            )

        return result