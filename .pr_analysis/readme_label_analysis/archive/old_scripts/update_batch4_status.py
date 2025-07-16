#!/usr/bin/env python3
import yaml

# Load merged data
with open('readme-pr-merged.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Load batch 4 classifications
with open('batch4_classification_results.yaml', 'r', encoding='utf-8') as f:
    batch4_results = yaml.safe_load(f)

# Update status for batch 4 PRs
classified_numbers = {item['pr_number'] for item in batch4_results['batch_4_classifications']}

for pr in data['pull_requests']:
    if pr['number'] in classified_numbers:
        pr['classification_status'] = 'classified'
        # Find the classification
        for item in batch4_results['batch_4_classifications']:
            if item['pr_number'] == pr['number']:
                pr['new_label'] = item['label']
                pr['classification_reason'] = item['reason']
                break

# Save updated data
with open('readme-pr-merged.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

# Count status
classified = sum(1 for pr in data['pull_requests'] if pr.get('classification_status') == 'classified')
unclassified = sum(1 for pr in data['pull_requests'] if pr.get('classification_status') != 'classified')

print(f"バッチ4のステータス更新完了:")
print(f"  分類済み: {classified}件")
print(f"  未分類: {unclassified}件")
print(f"  合計: {len(data['pull_requests'])}件")