"""agent_workbench/metadata/errors.py — Metadata contract exceptions."""


class MetadataError(Exception):
    """Metadata 契约相关异常的基类。"""

    pass


class MetadataValidationError(MetadataError):
    """Metadata 定义不符合契约时抛出。"""

    pass


class MetadataNotFoundError(MetadataError):
    """Registry 中找不到指定 MetadataDefinition 时抛出。"""

    pass


class MetadataAdapterError(MetadataError):
    """MetadataAdapter 转换失败时抛出。"""

    pass
