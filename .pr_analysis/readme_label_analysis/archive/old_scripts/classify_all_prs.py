#!/usr/bin/env python3
"""
効率的なPR分類スクリプト
- 未分類PRをバッチで処理
- claude -pを使用してLLM分析
- 統一されたCSV出力
"""
import yaml
import csv
import subprocess
import json
import time
from datetime import datetime
import os

# 設定
BATCH_SIZE = 50
REPO = "team-mirai/policy"

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

def load_classified_prs():
    """既に分類済みのPRを読み込む"""
    classified_prs = {}
    
    # CSVファイルから読み込み
    csv_files = ['pr_analysis_combined_270.csv'] + \
                [f for f in os.listdir('.') if f.startswith('pr_analysis_batch_') and f.endswith('.csv')]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pr_num = int(row['PR番号'])
                    classified_prs[pr_num] = {
                        'label': row['政策分野（新ラベル）'],
                        'reason': row['分類理由']
                    }
    
    return classified_prs

def get_pr_details(pr_number):
    """PR詳細を取得"""
    # PR本文を取得
    body_cmd = ["gh", "pr", "view", str(pr_number), "--repo", REPO, "--json", "body,title"]
    result = subprocess.run(body_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    
    pr_data = json.loads(result.stdout)
    
    # 差分を取得（最初の200行のみ）
    diff_cmd = ["gh", "pr", "diff", str(pr_number), "--repo", REPO]
    diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
    
    diff_lines = diff_result.stdout.split('\n')[:200] if diff_result.returncode == 0 else []
    
    return {
        'title': pr_data['title'],
        'body': pr_data['body'],
        'diff': '\n'.join(diff_lines)
    }

def classify_pr_with_llm(pr_number, pr_info, pr_details):
    """LLMを使用してPRを分類"""
    prompt = f"""以下のPRを適切な政策分野に分類してください。

PR番号: {pr_number}
タイトル: {pr_info['title']}

PR本文:
{pr_details['body'][:1500]}

差分（最初の200行）:
{pr_details['diff']}

政策分野ラベル一覧:
{chr(10).join([f'{i+1}. {label}' for i, label in enumerate(POLICY_LABELS)])}

以下の形式で回答してください:
ラベル: [選択したラベル]
理由: [分類理由を1行で]
"""
    
    # claude -pコマンドで分類
    cmd = ["claude", "-p", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  LLM分類エラー: PR #{pr_number}")
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
    
    if label and label in POLICY_LABELS:
        return {'label': label, 'reason': reason}
    
    return None

def process_batch(unclassified_prs, batch_num, output_file):
    """バッチを処理してCSVに出力"""
    results = []
    
    print(f"\nバッチ{batch_num}を処理中 ({len(unclassified_prs)}件)")
    
    for i, pr in enumerate(unclassified_prs):
        print(f"  処理中 {i+1}/{len(unclassified_prs)}: PR #{pr['number']}")
        
        # PR詳細を取得
        pr_details = get_pr_details(pr['number'])
        if not pr_details:
            print(f"    PR詳細取得エラー")
            continue
        
        # LLMで分類
        classification = classify_pr_with_llm(pr['number'], pr, pr_details)
        if not classification:
            # フォールバック分類
            classification = {
                'label': 'その他政策',
                'reason': '自動分類失敗によりデフォルト分類'
            }
        
        results.append({
            'PR番号': pr['number'],
            'タイトル': pr['title'],
            '作成者': pr['author'],
            '作成日': pr['created_at'],
            'ステータス': pr['state'],
            '政策分野（新ラベル）': classification['label'],
            '旧ラベル': 'README',
            '分類理由': classification['reason'],
            '分析メモ': f'LLM自動分類: {datetime.now().strftime("%Y-%m-%d")}',
            'URL': pr['url'],
            '説明（200文字まで）': pr['title'][:200]
        })
        
        # レート制限回避
        time.sleep(1)
    
    # CSVに追記
    file_exists = os.path.exists(output_file)
    with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)
    
    return len(results)

def main():
    """メイン処理"""
    # 既存のデータを読み込み
    with open('readme-pr-merged.yaml', 'r', encoding='utf-8') as f:
        all_prs = yaml.safe_load(f)['pull_requests']
    
    # 分類済みPRを取得
    classified_prs = load_classified_prs()
    print(f"分類済みPR数: {len(classified_prs)}")
    
    # 未分類PRを抽出
    unclassified_prs = [pr for pr in all_prs if pr['number'] not in classified_prs]
    print(f"未分類PR数: {len(unclassified_prs)}")
    
    if len(unclassified_prs) == 0:
        print("すべてのPRが分類済みです")
        return
    
    # 出力ファイル名
    output_file = f'pr_analysis_auto_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    
    # バッチ処理
    total_processed = 0
    batch_num = 1
    
    for i in range(0, len(unclassified_prs), BATCH_SIZE):
        batch = unclassified_prs[i:i+BATCH_SIZE]
        processed = process_batch(batch, batch_num, output_file)
        total_processed += processed
        batch_num += 1
        
        print(f"  バッチ{batch_num-1}完了: {processed}件処理")
        print(f"  累計: {total_processed}/{len(unclassified_prs)}件")
    
    print(f"\n処理完了!")
    print(f"  出力ファイル: {output_file}")
    print(f"  処理したPR数: {total_processed}")

if __name__ == "__main__":
    main()