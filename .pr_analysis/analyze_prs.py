#!/usr/bin/env python3
import yaml
import json
import subprocess
import time
from typing import List, Dict, Any


def load_yaml_data():
    """YAML ファイルから PR データを読み込む"""
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_unprocessed_prs(data: Dict[str, Any], limit: int = 80) -> List[Dict[str, Any]]:
    """未処理の PR を取得"""
    unprocessed = []
    for pr in data['pull_requests']:
        if pr.get('label_updated') == False and pr.get('number') != 1998:  # 例のPRを除外
            unprocessed.append(pr)
            if len(unprocessed) >= limit:
                break
    return unprocessed


def get_pr_details(pr_number: int) -> Dict[str, Any]:
    """GitHub API を使って PR の詳細情報を取得"""
    try:
        # PR の基本情報を取得
        cmd = f"gh pr view {pr_number} --json title,body,state,author,url,createdAt"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ PR #{pr_number} の情報取得に失敗: {result.stderr}")
            return None

        pr_info = json.loads(result.stdout)

        # PR の diff を取得
        diff_cmd = f"gh pr diff {pr_number}"
        diff_result = subprocess.run(
            diff_cmd, shell=True, capture_output=True, text=True)

        pr_info['diff'] = diff_result.stdout if diff_result.returncode == 0 else ""

        return pr_info

    except Exception as e:
        print(f"❌ PR #{pr_number} の処理中にエラー: {e}")
        return None


def classify_pr(pr_info: Dict[str, Any]) -> tuple[str, str]:
    """PR の内容を分析して分類"""
    title = pr_info.get('title', '')
    body = pr_info.get('body', '')
    diff = pr_info.get('diff', '')

    # 分析ロジック
    content = f"{title} {body} {diff}".lower()

    # システム関連
    if any(keyword in content for keyword in ['readme', 'マニフェスト', '構成', '記述', 'システム', '運用', 'github', 'プロセス']):
        if any(keyword in content for keyword in ['政策', '提案', '項目', '追加', '改革', '制度']):
            # 政策内容を含む場合は詳細分析
            pass
        else:
            return '[システム]', 'マニフェストの構成や運用システムに関する提案'

    # 教育関連
    if any(keyword in content for keyword in ['教育', '学校', '学習', '才能', '奨学金', '大学', '学費']):
        return '教育', '教育制度や学習環境に関する政策提案'

    # 子育て関連
    if any(keyword in content for keyword in ['子育て', '子ども', '少子化', '児童', '保育', '養育']):
        return '子育て', '子育て支援や児童福祉に関する政策提案'

    # 福祉関連
    if any(keyword in content for keyword in ['福祉', '社会保障', '介護', '障害者', '高齢者', 'ベーシックインカム']):
        return '福祉', '社会保障制度や福祉政策に関する提案'

    # 医療関連
    if any(keyword in content for keyword in ['医療', '健康', '病院', '診療', '薬']):
        return '医療', '医療制度や健康政策に関する提案'

    # 行政改革関連
    if any(keyword in content for keyword in ['行政', 'デジタル化', 'dx', '手続き', '申請', '検収', '効率化']):
        return '行政改革', '行政手続きの改革やデジタル化に関する提案'

    # デジタル民主主義関連
    if any(keyword in content for keyword in ['民主主義', '政治参加', '透明性', '議員', '選挙', '誤報対策']):
        return 'デジタル民主主義', '政治参加や民主主義の発展に関する提案'

    # 経済財政関連
    if any(keyword in content for keyword in ['経済', '財政', '税', '予算', 'グラフィックス', '可視化']):
        return '経済財政', '経済政策や財政制度に関する提案'

    # エネルギー関連
    if any(keyword in content for keyword in ['エネルギー', '電力', '原子力', '再生可能']):
        return 'エネルギー', 'エネルギー政策に関する提案'

    # 産業政策関連
    if any(keyword in content for keyword in ['産業', '農業', '製造業', 'ビジネス']):
        return '産業政策', '産業振興や農業政策に関する提案'

    # 科学技術関連
    if any(keyword in content for keyword in ['科学', '技術', 'ai', '人工知能', 'テクノロジー']):
        return '科学技術', '科学技術政策に関する提案'

    # ビジョン関連
    if any(keyword in content for keyword in ['ビジョン', '将来', '方向性', '道筋', '文化立国']):
        return 'ビジョン', '国家ビジョンや将来構想に関する提案'

    # その他
    return 'その他政策', '上記カテゴリに該当しない政策提案'


def main():
    print("📊 未処理 PR の分析を開始します...")

    # YAML データを読み込み
    data = load_yaml_data()

    # 未処理 PR を取得（上位80件）
    unprocessed_prs = get_unprocessed_prs(data, 80)
    print(f"🔍 分析対象: {len(unprocessed_prs)} 件の未処理 PR")

    # 分析結果を保存
    analysis_results = []

    for i, pr in enumerate(unprocessed_prs, 1):
        pr_number = pr['number']
        print(f"📝 [{i:2d}/80] PR #{pr_number} を分析中...")

        # PR 詳細情報を取得
        pr_details = get_pr_details(pr_number)
        if not pr_details:
            continue

        # 分類を実行
        new_label, analysis_notes = classify_pr(pr_details)

        analysis_results.append({
            'number': pr_number,
            'title': pr['title'],
            'new_label': new_label,
            'analysis_notes': analysis_notes,
            'classification_reason': f"タイトル・本文・差分を分析した結果、{new_label}分野の政策提案と判定"
        })

        print(f"   ✅ 分類: {new_label} - {analysis_notes}")

        # API レート制限対策
        time.sleep(0.5)

    # 結果を JSON ファイルに保存
    with open('pr_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 分析完了！結果を pr_analysis_results.json に保存しました")

    # 統計情報を表示
    label_counts = {}
    for result in analysis_results:
        label = result['new_label']
        label_counts[label] = label_counts.get(label, 0) + 1

    print("\n📈 分類結果統計:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {label}: {count}件")


if __name__ == "__main__":
    main()
