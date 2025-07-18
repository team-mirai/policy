#!/usr/bin/env python3
"""
Rate limit対策付きバッチ分析スクリプト
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import argparse

class BatchAnalyzer:
    def __init__(self, prompts_dir, batch_size=50, wait_minutes=5, max_retries=3):
        self.prompts_dir = Path(prompts_dir)
        self.batch_size = batch_size
        self.wait_seconds = wait_minutes * 60
        self.max_retries = max_retries
        self.progress_file = self.prompts_dir / 'batch_progress.json'
        self.log_file = self.prompts_dir / f'batch_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
    def log(self, message):
        """ログを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{timestamp}] {message}"
        print(msg)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    
    def load_progress(self):
        """進捗を読み込む"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'completed_batches': [], 'failed_files': []}
    
    def save_progress(self, progress):
        """進捗を保存"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_pending_files(self):
        """処理が必要なファイルを取得"""
        input_dir = self.prompts_dir / 'individual'
        output_dir = self.prompts_dir / 'output' / 'individual'
        
        pending = []
        for prompt_file in sorted(input_dir.glob('*.txt')):
            output_file = output_dir / prompt_file.with_suffix('.json').name
            
            # 空ファイルまたは無効なJSONは再実行対象
            needs_processing = False
            if not output_file.exists():
                needs_processing = True
            else:
                try:
                    if output_file.stat().st_size == 0:
                        needs_processing = True
                    else:
                        with open(output_file, 'r', encoding='utf-8') as f:
                            json.load(f)
                except:
                    needs_processing = True
            
            if needs_processing:
                pending.append(str(prompt_file))
        
        return pending
    
    def run_batch(self, files, batch_num):
        """バッチを実行"""
        self.log(f"=== バッチ {batch_num} 開始: {len(files)}個のファイル ===")
        
        success_count = 0
        failed_files = []
        
        for i, file_path in enumerate(files, 1):
            output_file = self.prompts_dir / 'output' / 'individual' / Path(file_path).with_suffix('.json').name
            
            # claude -pコマンドを実行
            for retry in range(self.max_retries):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        result = subprocess.run(
                            ["claude", "-p"],
                            stdin=f,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        # 結果を保存
                        os.makedirs(output_file.parent, exist_ok=True)
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(result.stdout)
                        
                        # 有効なJSONかチェック
                        try:
                            with open(output_file, 'r', encoding='utf-8') as f:
                                json.load(f)
                            success_count += 1
                            self.log(f"  [{i}/{len(files)}] ✅ {Path(file_path).name}")
                            break
                        except:
                            self.log(f"  [{i}/{len(files)}] ⚠️  Invalid JSON: {Path(file_path).name}")
                            if retry < self.max_retries - 1:
                                time.sleep(5)
                                continue
                    else:
                        if "rate limit" in result.stderr.lower():
                            self.log(f"  ❌ Rate limit detected! Waiting longer...")
                            time.sleep(60)  # 1分待機
                        else:
                            self.log(f"  [{i}/{len(files)}] ❌ Error: {result.stderr[:100]}")
                        
                        if retry < self.max_retries - 1:
                            time.sleep(10)
                            continue
                        else:
                            failed_files.append(file_path)
                            
                except subprocess.TimeoutExpired:
                    self.log(f"  [{i}/{len(files)}] ⏱️  Timeout")
                    failed_files.append(file_path)
                except Exception as e:
                    self.log(f"  [{i}/{len(files)}] ❌ Exception: {e}")
                    failed_files.append(file_path)
            
            # 個別ファイル間の待機（rate limit対策）
            if i < len(files):
                time.sleep(3)
        
        self.log(f"バッチ {batch_num} 完了: 成功 {success_count}/{len(files)}")
        return success_count, failed_files
    
    def run(self):
        """バッチ処理を実行"""
        self.log("=== バッチ分析開始 ===")
        
        # 進捗を読み込む
        progress = self.load_progress()
        
        # 処理が必要なファイルを取得
        pending_files = self.get_pending_files()
        self.log(f"処理対象: {len(pending_files)}個のファイル")
        
        if not pending_files:
            self.log("処理が必要なファイルはありません")
            return
        
        # バッチに分割
        batches = []
        for i in range(0, len(pending_files), self.batch_size):
            batch = pending_files[i:i + self.batch_size]
            batches.append(batch)
        
        self.log(f"バッチ数: {len(batches)} (各{self.batch_size}個まで)")
        
        # 各バッチを実行
        total_success = 0
        all_failed = []
        
        for batch_num, batch_files in enumerate(batches, 1):
            # すでに完了したバッチはスキップ
            if batch_num in progress['completed_batches']:
                self.log(f"バッチ {batch_num} はすでに完了しています")
                continue
            
            success, failed = self.run_batch(batch_files, batch_num)
            total_success += success
            all_failed.extend(failed)
            
            # 進捗を保存
            progress['completed_batches'].append(batch_num)
            progress['failed_files'] = all_failed
            self.save_progress(progress)
            
            # 次のバッチまで待機（最後のバッチ以外）
            if batch_num < len(batches):
                next_time = datetime.now() + timedelta(seconds=self.wait_seconds)
                self.log(f"次のバッチは {next_time.strftime('%H:%M:%S')} に開始します")
                self.log(f"待機中... ({self.wait_seconds}秒)")
                time.sleep(self.wait_seconds)
        
        # 最終結果
        self.log("=== バッチ分析完了 ===")
        self.log(f"成功: {total_success}個")
        self.log(f"失敗: {len(all_failed)}個")
        
        if all_failed:
            self.log("\n失敗したファイル:")
            for f in all_failed[:10]:
                self.log(f"  - {Path(f).name}")
            if len(all_failed) > 10:
                self.log(f"  ... 他 {len(all_failed) - 10}個")

def main():
    parser = argparse.ArgumentParser(description='Rate limit対策付きバッチ分析')
    parser.add_argument('prompts_dir', help='プロンプトディレクトリ')
    parser.add_argument('--batch-size', type=int, default=50, 
                        help='バッチサイズ (default: 50)')
    parser.add_argument('--wait-minutes', type=int, default=5,
                        help='バッチ間の待機時間（分） (default: 5)')
    parser.add_argument('--max-retries', type=int, default=3,
                        help='最大リトライ回数 (default: 3)')
    
    args = parser.parse_args()
    
    analyzer = BatchAnalyzer(
        args.prompts_dir,
        batch_size=args.batch_size,
        wait_minutes=args.wait_minutes,
        max_retries=args.max_retries
    )
    
    analyzer.run()

if __name__ == "__main__":
    main()