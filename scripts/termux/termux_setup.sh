#!/data/data/com.termux/files/usr/bin/bash
PLANTAPPS_DIR="$HOME/plantapps"
BIN_DIR="$HOME/bin"
SHORTCUTS_DIR="$HOME/.shortcuts"
SCRIPTS_DIR="$PLANTAPPS_DIR/scripts/termux"
REPO_URL="https://github.com/d-kawakami/plantapps"

echo "=== Termux セットアップ開始 ==="

# Step 1: パッケージ更新・インストール
echo "[1/7] パッケージを更新・インストールします..."
pkg update -y || echo "エラー: pkg update 失敗"
pkg install -y python git curl termux-api || echo "エラー: pkg install 失敗"

# Step 2: plantapps クローンまたは pull
echo "[2/7] plantapps を取得します..."
if [ -d "$PLANTAPPS_DIR/.git" ]; then
    echo "既存リポジトリを更新します: $PLANTAPPS_DIR"
    cd "$PLANTAPPS_DIR" && git pull origin main || echo "エラー: git pull 失敗"
else
    git clone "$REPO_URL" "$PLANTAPPS_DIR" || { echo "エラー: git clone 失敗"; exit 1; }
fi

# Step 3: pip 依存インストール
echo "[3/7] Python 依存パッケージをインストールします..."
pip install -q flask openpyxl chardet || echo "エラー: pip install 失敗"

# Step 4: スクリプトを ~/bin/ にコピー・実行権付与
echo "[4/7] スクリプトを ~/bin/ にコピーします..."
mkdir -p "$BIN_DIR"
for script in "$SCRIPTS_DIR"/*.sh; do
    [ -f "$script" ] || continue
    name=$(basename "$script")
    cp "$script" "$BIN_DIR/$name" && chmod +x "$BIN_DIR/$name"
    echo "  コピー: $name → $BIN_DIR/"
done

# Step 5: Termux:Widget ショートカット配置
echo "[5/7] Termux:Widget ショートカットを配置します..."
mkdir -p "$SHORTCUTS_DIR"
for shortcut in start_tenken.sh stop_tenken.sh sync_tenken.sh; do
    if [ -f "$SCRIPTS_DIR/$shortcut" ]; then
        cp "$SCRIPTS_DIR/$shortcut" "$SHORTCUTS_DIR/$shortcut"
        chmod +x "$SHORTCUTS_DIR/$shortcut"
        echo "  ショートカット: $shortcut"
    fi
done

# Step 6: ~/.bashrc にエイリアス追記（重複防止）
echo "[6/7] ~/.bashrc にエイリアスを追記します..."
BASHRC="$HOME/.bashrc"
if ! grep -q "# plantapps aliases" "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" << 'EOF'

# plantapps aliases
alias tenken-start='bash ~/bin/start_tenken.sh'
alias tenken-stop='bash ~/bin/stop_tenken.sh'
alias tenken-sync='bash ~/bin/sync_tenken.sh'
alias tenken-update='bash ~/bin/update_plantapps.sh'
EOF
    echo "  エイリアスを追記しました"
else
    echo "  エイリアスは既に設定済みです（スキップ）"
fi

# Step 7: 完了メッセージ
echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "【使い方】"
echo "  tenken-start   : 点検アプリを起動"
echo "  tenken-stop    : 点検アプリを停止"
echo "  tenken-sync    : X260 AP接続後にDBを同期"
echo "  tenken-update  : plantapps を最新版に更新"
echo ""
echo "設定を反映するには: source ~/.bashrc"
echo "ブラウザで点検アプリ: http://localhost:5001"
