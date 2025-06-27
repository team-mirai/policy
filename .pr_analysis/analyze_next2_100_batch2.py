#!/usr/bin/env python3
import yaml
import subprocess
import json
import time


def analyze_pr_content(pr_number, title, body):
    """PR内容を分析してラベルを決定する"""

    # タイトルと本文を結合
    content = f"タイトル: {title}\n本文: {body or ''}"

    # キーワードベースの分類
    content_lower = content.lower()

    # ビジョン関連
    if any(word in content_lower for word in ['ビジョン', 'vision', '理念', '基本方針', '目標', '将来像', '方向性']):
        return 'ビジョン'

    # デジタル民主主義
    if any(word in content_lower for word in ['投票', 'vote', 'voting', '選挙', 'election', 'デジタル民主主義', 'digital democracy', 'オンライン投票', '電子投票', 'e-voting']):
        return 'デジタル民主主義'

    # 行政改革
    if any(word in content_lower for word in ['行政', 'administration', '省庁', '官僚', '公務員', '行政改革', '政府', 'government', '統計', 'statistics']):
        return '行政改革'

    # 教育
    if any(word in content_lower for word in ['教育', 'education', '学校', 'school', '学習', 'learning', '教師', 'teacher', '学生', 'student', '大学', 'university']):
        return '教育'

    # 福祉
    if any(word in content_lower for word in ['福祉', 'welfare', '社会保障', 'social security', '年金', 'pension', '介護', 'care', '障害', 'disability', '高齢者', 'elderly']):
        return '福祉'

    # 子育て
    if any(word in content_lower for word in ['子育て', 'childcare', '育児', '保育', 'nursery', '子ども', 'children', '児童', '幼児', '出産', 'birth']):
        return '子育て'

    # 医療
    if any(word in content_lower for word in ['医療', 'medical', 'healthcare', '健康', 'health', '病院', 'hospital', '医師', 'doctor', '看護', 'nursing']):
        return '医療'

    # 経済財政
    if any(word in content_lower for word in ['経済', 'economy', '財政', 'finance', '予算', 'budget', '税', 'tax', '金融', 'financial', '投資', 'investment']):
        return '経済財政'

    # 産業政策
    if any(word in content_lower for word in ['産業', 'industry', '企業', 'company', 'business', '製造', 'manufacturing', '農業', 'agriculture', '漁業', 'fishery']):
        return '産業政策'

    # 科学技術
    if any(word in content_lower for word in ['科学', 'science', '技術', 'technology', '研究', 'research', 'ai', '人工知能', 'iot', 'dx', 'デジタル変革']):
        return '科学技術'

    # エネルギー
    if any(word in content_lower for word in ['エネルギー', 'energy', '電力', 'power', '再生可能', 'renewable', '原発', 'nuclear', '環境', 'environment']):
        return 'エネルギー'

    # システム関連
    if any(word in content_lower for word in ['システム', 'system', 'プログラム', 'program', 'コード', 'code', 'バグ', 'bug', 'エラー', 'error']):
        return '[システム]'

    # デフォルトはその他政策
    return 'その他政策'


def get_pr_details(pr_number):
    """GitHub CLIを使ってPRの詳細を取得"""
    try:
        cmd = f"gh pr view {pr_number} --json title,body,files"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            pr_data = json.loads(result.stdout)
            return pr_data
        else:
            print(f"PR #{pr_number} の詳細取得に失敗: {result.stderr}")
            return None
    except Exception as e:
        print(f"PR #{pr_number} の詳細取得でエラー: {e}")
        return None


def analyze_next2_batch2():
    """次の100件分析（第2弾）のバッチ2を分析"""

    # バッチ情報を読み込み
    with open('next2_100_batch2_info.yaml', 'r', encoding='utf-8') as f:
        batch_info = yaml.safe_load(f)

    # readme-pr.yamlを読み込み
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    pr_numbers = batch_info['prs']
    results = []

    print(f"=== 次の100件分析（第2弾） - バッチ2分析開始 ===")
    print(f"対象PR数: {len(pr_numbers)}件")
    print(f"PR範囲: {batch_info['pr_range']}")

    for i, pr_number in enumerate(pr_numbers, 1):
        print(f"\n[{i}/{len(pr_numbers)}] PR #{pr_number} を分析中...")

        # PRの基本情報を取得
        pr_info = None
        for pr in data['pull_requests']:
            if pr['number'] == pr_number:
                pr_info = pr
                break

        if not pr_info:
            print(f"PR #{pr_number} が見つかりません")
            continue

        # GitHub APIから詳細情報を取得
        pr_details = get_pr_details(pr_number)

        if pr_details:
            title = pr_details.get('title', pr_info.get('title', ''))
            body = pr_details.get('body', '')
        else:
            title = pr_info.get('title', '')
            body = ''

        # 分析実行
        new_label = analyze_pr_content(pr_number, title, body)

        result = {
            'number': pr_number,
            'title': title,
            'new_label': new_label,
            'analysis_reason': f"タイトル・内容から{new_label}に分類"
        }
        results.append(result)

        print(f"PR #{pr_number}: {title[:50]}... → {new_label}")

        # API制限を避けるため少し待機
        time.sleep(0.5)

    # 結果を保存
    output_data = {
        'batch_info': batch_info,
        'analysis_results': results,
        'summary': {
            'total_analyzed': len(results),
            'label_distribution': {}
        }
    }

    # ラベル分布を計算
    for result in results:
        label = result['new_label']
        output_data['summary']['label_distribution'][label] = output_data['summary']['label_distribution'].get(
            label, 0) + 1

    with open('next2_100_batch2_results.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True)

    print(f"\n=== 分析完了 ===")
    print(f"分析済みPR数: {len(results)}件")
    print(f"結果を next2_100_batch2_results.yaml に保存しました")

    # ラベル分布を表示
    print(f"\n=== ラベル分布 ===")
    for label, count in sorted(output_data['summary']['label_distribution'].items()):
        print(f"- {label}: {count}件")

    return results


if __name__ == "__main__":
    analyze_next2_batch2()
