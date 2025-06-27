# Claude Code Configuration

このリポジトリでは、Claude Code が効率的に作業できるように設定されています。

## 自動実行可能なコマンド

`.claude_allowed_commands.json` に定義されているコマンドは、ユーザーの確認なしに実行できます。これにより、基本的なファイル操作や情報取得が迅速に行えます。

### 主なカテゴリー：
- **ファイル操作**: ls, cat, grep, find など（読み取り専用）
- **Git操作**: git status, git diff, git log など（読み取り専用）
- **開発ツール**: npm list, yarn list, バージョン確認など
- **解析ツール**: eslint, prettier, ruff など
- **システム情報**: date, whoami, which など
- **テキスト処理**: echo, sed, awk, sort など
- **GitHub CLI**: gh pr list, gh issue view など（読み取り専用）

## 確認が必要なコマンド

以下のような破壊的な操作や副作用のあるコマンドは、実行前に必ず確認を求めます：
- ファイルの削除・移動・変更（rm, mv, chmod など）
- Git の変更操作（push, commit, merge など）
- パッケージのインストール・アンインストール
- システム設定の変更
- Docker/Kubernetes 操作
- クラウドサービスの操作

## リンターとフォーマッター

このプロジェクトで利用可能なツール：
- Markdown: markdownlint, markdown-link-check
- その他必要に応じて設定

## プロジェクト固有の注意事項

1. PR作成時は、CI（linkspector）が通過することを確認してください
2. Markdownファイルのリンク記法に注意（正しい形式: `[テキスト](URL)`）
3. 日本語ファイル名を扱う際は適切にエスケープしてください