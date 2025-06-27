#!/usr/bin/env python3
import yaml


def get_final_21_batch():
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    unanalyzed = []
    for pr in data['pull_requests']:
        # label_updated が False で、かつ new_label が None または null
        if (pr.get('label_updated') == False and
                (pr.get('new_label') is None or pr.get('new_label') == 'None')):
            unanalyzed.append({
                'number': pr['number'],
                'title': pr['title'],
                'url': pr['url']
            })
            if len(unanalyzed) >= 21:
                break

    return unanalyzed


# 最後の21件を取得
final_21_batch = get_final_21_batch()
print(f"最終21件未分析PR: {len(final_21_batch)}件")
for pr in final_21_batch:
    print(f"PR #{pr['number']}: {pr['title']}")

# PR番号のリストを出力
pr_numbers = [pr['number'] for pr in final_21_batch]
print(f"\nPR番号リスト: {pr_numbers}")

# 統計情報
with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

total_unanalyzed = 0
for pr in data['pull_requests']:
    if (pr.get('label_updated') == False and
            (pr.get('new_label') is None or pr.get('new_label') == 'None')):
        total_unanalyzed += 1

print(f"\n統計:")
print(f"総未分析PR数: {total_unanalyzed}")
print(f"この21件を分析すれば目標の300件達成: {total_unanalyzed - 21}件")
