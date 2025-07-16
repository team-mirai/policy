#!/usr/bin/env python3
"""
PR分析結果に基づいてGitHub上のラベルを更新するスクリプト
"""

import csv
import subprocess
import time
import sys
import argparse
from datetime import datetime
import os

def update_github_labels(pr_number, new_label, remove_label='README'):
    """GitHub上のPRラベルを更新"""
    
    success = True
    error_messages = []
    
    # READMEラベルを削除（エラーがあっても続行）
    if remove_label:
        print(f"  Removing label '{remove_label}'...", end='', flush=True)
        cmd_remove = [
            "gh", "pr", "edit", str(pr_number),
            "--repo", "team-mirai/policy",
            "--remove-label", remove_label
        ]
        
        try:
            result = subprocess.run(cmd_remove, capture_output=True, text=True, check=True)
            print(" ✓")
        except subprocess.CalledProcessError as e:
            # ラベルが既に存在しない場合もエラーになるが、それは問題ない
            if "does not have label" in e.stderr:
                print(" ✓ (already removed)")
            else:
                print(f" ✗ Error: {e.stderr.strip()}")
                error_messages.append(f"Remove label error: {e.stderr.strip()}")
    
    # 新しいラベルを追加
    if new_label:
        print(f"  Adding label '{new_label}'...", end='', flush=True)
        cmd_add = [
            "gh", "pr", "edit", str(pr_number),
            "--repo", "team-mirai/policy",
            "--add-label", new_label
        ]
        
        try:
            result = subprocess.run(cmd_add, capture_output=True, text=True, check=True)
            print(" ✓")
        except subprocess.CalledProcessError as e:
            # ラベルが既に存在する場合もエラーになるが、それは問題ない
            if "already has label" in e.stderr:
                print(" ✓ (already added)")
            else:
                print(f" ✗ Error: {e.stderr.strip()}")
                error_messages.append(f"Add label error: {e.stderr.strip()}")
                success = False
    
    return success, error_messages

def load_pr_data(csv_file):
    """CSVファイルからPRデータを読み込み"""
    prs = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['政策分野（新ラベル）'] and row['政策分野（新ラベル）'].strip():
                prs.append({
                    'number': int(row['PR番号']),
                    'title': row['タイトル'],
                    'new_label': row['政策分野（新ラベル）'],
                    'status': row.get('ステータス', 'OPEN'),
                    'url': row.get('URL', '')
                })
    return prs

def save_progress(progress_file, processed_prs):
    """進捗を保存"""
    with open(progress_file, 'w') as f:
        for pr_num in sorted(processed_prs):
            f.write(f"{pr_num}\n")

def load_progress(progress_file):
    """進捗を読み込み"""
    if not os.path.exists(progress_file):
        return set()
    
    processed = set()
    with open(progress_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                processed.add(int(line))
    return processed

def main():
    parser = argparse.ArgumentParser(description='PR分析結果に基づいてGitHubラベルを更新')
    parser.add_argument('-i', '--input', default='complete_513_prs_analysis.csv', 
                        help='入力CSVファイル（デフォルト: complete_513_prs_analysis.csv）')
    parser.add_argument('-l', '--limit', type=int, help='更新するPR数の上限')
    parser.add_argument('--dry-run', action='store_true', help='実行せずに確認のみ')
    parser.add_argument('--resume', action='store_true', help='前回の続きから実行')
    parser.add_argument('--open-only', action='store_true', help='OPENのPRのみ更新')
    parser.add_argument('-s', '--sleep', type=float, default=0.5, 
                        help='API呼び出し間隔（秒、デフォルト: 0.5）')
    
    args = parser.parse_args()
    
    # 入力ファイルチェック
    if not os.path.exists(args.input):
        print(f"エラー: 入力ファイル '{args.input}' が見つかりません")
        return 1
    
    # PRデータ読み込み
    print(f"入力ファイル: {args.input}")
    all_prs = load_pr_data(args.input)
    
    # フィルタリング
    if args.open_only:
        prs = [pr for pr in all_prs if pr['status'] == 'OPEN']
        print(f"OPENのPRのみ対象: {len(prs)}/{len(all_prs)}件")
    else:
        prs = all_prs
    
    # 進捗管理
    progress_file = f"{args.input}.progress"
    processed_prs = set()
    
    if args.resume:
        processed_prs = load_progress(progress_file)
        print(f"再開モード: {len(processed_prs)}件の処理済みPRをスキップ")
        prs = [pr for pr in prs if pr['number'] not in processed_prs]
    
    # 制限適用
    if args.limit:
        prs = prs[:args.limit]
    
    print(f"\n=== ラベル更新対象 ===")
    print(f"更新対象: {len(prs)}件")
    
    # ドライラン
    if args.dry_run:
        print("\n[DRY RUN MODE - 実際の更新は行いません]\n")
        for i, pr in enumerate(prs[:10]):  # 最初の10件だけ表示
            print(f"{i+1}. PR #{pr['number']}: {pr['title'][:50]}...")
            print(f"   {pr.get('old_label', 'README')} → {pr['new_label']}")
        if len(prs) > 10:
            print(f"\n... 他 {len(prs) - 10}件")
        return 0
    
    # 確認
    if len(prs) > 0:
        response = input(f"\n{len(prs)}件のPRのラベルを更新します。続行しますか？ (y/N): ")
        if response.lower() != 'y':
            print("キャンセルしました")
            return 0
    else:
        print("更新対象のPRがありません")
        return 0
    
    # 更新実行
    print("\n=== 更新開始 ===")
    success_count = 0
    failed_prs = []
    start_time = time.time()
    
    for i, pr in enumerate(prs):
        # 進捗表示
        elapsed = time.time() - start_time
        eta = elapsed / (i + 1) * len(prs) - elapsed if i > 0 else 0
        
        print(f"\n[{i+1}/{len(prs)}] PR #{pr['number']}: {pr['title'][:50]}...")
        print(f"  経過: {elapsed/60:.1f}分, 残り: {eta/60:.1f}分")
        
        success, errors = update_github_labels(pr['number'], pr['new_label'])
        
        if success:
            success_count += 1
            processed_prs.add(pr['number'])
            # 進捗を保存
            if args.resume:
                save_progress(progress_file, processed_prs)
        else:
            failed_prs.append({
                'number': pr['number'],
                'title': pr['title'],
                'errors': errors
            })
        
        # API制限対策
        if i < len(prs) - 1:
            time.sleep(args.sleep)
    
    # 結果サマリー
    total_time = time.time() - start_time
    print(f"\n=== 更新完了 ===")
    print(f"成功: {success_count}件")
    print(f"失敗: {len(failed_prs)}件")
    print(f"処理時間: {total_time/60:.1f}分")
    
    if failed_prs:
        print(f"\n失敗したPR:")
        for pr in failed_prs[:10]:  # 最初の10件だけ表示
            print(f"  PR #{pr['number']}: {pr['title'][:40]}...")
            for error in pr['errors']:
                print(f"    - {error}")
        if len(failed_prs) > 10:
            print(f"  ... 他 {len(failed_prs) - 10}件")
    
    # 進捗ファイルのクリーンアップ
    if args.resume and success_count == len(prs):
        os.remove(progress_file)
        print(f"\n進捗ファイルを削除しました: {progress_file}")
    
    # 政策分野別の集計
    label_counts = {}
    for pr in all_prs:
        label = pr['new_label']
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print(f"\n=== 政策分野別分布 ===")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = count / len(all_prs) * 100
        print(f"  {label}: {count}件 ({percentage:.1f}%)")
    
    return 0

if __name__ == "__main__":
    exit(main())