# Workbench v6 Provider Integration Foundation

> **Version**: v6.10.0-alpha
> **Layer**: v6-agent (product layer on top of frozen Runtime Kernel)
> **Status**: Foundation Complete

---

## Architecture Position

```
Workbench v6 Architecture (v6.10-alpha)

v6-agent layer (NEW)
  └── presentation/services/
        ├── provider_registry.py    ← WorkbenchProviderRegistry (v6-agent aggregation)
        ├── provider_validator.py   ← ProviderValidator (static config check)
        └── __init__.py
  └── presentation/adapters/
        └── provider_adapter.py     ← ProviderAdapter (Foundation → UI ViewModel)
  └── presentation/view_models/
        └── provider.py             ← ProviderViewModel / ProviderListViewModel

v6-agent layer (EXISTING, NOT modified)
  └── presentation/protocols/foundation/
        ├── gateway.py              ← ProviderEndpoint (Frozen Foundation Contract)
        ├── data.py
        ├── event.py
        └── runtime.py
  └── ui/workbench/
        └── provider_workspace.py   ← Existing UI (consumes dict)

v6-core layer (FROZEN, NOT touched)
  └── runtime/
        ├── provider_registry.py    ← Runtime ProviderRegistry (Frozen)
        ├── model_module.py         ← ModelModule (Frozen)
        └── ...
```

---

## Boundary Discipline

| Component | Status | Touched? |
|-----------|--------|----------|
| v6-core Runtime Kernel | Frozen | ❌ NO |
| Decision Layer ABI | Frozen | ❌ NO |
| Capability Runtime Contract | Frozen | ❌ NO |
| Event Protocol | Frozen | ❌ NO |
| Foundation Protocol (gateway.py) | Frozen | ❌ NO |
| Foundation ViewModels (existing) | Stable | ❌ NO |
| UI Shell (provider_workspace.py) | Stable | ❌ NO |
| **v6-agent new components** | **NEW** | ✅ YES |

---

## What's New

### 1. ProviderViewModel (`presentation/view_models/provider.py`)

Pure data class for UI rendering:
- `provider_id`, `name`, `protocol`, `status`, `models`, `base_url`, `has_api_key`, `metadata`
- `ProviderListViewModel` for list rendering with `active_provider_id` tracking.

### 2. ProviderAdapter (`presentation/adapters/provider_adapter.py`)

Single translation point from Foundation Protocol `ProviderEndpoint` to UI `ProviderViewModel`:
- `to_view_model(endpoint)` → `ProviderViewModel`
- `to_list_view_model(endpoints, active_provider_id)` → `ProviderListViewModel`
- `_derive_status()`: disabled / needs_config / no_models / active
- `_derive_protocol()`: enum → string

### 3. WorkbenchProviderRegistry (`presentation/services/provider_registry.py`)

v6-agent layer aggregation over Runtime Provider Backend via `RuntimeProviderBackend` Protocol:
- `list_providers()` → list[ProviderInfo]
- `list_provider_names()` → list[str]
- `get_provider_info(provider_id)` → ProviderInfo | None
- `switch_provider(provider_id)` → SwitchResult
- `refresh()` → resync from Runtime

**Key boundary**: Never imports Runtime classes directly. Uses Protocol to decouple.

### 4. ProviderValidator (`presentation/services/provider_validator.py`)

Static config validation (NO network, NO Provider instantiation):
- `EMPTY_PROVIDER_ID` / `MISSING_API_KEY` / `INVALID_BASE_URL` (errors)
- `NO_MODELS` / `PROVIDER_DISABLED` (warnings)
- 4 protocols need API key (openai / anthropic / deepseek / gemini / qwen / kimi / custom)
- echo provider does NOT need API key

---

## Runtime Provider Switching Validation

`WorkbenchProviderRegistry.switch_provider()` validates:
1. ✅ Provider is registered (else SwitchResult.error = "not registered")
2. ✅ Backend accepts the switch (else SwitchResult.error = "refused")
3. ✅ Active state updated on success only
4. ✅ Refresh allows Runtime-side changes to propagate

**UI can configure provider without code modification** (Configuration-Driven Principle P5):
- Add new provider via ConfigStore → ModelModule hot-reloads → WorkbenchProviderRegistry reflects
- No source code change required for new provider registration

---

## Testing

All 34 new tests in `tests/provider/` pass:

```
tests/provider/test_provider_adapter.py    : 10 tests
tests/provider/test_provider_registry.py  : 10 tests
tests/provider/test_provider_validator.py : 14 tests
```

Run: `python -m pytest tests/provider/ -v`

---

## Migration Path for Existing Code

`provider_workspace.py` (UI) currently consumes `dict` config. To migrate:

```python
# Old:
config = {"name": "openai", "type": "openai", "models": [...], ...}
card = ProviderCard(config)

# New (via ProviderAdapter):
endpoint = ProviderEndpoint(provider_id="openai", protocol=ProviderProtocol.OPENAI, ...)
adapter = ProviderAdapter()
vm = adapter.to_view_model(endpoint)
config = {
    "name": vm.name,
    "type": vm.protocol,
    "models": vm.models,
    "base_url": vm.base_url,
    "enabled": vm.metadata.get("enabled") == "True",
    "status": vm.status,
}
card = ProviderCard(config)
```

This migration is **NOT in scope** for v6.10.0-alpha foundation. Existing UI continues to work; new Adapter provides path for future migration.

---

## Future Roadmap

- **v6.10.0-beta**: Migrate provider_workspace.py to consume ProviderViewModel directly.
- **v6.10.0-beta.1**: Wire WorkbenchProviderRegistry into Controller layer.
- **v6.11.0**: Add Provider health check (active ping) in Validator (currently static only).

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-23 | Initial Provider Integration Foundation. 5 new files in v6-agent layer. 34 new tests. No modification to frozen Runtime / Protocol / UI Shell. |