# Policy PR Analyzer

政策提案PRを分析し、政策チームの意思決定を支援するシステム

## 概要

GitHub上の大量の政策提案PR（例：教育ラベル724件）を効率的に分析・整理し、政策チームがレビューしやすい形にまとめるツールです。

## ワークフロー

```
1. fetch_pr_data.py → PRデータ取得（JSON出力）
2. prepare_for_analysis.py → LLM分析用プロンプト生成
3. [手動] claude -p < prompts/input/xxx.txt > prompts/output/xxx.txt
4. parse_llm_results.py → LLM結果の解析・整理
5. generate_report.py → レポート・スプレッドシート生成
```

## ディレクトリ構造

```
policy_pr_analyzer/
├── README.md                    # このファイル
├── scripts/
│   ├── fetch_pr_data.py        # 1. GitHub APIでPRデータ取得
│   ├── prepare_for_analysis.py  # 2. LLM分析用プロンプト準備
│   ├── parse_llm_results.py    # 4. LLM結果のパース
│   ├── group_similar_prs.py    # 5. 類似PRのグループ化
│   ├── generate_report.py      # 6. レポート生成
│   └── execute_decisions.py    # 7. レビュー後の一括処理
├── prompts/
│   ├── input/                  # LLMへの入力プロンプト
│   └── output/                 # LLMからの出力結果
├── output/
│   ├── data/                   # 生データ・中間データ
│   ├── reports/                # 分析レポート
│   └── spreadsheets/           # スプレッドシート
└── cache/                      # API応答のキャッシュ
```

## 使い方

### 1. PRデータの取得

```bash
python3 scripts/fetch_pr_data.py --label 教育 --output output/data/education_prs.json
```

### 2. LLM分析の準備

```bash
python3 scripts/prepare_for_analysis.py output/data/education_prs.json \
  --output-dir prompts/input/
```

### 3. LLM分析の実行（手動）

```bash
# 個別に実行
claude -p < prompts/input/pr_1234_analysis.txt > prompts/output/pr_1234_analysis.txt

# またはバッチ実行
for f in prompts/input/*.txt; do
  output="prompts/output/$(basename $f)"
  echo "Processing $f..."
  claude -p < "$f" > "$output"
  sleep 2  # レート制限対策
done
```

### 4. 結果の解析とレポート生成

```bash
# LLM結果をパース
python3 scripts/parse_llm_results.py prompts/output/ \
  --output output/data/analyzed_prs.json

# 類似PRをグループ化
python3 scripts/group_similar_prs.py output/data/analyzed_prs.json \
  --output output/data/grouped_prs.json

# レポート生成
python3 scripts/generate_report.py output/data/grouped_prs.json \
  --output output/reports/education_report.md \
  --spreadsheet output/spreadsheets/education_analysis.csv
```

## 必要な環境

- Python 3.6+
- GitHub CLI (`gh`)：認証済み
- Claude CLI (`claude`)：インストール済み
- リポジトリへの読み取り権限

## セットアップ

```bash
# GitHub CLI認証
gh auth login

# 依存関係のインストール（もし必要なら）
pip install -r requirements.txt
```