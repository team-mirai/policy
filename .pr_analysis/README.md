# PR 分析管理ディレクトリ

このディレクトリは、team-mirai/policy リポジトリの 400 件の README ラベル付き PR の分析・管理を行うためのファイルを格納しています。

## ファイル構成

### 📊 メインファイル

- **`readme-pr.yaml`** - 400 件すべての PR 情報を統合管理するメインファイル
  - PR 基本情報（番号、タイトル、状態、作成日、作成者、URL）
  - ラベル更新状況（`label_updated: true/false`）
  - 分類情報（`old_label`, `new_label`, `classification_reason`）
  - 分析メモ（`analysis_notes`）
  - 統計情報とバッチ処理計画

### 📝 実行ログ

- **`log.md`** - ラベル更新実行ログ
  - `gh pr edit` コマンドの実行履歴
  - 各 PR のラベル変更結果
  - 処理日時と結果統計

## 🔄 ワークフロー

### 1. 分析フェーズ

1. 未処理 PR（`label_updated: false`）を 10-20 件選択
2. GitHub API で PR の詳細情報（description, diff）を取得
3. Claude-4-Sonnet で内容を全文分析
4. 13 種類の政策ラベルから最適なものを選択
5. `readme-pr.yaml`の`new_label`と`analysis_notes`を更新

### 2. ラベル更新フェーズ（現在は禁止中）

1. 分析済み PR に対して`gh pr edit`コマンドを実行
2. README ラベルを削除し、新しい政策ラベルを追加
3. `label_updated: true`に更新
4. 実行ログを`log.md`に記録

## 📈 進捗状況

- **総 PR 数**: 401 件
- **処理済み**: 20 件（5.0%）
- **分析済み（未ラベル更新）**: 10 件
- **未処理**: 371 件

## 🏷️ 利用可能な政策ラベル

1. **[システム]** - マニフェストの構成や運用システム
2. **その他政策** - 上記カテゴリに該当しない政策提案
3. **エネルギー** - エネルギー政策
4. **デジタル民主主義** - 政治参加や民主主義の発展
5. **ビジョン** - 国家ビジョンや将来構想
6. **医療** - 医療制度や健康政策
7. **子育て** - 子育て支援や児童福祉
8. **教育** - 教育制度や学習環境
9. **産業政策** - 産業振興や農業政策
10. **福祉** - 社会保障制度や福祉政策
11. **科学技術** - 科学技術政策
12. **経済財政** - 経済政策や財政制度
13. **行政改革** - 行政手続きの改革やデジタル化

## 🎯 目標

- 400 件すべての PR を適切な政策ラベルで分類
- 体系的な政策議論の基盤構築
- 効率的な PR 管理システムの確立
- 政策分野別の議論活性化

## 📝 メモ

- 分析は Claude-4-Sonnet による全文読解で実施
- キーワードベースではなく、文脈を理解した分類
- 複数分野にまたがる場合は最も中心的なテーマを選択
- 分類理由と分析メモを詳細に記録

---

## 🤖 AI 作業者向けガイド

### 前提条件

- GitHub CLI (`gh`) がインストール・認証済み
- Python 3.x がインストール済み
- `pyyaml` パッケージがインストール済み
- Cursor 上で Claude-4-Sonnet を使用可能

### 📋 作業手順（10 件バッチ分析）

#### ステップ 1: 環境確認

```bash
# 作業ディレクトリに移動
cd /path/to/team-mirai/policy/.pr_analysis

# 現在の進捗確認
grep -c "label_updated: false" readme-pr.yaml
```

#### ステップ 2: 分析対象 PR の選定

```python
#!/usr/bin/env python3
# analyze_batch.py
import yaml

def get_next_batch(limit=10):
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    unprocessed = []
    for pr in data['pull_requests']:
        if pr.get('label_updated') == False and pr.get('new_label') is None:
            unprocessed.append(pr['number'])
            if len(unprocessed) >= limit:
                break

    return unprocessed

# 次の10件を取得
next_batch = get_next_batch(10)
print("次の分析対象PR:", next_batch)
```

#### ステップ 3: PR 詳細情報の取得

