#!/usr/bin/env python3
"""
バッチ2の分類結果をreadme-pr-merged.yamlに適用するスクリプト
"""

import yaml
from datetime import datetime

def load_yaml(filename):
    """YAMLファイルを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data, filename):
    """YAMLファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def apply_batch2_classifications():
    # 分類結果を読み込む
    classifications = load_yaml('batch2_classification_results.yaml')
    
    # メインのYAMLファイルを読み込む
    data = load_yaml('readme-pr-merged.yaml')
    
    # 分類結果を適用
    updated_count = 0
    for classification in classifications['batch_2_classifications']:
        pr_number = classification['pr_number']
        
        # 該当するPRを探す
        for pr in data['pull_requests']:
            if pr['number'] == pr_number:
                pr['new_label'] = classification['label']
                pr['classification_reason'] = classification['reason']
                pr['analysis_notes'] = f"LLM分析バッチ2: {datetime.now().strftime('%Y-%m-%d')}"
                updated_count += 1
                break
    
    # メタデータを更新
    data['metadata']['最終更新日時'] = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    
    # 保存
    save_yaml(data, 'readme-pr-merged.yaml')
    
    print(f"バッチ2の分類結果を適用しました")
    print(f"更新されたPR数: {updated_count}")
    
    # 統計情報を表示
    total_classified = sum(1 for pr in data['pull_requests'] if pr.get('new_label'))
    print(f"\n全体の進捗:")
    print(f"  分類済み: {total_classified}件")
    print(f"  未分類: {len(data['pull_requests']) - total_classified}件")
    print(f"  合計: {len(data['pull_requests'])}件")

if __name__ == "__main__":
    apply_batch2_classifications()