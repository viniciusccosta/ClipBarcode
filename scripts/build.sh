#!/bin/bash

APP_NAME="ClipBarcode"
DMG_NAME="${APP_NAME}.dmg"
APP_PATH="dist/${APP_NAME}.app"

rm -rf build dist
poetry run pyinstaller app.spec

echo "Build complete!"