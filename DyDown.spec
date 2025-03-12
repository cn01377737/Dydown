# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('PyQt6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['dydown/main.py'],
    pathex=[],
    hookspath=['hooks'],  # 新增hook路径
    hiddenimports=['wmi', 'pywin32'],  # 显式声明隐藏导入
    binaries=binaries,
    datas=datas,
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    added_files = [
        (os.path.join(pyqt6_plugins_dir, 'platforms'), os.path.join('plugins', 'platforms')),
    ]
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DyDown',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['dydown\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DyDown',
)
