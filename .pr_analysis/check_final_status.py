#!/usr/bin/env python3
import yaml


def check_final_status():
    """最終的なPR状況を確認する"""

    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    total_prs = len(data['pull_requests'])
    label_updated_true = sum(
        1 for pr in data['pull_requests'] if pr.get('label_updated') == True)
    label_updated_false = sum(
        1 for pr in data['pull_requests'] if pr.get('label_updated') == False)
    new_label_none = sum(
        1 for pr in data['pull_requests'] if pr.get('new_label') == 'None')

    print(f'=== PR ラベル更新状況 ===')
    print(f'総PR数: {total_prs}件')
    print(f'ラベル更新済み (label_updated: true): {label_updated_true}件')
    print(f'ラベル未更新 (label_updated: false): {label_updated_false}件')
    print(f'未分析 (new_label: None): {new_label_none}件')
    print(f'')
    print(f'目標達成状況:')
    print(f'- 未処理PR数: {new_label_none}件 (目標: 300件)')
    print(f'- 今回更新したPR数: 81件')

    # ラベル別統計
    label_counts = {}
    for pr in data['pull_requests']:
        if pr.get('label_updated') == True and pr.get('new_label'):
            label = pr.get('new_label')
            label_counts[label] = label_counts.get(label, 0) + 1

    print(f'\n=== 更新済みラベル統計 ===')
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        print(f'- {label}: {count}件')


if __name__ == "__main__":
    check_final_status()
