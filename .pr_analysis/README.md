# PR 分析・ラベル更新システム

このディレクトリには、team-mirai/policy リポジトリの Pull Request 分析とラベル更新を行うためのスクリプト群が含まれています。

## 概要

- **目的**: README ラベルが付いた PR を政策分野別に分類し、適切なラベルを付与する
- **対象**: `label_updated: false` かつ `new_label: None` の PR
- **分類カテゴリ**: 13 の政策分野 + [システム]

## 政策分野ラベル

1. **ビジョン** - 政治理念、基本方針
2. **デジタル民主主義** - 透明性、参加型政治、オープンガバメント
3. **行政改革** - 行政効率化、デジタル化、規制改革
4. **教育** - 教育制度、学習支援
5. **福祉** - 社会保障、高齢者・障害者支援
6. **子育て** - 少子化対策、育児支援
7. **医療** - 医療制度、健康政策
8. **経済財政** - 税制、財政政策、経済政策
9. **産業政策** - 産業振興、技術革新、雇用
10. **科学技術** - 研究開発、イノベーション
11. **エネルギー** - エネルギー政策、環境
12. **その他政策** - 上記に該当しない政策
13. **[システム]** - README 更新、システム改善

## 実行手順

### 1. 分析対象 PR の特定

```bash
python3 get_unanalyzed_batch.py
```

### 2. PR 詳細データの取得

```bash
python3 create_batch_analysis.py
```

### 3. 分析結果の更新

```bash
python3 update_analysis_results.py
```

### 4. ラベル更新の実行

```bash
python3 update_labels.py
```

**重要**: このスクリプトは以下の順序で実行されます：

1. 新しい政策分野ラベルを追加
2. README ラベルを削除
3. YAML ファイルを更新

### 5. README ラベル削除の確認・修正

ラベル更新後、README ラベルが残っている場合は以下を実行：

```bash
python3 remove_readme_labels.py
```

### 6. 最終状況確認

```bash
python3 check_final_status.py
```

## ファイル構成

### スクリプト

- `get_unanalyzed_batch.py` - 未分析 PR の抽出
- `create_batch_analysis.py` - PR 詳細データ取得
- `update_analysis_results.py` - 分析結果の反映
- `update_labels.py` - ラベル更新（メイン）
- `remove_readme_labels.py` - README ラベル削除（補助）
- `check_final_status.py` - 状況確認

### データファイル

- `readme-pr.yaml` - PR 情報とラベル状態
- `log.md` - 実行ログ
- `*.md` - 分析結果ファイル

## 注意事項

### ラベル更新について

1. **必ず新ラベル追加後に README ラベル削除**を行う
2. 部分的失敗の場合は `remove_readme_labels.py` で一括削除
3. 実行前に対象 PR 数を確認する

### エラー対応

- GitHub CLI 認証エラー: `gh auth login` で再認証
- API 制限エラー: 時間をおいて再実行
- ラベル削除失敗: 手動確認後 `remove_readme_labels.py` 実行

### データ整合性

- 実行前後で必ず `check_final_status.py` で状況確認
- YAML ファイルのバックアップを推奨
- ログファイルで実行履歴を追跡

## トラブルシューティング

### よくある問題

1. **README ラベルが削除されない**

   - 原因: GitHub API の制限や権限問題
   - 対処: `remove_readme_labels.py` で一括削除

2. **ラベル更新が部分的に失敗**

   - 原因: ネットワークエラーや API 制限
   - 対処: 失敗した PR を特定し、手動で再実行

3. **YAML 更新エラー**
   - 原因: ファイル権限やフォーマット問題
   - 対処: バックアップから復元し、再実行

## 実行例

```bash
# 1. 未分析PRを20件取得
python3 get_unanalyzed_batch.py

# 2. PR詳細を取得
python3 create_batch_analysis.py

# 3. 分析結果を反映（手動編集後）
python3 update_analysis_results.py

# 4. ラベル更新実行
python3 update_labels.py

# 5. READMEラベル削除確認
python3 remove_readme_labels.py

# 6. 最終確認
python3 check_final_status.py
```

## 成功指標

- `label_updated: true` の件数増加
- `new_label: None` の件数減少
- README ラベル付き PR の減少
- 適切な政策分野ラベルの付与

## 新しい作業手順（2025年7月版）

詳細な手順とトラブルシューティングは以下のドキュメントを参照：
- [手順書_PR分析とラベル更新.md](./手順書_PR分析とラベル更新.md) - 最新の標準作業手順
- [今回の作業記録と教訓.md](./今回の作業記録と教訓.md) - 2025年7月9日の作業記録

### クイックスタート
```bash
# 1. 現状確認
python3 check_label_status.py

# 2. PR情報取得
python3 get_readme_prs.py

# 3. 分析（要LLM、キーワードベース不可）
python3 complete_all_analysis.py

# 4. ラベル更新（推奨版）
python3 update_with_logging.py
```

### 主要な変更点
- LLMによる分析が必須（キーワードベースは不可）
- `update_with_logging.py` が最も安定した更新方法
- ghコマンドの実行間隔は0.5秒以上必要

## 履歴

- 2024-12-19: 初回 71 件分析・更新完了
- 2024-12-19: README ラベル削除機能追加
- 2024-12-19: エラーハンドリング改善
- 2025-07-09: 383件の大規模処理完了（325件成功）
- 2025-07-09: 作業手順書とトラブルシューティングガイド追加
