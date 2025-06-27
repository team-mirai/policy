#!/usr/bin/env python3
import yaml


def get_next_batch():
    """次の30件の未分析PRを取得する"""

    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 未分析のPRを抽出（label_updated: false かつ new_label: None）
    unanalyzed_prs = []
    for pr in data['pull_requests']:
        if (pr.get('label_updated') == False and
                pr.get('new_label') == 'None'):
            unanalyzed_prs.append(pr)

    # 最初の30件を取得
    batch_prs = unanalyzed_prs[:30]

    print(f"=== 次の100件分析 - バッチ1（30件） ===")
    print(f"未分析PR総数: {len(unanalyzed_prs)}件")
    print(f"今回取得: {len(batch_prs)}件")
    print(f"PR番号範囲: #{batch_prs[-1]['number']} - #{batch_prs[0]['number']}")

    # バッチ情報をファイルに保存
    batch_info = {
        'batch_name': 'next_100_batch1',
        'batch_size': len(batch_prs),
        'pr_range': f"#{batch_prs[-1]['number']}-#{batch_prs[0]['number']}",
        'prs': [pr['number'] for pr in batch_prs]
    }

    with open('next_100_batch1_info.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(batch_info, f, default_flow_style=False, allow_unicode=True)

    print(f"\nバッチ情報を next_100_batch1_info.yaml に保存しました")
    print(f"次のステップ: create_next_100_batch1_analysis.py を実行してください")

    return batch_prs


if __name__ == "__main__":
    get_next_batch()
