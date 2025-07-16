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
    """個別PR分析用のプロンプトを生成"""
    prompt = f"""以下の政策提案PRを分析してください。

【PR情報】
- PR番号: #{pr['number']}
- タイトル: {pr['title']}
- 作成者: {pr['author']['login']}
- 作成日: {pr['createdAt']}
- 状態: {pr['state']}
- コメント数: {pr['statistics']['commentsCount']}
- リアクション数: {pr['statistics']['totalReactions']}
- 変更ファイル数: {pr['statistics']['filesChanged']}
- 追加行数: {pr['statistics']['additions']}
- 削除行数: {pr['statistics']['deletions']}

【PR本文】
{pr.get('body', '(本文なし)')[:3000]}

【変更内容（diff）】
{pr.get('diff', '(diffなし)')[:3000]}

【分析項目】
以下の項目について分析し、JSON形式で出力してください：

1. 提案要約: 50字以内で提案の核心を要約
2. カテゴリ: 以下から1つ選択
   - カリキュラム改革
   - 教員・人材
   - 設備・インフラ
   - 制度・システム
   - 予算・財源
   - デジタル化
   - 地域連携
   - その他
3. 具体性: 高/中/低で評価し、理由も簡潔に
4. 実現難易度: 高/中/低で評価し、主な課題を1つ挙げる
5. 影響範囲: 全国/地域/学校単位など
6. 必要なリソース: 主に必要となるリソース（予算/人材/制度改正など）
7. キーワード: 類似提案を見つけるためのキーワードを5個
8. 提案の特徴: この提案の独自性や特筆すべき点（30字以内）
9. 議論ポイント: 議論が必要な主要な論点を2つ

出力形式：
{{
  "pr_number": {pr['number']},
  "summary": "50字以内の要約",
  "category": "カテゴリ名",
  "specificity": {{
    "level": "高/中/低",
    "reason": "理由"
  }},
  "difficulty": {{
    "level": "高/中/低", 
    "main_challenge": "主な課題"
  }},
  "scope": "影響範囲",
  "required_resources": "必要なリソース",
  "keywords": ["キーワード1", "キーワード2", "キーワード3", "キーワード4", "キーワード5"],
  "unique_features": "独自性や特徴",
  "discussion_points": ["論点1", "論点2"]
}}"""
    
    return prompt

def create_similarity_check_prompt(pr1, pr2):
    """2つのPR間の類似度チェック用プロンプトを生成"""
    prompt = f"""以下の2つの政策提案PRの類似度を分析してください。

【PR1】
- 番号: #{pr1['number']}
- タイトル: {pr1['title']}
- 本文: {pr1.get('body', '')[:1000]}

【PR2】
- 番号: #{pr2['number']}  
- タイトル: {pr2['title']}
- 本文: {pr2.get('body', '')[:1000]}

【分析項目】
1. 類似度スコア（0-100）
2. 共通する主要なテーマ・目的
3. 共通するアプローチ・手法
4. 主な相違点
5. 統合可能性（これらを1つの提案にまとめられるか）

出力形式（JSON）：
{{
  "pr1_number": {pr1['number']},
  "pr2_number": {pr2['number']},
  "similarity_score": 85,
  "common_themes": ["共通テーマ1", "共通テーマ2"],
  "common_approaches": ["アプローチ1", "アプローチ2"],
  "differences": ["相違点1", "相違点2"],
  "can_merge": true,
  "merge_recommendation": "統合する場合の推奨事項"
}}"""
    
    return prompt

def create_trend_analysis_prompt(pr_summaries, metadata):
    """全体傾向分析用のプロンプトを生成"""
    # 基本統計情報をまとめる
    total_prs = metadata['totalPRs']
    label = metadata['label']
    
    prompt = f"""以下は{label}ラベルが付いた{total_prs}件の政策提案PRの概要です。全体的な傾向を分析してください。

【基本情報】
- 総PR数: {total_prs}件
- 対象期間: 過去から現在まで
- リポジトリ: {metadata['repo']}

【PR概要リスト】
"""
    
    # 各PRの要約情報を追加（最大50件程度）
    for i, pr in enumerate(pr_summaries[:50]):
        prompt += f"\n{i+1}. PR#{pr['number']}: {pr['title']}"
        if 'summary' in pr:
            prompt += f" - {pr['summary']}"
    
    if len(pr_summaries) > 50:
        prompt += f"\n... 他{len(pr_summaries) - 50}件"
    
    prompt += """

【分析項目】
以下の観点で全体傾向を分析し、JSON形式で出力してください：

1. 主要テーマ: 最も多い提案テーマTOP10（件数付き）
2. カテゴリ分布: 各カテゴリの提案数
3. トレンド: 最近増えている提案の傾向
4. 議論活発度: コメントが多い提案の共通点
5. 実現可能性: 実現しやすそうな提案の特徴
6. 課題領域: 多くの提案が指摘している課題
7. 革新的提案: 特に独創的・革新的な提案の特徴
8. 地域性: 地域特有の課題への言及があるか
9. 総合所見: 全体を通じての気づきや提言

出力形式（JSON）：
{
  "main_themes": [
    {"theme": "テーマ1", "count": 45, "percentage": 8.8},
    ...
  ],
  "category_distribution": {
    "カリキュラム改革": 120,
    "教員・人材": 85,
    ...
  },
  "recent_trends": ["トレンド1", "トレンド2"],
  "active_discussion_traits": "議論が活発な提案の共通点",
  "feasible_proposal_traits": "実現可能な提案の特徴",
  "common_challenges": ["課題1", "課題2", "課題3"],
  "innovative_features": "革新的提案の特徴",
  "regional_aspects": "地域性に関する観察",
  "overall_insights": "総合的な所見と提言"
}"""
    
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