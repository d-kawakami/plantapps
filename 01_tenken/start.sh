#!/bin/bash
# 日常点検アプリ起動スクリプト（Linux / Android Termux）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "日常点検アプリを起動しています..."

# 初回: 依存パッケージのインストール
if [ ! -f ".deps_installed" ]; then
  echo "パッケージをインストール中..."
  pip install -r requirements.txt
  touch .deps_installed
fi

# DB初期化（初回のみシードデータ投入）
python database.py

echo ""
echo "ブラウザで http://localhost:5000 を開いてください"
echo "停止するには Ctrl+C を押してください"
echo ""

python app.py
