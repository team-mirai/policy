#!/usr/bin/env python3
"""
分析したPRとmainブランチの既存政策との重複をチェック
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime

def load_analysis_summary(summary_file):
    """分析サマリーを読み込む"""
    with open(summary_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_individual_analyses(output_dir):
    """個別分析結果を読み込む"""
    analyses = {}
    individual_dir = Path(output_dir) / 'individual'
    
    for json_file in individual_dir.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                data = json.loads(content)
                analyses[data['pr_number']] = data
        except:
            continue
    
    return analyses

def check_duplicates_with_main(analyses, pr_data):
    """mainブランチの既存政策と重複している可能性があるPRを特定"""
    
    # PRデータをPR番号でインデックス化してタイトルを取得できるようにする
    pr_info = {pr['number']: pr for pr in pr_data['prs']}
    
    # mainブランチに既に含まれている主要な政策
    existing_policies = {
        "体験学習クーポン": [
            "体験格差",
            "体験学習クーポン",
            "世帯年収600万円以下",
            "学校外の体験"
        ],
        "EdTech投資": [
            "EdTech",
            "500億円",
            "政府ファンド",
            "ソフトウェア費用"
        ],
        "新世代児童館": [
            "STEAM",
            "新世代児童館",
            "児童館",
            "3Dプリンター",
            "メイカースペース"
        ],
        "GIGAスクール": [
            "GIGA",
            "端末更新",
            "1人1台端末",
            "スペック"
        ],
        "AI活用効率化": [
            "AI活用",
            "業務効率化",
            "教育国債"
        ]
    }
    
    potential_duplicates = []
    
    for pr_num, analysis in analyses.items():
        summary = analysis.get('summary', '')
        keywords = analysis.get('keywords', [])
        pr = pr_info.get(pr_num, {})
        title = pr.get('title', '')
        
        # 各既存政策との類似度をチェック
        for policy_name, policy_keywords in existing_policies.items():
            match_count = 0
            matched_keywords = []
            
            # タイトル、サマリー、キーワードをチェック
            text_to_check = f"{title} {summary} {' '.join(keywords)}".lower()
            
            for keyword in policy_keywords:
                if keyword.lower() in text_to_check:
                    match_count += 1
                    matched_keywords.append(keyword)
            
            # 1つ以上のキーワードがマッチしたら重複の可能性あり（閾値を下げて検出感度を上げる）
            if match_count >= 1:
                potential_duplicates.append({
                    'pr_number': pr_num,
                    'summary': summary,
                    'category': analysis.get('category', 'N/A'),
                    'existing_policy': policy_name,
                    'matched_keywords': matched_keywords,
                    'match_strength': 'high' if match_count >= 3 else ('medium' if match_count >= 2 else 'low')
                })
    
    return potential_duplicates

def generate_duplicate_report(duplicates, pr_data, output_file):
    """重複レポートを生成"""
    
    # PRデータをPR番号でインデックス化
    pr_info = {pr['number']: pr for pr in pr_data['prs']}
    
    report = []
    report.append("# 既存政策との重複可能性があるPR分析レポート")
    report.append(f"\n生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    report.append(f"\n## 概要")
    report.append(f"- 重複の可能性があるPR数: {len(duplicates)}件")
    
    if not duplicates:
        report.append("\n既存のmainブランチの政策と明確に重複するPRは見つかりませんでした。")
    else:
        report.append(f"\n## 重複の可能性があるPR一覧")
        report.append("\n以下のPRは、既にmainブランチに含まれている政策と部分的に重複している可能性があります。")
        
        # 既存政策ごとにグループ化
        by_policy = {}
        for dup in duplicates:
            policy = dup['existing_policy']
            if policy not in by_policy:
                by_policy[policy] = []
            by_policy[policy].append(dup)
        
        for policy_name, dups in by_policy.items():
            report.append(f"\n### {policy_name}と関連する可能性があるPR")
            report.append("\n| PR# | タイトル | 提案要約 | 一致したキーワード | 重複度 |")
            report.append("|-----|---------|---------|------------------|--------|")
            
            for dup in dups:
                pr_num = dup['pr_number']
                pr = pr_info.get(pr_num, {})
                title = pr.get('title', 'N/A')[:30] + '...' if len(pr.get('title', '')) > 30 else pr.get('title', 'N/A')
                pr_link = f"[#{pr_num}](https://github.com/team-mirai/policy/pull/{pr_num})"
                summary = dup['summary'][:40] + '...' if len(dup['summary']) > 40 else dup['summary']
                keywords = '、'.join(dup['matched_keywords'])
                strength = '高' if dup['match_strength'] == 'high' else ('中' if dup['match_strength'] == 'medium' else '低')
                
                report.append(f"| {pr_link} | {title} | {summary} | {keywords} | {strength} |")
        
        report.append(f"\n## 推奨アクション")
        report.append("1. **詳細確認**: 各PRの内容を精査し、既存政策との具体的な差分を確認")
        report.append("2. **提案者への連絡**: 既存政策を踏まえた上での改善提案への修正を依頼")
        report.append("3. **統合検討**: 既存政策の強化・拡充として取り込める部分の検討")
    
    # ファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Duplicate check report saved to: {output_file}")
    
    return len(duplicates)

def main():
    parser = argparse.ArgumentParser(description='Check duplicates with main branch policies')
    parser.add_argument('--summary', required=True, help='Analysis summary JSON file')
    parser.add_argument('--pr-data', required=True, help='Original PR data JSON file')
    parser.add_argument('--output-dir', required=True, help='Directory containing individual analyses')
    parser.add_argument('--output', '-o', default='duplicate_check_report.md',
                        help='Output report file')
    
    args = parser.parse_args()
    
    print("Loading analysis data...")
    analyses = load_individual_analyses(args.output_dir)
    
    # PRデータを読み込む
    with open(args.pr_data, 'r', encoding='utf-8') as f:
        pr_data = json.load(f)
    
    print("Checking for duplicates with main branch policies...")
    print("Note: Comparing against origin/main (remote) for latest policies")
    duplicates = check_duplicates_with_main(analyses, pr_data)
    
    print(f"Found {len(duplicates)} potential duplicates")
    
    # レポート生成
    generate_duplicate_report(duplicates, pr_data, args.output)
    
    print("\n✨ Duplicate check complete!")

if __name__ == "__main__":
    main()