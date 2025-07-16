#!/usr/bin/env python3
"""
残りの未分類PRを一気に分類
"""
import csv
import subprocess
import json
import time
import os
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

def get_pr_details(pr_number):
    """PR詳細を取得（キャッシュ付き）"""
    cache_dir = "pr_cache"
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
    # 未分類PRリストを読み込み
    unclassified_file = "unclassified_prs_20250714_230316.csv"
    if not os.path.exists(unclassified_file):
        print(f"エラー: {unclassified_file} が見つかりません")
        return
    
    unclassified_prs = []
    with open(unclassified_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        unclassified_prs = list(reader)
    
    print(f"未分類PR数: {len(unclassified_prs)}件")
    print("分類を開始します...\n")
    
    # 結果を保存するリスト
    results = []
    
    # 進捗表示用
    start_time = time.time()
    
    for i, pr in enumerate(unclassified_prs):
        pr_num = int(pr['PR番号'])
        pr_title = pr['タイトル']
        
        # 進捗表示
        progress = (i + 1) / len(unclassified_prs) * 100
        elapsed = time.time() - start_time
        eta = elapsed / (i + 1) * len(unclassified_prs) - elapsed
        
        print(f"[{i+1}/{len(unclassified_prs)}] ({progress:.1f}%) PR #{pr_num}: {pr_title[:50]}...")
        print(f"  経過時間: {elapsed/60:.1f}分, 推定残り時間: {eta/60:.1f}分")
        
        # PR詳細取得
        pr_details = get_pr_details(pr_num)
        if not pr_details:
            # エラーの場合はデフォルト分類
            results.append({
                'PR番号': pr_num,
                'タイトル': pr_title,
                '作成者': pr['作成者'],
                '作成日': pr['作成日'],
                'ステータス': pr['ステータス'],
                '政策分野（新ラベル）': 'その他政策',
                '旧ラベル': 'README',
                '分類理由': 'PR詳細取得エラーによりデフォルト分類',
                '分析メモ': f'自動分類: {datetime.now().strftime("%Y-%m-%d")}',
                'URL': pr['URL'],
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
            '作成者': pr['作成者'],
            '作成日': pr['作成日'],
            'ステータス': pr['ステータス'],
            '政策分野（新ラベル）': classification['label'],
            '旧ラベル': 'README',
            '分類理由': classification['reason'],
            '分析メモ': f'自動分類: {datetime.now().strftime("%Y-%m-%d")}',
            'URL': pr['URL'],
            '説明（200文字まで）': pr_title[:200]
        })
        
        # レート制限対策（短めに設定）
        time.sleep(0.3)
    
    # 結果を保存
    output_file = f'newly_classified_prs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n分類完了!")
    print(f"  出力ファイル: {output_file}")
    print(f"  分類数: {len(results)}件")
    print(f"  総処理時間: {(time.time() - start_time)/60:.1f}分")
    
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