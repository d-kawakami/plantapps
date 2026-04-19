#!/data/data/com.termux/files/usr/bin/bash
PID_FILE="$HOME/tenken.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "点検アプリは起動していません"
    exit 0
fi

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" || { echo "エラー: プロセス停止に失敗しました (PID: $PID)"; exit 1; }
    echo "点検アプリを停止しました (PID: $PID)"
else
    echo "プロセスが見つかりません (PID: $PID) — PIDファイルを削除します"
fi

rm -f "$PID_FILE"
