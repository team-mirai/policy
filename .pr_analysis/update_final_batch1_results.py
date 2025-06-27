#!/usr/bin/env python3
import yaml

# 最終バッチ1の分析結果（10件）
final_batch1_results = {
    1787: {
        'new_label': '産業政策',
        'analysis_notes': 'AI・ドローン技術を活用した農業支援、山間部農業の高付加価値化など、農業分野の産業振興・経済活動支援に関する具体的な提案'
    },
    1777: {
        'new_label': '経済財政',
        'analysis_notes': '贈与税の非課税枠拡大、相続税の累進課税強化など、税制・財政政策に関する提案。若者支援と経済活性化を目的とした経済政策'
    },
    1775: {
        'new_label': '医療',
        'analysis_notes': '食を通じた健康増進、予防医療の推進、QOL向上など、健康政策・医療制度に関する提案。オーガニック食品による健康維持・増進'
    },
    1774: {
        'new_label': '福祉',
        'analysis_notes': '社会保障制度（年金、医療、介護、子育て支援、生活困窮者支援など）に関する項目追加。社会保障・高齢者支援分野の政策提案'
    },
    1771: {
        'new_label': '福祉',
        'analysis_notes': '社会保障制度の項目追加。年金、医療、介護、子育て支援、生活困窮者支援などを含む社会保障分野の政策提案'
    },
    1765: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': 'デジタル技術を活用した政策形成プロセス、専門家と市民の議論の場の設置など、デジタル民主主義に関する提案'
    },
    1762: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': 'SNS運用の透明性、デジタル技術を活用した情報発信・コミュニケーションに関する提案'
    },
    1757: {
        'new_label': '経済財政',
        'analysis_notes': '生涯所得課税という税制改革、経済政策・財政政策に関する提案。所得変動に対する公平な課税制度の導入'
    },
    1755: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': '意思決定プロセスの透明化、民主的な運営、オープンな議論に関する提案。デジタル民主主義の理念に関する内容'
    },
    1752: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': 'AI技術を活用した社会課題の自動抽出、議論のきっかけ作り、デジタル技術による民主主義の発展に関する提案'
    }
}


def update_yaml_with_results():
    # YAMLファイルを読み込み
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    updated_count = 0

    # 各PRの分析結果を更新
    for pr in data['pull_requests']:
        pr_number = pr['number']
        if pr_number in final_batch1_results:
            result = final_batch1_results[pr_number]
            pr['new_label'] = result['new_label']
            pr['analysis_notes'] = result['analysis_notes']
            pr['classification_reason'] = 'PR内容を詳細分析した結果、' + \
                result['new_label'] + '分野の政策提案と判定'
            updated_count += 1

    # YAMLファイルに書き戻し
    with open('readme-pr.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False)

    print(f"最終バッチ1の分析結果を反映しました: {updated_count}件")

    # 統計情報を表示
    total_unanalyzed = 0
    for pr in data['pull_requests']:
        if (pr.get('label_updated') == False and
                (pr.get('new_label') is None or pr.get('new_label') == 'None')):
            total_unanalyzed += 1

    print(f"残り未分析PR数: {total_unanalyzed}件")
    print(f"目標300件まで: あと{total_unanalyzed - 300}件の分析が必要")


if __name__ == "__main__":
    update_yaml_with_results()
