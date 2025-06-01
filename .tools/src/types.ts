export interface PullRequest {
  number: number;
  title: string;
  labels: Label[];
}

export interface Label {
  id: number;
  name: string;
  color: string;
}

export interface FileChange {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  blob_url: string;
  raw_url: string;
  contents_url: string;
}
