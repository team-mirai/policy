#!/usr/bin/env python3
import yaml


def update_final_100_results():
    """最後の100件分析の結果をreadme-pr.yamlに反映"""

    # バッチ1とバッチ2の結果を読み込み
    with open('final_100_batch1_results.yaml', 'r', encoding='utf-8') as f:
        batch1_data = yaml.safe_load(f)

    with open('final_100_batch2_results.yaml', 'r', encoding='utf-8') as f:
        batch2_data = yaml.safe_load(f)

    # 全結果をまとめる
    all_results = batch1_data['analysis_results'] + \
        batch2_data['analysis_results']

    # readme-pr.yamlを読み込み
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 結果を反映
    updated_count = 0
    for result in all_results:
        pr_number = result['number']
        new_label = result['new_label']

        # 該当PRを見つけて更新
        for pr in data['pull_requests']:
            if pr['number'] == pr_number:
                pr['new_label'] = new_label
                pr['analysis_reason'] = result['analysis_reason']
                updated_count += 1
                break

    # ファイルに保存
    with open('readme-pr.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False)

    # 統計情報を計算
    label_distribution = {}
    for result in all_results:
        label = result['new_label']
        label_distribution[label] = label_distribution.get(label, 0) + 1

    print(f"=== 最後の100件分析結果更新完了 ===")
    print(f"更新されたPR数: {updated_count}件")
    print(f"バッチ1: {len(batch1_data['analysis_results'])}件")
    print(f"バッチ2: {len(batch2_data['analysis_results'])}件")
    print(f"合計: {len(all_results)}件")

    print(f"\n=== ラベル分布 ===")
    for label, count in sorted(label_distribution.items()):
        print(f"- {label}: {count}件")

    # 更新対象PRリストを作成
    pr_numbers = [result['number'] for result in all_results]

    # 更新情報を保存
    update_info = {
        'batch_name': 'final_100_combined',
        'total_updated': updated_count,
        'pr_numbers': pr_numbers,
        'label_distribution': label_distribution,
        'batch1_count': len(batch1_data['analysis_results']),
        'batch2_count': len(batch2_data['analysis_results'])
    }

    with open('final_100_update_info.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(update_info, f, default_flow_style=False, allow_unicode=True)

    print(f"\n更新情報を final_100_update_info.yaml に保存しました")
    print(f"次のステップ: update_labels.py を実行してGitHubラベルを更新してください")

    return all_results


if __name__ == "__main__":
    update_final_100_results()
