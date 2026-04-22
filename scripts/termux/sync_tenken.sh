#!/data/data/com.termux/files/usr/bin/bash
SERVER_IP=192.168.1.1   # サーバのIPアドレスに変更してください
SERVER_PORT=5000        # サーバのポート番号に変更してください
UPLOAD_URL=http://${SERVER_IP}:${SERVER_PORT}/api/tenken/upload
STATUS_URL=http://${SERVER_IP}:${SERVER_PORT}/api/tenken/status
DB_PATH=$HOME/plantapps/01_tenken/tenken.db
LOG_FILE=$HOME/tenken_sync.log

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== DB同期開始 ==="

# Step 1: AP到達確認
if ! ping -c 1 -W 2 "$SERVER_IP" > /dev/null 2>&1; then
    log "エラー: $SERVER_IP に到達できません。APへのWi-Fi接続を確認してください"
    exit 1
fi
log "サーバ到達確認OK: $SERVER_IP"

# Step 2: DBファイル存在確認
if [ ! -f "$DB_PATH" ]; then
    log "エラー: DBファイルが見つかりません: $DB_PATH"
    exit 1
fi
log "DBファイル確認OK: $DB_PATH ($(du -h "$DB_PATH" | cut -f1))"

# Step 3: サーバ側の状態取得
log "サーバ側DB状態を確認中..."
STATUS_RESP=$(curl -s --connect-timeout 5 "$STATUS_URL") || true
if [ -n "$STATUS_RESP" ]; then
    log "サーバ状態: $STATUS_RESP"
else
    log "警告: サーバ状態の取得に失敗しました（続行します）"
fi

# Step 4: DBアップロード
log "DBをアップロード中: $UPLOAD_URL"
HTTP_CODE=$(curl -s -o /tmp/tenken_sync_resp.txt -w "%{http_code}" \
    --connect-timeout 10 \
    -F "db=@${DB_PATH}" \
    "$UPLOAD_URL")
RESP_BODY=$(cat /tmp/tenken_sync_resp.txt 2>/dev/null)

# Step 5 & 6: 結果判定
if [ "$HTTP_CODE" = "200" ]; then
    log "同期成功: $RESP_BODY"
    # termux-notification が利用可能な場合のみ通知
    if command -v termux-notification > /dev/null 2>&1; then
        termux-notification --title "点検DB同期完了" --content "tenken.db をサーバへ送信しました" 2>/dev/null || true
    fi
else
    log "エラー: HTTPコード=$HTTP_CODE レスポンス=$RESP_BODY"
    exit 1
fi

log "=== DB同期完了 ==="
