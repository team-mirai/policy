#!/usr/bin/env python3
"""
YAMLファイルの分類結果に基づいてGitHub上のラベルを更新するスクリプト
"""

import yaml
import subprocess
import time
import sys
from datetime import datetime

def load_yaml(filename):
    """YAMLファイルを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data, filename):
    """YAMLファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def update_github_labels(pr_number, new_label, remove_label='README'):
    """GitHub上のPRラベルを更新"""
    
    success = True
    
    # 新しいラベルを追加
    if new_label:
        print(f"  Adding label '{new_label}'...", end='', flush=True)
        cmd_add = [
            "gh", "pr", "edit", str(pr_number),
            "--repo", "team-mirai/policy",
            "--add-label", new_label
        ]
        
        try:
            subprocess.run(cmd_add, capture_output=True, text=True, check=True)
            print(" ✓")
        except subprocess.CalledProcessError as e:
            print(f" ✗ Error: {e.stderr.strip()}")
            success = False
    
    # READMEラベルを削除
    if remove_label and success:
        print(f"  Removing label '{remove_label}'...", end='', flush=True)
        cmd_remove = [
            "gh", "pr", "edit", str(pr_number),
            "--repo", "team-mirai/policy",
            "--remove-label", remove_label
        ]
        
        try:
            subprocess.run(cmd_remove, capture_output=True, text=True, check=True)
            print(" ✓")
        except subprocess.CalledProcessError as e:
            print(f" ✗ Error: {e.stderr.strip()}")
            success = False
    
    return success

def update_labels_batch(yaml_file, limit=None, dry_run=False):
    """バッチでラベルを更新"""
    
    data = load_yaml(yaml_file)
    
    # 更新対象のPRを抽出
    prs_to_update = []
    for pr in data['pull_requests']:
        if pr.get('new_label') and not pr.get('label_updated', False):
            prs_to_update.append(pr)
    
    if limit:
        prs_to_update = prs_to_update[:limit]
    
    print(f"=== ラベル更新 ===")
    print(f"更新対象: {len(prs_to_update)}件")
    
    if dry_run:
        print("\n[DRY RUN MODE - 実際の更新は行いません]")
        for pr in prs_to_update:
            print(f"PR #{pr['number']}: {pr['title'][:50]}...")
            print(f"  → {pr['new_label']}")
        return
    
    # 確認
    if len(prs_to_update) > 0:
        response = input(f"\n{len(prs_to_update)}件のPRのラベルを更新します。続行しますか？ (y/N): ")
        if response.lower() != 'y':
            print("キャンセルしました")
            return
    
    # 更新実行
    success_count = 0
    failed_prs = []
    
    for i, pr in enumerate(prs_to_update):
        print(f"\n[{i+1}/{len(prs_to_update)}] PR #{pr['number']}: {pr['title'][:50]}...")
        
        success = update_github_labels(pr['number'], pr['new_label'])
        
        if success:
            # YAMLファイルを更新
            for yaml_pr in data['pull_requests']:
                if yaml_pr['number'] == pr['number']:
                    yaml_pr['label_updated'] = True
                    yaml_pr['old_label'] = 'README'
                    break
            
            success_count += 1
            
            # YAMLファイルを保存（進捗を保存）
            data['metadata']['ラベル更新済み件数'] = sum(1 for p in data['pull_requests'] if p.get('label_updated', False))
            data['metadata']['最終更新日時'] = datetime.now().strftime('%Y年%m月%d日 %H:%M')
            save_yaml(data, yaml_file)
        else:
            failed_prs.append(pr['number'])
        
        # API制限を考慮して待機
        if i < len(prs_to_update) - 1:
            time.sleep(0.5)
    
    # 結果サマリー
    print(f"\n=== 更新結果 ===")
    print(f"成功: {success_count}件")
    print(f"失敗: {len(failed_prs)}件")
    
    if failed_prs:
        print(f"\n失敗したPR: {failed_prs}")
    
    # 統計情報を更新
    total_updated = sum(1 for pr in data['pull_requests'] if pr.get('label_updated', False))
    print(f"\n全体の進捗: {total_updated}/{len(data['pull_requests'])}件 完了")

def main():
    yaml_file = 'readme-pr-merged.yaml'
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--dry-run':
            update_labels_batch(yaml_file, dry_run=True)
        elif sys.argv[1].isdigit():
            limit = int(sys.argv[1])
            update_labels_batch(yaml_file, limit=limit)
        else:
            print("使用方法:")
            print("  python update_labels.py          # すべての未更新PRを更新")
            print("  python update_labels.py 10       # 最初の10件だけ更新")
            print("  python update_labels.py --dry-run # 実行せずに確認のみ")
    else:
        update_labels_batch(yaml_file)

if __name__ == "__main__":
    main()