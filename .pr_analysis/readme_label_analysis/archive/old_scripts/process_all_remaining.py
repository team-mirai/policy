#!/usr/bin/env python3
"""
残りの未分類PRをすべて処理
"""
import csv
import subprocess
import json
import time
import os
from datetime import datetime

def get_pr_details_quick(pr_numbers):
    """PR詳細をまとめて取得"""
    pr_details = {}
    
    for pr_num in pr_numbers:
        cache_file = f"pr_cache/pr_{pr_num}.json"
        
        # キャッシュがあれば読み込み
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                pr_details[pr_num] = json.load(f)
            continue
        
        # GitHub APIで取得（簡易版）
        cmd = ["gh", "pr", "view", str(pr_num), 
               "--repo", "team-mirai/policy", 
               "--json", "body,title"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                pr_details[pr_num] = data
                
                # キャッシュ保存
                os.makedirs("pr_cache", exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                pr_details[pr_num] = {"body": "", "title": ""}
        except:
            pr_details[pr_num] = {"body": "", "title": ""}
    
    return pr_details

def classify_pr_smart(title, body):
    """改良版分類ロジック"""
    content = f"{title} {body}".lower()
    
    # より具体的なキーワードマッチング
    
    # システム関連
    if any(word in content for word in ["readme", "目次", "リンク修正", "誤字", "脱字", "タイポ", "議論のハイライト"]) and "政策" not in content:
        return "[システム]", "マニフェストの構造改善・修正"
    
    # 子育て・福祉
    if any(word in content for word in ["子育て", "保育", "育児", "出産", "母子手帳", "少子化"]):
        return "子育て", "子育て支援・少子化対策"
    
    if any(word in content for word in ["福祉", "介護", "高齢者", "障害者", "生活保護", "社会保障", "養護"]):
        return "福祉", "社会保障・福祉政策"
    
    # 教育
    if any(word in content for word in ["教育", "学校", "教員", "学習", "いじめ", "体育"]):
        return "教育", "教育制度・学習支援"
    
    # 医療
    if any(word in content for word in ["医療", "病院", "健康", "医師", "治療", "難病", "メンタルヘルス"]):
        return "医療", "医療制度・健康政策"
    
    # デジタル民主主義
    if any(word in content for word in ["選挙", "投票", "オンライン投票", "在外選挙", "サイバーセキュリティ", "透明性"]):
        return "デジタル民主主義", "選挙制度・政治参加"
    
    # 行政改革
    if any(word in content for word in ["行政", "公務員", "制度改革", "規制緩和", "デジタル化"]):
        return "行政改革", "行政効率化・制度改革"
    
    # 科学技術
    if any(word in content for word in ["ai", "人工知能", "デジタル", "セキュリティ", "テクノロジー"]):
        return "科学技術", "AI・デジタル技術"
    
    # 産業政策
    if any(word in content for word in ["産業", "経済", "雇用", "企業", "インボイス", "税制", "移民", "外国人労働"]):
        return "産業政策", "産業振興・雇用・経済政策"
    
    # 経済財政
    if any(word in content for word in ["税", "財政", "年金", "消費税", "財源"]):
        return "経済財政", "税制・財政政策"
    
    # エネルギー
    if any(word in content for word in ["エネルギー", "原子力", "電力", "環境", "グリーン"]):
        return "エネルギー", "エネルギー・環境政策"
    
    # ビジョン・その他政策の判定
    if any(word in content for word in ["基本方針", "理念", "外交", "安全保障", "平和", "人権", "多様性", "同性婚", "夫婦別姓", "表現の自由"]):
        return "ビジョン", "基本理念・政治哲学"
    
    if any(word in content for word in ["性犯罪", "治安", "司法", "警察", "法律", "防災", "災害", "シェルター"]):
        return "その他政策", "司法・治安・防災政策"
    
    # デフォルト
    return "その他政策", "複合的政策提案"

def main():
    # 未分類PRリストを読み込み
    unclassified_file = "unclassified_prs_20250714_230316.csv"
    with open(unclassified_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        all_unclassified = list(reader)
    
    # バッチ1は完了したので、51件目以降を処理
    remaining_prs = all_unclassified[50:]  # 51件目から
    
    print(f"残り処理対象: {len(remaining_prs)}件")
    
    # バッチサイズ
    batch_size = 50
    total_batches = (len(remaining_prs) + batch_size - 1) // batch_size
    
    all_results = []
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(remaining_prs))
        batch_prs = remaining_prs[start_idx:end_idx]
        
        print(f"\n=== バッチ{batch_num + 2} ({len(batch_prs)}件) ===")
        
        # PR番号を取得
        pr_numbers = [int(pr['PR番号']) for pr in batch_prs]
        
        # PR詳細を取得
        print("PR詳細取得中...")
        pr_details = get_pr_details_quick(pr_numbers)
        
        # 分類実行
        batch_results = []
        for i, pr in enumerate(batch_prs):
            pr_num = int(pr['PR番号'])
            pr_title = pr['タイトル']
            
            detail = pr_details.get(pr_num, {})
            body = detail.get('body', '')
            
            label, reason = classify_pr_smart(pr_title, body)
            
            print(f"  [{i+1}/{len(batch_prs)}] PR #{pr_num}: {label}")
            
            result = {
                'PR番号': pr_num,
                'タイトル': pr_title,
                '作成者': pr['作成者'],
                '作成日': pr['作成日'],
                'ステータス': pr['ステータス'],
                '政策分野（新ラベル）': label,
                '旧ラベル': 'README',
                '分類理由': reason,
                '分析メモ': f'自動分類: {datetime.now().strftime("%Y-%m-%d")}',
                'URL': pr['URL'],
                '説明（200文字まで）': pr_title[:200]
            }
            
            batch_results.append(result)
            all_results.append(result)
        
        # バッチごとに保存
        batch_file = f'batch{batch_num + 2}_classified_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        with open(batch_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=batch_results[0].keys())
            writer.writeheader()
            writer.writerows(batch_results)
        
        print(f"  保存: {batch_file}")
        
        # 短い休憩
        time.sleep(1)
    
    # 全体の統計
    print(f"\n=== 処理完了 ===")
    print(f"総処理数: {len(all_results)}件")
    
    # ラベル別集計
    label_counts = {}
    for result in all_results:
        label = result['政策分野（新ラベル）']
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print("\n新規分類結果:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(all_results) * 100
        print(f"  {label}: {count}件 ({percentage:.1f}%)")

if __name__ == "__main__":
    main()