#!/usr/bin/env python3
"""
生成したプロンプトをClaude APIで実行して分析を行う
"""

import os
import sys
import argparse
import time
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def run_claude_analysis(prompt_file, output_file, dry_run=False, client=None):
    """Claude APIを使用して分析"""
    if dry_run:
        print(f"  [DRY RUN] Would analyze: {prompt_file} -> {output_file}")
        return True

    if not ANTHROPIC_AVAILABLE:
        print("  ❌ Error: anthropic library not installed. Run: pip install anthropic")
        return False

    if client is None:
        print("  ❌ Error: Claude client not initialized")
        return False

    try:
        # 出力ディレクトリを作成
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # プロンプトファイルを読み込み
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        # Claude APIを実行（リトライ機能付き）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0,
                    messages=[
                        {"role": "user", "content": prompt_content}
                    ]
                )

                result_text = response.content[0].text

                # 結果を保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result_text)

                print(f"  ✅ Analyzed: {os.path.basename(prompt_file)}")
                return True

            except anthropic.RateLimitError as e:
                print(
                    f"  ⏱️ Rate limit hit for {os.path.basename(prompt_file)}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    # 指数バックオフ（1分、2分、4分）
                    wait_time = 60 * (2 ** attempt)
                    print(f"  ⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    print(
                        f"  ❌ Max retries reached for {os.path.basename(prompt_file)}")
                    return False
            except Exception as e:
                print(f"  ❌ API Error: {e}")
                return False

    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return False


def get_analysis_status(prompts_dir):
    """分析の進捗状況を確認"""
    status = {
        'individual': {'total': 0, 'completed': 0, 'files': []},
        'similarity': {'total': 0, 'completed': 0, 'files': []},
        'trend': {'total': 0, 'completed': 0, 'files': []}
    }

    for analysis_type in ['individual', 'similarity', 'trend']:
        input_dir = Path(prompts_dir) / analysis_type
        output_dir = Path(prompts_dir) / 'output' / analysis_type

        if input_dir.exists():
            input_files = list(input_dir.glob('*.txt'))
            status[analysis_type]['total'] = len(input_files)

            for input_file in input_files:
                output_file = output_dir / input_file.with_suffix('.json').name
                if output_file.exists():
                    status[analysis_type]['completed'] += 1
                else:
                    status[analysis_type]['files'].append(input_file)

    return status


def analyze_individual_prs(prompts_dir, sleep_time=10, dry_run=False, resume=True, max_workers=1, client=None):
    """個別PR分析を実行（並列処理）"""
    input_dir = Path(prompts_dir) / 'individual'
    output_dir = Path(prompts_dir) / 'output' / 'individual'

    if not input_dir.exists():
        print("❌ Individual prompts directory not found")
        return 0, 0

    # プロンプトファイルを取得
    prompt_files = sorted(input_dir.glob('*.txt'))

    # 分析が必要なファイルのみを抽出
    files_to_analyze = []
    skipped = 0

    for prompt_file in prompt_files:
        output_file = output_dir / prompt_file.with_suffix('.json').name
        if resume and output_file.exists():
            skipped += 1
        else:
            files_to_analyze.append((prompt_file, output_file))

    total = len(prompt_files)
    total_to_analyze = len(files_to_analyze)

    print(
        f"\n=== Analyzing Individual PRs ({total} files, {total_to_analyze} remaining) ===")
    print(f"Using {max_workers} parallel workers")

    if dry_run:
        for i, (prompt_file, output_file) in enumerate(files_to_analyze):
            print(f"[{i+1}/{total_to_analyze}] Would analyze: {prompt_file.name}")
        return total_to_analyze, skipped

    completed = 0

    def analyze_single_file(file_info):
        prompt_file, output_file = file_info
        try:
            if run_claude_analysis(prompt_file, output_file, dry_run=False, client=client):
                return prompt_file.name, True, None
            else:
                return prompt_file.name, False, "Analysis failed"
        except Exception as e:
            return prompt_file.name, False, str(e)

    # 並列実行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # タスクを投入
        future_to_file = {executor.submit(
            analyze_single_file, file_info): file_info for file_info in files_to_analyze}

        # 結果を処理
        for future in as_completed(future_to_file):
            file_info = future_to_file[future]
            prompt_file, output_file = file_info

            try:
                filename, success, error = future.result()
                completed_now = completed + 1
                if success:
                    print(
                        f"[{completed_now}/{total_to_analyze}] ✅ Completed: {filename}")
                    completed += 1
                else:
                    print(
                        f"[{completed_now}/{total_to_analyze}] ❌ Failed: {filename} - {error}")
            except Exception as e:
                print(f"❌ Exception analyzing {prompt_file.name}: {e}")

            # 長いスリープ（API制限対策）
            time.sleep(sleep_time)

    return completed, skipped


def analyze_similarity_checks(prompts_dir, sleep_time=10, dry_run=False, resume=True, limit=None, client=None):
    """類似度チェックを実行"""
    input_dir = Path(prompts_dir) / 'similarity'
    output_dir = Path(prompts_dir) / 'output' / 'similarity'

    if not input_dir.exists():
        print("❌ Similarity prompts directory not found")
        return 0, 0

    # プロンプトファイルを取得
    prompt_files = sorted(input_dir.glob('*.txt'))
    if limit:
        prompt_files = prompt_files[:limit]

    total = len(prompt_files)
    completed = 0
    skipped = 0

    print(f"\n=== Analyzing Similarity Checks ({total} files) ===")

    for i, prompt_file in enumerate(prompt_files):
        output_file = output_dir / prompt_file.with_suffix('.json').name

        # 既に分析済みの場合はスキップ
        if resume and output_file.exists():
            print(f"[{i+1}/{total}] Skipping (already analyzed): {prompt_file.name}")
            skipped += 1
            continue

        print(f"[{i+1}/{total}] Analyzing: {prompt_file.name}")

        if run_claude_analysis(prompt_file, output_file, dry_run, client=client):
            completed += 1

        # 最後のファイル以外は長いスリープ
        if i < total - 1 and not dry_run:
            time.sleep(sleep_time)

    return completed, skipped


def analyze_trend(prompts_dir, dry_run=False, client=None):
    """全体傾向分析を実行"""
    input_file = Path(prompts_dir) / 'trend' / 'overall_trend_analysis.txt'
    output_file = Path(prompts_dir) / 'output' / 'trend' / \
        'overall_trend_analysis.json'

    if not input_file.exists():
        print("❌ Trend analysis prompt not found")
        return False

    print(f"\n=== Analyzing Overall Trend ===")
    print(f"Analyzing: {input_file.name}")

    return run_claude_analysis(input_file, output_file, dry_run, client=client)


def main():
    parser = argparse.ArgumentParser(
        description='Run Claude API analysis on generated prompts')
    parser.add_argument(
        'prompts_dir', help='Directory containing the prompts (e.g., prompts/batch_50)')
    parser.add_argument('--type', choices=['all', 'individual', 'similarity', 'trend'],
                        default='all', help='Type of analysis to run (default: all)')
    parser.add_argument('--sleep', type=float, default=10,
                        help='Sleep time between analyses in seconds (default: 10)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without actually running')
    parser.add_argument('--no-resume', action='store_true',
                        help='Re-analyze all files (don\'t skip existing ones)')
    parser.add_argument('--similarity-limit', type=int,
                        help='Limit number of similarity checks to run')
    parser.add_argument('--status', action='store_true',
                        help='Show analysis status and exit')
    parser.add_argument('--workers', type=int, default=1,
                        help='Number of parallel workers for analysis (default: 1)')

    args = parser.parse_args()

    # ステータス表示モード
    if args.status:
        status = get_analysis_status(args.prompts_dir)
        print("\n=== Analysis Status ===")
        for analysis_type, info in status.items():
            print(f"\n{analysis_type.capitalize()}:")
            print(f"  Total: {info['total']}")
            print(f"  Completed: {info['completed']}")
            print(f"  Remaining: {info['total'] - info['completed']}")
        sys.exit(0)

        # Claude APIクライアントを初期化
    if not args.dry_run and not ANTHROPIC_AVAILABLE:
        print("❌ Error: anthropic library not installed. Run: pip install anthropic")
        sys.exit(1)

    client = None
    if not args.dry_run:
        try:
            client = anthropic.Anthropic()
            print("✅ Claude API client initialized")
        except Exception as e:
            print(f"❌ Error initializing Claude API client: {e}")
            sys.exit(1)

    resume = not args.no_resume
    start_time = datetime.now()

    print(f"Starting analysis at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Prompts directory: {args.prompts_dir}")
    print(f"Resume mode: {resume}")
    print(f"Parallel workers: {args.workers}")
    print(f"Sleep time: {args.sleep} seconds")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual analysis will be performed")

    results = {
        'individual': {'completed': 0, 'skipped': 0},
        'similarity': {'completed': 0, 'skipped': 0},
        'trend': {'completed': 0}
    }

    # 個別PR分析
    if args.type in ['all', 'individual']:
        completed, skipped = analyze_individual_prs(
            args.prompts_dir, args.sleep, args.dry_run, resume, args.workers, client
        )
        results['individual']['completed'] = completed
        results['individual']['skipped'] = skipped

    # 類似度チェック
    if args.type in ['all', 'similarity']:
        completed, skipped = analyze_similarity_checks(
            args.prompts_dir, args.sleep, args.dry_run, resume, args.similarity_limit, client
        )
        results['similarity']['completed'] = completed
        results['similarity']['skipped'] = skipped

    # 全体傾向分析
    if args.type in ['all', 'trend']:
        if analyze_trend(args.prompts_dir, args.dry_run, client):
            results['trend']['completed'] = 1

    # 結果サマリー
    end_time = datetime.now()
    duration = end_time - start_time

    print(f"\n=== Analysis Complete ===")
    print(f"Duration: {duration}")
    print(f"\nResults:")
    print(
        f"  Individual PRs: {results['individual']['completed']} analyzed, {results['individual']['skipped']} skipped")
    print(
        f"  Similarity checks: {results['similarity']['completed']} analyzed, {results['similarity']['skipped']} skipped")
    print(f"  Trend analysis: {results['trend']['completed']} completed")

    if not args.dry_run:
        print(f"\nOutput files saved in: {args.prompts_dir}/output/")


if __name__ == "__main__":
    main()
