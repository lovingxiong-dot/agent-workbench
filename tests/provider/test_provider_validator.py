"""tests/provider/test_provider_validator.py — ProviderValidator 测试。

v6.10.0-alpha Provider Integration Foundation。

边界：
  - 静态验证 Provider 配置
  - 不发起网络请求
  - 不调用任何 Provider 实现
"""
from __future__ import annotations

import pytest

from agent_workbench.presentation.protocols.foundation.gateway import (
    ProviderEndpoint,
    ProviderProtocol,
)
from agent_workbench.presentation.services.provider_validator import (
    ProviderValidator,
    ValidationResult,
)


class TestProviderValidatorValid:
    """合法配置测试。"""

    @pytest.fixture
    def validator(self) -> ProviderValidator:
        return ProviderValidator()

    def test_echo_provider_valid(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="echo",
            protocol=ProviderProtocol.ECHO,
            models=["echo-1"],
        )
        result = validator.validate(endpoint)
        assert result.valid is True
        assert result.errors == []

    def test_openai_provider_valid(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            models=["gpt-4", "gpt-3.5-turbo"],
        )
        result = validator.validate(endpoint)
        assert result.valid is True
        assert result.errors == []

    def test_custom_provider_with_http_base_url(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="custom",
            protocol=ProviderProtocol.CUSTOM,
            api_key="key",
            base_url="http://localhost:8080/v1",
        )
        result = validator.validate(endpoint)
        assert result.valid is True


class TestProviderValidatorErrors:
    """错误配置测试。"""

    @pytest.fixture
    def validator(self) -> ProviderValidator:
        return ProviderValidator()

    def test_empty_provider_id(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="",
            protocol=ProviderProtocol.OPENAI,
        )
        result = validator.validate(endpoint)
        assert result.valid is False
        assert any(i.code == "EMPTY_PROVIDER_ID" for i in result.errors)

    def test_whitespace_provider_id(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="   ",
            protocol=ProviderProtocol.OPENAI,
        )
        result = validator.validate(endpoint)
        assert result.valid is False
        assert any(i.code == "EMPTY_PROVIDER_ID" for i in result.errors)

    def test_missing_api_key_openai(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="",
            models=["gpt-4"],
        )
        result = validator.validate(endpoint)
        assert result.valid is False
        assert any(i.code == "MISSING_API_KEY" for i in result.errors)

    def test_missing_api_key_deepseek(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="deepseek",
            protocol=ProviderProtocol.DEEPSEEK,
            api_key="",
        )
        result = validator.validate(endpoint)
        assert result.valid is False
        assert any(i.code == "MISSING_API_KEY" for i in result.errors)

    def test_invalid_base_url(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="custom",
            protocol=ProviderProtocol.CUSTOM,
            api_key="key",
            base_url="ftp://invalid",
        )
        result = validator.validate(endpoint)
        assert result.valid is False
        assert any(i.code == "INVALID_BASE_URL" for i in result.errors)


class TestProviderValidatorWarnings:
    """警告测试。"""

    @pytest.fixture
    def validator(self) -> ProviderValidator:
        return ProviderValidator()

    def test_no_models_warning(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="echo",
            protocol=ProviderProtocol.ECHO,
            models=[],
        )
        result = validator.validate(endpoint)
        assert result.valid is True
        assert any(i.code == "NO_MODELS" for i in result.warnings)

    def test_disabled_warning(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="echo",
            protocol=ProviderProtocol.ECHO,
            models=["m"],
            enabled=False,
        )
        result = validator.validate(endpoint)
        assert result.valid is True
        assert any(i.code == "PROVIDER_DISABLED" for i in result.warnings)

    def test_multiple_issues(self, validator: ProviderValidator) -> None:
        endpoint = ProviderEndpoint(
            provider_id="openai",
            protocol=ProviderProtocol.OPENAI,
            api_key="",
            base_url="ftp://bad",
            models=[],
            enabled=False,
        )
        result = validator.validate(endpoint)
        assert result.valid is False
        error_codes = {i.code for i in result.errors}
        warning_codes = {i.code for i in result.warnings}
        assert "MISSING_API_KEY" in error_codes
        assert "INVALID_BASE_URL" in error_codes
        assert "NO_MODELS" in warning_codes
        assert "PROVIDER_DISABLED" in warning_codes


class TestValidationResult:
    """ValidationResult 数据类测试。"""

    def test_default_valid(self) -> None:
        result = ValidationResult(valid=True)
        assert result.errors == []
        assert result.warnings == []

    def test_add_error_invalidates(self) -> None:
        result = ValidationResult(valid=True)
        result.add_error("X", "msg")
        assert result.valid is False

    def test_severity_filtering(self) -> None:
        result = ValidationResult(valid=True)
        result.add_warning("W", "warn")
        result.add_error("E", "err")
        assert len(result.errors) == 1
        assert len(result.warnings) == 1