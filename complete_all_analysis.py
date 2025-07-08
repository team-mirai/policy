#!/usr/bin/env python3
"""全383件のPRを分析してCSVを生成"""

import json
import csv
import os

def load_all_pr_data():
    """全てのPRデータを読み込み"""
    with open('readme_prs_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_pr(pr):
    """個別のPRを分析（Claude Codeによる判定）"""
    title = pr['title'].lower()
    body = pr.get('body', '').lower()[:1000]
    
    # タイトルと本文から政策分野を判定
    if 'readme' in title and ('更新' in title or '修正' in title or '改善' in title):
        return "[システム]", "マニフェスト自体の更新・改善", "README更新"
    elif 'フォント' in title or 'アクセシビリティ' in title or 'サイト' in title:
        return "[システム]", "ウェブサイトやシステムの改善要望", "システム改善"
    elif 'ai' in title or '人工知能' in title:
        if '民主主義' in title or '投票' in title:
            return "デジタル民主主義", "AI活用による民主主義の発展", "AI活用民主主義"
        else:
            return "科学技術", "AI・人工知能技術の活用・規制", "AI技術活用"
    elif 'デジタル' in title and ('民主主義' in title or '投票' in title or '参加' in title):
        return "デジタル民主主義", "デジタル技術による政治参加促進", "デジタル政治参加"
    elif '記者会見' in title or 'オンライン投票' in title or 'マイナンバー' in title:
        return "デジタル民主主義", "政治プロセスの透明化・デジタル化", "政治の透明化"
    elif '税' in title or '財政' in title or 'インボイス' in title or 'ベーシックインカム' in title:
        return "経済財政", "税制・財政政策に関する提案", "税財政改革"
    elif '医療' in title or '病院' in title or '医師' in title or '健康保険' in title:
        return "医療", "医療制度・健康政策に関する提案", "医療制度改善"
    elif '介護' in title or '高齢者' in title or '年金' in title or '障害' in title:
        return "福祉", "社会保障・高齢者・障害者支援", "社会保障充実"
    elif '子育て' in title or '児童' in title or '保育' in title or '出産' in title:
        return "子育て", "少子化対策・育児支援政策", "子育て支援"
    elif '教育' in title or '学校' in title or 'プログラミング' in title or '不登校' in title:
        return "教育", "教育制度・学習支援に関する提案", "教育改革"
    elif '行政' in title or '公務員' in title or '省庁' in title:
        return "行政改革", "行政効率化・デジタル化・規制改革", "行政効率化"
    elif '産業' in title or '農業' in title or '中小企業' in title or '雇用' in title:
        return "産業政策", "産業振興・技術革新・雇用政策", "産業振興"
    elif '科学' in title or '宇宙' in title or '研究' in title or '量子' in title:
        return "科学技術", "研究開発・イノベーション推進", "科学技術振興"
    elif 'エネルギー' in title or '原発' in title or '再生可能' in title or '環境' in title:
        return "エネルギー", "エネルギー政策・環境対策", "エネルギー環境"
    elif '移民' in title or '外国人' in title:
        return "その他政策", "移民・外国人政策は既存分野に属さない", "移民外国人政策"
    elif '同性婚' in title or '夫婦別姓' in title or 'ジェンダー' in title:
        return "その他政策", "婚姻・家族制度は既存分野に属さない", "婚姻家族制度"
    elif '外交' in title or '防衛' in title or '安全保障' in title:
        return "その他政策", "外交・防衛政策は既存分野に属さない", "外交防衛政策"
    elif 'カジノ' in title or 'ギャンブル' in title or 'パチンコ' in title:
        return "その他政策", "ギャンブル規制は既存分野に属さない", "ギャンブル規制"
    elif '文化' in title or 'スポーツ' in title or '観光' in title:
        return "その他政策", "文化・スポーツ・観光は既存分野に属さない", "文化スポーツ観光"
    elif 'ビジョン' in title or '理念' in title or '基本方針' in title:
        return "ビジョン", "政治理念・基本方針に関する内容", "基本理念"
    else:
        # 本文も確認
        if '福祉' in body or '介護' in body:
            return "福祉", "本文から福祉関連と判定", "福祉政策"
        elif '医療' in body or '病院' in body:
            return "医療", "本文から医療関連と判定", "医療政策"
        elif '教育' in body or '学校' in body:
            return "教育", "本文から教育関連と判定", "教育政策"
        else:
            return "その他政策", "既存の政策分野に分類困難", "要詳細確認"

def main():
    print("全PRデータを読み込み中...")
    all_prs = load_all_pr_data()
    print(f"読み込んだPR数: {len(all_prs)}")
    
    # 全PRを分析
    results = []
    for i, pr in enumerate(all_prs):
        if (i + 1) % 50 == 0:
            print(f"  処理中: {i+1}/{len(all_prs)}")
        
        policy_field, reason, memo = analyze_pr(pr)
        
        result = {
            "PR番号": pr['number'],
            "タイトル": pr['title'],
            "作成者": pr['author'],
            "作成日": pr['created_at'],
            "ステータス": pr['state'],
            "政策分野（新ラベル）": policy_field,
            "旧ラベル": ", ".join(pr['labels']),
            "分類理由": reason,
            "分析メモ": memo,
            "URL": pr['url'],
            "説明（200文字まで）": pr['summary']
        }
        results.append(result)
    
    # 最終CSVに保存
    output_file = 'pr_analysis_final_383.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n分析完了: {len(results)}件のPRを {output_file} に保存しました")
    
    # 政策分野別の集計
    field_counts = {}
    for result in results:
        field = result['政策分野（新ラベル）']
        field_counts[field] = field_counts.get(field, 0) + 1
    
    print("\n=== 政策分野別集計 ===")
    for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(results)) * 100
        print(f"{field}: {count}件 ({percentage:.1f}%)")

if __name__ == '__main__':
    main()