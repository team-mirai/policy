#!/usr/bin/env python3
"""
バッチのPR詳細を取得し、分析用のMarkdownファイルを作成するスクリプト
"""

import yaml
import subprocess
import json
import sys
from datetime import datetime

def load_yaml(filename):
    """YAMLファイルを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_pr_details(pr_number):
    """GitHub CLIを使用してPRの詳細を取得"""
    cmd = [
        "gh", "pr", "view", str(pr_number),
        "--repo", "team-mirai/policy",
        "--json", "number,title,body,author,createdAt,url,additions,deletions,files"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR #{pr_number}: {e}")
        return None

def get_pr_diff(pr_number):
    """PRの差分を取得"""
    cmd = [
        "gh", "pr", "diff", str(pr_number),
        "--repo", "team-mirai/policy"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching diff for PR #{pr_number}: {e}")
        return None

def create_analysis_markdown(batch_file):
    """バッチファイルからPR詳細を取得し、分析用Markdownを作成"""
    
    # バッチファイルを読み込む
    batch_data = load_yaml(batch_file)
    prs = batch_data['pull_requests']
    
    # Markdownファイルの内容を構築
    md_content = f"# PR分析バッチ - {datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n\n"
    md_content += f"## 分析対象: {len(prs)}件\n\n"
    md_content += "## 政策分野ラベル一覧\n\n"
    md_content += "1. **ビジョン** - 政治理念、基本方針\n"
    md_content += "2. **デジタル民主主義** - 透明性、参加型政治、オープンガバメント\n"
    md_content += "3. **行政改革** - 行政効率化、デジタル化、規制改革\n"
    md_content += "4. **教育** - 教育制度、学習支援\n"
    md_content += "5. **福祉** - 社会保障、高齢者・障害者支援\n"
    md_content += "6. **子育て** - 少子化対策、育児支援\n"
    md_content += "7. **医療** - 医療制度、健康政策\n"
    md_content += "8. **経済財政** - 税制、財政政策、経済政策\n"
    md_content += "9. **産業政策** - 産業振興、技術革新、雇用\n"
    md_content += "10. **科学技術** - 研究開発、イノベーション\n"
    md_content += "11. **エネルギー** - エネルギー政策、環境\n"
    md_content += "12. **その他政策** - 上記に該当しない政策\n"
    md_content += "13. **[システム]** - README更新、システム改善\n\n"
    md_content += "---\n\n"
    
    # 各PRの詳細を追加
    for i, pr in enumerate(prs):
        print(f"Fetching PR #{pr['number']} ({i+1}/{len(prs)})...")
        
        md_content += f"## PR #{pr['number']}: {pr['title']}\n\n"
        md_content += f"- **作成者**: {pr['author']}\n"
        md_content += f"- **作成日**: {pr['created_at']}\n"
        md_content += f"- **URL**: {pr['url']}\n\n"
        
        # PR詳細を取得
        details = get_pr_details(pr['number'])
        if details and details.get('body'):
            md_content += "### PR本文\n"
            md_content += f"{details['body'][:2000]}{'...(省略)' if len(details.get('body', '')) > 2000 else ''}\n\n"
        
        # 差分を取得（最初の500行まで）
        diff = get_pr_diff(pr['number'])
        if diff:
            diff_lines = diff.split('\n')[:500]
            md_content += "### 差分内容\n"
            md_content += "```diff\n"
            md_content += '\n'.join(diff_lines)
            if len(diff.split('\n')) > 500:
                md_content += "\n... (省略)"
            md_content += "\n```\n\n"
        
        md_content += "### 分析結果\n"
        md_content += "**推奨ラベル**: \n"
        md_content += "**理由**: \n\n"
        md_content += "---\n\n"
    
    # ファイルに保存
    output_file = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"\n分析用ファイルを作成しました: {output_file}")
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_batch_analysis.py <batch_file.yaml>")
        sys.exit(1)
    
    create_analysis_markdown(sys.argv[1])