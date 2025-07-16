#!/usr/bin/env python3
"""
GitHub APIを使用して指定されたラベルのPRデータを取得する
"""

import json
import subprocess
import os
import argparse
from datetime import datetime
from pathlib import Path
import time

def ensure_cache_dir(cache_dir="cache"):
    """キャッシュディレクトリを作成"""
    Path(cache_dir).mkdir(exist_ok=True)

def get_cached_data(cache_file):
    """キャッシュファイルからデータを読み込む"""
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_to_cache(data, cache_file):
    """データをキャッシュファイルに保存"""
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_gh_command(args, check=True):
    """GitHub CLIコマンドを実行"""
    cmd = ["gh"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
        return None
    return result.stdout

def get_pr_list(label, state="open", limit=1000):
    """指定されたラベルのPRリストを取得"""
    print(f"Fetching {state} PRs with label '{label}'...")
    
    args = [
        "pr", "list",
        "--repo", "team-mirai/policy",
        "--label", label,
        "--state", state,
        "--limit", str(limit),
        "--json", "number,title,author,createdAt,updatedAt,state,url,labels,isDraft,milestone"
    ]
    
    result = run_gh_command(args)
    if result:
        prs = json.loads(result)
        print(f"Found {len(prs)} PRs")
        return prs
    return []

def get_pr_details(pr_number, cache_dir="cache"):
    """PR詳細情報を取得（キャッシュ付き）"""
    cache_file = f"{cache_dir}/pr_{pr_number}_details.json"
    
    # キャッシュチェック
    cached_data = get_cached_data(cache_file)
    if cached_data:
        return cached_data
    
    # PR詳細を取得
    args = [
        "pr", "view", str(pr_number),
        "--repo", "team-mirai/policy",
        "--json", "number,title,body,author,createdAt,updatedAt,state,url,labels,comments,reactions,files,additions,deletions,changedFiles,mergeable,merged,mergedAt,milestone,assignees"
    ]
    
    result = run_gh_command(args)
    if not result:
        return None
    
    pr_data = json.loads(result)
    
    # コメント数の取得（comments配列の長さ）
    pr_data['commentsCount'] = len(pr_data.get('comments', []))
    
    # リアクション数の集計
    reactions = pr_data.get('reactions', {})
    total_reactions = sum([
        reactions.get('+1', 0),
        reactions.get('-1', 0),
        reactions.get('laugh', 0),
        reactions.get('hooray', 0),
        reactions.get('confused', 0),
        reactions.get('heart', 0),
        reactions.get('rocket', 0),
        reactions.get('eyes', 0)
    ])
    pr_data['totalReactions'] = total_reactions
    
    # キャッシュに保存
    save_to_cache(pr_data, cache_file)
    
    return pr_data

def get_pr_diff(pr_number, cache_dir="cache", max_lines=1000):
    """PR差分を取得（キャッシュ付き）"""
    cache_file = f"{cache_dir}/pr_{pr_number}_diff.txt"
    
    # キャッシュチェック
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # diffを取得
    args = ["pr", "diff", str(pr_number), "--repo", "team-mirai/policy"]
    result = run_gh_command(args, check=False)
    
    if result:
        # 大きすぎるdiffは制限
        lines = result.split('\n')
        if len(lines) > max_lines:
            diff = '\n'.join(lines[:max_lines]) + f"\n... (truncated at {max_lines} lines)"
        else:
            diff = result
        
        # キャッシュに保存
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(diff)
        
        return diff
    
    return ""

def fetch_all_pr_data(label, state="open", limit=None, output_file=None):
    """すべてのPRデータを取得して統合"""
    ensure_cache_dir()
    
    # PRリストを取得
    pr_list = get_pr_list(label, state, limit or 1000)
    
    if limit:
        pr_list = pr_list[:limit]
        print(f"Limited to {limit} PRs")
    
    # 詳細データを収集
    all_pr_data = []
    total = len(pr_list)
    
    for i, pr in enumerate(pr_list):
        pr_number = pr['number']
        print(f"\nProcessing PR #{pr_number} ({i+1}/{total}): {pr['title'][:50]}...")
        
        # 詳細情報を取得
        details = get_pr_details(pr_number)
        if not details:
            print(f"  ⚠ Failed to get details for PR #{pr_number}")
            continue
        
        # diffを取得
        diff = get_pr_diff(pr_number)
        details['diff'] = diff
        details['diffLines'] = len(diff.split('\n'))
        
        # 統計情報を追加
        details['statistics'] = {
            'commentsCount': details.get('commentsCount', 0),
            'totalReactions': details.get('totalReactions', 0),
            'filesChanged': details.get('changedFiles', 0),
            'additions': details.get('additions', 0),
            'deletions': details.get('deletions', 0),
            'diffLines': details['diffLines']
        }
        
        all_pr_data.append(details)
        
        # レート制限対策
        if i < total - 1:
            time.sleep(0.5)
    
    # 結果を保存
    result_data = {
        'metadata': {
            'label': label,
            'state': state,
            'fetchedAt': datetime.now().isoformat(),
            'totalPRs': len(all_pr_data),
            'repo': 'team-mirai/policy'
        },
        'prs': all_pr_data
    }
    
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"\nData saved to: {output_file}")
    else:
        print(json.dumps(result_data, ensure_ascii=False, indent=2))
    
    # サマリーを表示
    print(f"\n=== Summary ===")
    print(f"Total PRs fetched: {len(all_pr_data)}")
    print(f"Total comments: {sum(pr['statistics']['commentsCount'] for pr in all_pr_data)}")
    print(f"Total reactions: {sum(pr['statistics']['totalReactions'] for pr in all_pr_data)}")
    print(f"Most commented PR: ", end="")
    if all_pr_data:
        most_commented = max(all_pr_data, key=lambda x: x['statistics']['commentsCount'])
        print(f"#{most_commented['number']} ({most_commented['statistics']['commentsCount']} comments)")
    
    return result_data

def main():
    parser = argparse.ArgumentParser(description='Fetch PR data from GitHub')
    parser.add_argument('--label', required=True, help='PR label to filter (e.g., 教育)')
    parser.add_argument('--state', default='open', choices=['open', 'closed', 'all'],
                        help='PR state (default: open)')
    parser.add_argument('--limit', type=int, help='Limit number of PRs to fetch')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--cache-dir', default='cache', help='Cache directory (default: cache)')
    
    args = parser.parse_args()
    
    # キャッシュディレクトリを設定
    global cache_dir
    cache_dir = args.cache_dir
    
    # データを取得
    fetch_all_pr_data(
        label=args.label,
        state=args.state,
        limit=args.limit,
        output_file=args.output
    )

if __name__ == "__main__":
    main()