# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['agent_workbench\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('v6', 'v6'), ('agent_workbench', 'agent_workbench')],
    hiddenimports=['PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'v6.ui.left_panel', 'v6.ui.input_area', 'v6.ui.header_bar', 'v6.ui.chat_area', 'v6.ui.base', 'v6.ui.chat_scene', 'v6.ui.chat_items', 'v6.ui.right_panel', 'v6.ui.session_group', 'v6.ui.function_page', 'v6.ui.recent_files', 'v6.ui.tab_button', 'v6.ui.apple_menu', 'v6.ui.more_dropdown', 'v6.ui.settings_panel', 'v6.ui.window_frame', 'v6.ui.file_reader_widget', 'v6.ui.browser_widget', 'v6.ui.terminal_widget', 'agent_workbench.ui.workbench.workbench', 'agent_workbench.ui.workbench.status_bar_host', 'agent_workbench.ui.workbench.workbench_host', 'agent_workbench.presentation', 'agent_workbench.presentation.view_models', 'agent_workbench.presentation.view_models.agent', 'agent_workbench.presentation.view_models.conversation', 'agent_workbench.presentation.view_models.capability', 'agent_workbench.presentation.view_models.settings', 'agent_workbench.presentation.view_models.memory', 'agent_workbench.presentation.adapters', 'agent_workbench.presentation.adapters.agent_adapter', 'agent_workbench.presentation.adapters.conversation_adapter', 'agent_workbench.presentation.adapters.capability_adapter', 'agent_workbench.presentation.adapters.memory_adapter'],
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
)
