# -*- mode: python ; coding: utf-8 -*-
import toml

# Tell the linter these are defined by PyInstaller
Analysis: object
PYZ: object
EXE: object
BUNDLE: object
COLLECT: object

block_cipher = None

# Read version from pyproject.toml
config = toml.load("pyproject.toml")
version = config["tool"]["poetry"]["version"]

a = Analysis(
    ["app.pyw"],
    pathex=[],
    binaries=[
        # (".venv\Lib\site-packages\pyzbar\libiconv.dll", "."),
        # (".venv\Lib\site-packages\pyzbar\libzbar-64.dll", "."),
        ("/opt/homebrew/bin/tesseract", "tesseract")
    ],
    datas=[
        ("./assets/icon.ico", "./assets/"),
        ("./assets/icon.png", "./assets/"),
        ("./assets/icon.icns", "./assets/"),
        ("README.md", "./"),
        ("pyproject.toml", "./"),
        ("/opt/homebrew/share/tessdata", "tessdata"),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name="ClipBarcode",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    windowed=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="./assets/icon.ico",
)

coll = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ClipBarcode.app",
    icon="./assets/icon.icns",
    bundle_identifier="com.clipbarcode.app",
    version=version,
    info_plist={
        "CFBundleDisplayName": "ClipBarcode",  # A user-friendly name for the Finder/Dock
        "CFBundleName": "ClipBarcode",  # Short name for the app
        "CFBundleVersion": version,  # Full version number
        "CFBundleShortVersionString": version,  # User-visible version
        "LSApplicationCategoryType": "public.app-category.productivity",  # App category
        "NSHighResolutionCapable": True,  # Support for Retina displays
        "NSAppleScriptEnabled": True,
        "NSClipboardUsageDescription": "This app needs clipboard access to read barcodes.",
    },
)
