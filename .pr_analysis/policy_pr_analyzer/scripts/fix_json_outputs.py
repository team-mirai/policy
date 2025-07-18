#!/usr/bin/env python3
"""
既存のJSON出力ファイルを修正するスクリプト
- マークダウンラップを除去
- 文字エンコーディングを修正
- 無効なJSONをスキップ
"""

import os
import json
import re
from pathlib import Path

def fix_json_file(file_path):
    """個別のJSONファイルを修正"""
    try:
        # ファイルサイズをチェック
        if os.path.getsize(file_path) == 0:
            return 'empty', None
        
        # UTF-8で読み込みを試みる（エラーは無視）
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
        except Exception:
            # エンコーディングエラーの場合はlatin-1で読み込み
            with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                content = f.read().strip()
        
        if not content:
            return 'empty', None
        
        # まず有効なJSONか確認
        try:
            data = json.loads(content)
            return 'valid', data
        except json.JSONDecodeError:
            pass
        
        # マークダウンラップを除去
        if content.startswith('```json'):
            # ```json ... ``` 形式を処理
            match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                json_content = match.group(1).strip()
                try:
                    data = json.loads(json_content)
                    return 'markdown_fixed', data
                except json.JSONDecodeError:
                    pass
        
        # 日本語メッセージの場合はスキップ
        if any(phrase in content for phrase in ['分析完了しました', '分析結果を', 'JSON形式で保存しました']):
            return 'japanese_message', None
        
        # その他の無効なJSON
        return 'invalid', None
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 'error', None

def process_directory(directory_path, dry_run=False):
    """ディレクトリ内のすべてのJSONファイルを処理"""
    stats = {
        'total': 0,
        'valid': 0,
        'markdown_fixed': 0,
        'empty': 0,
        'japanese_message': 0,
        'invalid': 0,
        'error': 0
    }
    
    json_files = list(Path(directory_path).rglob('*.json'))
    print(f"Found {len(json_files)} JSON files")
    
    for file_path in json_files:
        stats['total'] += 1
        status, data = fix_json_file(file_path)
        stats[status] += 1
        
        if status == 'markdown_fixed' and not dry_run:
            # 修正されたJSONを書き戻す
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Fixed: {file_path.name}")
        elif status == 'valid':
            # すでに有効なJSONの場合、UTF-8で再保存（文字化け修正）
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        elif status in ['empty', 'japanese_message', 'invalid']:
            print(f"⚠️  Skipped ({status}): {file_path.name}")
    
    return stats

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix JSON output files')
    parser.add_argument('directory', help='Directory containing JSON files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')
    args = parser.parse_args()
    
    print(f"Processing directory: {args.directory}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 60)
    
    stats = process_directory(args.directory, args.dry_run)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"Total files: {stats['total']}")
    print(f"Already valid: {stats['valid']}")
    print(f"Fixed markdown wrap: {stats['markdown_fixed']}")
    print(f"Empty files: {stats['empty']}")
    print(f"Japanese messages: {stats['japanese_message']}")
    print(f"Invalid JSON: {stats['invalid']}")
    print(f"Errors: {stats['error']}")
    
    total_fixed = stats['valid'] + stats['markdown_fixed']
    print(f"\nTotal usable after fix: {total_fixed} ({total_fixed/stats['total']*100:.1f}%)")

if __name__ == "__main__":
    main()