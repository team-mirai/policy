# PR分析・ラベル更新システム

READMEラベルが付いているPRを13の政策分野に自動分類し、GitHubのラベルを更新するシステムです。

## クイックスタート（2コマンドで完了）

```bash
# 1. まずドライランで確認（実際の更新はしない）
./classify_and_update_labels.sh --dry-run

# 2. 問題なければ実行
./classify_and_update_labels.sh
```

これだけで全てのREADMEラベルPRが分析・分類・更新されます！

## 詳細な使い方

### オプション

```bash
# OPENのPRのみ処理
./classify_and_update_labels.sh --open-only

# 最初の50件だけ処理
./classify_and_update_labels.sh --limit 50

# OPENのPRを10件だけドライラン
./classify_and_update_labels.sh --open-only --limit 10 --dry-run
```

### 個別実行（細かい制御が必要な場合）

```bash
# 1. READMEラベルのPRを取得
python3 get_readme_prs.py -o target_prs.csv

# 2. 分析・分類
python3 claude_pr_classifier.py target_prs.csv -o classified_prs.csv

# 3. ラベル表記修正（[システム] の表記揺れなど）
python3 fix_label_format.py classified_prs.csv

# 4. GitHubラベル更新
python3 update_pr_labels.py -i classified_prs_fixed.csv
```

## 政策分野ラベル

以下の13分野に分類されます：

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
13. **[システム]** - README更新、システム改善

## 処理時間の目安

- PR取得: 数秒
- 分析・分類: 約0.3秒/PR（100件で約30秒）
- ラベル更新: 約0.5秒/PR（100件で約50秒）

## トラブルシューティング

### 中断した場合の再開

```bash
# 分析の再開（キャッシュが効くので高速）
python3 claude_pr_classifier.py target_prs.csv --resume

# ラベル更新の再開
python3 update_pr_labels.py -i classified_prs_fixed.csv --resume
```

### エラーが出た場合

1. **GitHub CLI認証エラー**: `gh auth login` で再認証
2. **claude コマンドエラー**: Claude CLIがインストールされているか確認
3. **権限エラー**: リポジトリへの書き込み権限があるか確認

## ファイル構成

```
.pr_analysis/
├── README.md                         # このファイル
├── classify_and_update_labels.sh     # 一括実行スクリプト
├── get_readme_prs.py                 # PR取得
├── claude_pr_classifier.py           # 分析・分類
├── fix_label_format.py               # ラベル表記修正
├── update_pr_labels.py               # GitHubラベル更新
└── pr_cache/                         # PR情報のキャッシュ
```

## 必要な環境

- Python 3.6+
- GitHub CLI (`gh`)
- Claude CLI (`claude`)
- リポジトリへの書き込み権限

## セットアップ

```bash
# GitHub CLI認証
gh auth login

# Python依存関係（標準ライブラリのみ使用）
# 追加インストール不要
```

---

以上で完了です！質問があれば issue を作成してください。