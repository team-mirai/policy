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
        print(f"Error processing PR #{pr_number}: {e}")
        return None


def create_analysis_file(pr_numbers, filename):
    """分析用ファイルを作成"""
    content = """# PR分析バッチ - 最終21件

以下のPRを詳細に分析し、適切な政策ラベルを決定してください。

## 利用可能な政策ラベル
- [システム]: システム・技術基盤
- その他政策: 上記に該当しない政策
- エネルギー: エネルギー政策
- デジタル民主主義: デジタル技術を活用した民主主義
- ビジョン: 国家の基本方針・長期戦略
- 医療: 医療制度・健康政策
- 子育て: 子育て支援・少子化対策
- 教育: 教育制度・学習支援
- 産業政策: 産業振興・経済活動支援
- 福祉: 社会保障・高齢者支援
- 科学技術: 科学技術振興・研究開発
- 経済財政: 経済政策・財政政策
- 行政改革: 行政効率化・政府DX

## 分析指示
各PRについて、タイトル、本文、コード差分を総合的に分析し、最も適切なラベルを1つ選択してください。

---

"""

    for pr_number in pr_numbers:
        print(f"PR #{pr_number} の詳細を取得中...")
        pr_details = get_pr_details(pr_number)

        if pr_details:
            content += f"""
## PR #{pr_number}

**タイトル**: {pr_details['title']}
**作成者**: {pr_details['author']['login']}
**作成日**: {pr_details['createdAt']}
**URL**: {pr_details['url']}

### PR本文
```
{pr_details.get('body', '本文なし')}
```

### コード差分
```diff
{pr_details['diff']}
```

---
"""
        else:
            content += f"""
## PR #{pr_number}

**エラー**: PR詳細の取得に失敗しました

---
"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"分析ファイル '{filename}' を作成しました")


# メイン処理
if __name__ == "__main__":
    # 最後の21件
    pr_numbers = [1750, 1740, 1736, 1733, 1725, 1723, 1716, 1715, 1710, 1707,
                  1705, 1701, 1700, 1697, 1696, 1694, 1688, 1687, 1683, 1682, 1680]

    print(f"最終21件分析ファイルを作成中... ({len(pr_numbers)}件)")
    create_analysis_file(pr_numbers, "final_21_analysis.md")
    print("完了！")
