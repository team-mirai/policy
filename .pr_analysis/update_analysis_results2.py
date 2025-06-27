#!/usr/bin/env python3
import yaml

# 分析結果（2番目の20件）
analysis_results2 = {
    1856: {
        'new_label': 'ビジョン',
        'analysis_notes': '人間性の涵養と主体的な生き方のサポートに関する記述追加による基本理念の表明'
    },
    1854: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': 'デジタル化推進における情報弱者への配慮を明記するデジタル民主主義政策'
    },
    1851: {
        'new_label': '産業政策',
        'analysis_notes': '農業政策における高収益化の実現に関する産業振興提案'
    },
    1849: {
        'new_label': 'ビジョン',
        'analysis_notes': '政策公募の姿勢を明確化する基本方針の表明'
    },
    1844: {
        'new_label': '行政改革',
        'analysis_notes': '歳出改革と行政の透明化を最優先課題として明記する行政改革提案'
    },
    1843: {
        'new_label': '医療',
        'analysis_notes': '子どもの矯正歯科治療の保険適用に関する医療制度改革提案'
    },
    1841: {
        'new_label': '福祉',
        'analysis_notes': '総合的な社会保障改革案「みんなで築く 未来への安心社会保障プラン」'
    },
    1840: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': '国会におけるデジタル機器活用推進と議論活性化の提案'
    },
    1834: {
        'new_label': '子育て',
        'analysis_notes': 'ステップ3に少子化対策の項目を追加する子育て支援政策'
    },
    1831: {
        'new_label': '[システム]',
        'analysis_notes': 'ステップ１に情報セキュリティ項目を追加するシステム関連提案'
    },
    1826: {
        'new_label': '産業政策',
        'analysis_notes': '農業政策に関する産業振興提案'
    },
    1822: {
        'new_label': 'デジタル民主主義',
        'analysis_notes': '議員の通信簿データベース作成による政治の透明化・情報公開提案'
    },
    1820: {
        'new_label': 'ビジョン',
        'analysis_notes': 'システム、説明責任、熟議システム運用姿勢に関するマニフェスト改善提案'
    },
    1818: {
        'new_label': '産業政策',
        'analysis_notes': '生成AIを活用したレガシーITシステム刷新による産業競争力強化'
    },
    1814: {
        'new_label': '産業政策',
        'analysis_notes': '採用選考における差別的情報収集の制限と公正性の確保に関する労働政策'
    },
    1813: {
        'new_label': 'その他政策',
        'analysis_notes': '転売対策に関する提案'
    },
    1809: {
        'new_label': '[システム]',
        'analysis_notes': 'WIP: Changes for idobata-dgu4jo - システム関連の技術的修正'
    },
    1808: {
        'new_label': 'ビジョン',
        'analysis_notes': '革新的な政策アイデアを積極的に議論する姿勢を表明する基本方針'
    },
    1801: {
        'new_label': '[システム]',
        'analysis_notes': 'システムトラブル発生時の対応と説明責任に関するシステム運用提案'
    },
    1791: {
        'new_label': '科学技術',
        'analysis_notes': 'シミュレーション仮説の研究を通じたデジタル民主主義の深化に関する科学技術政策'
    }
}


def update_yaml_with_analysis2():
    # YAMLファイルを読み込み
    with open('readme-pr.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 分析結果を反映
    updated_count = 0
    for pr in data['pull_requests']:
        pr_number = pr['number']
        if pr_number in analysis_results2:
            result = analysis_results2[pr_number]
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
    update_yaml_with_analysis2()
