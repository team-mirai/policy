#!/bin/bash
# 古いスクリプトを整理

echo "古いスクリプトを整理します..."
echo "以下のファイルをarchive/old_scriptsに移動します："

# アーカイブディレクトリを作成
mkdir -p archive/old_scripts

# 移動対象のファイル
OLD_FILES=(
    "create_batch*.py"
    "get_batch*_pr_details.py"
    "export_batch*_to_csv.py"
    "update_batch*_status.py"
    "export_to_csv_correct.py"
    "combine_all_csvs.py"
    "check_classified_prs.py"
    "classify_all_prs.py"
    "get_all_readme_prs.py"
    "merge_pr_data.py"
)

# ファイルを移動
for pattern in "${OLD_FILES[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            echo "  - $file"
            mv "$file" archive/old_scripts/
        fi
    done
done

# 古い分析ファイルも移動
echo ""
echo "古い分析ファイルを移動します："
mkdir -p archive/old_analysis
for file in analysis_*.md; do
    if [ -f "$file" ]; then
        echo "  - $file"
        mv "$file" archive/old_analysis/
    fi
done

# 古いバッチファイルも移動
echo ""
echo "古いバッチファイルを移動します："
mkdir -p archive/old_batches
for file in batch*.yaml; do
    if [ -f "$file" ]; then
        echo "  - $file"
        mv "$file" archive/old_batches/
    fi
done

echo ""
echo "整理完了！"
echo ""
echo "残っている重要なファイル："
echo "  - pr_classifier_system.py (メインスクリプト)"
echo "  - Makefile (実行用)"
echo "  - README.md (ドキュメント)"
echo "  - readme-pr-merged.yaml (元データ)"
echo ""
echo "アーカイブされたファイルは archive/ ディレクトリにあります"