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
            print(f"Error getting PR info: {result.stderr}")
            return None

        pr_info = json.loads(result.stdout)

        # PR差分を取得
        diff_result = subprocess.run([
            'gh', 'pr', 'diff', str(pr_number)
        ], capture_output=True, text=True, cwd='..')

        pr_info['diff'] = diff_result.stdout if diff_result.returncode == 0 else "差分取得エラー"

        return pr_info

    except Exception as e:
        print(f"Error: {e}")
        return None


def create_analysis_file(pr_number, pr_info):
    """分析用のマークダウンファイルを作成"""
    content = f"""# PR #{pr_number} 分析

## 基本情報
- **タイトル**: {pr_info['title']}
- **作成者**: {pr_info['author']['login']}
- **作成日**: {pr_info['createdAt']}
- **URL**: {pr_info['url']}

## PR本文
{pr_info['body'] or '（本文なし）'}

## 差分内容
```diff
{pr_info['diff']}
```

## 分析指示

以下の13のラベルから最も適切なものを1つ選んでください：

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

**分析結果をここに記入してください：**
- **推奨ラベル**: 
- **理由**: 
"""

    filename = f"pr_{pr_number}_analysis.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    return filename


# メイン処理
if __name__ == "__main__":
    pr_number = 1998

    print(f"PR #{pr_number} の詳細を取得中...")
    pr_info = get_pr_details(pr_number)

    if pr_info:
        filename = create_analysis_file(pr_number, pr_info)
        print(f"分析ファイルを作成しました: {filename}")
        print(f"\nファイルを開いて分析を行い、結果を記入してください。")
    else:
        print("PR情報の取得に失敗しました。")
