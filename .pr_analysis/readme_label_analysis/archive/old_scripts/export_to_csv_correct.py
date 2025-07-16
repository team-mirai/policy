#!/usr/bin/env python3
"""
分類結果を正しい形式のCSVファイルにエクスポートするスクリプト
"""

import yaml
import csv
from datetime import datetime

def load_yaml(filename):
    """YAMLファイルを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def export_to_correct_csv(yaml_file='readme-pr-merged.yaml', output_file=None):
    """YAMLデータを正しい形式のCSVにエクスポート"""
    
    data = load_yaml(yaml_file)
    
    if not output_file:
        # 処理済み件数を含むファイル名
        processed_count = sum(1 for pr in data['pull_requests'] if pr.get('new_label'))
        output_file = f'pr_analysis_final_{processed_count}.csv'
    
    # CSVファイルを作成
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'PR番号',
            'タイトル',
            '作成者',
            '作成日',
            'ステータス',
            '政策分野（新ラベル）',
            '旧ラベル',
            '分類理由',
            '分析メモ',
            'URL',
            '説明（200文字まで）'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # 分類済みのPRを先に出力
        processed = []
        unprocessed = []
        
        for pr in data['pull_requests']:
            if pr.get('new_label'):
                processed.append(pr)
            else:
                unprocessed.append(pr)
        
        # 分類済みのPRを書き込み
        for pr in processed:
            # PR本文から説明を生成（200文字まで）
            description = pr.get('title', '')[:200]
            
            writer.writerow({
                'PR番号': pr['number'],
                'タイトル': pr['title'],
                '作成者': pr['author'],
                '作成日': pr['created_at'],
                'ステータス': 'OPEN',
                '政策分野（新ラベル）': pr.get('new_label', ''),
                '旧ラベル': pr.get('old_label', 'README'),
                '分類理由': pr.get('classification_reason', ''),
                '分析メモ': pr.get('analysis_notes', ''),
                'URL': pr['url'],
                '説明（200文字まで）': description
            })
        
        # 未分類のPRも書き込み（今後の処理用）
        for pr in unprocessed:
            description = pr.get('title', '')[:200]
            
            writer.writerow({
                'PR番号': pr['number'],
                'タイトル': pr['title'],
                '作成者': pr['author'],
                '作成日': pr['created_at'],
                'ステータス': 'OPEN',
                '政策分野（新ラベル）': '',
                '旧ラベル': 'README',
                '分類理由': '',
                '分析メモ': '',
                'URL': pr['url'],
                '説明（200文字まで）': description
            })
    
    print(f"正しい形式のCSVファイルを作成しました: {output_file}")
    print(f"  分類済み: {len(processed)}件")
    print(f"  未分類: {len(unprocessed)}件")
    print(f"  合計: {len(data['pull_requests'])}件")
    
    return output_file

def export_batch_csv(batch_start=0, batch_size=20):
    """特定のバッチのCSVを作成"""
    
    data = load_yaml('readme-pr-merged.yaml')
    
    # 分類済みのPRのみを抽出
    processed = [pr for pr in data['pull_requests'] if pr.get('new_label')]
    
    # バッチの範囲を決定
    batch_end = min(batch_start + batch_size, len(processed))
    batch_prs = processed[batch_start:batch_end]
    
    output_file = f'pr_analysis_batch_{batch_start}_{batch_end}.csv'
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'PR番号',
            'タイトル',
            '作成者',
            '作成日',
            'ステータス',
            '政策分野（新ラベル）',
            '旧ラベル',
            '分類理由',
            '分析メモ',
            'URL',
            '説明（200文字まで）'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for pr in batch_prs:
            description = pr.get('title', '')[:200]
            
            writer.writerow({
                'PR番号': pr['number'],
                'タイトル': pr['title'],
                '作成者': pr['author'],
                '作成日': pr['created_at'],
                'ステータス': 'OPEN',
                '政策分野（新ラベル）': pr.get('new_label', ''),
                '旧ラベル': pr.get('old_label', 'README'),
                '分類理由': pr.get('classification_reason', ''),
                '分析メモ': pr.get('analysis_notes', ''),
                'URL': pr['url'],
                '説明（200文字まで）': description
            })
    
    print(f"\nバッチCSVファイルを作成しました: {output_file}")
    print(f"  バッチ範囲: {batch_start}〜{batch_end}")
    print(f"  PR数: {len(batch_prs)}件")

if __name__ == "__main__":
    # 全データの正しい形式のCSVを出力
    export_to_correct_csv()
    
    # 最初の20件のバッチCSVも作成
    export_batch_csv(0, 20)