#!/usr/bin/env python3
"""全ての残りのREADMEラベル付きPRを処理（ログ付き）"""

import subprocess
import json
import csv
import time
import sys
from datetime import datetime

def get_remaining_prs():
    """READMEラベル付きPRを取得"""
    cmd = ["gh", "pr", "list", "--repo", "team-mirai/policy", "--label", "README", 
           "--limit", "1000", "--json", "number,title"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def load_analysis_results():
    """分析結果を読み込む"""
    analysis = {}
    with open('pr_analysis_final_383.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            analysis[row['PR番号']] = row['政策分野（新ラベル）']
    return analysis

def log_print(msg):
    """即座に出力とフラッシュ"""
    print(msg)
    sys.stdout.flush()

def main():
    log_print(f"処理開始: {datetime.now()}")
    
    # 残りのPRを取得
    remaining_prs = get_remaining_prs()
    total_count = len(remaining_prs)
    log_print(f"残りのPR数: {total_count}")
    
    # 分析結果を読み込む
    analysis = load_analysis_results()
    
    success_count = 0
    error_count = 0
    
    # ログファイルも作成
    with open('update_detailed.log', 'w') as logfile:
        logfile.write(f"開始時刻: {datetime.now()}\n")
        logfile.write(f"総PR数: {total_count}\n\n")
        logfile.flush()
        
        for i, pr in enumerate(remaining_prs):
            pr_num = str(pr['number'])
            
            # 分析結果から新ラベルを取得
            if pr_num not in analysis:
                msg = f"[{i+1}/{total_count}] PR #{pr_num}: 分析結果なし - スキップ"
                log_print(msg)
                logfile.write(msg + "\n")
                logfile.flush()
                continue
            
            new_label = analysis[pr_num]
            msg = f"[{i+1}/{total_count}] PR #{pr_num}: README → {new_label}"
            log_print(msg)
            logfile.write(msg + "\n")
            
            # READMEラベルを削除して新ラベルを追加
            cmd = [
                "gh", "pr", "edit", pr_num, 
                "--repo", "team-mirai/policy",
                "--remove-label", "README",
                "--add-label", new_label
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success_count += 1
                msg = f"  ✓ 成功"
                log_print(msg)
                logfile.write(msg + "\n")
            else:
                error_count += 1
                msg = f"  ✗ 失敗: {result.stderr}"
                log_print(msg)
                logfile.write(msg + "\n")
            
            logfile.flush()
            
            # 適切な間隔で実行
            time.sleep(0.5)
            
            # 25件ごとに進捗表示
            if (i + 1) % 25 == 0:
                progress_msg = f"\n--- 進捗: {i+1}/{total_count} ({success_count}成功, {error_count}失敗) ---\n"
                log_print(progress_msg)
                logfile.write(progress_msg + "\n")
                logfile.flush()
    
    summary = f"\n=== 処理完了 ===\n"
    summary += f"終了時刻: {datetime.now()}\n"
    summary += f"総数: {total_count}件\n"
    summary += f"成功: {success_count}件\n"
    summary += f"失敗: {error_count}件\n"
    summary += f"成功率: {success_count/total_count*100:.1f}%"
    
    log_print(summary)
    
    with open('update_detailed.log', 'a') as logfile:
        logfile.write(summary)

if __name__ == '__main__':
    main()