# PR分類システム Makefile
# 再現性の高い実行のため

.PHONY: help fetch classify merge clean setup

# デフォルトターゲット
help:
	@echo "PR分類システム - 使用方法:"
	@echo ""
	@echo "make setup      - 初期セットアップ（ディレクトリ作成）"
	@echo "make fetch      - GitHubから最新のPRを取得して分類"
	@echo "make classify   - 既存データを使用して分類（要INPUT指定）"
	@echo "make merge      - 分類結果を統合"
	@echo "make clean      - 一時ファイルを削除"
	@echo "make report     - 分類結果のレポート生成"
	@echo ""
	@echo "例:"
	@echo "  make fetch                    # 最新データで分類実行"
	@echo "  make classify INPUT=data/readme_prs_20250714.yaml  # 既存データで分類"

# セットアップ
setup:
	@echo "ディレクトリをセットアップ中..."
	@mkdir -p data output archive
	@echo "完了"

# GitHubから取得して分類
fetch: setup
	@echo "GitHubから最新のPRを取得して分類を開始..."
	python3 pr_classifier_system.py --fetch

# 既存データで分類
classify: setup
	@if [ -z "$(INPUT)" ]; then \
		echo "エラー: INPUTを指定してください"; \
		echo "例: make classify INPUT=data/readme_prs_20250714.yaml"; \
		exit 1; \
	fi
	@echo "既存データで分類を開始: $(INPUT)"
	python3 pr_classifier_system.py --input $(INPUT)

# 結果を統合
merge:
	@echo "分類結果を統合中..."
	python3 pr_classifier_system.py --merge

# レポート生成
report: merge
	@echo "レポートを生成中..."
	@python3 -c "import csv; \
		with open('output/merged_all_latest.csv', 'r', encoding='utf-8-sig') as f: \
			reader = list(csv.DictReader(f)); \
			total = len(reader); \
			labels = {}; \
			for row in reader: \
				label = row['政策分野（新ラベル）']; \
				labels[label] = labels.get(label, 0) + 1; \
			print('\n=== PR分類レポート ==='); \
			print(f'総PR数: {total}'); \
			print('\nラベル別分類結果:'); \
			for label, count in sorted(labels.items(), key=lambda x: x[1], reverse=True): \
				print(f'  {label}: {count}件 ({count/total*100:.1f}%)')"

# クリーンアップ
clean:
	@echo "一時ファイルを削除中..."
	@rm -f data/prompt_pr_*.txt
	@echo "完了"

# アーカイブ（古い結果を保存）
archive:
	@echo "古い結果をアーカイブ中..."
	@mkdir -p archive/$(shell date +%Y%m%d)
	@mv output/*.csv archive/$(shell date +%Y%m%d)/ 2>/dev/null || true
	@echo "完了"

# 全体的なワークフロー
all: fetch merge report
	@echo "すべての処理が完了しました"