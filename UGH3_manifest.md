# UGH3指標（PoR・ΔE・grv）による動的意見評価機能の追加

## 概要
意見データの異常検知・語彙背景分析を強化するため、以下3つの指標を新規実装します。

- **PoR**（Point of Resonance）：質問文と意見文のコサイン類似度（[0,1]範囲）
- **ΔE**（応答エネルギー変動）：PoR値の時系列差分（|PoRₜ−PoRₜ₋₁|）
- **grv**（語彙重力）：各タイムバケットにおける全意見の語彙頻度分布エントロピー（`scipy.stats.entropy`使用）

## 目的
- 急激な意見変化や語彙の偏りをリアルタイムに把握
- 意見動向と社会的背景の連動を動的に分析・可視化

## 実装内容
- `ugh3_metrics.py`：PoR・ΔE・grv指標のコア計算モジュール
- `test_ugh3_metrics.py`：各指標の正常系・異常系テスト
- `sample_data.csv`：20件前後の時系列サンプルデータ
- `ugh3_demo.ipynb`：主要指標の推移グラフ・grvヒートマップ等の可視化デモ

## 技術詳細
- **PoR**：  
  `cosine_similarity(embedding(question), embedding(comment))`
- **ΔE**：  
  `abs(PoR[t] - PoR[t-1])`
- **grv**：  
  指定タイムバケット（例：1分/5件ごと等）に収集された全コメントを単語分割し、頻度分布からエントロピー値（float）を算出  
  例：  
  1. バケット内コメント → 単語分割  
  2. 各単語の出現頻度で分布作成  
  3. `scipy.stats.entropy` でgrv値を算出
- grvの計算単位は「バケットごとの意見集合」です（発言単位ではありません）。
- 日本語処理には必要に応じて形態素解析（Janome/MeCab等）も可
- 多言語データにも将来対応しやすいよう設計

## 入出力例
- **入力CSV**：timestamp, question, comment
- **出力CSV**：上記＋PoR, ΔE, grv（grvはバケット内各発言に付与）

## 依存ライブラリ
- Python 3.9+, numpy, pandas, scipy, sentence-transformers  
- 日本語形態素解析用ライブラリ（任意）

## 備考
- 既存OSSのデータ構造を尊重し、破壊的変更は行いません
- サンプル・デモはGoogle Colabやスマホアプリでも動作確認可能な範囲で作成

---

**ご確認・レビューをよろしくお願いします。**
