#!/usr/bin/env python3
import yaml

# 分析結果（最初の20件）
analysis_results = {
    1998: {
        'new_label': '医療',
        'analysis_notes': '美容医療制度の改革、医療滞在ビザの見直し、看護師認定制度など、医療制度・健康政策に関する包括的な提案'
    },
    1935: {
        'new_label': 'ビジョン',
        'analysis_notes': '国家の基本的な方向性、社会全体の課題認識、長期戦略に関する内容で、マニフェスト全体の理念・ビジョンを示すもの'
    },
    1933: {
        'new_label': '経済財政',
        'analysis_notes': 'ベーシックインカム導入という経済政策・財政政策に関する提案'
    },
    1928: {
        'new_label': '教育',
        'analysis_notes': '学校外教育、才能育成支援、マッチングシステムなど、教育制度・学習支援に関する提案'
    },
    1924: {
        'new_label': '経済財政',
        'analysis_notes': '消費税改革、政府資産運用、新税導入など、税制・財政政策に関する提案'
    },
    1923: {
        'new_label': 'ビジョン',
        'analysis_notes': '国家の基本方針、課題認識、未来社会のあり方など、長期戦略・ビジョンに関する内容'
    },
    1916: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': 'デジタル技術を活用した民主主義、情報公開に関する提案'
    },
    1911: {
        'new_label': '行政改革',
        'analysis_notes': '財政システムの可視化、政府DX、行政効率化に関する提案'
    },
    1910: {
        'new_label': '産業政策',
        'analysis_notes': '農業振興、植物工場団地構想など産業振興・経済活動支援に関する提案'
    },
    1907: {
        'new_label': '福祉',
        'analysis_notes': '介護制度、高齢者支援、社会保障に関する提案'
    },
    1905: {
        'new_label': '行政改革',
        'analysis_notes': '行政効率化、制度運用改善に関する提案'
    },
    1901: {
        'new_label': '産業政策',
        'analysis_notes': '非正規雇用・派遣労働の構造問題と待遇改善に関する労働政策提案'
    },
    1900: {
        'new_label': 'その他政策',
        'analysis_notes': '訪日外国人観光客の海外旅行保険加入義務化について'
    },
    1897: {
        'new_label': 'ビジョン',
        'analysis_notes': 'スローガン「この社会を、生き残る。」の追加による基本理念の表明'
    },
    1888: {
        'new_label': '子育て',
        'analysis_notes': '「子ども」政策への呼称変更及び教育・子ども分野の課題追記と改善提案'
    },
    1876: {
        'new_label': 'ビジョン',
        'analysis_notes': 'マニフェスト目次構成の大幅な刷新による全体構造の改善'
    },
    1871: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': 'デジタル民主主義の推進と議員定数削減による行財政改革'
    },
    1865: {
        'new_label': 'ビジョン',
        'analysis_notes': 'キャッチフレーズ追加による基本理念の表明'
    },
    1862: {
        'new_label': '福祉',
        'analysis_notes': '更生保護改革に関する新規提案'
    },
    1858: {
        'new_label': 'その他政策',
        'analysis_notes': '香害対策、難病支援、SNS誹謗中傷対策など複数分野にわたる政策改善提案'
    }
}


def update_yaml_with_analysis():
    # YAMLファイルを読み込み
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 分析結果を反映
    updated_count = 0
    for pr in data['pull_requests']:
        pr_number = pr['number']
        if pr_number in analysis_results:
            result = analysis_results[pr_number]
            pr['new_label'] = result['new_label']
            pr['analysis_notes'] = result['analysis_notes']
            pr['classification_reason'] = 'PR内容を詳細分析した結果、' + \
                result['new_label'] + '分野の政策提案と判定'
            updated_count += 1

    # YAMLファイルに書き戻し
    with open('readme-pr.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False,
                  allow_unicode=True, sort_keys=False)

    print(f"分析結果を反映しました: {updated_count}件")

    # 統計を更新
    total_unanalyzed = 0
    for pr in data['pull_requests']:
        if (pr.get('label_updated') == False and
                (pr.get('new_label') is None or pr.get('new_label') == 'None')):
            total_unanalyzed += 1

    print(f"残り未分析PR数: {total_unanalyzed}")
    print(f"目標まで: {total_unanalyzed - 300}件の分析が必要")


if __name__ == "__main__":
    update_yaml_with_analysis()
