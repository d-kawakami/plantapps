# Termux 点検アプリ 運用ガイド

## 前提条件

以下のアプリを F-Droid からインストールしてください。

- **Termux**: https://f-droid.org/packages/com.termux/
- **Termux:API**: https://f-droid.org/packages/com.termux.api/
- **Termux:Widget**: https://f-droid.org/packages/com.termux.widget/

> Google Play 版の Termux は動作が不安定なため、F-Droid 版を推奨します。

---

## 初回セットアップ

1. Termux を開いて以下を実行します:

```bash
curl -fsSL https://raw.githubusercontent.com/d-kawakami/plantapps/main/scripts/termux/termux_setup.sh | bash
```

または、リポジトリを手動でクローンしてから実行する場合:

```bash
git clone https://github.com/d-kawakami/plantapps ~/plantapps
bash ~/plantapps/scripts/termux/termux_setup.sh
source ~/.bashrc
```

---

## 日常運用フロー

```
1. Termux:Widget「start_tenken.sh」をタップ（または: tenken-start）
2. ブラウザで http://localhost:5001 を開く
3. 点検データを入力（オフライン可）
4. 作業終了後、X260 AP（SSID: YourSSID）へ Wi-Fi 接続
5. Termux:Widget「sync_tenken.sh」をタップ（または: tenken-sync）
6. 通知「点検DB同期完了」を確認
7. X260サーバの http://192.168.10.1/list でも確認可能
```

---

## 接続先設定の変更方法

`sync_tenken.sh` の冒頭にある変数を編集してください:

```bash
nano ~/bin/sync_tenken.sh
```

```bash
SERVER_IP=192.168.10.1   # X260 のIPアドレス
SERVER_PORT=5400          # media-kanri のポート番号
```

---

## トラブルシューティング

| 症状 | 確認方法 |
|---|---|
| DB同期が失敗する | `ping 192.168.10.1` でAP接続確認 |
| サーバ側の状態確認 | `curl http://192.168.10.1:5400/api/tenken/status` |
| 同期ログ確認 | `cat ~/tenken_sync.log` |
| アプリが起動しない | `cat ~/tenken.log` でエラー確認 |
| PIDファイルが残っている | `rm ~/tenken.pid` してから再起動 |
| Termux:Widget に表示されない | Termux:Widget のウィジェットを一度削除して再追加 |
