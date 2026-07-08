"""agent_workbench/runtime/capability/graph.py — Capability Tree 实现。

设计约束：
- v6.9.3 只实现 Tree（parent_id + children + lineage），不引入 DAG / 图搜索 / 权重传播。
- CapabilityRegistry 由 AgentWorkbenchRuntime 单例持有并注入 Manager 与 Router。
- 所有节点通过 id 索引；父子关系在 register 时自动维护。
"""
from __future__ import annotations

from agent_workbench.runtime.capability.model import CapabilityDefinition, CapabilityIntent, CapabilityMatch


class CapabilityNode:
    """能力树节点。

    - definition: 节点能力定义。
    - parent: 父节点引用。
    - children: 子节点列表。
    """

    def __init__(self, definition: CapabilityDefinition) -> None:
        self.definition = definition
        self.parent: CapabilityNode | None = None
        self.children: list[CapabilityNode] = []


class CapabilityRegistry:
    """能力注册表：管理 Capability Tree。

    核心方法：
    - register / get: 注册与获取能力定义。
    - children / lineage / roots: 树结构查询。
    - load_defaults: 加载默认能力树。
    - find / resolve: Intent 匹配（最后实现，涉及策略）。
    """

    def __init__(self) -> None:
        self._nodes: dict[str, CapabilityNode] = {}

    def register(self, definition: CapabilityDefinition) -> None:
        """注册能力定义，并自动维护父子关系。"""
        node = CapabilityNode(definition)
        self._nodes[definition.id] = node

        parent_id = definition.parent_id
        if parent_id is not None and parent_id in self._nodes:
            parent_node = self._nodes[parent_id]
            node.parent = parent_node
            if node not in parent_node.children:
                parent_node.children.append(node)

        # 如果已有子节点声明该节点为父节点，补全链接。
        for existing in self._nodes.values():
            if existing.definition.parent_id == definition.id and existing is not node:
                existing.parent = node
                if existing not in node.children:
                    node.children.append(existing)

    def get(self, capability_id: str) -> CapabilityDefinition | None:
        """按 id 获取能力定义。"""
        node = self._nodes.get(capability_id)
        return node.definition if node is not None else None

    def lineage(self, capability_id: str) -> list[str]:
        """返回从根节点到该节点的路径 id 列表（含自身）。"""
        node = self._nodes.get(capability_id)
        if node is None:
            return []

        path: list[str] = []
        current: CapabilityNode | None = node
        while current is not None:
            path.append(current.definition.id)
            current = current.parent
        path.reverse()
        return path

    def children(self, capability_id: str) -> list[CapabilityDefinition]:
        """返回指定节点的直接子能力定义列表。"""
        node = self._nodes.get(capability_id)
        if node is None:
            return []
        return [child.definition for child in node.children]

    def roots(self) -> list[CapabilityDefinition]:
        """返回所有根能力定义（parent_id 为 None）。"""
        return [
            node.definition
            for node in self._nodes.values()
            if node.definition.parent_id is None
        ]

    def leaves(self, capability_id: str) -> list[CapabilityDefinition]:
        """返回以 capability_id 为根的子树中所有叶子节点定义（保持注册顺序）。"""
        node = self._nodes.get(capability_id)
        if node is None:
            return []

        result: list[CapabilityDefinition] = []

        def _collect(current: CapabilityNode) -> None:
            if not current.children:
                result.append(current.definition)
                return
            for child in current.children:
                _collect(child)

        _collect(node)
        return result

    def find(self, intent: CapabilityIntent) -> list[CapabilityMatch]:
        """根据 CapabilityIntent 查找匹配的能力。

        匹配策略（第一版规则）：
        - 按关键词在 intent.text 中的命中次数计算分数。
        - 若 intent.required_permissions 非空，排除缺少任一必需权限的能力。
        - 若 intent.preferred_providers 非空，排除不包含任一偏好 Provider 的能力。
        - 返回按分数降序排列的 CapabilityMatch 列表。
        """
        text = (intent.text or "").lower()
        required_permissions = set(intent.required_permissions or [])
        preferred_providers = set(intent.preferred_providers or [])

        matches: list[CapabilityMatch] = []
        for node in self._nodes.values():
            definition = node.definition

            if required_permissions and not required_permissions.issubset(definition.permissions):
                continue

            if preferred_providers and not preferred_providers.intersection(definition.providers):
                continue

            score = self._score_definition(definition, text)
            if score > 0:
                matches.append(
                    CapabilityMatch(
                        definition=definition,
                        score=score,
                        lineage=self.lineage(definition.id),
                    )
                )

        matches.sort(key=lambda match: match.score, reverse=True)
        return matches

    def _score_definition(self, definition: CapabilityDefinition, text: str) -> float:
        """基于关键词命中计算匹配分数。"""
        if not text:
            return 0.0
        keywords = [keyword.lower() for keyword in definition.keywords]
        if not keywords:
            return 0.0
        hits = sum(1 for keyword in keywords if keyword in text)
        return hits / len(keywords)

    def resolve(self, intent: CapabilityIntent) -> CapabilityMatch:
        """解析最佳 CapabilityMatch；无命中时回退到 chat 能力。"""
        matches = self.find(intent)
        if matches:
            return matches[0]

        chat_definition = self.get("chat")
        if chat_definition is not None:
            return CapabilityMatch(
                definition=chat_definition,
                score=0.0,
                lineage=self.lineage("chat"),
            )

        # 如果连默认 chat 都没有（异常状态），返回 assistant 根节点。
        assistant_definition = self.get("assistant")
        if assistant_definition is not None:
            return CapabilityMatch(
                definition=assistant_definition,
                score=0.0,
                lineage=self.lineage("assistant"),
            )

        raise RuntimeError("CapabilityRegistry has no fallback capability.")

    def load_defaults(self) -> None:
        """加载 v6.9.3-alpha 默认能力树。

        默认树：
        assistant
          ├── chat (text_generation)
          ├── analyze (text_generation)
          ├── tool (tool_execution)
          └── coding
                ├── python
                │     ├── analysis (code_generation)
                │     ├── debugging (code_generation)
                │     └── testing (code_generation)
                └── code_editor (code_generation)
        """
        definitions = [
            CapabilityDefinition(
                id="assistant",
                name="Assistant",
                description="Root assistant capability.",
            ),
            CapabilityDefinition(
                id="chat",
                name="Chat",
                description="General chat capability.",
                parent_id="assistant",
                keywords=["chat", "talk", "ask"],
                engine_capability="text_generation",
            ),
            CapabilityDefinition(
                id="analyze",
                name="Analyze",
                description="Analyze a project or code.",
                parent_id="assistant",
                keywords=["analyze", "analysis", "review"],
                engine_capability="text_generation",
            ),
            CapabilityDefinition(
                id="tool",
                name="Tool",
                description="Execute a tool.",
                parent_id="assistant",
                keywords=["tool", "execute"],
                engine_capability="tool_execution",
            ),
            CapabilityDefinition(
                id="coding",
                name="Coding",
                description="Software development tasks.",
                parent_id="assistant",
                keywords=["code", "coding", "program"],
            ),
            CapabilityDefinition(
                id="coding.python",
                name="Python",
                description="Python development.",
                parent_id="coding",
                keywords=["python", "py"],
            ),
            CapabilityDefinition(
                id="coding.python.analysis",
                name="Python Analysis",
                description="Analyze Python code or project.",
                parent_id="coding.python",
                keywords=["analyze", "analysis", "review", "project"],
                engine_capability="code_generation",
            ),
            CapabilityDefinition(
                id="coding.python.debugging",
                name="Python Debugging",
                description="Debug Python code.",
                parent_id="coding.python",
                keywords=["debug", "fix", "bug"],
                engine_capability="code_generation",
            ),
            CapabilityDefinition(
                id="coding.python.testing",
                name="Python Testing",
                description="Write or run Python tests.",
                parent_id="coding.python",
                keywords=["test", "pytest", "unittest"],
                engine_capability="code_generation",
            ),
            CapabilityDefinition(
                id="coding.code_editor",
                name="Code Editor",
                description="Edit code files.",
                parent_id="coding",
                keywords=["edit", "refactor"],
                engine_capability="code_generation",
            ),
            CapabilityDefinition(
                id="image_generation",
                name="Image Generation",
                description="Generate images from text prompts.",
                parent_id="assistant",
                keywords=["image", "picture", "photo", "generate image"],
                engine_capability="image_generation",
            ),
        ]
        for definition in definitions:
            self.register(definition)
