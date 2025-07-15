#!/usr/bin/env python3
"""
残りの未分類PRを分類（直接分析版）
"""
import csv
import subprocess
import json
import yaml
import os
from datetime import datetime

def load_unclassified_prs():
    """未分類PRを読み込み"""
    unclassified_file = "unclassified_prs_20250714_230316.csv"
    unclassified_prs = []
    
    with open(unclassified_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        unclassified_prs = list(reader)
    
    return unclassified_prs

def get_pr_details_batch(pr_numbers):
    """複数のPR詳細をバッチで取得"""
    pr_details = {}
    
    for pr_num in pr_numbers:
        # キャッシュチェック
        cache_file = f"pr_cache/pr_{pr_num}.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                pr_details[pr_num] = json.load(f)
            continue
        
        # GitHub APIで取得
        cmd = ["gh", "pr", "view", str(pr_num), 
               "--repo", "team-mirai/policy", 
               "--json", "body,title,files,additions,deletions"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # 差分も取得（最初の200行）
            diff_cmd = ["gh", "pr", "diff", str(pr_num), "--repo", "team-mirai/policy"]
            diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
            
            if diff_result.returncode == 0:
                diff_lines = diff_result.stdout.split('\n')[:200]
                data['diff'] = '\n'.join(diff_lines)
            
            pr_details[pr_num] = data
            
            # キャッシュ保存
            os.makedirs("pr_cache", exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    return pr_details

def save_batch_for_analysis(batch_prs, batch_num):
    """分析用にバッチ情報を保存"""
    batch_data = {
        'batch_num': batch_num,
        'timestamp': datetime.now().isoformat(),
        'prs': []
    }
    
    for pr in batch_prs:
        batch_data['prs'].append({
            'number': int(pr['PR番号']),
            'title': pr['タイトル'],
            'author': pr['作成者'],
            'created_at': pr['作成日'],
            'url': pr['URL']
        })
    
    filename = f"analysis_batch_{batch_num:03d}.yaml"
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(batch_data, f, allow_unicode=True, default_flow_style=False)
    
    return filename

def main():
    # 未分類PRを読み込み
    unclassified_prs = load_unclassified_prs()
    print(f"未分類PR総数: {len(unclassified_prs)}件")
    
    # バッチサイズ
    batch_size = 50
    total_batches = (len(unclassified_prs) + batch_size - 1) // batch_size
    
    print(f"バッチ数: {total_batches} (各{batch_size}件)")
    
    # 最初のバッチを準備
    batch_num = 1
    start_idx = 0
    end_idx = min(batch_size, len(unclassified_prs))
    
    current_batch = unclassified_prs[start_idx:end_idx]
    
    print(f"\nバッチ{batch_num}を準備中 ({len(current_batch)}件)...")
    
    # PR番号リスト
    pr_numbers = [int(pr['PR番号']) for pr in current_batch]
    
    # PR詳細を取得
    print("PR詳細を取得中...")
    pr_details = get_pr_details_batch(pr_numbers)
    
    # 分析用ファイルを作成
    batch_file = save_batch_for_analysis(current_batch, batch_num)
    
    # 詳細情報も保存
    details_file = f"batch_details_{batch_num:03d}.json"
    with open(details_file, 'w', encoding='utf-8') as f:
        json.dump(pr_details, f, ensure_ascii=False, indent=2)
    
    print(f"\n準備完了!")
    print(f"  バッチ情報: {batch_file}")
    print(f"  PR詳細: {details_file}")
    print(f"  PR数: {len(current_batch)}件")
    print(f"\n最初の5件:")
    for i, pr in enumerate(current_batch[:5]):
        print(f"  {i+1}. PR #{pr['PR番号']}: {pr['タイトル']}")

if __name__ == "__main__":
    main()