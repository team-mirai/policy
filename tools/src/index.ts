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
const BATCH_SIZE = parseInt(process.env.BATCH_SIZE || '10', 10); // 一度に処理するPR数

/**
 * ページング処理でラベルのないPRを取得する
 * @param page ページ番号
 * @param perPage 1ページあたりの取得数
 */
async function fetchPullRequestsWithoutLabels(page: number = 1, perPage: number = BATCH_SIZE): Promise<{
  pullRequests: PullRequest[];
  hasNextPage: boolean;
}> {
  try {
    const { data } = await octokit.pulls.list({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      state: 'open',
      per_page: perPage,
      page: page,
    });

    const pullRequests = data.filter(pr => pr.labels.length === 0) as PullRequest[];
    
    const hasNextPage = data.length === perPage;

    return { pullRequests, hasNextPage };
  } catch (error) {
    console.error(`PRの取得に失敗しました (ページ ${page}):`, error);
    return { pullRequests: [], hasNextPage: false };
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
 * PRのバッチを処理する
 */
async function processPullRequestBatch(pullRequests: PullRequest[]): Promise<void> {
  for (const pr of pullRequests) {
    console.log(`PR #${pr.number} "${pr.title}" を処理中...`);

    const files = await fetchPullRequestFiles(pr.number);
    console.log(`  変更ファイル数: ${files.length}`);

    const labels = determineLabelsFromFiles(files);
    console.log(`  適用するラベル: ${labels.join(', ') || 'なし'}`);

    await addLabelsToPullRequest(pr.number, labels);
  }
}

/**
 * メイン処理
 */
async function main() {
  console.log('PR自動ラベル付けバッチを開始します...');
  console.log(`バッチサイズ: ${BATCH_SIZE} PRs/バッチ`);

  let page = 1;
  let hasNextPage = true;
  let totalProcessed = 0;

  while (hasNextPage) {
    console.log(`ページ ${page} を処理中...`);
    
    const result = await fetchPullRequestsWithoutLabels(page, BATCH_SIZE);
    hasNextPage = result.hasNextPage;
    
    console.log(`ページ ${page} でラベルのないPRが ${result.pullRequests.length} 件見つかりました`);
    
    if (result.pullRequests.length > 0) {
      await processPullRequestBatch(result.pullRequests);
      totalProcessed += result.pullRequests.length;
    }
    
    page++;
  }

  console.log(`処理が完了しました。合計 ${totalProcessed} 件のPRを処理しました。`);
}

main().catch(error => {
  console.error('エラーが発生しました:', error);
  process.exit(1);
});
