#!/usr/bin/env python3
import yaml


def get_final_100_batch2():
    """最後の100件分析のバッチ2（50件）を取得する"""

    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 未分析のPRを抽出（label_updated: false かつ new_label: None）
    unanalyzed_prs = []
    for pr in data['pull_requests']:
        if (pr.get('label_updated') == False and
                pr.get('new_label') == 'None'):
            unanalyzed_prs.append(pr)

    # 51-100件目を取得（バッチ1で50件処理済み）
    batch_prs = unanalyzed_prs[50:100]

    print(f"=== 最後の100件分析 - バッチ2（50件） ===")
    print(f"未分析PR総数: {len(unanalyzed_prs)}件")
    print(f"今回取得: {len(batch_prs)}件")
    if batch_prs:
        print(
            f"PR番号範囲: #{batch_prs[-1]['number']} - #{batch_prs[0]['number']}")

    # バッチ情報をファイルに保存
    batch_info = {
        'batch_name': 'final_100_batch2',
        'batch_size': len(batch_prs),
        'pr_range': f"#{batch_prs[-1]['number']}-#{batch_prs[0]['number']}" if batch_prs else "N/A",
        'prs': [pr['number'] for pr in batch_prs]
    }

    with open('final_100_batch2_info.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(batch_info, f, default_flow_style=False, allow_unicode=True)

    print(f"\nバッチ情報を final_100_batch2_info.yaml に保存しました")
    print(f"次のステップ: analyze_final_100_batch2.py を実行してください")

    return batch_prs


if __name__ == "__main__":
    get_final_100_batch2()
