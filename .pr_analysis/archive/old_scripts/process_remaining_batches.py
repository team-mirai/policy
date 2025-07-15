#!/usr/bin/env python3
"""
残りのPRを効率的に処理するスクリプト
"""

import subprocess
import time
from datetime import datetime

def process_remaining_batches():
    """残りのバッチを処理"""
    
    batch_num = 4
    
    while True:
        print(f"\n=== バッチ{batch_num}の処理開始 ===")
        
        # 1. バッチ作成
        print(f"バッチ{batch_num}を作成中...")
        result = subprocess.run(
            ["python3", "get_unanalyzed_batch.py", "50"],
            capture_output=True,
            text=True
        )
        
        if "総未処理PR数: 0" in result.stdout:
            print("すべてのPRの処理が完了しました！")
            break
        
        # バッチファイル名を取得
        batch_file = None
        for line in result.stdout.split('\n'):
            if 'ファイル名: ' in line:
                batch_file = line.split('ファイル名: ')[1].strip()
                break
        
        if not batch_file:
            print("バッチファイルが見つかりません")
            break
        
        print(f"バッチファイル: {batch_file}")
        
        # 2. PR詳細を取得
        print(f"PR詳細を取得中...")
        subprocess.run(
            ["python3", "create_batch_analysis.py", batch_file],
            check=True
        )
        
        # 3. 分析結果ファイル名を特定
        analysis_file = f"analysis_{batch_file.replace('batch_', '').replace('.yaml', '')}.md"
        
        print(f"バッチ{batch_num}の分類を実行します...")
        print(f"（注：LLMによる詳細分析が必要です）")
        
        # 処理時間の記録
        start_time = datetime.now()
        
        # ここで手動分析が必要
        input(f"\nバッチ{batch_num}の分類結果をbatch{batch_num}_classification_results.yamlに保存してください。\n完了したらEnterキーを押してください...")
        
        end_time = datetime.now()
        print(f"バッチ{batch_num}の分析時間: {end_time - start_time}")
        
        batch_num += 1
        
        # API制限を考慮して少し待機
        time.sleep(2)
    
    print("\n=== 全体の処理完了 ===")

if __name__ == "__main__":
    process_remaining_batches()