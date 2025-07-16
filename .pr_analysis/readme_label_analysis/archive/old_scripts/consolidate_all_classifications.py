#!/usr/bin/env python3
"""
すべての分類結果を1つのCSVファイルに統合
"""
import yaml
import csv
import os
from datetime import datetime

def main():
    all_classifications = []
    
    # 1. 既存のCSVファイルから読み込み
    csv_files = [
        'pr_analysis_batch_0_20.csv',
        'pr_analysis_batch_4.csv',
        'pr_analysis_batch_5.csv',
        'pr_analysis_batch_6.csv'
    ]
    
    print("CSVファイルから読み込み中...")
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                all_classifications.extend(rows)
                print(f"  {csv_file}: {len(rows)}件")
    
    # 2. YAMLファイルから読み込み（batch2, batch3）
    yaml_files = [
        ('batch2_classification_results.yaml', 'batch_2_classifications'),
        ('batch3_classification_results.yaml', 'batch_3_classifications')
    ]
    
    print("\nYAMLファイルから読み込み中...")
    
    # batch2,3のPR詳細を取得するため、元のバッチファイルも読み込む
    batch_data = {}
    batch_files = [
        'batch_20250714_2227.yaml',  # batch2
        'batch_20250714_2229.yaml'   # batch3
    ]
    
    # まず元データを読み込み
    for i, batch_file in enumerate(batch_files):
        if os.path.exists(batch_file):
            with open(batch_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                for pr in data['pull_requests']:
                    batch_data[pr['number']] = pr
            print(f"  バッチ{i+2}データ: {len(data['pull_requests'])}件")
    
    # readme-pr-merged.yamlからも読み込み（フォールバック用）
    if os.path.exists('readme-pr-merged.yaml'):
        with open('readme-pr-merged.yaml', 'r', encoding='utf-8') as f:
            merged_data = yaml.safe_load(f)
            for pr in merged_data['pull_requests']:
                if pr['number'] not in batch_data:
                    batch_data[pr['number']] = pr
    
    # 分類結果を読み込んでCSV形式に変換
    for yaml_file, key in yaml_files:
        if os.path.exists(yaml_file):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                results = yaml.safe_load(f)
                if key in results:
                    converted_count = 0
                    for item in results[key]:
                        pr_num = item['pr_number']
                        if pr_num in batch_data:
                            pr = batch_data[pr_num]
                            csv_row = {
                                'PR番号': pr_num,
                                'タイトル': pr['title'],
                                '作成者': pr['author']['login'] if isinstance(pr['author'], dict) else pr['author'],
                                '作成日': pr['created_at'],
                                'ステータス': pr.get('state', 'OPEN'),
                                '政策分野（新ラベル）': item['label'],
                                '旧ラベル': 'README',
                                '分類理由': item['reason'],
                                '分析メモ': '自動分類: 2025-07-14',
                                'URL': pr['url'],
                                '説明（200文字まで）': pr['title'][:200]
                            }
                            all_classifications.append(csv_row)
                            converted_count += 1
                    print(f"  {yaml_file}: {converted_count}件")
    
    # 3. バッチ7のYAMLからも既に分類されているものを取得
    batch7_file = 'batch7_20250714_2249.yaml'
    if os.path.exists(batch7_file):
        with open(batch7_file, 'r', encoding='utf-8') as f:
            batch7_data = yaml.safe_load(f)
            converted_count = 0
            for pr in batch7_data['pull_requests']:
                if 'new_label' in pr and pr['new_label']:
                    csv_row = {
                        'PR番号': pr['number'],
                        'タイトル': pr['title'],
                        '作成者': pr['author']['login'] if isinstance(pr['author'], dict) else pr['author'],
                        '作成日': pr['created_at'],
                        'ステータス': pr.get('state', 'OPEN'),
                        '政策分野（新ラベル）': pr['new_label'],
                        '旧ラベル': 'README',
                        '分類理由': pr.get('classification_reason', ''),
                        '分析メモ': pr.get('analysis_notes', '自動分類: 2025-07-14'),
                        'URL': pr['url'],
                        '説明（200文字まで）': pr['title'][:200]
                    }
                    all_classifications.append(csv_row)
                    converted_count += 1
            if converted_count > 0:
                print(f"  {batch7_file}: {converted_count}件")
    
    # 重複を除去（PR番号でユニーク化）
    unique_classifications = {}
    for row in all_classifications:
        pr_num = int(row['PR番号'])
        unique_classifications[pr_num] = row
    
    # PR番号順にソート
    sorted_classifications = [unique_classifications[pr_num] for pr_num in sorted(unique_classifications.keys(), reverse=True)]
    
    # 4. 統合CSVファイルを作成
    output_file = f'all_classified_prs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        if sorted_classifications:
            writer = csv.DictWriter(f, fieldnames=sorted_classifications[0].keys())
            writer.writeheader()
            writer.writerows(sorted_classifications)
    
    print(f"\n統合完了!")
    print(f"  出力ファイル: {output_file}")
    print(f"  総分類数: {len(sorted_classifications)}件")
    
    # ラベル別集計
    label_counts = {}
    for row in sorted_classifications:
        label = row['政策分野（新ラベル）']
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print("\nラベル別分類結果:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(sorted_classifications) * 100
        print(f"  {label}: {count}件 ({percentage:.1f}%)")
    
    # 未分類PRの確認
    if os.path.exists('readme-pr-merged.yaml'):
        with open('readme-pr-merged.yaml', 'r', encoding='utf-8') as f:
            all_prs = yaml.safe_load(f)['pull_requests']
            classified_prs = set(unique_classifications.keys())
            unclassified_prs = [pr for pr in all_prs if pr['number'] not in classified_prs]
            
            print(f"\n未分類PR: {len(unclassified_prs)}件")
            
            # 未分類PRリストも出力
            if unclassified_prs:
                unclassified_file = f'unclassified_prs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'
                with open(unclassified_file, 'w', encoding='utf-8') as f:
                    yaml.dump({
                        'total_count': len(unclassified_prs),
                        'pull_requests': unclassified_prs
                    }, f, allow_unicode=True, default_flow_style=False)
                print(f"  未分類PRリスト: {unclassified_file}")

if __name__ == "__main__":
    main()