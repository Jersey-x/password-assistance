# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['password-assistance.py'],  # 替换为你的文件名
    pathex=[],
    binaries=[],
    datas=[('final_app.ico', '.')], # 确保图标文件在目录下
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
    name='快捷密码助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # macOS应用通常不显示终端
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
    name='快捷密码助手',
)
app = BUNDLE(
    coll,
    name='快捷密码助手.app',
    icon='final_app.icns', # macOS通常使用.icns，但PyInstaller会自动转换部分格式
    bundle_identifier='com.jerseyx.passwordassistant',
    info_plist={
        'NSAppleEventsUsageDescription': '需要按键监听权限以实现自动填充功能',
        'NSAccessibilityUsageDescription': '需要辅助功能权限以模拟按键输入',
    },
)
