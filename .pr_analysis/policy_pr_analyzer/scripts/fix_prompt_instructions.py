#!/usr/bin/env python3
"""
既存のプロンプトファイルの末尾指示を改善
"""

import os
from pathlib import Path
import argparse

def fix_prompt_instruction(prompt_file):
    """プロンプトファイルの末尾指示を改善"""
    
    # ファイルを読み込み
    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 古い指示部分を特定
    old_instructions = [
        "【分析項目】\n以下の項目について分析し、JSON形式で出力してください：",
        "出力形式：\n{",
        "JSON形式で出力してください："
    ]
    
    # 古い指示部分を削除
    for old_inst in old_instructions:
        if old_inst in content:
            content = content.split(old_inst)[0]
            break
    
    # 新しい指示を追加
    new_instruction = """

**重要：以下の指示に厳密に従ってください**

この政策提案PRを分析し、以下の形式の有効なJSONのみを出力してください。
説明文や「分析が完了しました」等のテキストは一切含めないでください。

```json
{
  "pr_number": 999,
  "summary": "50字以内の要約",
  "category": "カリキュラム改革/教員・人材/設備・インフラ/制度・システム/予算・財源/デジタル化/地域連携/その他",
  "specificity": {
    "level": "高/中/低",
    "reason": "理由"
  },
  "difficulty": {
    "level": "高/中/低",
    "main_challenge": "主な課題"
  },
  "scope": "影響範囲",
  "required_resources": "必要なリソース",
  "keywords": ["キーワード1", "キーワード2", "キーワード3", "キーワード4", "キーワード5"],
  "unique_features": "30字以内の特徴",
  "discussion_points": ["論点1", "論点2"]
}
```

上記のJSON形式で回答してください。説明文は不要です。"""
    
    # 新しい内容を作成
    new_content = content.strip() + new_instruction
    
    # ファイルを書き戻し
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Fix prompt instructions')
    parser.add_argument('prompts_dir', help='Directory containing prompt files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed')
    
    args = parser.parse_args()
    
    individual_dir = Path(args.prompts_dir) / 'individual'
    if not individual_dir.exists():
        print("❌ Individual prompts directory not found")
        return
    
    prompt_files = list(individual_dir.glob('*.txt'))
    print(f"Found {len(prompt_files)} prompt files")
    
    if args.dry_run:
        print("DRY RUN - would fix these files:")
        for f in prompt_files[:5]:
            print(f"  - {f.name}")
        print(f"  ... and {len(prompt_files) - 5} more")
        return
    
    fixed = 0
    for prompt_file in prompt_files:
        try:
            fix_prompt_instruction(prompt_file)
            fixed += 1
            if fixed % 50 == 0:
                print(f"Fixed {fixed}/{len(prompt_files)} files")
        except Exception as e:
            print(f"❌ Error fixing {prompt_file}: {e}")
    
    print(f"✅ Fixed {fixed} prompt files")
    print("Now re-run the analysis for better results")

if __name__ == "__main__":
    main()