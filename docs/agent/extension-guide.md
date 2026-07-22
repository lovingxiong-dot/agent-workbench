# Extension Guide for AI Agents

> **Target reader**: AI Agent adding new capabilities to Workbench OS.
> **Goal**: Know exactly where and how to add new functionality.

---

## Adding a New Provider

1. Create `agent_workbench/services/<name>_provider.py`
2. Implement `ModelProvider` interface
3. Register in `agent_workbench/runtime/provider_registry.py`
4. Model appears in ControlBar dropdown automatically

**Example**: See `agent_workbench/services/deepseek_provider.py`

---

## Adding a New Runtime Module

1. Create `agent_workbench/runtime/modules/<name>_module.py`
2. Extend `BaseRuntimeModule`
3. Implement `metadata()` returning `MetadataDefinition`
4. Register in `ModuleRegistry`

**What you get for free**: Navigator entry, Inspector properties, StatusBar statistics — all auto-generated from `metadata()`.

**Do NOT create**: `XXXPanel`, `XXXController`, `XXXInspector`, `XXXNavigator` — these are anti-patterns.

---

## Adding a New Workspace Type

1. Create `agent_workbench/ui/workbench/<name>_workspace.py`
2. Extend `BaseWorkspace`
3. Register in `WorkspaceRegistry`

**WorkspaceHost never needs modification** — it auto-discovers registered workspace types.

---

## Adding a New Agent Package

1. Create `packages/<agent_name>/`
2. Add `manifest.yaml` with `name`, `description`, `system_prompt`, `provider`, `skills`
3. Agent appears in ControlBar dropdown automatically

**Example**: See `packages/coding_agent/manifest.yaml`

---

## Adding a New Tool

1. Implement tool function
2. Register in `agent_workbench/runtime/modules/tool_module.py`
3. Tool appears in Navigator → Tools section automatically

---

## Adding a New Skill

1. Implement skill logic
2. Register in `agent_workbench/runtime/modules/skill_module.py`
3. Skill appears in Navigator → Skills section automatically

---

## Adding a New Workflow

1. Define workflow steps
2. Register in `agent_workbench/runtime/modules/workflow_module.py`
3. Workflow appears in Navigator → Workflows section automatically

---

## Key Principle

> **Every extension follows the same pattern**: Implement → Register → Auto-discover in UI.

The Workbench never needs new UI code for a new capability type. Navigator, Inspector, StatusBar all render from `metadata()`. This is the No-Code Registration Principle.