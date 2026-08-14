# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pdf_unlocker.py'],
    pathex=[],
    binaries=[],
    datas=[],
    # pypdf 的 AES 後端。pypdf/_crypt_providers/__init__.py 是 try/except 鏈
    # （cryptography → pycryptodome → fallback）。
    #
    # 這五行今天是「保險」而不是「必要」——2026-08-13 實測 PyInstaller 6.21.0 + pypdf 6.14.2：
    # 把 hiddenimports 清空後重新打包，AES-128 / AES-256 一樣解得開，兩顆 exe 只差 118 bytes，
    # 靜態分析自己追到了 try 區塊裡的 import。所以留著的理由是防未來（pypdf 改成更動態的
    # 載入方式、或 PyInstaller 收緊分析），不是防現在。
    #
    # 要驗證的話別靠讀這段註解：CI 每次都會打包後跑 `PDFUnlocker.exe --self-test`，
    # 四種演算法真的解一遍。漏掉後端的症狀是「開發時能解、打包後的 exe 一遇到 AES 就炸」，
    # 那個 job 抓的是這個症狀本身，不管成因是不是 hiddenimports。
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
