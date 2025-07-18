#!/usr/bin/env python3
"""
10個まとめて分析するバッチ処理スクリプト
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

def create_multi_prompt(prompt_files):
    """10個のプロンプトを1つにまとめる"""
    multi_prompt = """以下の10個の政策提案PRをそれぞれ分析してください。

重要な指示:
1. 各PRを独立して分析してください
2. 各PRの分析結果は指定されたJSON形式で出力してください
3. 10個のJSON結果を以下の形式で出力してください：

===START_PR_00019===
{JSON結果}
===END_PR_00019===

===START_PR_00036===
{JSON結果}
===END_PR_00036===

という形式で、マークダウンコードブロックは使わず、生のJSONのみを出力してください。

"""
    
    for prompt_file in prompt_files:
        pr_number = prompt_file.stem.replace('pr_', '').replace('_analysis', '')
        multi_prompt += f"\n\n===PROMPT_PR_{pr_number}===\n"
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        multi_prompt += content
        multi_prompt += f"\n===END_PROMPT_PR_{pr_number}===\n"
    
    return multi_prompt

def parse_multi_output(output):
    """複数の出力を個別のJSONに分割"""
    results = {}
    
    # PR番号を抽出するパターン
    import re
    pattern = r'===START_PR_(\d+)===(.*?)===END_PR_\d+==='
    matches = re.findall(pattern, output, re.DOTALL)
    
    for pr_number, json_content in matches:
        json_content = json_content.strip()
        try:
            # JSONとして解析
            data = json.loads(json_content)
            results[f"pr_{pr_number.zfill(5)}"] = data
        except json.JSONDecodeError:
            print(f"  ⚠️  PR {pr_number}: JSONパースエラー")
            results[f"pr_{pr_number.zfill(5)}"] = None
    
    return results

class BatchMultiAnalyzer:
    def __init__(self, prompts_dir, batch_size=10, wait_seconds=30):
        self.prompts_dir = Path(prompts_dir)
        self.batch_size = batch_size
        self.wait_seconds = wait_seconds
        self.progress_file = self.prompts_dir / 'batch_multi_progress.json'
        self.log_file = self.prompts_dir / f'batch_multi_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
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
        return {'completed_batches': [], 'failed_prs': []}
    
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
                pending.append(prompt_file)
        
        return pending
    
    def save_results(self, results):
        """結果を個別のJSONファイルに保存"""
        output_dir = self.prompts_dir / 'output' / 'individual'
        os.makedirs(output_dir, exist_ok=True)
        
        saved_count = 0
        for pr_name, data in results.items():
            if data is not None:
                output_file = output_dir / f"{pr_name}_analysis.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                saved_count += 1
        
        return saved_count
    
    def run_batch(self, batch_files, batch_num):
        """10個まとめてバッチ実行"""
        self.log(f"=== バッチ {batch_num} 開始: {len(batch_files)}個のファイル ===")
        
        # マルチプロンプトを作成
        multi_prompt = create_multi_prompt(batch_files)
        
        # 一時ファイルに保存
        temp_prompt = self.prompts_dir / f'temp_batch_{batch_num}.txt'
        with open(temp_prompt, 'w', encoding='utf-8') as f:
            f.write(multi_prompt)
        
        try:
            # claude -pコマンドを実行
            with open(temp_prompt, 'r', encoding='utf-8') as f:
                result = subprocess.run(
                    ["claude", "-p"],
                    stdin=f,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2分のタイムアウト
                )
            
            if result.returncode == 0 and result.stdout.strip():
                # 結果を解析
                results = parse_multi_output(result.stdout)
                
                # 結果を保存
                saved_count = self.save_results(results)
                self.log(f"  ✅ バッチ {batch_num} 完了: {saved_count}/{len(batch_files)} 個保存")
                
                return saved_count, len(batch_files) - saved_count
            else:
                self.log(f"  ❌ エラー: {result.stderr[:200]}")
                return 0, len(batch_files)
                
        except subprocess.TimeoutExpired:
            self.log(f"  ⏱️  タイムアウト")
            return 0, len(batch_files)
        except Exception as e:
            self.log(f"  ❌ 例外: {e}")
            return 0, len(batch_files)
        finally:
            # 一時ファイルを削除
            if temp_prompt.exists():
                temp_prompt.unlink()
    
    def run(self):
        """バッチ処理を実行"""
        self.log("=== マルチバッチ分析開始 ===")
        
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
        
        # 推定時間
        total_time = len(batches) * self.wait_seconds
        self.log(f"推定実行時間: {total_time // 60}分 {total_time % 60}秒")
        
        # 各バッチを実行
        total_success = 0
        total_failed = 0
        
        for batch_num, batch_files in enumerate(batches, 1):
            # すでに完了したバッチはスキップ
            if batch_num in progress['completed_batches']:
                self.log(f"バッチ {batch_num} はすでに完了しています")
                continue
            
            success, failed = self.run_batch(batch_files, batch_num)
            total_success += success
            total_failed += failed
            
            # 進捗を保存
            progress['completed_batches'].append(batch_num)
            self.save_progress(progress)
            
            # 次のバッチまで待機（最後のバッチ以外）
            if batch_num < len(batches):
                self.log(f"待機中... ({self.wait_seconds}秒)")
                time.sleep(self.wait_seconds)
        
        # 最終結果
        self.log("=== マルチバッチ分析完了 ===")
        self.log(f"成功: {total_success}個")
        self.log(f"失敗: {total_failed}個")

def main():
    parser = argparse.ArgumentParser(description='10個まとめて分析するバッチ処理')
    parser.add_argument('prompts_dir', help='プロンプトディレクトリ')
    parser.add_argument('--batch-size', type=int, default=10, 
                        help='バッチサイズ (default: 10)')
    parser.add_argument('--wait-seconds', type=int, default=30,
                        help='バッチ間の待機時間（秒） (default: 30)')
    
    args = parser.parse_args()
    
    analyzer = BatchMultiAnalyzer(
        args.prompts_dir,
        batch_size=args.batch_size,
        wait_seconds=args.wait_seconds
    )
    
    analyzer.run()

if __name__ == "__main__":
    main()