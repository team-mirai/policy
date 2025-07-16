#!/usr/bin/env python3
import yaml
from datetime import datetime

# Load the merged data
with open('readme-pr-merged.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Get all classified PRs from previous batches
classified_prs = set()

# Add all PR numbers from batches 1-6
batch_files = [
    'batch_20250714_2223.yaml',  # batch 1
    'batch_20250714_2227.yaml',  # batch 2
    'batch_20250714_2229.yaml',  # batch 3
    'batch_20250714_2232.yaml',  # batch 4
    'batch5_20250714_2239.yaml', # batch 5
    'batch6_20250714_2245.yaml'  # batch 6
]

for batch_file in batch_files:
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_data = yaml.safe_load(f)
            for pr in batch_data['pull_requests']:
                classified_prs.add(pr['number'])
    except FileNotFoundError:
        print(f"警告: {batch_file} が見つかりません")

print(f"これまでに分類されたPR数: {len(classified_prs)}")

# Get next 50 unclassified PRs
unclassified_prs = []
for pr in data['pull_requests']:
    if pr['number'] not in classified_prs:
        unclassified_prs.append(pr)
    if len(unclassified_prs) >= 50:
        break

# Create batch 7
batch7_data = {
    'batch_metadata': {
        '作成日時': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
        'バッチサイズ': len(unclassified_prs),
        '累計処理数': len(classified_prs) + len(unclassified_prs),
        '総未処理数': 513 - len(classified_prs) - len(unclassified_prs)
    },
    'pull_requests': unclassified_prs
}

# Save batch 7
filename = f"batch7_{datetime.now().strftime('%Y%m%d_%H%M')}.yaml"
with open(filename, 'w', encoding='utf-8') as f:
    yaml.dump(batch7_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

print(f"\nバッチ7を作成しました: {filename}")
print(f"  PR数: {len(unclassified_prs)}件")
print(f"  累計処理済み: {len(classified_prs)}件")
print(f"  今回処理: {len(unclassified_prs)}件")
print(f"  残り: {513 - len(classified_prs) - len(unclassified_prs)}件")
print("\nバッチ7のPR番号:")
for i, pr in enumerate(unclassified_prs[:10]):
    print(f"  {i+1}. PR #{pr['number']}: {pr['title']}")