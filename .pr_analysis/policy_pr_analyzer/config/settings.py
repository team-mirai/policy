#!/usr/bin/env python3
"""
Policy PR Analyzer 設定ファイル
"""

# APIデータ取得設定
FETCH_CONFIG = {
    'default_batch_size': 50,      # デフォルトのバッチサイズ
    'cache_dir': 'cache',          # キャッシュディレクトリ
    'rate_limit_sleep': 0.5,       # API呼び出し間隔（秒）
    'max_diff_lines': 1000,        # diff最大行数
    'pr_body_limit': 3000,         # PR本文の文字数制限
}

# LLM分析設定
ANALYSIS_CONFIG = {
    'prompt_body_limit': 3000,     # プロンプトに含めるPR本文の最大文字数
    'prompt_diff_limit': 3000,     # プロンプトに含めるdiffの最大文字数
    'similarity_sample_size': 10,  # 類似度チェックのサンプル数
    'trend_analysis_limit': 50,    # 傾向分析に含めるPR数の上限
}

# 教育政策のカテゴリ定義
EDUCATION_CATEGORIES = [
    'カリキュラム改革',
    '教員・人材',
    '設備・インフラ',
    '制度・システム',
    '予算・財源',
    'デジタル化',
    '地域連携',
    'その他'
]

# 出力設定
OUTPUT_CONFIG = {
    'output_dir': 'output',
    'data_subdir': 'data',
    'reports_subdir': 'reports',
    'spreadsheets_subdir': 'spreadsheets',
}

# リポジトリ設定
REPO_CONFIG = {
    'owner': 'team-mirai',
    'repo': 'policy',
    'default_state': 'open',  # open, closed, all
}