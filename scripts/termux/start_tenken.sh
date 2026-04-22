#!/data/data/com.termux/files/usr/bin/bash
PID_FILE="$HOME/tenken.pid"
LOG_FILE="$HOME/tenken.log"
APP_DIR="$HOME/plantapps/01_tenken"
PORT=5001

# APP_DIR の存在確認
if [ ! -d "$APP_DIR" ]; then
    echo "エラー: $APP_DIR が見つかりません"
    exit 1
fi

if [ ! -f "$APP_DIR/app.py" ]; then
    echo "エラー: $APP_DIR/app.py が見つかりません"
    exit 1
fi

# 古いPIDファイルの処理（プロセス名も確認して誤判定を防ぐ）
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null && ps -p "$PID" -o args= 2>/dev/null | grep -q "app.py"; then
        echo "点検アプリは既に起動中です (PID: $PID)"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# app.py プロセスが既に動いているか確認
if pgrep -f "app.py" > /dev/null 2>&1; then
    echo "エラー: app.py は既に起動中です (PID: $(pgrep -f 'app.py' | tr '\n' ' '))"
    echo "停止するには stop_tenken.sh を実行してください"
    exit 1
fi

# ポート使用中の確認（権限不要の方法）
if ss -tln 2>/dev/null | grep -q ":$PORT " || netstat -tln 2>/dev/null | grep -q ":$PORT "; then
    echo "エラー: ポート $PORT は既に使用中です"
    exit 1
fi

cd "$APP_DIR" || { echo "エラー: $APP_DIR に移動できません"; exit 1; }
nohup python app.py >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 1
if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "点検アプリを起動しました (PID: $(cat "$PID_FILE"))"
    echo "ブラウザで http://localhost:$PORT を開いてください"
else
    echo "エラー: 起動に失敗しました。ログを確認してください: $LOG_FILE"
    tail -5 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
