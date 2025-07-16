#!/usr/bin/env python3
"""
政策チーム向けのマークダウンレポートを生成
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_summary_data(summary_file):
    """サマリーデータを読み込む"""
    with open(summary_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_pr_data(pr_data_file):
    """元のPRデータを読み込む"""
    with open(pr_data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_individual_analyses(output_dir):
    """個別分析結果を読み込んでPR番号でインデックス化"""
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

def generate_markdown_report(summary_data, pr_data, individual_analyses, output_file):
    """マークダウン形式のレポートを生成"""
    
    # PRデータをPR番号でインデックス化
    pr_info = {pr['number']: pr for pr in pr_data['prs']}
    
    # PR番号をリンク形式に変換するヘルパー関数
    def pr_link(pr_num):
        return f"[#{pr_num}](https://github.com/team-mirai/policy/pull/{pr_num})"
    
    # レポート生成開始
    report = []
    report.append(f"# 教育政策PR分析レポート")
    report.append(f"\n生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    report.append(f"\n## 概要")
    report.append(f"- 分析対象PR数: {summary_data['metadata']['total_prs_analyzed']}件")
    report.append(f"- 類似度チェック実施数: {summary_data['metadata']['similarity_checks']}件")
    report.append(f"- 発見された類似PRグループ数: {summary_data['key_findings']['similar_groups_count']}グループ")
    
    # カテゴリ別統計
    report.append(f"\n## カテゴリ別分布")
    report.append(f"\n| カテゴリ | PR数 | 割合 |")
    report.append(f"|---------|------|------|")
    
    total_prs = summary_data['metadata']['total_prs_analyzed']
    for category, count in sorted(summary_data['category_analysis']['distribution'].items(), 
                                 key=lambda x: x[1], reverse=True):
        percentage = count / total_prs * 100
        report.append(f"| {category} | {count} | {percentage:.1f}% |")
    
    # 実現難易度別統計
    report.append(f"\n## 実現難易度別分布")
    report.append(f"\n| 難易度 | PR数 | 主な課題 |")
    report.append(f"|--------|------|---------|")
    
    for difficulty in ['低', '中', '高']:
        if difficulty in summary_data['difficulty_analysis']['distribution']:
            count = summary_data['difficulty_analysis']['distribution'][difficulty]
            # 最初の3つの課題を表示
            challenges = []
            for pr_detail in summary_data['difficulty_analysis']['details_by_difficulty'].get(difficulty, [])[:3]:
                challenge = pr_detail.get('challenge', '')
                if challenge:
                    challenges.append(challenge)
            challenges_text = '<br>'.join(f"・{c}" for c in challenges) if challenges else '-'
            report.append(f"| {difficulty} | {count} | {challenges_text} |")
    
    # 類似PRグループ
    report.append(f"\n## 類似提案グループ（統合検討候補）")
    report.append(f"\n類似度の高い提案をグループ化しました。これらは内容が重複している可能性があり、統合を検討すべきものです。")
    
    for group in summary_data['similar_pr_groups'][:10]:  # 上位10グループ
        report.append(f"\n### グループ{group['group_id']} （{group['pr_count']}件）")
        report.append(f"\n| PR# | タイトル | 提案要約 | カテゴリ |")
        report.append(f"|-----|---------|---------|----------|")
        
        for pr_num in group['pr_numbers']:
            pr = pr_info.get(pr_num, {})
            analysis = individual_analyses.get(pr_num, {})
            title = pr.get('title', 'N/A')[:40] + '...' if len(pr.get('title', '')) > 40 else pr.get('title', 'N/A')
            summary = analysis.get('summary', 'N/A')
            category = analysis.get('category', 'N/A')
            report.append(f"| {pr_link(pr_num)} | {title} | {summary} | {category} |")
    
    # カテゴリ別詳細
    report.append(f"\n## カテゴリ別PR一覧")
    
    for category, pr_numbers in sorted(summary_data['category_analysis']['pr_numbers_by_category'].items()):
        report.append(f"\n### {category} ({len(pr_numbers)}件)")
        report.append(f"\n| PR# | タイトル | 具体性 | 実現難易度 | キーポイント |")
        report.append(f"|-----|---------|--------|-----------|------------|")
        
        for pr_num in sorted(pr_numbers)[:10]:  # 各カテゴリ最大10件
            pr = pr_info.get(pr_num, {})
            analysis = individual_analyses.get(pr_num, {})
            title = pr.get('title', 'N/A')[:30] + '...' if len(pr.get('title', '')) > 30 else pr.get('title', 'N/A')
            specificity = analysis.get('specificity', {}).get('level', 'N/A')
            difficulty = analysis.get('difficulty', {}).get('level', 'N/A')
            unique_features = analysis.get('unique_features', 'N/A')
            report.append(f"| {pr_link(pr_num)} | {title} | {specificity} | {difficulty} | {unique_features} |")
        
        if len(pr_numbers) > 10:
            report.append(f"\n*他{len(pr_numbers) - 10}件*")
    
    # アクション推奨事項
    report.append(f"\n## 推奨アクション")
    report.append(f"\n### 1. 即座に対応すべき項目")
    report.append(f"- **類似提案の統合**: {summary_data['key_findings']['similar_groups_count']}グループの類似提案について、提案者への連絡と統合を検討")
    report.append(f"- **高難易度提案の精査**: {summary_data['key_findings']['high_difficulty_count']}件の高難易度提案について、実現可能性の詳細検討が必要")
    
    report.append(f"\n### 2. 優先的に検討すべきカテゴリ")
    top_categories = sorted(summary_data['category_analysis']['distribution'].items(), 
                          key=lambda x: x[1], reverse=True)[:3]
    for category, count in top_categories:
        report.append(f"- **{category}**: {count}件の提案があり、最も関心が高い分野")
    
    report.append(f"\n### 3. 次のステップ")
    report.append(f"- 類似提案グループごとに担当者を割り当て、統合案の作成")
    report.append(f"- 各カテゴリのリーダーを決め、具体的な実施計画の策定")
    report.append(f"- 高難易度提案について、専門家を交えた実現可能性検討会の開催")
    
    # ファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Markdown report saved to: {output_file}")
    
    # CSV用データも準備
    csv_data = []
    csv_data.append("PR番号,URL,タイトル,カテゴリ,具体性,実現難易度,要約,類似グループ")
    
    # 類似グループ情報を整理
    pr_to_group = {}
    for group in summary_data['similar_pr_groups']:
        for pr_num in group['pr_numbers']:
            pr_to_group[pr_num] = group['group_id']
    
    for pr_num, analysis in individual_analyses.items():
        pr = pr_info.get(pr_num, {})
        url = f"https://github.com/team-mirai/policy/pull/{pr_num}"
        title = pr.get('title', 'N/A').replace(',', '、')
        category = analysis.get('category', 'N/A')
        specificity = analysis.get('specificity', {}).get('level', 'N/A')
        difficulty = analysis.get('difficulty', {}).get('level', 'N/A')
        summary = analysis.get('summary', 'N/A').replace(',', '、')
        group_id = pr_to_group.get(pr_num, '-')
        
        csv_data.append(f"{pr_num},{url},{title},{category},{specificity},{difficulty},{summary},{group_id}")
    
    # CSV保存
    csv_file = output_file.replace('.md', '.csv')
    with open(csv_file, 'w', encoding='utf-8-sig') as f:  # BOM付きUTF-8で保存
        f.write('\n'.join(csv_data))
    
    print(f"✅ CSV data saved to: {csv_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate policy team report')
    parser.add_argument('summary_file', help='Summary JSON file from parse_llm_results.py')
    parser.add_argument('--pr-data', required=True, help='Original PR data JSON file')
    parser.add_argument('--output-dir', required=True, help='Directory containing individual analysis results')
    parser.add_argument('--output', '-o', default='education_policy_report.md',
                        help='Output markdown file (default: education_policy_report.md)')
    
    args = parser.parse_args()
    
    # データ読み込み
    print("Loading data...")
    summary_data = load_summary_data(args.summary_file)
    pr_data = load_pr_data(args.pr_data)
    individual_analyses = load_individual_analyses(args.output_dir)
    
    # レポート生成
    print("Generating report...")
    generate_markdown_report(summary_data, pr_data, individual_analyses, args.output)
    
    print("\n✨ Report generation complete!")

if __name__ == "__main__":
    main()