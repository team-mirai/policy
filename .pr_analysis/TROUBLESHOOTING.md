# トラブルシューティングガイド

## よくある問題と解決方法

### 1. README ラベルが削除されない

**症状**: 新しいラベルは追加されているが、README ラベルが残っている

**原因**:

- GitHub API の制限
- 権限の問題
- ネットワークエラー
- 同時実行による競合

**解決方法**:

```bash
# 1. 対象PRの確認
python3 check_final_status.py

# 2. READMEラベル一括削除
python3 remove_readme_labels.py

# 3. 手動確認（必要に応じて）
gh pr view [PR番号] --json labels
```

**予防策**:

- `update_labels.py` 実行後は必ず `remove_readme_labels.py` を実行
- 大量処理時は小分けにして実行

### 2. ラベル更新が部分的に失敗

**症状**: 一部の PR でラベル更新が失敗する

**原因**:

- GitHub API レート制限
- ネットワーク接続の問題
- PR が既にクローズされている
- 権限不足

**解決方法**:

```bash
# 1. 失敗したPRを特定
grep "label_updated: false" readme-pr.yaml | head -10

# 2. 個別に再実行
gh pr edit [PR番号] --add-label "[新ラベル]"
gh pr edit [PR番号] --remove-label "README"

# 3. YAMLファイルを手動更新
# label_updated: true に変更
```

**予防策**:

- 実行前に GitHub API 制限を確認
- 大量処理時は間隔を空けて実行

### 3. YAML 更新エラー

**症状**: YAML ファイルの読み書きでエラーが発生

**原因**:

- ファイル権限の問題
- YAML フォーマットの破損
- 同時アクセスによる競合
- ディスク容量不足

**解決方法**:

```bash
# 1. バックアップから復元
cp readme-pr.yaml.bak readme-pr.yaml

# 2. 権限確認・修正
chmod 644 readme-pr.yaml

# 3. YAMLフォーマット検証
python3 -c "import yaml; yaml.safe_load(open('readme-pr.yaml'))"

# 4. 手動修正後に再実行
```

**予防策**:

- 実行前にバックアップを作成
- 定期的に YAML ファイルの整合性をチェック

### 4. GitHub CLI 認証エラー

**症状**: `gh` コマンドで認証エラーが発生

**原因**:

- トークンの期限切れ
- 権限スコープの不足
- 認証情報の破損

**解決方法**:

```bash
# 1. 現在の認証状態確認
gh auth status

# 2. 再認証
gh auth login

# 3. 必要な権限スコープを確認
# - repo (フルアクセス)
# - write:org (組織の場合)
```

### 5. スクリプト実行エラー

**症状**: Python スクリプトでエラーが発生

**原因**:

- 依存パッケージの不足
- Python バージョンの問題
- ファイルパスの問題

**解決方法**:

```bash
# 1. 依存パッケージのインストール
pip install pyyaml

# 2. Pythonバージョン確認
python3 --version  # 3.6以上推奨

# 3. 作業ディレクトリの確認
pwd  # .pr_analysis ディレクトリにいることを確認
```

## エラーメッセージ別対処法

### `Error: HTTP 403: Forbidden`

- **原因**: 権限不足
- **対処**: リポジトリの管理者権限を確認、必要に応じて権限を要求

### `Error: HTTP 422: Unprocessable Entity`

- **原因**: 無効なラベル名または存在しない PR
- **対処**: ラベル名と PR 番号を確認

### `Error: HTTP 429: Too Many Requests`

- **原因**: API 制限に達した
- **対処**: 1 時間待機後に再実行

### `FileNotFoundError: readme-pr.yaml`

- **原因**: ファイルパスの問題
- **対処**: 正しいディレクトリにいることを確認

### `yaml.scanner.ScannerError`

- **原因**: YAML フォーマットエラー
- **対処**: バックアップから復元、または手動修正

## 緊急時の対処

### 1. 大量の PR が誤ったラベルで更新された場合

```bash
# 1. 影響範囲の確認
python3 check_final_status.py

# 2. 誤ったラベルを一括削除
# (手動でスクリプト作成が必要)

# 3. 正しいラベルを再適用
python3 update_labels.py
```

### 2. YAML ファイルが破損した場合

```bash
# 1. Gitから最新版を取得
git checkout HEAD -- readme-pr.yaml

# 2. 作業内容を再実行
# (分析結果は別ファイルに保存されているため復旧可能)
```

### 3. 大量の API エラーが発生した場合

```bash
# 1. 実行を停止
Ctrl+C

# 2. 状況確認
python3 check_final_status.py

# 3. 小分けして再実行
# バッチサイズを10件程度に減らして実行
```

## 予防策

### 1. 実行前チェックリスト

- [ ] GitHub CLI 認証確認 (`gh auth status`)
- [ ] 作業ディレクトリ確認 (`.pr_analysis`)
- [ ] YAML ファイルバックアップ作成
- [ ] 対象 PR 数確認
- [ ] API 制限状況確認

### 2. 定期メンテナンス

```bash
# 週次実行推奨
# 1. データ整合性チェック
python3 check_final_status.py

# 2. ログファイルのローテーション
mv log.md log_$(date +%Y%m%d).md
touch log.md

# 3. 一時ファイルの削除
rm -f *.tmp *.bak
```

### 3. モニタリング

- 実行ログの定期確認
- エラー率の監視
- API 制限使用量の確認
- ディスク容量の監視

## サポート

問題が解決しない場合は、以下の情報を含めて報告してください：

1. エラーメッセージの全文
2. 実行したコマンド
3. 実行環境（OS、Python バージョン等）
4. 実行時の状況（対象 PR 数、時刻等）
5. `check_final_status.py` の出力結果
