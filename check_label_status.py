#!/usr/bin/env python3
"""ラベル更新の進捗を確認"""

import subprocess
import json

# READMEラベル付きPRを取得
cmd = ["gh", "pr", "list", "--repo", "team-mirai/policy", "--label", "README", "--limit", "1000", "--json", "number,labels"]
result = subprocess.run(cmd, capture_output=True, text=True)
prs_with_readme = json.loads(result.stdout)

# 各政策ラベル付きPRを取得
policy_labels = [
    "ビジョン", "デジタル民主主義", "行政改革", "教育", "福祉", 
    "子育て", "医療", "経済財政", "産業政策", "科学技術", 
    "エネルギー", "その他政策", "[システム]"
]

total_updated = 0
for label in policy_labels:
    cmd = ["gh", "pr", "list", "--repo", "team-mirai/policy", "--label", label, "--limit", "100", "--json", "number"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    count = len(json.loads(result.stdout))
    if count > 0:
        print(f"{label}: {count}件")
        total_updated += count

print(f"\n=== 進捗状況 ===")
print(f"READMEラベル付きPR: {len(prs_with_readme)}件")
print(f"政策ラベル付きPR: {total_updated}件")
print(f"処理済み: {383 - len(prs_with_readme)}件")
print(f"未処理: {len(prs_with_readme)}件")