#!/usr/bin/env python3
import yaml
import csv

# Load batch 4 classification results
with open('batch4_classification_results.yaml', 'r', encoding='utf-8') as f:
    batch4_data = yaml.safe_load(f)

# Load batch 4 PR details
with open('batch_20250714_2232.yaml', 'r', encoding='utf-8') as f:
    pr_details = yaml.safe_load(f)

# Create PR number to details mapping
pr_map = {pr['number']: pr for pr in pr_details['pull_requests']}

# Write CSV
with open('pr_analysis_batch_4.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    
    # Header
    writer.writerow([
        'PR番号', 'タイトル', '作成者', '作成日', 'ステータス', 
        '政策分野（新ラベル）', '旧ラベル', '分類理由', '分析メモ', 
        'URL', '説明（200文字まで）'
    ])
    
    # Data rows
    for item in batch4_data['batch_4_classifications']:
        pr_num = item['pr_number']
        pr = pr_map[pr_num]
        
        writer.writerow([
            pr_num,
            pr['title'],
            pr['author'],
            pr['created_at'],
            pr['state'],
            item['label'],
            'README',
            item['reason'],
            f"自動分類: 2025-07-14",
            pr['url'],
            pr['title'][:200]
        ])

print(f"バッチ4のCSVファイルを作成しました: pr_analysis_batch_4.csv")
print(f"  PR数: {len(batch4_data['batch_4_classifications'])}件")