#!/usr/bin/env python3
"""
LLM分析結果をパースして集計する
"""

import json
import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # JSONブロックを抽出（```json ... ```の形式に対応）
            if content.startswith('```json'):
                content = content[7:]  # ```json を削除
            if content.endswith('```'):
                content = content[:-3]  # ``` を削除
            return json.loads(content)
    except Exception as e:
        print(f"  ⚠ Error loading {file_path}: {e}")
        return None

def parse_individual_results(output_dir):
    """個別PR分析結果をパース"""
    individual_dir = Path(output_dir) / 'individual'
    if not individual_dir.exists():
        print("❌ Individual results directory not found")
        return []
    
    results = []
    failed_files = []
    
    for json_file in sorted(individual_dir.glob('*.json')):
        data = load_json_file(json_file)
        if data:
            results.append(data)
        else:
            failed_files.append(json_file.name)
    
    print(f"✅ Parsed {len(results)} individual PR analyses")
    if failed_files:
        print(f"⚠ Failed to parse {len(failed_files)} files: {failed_files[:5]}...")
    
    return results

def parse_similarity_results(output_dir):
    """類似度分析結果をパース"""
    similarity_dir = Path(output_dir) / 'similarity'
    if not similarity_dir.exists():
        print("❌ Similarity results directory not found")
        return []
    
    results = []
    failed_files = []
    
    for json_file in sorted(similarity_dir.glob('*.json')):
        data = load_json_file(json_file)
        if data:
            results.append(data)
        else:
            failed_files.append(json_file.name)
    
    print(f"✅ Parsed {len(results)} similarity analyses")
    if failed_files:
        print(f"⚠ Failed to parse {len(failed_files)} files")
    
    return results

def parse_trend_result(output_dir):
    """全体傾向分析結果をパース"""
    trend_file = Path(output_dir) / 'trend' / 'overall_trend_analysis.json'
    if not trend_file.exists():
        print("❌ Trend analysis result not found")
        return None
    
    data = load_json_file(trend_file)
    if data:
        print("✅ Parsed trend analysis")
    return data

def analyze_categories(individual_results):
    """カテゴリ別の統計を分析"""
    category_count = Counter()
    category_prs = defaultdict(list)
    
    for pr in individual_results:
        category = pr.get('category', '不明')
        category_count[category] += 1
        category_prs[category].append(pr['pr_number'])
    
    return dict(category_count), dict(category_prs)

def analyze_difficulty(individual_results):
    """実現難易度別の統計を分析"""
    difficulty_count = Counter()
    difficulty_prs = defaultdict(list)
    
    for pr in individual_results:
        difficulty = pr.get('difficulty', {}).get('level', '不明')
        difficulty_count[difficulty] += 1
        difficulty_prs[difficulty].append({
            'pr_number': pr['pr_number'],
            'summary': pr.get('summary', ''),
            'challenge': pr.get('difficulty', {}).get('main_challenge', '')
        })
    
    return dict(difficulty_count), dict(difficulty_prs)

def find_similar_groups(similarity_results, threshold=70):
    """類似度の高いPRグループを見つける"""
    similar_groups = []
    grouped_prs = set()
    
    # 高い類似度のペアを抽出
    high_similarity_pairs = []
    for result in similarity_results:
        if result.get('similarity_score', 0) >= threshold:
            pr1 = result['pr1_number']
            pr2 = result['pr2_number']
            high_similarity_pairs.append((pr1, pr2, result['similarity_score']))
    
    # グループ化
    for pr1, pr2, score in sorted(high_similarity_pairs, key=lambda x: x[2], reverse=True):
        # 既存のグループに追加するか確認
        added_to_existing = False
        for group in similar_groups:
            if pr1 in group['prs'] or pr2 in group['prs']:
                group['prs'].add(pr1)
                group['prs'].add(pr2)
                added_to_existing = True
                break
        
        # 新しいグループを作成
        if not added_to_existing:
            similar_groups.append({
                'prs': {pr1, pr2},
                'scores': [(pr1, pr2, score)]
            })
    
    # セットをリストに変換
    for group in similar_groups:
        group['prs'] = sorted(list(group['prs']))
    
    return similar_groups

def create_summary_report(individual_results, similarity_results, trend_result, output_file):
    """サマリーレポートを作成"""
    # カテゴリ分析
    category_count, category_prs = analyze_categories(individual_results)
    
    # 難易度分析
    difficulty_count, difficulty_prs = analyze_difficulty(individual_results)
    
    # 類似グループ分析
    similar_groups = find_similar_groups(similarity_results)
    
    # レポート作成
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_prs_analyzed': len(individual_results),
            'similarity_checks': len(similarity_results),
        },
        'category_analysis': {
            'distribution': category_count,
            'pr_numbers_by_category': category_prs
        },
        'difficulty_analysis': {
            'distribution': difficulty_count,
            'details_by_difficulty': difficulty_prs
        },
        'similar_pr_groups': [
            {
                'group_id': i + 1,
                'pr_numbers': group['prs'],
                'pr_count': len(group['prs'])
            }
            for i, group in enumerate(similar_groups)
        ],
        'trend_insights': trend_result if trend_result else {},
        'key_findings': {
            'most_common_category': max(category_count, key=category_count.get) if category_count else 'N/A',
            'high_difficulty_count': difficulty_count.get('高', 0),
            'similar_groups_count': len(similar_groups),
            'largest_similar_group_size': max(len(g['prs']) for g in similar_groups) if similar_groups else 0
        }
    }
    
    # JSON形式で保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Summary report saved to: {output_file}")
    
    # コンソールにサマリー表示
    print("\n=== Analysis Summary ===")
    print(f"Total PRs analyzed: {len(individual_results)}")
    print(f"\nCategory Distribution:")
    for category, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count} PRs ({count/len(individual_results)*100:.1f}%)")
    
    print(f"\nDifficulty Distribution:")
    for difficulty, count in sorted(difficulty_count.items()):
        print(f"  {difficulty}: {count} PRs")
    
    print(f"\nSimilar PR Groups: {len(similar_groups)} groups found")
    for i, group in enumerate(similar_groups[:5]):  # 最初の5グループのみ表示
        print(f"  Group {i+1}: {len(group['prs'])} PRs - {group['prs']}")
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Parse LLM analysis results')
    parser.add_argument('output_dir', help='Directory containing analysis outputs (e.g., prompts/batch_50/output)')
    parser.add_argument('--output', '-o', default='analysis_summary.json',
                        help='Output file for summary report (default: analysis_summary.json)')
    parser.add_argument('--similarity-threshold', type=int, default=70,
                        help='Similarity score threshold for grouping (default: 70)')
    
    args = parser.parse_args()
    
    print(f"Parsing analysis results from: {args.output_dir}")
    
    # 各種結果をパース
    individual_results = parse_individual_results(args.output_dir)
    similarity_results = parse_similarity_results(args.output_dir)
    trend_result = parse_trend_result(args.output_dir)
    
    if not individual_results:
        print("❌ No individual analysis results found. Exiting.")
        sys.exit(1)
    
    # サマリーレポート作成
    report = create_summary_report(
        individual_results,
        similarity_results,
        trend_result,
        args.output
    )
    
    print(f"\n✨ Analysis complete! Check {args.output} for detailed results.")

if __name__ == "__main__":
    main()