# PR分析・ラベル更新システム

READMEラベルが付いているPRを13の政策分野に自動分類し、GitHubのラベルを更新するシステムです。

## 使い方（2ステップ）

### ステップ1: READMEラベルのPRを分析してCSV出力

```bash
python3 analyze_readme_prs.py
```

これでREADMEラベルの全PRが分析され、`analyzed_prs_YYYYMMDD_HHMMSS.csv`が出力されます。

### ステップ2: CSVを使ってGitHubのラベルを更新

```bash
# まずドライランで確認
python3 update_pr_labels.py -i analyzed_prs_YYYYMMDD_HHMMSS.csv --dry-run

# 問題なければ実行
python3 update_pr_labels.py -i analyzed_prs_YYYYMMDD_HHMMSS.csv
```

## オプション

### ステップ1のオプション

```bash
# OPENのPRのみ分析
python3 analyze_readme_prs.py --state open

# 最初の50件だけ分析
python3 analyze_readme_prs.py --limit 50

# ドライラン（PR取得のみ、分析はしない）
python3 analyze_readme_prs.py --dry-run
```

### ステップ2のオプション

```bash
# OPENのPRのみ更新
python3 update_pr_labels.py -i analyzed_prs.csv --open-only

# 最初の10件だけ更新
python3 update_pr_labels.py -i analyzed_prs.csv --limit 10

# 中断した場合の再開
python3 update_pr_labels.py -i analyzed_prs.csv --resume
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

- ステップ1: 約0.3秒/PR（100件で約30秒）
- ステップ2: 約0.5秒/PR（100件で約50秒）

## 必要な環境

- Python 3.6+
- GitHub CLI (`gh auth login`で認証済み)
- Claude CLI (`claude`コマンドが使える状態)
- リポジトリへの書き込み権限

## ファイル構成

```
.pr_analysis/
├── README.md                  # このファイル
├── analyze_readme_prs.py      # ステップ1: PR分析・CSV出力
├── update_pr_labels.py        # ステップ2: ラベル更新
└── pr_cache/                  # PR情報のキャッシュ（高速化用）
```

## トラブルシューティング

### エラーが出た場合

1. **GitHub CLI認証エラー**: `gh auth login` で再認証
2. **claude コマンドエラー**: Claude CLIがインストールされているか確認
3. **権限エラー**: リポジトリへの書き込み権限があるか確認

### 中断した場合

```bash
# ステップ2で中断した場合は--resumeで再開可能
python3 update_pr_labels.py -i analyzed_prs.csv --resume
```

---

以上です。質問があれば issue を作成してください。