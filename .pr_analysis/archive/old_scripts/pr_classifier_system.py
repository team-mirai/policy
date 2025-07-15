#!/usr/bin/env python3
"""
PR分類システム - 統合版
再現性の高い、整理されたPR分類処理
"""
import yaml
import csv
import subprocess
import json
import time
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 設定
CONFIG = {
    'repo': 'team-mirai/policy',
    'batch_size': 50,
    'output_dir': 'output',
    'data_dir': 'data',
    'rate_limit_sleep': 0.5,
    'policy_labels': [
        "ビジョン",
        "デジタル民主主義", 
        "行政改革",
        "教育",
        "福祉",
        "子育て",
        "医療",
        "経済財政",
        "産業政策",
        "科学技術",
        "エネルギー",
        "その他政策",
        "[システム]"
    ]
}

class PRClassifier:
    def __init__(self, config):
        self.config = config
        self.setup_directories()
        
    def setup_directories(self):
        """ディレクトリ構造をセットアップ"""
        Path(self.config['output_dir']).mkdir(exist_ok=True)
        Path(self.config['data_dir']).mkdir(exist_ok=True)
        
    def fetch_all_readme_prs(self):
        """GitHubからREADMEラベルのPRを取得"""
        print("GitHubからREADMEラベルのPRを取得中...")
        cmd = [
            "gh", "pr", "list",
            "--repo", self.config['repo'],
            "--label", "README",
            "--state", "open",
            "--limit", "600",
            "--json", "number,title,author,createdAt,url,labels,state"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"エラー: {result.stderr}")
            return []
        
        prs = json.loads(result.stdout)
        
        # YAMLに保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.config['data_dir']}/readme_prs_{timestamp}.yaml"
        
        data = {
            'fetch_time': datetime.now().isoformat(),
            'total_count': len(prs),
            'pull_requests': prs
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
        print(f"  {len(prs)}件のPRを取得")
        print(f"  保存先: {filename}")
        return filename
    
    def load_existing_classifications(self):
        """既存の分類結果を読み込む"""
        classifications = {}
        
        # outputディレクトリのCSVファイルを読み込む
        csv_files = Path(self.config['output_dir']).glob('*.csv')
        
        for csv_file in csv_files:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pr_num = int(row['PR番号'])
                    classifications[pr_num] = {
                        'label': row['政策分野（新ラベル）'],
                        'reason': row['分類理由'],
                        'source': csv_file.name
                    }
        
        return classifications
    
    def get_pr_details(self, pr_number):
        """PR詳細を取得してキャッシュ"""
        cache_file = f"{self.config['data_dir']}/pr_{pr_number}.json"
        
        # キャッシュチェック
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # PR詳細を取得
        cmd = ["gh", "pr", "view", str(pr_number), 
               "--repo", self.config['repo'], 
               "--json", "body,title,files,additions,deletions"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return None
        
        pr_data = json.loads(result.stdout)
        
        # 差分を取得（最初の300行）
        diff_cmd = ["gh", "pr", "diff", str(pr_number), "--repo", self.config['repo']]
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
        
        if diff_result.returncode == 0:
            diff_lines = diff_result.stdout.split('\n')[:300]
            pr_data['diff'] = '\n'.join(diff_lines)
        
        # キャッシュに保存
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(pr_data, f, ensure_ascii=False, indent=2)
        
        return pr_data
    
    def create_classification_prompt(self, pr_number, pr_info, pr_details):
        """分類用プロンプトを作成"""
        prompt_file = f"{self.config['data_dir']}/prompt_pr_{pr_number}.txt"
        
        prompt = f"""以下のPRを13の政策分野のいずれかに分類してください。

PR番号: {pr_number}
タイトル: {pr_info['title']}
作成者: {pr_info['author']['login'] if isinstance(pr_info['author'], dict) else pr_info['author']}

PR本文（最初の2000文字）:
{pr_details['body'][:2000] if pr_details.get('body') else '(本文なし)'}

変更ファイル数: {len(pr_details.get('files', []))}
追加行数: {pr_details.get('additions', 0)}
削除行数: {pr_details.get('deletions', 0)}

差分（最初の300行）:
{pr_details.get('diff', '(差分取得エラー)')}

政策分野ラベル一覧:
1. ビジョン - 政治理念、基本方針
2. デジタル民主主義 - 透明性、参加型政治、オープンガバメント
3. 行政改革 - 行政効率化、デジタル化、規制改革
4. 教育 - 教育制度、学習支援
5. 福祉 - 社会保障、高齢者・障害者支援
6. 子育て - 少子化対策、育児支援
7. 医療 - 医療制度、健康政策
8. 経済財政 - 税制、財政政策、経済政策
9. 産業政策 - 産業振興、技術革新、雇用
10. 科学技術 - 研究開発、イノベーション
11. エネルギー - エネルギー政策、環境
12. その他政策 - 上記に該当しない政策
13. [システム] - README更新、システム改善

分類基準:
- PRのタイトルと本文から主要なテーマを特定
- 複数の分野に関連する場合は、最も中心的なテーマを選択
- 政策内容の追加・修正は該当する政策分野へ
- マニフェスト自体の構造改善は[システム]へ

以下の形式で回答してください（他の文章は不要）:
ラベル: [選択したラベル]
理由: [分類理由を1行で簡潔に]"""
        
        # プロンプトを保存（デバッグ用）
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        return prompt
    
    def classify_with_llm(self, prompt):
        """LLMで分類（claude -pを使用）"""
        # claude -pコマンドで実行
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return None
        
        # 結果をパース
        output = result.stdout.strip()
        label = None
        reason = None
        
        for line in output.split('\n'):
            if line.startswith('ラベル:'):
                label = line.replace('ラベル:', '').strip()
            elif line.startswith('理由:'):
                reason = line.replace('理由:', '').strip()
        
        # ラベル検証
        if label in self.config['policy_labels']:
            return {'label': label, 'reason': reason}
        
        return None
    
    def process_batch(self, prs, batch_num, total_batches):
        """バッチ処理"""
        results = []
        
        print(f"\n=== バッチ {batch_num}/{total_batches} 処理中 ({len(prs)}件) ===")
        
        for i, pr in enumerate(prs):
            pr_num = pr['number']
            print(f"  [{i+1}/{len(prs)}] PR #{pr_num}: {pr['title'][:50]}...")
            
            # PR詳細取得
            pr_details = self.get_pr_details(pr_num)
            if not pr_details:
                print(f"    ⚠ 詳細取得失敗")
                continue
            
            # プロンプト作成
            prompt = self.create_classification_prompt(pr_num, pr, pr_details)
            
            # LLM分類
            classification = self.classify_with_llm(prompt)
            if not classification:
                print(f"    ⚠ 分類失敗 - デフォルト使用")
                classification = {
                    'label': 'その他政策',
                    'reason': 'LLM分類エラーによりデフォルト分類'
                }
            else:
                print(f"    ✓ {classification['label']}")
            
            results.append({
                'PR番号': pr_num,
                'タイトル': pr['title'],
                '作成者': pr['author']['login'] if isinstance(pr['author'], dict) else pr['author'],
                '作成日': pr['createdAt'],
                'ステータス': pr.get('state', 'OPEN'),
                '政策分野（新ラベル）': classification['label'],
                '旧ラベル': 'README',
                '分類理由': classification['reason'],
                '分析メモ': f'自動分類: {datetime.now().strftime("%Y-%m-%d")}',
                'URL': pr['url'],
                '説明（200文字まで）': pr['title'][:200]
            })
            
            # レート制限対策
            time.sleep(self.config['rate_limit_sleep'])
        
        return results
    
    def save_results(self, results, batch_num):
        """結果を保存"""
        if not results:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.config['output_dir']}/batch_{batch_num:03d}_{timestamp}.csv"
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        print(f"  保存: {filename} ({len(results)}件)")
    
    def run_classification(self, input_file=None):
        """分類処理を実行"""
        # PRデータを読み込みまたは取得
        if input_file:
            print(f"既存データを使用: {input_file}")
            pr_file = input_file
        else:
            pr_file = self.fetch_all_readme_prs()
        
        # PRデータ読み込み
        with open(pr_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            all_prs = data['pull_requests']
        
        print(f"\n総PR数: {len(all_prs)}")
        
        # 既存分類を読み込み
        existing = self.load_existing_classifications()
        print(f"既存分類数: {len(existing)}")
        
        # 未分類PRを抽出
        unclassified = [pr for pr in all_prs if pr['number'] not in existing]
        print(f"未分類PR数: {len(unclassified)}")
        
        if not unclassified:
            print("\nすべてのPRが分類済みです")
            return
        
        # バッチ処理
        batch_size = self.config['batch_size']
        total_batches = (len(unclassified) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(unclassified))
            batch = unclassified[start_idx:end_idx]
            
            results = self.process_batch(batch, batch_num + 1, total_batches)
            self.save_results(results, batch_num + 1)
        
        print("\n処理完了!")
    
    def merge_all_results(self):
        """すべての結果を統合"""
        print("\n結果を統合中...")
        
        all_results = []
        csv_files = sorted(Path(self.config['output_dir']).glob('*.csv'))
        
        for csv_file in csv_files:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                all_results.extend(list(reader))
        
        # 重複を除去（最新の分類を優先）
        unique_results = {}
        for result in all_results:
            pr_num = int(result['PR番号'])
            unique_results[pr_num] = result
        
        # 統合ファイルを保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        merged_file = f"{self.config['output_dir']}/merged_all_{timestamp}.csv"
        
        with open(merged_file, 'w', encoding='utf-8-sig', newline='') as f:
            if unique_results:
                writer = csv.DictWriter(f, fieldnames=list(unique_results.values())[0].keys())
                writer.writeheader()
                writer.writerows(unique_results.values())
        
        print(f"  統合完了: {merged_file}")
        print(f"  総件数: {len(unique_results)}")
        
        # ラベル別集計
        label_counts = {}
        for result in unique_results.values():
            label = result['政策分野（新ラベル）']
            label_counts[label] = label_counts.get(label, 0) + 1
        
        print("\nラベル別集計:")
        for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {label}: {count}件 ({count/len(unique_results)*100:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='PR分類システム')
    parser.add_argument('--fetch', action='store_true', help='GitHubから最新データを取得')
    parser.add_argument('--input', help='既存のPRデータファイルを使用')
    parser.add_argument('--merge', action='store_true', help='結果を統合')
    parser.add_argument('--batch-size', type=int, default=50, help='バッチサイズ')
    
    args = parser.parse_args()
    
    # 設定を更新
    if args.batch_size:
        CONFIG['batch_size'] = args.batch_size
    
    # 分類器を初期化
    classifier = PRClassifier(CONFIG)
    
    if args.merge:
        # 結果統合のみ
        classifier.merge_all_results()
    else:
        # 分類実行
        if args.fetch:
            classifier.run_classification()
        elif args.input:
            classifier.run_classification(args.input)
        else:
            print("--fetchまたは--inputオプションを指定してください")
            sys.exit(1)

if __name__ == "__main__":
    main()