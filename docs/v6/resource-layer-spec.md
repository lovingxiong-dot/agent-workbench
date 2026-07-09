# Resource Layer Specification

> **Status**: Design proposal for v6.12.x+ (post Metadata-driven Workbench).  
> **Scope**: Define how Workbench models external execution targets as first-class configuration objects, separate from Capability and Provider.

---

## Core Principle

> **System environments, virtual environments, IDEs, CLIs, and Agent CLIs are not Capabilities. They are Resources (execution targets).**

A Capability answers:

> **What can the Agent do?**
> — Coding, Browsing, Analyzing, Image understanding, etc.

A Resource answers:

> **Where and with what tools can the Agent do it?**
> — On Windows, inside a Python venv, via VS Code, using `git`, calling `codex`, etc.

A Provider answers:

> **Which model performs the reasoning?**
> — OpenAI, Claude, Gemini, Kimi, DeepSeek, local Ollama, etc.

Separating these three concerns prevents the Capability layer from becoming a grab-bag of unrelated integration points and keeps the architecture composable.

---

## Five Resource Layers

```text
Workbench
    │
    ├── Digital Identity（AI）
    │
    ├── Capability（我会什么）
    │      ├── Coding
    │      ├── Browser
    │      ├── Analyze
    │      └── ...
    │
    ├── Runtime（调度）
    │
    ├── Resource（我可以使用什么）
    │      ├── System
    │      ├── PythonEnv
    │      ├── IDE
    │      ├── CLI
    │      ├── AgentCLI
    │      ├── MCP
    │      ├── FileSystem
    │      └── Browser
    │
    ├── Provider（调用哪个模型）
    │
    └── Target（在哪个环境执行）
```

### Layer 1: System

Describes an operating environment where commands may be executed.

```yaml
system:
  - id: windows-local
    type: windows
    name: Local Windows
    root: C:\
    shell: powershell
    default: true

  - id: wsl-ubuntu
    type: wsl
    name: WSL Ubuntu
    root: /home/user
    shell: bash
    host: localhost

  - id: docker-dev
    type: docker
    name: Dev Container
    image: python:3.12
    shell: bash

  - id: remote-lab
    type: ssh
    name: Remote Lab
    host: 192.168.1.100
    user: lab
    shell: bash
```

### Layer 2: Python Environment

Independent Python interpreters / virtual environments. Not managed by the IDE.

```yaml
python_env:
  - id: workbench
    name: Workbench venv
    python: D:\Python\.venv\workbench\python.exe
    pip: D:\Python\.venv\workbench\Scripts\pip.exe
    version: "3.12"

  - id: quant
    name: Quant venv
    python: D:\Python\.venv\quant\python.exe
    pip: D:\Python\.venv\quant\Scripts\pip.exe
    version: "3.11"
```

### Layer 3: IDE

Registered integrated development environments that can be launched or controlled.

```yaml
ide:
  - id: cursor
    name: Cursor
    exe: C:\Users\xxx\AppData\Local\Programs\cursor\Cursor.exe
    cli: cursor
    workspace: F:\Agent

  - id: vscode
    name: VS Code
    exe: C:\Users\xxx\AppData\Local\Programs\Microsoft VS Code\Code.exe
    cli: code
    workspace: F:\Agent

  - id: traecode
    name: Trae Code
    exe: C:\Users\xxx\AppData\Local\Programs\Trae\Trae.exe
    cli: traecode
    workspace: F:\Agent
```

### Layer 4: CLI

Standalone command-line tools available to the Agent.

```yaml
cli:
  - id: git
    name: Git
    command: C:\Program Files\Git\bin\git.exe
    version: "2.49"
    args: []

  - id: uv
    name: uv
    command: C:\Users\xxx\.cargo\bin\uv.exe
    version: "0.4.x"

  - id: npm
    name: npm
    command: C:\Program Files\nodejs\npm.cmd
    version: "10.x"
```

### Layer 5: Agent CLI

Other agent runtimes callable as tools. This is expected to become the highest-value Resource category.

```yaml
agent_cli:
  - id: codex
    name: OpenAI Codex CLI
    command: codex
    supports:
      - chat
      - edit
      - run
      - diff

  - id: claude-code
    name: Claude Code
    command: claude
    supports:
      - chat
      - edit
      - run

  - id: aider
    name: Aider
    command: aider
    supports:
      - edit
      - diff
```

---

## Navigator Layout

```text
Resources
│
├── System
│   ├── windows-local
│   ├── wsl-ubuntu
│   └── remote-lab
│
├── Python Env
│   ├── workbench
│   └── quant
│
├── IDE
│   ├── Cursor
│   ├── VS Code
│   └── Trae Code
│
├── CLI
│   ├── git
│   ├── uv
│   └── npm
│
├── Agent CLI
│   ├── codex
│   ├── claude-code
│   └── aider
│
├── MCP
├── Browser
├── FileSystem
└── Network
```

All entries support `+` / `Edit` / `Delete` and are driven by Config + Metadata. No code changes are required to register a new Resource instance.

---

## Execution Flow Example

```text
Digital Identity (Manager AI)
        │
        ▼
Capability: Coding
        │
        ▼
Resource: Agent CLI / codex
        │
        ▼
Provider: claude-3-7-sonnet
        │
        ▼
Target: windows-local
        │
        ▼
Execute via codex CLI on local Windows
```

This composition allows the same Capability to be executed by different Resources, on different Targets, using different Providers, without any hard-coded integration logic.

---

## Relationship to Metadata / Schema

Each Resource type must provide:

1. **Metadata** — `id`, `type`, `name`, `icon`, `properties`, `statistics`, `actions`.
2. **Schema** — how to configure instances of this Resource type.
3. **Runtime Binding** — a small adapter that knows how to invoke the Resource (e.g., start Cursor, run `codex`, execute PowerShell on `windows-local`).

The UI for adding a Resource is generated from Schema. The Navigator groups Resources by `type`. The Runtime selects Resources by `id`.

---

## Non-Goals (for v6.12.x)

- Remote agent orchestration (Gateway) — future.
- Resource marketplace / plugin store — Plugin-driven stage.
- Automatic Resource discovery — may be added later, but initial registration is config-driven.
- Real-time resource health monitoring — statistics only, no heartbeat protocol yet.

---

## Open Questions

1. Should `MCP` be a Resource type or a Capability transport?
2. Should `FileSystem` and `Browser` be Resources or built-in Runtime services?
3. Should Resource adapters live in `agent_workbench/resources/` or in Plugin packages?
