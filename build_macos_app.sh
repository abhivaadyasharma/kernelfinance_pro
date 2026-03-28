#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="KernelFinance Pro"
SCRIPT="kernel_finance_pro.py"
ICON_FILE=""

# Keep pyinstaller state local to project so builds work in restricted environments.
export PYINSTALLER_CONFIG_DIR="$(pwd)/.pyinstaller"

if [[ -f "assets/logo.icns" ]]; then
  ICON_FILE="assets/logo.icns"
elif [[ -f "logo.icns" ]]; then
  ICON_FILE="logo.icns"
fi

if [[ -n "$ICON_FILE" ]]; then
  pyinstaller --noconfirm --windowed --name "$APP_NAME" --icon "$ICON_FILE" --add-data "assets:assets" "$SCRIPT"
else
  pyinstaller --noconfirm --windowed --name "$APP_NAME" --add-data "assets:assets" "$SCRIPT"
fi

echo "Built app at: dist/$APP_NAME.app"
