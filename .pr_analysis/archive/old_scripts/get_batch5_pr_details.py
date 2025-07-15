#!/usr/bin/env python3
import subprocess
import json
import yaml
import time
from datetime import datetime

# Load batch 5 data
with open('batch5_20250714_2239.yaml', 'r', encoding='utf-8') as f:
    batch_data = yaml.safe_load(f)

# Extract PR numbers
pr_numbers = [pr['number'] for pr in batch_data['pull_requests']]

print(f"バッチ5のPR詳細を取得します: {len(pr_numbers)}件")

# Create analysis file
analysis_filename = f"analysis_batch5_{datetime.now().strftime('%Y%m%d_%H%M')}.md"

with open(analysis_filename, 'w', encoding='utf-8') as f:
    f.write(f"# PR分析バッチ5 - {datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n\n")
    f.write(f"## 分析対象: {len(pr_numbers)}件\n\n")
    f.write("## 政策分野ラベル一覧\n\n")
    f.write("1. **ビジョン** - 政治理念、基本方針\n")
    f.write("2. **デジタル民主主義** - 透明性、参加型政治、オープンガバメント\n")
    f.write("3. **行政改革** - 行政効率化、デジタル化、規制改革\n")
    f.write("4. **教育** - 教育制度、学習支援\n")
    f.write("5. **福祉** - 社会保障、高齢者・障害者支援\n")
    f.write("6. **子育て** - 少子化対策、育児支援\n")
    f.write("7. **医療** - 医療制度、健康政策\n")
    f.write("8. **経済財政** - 税制、財政政策、経済政策\n")
    f.write("9. **産業政策** - 産業振興、技術革新、雇用\n")
    f.write("10. **科学技術** - 研究開発、イノベーション\n")
    f.write("11. **エネルギー** - エネルギー政策、環境\n")
    f.write("12. **その他政策** - 上記に該当しない政策\n")
    f.write("13. **[システム]** - README更新、システム改善\n\n")
    f.write("---\n\n")

    # Get details for each PR
    for i, pr_num in enumerate(pr_numbers):
        print(f"処理中 {i+1}/{len(pr_numbers)}: PR #{pr_num}")
        
        # Find PR in batch data
        pr_info = next(pr for pr in batch_data['pull_requests'] if pr['number'] == pr_num)
        
        f.write(f"## PR #{pr_num}: {pr_info['title']}\n\n")
        f.write(f"- **作成者**: {pr_info['author']}\n")
        f.write(f"- **作成日**: {pr_info['created_at']}\n")
        f.write(f"- **URL**: {pr_info['url']}\n\n")
        
        # Get PR body
        try:
            body_cmd = ["gh", "pr", "view", str(pr_num), "--repo", "team-mirai/policy", "--json", "body"]
            body_result = subprocess.run(body_cmd, capture_output=True, text=True)
            if body_result.returncode == 0:
                body_data = json.loads(body_result.stdout)
                f.write("### PR本文\n")
                f.write(body_data['body'] + "\n\n")
            else:
                f.write("### PR本文\n")
                f.write("（取得エラー）\n\n")
        except Exception as e:
            print(f"  PR本文取得エラー: {e}")
            f.write("### PR本文\n")
            f.write("（取得エラー）\n\n")
        
        # Get diff
        try:
            diff_cmd = ["gh", "pr", "diff", str(pr_num), "--repo", "team-mirai/policy"]
            diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
            if diff_result.returncode == 0:
                f.write("### 差分内容\n")
                f.write("```diff\n")
                # Limit diff to first 100 lines to avoid too large files
                diff_lines = diff_result.stdout.split('\n')[:100]
                f.write('\n'.join(diff_lines))
                if len(diff_result.stdout.split('\n')) > 100:
                    f.write("\n\n... (差分が大きいため省略)")
                f.write("\n```\n\n")
            else:
                f.write("### 差分内容\n")
                f.write("（取得エラー）\n\n")
        except Exception as e:
            print(f"  差分取得エラー: {e}")
            f.write("### 差分内容\n")
            f.write("（取得エラー）\n\n")
        
        f.write("---\n\n")
        
        # Brief pause to avoid rate limits
        if i < len(pr_numbers) - 1:
            time.sleep(0.5)

print(f"\n分析ファイルを作成しました: {analysis_filename}")
print(f"収集したPR数: {len(pr_numbers)}件")