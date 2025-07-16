#!/usr/bin/env python3
"""
READMEラベルのPRを取得してAI分析し、政策分野に分類してCSV出力
"""

import subprocess
import json
import csv
import time
import os
import argparse
from datetime import datetime

# 政策分野ラベル
POLICY_LABELS = [
    "ビジョン",
    "デジタル民主主義", 
    "行政改革",
    "教育",
    "福祉",
    "子育て",
    "医療",
    "経済財政",
    "産業政策",
    "科学技術",
    "エネルギー",
    "その他政策",
    "[システム]"
]

def get_readme_prs(state='all', limit=1000):
    """READMEラベルのPRを取得"""
    
    # GitHub CLIでPRを検索
    cmd = [
        "gh", "pr", "list",
        "--repo", "team-mirai/policy",
        "--label", "README",
        "--json", "number,title,author,createdAt,state,url",
        "--limit", str(limit)
    ]
    
    if state != 'all':
        cmd.insert(-2, f"--state={state}")
    
    print(f"READMEラベルのPRを取得中...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"エラー: {result.stderr}")
        return []
    
    prs = json.loads(result.stdout)
    print(f"取得したPR数: {len(prs)}件")
    return prs

def get_pr_details(pr_number, cache_dir="pr_cache"):
    """PR詳細を取得（キャッシュ付き）"""
    
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = f"{cache_dir}/pr_{pr_number}.json"
    
    # キャッシュチェック
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # PR詳細を取得
    cmd = ["gh", "pr", "view", str(pr_number), 
           "--repo", "team-mirai/policy", 
           "--json", "body,title"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ⚠ PR詳細取得エラー: {pr_number}")
        return None
    
    pr_data = json.loads(result.stdout)
    
    # 差分を取得（最初の300行）
    diff_cmd = ["gh", "pr", "diff", str(pr_number), "--repo", "team-mirai/policy"]
    diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
    
    if diff_result.returncode == 0:
        diff_lines = diff_result.stdout.split('\n')[:300]
        pr_data['diff'] = '\n'.join(diff_lines)
    else:
        pr_data['diff'] = "(差分取得エラー)"
    
    # キャッシュに保存
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(pr_data, f, ensure_ascii=False, indent=2)
    
    return pr_data

def create_prompt(pr_number, pr_title, pr_details):
    """分類用プロンプトを作成"""
    return f"""以下のPRを13の政策分野のいずれかに分類してください。

PR番号: {pr_number}
タイトル: {pr_title}

PR本文（最初の2000文字）:
{pr_details.get('body', '(本文なし)')[:2000]}

差分（最初の300行）:
{pr_details.get('diff', '(差分なし)')}

政策分野ラベル:
1. ビジョン - 政治理念、基本方針
2. デジタル民主主義 - 透明性、参加型政治、オープンガバメント
3. 行政改革 - 行政効率化、デジタル化、規制改革
4. 教育 - 教育制度、学習支援
5. 福祉 - 社会保障、高齢者・障害者支援
6. 子育て - 少子化対策、育児支援
7. 医療 - 医療制度、健康政策
8. 経済財政 - 税制、財政政策、経済政策
9. 産業政策 - 産業振興、技術革新、雇用
10. 科学技術 - 研究開発、イノベーション
11. エネルギー - エネルギー政策、環境
12. その他政策 - 上記に該当しない政策
13. [システム] - README更新、システム改善

以下の形式で回答してください（他の文章は不要）:
ラベル: [選択したラベル]
理由: [分類理由を1行で簡潔に]"""

def classify_with_llm(prompt):
    """LLMで分類"""
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return None
    
    # 結果をパース
    output = result.stdout.strip()
    label = None
    reason = None
    
    for line in output.split('\n'):
        if line.startswith('ラベル:'):
            label = line.replace('ラベル:', '').strip()
        elif line.startswith('理由:'):
            reason = line.replace('理由:', '').strip()
    
    if label in POLICY_LABELS:
        return {'label': label, 'reason': reason}
    
    return None

def main():
    parser = argparse.ArgumentParser(description='READMEラベルのPRを分析して政策分野に分類')
    parser.add_argument('-o', '--output', 
                        default=f'analyzed_prs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        help='出力CSVファイル名')
    parser.add_argument('-s', '--state', choices=['open', 'closed', 'merged', 'all'],
                        default='all', help='PR状態フィルター（デフォルト: all）')
    parser.add_argument('-l', '--limit', type=int, help='処理するPR数の上限')
    parser.add_argument('--sleep', type=float, default=0.3, 
                        help='API呼び出し間隔（秒、デフォルト: 0.3）')
    parser.add_argument('--dry-run', action='store_true', help='PR取得のみ行い分析はしない')
    
    args = parser.parse_args()
    
    # READMEラベルのPRを取得
    prs = get_readme_prs(args.state)
    
    if not prs:
        print("READMEラベルのPRが見つかりませんでした")
        return
    
    # 制限適用
    if args.limit:
        prs = prs[:args.limit]
        print(f"処理対象を{args.limit}件に制限")
    
    # ドライラン
    if args.dry_run:
        print(f"\n[DRY RUN] 以下の{len(prs)}件のPRを分析します:")
        for i, pr in enumerate(prs[:10]):
            print(f"{i+1}. PR #{pr['number']}: {pr['title'][:50]}...")
        if len(prs) > 10:
            print(f"... 他 {len(prs) - 10}件")
        return
    
    print(f"\n{len(prs)}件のPRを分析します...")
    
    # 結果を保存するリスト
    results = []
    start_time = time.time()
    
    # 各PRを分析
    for i, pr in enumerate(prs):
        pr_num = pr['number']
        pr_title = pr['title']
        
        # 進捗表示
        progress = (i + 1) / len(prs) * 100
        elapsed = time.time() - start_time
        eta = elapsed / (i + 1) * len(prs) - elapsed if i > 0 else 0
        
        print(f"\n[{i+1}/{len(prs)}] ({progress:.1f}%) PR #{pr_num}: {pr_title[:50]}...")
        print(f"  経過時間: {elapsed/60:.1f}分, 推定残り時間: {eta/60:.1f}分")
        
        # PR詳細取得
        pr_details = get_pr_details(pr_num)
        if not pr_details:
            # エラーの場合はデフォルト分類
            results.append({
                'PR番号': pr_num,
                'タイトル': pr_title,
                '作成者': pr['author']['login'],
                '作成日': pr['createdAt'],
                'ステータス': pr['state'],
                '政策分野（新ラベル）': 'その他政策',
                '旧ラベル': 'README',
                '分類理由': 'PR詳細取得エラーによりデフォルト分類',
                '分析メモ': f'AI分析: {datetime.now().strftime("%Y-%m-%d")}',
                'URL': pr['url'],
                '説明（200文字まで）': pr_title[:200]
            })
            continue
        
        # プロンプト作成
        prompt = create_prompt(pr_num, pr_title, pr_details)
        
        # LLM分類
        classification = classify_with_llm(prompt)
        if not classification:
            print(f"    ⚠ 分類失敗 - デフォルト使用")
            classification = {
                'label': 'その他政策',
                'reason': 'LLM分類エラーによりデフォルト分類'
            }
        else:
            print(f"    ✓ {classification['label']}: {classification['reason'][:50]}...")
        
        results.append({
            'PR番号': pr_num,
            'タイトル': pr_title,
            '作成者': pr['author']['login'],
            '作成日': pr['createdAt'],
            'ステータス': pr['state'],
            '政策分野（新ラベル）': classification['label'],
            '旧ラベル': 'README',
            '分類理由': classification['reason'],
            '分析メモ': f'AI分析: {datetime.now().strftime("%Y-%m-%d")}',
            'URL': pr['url'],
            '説明（200文字まで）': pr_title[:200]
        })
        
        # レート制限対策
        time.sleep(args.sleep)
        
        # 10件ごとに中間保存
        if (i + 1) % 10 == 0:
            with open(args.output, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            print(f"  中間保存: {args.output}")
    
    # 最終結果を保存
    with open(args.output, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    total_time = time.time() - start_time
    print(f"\n分析完了!")
    print(f"  出力ファイル: {args.output}")
    print(f"  分析数: {len(results)}件")
    print(f"  総処理時間: {total_time/60:.1f}分")
    
    # ラベル別集計
    label_counts = {}
    for result in results:
        label = result['政策分野（新ラベル）']
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print("\nラベル別分類結果:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(results) * 100
        print(f"  {label}: {count}件 ({percentage:.1f}%)")

if __name__ == "__main__":
    main()