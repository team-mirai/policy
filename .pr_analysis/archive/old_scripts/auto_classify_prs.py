#!/usr/bin/env python3
"""
PRタイトルと内容から政策分野を自動分類するスクリプト
"""

import re

def classify_pr(title, body="", diff=""):
    """PRを政策分野に分類"""
    
    # テキストを結合して小文字化
    full_text = f"{title} {body} {diff}".lower()
    
    # キーワードベースの分類ルール
    classification_rules = {
        '[システム]': [
            'readme', 'マニフェスト.*修正', 'マニフェスト.*改善', 'タイポ', '誤字', 
            '誤記', 'リンク.*修正', 'フォーマット', '文章校正', 'メタデータ',
            'ファイル名', 'ディレクトリ', 'github', 'git'
        ],
        'ビジョン': [
            '基本理念', '基本方針', '政治理念', 'ビジョン', '基本姿勢',
            'sogi', 'lgbtq', '多様性', '共生社会', '人権', '尊厳'
        ],
        'デジタル民主主義': [
            'デジタル民主主義', 'オープンガバメント', '透明性', '情報公開',
            'インターネット投票', 'オンライン投票', '電子投票', '選挙.*デジタル',
            '参加型民主主義', '市民参加', 'いどばた'
        ],
        '行政改革': [
            '行政改革', '規制改革', 'デジタル庁', '行政.*効率化', '公務員',
            '官僚', '省庁', '行政.*デジタル化', 'dx', '電子政府'
        ],
        '教育': [
            '教育', '学校', '大学', '学習', '教育改革', '学力', '教師',
            '教員', 'ict教育', 'stem', 'プログラミング教育', '給食'
        ],
        '福祉': [
            '福祉', '社会保障', '年金', '介護', '高齢者', '障害者', '障がい',
            'バリアフリー', '生活保護', 'セーフティネット', '社会的弱者'
        ],
        '子育て': [
            '子育て', '育児', '少子化', '出産', '妊娠', '保育', '児童',
            '子ども', '母子', '父子', '養育費', '児童手当', '待機児童'
        ],
        '医療': [
            '医療', '健康', '病院', '医師', '看護', '薬', '治療',
            '診療', '健康保険', '医療保険', 'コロナ', 'ワクチン'
        ],
        '経済財政': [
            '経済', '財政', '税', '予算', '財源', '税制', '財政改革',
            '経済成長', '景気', 'gdp', '財務', '国債', '赤字'
        ],
        '産業政策': [
            '産業', '企業', '中小企業', 'スタートアップ', '起業', '雇用',
            '労働', '働き方', '賃金', '最低賃金', '非正規', '就労支援'
        ],
        '科学技術': [
            '科学技術', 'ai', '人工知能', 'ロボット', '研究開発', 'イノベーション',
            '技術革新', '研究', '開発', 'iot', 'ブロックチェーン'
        ],
        'エネルギー': [
            'エネルギー', '電力', '原発', '再生可能エネルギー', '太陽光',
            '風力', '環境', '気候変動', '脱炭素', 'カーボンニュートラル'
        ],
        'その他政策': [
            '外交', '防衛', '自衛隊', '憲法', '安全保障', '犯罪',
            '司法', '警察', '交通', 'インフラ', '災害', '防災'
        ]
    }
    
    # 各分類のスコアを計算
    scores = {}
    for category, keywords in classification_rules.items():
        score = 0
        for keyword in keywords:
            if re.search(keyword, full_text):
                score += 1
        if score > 0:
            scores[category] = score
    
    # 最もスコアの高いカテゴリを返す
    if scores:
        return max(scores, key=scores.get)
    else:
        return 'その他政策'  # デフォルト

def analyze_pr_for_classification(pr_data):
    """PR情報から分類に必要な情報を抽出"""
    
    # タイトルから提案者名を除去
    title = pr_data.get('title', '')
    # 「○○さん提案：」のパターンを除去
    title_clean = re.sub(r'^.*?さん提案[：:]', '', title)
    title_clean = re.sub(r'^.*?提案[：:]', '', title_clean)
    title_clean = re.sub(r'^【.*?】', '', title_clean)
    
    # 本文から重要な部分を抽出（最初の1000文字）
    body = pr_data.get('body', '')[:1000] if pr_data.get('body') else ''
    
    # 差分から重要な部分を抽出
    diff = pr_data.get('diff', '')[:1000] if pr_data.get('diff') else ''
    
    # 分類を実行
    category = classify_pr(title_clean, body, diff)
    
    # 分類理由を生成
    reason = f"タイトル「{title_clean[:50]}」と内容から{category}に分類"
    
    return {
        'category': category,
        'reason': reason,
        'title_clean': title_clean
    }

def main():
    """テスト用のメイン関数"""
    test_cases = [
        {
            'title': 'マニフェストの基本方針の明確化と誤字の修正',
            'body': 'タイポが発見されたため、これを「マニフェスト」に修正しております。'
        },
        {
            'title': '提案：チームみらいの基本姿勢にSOGIに関する記述を追加',
            'body': 'LGBTQに関連するようなマニフェストはありますか？'
        },
        {
            'title': '選挙の参加しやすさと公平性を高めるための包括的提案',
            'body': 'インターネット投票制度の導入'
        }
    ]
    
    for pr in test_cases:
        result = analyze_pr_for_classification(pr)
        print(f"タイトル: {pr['title']}")
        print(f"分類: {result['category']}")
        print(f"理由: {result['reason']}")
        print("---")

if __name__ == "__main__":
    main()