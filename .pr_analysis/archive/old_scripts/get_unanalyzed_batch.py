#!/usr/bin/env python3
"""
未分析のPRを指定数だけ取得し、バッチ処理用のファイルを作成するスクリプト
"""

import yaml
import sys
from datetime import datetime

def load_yaml(filename):
    """YAMLファイルを読み込む"""
    with open(filename, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(data, filename):
    """YAMLファイルに保存"""
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def get_unanalyzed_batch(batch_size=20):
    """未分析のPRを指定数だけ取得"""
    
    # マージされたデータを読み込む（なければ新規データを使用）
    try:
        data = load_yaml('readme-pr-merged.yaml')
    except FileNotFoundError:
        data = load_yaml('readme-pr-new.yaml')
    
    # 未処理のPRを抽出
    unprocessed_prs = []
    for pr in data['pull_requests']:
        if not pr.get('label_updated', False) and pr.get('new_label') is None:
            unprocessed_prs.append(pr)
    
    # バッチサイズに制限
    batch_prs = unprocessed_prs[:batch_size]
    
    # バッチ情報をファイルに保存
    batch_info = {
        'batch_metadata': {
            '作成日時': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
            'バッチサイズ': len(batch_prs),
            '総未処理数': len(unprocessed_prs)
        },
        'pull_requests': batch_prs
    }
    
    filename = f'batch_{datetime.now().strftime("%Y%m%d_%H%M")}.yaml'
    save_yaml(batch_info, filename)
    
    # 情報を表示
    print(f"=== 未分析バッチ作成 ===")
    print(f"総未処理PR数: {len(unprocessed_prs)}")
    print(f"バッチサイズ: {len(batch_prs)}")
    print(f"ファイル名: {filename}")
    print(f"\n最初の5件:")
    for pr in batch_prs[:5]:
        print(f"  #{pr['number']}: {pr['title'][:60]}...")
    
    return filename, batch_prs

if __name__ == "__main__":
    # コマンドライン引数でバッチサイズを指定可能
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    get_unanalyzed_batch(batch_size)