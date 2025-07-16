#!/usr/bin/env python3
"""
生成したプロンプトを複数のAPIプロバイダーで実行して分析を行う
"""

import os
import sys
import argparse
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# API プロバイダーの動的インポート
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class APIProvider:
    """APIプロバイダーの基底クラス"""

    def __init__(self):
        self.name = "base"

    def analyze(self, prompt_content):
        """分析を実行する"""
        raise NotImplementedError

    def is_available(self):
        """プロバイダーが利用可能かチェック"""
        return False


class ClaudeCLIProvider(APIProvider):
    """Claude CLI (claude -p) プロバイダー"""

    def __init__(self):
        super().__init__()
        self.name = "claude-cli"

    def analyze(self, prompt_content):
        """claude -pコマンドで分析"""
        try:
            result = subprocess.run(
                ["claude", "-p"],
                input=prompt_content,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return None, f"Error: {result.stderr}"

            return result.stdout, None
        except Exception as e:
            return None, f"Exception: {e}"

    def is_available(self):
        """claude コマンドが利用可能かチェック"""
        try:
            result = subprocess.run(
                ["claude", "--version"], capture_output=True)
            return result.returncode == 0
        except:
            return False


class AnthropicAPIProvider(APIProvider):
    """Anthropic API プロバイダー"""

    def __init__(self):
        super().__init__()
        self.name = "anthropic"
        self.client = None
        if ANTHROPIC_AVAILABLE:
            try:
                self.client = anthropic.Anthropic()
            except Exception as e:
                print(f"Warning: Failed to initialize Anthropic client: {e}")

    def analyze(self, prompt_content):
        """Anthropic APIで分析"""
        if not self.client:
            return None, "Anthropic client not initialized"

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt_content}
                ]
            )

            return response.content[0].text, None
        except anthropic.RateLimitError as e:
            return None, f"Rate limit error: {e}"
        except Exception as e:
            return None, f"API error: {e}"

    def is_available(self):
        """Anthropic APIが利用可能かチェック"""
        return ANTHROPIC_AVAILABLE and self.client is not None


class OpenAIAPIProvider(APIProvider):
    """OpenAI API プロバイダー"""

    def __init__(self):
        super().__init__()
        self.name = "openai"
        self.client = None
        if OPENAI_AVAILABLE:
            try:
                self.client = openai.OpenAI()
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")

    def analyze(self, prompt_content):
        """OpenAI APIで分析"""
        if not self.client:
            return None, "OpenAI client not initialized"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=4000,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt_content}
                ]
            )

            return response.choices[0].message.content, None
        except openai.RateLimitError as e:
            return None, f"Rate limit error: {e}"
        except Exception as e:
            return None, f"API error: {e}"

    def is_available(self):
        """OpenAI APIが利用可能かチェック"""
        return OPENAI_AVAILABLE and self.client is not None


def get_provider(provider_name):
    """指定されたプロバイダーを取得"""
    providers = {
        "claude-cli": ClaudeCLIProvider(),
        "anthropic": AnthropicAPIProvider(),
        "openai": OpenAIAPIProvider()
    }

    if provider_name not in providers:
        available = list(providers.keys())
        raise ValueError(
            f"Unknown provider: {provider_name}. Available: {available}")

    provider = providers[provider_name]
    if not provider.is_available():
        raise ValueError(f"Provider {provider_name} is not available")

    return provider


