#!/bin/bash
# Plant Apps 全アプリ一括起動スクリプト (Linux / macOS / Termux)
# 各アプリをバックグラウンドで起動します

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo " Plant Apps 起動中"
echo "========================================"
echo ""
echo " 01 日常点検     http://localhost:5001"
echo " 02 機器台帳     http://localhost:5002"
echo " 03 引継ぎノート   http://localhost:5003"
echo " 04 写真管理     http://localhost:5004/media"
echo ""
echo "停止: ./stop_all.sh または pkill -f app.py"
echo "========================================"

cd "$SCRIPT_DIR/01_tenken" && python app.py &
PID1=$!
cd "$SCRIPT_DIR/02_daicho" && python app.py &
PID2=$!
cd "$SCRIPT_DIR/03_note"   && python app.py &
PID3=$!
cd "$SCRIPT_DIR/04_media"  && python app.py &
PID4=$!

echo ""
echo "PIDs: 01=$PID1  02=$PID2  03=$PID3  04=$PID4"
echo "全アプリを起動しました。"
echo ""
echo "モバイルからアクセスする場合は localhost を"
echo "このサーバーのIPアドレスに置き換えてください。"

# 全プロセスを待機（Ctrl+C で全停止）
wait $PID1 $PID2 $PID3 $PID4
