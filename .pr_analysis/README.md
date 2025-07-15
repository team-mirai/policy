# PR分類システム

team-mirai/policyリポジトリのREADMEラベル付きPRを13の政策分野に自動分類するシステム

## 概要

このシステムは以下の特徴を持ちます：
- 再現性の高い処理フロー
- LLM（claude -p）を使用した高精度な分類
- バッチ処理による効率的な実行
- キャッシュによる重複処理の回避

## ディレクトリ構造

```
.pr_analysis/
├── pr_classifier_system.py  # メインスクリプト
├── Makefile                 # 実行用Makefile
├── README.md               # このファイル
├── data/                   # 入力データとキャッシュ
│   ├── readme_prs_*.yaml   # 取得したPRデータ
│   └── pr_*.json          # PR詳細キャッシュ
├── output/                 # 分類結果
│   ├── batch_*.csv        # バッチごとの結果
│   └── merged_all_*.csv   # 統合結果
└── archive/               # アーカイブ
    ├── old_scripts/       # 古いスクリプト
    └── YYYYMMDD/         # 日付ごとの結果
```

## 使い方

### 1. 初期セットアップ
```bash
make setup
```

### 2. 最新のPRを取得して分類
```bash
make fetch
```

### 3. 既存データで分類を再実行
```bash
make classify INPUT=data/readme_prs_20250714_120000.yaml
```

### 4. 結果を統合
```bash
make merge
```

### 5. レポート生成
```bash
make report
```

### 6. すべてを一度に実行
```bash
make all
```

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
13. **[システム]** - README更新、システム改善

## 詳細な使い方

### コマンドラインオプション

```bash
# 基本的な使い方
python3 pr_classifier_system.py --help

# GitHubから取得して分類
python3 pr_classifier_system.py --fetch

# 既存データで分類
python3 pr_classifier_system.py --input data/readme_prs_20250714.yaml

# バッチサイズを変更（デフォルト: 50）
python3 pr_classifier_system.py --fetch --batch-size 30

# 結果を統合
python3 pr_classifier_system.py --merge
```

### カスタマイズ

`pr_classifier_system.py`の`CONFIG`セクションで設定変更可能：

```python
CONFIG = {
    'repo': 'team-mirai/policy',
    'batch_size': 50,
    'output_dir': 'output',
    'data_dir': 'data',
    'rate_limit_sleep': 0.5,
    'policy_labels': [...]
}
```

## トラブルシューティング

### claude -pが使えない場合
`claude`コマンドがインストールされていることを確認してください。

### GitHub認証エラー
`gh auth login`でGitHub CLIの認証を行ってください。

### レート制限エラー
`CONFIG['rate_limit_sleep']`の値を増やしてください。

## 再現性を保つために

1. **同じ入力データを使用**: `data/`ディレクトリのYAMLファイルを保存
2. **バージョン管理**: 結果をGitで管理
3. **タイムスタンプ**: すべての出力ファイルにタイムスタンプ付与
4. **キャッシュ活用**: PR詳細は`data/pr_*.json`にキャッシュ

## メンテナンス

### 古い結果のアーカイブ
```bash
make archive
```

### 一時ファイルの削除
```bash
make clean
```

### 古いスクリプトの整理
```bash
chmod +x cleanup_old_scripts.sh
./cleanup_old_scripts.sh
```