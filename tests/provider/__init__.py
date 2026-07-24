"""tests/provider/__init__.py — v6.10.0-alpha Provider 测试包。

测试范围：
  - ProviderAdapter (Foundation Protocol → UI ViewModel)
  - WorkbenchProviderRegistry (v6-agent 层聚合)
  - ProviderValidator (静态配置验证)

边界：
  - 不修改 Runtime Kernel
  - 不修改 Foundation Protocol
  - 使用 Mock RuntimeBackend 验证 v6-agent 层逻辑
"""