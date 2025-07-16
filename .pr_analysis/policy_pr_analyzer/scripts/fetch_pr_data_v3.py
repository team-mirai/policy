#!/usr/bin/env python3
"""
GitHub APIを使用して指定されたラベルのPRデータを取得する（改良版v3）
reactionsをreactionGroupsに変更
"""

import json
import subprocess
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import FETCH_CONFIG, REPO_CONFIG

def ensure_cache_dir(cache_dir=None):
    """キャッシュディレクトリを作成"""
    if cache_dir is None:
        cache_dir = FETCH_CONFIG['cache_dir']
    Path(cache_dir).mkdir(exist_ok=True)

def get_cached_data(cache_file):
    """キャッシュファイルからデータを読み込む"""
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_to_cache(data, cache_file):
    """データをキャッシュファイルに保存"""
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ⚠ キャッシュ保存エラー: {e}")

def run_gh_command(args, check=False):
    """GitHub CLIコマンドを実行（エラーハンドリング改善）"""
    cmd = ["gh"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        if result.returncode != 0:
            print(f"  ⚠ コマンドエラー: {' '.join(cmd)}")
            print(f"  エラー詳細: {result.stderr}")
            return None
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"  ⚠ コマンド実行エラー: {e}")
        return None
    except Exception as e:
        print(f"  ⚠ 予期しないエラー: {e}")
        return None

def get_pr_list(label, state="open", limit=1000):
    """指定されたラベルのPRリストを取得"""
    print(f"Fetching {state} PRs with label '{label}'...")
    
    repo = f"{REPO_CONFIG['owner']}/{REPO_CONFIG['repo']}"
    args = [
        "pr", "list",
        "--repo", repo,
        "--label", label,
        "--state", state,
        "--limit", str(limit),
        "--json", "number,title,author,createdAt,updatedAt,state,url,labels,isDraft,milestone"
    ]
    
    result = run_gh_command(args)
    if result:
        try:
            prs = json.loads(result)
            print(f"Found {len(prs)} PRs")
            return prs
        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON解析エラー: {e}")
            return []
    return []

def get_pr_details(pr_number, cache_dir=None):
    """PR詳細情報を取得（エラーハンドリング改善）"""
    if cache_dir is None:
        cache_dir = FETCH_CONFIG['cache_dir']
        
    cache_file = f"{cache_dir}/pr_{pr_number}_details.json"
    
    # キャッシュチェック
    cached_data = get_cached_data(cache_file)
    if cached_data:
        print(f"  ✓ キャッシュから読み込み: PR #{pr_number}")
        return cached_data
    
    # PR詳細を取得（reactionGroupsを使用）
    repo = f"{REPO_CONFIG['owner']}/{REPO_CONFIG['repo']}"
    args = [
        "pr", "view", str(pr_number),
        "--repo", repo,
        "--json", "number,title,body,author,createdAt,updatedAt,state,url,labels,reactionGroups,additions,deletions,changedFiles,mergeable,mergedAt,comments"
    ]
    
    result = run_gh_command(args, check=False)
    if not result:
        print(f"  ⚠ PR #{pr_number} の詳細取得に失敗しました")
        return None
    
    try:
        pr_data = json.loads(result)
    except json.JSONDecodeError:
        print(f"  ⚠ PR #{pr_number} のJSON解析に失敗しました")
        return None
    
    # コメント数を取得
    pr_data['commentsCount'] = len(pr_data.get('comments', []))
    
    # リアクション数の集計（reactionGroupsから）
    total_reactions = 0
    reaction_groups = pr_data.get('reactionGroups', [])
    for group in reaction_groups:
        # 各リアクショングループのusers.totalCountを合計
        total_reactions += group.get('users', {}).get('totalCount', 0)
    
    pr_data['totalReactions'] = total_reactions
    
    # キャッシュに保存
    save_to_cache(pr_data, cache_file)
    
    return pr_data

def get_pr_diff(pr_number, cache_dir=None, max_lines=None):
    """PR差分を取得（エラーハンドリング改善）"""
    if cache_dir is None:
        cache_dir = FETCH_CONFIG['cache_dir']
    if max_lines is None:
        max_lines = FETCH_CONFIG['max_diff_lines']
        
    cache_file = f"{cache_dir}/pr_{pr_number}_diff.txt"
    
    # キャッシュチェック
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            pass
    
    # diffを取得
    repo = f"{REPO_CONFIG['owner']}/{REPO_CONFIG['repo']}"
    args = ["pr", "diff", str(pr_number), "--repo", repo]
    result = run_gh_command(args, check=False)
    
    if result:
        # 大きすぎるdiffは制限
        lines = result.split('\n')
        if len(lines) > max_lines:
            diff = '\n'.join(lines[:max_lines]) + f"\n... (truncated at {max_lines} lines)"
        else:
            diff = result
        
        # キャッシュに保存
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(diff)
        except Exception as e:
            print(f"  ⚠ diffキャッシュ保存エラー: {e}")
        
        return diff
    
    return ""

