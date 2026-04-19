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
4. 作業終了後、サーバの AP（SSID は環境に合わせて設定）へ Wi-Fi 接続
5. Termux:Widget「sync_tenken.sh」をタップ（または: tenken-sync）
6. 通知「点検DB同期完了」を確認
7. サーバの管理画面（例: http://192.168.1.1/list）でも確認可能
```

---

## 接続先設定の変更方法

### Web UI から変更する（推奨）

アプリ起動中にブラウザで以下を開きます:

```
http://localhost:5001/sync
```

「⚙️ サーバ接続設定」からサーバ IP・ポート・DB パスを変更し、「💾 設定を保存」をタップしてください。変更した設定は `sync_config.json` に保存され、次回以降も引き継がれます。

### シェルスクリプトのデフォルト値を変更する

`sync_tenken.sh` の初期値を書き換えたい場合は直接編集してください:

```bash
nano ~/bin/sync_tenken.sh
```

```bash
SERVER_IP=192.168.1.1   # サーバのIPアドレスに変更してください
SERVER_PORT=5000         # サーバのポート番号に変更してください
```

> Web UI で保存した設定が優先されます。`sync_config.json` を削除するとシェルスクリプトの初期値に戻ります。

---

## トラブルシューティング

| 症状 | 確認方法 |
|---|---|
| DB同期が失敗する | `ping <SERVER_IP>` でAP接続確認 |
| サーバ側の状態確認 | `curl http://<SERVER_IP>:<SERVER_PORT>/api/tenken/status` |
| 同期ログ確認 | `cat ~/tenken_sync.log` |
| アプリが起動しない | `cat ~/tenken.log` でエラー確認 |
| PIDファイルが残っている | `rm ~/tenken.pid` してから再起動 |
| Termux:Widget に表示されない | Termux:Widget のウィジェットを一度削除して再追加 |
