#!/usr/bin/env python3
import yaml
import subprocess
from datetime import datetime


def remove_readme_labels():
    """今回更新したPRからREADMEラベルを削除する"""

    # YAMLファイルを読み込み
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 今回更新したPRを特定（label_updated が True のもの）
    updated_prs = []
    for pr in data['pull_requests']:
        if pr.get('label_updated') == True:
            updated_prs.append(pr)

    print(f"READMEラベル削除対象PR: {len(updated_prs)}件")

    # 各PRからREADMEラベルを削除
    success_count = 0
    failed_count = 0

    for pr in updated_prs:
        pr_number = pr['number']

        print(f"PR #{pr_number}: READMEラベルを削除中...")

        try:
            # READMEラベルを削除
            result = subprocess.run([
                'gh', 'pr', 'edit', str(pr_number),
                '--remove-label', 'README'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                success_count += 1
                print(f"  ✅ 成功")
            else:
                print(f"  ❌ 失敗: {result.stderr}")
                failed_count += 1

        except Exception as e:
            print(f"  ❌ エラー: {e}")
            failed_count += 1

    # 結果をログに記録
    log_entry = f"""
## READMEラベル削除実行結果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

- 対象PR数: {len(updated_prs)}件
- 削除成功: {success_count}件
- 削除失敗: {failed_count}件

### 削除対象PRリスト
"""

    for pr in updated_prs:
        log_entry += f"- PR #{pr['number']}: {pr.get('new_label', 'N/A')}\n"

    # log.mdに追記
    with open('log.md', 'a', encoding='utf-8') as f:
        f.write(log_entry)

    print(f"\n=== 実行結果 ===")
    print(f"対象PR数: {len(updated_prs)}件")
    print(f"削除成功: {success_count}件")
    print(f"削除失敗: {failed_count}件")
    print(f"ログをlog.mdに追記しました")

    return success_count, failed_count


if __name__ == "__main__":
    remove_readme_labels()
