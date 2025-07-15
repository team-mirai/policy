#!/usr/bin/env python3
"""
既存のreadme-pr.yamlのデータを新しいreadme-pr-new.yamlにマージするスクリプト
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

def merge_pr_data():
    # 既存のデータと新しいデータを読み込む
    existing_data = load_yaml('readme-pr.yaml')
    new_data = load_yaml('readme-pr-new.yaml')
    
    # 既存のPRデータをマップに変換
    existing_pr_map = {}
    for pr in existing_data['pull_requests']:
        existing_pr_map[pr['number']] = pr
    
    # 統計情報の初期化
    updated_count = 0
    already_processed_count = 0
    new_prs_count = 0
    
    # 新しいデータに既存の処理済み情報をマージ
    for pr in new_data['pull_requests']:
        pr_number = pr['number']
        
        if pr_number in existing_pr_map:
            existing_pr = existing_pr_map[pr_number]
            
            # 既存の処理済み情報を引き継ぐ
            if existing_pr.get('label_updated', False):
                pr['label_updated'] = True
                pr['old_label'] = existing_pr.get('old_label', 'README')
                pr['new_label'] = existing_pr.get('new_label')
                pr['classification_reason'] = existing_pr.get('classification_reason')
                pr['analysis_notes'] = existing_pr.get('analysis_notes')
                updated_count += 1
                already_processed_count += 1
            else:
                # 未処理のPR
                pr['label_updated'] = False
                pr['old_label'] = 'README'
                pr['new_label'] = None
        else:
            # 新規のPR
            pr['label_updated'] = False
            pr['old_label'] = 'README'
            pr['new_label'] = None
            new_prs_count += 1
    
    # メタデータを更新
    new_data['metadata']['ラベル更新済み件数'] = updated_count
    new_data['metadata']['最終更新日時'] = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    
    # 統計情報を表示
    print("=== マージ結果 ===")
    print(f"総PR数: {len(new_data['pull_requests'])}")
    print(f"既に処理済み: {already_processed_count}")
    print(f"新規PR: {new_prs_count}")
    print(f"未処理PR: {len(new_data['pull_requests']) - already_processed_count}")
    
    # マージしたデータを保存
    save_yaml(new_data, 'readme-pr-merged.yaml')
    print("\nマージ結果を readme-pr-merged.yaml に保存しました")
    
    # 未処理のPRをリストアップ
    unprocessed_prs = [pr for pr in new_data['pull_requests'] if not pr.get('label_updated', False)]
    print(f"\n未処理のPR数: {len(unprocessed_prs)}")
    
    # 最新の未処理PRを10件表示
    print("\n最新の未処理PR（10件）:")
    for pr in unprocessed_prs[:10]:
        print(f"  #{pr['number']}: {pr['title'][:60]}...")

if __name__ == "__main__":
    merge_pr_data()