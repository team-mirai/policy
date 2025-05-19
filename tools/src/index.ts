import { Octokit } from '@octokit/rest';
import dotenv from 'dotenv';
import { fileLabelMappings } from './config';
import { PullRequest, FileChange } from './types';

dotenv.config();

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

const REPO_OWNER = process.env.REPO_OWNER || 'team-mirai';
const REPO_NAME = process.env.REPO_NAME || 'policy';

/**
 * ラベルのないPRを取得する
 */
async function fetchPullRequestsWithoutLabels(): Promise<PullRequest[]> {
  try {
    const { data } = await octokit.pulls.list({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      state: 'open',
    });

    return data.filter(pr => pr.labels.length === 0) as PullRequest[];
  } catch (error) {
    console.error('PRの取得に失敗しました:', error);
    return [];
  }
}

/**
 * PRの変更ファイル一覧を取得する
 */
async function fetchPullRequestFiles(prNumber: number): Promise<FileChange[]> {
  try {
    const { data } = await octokit.pulls.listFiles({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      pull_number: prNumber,
    });

    return data as FileChange[];
  } catch (error) {
    console.error(`PR #${prNumber} の変更ファイル取得に失敗しました:`, error);
    return [];
  }
}

/**
 * ファイル名からラベルを決定する
 */
function determineLabelsFromFiles(files: FileChange[]): string[] {
  const labels = new Set<string>();

  files.forEach(file => {
    for (const mapping of fileLabelMappings) {
      if (file.filename.includes(mapping.pattern)) {
        labels.add(mapping.label);
        break;
      }
    }
  });

  return Array.from(labels);
}

/**
 * PRにラベルを追加する
 */
async function addLabelsToPullRequest(prNumber: number, labels: string[]): Promise<void> {
  if (labels.length === 0) {
    console.log(`PR #${prNumber}: 適用するラベルが見つかりませんでした`);
    return;
  }

  try {
    await octokit.issues.addLabels({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      issue_number: prNumber,
      labels,
    });

    console.log(`PR #${prNumber}: ラベル "${labels.join(', ')}" を追加しました`);
  } catch (error) {
    console.error(`PR #${prNumber}: ラベル追加に失敗しました:`, error);
  }
}

/**
 * メイン処理
 */
async function main() {
  console.log('PR自動ラベル付けバッチを開始します...');

  const pullRequests = await fetchPullRequestsWithoutLabels();
  console.log(`ラベルのないPRが ${pullRequests.length} 件見つかりました`);


  for (const pr of pullRequests) {
    console.log(`PR #${pr.number} "${pr.title}" を処理中...`);

    const files = await fetchPullRequestFiles(pr.number);
    console.log(`  変更ファイル数: ${files.length}`);

    const labels = determineLabelsFromFiles(files);
    console.log(`  適用するラベル: ${labels.join(', ') || 'なし'}`);

    await addLabelsToPullRequest(pr.number, labels);
  }

  console.log('処理が完了しました');
}

main().catch(error => {
  console.error('エラーが発生しました:', error);
  process.exit(1);
});
