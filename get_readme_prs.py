#!/usr/bin/env python3
"""READMEラベル付きPRの詳細情報を取得するスクリプト"""

import json
import subprocess
import sys
from datetime import datetime

def get_readme_prs():
    """READMEラベル付きのPRリストを取得"""
    cmd = [
        "gh", "pr", "list",
        "--repo", "team-mirai/policy",
        "--label", "README",
        "--limit", "1000",
        "--json", "number,title,author,createdAt,state,labels,url,body"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PRs: {e}")
        sys.exit(1)

def format_pr_data(prs):
    """PR情報を整形"""
    formatted_prs = []
    
    for pr in prs:
        # 作成者名の取得
        author = pr['author']['login'] if pr['author'] else 'Unknown'
        
        # ラベル名のリスト
        labels = [label['name'] for label in pr.get('labels', [])]
        
        # 日付のフォーマット
        created_date = pr['createdAt'][:10] if pr['createdAt'] else ''
        
        # 本文の要約（最初の200文字）
        body = pr.get('body', '')
        summary = body[:200] + '...' if len(body) > 200 else body
        summary = summary.replace('\n', ' ').replace('\r', '')
        
        formatted_prs.append({
            'number': pr['number'],
            'title': pr['title'],
            'author': author,
            'created_at': created_date,
            'state': pr['state'],
            'labels': labels,
            'url': pr['url'],
            'body': body,
            'summary': summary
        })
    
    return formatted_prs

def save_to_json(data, filename):
    """データをJSONファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    print("READMEラベル付きPRを取得中...")
    prs = get_readme_prs()
    print(f"取得したPR数: {len(prs)}")
    
    print("データを整形中...")
    formatted_prs = format_pr_data(prs)
    
    # JSONファイルに保存
    output_file = 'readme_prs_data.json'
    save_to_json(formatted_prs, output_file)
    print(f"データを {output_file} に保存しました")
    
    # 最初の5件を表示
    print("\n最初の5件のPR:")
    for i, pr in enumerate(formatted_prs[:5]):
        print(f"\n{i+1}. PR #{pr['number']}: {pr['title']}")
        print(f"   作成者: {pr['author']}, 作成日: {pr['created_at']}")
        print(f"   ステータス: {pr['state']}")
        print(f"   URL: {pr['url']}")

if __name__ == '__main__':
    main()