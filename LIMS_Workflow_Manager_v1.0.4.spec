# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('file_dialog.py', '.'), ('version.json', '.')],
    hiddenimports=['streamlit'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['/Users/RRMalmstrom/Desktop/lims_workflow_manager/.venv/lib/python3.9/site-packages/streamlit/runtime/scriptrunner/pyi_rth_script_runner.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LIMS_Workflow_Manager_v1.0.4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LIMS_Workflow_Manager_v1.0.4',
)
app = BUNDLE(
    coll,
    name='LIMS_Workflow_Manager_v1.0.4.app',
    icon=None,
    bundle_identifier=None,
)
