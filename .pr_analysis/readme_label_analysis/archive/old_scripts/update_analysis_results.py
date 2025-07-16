#!/usr/bin/env python3
"""
分析用Markdownファイルに記載された分類結果をYAMLファイルに反映するスクリプト
"""

import yaml
import re
import sys
from datetime import datetime
from auto_classify_prs import analyze_pr_for_classification

def load_yaml(filename):
    """YAMLファイルを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data, filename):
    """YAMLファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def parse_analysis_markdown(md_file):
    """分析用Markdownファイルから分類結果を抽出"""
    
    results = {}
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # PRごとのセクションを抽出
    pr_sections = re.split(r'^## PR #(\d+):', content, flags=re.MULTILINE)
    
    # 最初の要素はヘッダーなので除外
    for i in range(1, len(pr_sections), 2):
        if i+1 < len(pr_sections):
            pr_number = int(pr_sections[i])
            pr_content = pr_sections[i+1]
            
            # 分析結果セクションを探す
            result_match = re.search(r'### 分析結果\s*\n\*\*推奨ラベル\*\*:\s*(.+?)\n\*\*理由\*\*:\s*(.+?)(?:\n|$)', pr_content, re.DOTALL)
            
            if result_match:
                label = result_match.group(1).strip()
                reason = result_match.group(2).strip()
                
                # 空でない場合のみ結果を保存
                if label and label != '':
                    results[pr_number] = {
                        'label': label,
                        'reason': reason
                    }
    
    return results

def auto_classify_batch(batch_file, use_auto_classify=True):
    """バッチファイルのPRを自動分類"""
    
    batch_data = load_yaml(batch_file)
    results = {}
    
    if use_auto_classify:
        print("自動分類を実行中...")
        for pr in batch_data['pull_requests']:
            # PRデータから分類に必要な情報を準備
            pr_info = {
                'title': pr.get('title', ''),
                'body': '',  # バッチファイルには本文が含まれていない場合がある
                'diff': ''
            }
            
            # 自動分類を実行
            classification = analyze_pr_for_classification(pr_info)
            
            results[pr['number']] = {
                'label': classification['category'],
                'reason': classification['reason']
            }
            
            print(f"  PR #{pr['number']}: {pr['title'][:50]}... → {classification['category']}")
    
    return results

def update_yaml_with_results(yaml_file, results):
    """YAMLファイルに分析結果を反映"""
    
    data = load_yaml(yaml_file)
    updated_count = 0
    
    for pr in data['pull_requests']:
        pr_number = pr['number']
        
        if pr_number in results:
            pr['new_label'] = results[pr_number]['label']
            pr['classification_reason'] = results[pr_number]['reason']
            pr['analysis_notes'] = f"自動分類: {datetime.now().strftime('%Y-%m-%d')}"
            updated_count += 1
    
    # メタデータを更新
    data['metadata']['最終更新日時'] = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    
    # 保存
    save_yaml(data, yaml_file)
    
    print(f"\n{updated_count}件のPRの分類結果を更新しました")
    
    return updated_count

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  自動分類: python update_analysis_results.py --auto <batch_file.yaml>")
        print("  手動結果反映: python update_analysis_results.py <analysis.md> <yaml_file>")
        sys.exit(1)
    
    if sys.argv[1] == '--auto':
        # 自動分類モード
        if len(sys.argv) < 3:
            print("バッチファイルを指定してください")
            sys.exit(1)
        
        batch_file = sys.argv[2]
        results = auto_classify_batch(batch_file)
        
        # 結果を適用するYAMLファイルを決定
        yaml_file = 'readme-pr-merged.yaml' if os.path.exists('readme-pr-merged.yaml') else 'readme-pr-new.yaml'
        
        update_yaml_with_results(yaml_file, results)
    else:
        # 手動分析結果の反映モード
        md_file = sys.argv[1]
        yaml_file = sys.argv[2] if len(sys.argv) > 2 else 'readme-pr-merged.yaml'
        
        # Markdownファイルから結果を抽出
        results = parse_analysis_markdown(md_file)
        
        if results:
            print(f"{len(results)}件の分析結果を検出しました")
            update_yaml_with_results(yaml_file, results)
        else:
            print("分析結果が見つかりませんでした")

if __name__ == "__main__":
    import os
    main()