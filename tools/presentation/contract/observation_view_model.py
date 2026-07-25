"""tools/presentation/contract/observation_view_model.py — Phase 3.13 ObservationViewModel Frozen Contract.

Phase 3.13 Step 1: Presentation Contract (Schema-First, Frozen).

Frozen fields (10):
- id
- title
- summary
- category
- severity
- timestamp
- source
- metrics
- metadata
- schema_version

Strict NOT in scope (Phase 3.13):
- ❌ Renderer / Widget / Layout / Panel / Theme / Style / View State
- ❌ Storage / Persistence / Memory / Embedding / Insight / AI Summary
- ❌ EventBus new channel
- ❌ Runtime event changes

Contract boundary (ADR-017):
- platform-agnostic (NOT UI Model)
- No runtime dependency
- No UI dependency
- No event bus
- No storage
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


OBSERVATION_VIEW_MODEL_SCHEMA_VERSION = "presentation.v0.1"


class PresentationCategory(str, Enum):
    """5 类 Presentation Category (mapped from ObservationType).

    ObservationType → PresentationCategory:
    - PERFORMANCE → PERFORMANCE
    - RESOURCE → RESOURCE
    - LIFECYCLE → LIFECYCLE
    - EVENT → EVENT
    - HEALTH → HEALTH
    """

    PERFORMANCE = "performance"
    RESOURCE = "resource"
    LIFECYCLE = "lifecycle"
    EVENT = "event"
    HEALTH = "health"


class PresentationSeverity(str, Enum):
    """4 类 Severity (presentation-level)."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PresentationSource(str, Enum):
    """4 类 Source (mapped from ObservationSource)."""

    HUMAN = "human"
    AGENT = "agent"
    RUNTIME = "runtime"
    SYSTEM = "system"


@dataclass(frozen=True)
class ObservationViewModel:
    """Phase 3.13 Presentation Frozen Contract (platform-agnostic).

    10 fields (Frozen):
    - id (str, required): Unique view model ID
    - title (str, required): Short title (display-ready)
    - summary (str, required): Brief summary (display-ready)
    - category (PresentationCategory, required): Type category
    - severity (PresentationSeverity, required): Severity level
    - timestamp (float, default): Creation timestamp
    - source (PresentationSource, required): Provenance
    - metrics (Dict[str, Any], default): Display-ready metrics
    - metadata (Dict[str, Any], default): Source metadata (raw)
    - schema_version (str, default): Frozen schema version

    关键约束:
    - frozen dataclass (immutable)
    - platform-agnostic (NOT UI Model)
    - serialization friendly (to_dict → JSON)
    - no runtime dependency
    - no UI dependency
    """

    id: str
    title: str
    summary: str
    category: PresentationCategory
    severity: PresentationSeverity
    source: PresentationSource
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = OBSERVATION_VIEW_MODEL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate required fields (Mandatory Contract)."""
        if not self.id:
            raise ValueError("ObservationViewModel.id must be non-empty")
        if not self.title:
            raise ValueError("ObservationViewModel.title must be non-empty (display-ready)")
        if not self.summary:
            raise ValueError("ObservationViewModel.summary must be non-empty (display-ready)")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (JSON-friendly)."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "source": self.source.value,
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
            "schema_version": self.schema_version,
        }
