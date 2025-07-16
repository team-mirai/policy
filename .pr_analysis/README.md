# PR分析システム

政策提案PRの分析・整理を行うツール群

## ディレクトリ構造

```
.pr_analysis/
├── policy_pr_analyzer/      # 政策分野別PR分析システム（新）
│   ├── README.md           # 詳細なドキュメント
│   ├── scripts/            # 分析スクリプト
│   │   ├── fetch_pr_data.py        # GitHub APIでPRデータ取得
│   │   └── prepare_for_analysis.py # LLM分析用プロンプト生成
│   └── output/             # 分析結果
│
└── readme_label_analysis/   # READMEラベル分類システム（旧）
    ├── analyze_readme_prs.py      # READMEラベルPR分析
    ├── update_pr_labels.py        # GitHubラベル更新
    └── archive/                   # 過去の分析結果
```

## 使い分け

### 1. 政策分野別の大量PR分析（新システム）
`policy_pr_analyzer/` を使用。教育・医療・福祉など特定の政策分野ラベルが付いたPRを分析し、類似提案をグループ化して政策チームの意思決定を支援。

```bash
cd policy_pr_analyzer
python3 scripts/fetch_pr_data.py --label 教育 --limit 10
```

### 2. READMEラベルの分類（旧システム）
`readme_label_analysis/` を使用。READMEラベルが付いたPRを13の政策分野に自動分類。

```bash
cd readme_label_analysis
python3 analyze_readme_prs.py
```

## 詳細

各システムの詳細は、それぞれのディレクトリ内のREADME.mdを参照してください。