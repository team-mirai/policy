#!/usr/bin/env python3
"""
自動分類結果をレビューし、必要に応じて修正するスクリプト
"""

import yaml
from datetime import datetime

def load_yaml(filename):
    """YAMLファイルを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data, filename):
    """YAMLファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def review_classifications():
    """分類結果をレビューして修正"""
    
    # 修正が必要な分類のマッピング
    corrections = {
        6210: {'label': 'デジタル民主主義', 'reason': 'インターネット投票と選挙制度の改善に関する提案'},
        6207: {'label': 'その他政策', 'reason': '性犯罪対策は司法・治安分野に該当'},
        6201: {'label': 'デジタル民主主義', 'reason': '義務投票制と選挙制度改革に関する提案'},
        6200: {'label': 'その他政策', 'reason': 'サイバー犯罪条約は国際条約・セキュリティ分野'},
        6195: {'label': '子育て', 'reason': '養育費に関する提案が含まれているため'},
        6194: {'label': 'その他政策', 'reason': '憲法9条と自衛隊は防衛・安全保障分野'},
        6192: {'label': 'ビジョン', 'reason': '多様な家族のあり方は基本理念に関わる'},
        6188: {'label': 'その他政策', 'reason': '葬儀・墓地は社会インフラに関わる分野'},
        6184: {'label': '産業政策', 'reason': '農家支援と食料安定供給は農業産業政策'},
        6180: {'label': '福祉', 'reason': '氷河期世代支援は社会保障・福祉政策'},
        6179: {'label': '教育', 'reason': 'いじめ問題は教育分野の重要課題'},
        6176: {'label': 'デジタル民主主義', 'reason': '高齢者の投票参加促進は民主主義の基盤強化'},
        6163: {'label': 'ビジョン', 'reason': '選択的夫婦別姓は多様性を尊重する基本理念'},
        6160: {'label': '行政改革', 'reason': 'マイナンバーカードは行政デジタル化の中核'}
    }
    
    # YAMLファイルを読み込む
    yaml_file = 'readme-pr-merged.yaml' if os.path.exists('readme-pr-merged.yaml') else 'readme-pr-new.yaml'
    data = load_yaml(yaml_file)
    
    # 修正を適用
    corrected_count = 0
    for pr in data['pull_requests']:
        if pr['number'] in corrections:
            old_label = pr.get('new_label', 'なし')
            new_label = corrections[pr['number']]['label']
            
            pr['new_label'] = new_label
            pr['classification_reason'] = corrections[pr['number']]['reason']
            pr['analysis_notes'] = f"自動分類後に手動修正: {datetime.now().strftime('%Y-%m-%d')}"
            
            print(f"PR #{pr['number']}: {old_label} → {new_label}")
            corrected_count += 1
    
    # 保存
    save_yaml(data, yaml_file)
    
    print(f"\n{corrected_count}件の分類を修正しました")

def show_current_classifications():
    """現在の分類状況を表示"""
    yaml_file = 'readme-pr-merged.yaml' if os.path.exists('readme-pr-merged.yaml') else 'readme-pr-new.yaml'
    data = load_yaml(yaml_file)
    
    # 分類ごとにカウント
    label_counts = {}
    for pr in data['pull_requests']:
        label = pr.get('new_label', '未分類')
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print("\n=== 現在の分類状況 ===")
    for label, count in sorted(label_counts.items(), key=lambda x: (x[0] is None, x[0])):
        print(f"{label}: {count}件")
    
    # 最新20件の分類を表示
    print("\n=== 最新20件の分類 ===")
    for pr in data['pull_requests'][:20]:
        label = pr.get('new_label', '未分類')
        print(f"PR #{pr['number']}: {pr['title'][:40]}... → {label}")

if __name__ == "__main__":
    import os
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--show':
        show_current_classifications()
    else:
        review_classifications()
        show_current_classifications()