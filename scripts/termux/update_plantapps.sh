#!/data/data/com.termux/files/usr/bin/bash
PLANTAPPS_DIR="$HOME/plantapps"
BIN_DIR="$HOME/bin"
SHORTCUTS_DIR="$HOME/.shortcuts"
SCRIPTS_DIR="$PLANTAPPS_DIR/scripts/termux"

echo "=== plantapps 更新開始 ==="

# git pull
cd "$PLANTAPPS_DIR" || { echo "エラー: $PLANTAPPS_DIR が見つかりません"; exit 1; }
git pull origin main || echo "エラー: git pull 失敗"

# pip 依存再インストール
pip install -q flask openpyxl chardet || echo "エラー: pip install 失敗"

# スクリプトを ~/bin/ と ~/.shortcuts/ へ再配置
mkdir -p "$BIN_DIR" "$SHORTCUTS_DIR"
for script in "$SCRIPTS_DIR"/*.sh; do
    [ -f "$script" ] || continue
    name=$(basename "$script")
    cp "$script" "$BIN_DIR/$name" && chmod +x "$BIN_DIR/$name"
done

# Termux:Widget ショートカット
for shortcut in start_tenken.sh stop_tenken.sh sync_tenken.sh; do
    if [ -f "$SCRIPTS_DIR/$shortcut" ]; then
        cp "$SCRIPTS_DIR/$shortcut" "$SHORTCUTS_DIR/$shortcut"
        chmod +x "$SHORTCUTS_DIR/$shortcut"
    fi
done

echo "=== plantapps 更新完了 ==="
