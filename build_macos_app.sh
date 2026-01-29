#!/bin/bash
# ============================================
# macOS 打包腳本 - 將 Python 程式轉為 .app/.pkg
# 請在 Mac 終端機執行此腳本
# ============================================

APP_NAME="BookingSearchTool"
PYTHON_SCRIPT="booking_search.py"
VERSION="1.0.0"

echo "=== macOS 打包工具 ==="
echo "1️⃣ 確認 Python 環境..."

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 Python3，請先安裝"
    exit 1
fi

# 安裝必要套件
echo "2️⃣ 安裝打包工具與相依套件..."
pip3 install pyinstaller playwright pandas openpyxl

# 安裝 Playwright 瀏覽器
echo "3️⃣ 安裝 Playwright 瀏覽器..."
python3 -m playwright install chromium

# 建立 PyInstaller 規格檔
echo "4️⃣ 建立打包設定..."
cat > ${APP_NAME}.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 收集 playwright 資料
playwright_datas = collect_data_files('playwright')
playwright_hiddenimports = collect_submodules('playwright')

a = Analysis(
    ['booking_search.py'],
    pathex=[],
    binaries=[],
    datas=playwright_datas,
    hiddenimports=playwright_hiddenimports + ['pandas', 'openpyxl'],
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
    name='BookingSearchTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='BookingSearchTool.app',
    icon=None,
    bundle_identifier='com.booking.searchtool',
    version='1.0.0',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'BookingSearchTool',
    },
)
EOF

# 使用 PyInstaller 打包
echo "5️⃣ 開始打包為 .app..."
pyinstaller ${APP_NAME}.spec --clean

# 檢查是否成功
if [ -d "dist/${APP_NAME}.app" ]; then
    echo "✅ .app 建立成功: dist/${APP_NAME}.app"
else
    echo "❌ 打包失敗，請檢查錯誤訊息"
    exit 1
fi

# 建立 .pkg 安裝包
echo "6️⃣ 建立 .pkg 安裝包..."

# 建立暫存目錄結構
mkdir -p pkg_root/Applications
cp -R "dist/${APP_NAME}.app" pkg_root/Applications/

# 使用 pkgbuild 建立 pkg
pkgbuild --root pkg_root \
         --identifier "com.booking.searchtool" \
         --version "${VERSION}" \
         --install-location "/" \
         "${APP_NAME}_${VERSION}.pkg"

if [ -f "${APP_NAME}_${VERSION}.pkg" ]; then
    echo ""
    echo "🎉 打包完成！"
    echo "   .app 位置: dist/${APP_NAME}.app"
    echo "   .pkg 位置: ${APP_NAME}_${VERSION}.pkg"
    echo ""
    echo "📝 使用方式:"
    echo "   - 雙擊 .pkg 檔案即可安裝到 /Applications"
    echo "   - 或直接拖曳 .app 到應用程式資料夾"
else
    echo "❌ .pkg 建立失敗"
    exit 1
fi

# 清理暫存檔
rm -rf pkg_root
echo "✨ 清理完成"
