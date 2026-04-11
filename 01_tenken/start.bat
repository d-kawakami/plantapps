@echo off
chcp 65001 > nul
echo 日常点検アプリを起動しています...
echo.

cd /d "%~dp0"

REM 初回: 依存パッケージのインストール
if not exist ".deps_installed" (
  echo パッケージをインストール中...
  pip install -r requirements.txt
  echo. > .deps_installed
)

REM DB初期化（初回のみシードデータ投入）
python database.py

echo.
echo ブラウザで http://localhost:5000 を開いてください
echo 停止するには Ctrl+C を押してください
echo.
python app.py
pause
