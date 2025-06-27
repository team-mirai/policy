#!/usr/bin/env python3
import yaml

with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

total = len(data['pull_requests'])
label_updated_false = 0
new_label_none = 0
both_conditions = 0

print(f"総PR数: {total}")

# 各条件をチェック
for pr in data['pull_requests']:
    if pr.get('label_updated') == False:
        label_updated_false += 1
    if pr.get('new_label') is None:
        new_label_none += 1
    if pr.get('label_updated') == False and pr.get('new_label') is None:
        both_conditions += 1

print(f"label_updated: false の数: {label_updated_false}")
print(f"new_label: None の数: {new_label_none}")
print(f"両方の条件を満たす数: {both_conditions}")

# 最初の10件の状況を確認
print("\n最初の10件の状況:")
for i, pr in enumerate(data['pull_requests'][:10]):
    print(f"PR #{pr['number']}: label_updated={pr.get('label_updated')}, new_label={pr.get('new_label')}")

# 未処理の最初の20件を探す
print("\n未処理の最初の20件:")
count = 0
for pr in data['pull_requests']:
    if pr.get('label_updated') == False and pr.get('new_label') is None:
        print(f"PR #{pr['number']}: {pr['title']}")
        count += 1
        if count >= 20:
            break 