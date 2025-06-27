#!/usr/bin/env python3
import yaml

with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# 分析が必要なPRの条件を確認
unanalyzed = []
for pr in data['pull_requests']:
    # label_updated が False で、かつ new_label が設定されていない（None または存在しない）
    if (pr.get('label_updated') == False and
            ('new_label' not in pr or pr.get('new_label') is None)):
        unanalyzed.append(pr)

print(f"未分析PR数: {len(unanalyzed)}")

# 最初の20件を表示
print("\n未分析の最初の20件:")
for i, pr in enumerate(unanalyzed[:20]):
    print(f"PR #{pr['number']}: {pr['title']}")

# PR番号のリストを出力
pr_numbers = [pr['number'] for pr in unanalyzed[:20]]
print(f"\nPR番号リスト: {pr_numbers}")

# 全体の統計
total_prs = len(data['pull_requests'])
label_updated_false = sum(
    1 for pr in data['pull_requests'] if pr.get('label_updated') == False)
print(f"\n統計:")
print(f"総PR数: {total_prs}")
print(f"label_updated: false の数: {label_updated_false}")
print(f"未分析PR数: {len(unanalyzed)}")
print(f"分析済みPR数: {label_updated_false - len(unanalyzed)}")
