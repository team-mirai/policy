#!/usr/bin/env python3
import yaml


def get_unanalyzed_batch(limit=20):
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
            if len(unanalyzed) >= limit:
                break

    return unanalyzed


# 次の20件を取得
next_batch = get_unanalyzed_batch(20)
print(f"未分析PR: {len(next_batch)}件")
for pr in next_batch:
    print(f"PR #{pr['number']}: {pr['title']}")

# PR番号のリストを出力
pr_numbers = [pr['number'] for pr in next_batch]
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
print(f"目標: 300件まで減らす = {total_unanalyzed - 300}件の分析が必要")