def fetch_all_pr_data(label, state="open", limit=None, output_file=None):
    """すべてのPRデータを取得して統合"""
    ensure_cache_dir()
    
    # デフォルトバッチサイズを使用
    if limit is None:
        limit = FETCH_CONFIG['default_batch_size']
    
    # PRリストを取得
    pr_list = get_pr_list(label, state, limit or 1000)
    
    if limit:
        pr_list = pr_list[:limit]
        print(f"Limited to {limit} PRs")
    
    # 詳細データを収集
    all_pr_data = []
    failed_prs = []
    total = len(pr_list)
    
    print(f"\n=== PR詳細取得開始 ===")
    
    for i, pr in enumerate(pr_list):
        pr_number = pr['number']
        print(f"\n[{i+1}/{total}] PR #{pr_number}: {pr['title'][:50]}...")
        
        # 詳細情報を取得
        details = get_pr_details(pr_number)
        if not details:
            print(f"  ⚠ PR #{pr_number} の詳細取得をスキップします")
            failed_prs.append(pr_number)
            # 基本情報だけでも保存
            details = pr.copy()
            details['statistics'] = {
                'commentsCount': 0,
                'totalReactions': 0,
                'filesChanged': 0,
                'additions': 0,
                'deletions': 0,
                'diffLines': 0
            }
            details['fetch_error'] = True
        else:
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
            
            # 成功メッセージ
            print(f"  ✓ 取得成功 (コメント: {details['statistics']['commentsCount']}, リアクション: {details['statistics']['totalReactions']})")
        
        all_pr_data.append(details)
        
        # レート制限対策
        if i < total - 1:
            time.sleep(FETCH_CONFIG['rate_limit_sleep'])
    
    # 結果を保存
    result_data = {
        'metadata': {
            'label': label,
            'state': state,
            'fetchedAt': datetime.now().isoformat(),
            'totalPRs': len(all_pr_data),
            'successfulPRs': len(all_pr_data) - len(failed_prs),
            'failedPRs': len(failed_prs),
            'failedPRNumbers': failed_prs,
            'repo': f"{REPO_CONFIG['owner']}/{REPO_CONFIG['repo']}"
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
    print(f"Successful: {len(all_pr_data) - len(failed_prs)}")
    print(f"Failed: {len(failed_prs)}")
    if failed_prs:
        print(f"Failed PRs: {failed_prs[:10]}{'...' if len(failed_prs) > 10 else ''}")
    
    # 統計情報
    valid_prs = [pr for pr in all_pr_data if not pr.get('fetch_error')]
    if valid_prs:
        print(f"\n=== Statistics (from {len(valid_prs)} valid PRs) ===")
        print(f"Total comments: {sum(pr['statistics']['commentsCount'] for pr in valid_prs)}")
        print(f"Total reactions: {sum(pr['statistics']['totalReactions'] for pr in valid_prs)}")
        
        most_commented = max(valid_prs, key=lambda x: x['statistics']['commentsCount'])
        print(f"Most commented: PR #{most_commented['number']} ({most_commented['statistics']['commentsCount']} comments)")
        
        most_reactions = max(valid_prs, key=lambda x: x['statistics']['totalReactions'])
        print(f"Most reactions: PR #{most_reactions['number']} ({most_reactions['statistics']['totalReactions']} reactions)")
    
    return result_data

def main():
    parser = argparse.ArgumentParser(description='Fetch PR data from GitHub (改良版v3)')
    parser.add_argument('--label', required=True, help='PR label to filter (e.g., 教育)')
    parser.add_argument('--state', default=REPO_CONFIG['default_state'], 
                        choices=['open', 'closed', 'all'],
                        help=f'PR state (default: {REPO_CONFIG["default_state"]})')
    parser.add_argument('--limit', type=int, 
                        help=f'Limit number of PRs to fetch (default: {FETCH_CONFIG["default_batch_size"]})')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--cache-dir', default=FETCH_CONFIG['cache_dir'], 
                        help=f'Cache directory (default: {FETCH_CONFIG["cache_dir"]})')
    
    args = parser.parse_args()
    
    # データを取得
    fetch_all_pr_data(
        label=args.label,
        state=args.state,
        limit=args.limit,
        output_file=args.output
    )

if __name__ == "__main__":
    main()