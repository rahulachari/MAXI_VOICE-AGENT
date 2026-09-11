# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../run.py'],
    pathex=['..'],
    binaries=[],
    datas=[
        ('../jarvis/ui/assets', 'jarvis/ui/assets'),
    ],
    hiddenimports=[
        'win32gui',
        'win32con',
        'win32api',
        'win32process',
        'pythoncom',
        'comtypes',
        'comtypes.client',
        'pyperclip',
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'edge_tts',
        'pygame',
        'groq',
        'sounddevice',
        'speech_recognition',
        'PySide6.QtWebEngineWidgets',
        'jarvis.tools.folder_registry',
        'jarvis.ui.folder_browser',
        'jarvis.tools.email_reader_tool',
        'jarvis.tools.prompt_gen_tool',
        'jarvis.ui.prompt_card',
        'jarvis.ui.email_list_card',
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
    [],
    exclude_binaries=True,
    name='JARVIS',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JARVIS',
)
