# Contribution Rules for AI Agents

> **Target reader**: AI Agent about to modify code.
> **Goal**: Know what checks to run before, during, and after changes.

---

## Before Any Change

1. Check `.agent-entry.json` → `architecture_boundaries` — is your target in `frozen` or `allowed_changes`?
2. If `frozen` → STOP. Request architecture review.
3. If `requires_review` → Proceed with caution. Document your reasoning.
4. If `allowed_changes` → Proceed.

---

## During Development

### Forbidden Patterns

- ❌ UI directly calls Capability / Provider / Service
- ❌ LLM directly selects Tool (Interpreter rejects tool/function calling)
- ❌ Decision Layer imports Capability / Planner / Service / Orchestrator
- ❌ Any entry point bypasses `RuntimeDecision` to manipulate `Task` internals
- ❌ Module directly imports another Module
- ❌ Metadata contains UI concepts (layout, width, editor type)
- ❌ UI saves business state (`self.selected_model = "gpt-4o"`)

### Required Patterns

- ✅ UI → RuntimeRequest → Decision Layer → RuntimeDecision → Orchestrator
- ✅ Module communication via EventBus / Interface / Registry
- ✅ Metadata is platform-agnostic (Qt, Web, CLI compatible)
- ✅ Business state lives in Runtime, UI only holds presentation state

---

## After Changes

### Verification

```bash
# Core Runtime tests
python -m pytest tests/v6/ -q

# UI tests
python -m pytest tests/ui/ -q

# All active tests
python -m pytest tests/v6/ tests/ui/ tests/metadata/ tests/package/ tests/conversation/ tests/interaction/ tests/runtime/ -q
```

### Test Status Baseline

- Core Stability: 456 passed
- Known UI failures: 7 (v6.14 API migration, not your fault)
- If you introduce NEW failures → fix before proceeding

---

## Commit Rules

1. Message format: `type(scope): summary [hint:keyword] (by AI-Model)`
2. Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`
3. Never commit to `main` directly. All changes go through `v6-agent`.
4. Never force push to `main` or `v6-agent`.
5. Never rebase shared branches.

---

## Frozen Zone Verification

If you're unsure whether a file is in a frozen zone, check:

```bash
python scripts/verify_agent_boundary.py <file_path>
```

Or manually cross-reference with `.agent-entry.json` → `architecture_boundaries.frozen`.