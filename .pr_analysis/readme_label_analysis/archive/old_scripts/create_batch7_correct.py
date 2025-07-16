#!/usr/bin/env python3
import yaml
from datetime import datetime

# Load the merged data
with open('readme-pr-merged.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Load all classification results to get classified PRs
classified_prs = set()

# Load classification results from all batches
classification_files = [
    'batch1_classification_results.yaml',
    'batch2_classification_results.yaml',
    'batch3_classification_results.yaml',
    'batch4_classification_results.yaml',
    'batch5_classification_results.yaml',
    'batch6_classification_results.yaml'
]

for file in classification_files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            results = yaml.safe_load(f)
            # Extract PR numbers from classification results
            for key, classifications in results.items():
                if isinstance(classifications, list):
                    for item in classifications:
                        if 'pr_number' in item:
                            classified_prs.add(item['pr_number'])
    except FileNotFoundError:
        print(f"警告: {file} が見つかりません")

print(f"これまでに分類されたPR数: {len(classified_prs)}")
print(f"分類済みPR番号の例: {sorted(list(classified_prs))[:10]}")

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
filename = f"batch7_correct_{datetime.now().strftime('%Y%m%d_%H%M')}.yaml"
with open(filename, 'w', encoding='utf-8') as f:
    yaml.dump(batch7_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

print(f"\n正しいバッチ7を作成しました: {filename}")
print(f"  PR数: {len(unclassified_prs)}件")
print(f"  累計処理済み: {len(classified_prs)}件")
print(f"  今回処理: {len(unclassified_prs)}件")
print(f"  残り: {513 - len(classified_prs) - len(unclassified_prs)}件")
print("\nバッチ7のPR番号:")
for i, pr in enumerate(unclassified_prs[:10]):
    print(f"  {i+1}. PR #{pr['number']}: {pr['title']}")