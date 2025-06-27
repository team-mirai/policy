#!/usr/bin/env python3
"""
readme-pr.yaml を CSV に変換するスクリプト
スプレッドシートで分析結果を確認するために使用
"""

import yaml
import csv
import sys
from pathlib import Path


def load_yaml_data(yaml_file):
    """YAML ファイルを読み込む"""
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    except Exception as e:
        print(f"YAML ファイルの読み込みエラー: {e}")
        return None


def convert_to_csv(yaml_data, output_file):
    """YAML データを CSV に変換"""
    if not yaml_data or 'pull_requests' not in yaml_data:
        print("有効な pull_requests データが見つかりません")
        return False

    pull_requests = yaml_data['pull_requests']

    # CSV のヘッダー
    headers = [
        'PR番号',
        'タイトル',
        '作成者',
        '作成日',
        'ステータス',
        '政策分野（新ラベル）',
        '旧ラベル',
        '分類理由',
        '分析メモ',
        'URL',
        '説明（200文字まで）'
    ]

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            for pr in pull_requests:
                # 政策分野の取得（new_labelから）
                policy_area = pr.get('new_label', pr.get('policy_area', ''))

                # 説明文の処理
                body = pr.get('body', '')
                if body and len(body) > 200:
                    body_short = body[:200] + '...'
                else:
                    body_short = body

                # 行データの作成
                row = [
                    pr.get('number', ''),
                    pr.get('title', ''),
                    pr.get('author', pr.get('user', '')),
                    pr.get('created_at', ''),
                    pr.get('state', ''),
                    policy_area,
                    pr.get('old_label', ''),
                    pr.get('classification_reason', ''),
                    pr.get('analysis_notes', ''),
                    pr.get('url', pr.get('html_url', '')),
                    body_short
                ]

                writer.writerow(row)

        return True

    except Exception as e:
        print(f"CSV ファイルの書き込みエラー: {e}")
        return False


def main():
    """メイン処理"""
    # ファイルパスの設定
    yaml_file = Path('readme-pr.yaml')
    csv_file = Path('readme-pr.csv')

    print("readme-pr.yaml を CSV に変換しています...")

    # YAML ファイルの存在確認
    if not yaml_file.exists():
        print(f"エラー: {yaml_file} が見つかりません")
        sys.exit(1)

    # YAML データの読み込み
    yaml_data = load_yaml_data(yaml_file)
    if yaml_data is None:
        sys.exit(1)

    # CSV への変換
    if convert_to_csv(yaml_data, csv_file):
        print(f"✅ 変換完了: {csv_file}")

        # 統計情報の表示
        pr_count = len(yaml_data.get('pull_requests', []))
        print(f"📊 総 PR 数: {pr_count}")

        # 政策分野別の統計
        policy_counts = {}
        for pr in yaml_data.get('pull_requests', []):
            policy = pr.get('new_label', pr.get('policy_area', '未分類'))
            policy_counts[policy] = policy_counts.get(policy, 0) + 1

        print("\n📈 政策分野別統計:")
        for policy, count in sorted(policy_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {policy}: {count}件")

        print(f"\n💡 スプレッドシートで {csv_file} を開いて分析してください！")
    else:
        print("❌ 変換に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
