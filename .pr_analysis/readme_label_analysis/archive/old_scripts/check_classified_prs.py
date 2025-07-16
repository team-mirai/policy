#!/usr/bin/env python3
import yaml
import csv

# Get classified PRs from all sources
classified_prs = set()

# 1. From CSV files
csv_files = ['pr_analysis_batch_0_20.csv', 'pr_analysis_batch_4.csv', 
             'pr_analysis_batch_5.csv', 'pr_analysis_batch_6.csv']

for csv_file in csv_files:
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                classified_prs.add(int(row['PR番号']))
    except FileNotFoundError:
        print(f"CSVファイル {csv_file} が見つかりません")

# 2. From classification result files
classification_files = [
    'batch2_classification_results.yaml',
    'batch3_classification_results.yaml'
]

for file in classification_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            results = yaml.safe_load(f)
            for key, classifications in results.items():
                if isinstance(classifications, list):
                    for item in classifications:
                        if 'pr_number' in item:
                            classified_prs.add(item['pr_number'])
    except FileNotFoundError:
        print(f"分類ファイル {file} が見つかりません")

print(f"分類済みPR総数: {len(classified_prs)}件")
print(f"最小PR番号: {min(classified_prs)}")
print(f"最大PR番号: {max(classified_prs)}")
print(f"\n分類済みPR番号の分布:")
sorted_prs = sorted(classified_prs, reverse=True)
for i in range(0, min(20, len(sorted_prs))):
    print(f"  #{sorted_prs[i]}")