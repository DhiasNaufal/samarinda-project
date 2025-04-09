# -*- mode: python ; coding: utf-8 -*-
import pkgutil
from PyInstaller.utils.hooks import collect_all
import rasterio

# list all rasterio and fiona submodules, to include them in the package
additional_packages = list()
for package in pkgutil.iter_modules(rasterio.__path__, prefix="rasterio."):
    additional_packages.append(package.name)

pyogrio_datas, pyogrio_binaries, pyogrio_hiddenimports = collect_all("pyogrio")

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyogrio_binaries,
    datas=pyogrio_datas,
    hiddenimports=additional_packages+pyogrio_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='main',
    debug=True,
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
