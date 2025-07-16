#!/usr/bin/env python3
import yaml
import csv
from datetime import datetime

# Load the merged data
with open('readme-pr-merged.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Get classified PRs from all sources
classified_prs = set()

# 1. From CSV files (batches 1, 4, 5, 6)
csv_files = ['pr_analysis_batch_0_20.csv', 'pr_analysis_batch_4.csv', 
             'pr_analysis_batch_5.csv', 'pr_analysis_batch_6.csv']

for csv_file in csv_files:
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                classified_prs.add(int(row['PR番号']))
        print(f"✓ {csv_file}: {sum(1 for _ in open(csv_file, 'r', encoding='utf-8-sig')) - 1}件")
    except FileNotFoundError:
        print(f"✗ {csv_file} が見つかりません")

# 2. From classification result files (batches 2, 3)
classification_files = [
    ('batch2_classification_results.yaml', 'batch_2_classifications'),
    ('batch3_classification_results.yaml', 'batch_3_classifications')
]

for file, key in classification_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            results = yaml.safe_load(f)
            if key in results:
                for item in results[key]:
                    if 'pr_number' in item:
                        classified_prs.add(item['pr_number'])
                print(f"✓ {file}: {len(results[key])}件")
    except FileNotFoundError:
        print(f"✗ {file} が見つかりません")

print(f"\n分類済みPR総数: {len(classified_prs)}件")

# Get unclassified PRs
unclassified_prs = []
for pr in data['pull_requests']:
    if pr['number'] not in classified_prs:
        unclassified_prs.append(pr)

# Create batch 7 with first 50 unclassified PRs
batch7_prs = unclassified_prs[:50]

# Create batch 7
batch7_data = {
    'batch_metadata': {
        '作成日時': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
        'バッチサイズ': len(batch7_prs),
        '累計処理数': len(classified_prs),
        '今回処理': len(batch7_prs),
        '総未処理数': len(unclassified_prs) - len(batch7_prs)
    },
    'pull_requests': batch7_prs
}

# Save batch 7
filename = f"batch7_real_{datetime.now().strftime('%Y%m%d_%H%M')}.yaml"
with open(filename, 'w', encoding='utf-8') as f:
    yaml.dump(batch7_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

print(f"\n正しいバッチ7を作成しました: {filename}")
print(f"  バッチサイズ: {len(batch7_prs)}件")
print(f"  累計分類済み: {len(classified_prs)}件")
print(f"  未分類残り: {len(unclassified_prs)}件 → {len(unclassified_prs) - len(batch7_prs)}件")
print(f"\nバッチ7のPR番号:")
for i, pr in enumerate(batch7_prs[:10]):
    print(f"  {i+1}. PR #{pr['number']}: {pr['title']}")