"""
PathResolver — 工具路径解析辅助

为文件工具提供统一的路径解析逻辑：
- 优先处理绝对路径
- 相对路径基于 project_root 解析
- 展开环境变量
"""
import os


def resolve_path(path: str, project_root: str) -> str:
    """解析工具传入的路径为绝对路径。

    Args:
        path: 用户传入的路径，可能是绝对路径、相对路径或空字符串。
        project_root: 当前项目根目录，作为相对路径的解析基准。

    Returns:
        规范化后的绝对路径。
    """
    if path is None:
        path = ""
    path = os.path.expandvars(str(path).strip())
    if not path:
        return os.path.normpath(project_root or os.getcwd())
    if os.path.isabs(path):
        return os.path.normpath(path)
    base = project_root or os.getcwd()
    return os.path.normpath(os.path.join(base, path))