各 PR について以下のコマンドで詳細情報を取得：

```bash
# PR基本情報
gh pr view {PR_NUMBER} --json title,body,state,author,url,createdAt

# PR差分
gh pr diff {PR_NUMBER}
```

**重要**: 各 PR の内容を `pr_{NUMBER}_analysis.md` ファイルに保存し、以下の形式で整理：

````markdown
# PR #{NUMBER} 分析用データ

## 基本情報

- **タイトル**: {title}
- **作成者**: {author}
- **作成日**: {createdAt}
- **URL**: {url}

## PR 本文

{body}

## 差分内容

```diff
{diff}
```
````

## 分析指示

[13 種類の政策ラベルから選択する指示を記載]

```

#### ステップ 4: Claude-4-Sonnet による分析

各 PR について以下の判断基準で分析：

1. **PR の内容を全体的に読んで、主要な政策テーマを特定**
2. **マニフェストの構成や記述方法に関する提案は [システム] を選択**
3. **複数の分野にまたがる場合は、最も中心的なテーマを選択**
4. **政策提案の具体的な内容を重視して判断**

分析結果の記録形式：
```

選択したラベル: [ラベル名]
理由: [100 文字程度で選択理由を説明]

````

#### ステップ 5: YAML ファイルの更新

分析結果を `readme-pr.yaml` に反映するスクリプト：

```python
#!/usr/bin/env python3
# update_analysis.py
import yaml
from datetime import datetime

def update_pr_analysis(analysis_results):
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    analysis_dict = {result['number']: result for result in analysis_results}

    for pr in data['pull_requests']:
        if pr['number'] in analysis_dict:
            analysis = analysis_dict[pr['number']]
            pr['new_label'] = analysis['new_label']
            pr['analysis_notes'] = analysis['analysis_notes']
            pr['classification_reason'] = analysis['classification_reason']

    # 統計情報を更新
    total_prs = len(data['pull_requests'])
    processed_count = sum(1 for pr in data['pull_requests'] if pr.get('label_updated') == True)

    data['statistics']['processed'] = processed_count
    data['statistics']['unprocessed'] = total_prs - processed_count
    data['statistics']['progress_rate'] = f"{(processed_count / total_prs) * 100:.1f}%"
    data['statistics']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open('readme-pr.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True,
                 sort_keys=False, width=1000, indent=2)

# 分析結果の例
analysis_results = [
    {
        'number': 1234,
        'new_label': '教育',
        'analysis_notes': '教育制度改革に関する具体的な政策提案',
        'classification_reason': 'PR内容を詳細分析した結果、教育分野の政策提案と判定'
    }
    # ... 他の分析結果
]

update_pr_analysis(analysis_results)
````

#### ステップ 6: 作業ファイルの整理

```bash
# 一時ファイルを削除
rm -f pr_*_analysis.md analyze_batch.py update_analysis.py

# 変更をコミット
git add .pr_analysis/readme-pr.yaml
git commit -m "feat: {N}件のPR分析を完了 - PR#{開始番号}-#{終了番号}の分析結果を追加"
git push origin pr-classification
```

### ⚠️ 注意事項

1. **実際のラベル更新は禁止**: `gh pr edit` コマンドは実行しない
2. **分析の一貫性**: 同じ基準で判断を行う
3. **詳細な記録**: 分類理由を必ず記録する
4. **バッチサイズ**: 一度に 10-20 件程度に留める
5. **進捗管理**: 統計情報を必ず更新する

### 🔍 品質チェック

分析完了後、以下を確認：

```bash
# 分析済みPR数の確認
grep -c "new_label: " readme-pr.yaml

# 各ラベルの件数確認
grep "new_label: " readme-pr.yaml | sort | uniq -c

# 未分析PR数の確認
grep -c "analysis_notes: 未分析" readme-pr.yaml
```

### 📊 進捗レポート

作業完了時に以下の情報を報告：

- 分析対象 PR 番号の範囲
- 各 PR の分類結果（ラベル + 理由）
- 全体の進捗率
- 分類統計の更新結果

この手順に従うことで、一貫性のある高品質な PR 分析を効率的に実行できます。
