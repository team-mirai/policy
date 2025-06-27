#!/usr/bin/env python3
import yaml


def get_next_batch(limit=20):
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    unprocessed = []
    for pr in data['pull_requests']:
        if pr.get('label_updated') == False and pr.get('new_label') is None:
            unprocessed.append({
                'number': pr['number'],
                'title': pr['title'],
                'url': pr['url']
            })
            if len(unprocessed) >= limit:
                break

    return unprocessed


# 次の20件を取得
next_batch = get_next_batch(20)
print(f"次の分析対象PR: {len(next_batch)}件")
for pr in next_batch:
    print(f"PR #{pr['number']}: {pr['title']}")

# PR番号のリストを出力
pr_numbers = [pr['number'] for pr in next_batch]
print(f"\nPR番号リスト: {pr_numbers}")
