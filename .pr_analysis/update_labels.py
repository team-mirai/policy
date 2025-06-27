#!/usr/bin/env python3
import yaml
import subprocess
import json
from datetime import datetime


def update_pr_labels():
    """分析済みPRのラベルを更新する"""

    # YAMLファイルを読み込み
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 更新対象のPRを特定
    target_prs = []
    for pr in data['pull_requests']:
        # label_updated が False で、new_label と analysis_notes が設定されているもの
        if (pr.get('label_updated') == False and
            pr.get('new_label') and
            pr.get('new_label') != 'None' and
                pr.get('analysis_notes')):
            target_prs.append(pr)

    print(f"ラベル更新対象PR: {len(target_prs)}件")

    # 各PRのラベルを更新
    updated_count = 0
    failed_count = 0

    for pr in target_prs:
        pr_number = pr['number']
        new_label = pr['new_label']
        old_label = pr.get('old_label', 'README')

        print(f"PR #{pr_number}: {old_label} → {new_label}")

        try:
            # 新しいラベルを追加
            add_result = subprocess.run([
                'gh', 'pr', 'edit', str(pr_number),
                '--add-label', new_label
            ], capture_output=True, text=True, cwd='..')

            if add_result.returncode == 0:
                print(f"  ✅ 新ラベル追加成功")

                # READMEラベルを削除（重要：新ラベル追加後に実行）
                remove_result = subprocess.run([
                    'gh', 'pr', 'edit', str(pr_number),
                    '--remove-label', 'README'
                ], capture_output=True, text=True, cwd='..')

                if remove_result.returncode == 0:
                    print(f"  ✅ READMEラベル削除成功")
                    # YAMLデータを更新
                    pr['label_updated'] = True
                    pr['updated_at'] = datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S')
                    updated_count += 1
                else:
                    print(f"  ⚠️  READMEラベル削除失敗: {remove_result.stderr}")
                    print(f"  ℹ️  新ラベルは追加済み、手動でREADMEラベル削除が必要")
                    # 新ラベルは追加されているので、部分的成功として扱う
                    pr['label_updated'] = True
                    pr['updated_at'] = datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S')
                    updated_count += 1
            else:
                print(f"  ❌ 新ラベル追加失敗: {add_result.stderr}")
                failed_count += 1

        except Exception as e:
            print(f"  ❌ エラー: {e}")
            failed_count += 1

    # YAMLファイルを更新
    with open('readme-pr.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False)

    # 結果をログに記録
    log_entry = f"""
## ラベル更新実行結果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

- 対象PR数: {len(target_prs)}件
- 更新成功: {updated_count}件
- 更新失敗: {failed_count}件

### 実行手順
1. 新しい政策分野ラベルを追加
2. READMEラベルを削除
3. YAMLファイルのlabel_updatedフィールドを更新

### 更新されたラベル統計
"""

    # ラベル別統計を追加
    label_counts = {}
    for pr in target_prs:
        if pr.get('label_updated') == True:
            label = pr.get('new_label')
            label_counts[label] = label_counts.get(label, 0) + 1

    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        log_entry += f"- {label}: {count}件\n"

    log_entry += f"""
### 注意事項
- 新ラベル追加後にREADMEラベル削除を実行
- 部分的失敗の場合は手動でREADMEラベル削除が必要
- 全て完了後、remove_readme_labels.pyで一括削除も可能
"""

    # log.mdに追記
    with open('log.md', 'a', encoding='utf-8') as f:
        f.write(log_entry)

    print(f"\n=== 実行結果 ===")
    print(f"対象PR数: {len(target_prs)}件")
    print(f"更新成功: {updated_count}件")
    print(f"更新失敗: {failed_count}件")
    print(f"ログをlog.mdに追記しました")

    # READMEラベル削除の確認を促す
    if updated_count > 0:
        print(f"\n⚠️  重要: READMEラベルが残っている可能性があります")
        print(f"確認後、必要に応じて remove_readme_labels.py を実行してください")

    return updated_count, failed_count


if __name__ == "__main__":
    update_pr_labels()
