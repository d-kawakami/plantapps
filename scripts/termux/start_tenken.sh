#!/data/data/com.termux/files/usr/bin/bash
PID_FILE="$HOME/tenken.pid"
LOG_FILE="$HOME/tenken.log"
APP_DIR="$HOME/plantapps/01_tenken"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "点検アプリは既に起動中です (PID: $PID)"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

cd "$APP_DIR" || { echo "エラー: $APP_DIR が見つかりません"; exit 1; }
nohup python app.py >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 1
if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "点検アプリを起動しました (PID: $(cat "$PID_FILE"))"
    echo "ブラウザで http://localhost:5001 を開いてください"
else
    echo "エラー: 起動に失敗しました。ログを確認してください: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
