@echo off
REM Plant Apps 全アプリ一括起動スクリプト (Windows)
REM 各アプリを別ウィンドウで起動します

echo ========================================
echo  Plant Apps 起動中
echo ========================================
echo.
echo  01 日常点検   http://localhost:5001
echo  02 機器台帳   http://localhost:5002
echo  03 引継ぎノート http://localhost:5003
echo  04 写真管理   http://localhost:5004/media
echo.
echo 各ウィンドウで Ctrl+C を押すと停止します
echo ========================================

start "01 日常点検 :5001"   cmd /k "cd /d %~dp001_tenken && python app.py"
timeout /t 1 /nobreak > nul
start "02 機器台帳 :5002"   cmd /k "cd /d %~dp002_daicho && python app.py"
timeout /t 1 /nobreak > nul
start "03 引継ぎノート :5003" cmd /k "cd /d %~dp003_note  && python app.py"
timeout /t 1 /nobreak > nul
start "04 写真管理 :5004"   cmd /k "cd /d %~dp004_media  && python app.py"

echo.
echo 全アプリを起動しました。ブラウザで各URLを開いてください。
pause
