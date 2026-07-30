# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pdf_unlocker.py'],
    pathex=[],
    binaries=[],
    datas=[],
    # pypdf 的 AES 後端。pypdf/_crypt_providers/__init__.py 是 try/except 鏈
    # （cryptography → pycryptodome → fallback），實測本機解析到的是 cryptography 49.0.0。
    # 那些 import 雖在 try 區塊內、PyInstaller 通常追得到，但這裡明確列出比較保險——
    # 漏掉的症狀是「開發時能解、打包後的 exe 一遇到 AES 加密的 PDF 就炸」。
    # （原本是 ['Crypto']，那是 PyPDF2 走 pycryptodome 時代的設定。）
    hiddenimports=[
        'pypdf._crypt_providers._cryptography',
        'cryptography.hazmat.primitives.ciphers.algorithms',
        'cryptography.hazmat.primitives.ciphers.base',
        'cryptography.hazmat.primitives.ciphers.modes',
        'cryptography.hazmat.primitives.padding',
    ],
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
    name='PDFUnlocker',
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
    version='version.txt',
)
