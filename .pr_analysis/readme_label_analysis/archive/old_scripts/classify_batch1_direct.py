#!/usr/bin/env python3
"""
バッチ1の50件を直接分析・分類
"""
import json
import csv
from datetime import datetime

# 政策分野の定義
POLICY_LABELS = {
    "ビジョン": "政治理念、基本方針",
    "デジタル民主主義": "透明性、参加型政治、オープンガバメント",
    "行政改革": "行政効率化、デジタル化、規制改革",
    "教育": "教育制度、学習支援",
    "福祉": "社会保障、高齢者・障害者支援",
    "子育て": "少子化対策、育児支援",
    "医療": "医療制度、健康政策",
    "経済財政": "税制、財政政策、経済政策",
    "産業政策": "産業振興、技術革新、雇用",
    "科学技術": "研究開発、イノベーション",
    "エネルギー": "エネルギー政策、環境",
    "その他政策": "上記に該当しない政策",
    "[システム]": "README更新、システム改善"
}

def analyze_pr_content(pr_number, title, body, diff):
    """PR内容を分析して分類"""
    
    # PRタイトルと本文から主要キーワードを抽出して分類
    content = f"{title} {body}".lower()
    
    # [システム]の判定
    system_keywords = ["readme", "マニフェスト", "目次", "リンク", "誤字", "脱字", "修正", "改善提案", "議論のハイライト"]
    if any(keyword in content for keyword in system_keywords) and "政策" not in content:
        return "[システム]", f"マニフェストの構造改善（{title}）"
    
    # ビジョンの判定
    vision_keywords = ["基本方針", "理念", "ビジョン", "目指す社会", "価値観", "哲学", "原則"]
    if any(keyword in content for keyword in vision_keywords):
        return "ビジョン", f"政治理念・基本方針に関する提案"
    
    # デジタル民主主義の判定
    digital_democracy_keywords = ["選挙", "投票", "民主主義", "透明性", "政治参加", "オンライン投票", "参政権"]
    if any(keyword in content for keyword in digital_democracy_keywords):
        return "デジタル民主主義", f"選挙制度・民主主義に関する提案"
    
    # 子育ての判定
    childcare_keywords = ["子育て", "保育", "母子手帳", "育児", "少子化", "出産", "子ども"]
    if any(keyword in content for keyword in childcare_keywords):
        return "子育て", f"子育て支援・少子化対策"
    
    # 福祉の判定
    welfare_keywords = ["福祉", "介護", "高齢者", "障害者", "生活保護", "社会保障", "セーフティネット"]
    if any(keyword in content for keyword in welfare_keywords):
        return "福祉", f"社会保障・福祉政策"
    
    # 教育の判定
    education_keywords = ["教育", "学校", "教員", "学習", "いじめ"]
    if any(keyword in content for keyword in education_keywords):
        return "教育", f"教育制度・学習支援"
    
    # 医療の判定
    medical_keywords = ["医療", "病院", "健康", "医師", "看護", "治療"]
    if any(keyword in content for keyword in medical_keywords):
        return "医療", f"医療制度・健康政策"
    
    # 科学技術の判定
    tech_keywords = ["ai", "人工知能", "デジタル", "it", "テクノロジー", "技術革新", "イノベーション"]
    if any(keyword in content for keyword in tech_keywords):
        return "科学技術", f"AI・デジタル技術の活用"
    
    # 産業政策の判定
    industry_keywords = ["産業", "経済", "雇用", "労働", "企業", "起業", "スタートアップ", "農業", "製造業"]
    if any(keyword in content for keyword in industry_keywords):
        return "産業政策", f"産業振興・雇用政策"
    
    # 経済財政の判定
    finance_keywords = ["税", "財政", "予算", "年金", "運用", "消費税"]
    if any(keyword in content for keyword in finance_keywords):
        return "経済財政", f"税制・財政政策"
    
    # 行政改革の判定
    admin_keywords = ["行政", "公務員", "規制", "制度改革", "デジタル化"]
    if any(keyword in content for keyword in admin_keywords):
        return "行政改革", f"行政効率化・制度改革"
    
    # エネルギーの判定
    energy_keywords = ["エネルギー", "原子力", "再生可能", "電力", "環境"]
    if any(keyword in content for keyword in energy_keywords):
        return "エネルギー", f"エネルギー・環境政策"
    
    # その他政策（デフォルト）
    return "その他政策", f"複合的な政策提案（{title}）"

def main():
    # 未分類PRリストを読み込み
    unclassified_file = "unclassified_prs_20250714_230316.csv"
    with open(unclassified_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        unclassified_prs = list(reader)
    
    # 最初の50件を取得
    batch1_prs = unclassified_prs[:50]
    
    # PR詳細を読み込み
    with open('batch_details_001.json', 'r', encoding='utf-8') as f:
        pr_details = json.load(f)
    
    print(f"バッチ1: {len(batch1_prs)}件を分析中...")
    
    results = []
    
    for i, pr in enumerate(batch1_prs):
        pr_num = int(pr['PR番号'])
        pr_title = pr['タイトル']
        
        print(f"[{i+1}/50] PR #{pr_num}: {pr_title[:60]}...")
        
        # PR詳細を取得
        pr_detail = pr_details.get(str(pr_num), {})
        body = pr_detail.get('body', '')
        diff = pr_detail.get('diff', '')
        
        # 分類実行
        label, reason = analyze_pr_content(pr_num, pr_title, body, diff)
        
        print(f"    → {label}: {reason}")
        
        results.append({
            'PR番号': pr_num,
            'タイトル': pr_title,
            '作成者': pr['作成者'],
            '作成日': pr['作成日'],
            'ステータス': pr['ステータス'],
            '政策分野（新ラベル）': label,
            '旧ラベル': 'README',
            '分類理由': reason,
            '分析メモ': f'直接分析: {datetime.now().strftime("%Y-%m-%d")}',
            'URL': pr['URL'],
            '説明（200文字まで）': pr_title[:200]
        })
    
    # 結果を保存
    output_file = f'batch1_classified_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nバッチ1分類完了!")
    print(f"  出力ファイル: {output_file}")
    print(f"  分類数: {len(results)}件")
    
    # ラベル別集計
    label_counts = {}
    for result in results:
        label = result['政策分野（新ラベル）']
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print("\nバッチ1ラベル別分類結果:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(results) * 100
        print(f"  {label}: {count}件 ({percentage:.1f}%)")

if __name__ == "__main__":
    main()