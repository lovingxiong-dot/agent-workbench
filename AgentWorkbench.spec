# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Agent Workbench V6 v6.10.0-alpha
#
# Path:
#   spec file:  AgentWorkbench.spec (project root)
#   entry:      agent_workbench/app.py
#   icon:       agent_workbench/resources/app_icon.ico
#   bundle:     dist/AgentWorkbench/ (onedir) + dist/AgentWorkbench.exe (onefile)

import os

PROJECT_ROOT = os.path.abspath(SPECPATH)

a = Analysis(
    [os.path.join('agent_workbench', 'app.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        ('v6', 'v6'),
        ('agent_workbench', 'agent_workbench'),
        ('agent_workbench/resources/app_icon.ico', 'agent_workbench/resources'),
        ('agent_workbench/resources/app_icon.png', 'agent_workbench/resources'),
    ],
    hiddenimports=[
        # PySide6 core
        'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        # v6 UI modules
        'v6.ui.left_panel', 'v6.ui.input_area', 'v6.ui.header_bar',
        'v6.ui.chat_area', 'v6.ui.base', 'v6.ui.chat_scene', 'v6.ui.chat_items',
        'v6.ui.right_panel', 'v6.ui.session_group', 'v6.ui.function_page',
        'v6.ui.recent_files', 'v6.ui.tab_button', 'v6.ui.apple_menu',
        'v6.ui.more_dropdown', 'v6.ui.settings_panel', 'v6.ui.window_frame',
        'v6.ui.file_reader_widget', 'v6.ui.browser_widget', 'v6.ui.terminal_widget',
        # Workbench legacy UI
        'agent_workbench.ui.workbench.workbench',
        'agent_workbench.ui.workbench.status_bar_host',
        'agent_workbench.ui.workbench.workbench_host',
        # Presentation layer
        'agent_workbench.presentation',
        'agent_workbench.presentation.view_models',
        'agent_workbench.presentation.view_models.agent',
        'agent_workbench.presentation.view_models.conversation',
        'agent_workbench.presentation.view_models.capability',
        'agent_workbench.presentation.view_models.settings',
        'agent_workbench.presentation.view_models.memory',
        'agent_workbench.presentation.view_models.provider',
        'agent_workbench.presentation.view_models.tool',
        'agent_workbench.presentation.view_models.skill',
        'agent_workbench.presentation.view_models.agent_profile',
        'agent_workbench.presentation.adapters',
        'agent_workbench.presentation.adapters.agent_adapter',
        'agent_workbench.presentation.adapters.conversation_adapter',
        'agent_workbench.presentation.adapters.capability_adapter',
        'agent_workbench.presentation.adapters.memory_adapter',
        'agent_workbench.presentation.adapters.provider_adapter',
        'agent_workbench.presentation.adapters.tool_adapter',
        'agent_workbench.presentation.adapters.skill_adapter',
        # v6.10 Presentation Services
        'agent_workbench.presentation.services',
        'agent_workbench.presentation.services.config_loader',
        'agent_workbench.presentation.services.provider_registry',
        'agent_workbench.presentation.services.provider_service',
        'agent_workbench.presentation.services.provider_validator',
        'agent_workbench.presentation.services.tool_service',
        'agent_workbench.presentation.services.skill_service',
        'agent_workbench.presentation.services.agent_profile_service',
        'agent_workbench.presentation.services.product_shell',
        'agent_workbench.presentation.services.model_module_backend',
        'agent_workbench.presentation.services.tool_module_backend',
        'agent_workbench.presentation.services.capability_lookup_backend',
        # Presentation Protocols (Foundation)
        'agent_workbench.presentation.protocols',
        'agent_workbench.presentation.protocols.foundation',
        'agent_workbench.presentation.protocols.foundation.data',
        'agent_workbench.presentation.protocols.foundation.event',
        'agent_workbench.presentation.protocols.foundation.gateway',
        'agent_workbench.presentation.protocols.foundation.runtime',
        # Providers
        'agent_workbench.services.openai_provider',
        'agent_workbench.services.claude_provider',
        'agent_workbench.services.gemini_provider',
        'agent_workbench.services.deepseek_provider',
        'agent_workbench.services.qwen_provider',
        'agent_workbench.services.kimi_provider',
        'agent_workbench.services.echo_provider',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AgentWorkbench',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('agent_workbench', 'resources', 'app_icon.ico'),
)