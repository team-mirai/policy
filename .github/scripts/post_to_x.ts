import { TwitterApi } from 'twitter-api-v2';
import * as fs from 'fs';

interface GitHubUser {
  login: string;
}

interface GitHubPullRequest {
  title?: string;
  html_url?: string;
  user?: GitHubUser;
}

interface GitHubEvent {
  pull_request?: GitHubPullRequest;
}

// PR情報をGitHub Actionsのイベントから取得
const eventPath = process.env.GITHUB_EVENT_PATH;
let pr: GitHubPullRequest = {};
if (eventPath && fs.existsSync(eventPath)) {
  const event: GitHubEvent = JSON.parse(fs.readFileSync(eventPath, 'utf8'));
  pr = event.pull_request || {};
}

const prTitle = pr.title ?? 'PRタイトル';
const prUrl = pr.html_url ?? 'PRリンク';
const prUser = pr.user?.login ?? 'ユーザー名';

const text = `提案したPRがマージされました！ありがとうございました！\nタイトル: ${prTitle}\nリンク: ${prUrl}\n提案者: ${prUser}さん`;

const client = new TwitterApi({
  appKey: process.env.TWITTER_API_KEY!,
  appSecret: process.env.TWITTER_API_SECRET!,
  accessToken: process.env.TWITTER_ACCESS_TOKEN!,
  accessSecret: process.env.TWITTER_ACCESS_TOKEN_SECRET!,
});

(async () => {
  try {
    const tweet = await client.v2.tweet(text);
    console.log('Success:', tweet);
  } catch (e: unknown) {
    if (e instanceof Error) {
      console.error('Error:', e.message);
    } else {
      console.error('Unknown error:', e);
    }
    process.exit(1);
  }
})(); 
