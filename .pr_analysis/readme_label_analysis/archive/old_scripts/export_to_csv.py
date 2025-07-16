#!/usr/bin/env python3
"""
分類結果をCSVファイルにエクスポートするスクリプト
"""

import yaml
import csv
from datetime import datetime

def load_yaml(filename):
    """YAMLファイルを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def export_to_csv(yaml_file='readme-pr-merged.yaml', output_file=None):
    """YAMLデータをCSVにエクスポート"""
    
    data = load_yaml(yaml_file)
    
    if not output_file:
        output_file = f'pr_classifications_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    
    # CSVファイルを作成
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'PR番号', 
            'タイトル', 
            '作成日', 
            '作成者',
            '現在のラベル',
            '新しいラベル',
            '分類理由',
            'ラベル更新済み',
            'URL'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # 未処理のPRを先に出力
        unprocessed = []
        processed = []
        
        for pr in data['pull_requests']:
            if pr.get('new_label'):
                processed.append(pr)
            else:
                unprocessed.append(pr)
        
        # 分類済みのPRを書き込み
        for pr in processed:
            writer.writerow({
                'PR番号': pr['number'],
                'タイトル': pr['title'],
                '作成日': pr['created_at'],
                '作成者': pr['author'],
                '現在のラベル': pr.get('old_label', 'README'),
                '新しいラベル': pr.get('new_label', ''),
                '分類理由': pr.get('classification_reason', ''),
                'ラベル更新済み': '済' if pr.get('label_updated', False) else '未',
                'URL': pr['url']
            })
        
        # 未分類のPRを書き込み
        for pr in unprocessed:
            writer.writerow({
                'PR番号': pr['number'],
                'タイトル': pr['title'],
                '作成日': pr['created_at'],
                '作成者': pr['author'],
                '現在のラベル': 'README',
                '新しいラベル': '',
                '分類理由': '',
                'ラベル更新済み': '',
                'URL': pr['url']
            })
    
    print(f"CSVファイルを作成しました: {output_file}")
    print(f"  分類済み: {len(processed)}件")
    print(f"  未分類: {len(unprocessed)}件")
    print(f"  合計: {len(data['pull_requests'])}件")
    
    return output_file

def export_batch_plan_csv():
    """バッチ処理計画のCSVを作成"""
    
    data = load_yaml('readme-pr-merged.yaml')
    
    # 未処理のPRのみを抽出
    unprocessed = [pr for pr in data['pull_requests'] if not pr.get('new_label')]
    
    output_file = 'batch_processing_plan.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['バッチ番号', 'PR番号', 'タイトル', '作成日', '作成者', 'URL']
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        batch_size = 50
        for i, pr in enumerate(unprocessed):
            batch_num = (i // batch_size) + 2  # バッチ1は既に処理済み
            
            writer.writerow({
                'バッチ番号': f'バッチ{batch_num}',
                'PR番号': pr['number'],
                'タイトル': pr['title'],
                '作成日': pr['created_at'],
                '作成者': pr['author'],
                'URL': pr['url']
            })
    
    print(f"\nバッチ処理計画を作成しました: {output_file}")
    print(f"  バッチサイズ: {batch_size}件")
    print(f"  必要バッチ数: {(len(unprocessed) + batch_size - 1) // batch_size}バッチ")

if __name__ == "__main__":
    # 全データのCSVを出力
    export_to_csv()
    
    # バッチ処理計画のCSVを出力
    export_batch_plan_csv()