def run_analysis_with_retry(prompt_file, output_file, provider, dry_run=False, max_retries=3):
    """リトライ機能付きで分析を実行"""
    if dry_run:
        print(f"  [DRY RUN] Would analyze: {prompt_file} -> {output_file}")
        return True

    try:
        # 出力ディレクトリを作成
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # プロンプトファイルを読み込み
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        # リトライ処理
        for attempt in range(max_retries):
            result, error = provider.analyze(prompt_content)

            if result is not None:
                # 結果を保存
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)

                print(
                    f"  ✅ Analyzed: {os.path.basename(prompt_file)} (using {provider.name})")
                return True

            # エラーハンドリング
            if "rate limit" in error.lower():
                print(
                    f"  ⏱️ Rate limit hit for {os.path.basename(prompt_file)}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    # 指数バックオフ
                    wait_time = 60 * (2 ** attempt)
                    print(f"  ⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    print(
                        f"  ❌ Max retries reached for {os.path.basename(prompt_file)}")
                    return False
            else:
                print(f"  ❌ Error: {error}")
                return False

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


def analyze_individual_prs(prompts_dir, provider, sleep_time=2, dry_run=False, resume=True, max_workers=3):
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
    print(f"Using {max_workers} parallel workers with {provider.name} provider")

    if dry_run:
        for i, (prompt_file, output_file) in enumerate(files_to_analyze):
            print(f"[{i+1}/{total_to_analyze}] Would analyze: {prompt_file.name}")
        return total_to_analyze, skipped

    completed = 0

    def analyze_single_file(file_info):
        prompt_file, output_file = file_info
        try:
            if run_analysis_with_retry(prompt_file, output_file, provider, dry_run=False):
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

            # スリープ（API制限対策）
            if provider.name in ['anthropic', 'openai']:
                time.sleep(sleep_time)
            elif provider.name == 'claude-cli':
                time.sleep(sleep_time / max_workers)

    return completed, skipped


def analyze_similarity_checks(prompts_dir, provider, sleep_time=2, dry_run=False, resume=True, limit=None):
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
    print(f"Using {provider.name} provider")

    for i, prompt_file in enumerate(prompt_files):
        output_file = output_dir / prompt_file.with_suffix('.json').name

        # 既に分析済みの場合はスキップ
        if resume and output_file.exists():
            print(f"[{i+1}/{total}] Skipping (already analyzed): {prompt_file.name}")
            skipped += 1
            continue

        print(f"[{i+1}/{total}] Analyzing: {prompt_file.name}")

        if run_analysis_with_retry(prompt_file, output_file, provider, dry_run):
            completed += 1

        # 最後のファイル以外はスリープ
        if i < total - 1 and not dry_run:
            time.sleep(sleep_time)

    return completed, skipped


def analyze_trend(prompts_dir, provider, dry_run=False):
    """全体傾向分析を実行"""
    input_file = Path(prompts_dir) / 'trend' / 'overall_trend_analysis.txt'
    output_file = Path(prompts_dir) / 'output' / 'trend' / \
        'overall_trend_analysis.json'

    if not input_file.exists():
        print("❌ Trend analysis prompt not found")
        return False

    print(f"\n=== Analyzing Overall Trend ===")
    print(f"Using {provider.name} provider")
    print(f"Analyzing: {input_file.name}")

    return run_analysis_with_retry(input_file, output_file, provider, dry_run)


def main():
    parser = argparse.ArgumentParser(
        description='Run analysis on generated prompts with multiple API providers')
    parser.add_argument(
        'prompts_dir', help='Directory containing the prompts (e.g., prompts/batch_50)')
    parser.add_argument('--api-provider', choices=['claude-cli', 'anthropic', 'openai'],
                        default='claude-cli', help='API provider to use (default: claude-cli)')
    parser.add_argument('--type', choices=['all', 'individual', 'similarity', 'trend'],
                        default='all', help='Type of analysis to run (default: all)')
    parser.add_argument('--sleep', type=float, default=2,
                        help='Sleep time between analyses in seconds (default: 2)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without actually running')
    parser.add_argument('--no-resume', action='store_true',
                        help='Re-analyze all files (don\'t skip existing ones)')
    parser.add_argument('--similarity-limit', type=int,
                        help='Limit number of similarity checks to run')
    parser.add_argument('--status', action='store_true',
                        help='Show analysis status and exit')
    parser.add_argument('--workers', type=int, default=3,
                        help='Number of parallel workers for analysis (default: 3)')

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

    # プロバイダーの初期化
    try:
        provider = get_provider(args.api_provider)
        print(f"✅ Using {provider.name} provider")
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # デフォルトの sleep 時間を API プロバイダーに応じて調整
    if args.sleep == 2:  # デフォルト値の場合のみ調整
        if args.api_provider in ['anthropic', 'openai']:
            args.sleep = 10  # API プロバイダーの場合は長めに
        elif args.api_provider == 'claude-cli':
            args.sleep = 2   # claude-cli の場合は短めに

    # 並列数をプロバイダーに応じて調整
    if args.workers == 3:  # デフォルト値の場合のみ調整
        if args.api_provider in ['anthropic', 'openai']:
            args.workers = 1  # API プロバイダーの場合は1つずつ
        elif args.api_provider == 'claude-cli':
            args.workers = 3  # claude-cli の場合は並列実行

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
            args.prompts_dir, provider, args.sleep, args.dry_run, resume, args.workers
        )
        results['individual']['completed'] = completed
        results['individual']['skipped'] = skipped

    # 類似度チェック
    if args.type in ['all', 'similarity']:
        completed, skipped = analyze_similarity_checks(
            args.prompts_dir, provider, args.sleep, args.dry_run, resume, args.similarity_limit
        )
        results['similarity']['completed'] = completed
        results['similarity']['skipped'] = skipped

    # 全体傾向分析
    if args.type in ['all', 'trend']:
        if analyze_trend(args.prompts_dir, provider, args.dry_run):
            results['trend']['completed'] = 1

    # 結果サマリー
    end_time = datetime.now()
    duration = end_time - start_time

    print(f"\n=== Analysis Complete ===")
    print(f"Duration: {duration}")
    print(f"Provider: {provider.name}")
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
