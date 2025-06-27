#!/usr/bin/env python3
import yaml
import subprocess
import json
import os


def get_pr_details(pr_number):
    """GitHub CLIを使ってPRの詳細を取得"""
    try:
        # PR基本情報を取得
        result = subprocess.run([
            'gh', 'pr', 'view', str(pr_number),
            '--json', 'title,body,author,createdAt,url'
        ], capture_output=True, text=True, cwd='..')

        if result.returncode != 0:
            print(f"Error getting PR #{pr_number} info: {result.stderr}")
            return None

        pr_info = json.loads(result.stdout)

        # PR差分を取得
        diff_result = subprocess.run([
            'gh', 'pr', 'diff', str(pr_number)
        ], capture_output=True, text=True, cwd='..')

        pr_info['diff'] = diff_result.stdout if diff_result.returncode == 0 else "差分取得エラー"

        return pr_info

    except Exception as e:
        print(f"Error getting PR #{pr_number}: {e}")
        return None


def create_batch_analysis_file(pr_numbers):
    """バッチ分析用のマークダウンファイルを作成"""
    content = f"""# バッチ分析 - PR #{pr_numbers[0]} から #{pr_numbers[-1]}

## 分析対象PR一覧
"""

    for i, pr_number in enumerate(pr_numbers, 1):
        print(f"PR #{pr_number} の詳細を取得中... ({i}/{len(pr_numbers)})")
        pr_info = get_pr_details(pr_number)

        if pr_info:
            content += f"""
---

## PR #{pr_number}: {pr_info['title']}

### 基本情報
- **作成者**: {pr_info['author']['login']}
- **作成日**: {pr_info['createdAt']}
- **URL**: {pr_info['url']}

### PR本文
{pr_info['body'] or '（本文なし）'}

### 差分内容
```diff
{pr_info['diff'][:2000]}{'...(省略)' if len(pr_info['diff']) > 2000 else ''}
```

### 分析結果
**推奨ラベル**: 
**理由**: 

"""
        else:
            content += f"""
---

## PR #{pr_number}: 詳細取得エラー

### 分析結果
**推奨ラベル**: 
**理由**: 

"""

    content += """
---

## 利用可能なラベル

1. **[システム]** - システム関連、技術的な修正
2. **その他政策** - 他のカテゴリに当てはまらない政策
3. **エネルギー** - エネルギー政策、環境・気候変動
4. **デジタル民主主義** - デジタル技術を活用した民主主義、情報公開
5. **ビジョン** - 国家ビジョン、長期戦略、文化政策
6. **医療** - 医療制度、健康政策
7. **子育て** - 子育て支援、少子化対策
8. **教育** - 教育制度、学習支援
9. **産業政策** - 産業振興、労働政策、経済活動支援
10. **福祉** - 社会保障、高齢者支援、障害者支援
11. **科学技術** - 科学技術政策、研究開発
12. **経済財政** - 経済政策、財政政策、税制
13. **行政改革** - 行政効率化、規制改革、政府DX
"""

    filename = f"batch_analysis_{pr_numbers[0]}_{pr_numbers[-1]}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    return filename


# メイン処理
if __name__ == "__main__":
    pr_numbers = [1998, 1935, 1933, 1928, 1924, 1923, 1916, 1911, 1910,
                  1907, 1905, 1901, 1900, 1897, 1888, 1876, 1871, 1865, 1862, 1858]

    print(f"バッチ分析ファイルを作成中... ({len(pr_numbers)}件)")
    filename = create_batch_analysis_file(pr_numbers)
    print(f"分析ファイルを作成しました: {filename}")
    print(f"\nファイルを開いて各PRの分析を行い、結果を記入してください。")
