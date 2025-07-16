# Policy PR Analyzer 実行手順

## 現在の状態

✅ **データ取得完了**: 教育ラベルのPR 50件を取得済み
✅ **プロンプト生成完了**: LLM分析用のプロンプトを生成済み
✅ **分析スクリプト作成**: `analyze_prompts.py`で一括実行可能

## 分析実行方法

### 方法1: スクリプトで一括実行（推奨）

```bash
cd policy_pr_analyzer

# すべての分析を実行
python3 scripts/analyze_prompts.py prompts/batch_50

# 個別PR分析のみ実行
python3 scripts/analyze_prompts.py prompts/batch_50 --type individual

# ドライラン（実行内容を確認）
python3 scripts/analyze_prompts.py prompts/batch_50 --dry-run

# 進捗状況を確認
python3 scripts/analyze_prompts.py prompts/batch_50 --status

# 類似度チェックを10件に制限して実行
python3 scripts/analyze_prompts.py prompts/batch_50 --type similarity --similarity-limit 10
```

### 方法2: 手動実行

スクリプトを使わずに手動で実行する場合：

```bash
cd policy_pr_analyzer

# 個別PR分析
for f in prompts/batch_50/individual/*.txt; do
  out="prompts/batch_50/output/individual/$(basename "$f" .txt).json"
  echo "Analyzing $(basename $f)..."
  claude -p < "$f" > "$out"
  sleep 2
done

# 全体傾向分析
claude -p < prompts/batch_50/trend/overall_trend_analysis.txt > prompts/batch_50/output/trend/overall_trend_analysis.json
```

## スクリプトの機能

`analyze_prompts.py`は以下の機能を提供します：

### 基本機能
- **一括分析実行**: 個別PR、類似度チェック、全体傾向を順番に分析
- **進捗管理**: 既に分析済みのファイルをスキップ（--no-resumeで無効化可能）
- **API制限対策**: 各分析間に2秒のスリープ（--sleepで調整可能）
- **エラーハンドリング**: 失敗した分析をスキップして続行

### オプション機能
- **--status**: 現在の分析進捗を表示
- **--dry-run**: 実際には実行せず、何を行うか表示
- **--type**: 特定の分析タイプのみ実行（individual/similarity/trend）
- **--similarity-limit**: 類似度チェックの実行数を制限
- **--no-resume**: すべてのファイルを再分析

## 出力ファイル

- **個別分析結果**: `prompts/batch_50/output/individual/pr_*_analysis.json`
- **類似度分析結果**: `prompts/batch_50/output/similarity/similarity_*.json`
- **全体傾向分析**: `prompts/batch_50/output/trend/overall_trend_analysis.json`

## 注意事項

1. **API制限**: 各分析の間に2秒のスリープを入れています
2. **時間**: 50件の個別分析には約2-3分かかります
3. **出力形式**: 各分析結果はJSON形式で出力されます

## 分析後の処理

分析結果が揃ったら、以下のスクリプトで処理できます：

- `parse_llm_results.py`: JSON結果をパース・集計
- `group_similar_prs.py`: 類似提案をグループ化
- `generate_report.py`: 政策チーム向けレポート生成

（これらのスクリプトは今後作成予定）