#!/usr/bin/env python3
"""分析結果に基づいてPRのラベルを更新（バッチ処理版）"""

import csv
import subprocess
import time
import sys
from datetime import datetime

def load_analysis_results(csv_file, start=0, limit=None):
    """CSVファイルから分析結果を読み込む（範囲指定可能）"""
    results = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < start:
                continue
            if limit and len(results) >= limit:
                break
            results.append({
                'pr_number': row['PR番号'],
                'old_label': 'README',
                'new_label': row['政策分野（新ラベル）'],
                'title': row['タイトル']
            })
    return results

def update_pr_label(pr_number, old_label, new_label):
    """PRのラベルを更新"""
    repo = "team-mirai/policy"
    
    try:
        # READMEラベルを削除
        remove_cmd = ["gh", "pr", "edit", pr_number, "--repo", repo, "--remove-label", old_label]
        subprocess.run(remove_cmd, capture_output=True, text=True, check=True)
        
        # 新しいラベルを追加
        add_cmd = ["gh", "pr", "edit", pr_number, "--repo", repo, "--add-label", new_label]
        subprocess.run(add_cmd, capture_output=True, text=True, check=True)
        
        return True, "SUCCESS"
    except subprocess.CalledProcessError as e:
        return False, f"ERROR: {e.stderr}"

def main():
    # 引数処理
    if len(sys.argv) < 2:
        print("使用方法: python3 update_pr_labels_batch.py <開始位置> [処理数]")
        print("例: python3 update_pr_labels_batch.py 0 10  # 最初の10件を処理")
        print("例: python3 update_pr_labels_batch.py 10 20  # 11件目から20件を処理")
        return
    
    start = int(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # 分析結果を読み込む
    csv_file = "pr_analysis_final_383.csv"
    print(f"分析結果を読み込み中: {csv_file}")
    
    results = load_analysis_results(csv_file, start, limit)
    print(f"処理対象PR数: {len(results)} (開始位置: {start})")
    
    # 確認
    print(f"\n以下のPRのラベルを更新します:")
    for i, pr in enumerate(results[:5]):  # 最初の5件を表示
        print(f"  PR #{pr['pr_number']}: {pr['old_label']} → {pr['new_label']}")
    if len(results) > 5:
        print(f"  ... 他 {len(results) - 5} 件")
    
    print("\n続行しますか？ (yes/no): ", end="")
    if input().lower() != "yes":
        print("キャンセルしました。")
        return
    
    # ログファイルを準備
    log_file = f"label_update_batch_{start}_{start+len(results)-1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # 処理開始
    print(f"\n処理を開始します...")
    success_count = 0
    error_count = 0
    errors = []
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"ラベル更新ログ - {datetime.now()}\n")
        log.write(f"開始位置: {start}, 処理数: {len(results)}\n\n")
        
        for i, pr in enumerate(results):
            pr_num = pr['pr_number']
            title = pr['title'][:50] + "..." if len(pr['title']) > 50 else pr['title']
            
            print(f"\n[{i+1}/{len(results)}] PR #{pr_num}: {title}")
            print(f"  {pr['old_label']} → {pr['new_label']}")
            
            # ラベル更新実行
            success, message = update_pr_label(pr_num, pr['old_label'], pr['new_label'])
            
            if success:
                success_count += 1
                print(f"  ✓ SUCCESS")
            else:
                error_count += 1
                print(f"  ✗ FAILED: {message}")
                errors.append(f"PR #{pr_num}: {message}")
            
            # ログに記録
            log.write(f"PR #{pr_num}: {pr['old_label']} → {pr['new_label']} - {message}\n")
            
            # レート制限対策
            if i < len(results) - 1:
                time.sleep(1)  # 1秒待機
    
    # 結果サマリー
    print(f"\n=== 処理完了 ===")
    print(f"成功: {success_count}件")
    print(f"失敗: {error_count}件")
    print(f"ログファイル: {log_file}")
    
    if errors:
        print("\n=== エラー一覧 ===")
        for error in errors[:10]:  # 最初の10件のエラーを表示
            print(error)
        if len(errors) > 10:
            print(f"... 他 {len(errors) - 10} 件のエラー")
    
    # 次の処理位置を表示
    next_start = start + len(results)
    print(f"\n次の処理: python3 update_pr_labels_batch.py {next_start} <処理数>")

if __name__ == '__main__':
    main()