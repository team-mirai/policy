#!/usr/bin/env python3
import csv
import glob

# Get all batch CSV files
csv_files = sorted(glob.glob('pr_analysis_batch_*.csv'))

print(f"見つかったCSVファイル: {len(csv_files)}個")
for f in csv_files:
    print(f"  - {f}")

# Combine all CSVs
all_rows = []
header_written = False

with open('pr_analysis_combined_270.csv', 'w', encoding='utf-8-sig', newline='') as outfile:
    writer = csv.writer(outfile)
    
    for csv_file in csv_files:
        with open(csv_file, 'r', encoding='utf-8-sig') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Read header
            
            # Write header only once
            if not header_written:
                writer.writerow(header)
                header_written = True
            
            # Write data rows
            for row in reader:
                writer.writerow(row)
                all_rows.append(row)

print(f"\n統合CSVファイルを作成しました: pr_analysis_combined_270.csv")
print(f"  合計PR数: {len(all_rows)}件")

# Summary by label
label_counts = {}
for row in all_rows:
    label = row[5]  # 政策分野（新ラベル）
    label_counts[label] = label_counts.get(label, 0) + 1

print("\n政策分野別の分類結果:")
for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {label}: {count}件")