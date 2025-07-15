#!/usr/bin/env python3
"""
READMEラベル付きの全PRを取得し、YAMLファイルに保存するスクリプト
"""

import subprocess
import json
import yaml
from datetime import datetime
import os

def get_all_readme_prs():
    """GitHub CLIを使用してREADMEラベル付きの全PRを取得"""
    print("READMEラベル付きPRを取得中...")
    
    # 600件まで取得（GitHubの制限により1回のクエリで取得できる最大数）
    cmd = [
        "gh", "pr", "list",
        "--repo", "team-mirai/policy",
        "--label", "README",
        "--state", "open",
        "--limit", "600",
        "--json", "number,title,author,createdAt,url,labels"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    prs = json.loads(result.stdout)
    
    print(f"取得したPR数: {len(prs)}")
    return prs

def load_existing_data(filename="readme-pr.yaml"):
    """既存のYAMLファイルを読み込む"""
    if not os.path.exists(filename):
        return None
    
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_new_yaml_structure(prs, existing_data=None):
    """新しいYAML構造を作成"""
    
    # 既存のデータから処理済み情報を取得
    existing_pr_map = {}
    if existing_data and 'pull_requests' in existing_data:
        for pr in existing_data['pull_requests']:
            existing_pr_map[pr['number']] = pr
    
    # 新しいデータ構造を作成
    data = {
        'metadata': {
            '取得日時': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
            '総数': len(prs),
            'ラベル更新済み件数': 0,
            '最終更新日時': datetime.now().strftime('%Y年%m月%d日 %H:%M')
        },
        'pull_requests': []
    }
    
    updated_count = 0
    
    for pr in sorted(prs, key=lambda x: x['number'], reverse=True):
        pr_data = {
            'number': pr['number'],
            'title': pr['title'],
            'state': 'OPEN',
            'created_at': pr['createdAt'],
            'author': pr['author']['login'],
            'url': pr['url'],
            'label_updated': False,
            'old_label': 'README',
            'new_label': None
        }
        
        # 既存のデータがある場合は、処理済み情報を引き継ぐ
        if pr['number'] in existing_pr_map:
            existing = existing_pr_map[pr['number']]
            pr_data['label_updated'] = existing.get('label_updated', False)
            pr_data['new_label'] = existing.get('new_label', None)
            pr_data['classification_reason'] = existing.get('classification_reason', None)
            pr_data['analysis_notes'] = existing.get('analysis_notes', None)
            
            if pr_data['label_updated']:
                updated_count += 1
        
        data['pull_requests'].append(pr_data)
    
    data['metadata']['ラベル更新済み件数'] = updated_count
    
    return data

def save_to_yaml(data, filename="readme-pr-new.yaml"):
    """データをYAMLファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"データを {filename} に保存しました")

def main():
    # 既存のデータを読み込む
    existing_data = load_existing_data()
    
    # 全PRを取得
    prs = get_all_readme_prs()
    
    # 新しいYAML構造を作成
    data = create_new_yaml_structure(prs, existing_data)
    
    # 統計情報を表示
    print(f"\n=== 統計情報 ===")
    print(f"総PR数: {data['metadata']['総数']}")
    print(f"ラベル更新済み: {data['metadata']['ラベル更新済み件数']}")
    print(f"未処理: {data['metadata']['総数'] - data['metadata']['ラベル更新済み件数']}")
    
    # YAMLファイルに保存
    save_to_yaml(data)
    
    # 既存のデータとの差分を表示
    if existing_data:
        old_count = len(existing_data.get('pull_requests', []))
        new_count = len(data['pull_requests'])
        print(f"\n既存データとの比較:")
        print(f"  以前のPR数: {old_count}")
        print(f"  現在のPR数: {new_count}")
        print(f"  差分: +{new_count - old_count}")

if __name__ == "__main__":
    main()