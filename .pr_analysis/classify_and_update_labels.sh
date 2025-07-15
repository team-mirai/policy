#!/bin/bash
#
# READMEラベルのPRを分析・分類してGitHubラベルを更新する
# 使用方法: ./classify_and_update_labels.sh [--open-only] [--dry-run]
#

set -e

# オプション解析
OPEN_ONLY=""
DRY_RUN=""
LIMIT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --open-only)
            OPEN_ONLY="--open-only"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --limit)
            LIMIT="-l $2"
            shift 2
            ;;
        *)
            echo "不明なオプション: $1"
            echo "使用方法: $0 [--open-only] [--dry-run] [--limit N]"
            exit 1
            ;;
    esac
done

echo "=== READMEラベルPR分析・更新スクリプト ==="
echo ""

# タイムスタンプ
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 1. READMEラベルのPRを取得
echo "ステップ1: READMEラベルのPRを取得..."
PR_STATE="all"
if [[ -n "$OPEN_ONLY" ]]; then
    PR_STATE="open"
fi

python3 get_readme_prs.py -s $PR_STATE -o readme_prs_${TIMESTAMP}.csv

# 2. PR分析・分類
echo ""
echo "ステップ2: PRを分析・分類..."
python3 claude_pr_classifier.py readme_prs_${TIMESTAMP}.csv -o classified_prs_${TIMESTAMP}.csv

# 3. ラベル表記揺れ修正
echo ""
echo "ステップ3: ラベル表記を修正..."
python3 fix_label_format.py classified_prs_${TIMESTAMP}.csv

# 4. GitHubラベル更新
echo ""
echo "ステップ4: GitHubラベルを更新..."
UPDATE_OPTS="$OPEN_ONLY $DRY_RUN $LIMIT"
python3 update_pr_labels.py -i classified_prs_${TIMESTAMP}_fixed.csv $UPDATE_OPTS

echo ""
echo "=== 完了 ==="
echo "分析結果: classified_prs_${TIMESTAMP}_fixed.csv"