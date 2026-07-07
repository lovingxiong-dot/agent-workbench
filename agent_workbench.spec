# -*- mode: python ; coding: utf-8 -*-
# agent_workbench.spec — PyInstaller 打包配置
#
# 用于验证 V6.8.0-alpha Baseline 可以独立打包启动。
# 本配置属于 v6-agent 应用层，不属于 v6-core / v6-service。

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

a = Analysis(
    ['agent_workbench/app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('agent_workbench/config/default.yaml', 'agent_workbench/config'),
    ],
    hiddenimports=[
        'yaml',
        'v6.runtime',
        'v6.runtime.engines',
        'agent_workbench.engines',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AgentWorkbenchV6',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
