"""presentation/services/__init__.py — Presentation Service 模块。

v6.10.0-alpha Provider Integration Foundation。

本模块承载 v6-agent 层服务：
  - WorkbenchProviderRegistry（Provider 注册中心，委托 Runtime）
  - ProviderValidator（配置验证器）

边界：
  - 不修改 Runtime Kernel
  - 不修改 Foundation Protocol
  - 通过 Protocol 接口委托 Runtime（v6-core 保留 frozen 状态）
"""