#!/usr/bin/env python3
"""
既存の分類結果と新規分類結果を統合して最終CSVを作成
"""
import csv
import os
from datetime import datetime

def main():
    # 読み込むファイル
    existing_file = "all_classified_prs_20250714_230316.csv"
    new_file = None
    
    # 最新のnewly_classified_prs_*.csvを探す
    for filename in sorted(os.listdir('.'), reverse=True):
        if filename.startswith('newly_classified_prs_') and filename.endswith('.csv'):
            new_file = filename
            break
    
    if not new_file:
        print("エラー: newly_classified_prs_*.csv が見つかりません")
        print("先に classify_remaining_prs.py を実行してください")
        return
    
    all_classifications = []
    
    # 既存の分類結果を読み込み
    print(f"既存の分類結果を読み込み中: {existing_file}")
    with open(existing_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        existing_rows = list(reader)
        all_classifications.extend(existing_rows)
        print(f"  {len(existing_rows)}件")
    
    # 新規分類結果を読み込み
    print(f"\n新規分類結果を読み込み中: {new_file}")
    with open(new_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        new_rows = list(reader)
        all_classifications.extend(new_rows)
        print(f"  {len(new_rows)}件")
    
    # PR番号順にソート（降順）
    all_classifications.sort(key=lambda x: int(x['PR番号']), reverse=True)
    
    # 最終CSVファイルを作成
    output_file = f'final_all_513_prs_classified_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_classifications[0].keys())
        writer.writeheader()
        writer.writerows(all_classifications)
    
    print(f"\n統合完了!")
    print(f"  出力ファイル: {output_file}")
    print(f"  総件数: {len(all_classifications)}件")
    
    # ラベル別集計
    label_counts = {}
    for row in all_classifications:
        label = row['政策分野（新ラベル）']
        # リスト形式の場合の処理
        if isinstance(label, list):
            label = label[0] if label else 'その他政策'
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print("\n最終的なラベル別分類結果:")
    print("-" * 50)
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(all_classifications) * 100
        print(f"{label:20} {count:4}件 ({percentage:5.1f}%)")
    print("-" * 50)
    print(f"{'合計':20} {len(all_classifications):4}件 (100.0%)")
    
    # サマリーレポートも作成
    summary_file = f'classification_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("PR分類作業 最終レポート\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
        f.write(f"総PR数: {len(all_classifications)}件\n\n")
        f.write("ラベル別分類結果:\n")
        f.write("-" * 50 + "\n")
        for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(all_classifications) * 100
            f.write(f"{label:20} {count:4}件 ({percentage:5.1f}%)\n")
        f.write("-" * 50 + "\n")
        f.write(f"{'合計':20} {len(all_classifications):4}件 (100.0%)\n")
    
    print(f"\nサマリーレポート: {summary_file}")

if __name__ == "__main__":
    main()