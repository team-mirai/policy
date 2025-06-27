#!/usr/bin/env python3
import yaml
import subprocess
import json


def create_batch_analysis():
    """バッチ1のPR詳細データを取得して分析用ファイルを作成"""

    # バッチ情報を読み込み
    with open('next_100_batch1_info.yaml', 'r', encoding='utf-8') as f:
        batch_info = yaml.safe_load(f)

    pr_numbers = batch_info['prs']
    print(f"=== PR詳細データ取得開始 ===")
    print(f"対象PR: {len(pr_numbers)}件")
    print(f"範囲: {batch_info['pr_range']}")

    analysis_content = f"""# 次の100件分析 - バッチ1 分析用データ

## 概要
- **バッチ名**: {batch_info['batch_name']}
- **対象PR数**: {batch_info['batch_size']}件
- **PR範囲**: {batch_info['pr_range']}
- **取得日時**: {yaml.dump({'timestamp': None}, default_flow_style=False).split(':')[0]}

## PR詳細データ

"""

    for i, pr_number in enumerate(pr_numbers, 1):
        print(f"PR #{pr_number} のデータを取得中... ({i}/{len(pr_numbers)})")

        try:
            # PR基本情報を取得
            result = subprocess.run([
                'gh', 'pr', 'view', str(pr_number),
                '--json', 'title,body,state,author,url,createdAt'
            ], capture_output=True, text=True, cwd='..')

            if result.returncode == 0:
                pr_data = json.loads(result.stdout)

                # PR差分を取得
                diff_result = subprocess.run([
                    'gh', 'pr', 'diff', str(pr_number)
                ], capture_output=True, text=True, cwd='..')

                diff_content = diff_result.stdout if diff_result.returncode == 0 else "差分取得エラー"

                # 分析用データを追加
                analysis_content += f"""### PR #{pr_number} - {pr_data.get('title', 'タイトル不明')}

**基本情報:**
- **作成者**: {pr_data.get('author', {}).get('login', '不明')}
- **作成日**: {pr_data.get('createdAt', '不明')}
- **状態**: {pr_data.get('state', '不明')}
- **URL**: {pr_data.get('url', '')}

**PR本文:**
```
{pr_data.get('body', 'PR本文なし')}
```

**差分内容:**
```diff
{diff_content[:2000]}{'...(省略)' if len(diff_content) > 2000 else ''}
```

---

"""
            else:
                print(f"  ❌ PR #{pr_number} の取得に失敗: {result.stderr}")
                analysis_content += f"""### PR #{pr_number} - データ取得エラー

**エラー**: {result.stderr}

---

"""
        except Exception as e:
            print(f"  ❌ PR #{pr_number} でエラー: {e}")
            analysis_content += f"""### PR #{pr_number} - 例外エラー

**エラー**: {str(e)}

---

"""

    # 分析用ファイルに保存
    with open('next_100_batch1_analysis.md', 'w', encoding='utf-8') as f:
        f.write(analysis_content)

    print(f"\n=== 完了 ===")
    print(f"分析用データを next_100_batch1_analysis.md に保存しました")
    print(f"次のステップ: ファイルを確認して分析を実行してください")


if __name__ == "__main__":
    create_batch_analysis()
