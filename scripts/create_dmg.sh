#!/bin/bash

APP_NAME="ClipBarcode"
DMG_NAME="${APP_NAME}.dmg"
APP_PATH="dist/${APP_NAME}.app"
VOL_NAME="${APP_NAME} Installer"
ICON_PATH="assets/icon.icns"
# BACKGROUND_PATH="../assets/background.png"

if [ ! -d "$APP_PATH" ]; then
  echo "Error: $APP_PATH does not exist. Run PyInstaller first."
  exit 1
fi

create-dmg --volname "$VOL_NAME" --volicon "$ICON_PATH" --window-pos 200 120 --window-size 600 400 --icon-size 100 --icon "${APP_NAME}.app" 150 50 --app-drop-link 450 50 --no-internet-enable "$DMG_NAME" "$APP_PATH"
echo "DMG created: $DMG_NAME"