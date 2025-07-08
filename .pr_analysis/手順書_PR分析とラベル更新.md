# PR分析とラベル更新の作業手順書

## 概要
このドキュメントは、READMEラベルが付いたPRを分析し、適切な政策分野ラベルに更新する作業の手順書です。

## 前提条件
- GitHubのリポジトリ: `team-mirai/policy`
- 使用ツール: `gh` (GitHub CLI)
- Python 3.x
- 作業ブランチ: `pr-classification`

## 政策分野ラベル（13種類）
1. ビジョン
2. デジタル民主主義
3. 行政改革
4. 教育
5. 福祉
6. 子育て
7. 医療
8. 経済財政
9. 産業政策
10. 科学技術
11. エネルギー
12. その他政策
13. [システム]

## 作業手順

### 1. 現状確認
```bash
# READMEラベル付きPRの数を確認
gh pr list --repo team-mirai/policy --label README --limit 1000 --json number | jq length

# 現在のラベル状況を確認
python3 check_label_status.py
```

### 2. PR情報の取得
```bash
# READMEラベル付きPRの詳細情報を取得
python3 get_readme_prs.py
```
- 出力: `readme_prs_data.json`

### 3. PRの分析
**重要**: LLMを使用した分析が必要（キーワードベースでは不可）

#### オプション1: 一括分析（推奨）
```bash
# 全PRを一括で分析
python3 complete_all_analysis.py
```

#### オプション2: バッチ分析
```bash
# 10件ずつバッチで分析
python3 analyze_prs_batch.py 0 10
python3 analyze_prs_batch.py 10 10
# ... 続ける
```

### 4. 分析結果の確認
分析結果は以下の形式のCSVファイルとして出力されます：
- ファイル名: `pr_analysis_final_XXX.csv`
- カラム: PR番号, タイトル, 作成者, 作成日, ステータス, 政策分野（新ラベル）, 旧ラベル, 分類理由, 分析メモ, URL, 説明（200文字まで）

### 5. ラベル更新

#### 最も安定した方法（推奨）
```bash
# 適切な間隔で1件ずつ処理
python3 update_with_logging.py
```

#### 代替方法（バッチ処理）
```bash
# 20件ずつバッチで処理
python3 update_pr_labels_batch.py 0 20
python3 update_pr_labels_batch.py 20 20
# ... 続ける
```

## トラブルシューティング

### タイムアウトエラーが発生する場合
1. **バッチサイズを小さくする**: 50件→20件→10件
2. **実行間隔を長くする**: 0.5秒→1秒→2秒
3. **バックグラウンド実行**:
   ```bash
   nohup python3 update_all_remaining.py > update_progress.log 2>&1 &
   ```

### 進捗が確認できない場合
- Pythonの出力バッファリングが原因
- `sys.stdout.flush()` を使用するか、`update_with_logging.py` を使用

### ghコマンドのエラー
- 適切な間隔（最低0.5秒）を空ける
- 1つのコマンドでラベルの削除と追加を同時に行う:
  ```bash
  gh pr edit PR番号 --repo team-mirai/policy --remove-label README --add-label 新ラベル
  ```

## 成功の目安
- 処理成功率: 70%以上（新規PRはスキップされるため100%にはならない）
- 1件あたりの処理時間: 0.5〜2秒

## 次回作業時の注意点
1. 新規PRが追加されている可能性があるため、必ず現状確認から始める
2. 分析済みCSVファイルがある場合は、そのPR番号のみを処理対象とする
3. LLMによる分析が必須（ユーザーから明確に指示されている）

## 関連ファイル
- `get_readme_prs.py`: PR情報取得スクリプト
- `complete_all_analysis.py`: 一括分析スクリプト
- `update_with_logging.py`: ログ付きラベル更新スクリプト
- `check_label_status.py`: 進捗確認スクリプト
- `pr_analysis_final_383.csv`: 分析結果（例）