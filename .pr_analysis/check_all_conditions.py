#!/usr/bin/env python3
import yaml

with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# 各パターンを詳しく調査
patterns = {
    'total': 0,
    'label_updated_false': 0,
    'new_label_none': 0,
    'new_label_missing': 0,
    'both_false_and_none': 0,
    'both_false_and_missing': 0,
    'both_false_and_none_or_missing': 0
}

examples = {
    'label_updated_false': [],
    'new_label_none': [],
    'new_label_missing': [],
    'both_false_and_none_or_missing': []
}

for pr in data['pull_requests']:
    patterns['total'] += 1
    
    # label_updated が False
    if pr.get('label_updated') == False:
        patterns['label_updated_false'] += 1
        if len(examples['label_updated_false']) < 5:
            examples['label_updated_false'].append(f"PR #{pr['number']}: {pr['title']}")
    
    # new_label が None
    if pr.get('new_label') is None:
        patterns['new_label_none'] += 1
        if len(examples['new_label_none']) < 5:
            examples['new_label_none'].append(f"PR #{pr['number']}: {pr['title']}")
    
    # new_label キーが存在しない
    if 'new_label' not in pr:
        patterns['new_label_missing'] += 1
        if len(examples['new_label_missing']) < 5:
            examples['new_label_missing'].append(f"PR #{pr['number']}: {pr['title']}")
    
    # label_updated が False かつ new_label が None
    if pr.get('label_updated') == False and pr.get('new_label') is None:
        patterns['both_false_and_none'] += 1
    
    # label_updated が False かつ new_label キーが存在しない
    if pr.get('label_updated') == False and 'new_label' not in pr:
        patterns['both_false_and_missing'] += 1
    
    # label_updated が False かつ (new_label が None または存在しない)
    if (pr.get('label_updated') == False and 
        ('new_label' not in pr or pr.get('new_label') is None)):
        patterns['both_false_and_none_or_missing'] += 1
        if len(examples['both_false_and_none_or_missing']) < 10:
            examples['both_false_and_none_or_missing'].append(f"PR #{pr['number']}: {pr['title']}")

print("=== 統計結果 ===")
for key, value in patterns.items():
    print(f"{key}: {value}")

print("\n=== 例 ===")
for key, example_list in examples.items():
    if example_list:
        print(f"\n{key}の例:")
        for example in example_list:
            print(f"  {example}")

# 実際に未処理のPRを20件取得
print("\n=== 未処理PR（最初の20件）===")
unprocessed = []
for pr in data['pull_requests']:
    if (pr.get('label_updated') == False and 
        ('new_label' not in pr or pr.get('new_label') is None)):
        unprocessed.append(pr['number'])
        if len(unprocessed) >= 20:
            break

print(f"未処理PR番号（最初の20件）: {unprocessed}")
print(f"実際の未処理PR数: {patterns['both_false_and_none_or_missing']}") 