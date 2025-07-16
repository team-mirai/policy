#!/usr/bin/env python3
"""
取得したPRデータからLLM分析用のプロンプトを生成する
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime

def load_pr_data(input_file):
    """PRデータを読み込む"""
    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_individual_pr_prompt(pr):
    """個別PR分析用のプロンプトを生成（トークン削減版）"""
    # PR本文を1000文字に制限
    body = pr.get('body', '(本文なし)')
    if len(body) > 1000:
        body = body[:1000] + '...(省略)'
    
    # diffを重要な部分のみ抽出（最大1000文字）
    diff = pr.get('diff', '(diffなし)')
    if len(diff) > 1000:
        # diffの行数を数える
        diff_lines = diff.split('\n')
        if len(diff_lines) > 50:
            # 最初の25行と最後の25行を保持
            diff = '\n'.join(diff_lines[:25]) + '\n...(中略)...\n' + '\n'.join(diff_lines[-25:])
        else:
            diff = diff[:1000] + '...(省略)'
    
    prompt = f"""政策提案PRを分析してください。

PR#{pr['number']}: {pr['title']}

【提案内容】
{body}

【主な変更】
{diff}

JSON形式で以下を分析：
1. summary: 要約(50字以内)
2. category: カリキュラム改革/教員・人材/設備・インフラ/制度・システム/予算・財源/デジタル化/地域連携/その他
3. specificity: {{level:高/中/低, reason:理由}}
4. difficulty: {{level:高/中/低, main_challenge:主な課題}}
5. keywords: [5個のキーワード]
6. unique_features: 特徴(30字以内)

{{"pr_number":{pr['number']},"summary":"","category":"","specificity":{{"level":"","reason":""}},"difficulty":{{"level":"","main_challenge":""}},"keywords":[],"unique_features":"","scope":"","required_resources":"","discussion_points":[]}}"""
    
    return prompt

def create_similarity_check_prompt(pr1, pr2):
    """2つのPR間の類似度チェック用プロンプトを生成（トークン削減版）"""
    # 本文を500文字に制限
    body1 = pr1.get('body', '')[:500]
    body2 = pr2.get('body', '')[:500]
    
    prompt = f"""2つのPRの類似度を分析。

PR1 #{pr1['number']}: {pr1['title']}
{body1}

PR2 #{pr2['number']}: {pr2['title']}  
{body2}

JSON形式で出力：
{{"pr1_number":{pr1['number']},"pr2_number":{pr2['number']},"similarity_score":0,"common_themes":[],"can_merge":false}}"""
    
    return prompt

def create_trend_analysis_prompt(pr_summaries, metadata):
    """全体傾向分析用のプロンプトを生成（トークン削減版）"""
    total_prs = metadata['totalPRs']
    label = metadata['label']
    
    prompt = f"""{label}ラベル{total_prs}件の政策提案PRの傾向分析。

PRリスト（最大30件）：
"""
    
    # 各PRの要約情報を追加（最大30件に削減）
    for i, pr in enumerate(pr_summaries[:30]):
        prompt += f"\n{pr['number']}: {pr['title'][:50]}"
    
    if len(pr_summaries) > 30:
        prompt += f"\n...他{len(pr_summaries) - 30}件"
    
    prompt += """

JSON形式で分析：
1. main_themes: TOP5テーマ[{{theme,count}}]
2. category_distribution: {{カテゴリ:件数}}
3. common_challenges: 主な課題3つ
4. overall_insights: 総合所見

{{"main_themes":[],"category_distribution":{{}},"common_challenges":[],"overall_insights":"","recent_trends":[],"active_discussion_traits":"","feasible_proposal_traits":"","innovative_features":"","regional_aspects":""}}"""
    
    return prompt

def save_prompt(prompt, output_path):
    """プロンプトをファイルに保存"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(prompt)

def prepare_analysis_prompts(input_file, output_dir, limit=None, pr_numbers=None):
    """分析用プロンプトを準備"""
    # PRデータを読み込む
    data = load_pr_data(input_file)
    prs = data['prs']
    metadata = data['metadata']
    
    print(f"Loaded {len(prs)} PRs")
    
    # 出力ディレクトリを作成
    output_dir = Path(output_dir)
    individual_dir = output_dir / "individual"
    similarity_dir = output_dir / "similarity"
    trend_dir = output_dir / "trend"
    
    for d in [individual_dir, similarity_dir, trend_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # フィルタリング
    if pr_numbers:
        prs = [pr for pr in prs if pr['number'] in pr_numbers]
    elif limit:
        prs = prs[:limit]
    
    # 1. 個別PR分析プロンプトを生成
    print(f"\nGenerating individual PR analysis prompts for {len(prs)} PRs...")
    for i, pr in enumerate(prs):
        prompt = create_individual_pr_prompt(pr)
        output_path = individual_dir / f"pr_{pr['number']:05d}_analysis.txt"
        save_prompt(prompt, output_path)
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{len(prs)} prompts")
    
    # 2. 類似度チェックプロンプトを生成（サンプルとして最初の10件の組み合わせ）
    if len(prs) > 1:
        print(f"\nGenerating similarity check prompts...")
        sample_prs = prs[:min(10, len(prs))]
        pair_count = 0
        
        for i in range(len(sample_prs)):
            for j in range(i + 1, len(sample_prs)):
                pr1, pr2 = sample_prs[i], sample_prs[j]
                prompt = create_similarity_check_prompt(pr1, pr2)
                output_path = similarity_dir / f"similarity_{pr1['number']:05d}_{pr2['number']:05d}.txt"
                save_prompt(prompt, output_path)
                pair_count += 1
        
        print(f"  Generated {pair_count} similarity check prompts")
    
    # 3. 全体傾向分析プロンプトを生成
    print(f"\nGenerating trend analysis prompt...")
    # ここでは仮の要約データを使用（実際には個別分析結果を使う）
    pr_summaries = [{"number": pr['number'], "title": pr['title']} for pr in prs]
    trend_prompt = create_trend_analysis_prompt(pr_summaries, metadata)
    save_prompt(trend_prompt, trend_dir / "overall_trend_analysis.txt")
    
    # 実行手順を出力
    print(f"\n=== Next Steps ===")
    print(f"1. Run individual PR analyses:")
    print(f"   for f in {individual_dir}/*.txt; do")
    print(f"     out=\"{output_dir}/output/individual/$(basename $f)\"")
    print(f"     claude -p < \"$f\" > \"$out\"")
    print(f"     sleep 2")
    print(f"   done")
    print(f"\n2. Run similarity checks (optional):")
    print(f"   Similar commands for {similarity_dir}")
    print(f"\n3. After parsing individual results, run trend analysis:")
    print(f"   claude -p < {trend_dir}/overall_trend_analysis.txt > {output_dir}/output/trend/overall_trend_analysis.txt")

def main():
    parser = argparse.ArgumentParser(description='Prepare prompts for LLM analysis')
    parser.add_argument('input_file', help='Input JSON file with PR data')
    parser.add_argument('--output-dir', '-o', default='prompts/input',
                        help='Output directory for prompts (default: prompts/input)')
    parser.add_argument('--limit', type=int, help='Limit number of PRs to process')
    parser.add_argument('--pr-numbers', nargs='+', type=int,
                        help='Specific PR numbers to process')
    
    args = parser.parse_args()
    
    prepare_analysis_prompts(
        input_file=args.input_file,
        output_dir=args.output_dir,
        limit=args.limit,
        pr_numbers=args.pr_numbers
    )

if __name__ == "__main__":
    main()