#!/usr/bin/env python3
"""
修正版：生成したプロンプトをclaude -pで実行して分析を行う
"""

import os
import sys
import argparse
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def run_claude_analysis(prompt_file, output_file, dry_run=False):
    """claude -pコマンドを実行して分析"""
    if dry_run:
        print(f"  [DRY RUN] Would analyze: {prompt_file} -> {output_file}")
        return True
    
    try:
        # 出力ディレクトリを作成
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # claude -pコマンドを実行
        with open(prompt_file, 'r', encoding='utf-8') as f:
            result = subprocess.run(
                ["claude", "-p"],
                stdin=f,
                capture_output=True,
                text=True
            )
        
        if result.returncode != 0:
            print(f"  ❌ Error: {result.stderr}")
            return False
        
        # 結果を保存
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        # 保存したファイルが有効なJSONかチェック
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"  ✅ Valid JSON: {os.path.basename(prompt_file)}")
            return True
        except json.JSONDecodeError:
            print(f"  ⚠️  Invalid JSON output: {os.path.basename(prompt_file)}")
            return False
    
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False

def get_analysis_status(prompts_dir):
    """分析の進捗状況を確認（修正版）"""
    status = {
        'individual': {'total': 0, 'completed': 0, 'files': []},
        'similarity': {'total': 0, 'completed': 0, 'files': []},
        'trend': {'total': 0, 'completed': 0, 'files': []}
    }
    
    for analysis_type in ['individual', 'similarity', 'trend']:
        input_dir = Path(prompts_dir) / analysis_type
        output_dir = Path(prompts_dir) / 'output' / analysis_type
        
        if input_dir.exists():
            input_files = list(input_dir.glob('*.txt'))
            status[analysis_type]['total'] = len(input_files)
            
            for input_file in input_files:
                output_file = output_dir / input_file.with_suffix('.json').name
                if output_file.exists():
                    # ファイルが存在しても、空または無効なJSONの場合はcompletedとしない
                    try:
                        if output_file.stat().st_size > 0:  # 空ファイルでない
                            with open(output_file, 'r', encoding='utf-8') as f:
                                json.load(f)  # 有効なJSONかチェック
                            status[analysis_type]['completed'] += 1
                        else:
                            status[analysis_type]['files'].append(input_file)
                    except (json.JSONDecodeError, Exception):
                        status[analysis_type]['files'].append(input_file)
                else:
                    status[analysis_type]['files'].append(input_file)
    
    return status

def analyze_individual_prs(prompts_dir, sleep_time=2, dry_run=False, resume=True, max_workers=3):
    """個別PR分析を実行（並列処理・修正版）"""
    input_dir = Path(prompts_dir) / 'individual'
    output_dir = Path(prompts_dir) / 'output' / 'individual'
    
    if not input_dir.exists():
        print("❌ Individual prompts directory not found")
        return 0, 0
    
    # プロンプトファイルを取得
    prompt_files = sorted(input_dir.glob('*.txt'))
    
    # 分析が必要なファイルのみを抽出
    files_to_analyze = []
    skipped = 0
    
    for prompt_file in prompt_files:
        output_file = output_dir / prompt_file.with_suffix('.json').name
        if resume and output_file.exists():
            # ファイルが存在しても、空または無効なJSONの場合は再実行対象とする
            try:
                if output_file.stat().st_size > 0:  # 空ファイルでない
                    with open(output_file, 'r', encoding='utf-8') as f:
                        json.load(f)  # 有効なJSONかチェック
                    skipped += 1
                else:
                    files_to_analyze.append((prompt_file, output_file))
            except (json.JSONDecodeError, Exception):
                files_to_analyze.append((prompt_file, output_file))
        else:
            files_to_analyze.append((prompt_file, output_file))
    
    total = len(prompt_files)
    total_to_analyze = len(files_to_analyze)
    
    print(f"\n=== Analyzing Individual PRs ({total} files, {total_to_analyze} remaining) ===")
    print(f"Using {max_workers} parallel workers")
    
    if dry_run:
        for i, (prompt_file, output_file) in enumerate(files_to_analyze):
            print(f"[{i+1}/{total_to_analyze}] Would analyze: {prompt_file.name}")
        return total_to_analyze, skipped
    
    # スレッドセーフなカウンタ
    completed_count = 0
    failed_count = 0
    processed_count = 0
    lock = threading.Lock()
    
    def analyze_single_file(file_info):
        prompt_file, output_file = file_info
        try:
            success = run_claude_analysis(prompt_file, output_file, dry_run=False)
            return prompt_file.name, success, None
        except Exception as e:
            return prompt_file.name, False, str(e)
    
    # 並列実行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # タスクを投入
        future_to_file = {executor.submit(analyze_single_file, file_info): file_info for file_info in files_to_analyze}
        
        # 結果を処理
        for future in as_completed(future_to_file):
            file_info = future_to_file[future]
            prompt_file, output_file = file_info
            
            try:
                filename, success, error = future.result()
                
                with lock:
                    processed_count += 1
                    if success:
                        completed_count += 1
                        print(f"[{processed_count}/{total_to_analyze}] ✅ Success: {filename} (Total success: {completed_count})")
                    else:
                        failed_count += 1
                        error_msg = error if error else "Invalid JSON or empty output"
                        print(f"[{processed_count}/{total_to_analyze}] ❌ Failed: {filename} - {error_msg} (Total failed: {failed_count})")
                        
            except Exception as e:
                with lock:
                    processed_count += 1
                    failed_count += 1
                    print(f"[{processed_count}/{total_to_analyze}] ❌ Exception: {prompt_file.name} - {e}")
            
            # 短いスリープ（API制限対策）
            time.sleep(sleep_time / max_workers)
    
    print(f"\n=== Summary ===")
    print(f"Processed: {processed_count}")
    print(f"Success: {completed_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped (already completed): {skipped}")
    
    return completed_count, skipped

def main():
    parser = argparse.ArgumentParser(description='Analyze prompts using Claude API')
    parser.add_argument('prompts_dir', help='Directory containing prompts')
    parser.add_argument('--type', choices=['individual', 'similarity', 'trend', 'all'], 
                        default='all', help='Type of analysis to run')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--no-resume', action='store_true', help='Re-analyze all files')
    parser.add_argument('--sleep', type=float, default=2, help='Sleep time between analyses (seconds)')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers for individual analysis')
    parser.add_argument('--status', action='store_true', help='Show analysis status and exit')
    
    args = parser.parse_args()
    
    if args.status:
        status = get_analysis_status(args.prompts_dir)
        print("\n=== Analysis Status ===\n")
        for analysis_type, info in status.items():
            print(f"{analysis_type.capitalize()}:")
            print(f"  Total: {info['total']}")
            print(f"  Completed: {info['completed']}")
            print(f"  Remaining: {len(info['files'])}")
            print()
        return
    
    resume = not args.no_resume
    
    if args.type in ['individual', 'all']:
        analyze_individual_prs(args.prompts_dir, args.sleep, args.dry_run, resume, args.workers)
    
    # similarity と trend の処理は元のコードと同じ（省略）

if __name__ == "__main__":
    main()