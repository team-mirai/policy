#!/usr/bin/env python3
"""
Script to analyze PRs in the policy repository and extract the specific sections 
of the manifest that are being modified.
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict

def run_command(command):
    """Run a shell command and return the output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error: {result.stderr}")
        return ""
    return result.stdout.strip()

def get_pr_list(limit=100):
    """Get a list of PRs from the repository."""
    command = f"gh pr list --limit {limit} --json number,title,headRefName,state,url"
    output = run_command(command)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(f"Error parsing JSON from PR list: {output}")
        return []

def get_pr_files(pr_number):
    """Get the list of files changed in a PR."""
    command = f"gh pr view {pr_number} --json files"
    output = run_command(command)
    try:
        data = json.loads(output)
        return data.get("files", [])
    except json.JSONDecodeError:
        print(f"Error parsing JSON from PR files: {output}")
        return []

def get_pr_diff(pr_number):
    """Get the diff for a PR."""
    command = f"gh pr diff {pr_number} --repo team-mirai/policy"
    return run_command(command)

def extract_markdown_sections(file_path):
    """Extract the markdown sections from a file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    headings = []
    for i, line in enumerate(content.split('\n')):
        match = re.match(r'^(#+)\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((i+1, level, title))
    
    sections = {}
    for i, (line_num, level, title) in enumerate(headings):
        parent_sections = []
        for prev_line, prev_level, prev_title in reversed(headings[:i]):
            if prev_level < level:
                parent_sections.insert(0, prev_title)
                if prev_level == 1:  # Stop at top level
                    break
        
        section_path = " > ".join(parent_sections + [title])
        sections[line_num] = {
            "level": level,
            "title": title,
            "path": section_path,
            "parent_sections": parent_sections
        }
    
    return sections

def find_section_for_line(sections, line_number):
    """Find the section that contains a specific line."""
    section_lines = sorted(sections.keys())
    for i, section_line in enumerate(section_lines):
        if section_line > line_number:
            if i > 0:
                return sections[section_lines[i-1]]
            break
    
    if section_lines:
        return sections[section_lines[-1]]
    
    return None

def parse_diff_hunks(diff_text):
    """Parse the diff hunks to extract line numbers and changes."""
    hunks = []
    current_file = None
    
    for line in diff_text.split('\n'):
        if line.startswith('diff --git'):
            match = re.search(r'b/(.+)$', line)
            if match:
                current_file = match.group(1)
        elif line.startswith('@@'):
            match = re.search(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
            if match and current_file:
                old_start = int(match.group(1))
                new_start = int(match.group(2))
                hunks.append({
                    'file': current_file,
                    'old_start': old_start,
                    'new_start': new_start,
                    'changes': []
                })
        elif current_file and hunks and line.startswith(('+', '-')) and not line.startswith(('+++', '---')):
            hunks[-1]['changes'].append(line)
    
    return hunks

def analyze_pr(pr_number):
    """Analyze a PR and extract the sections being modified."""
    diff_text = get_pr_diff(pr_number)
    if not diff_text:
        return None
    
    hunks = parse_diff_hunks(diff_text)
    
    results = []
    for hunk in hunks:
        file_path = hunk['file']
        if not file_path.endswith('.md'):
            continue
        
        full_path = os.path.join(os.getcwd(), file_path)
        
        sections = extract_markdown_sections(full_path)
        
        line_number = hunk['new_start']
        section = find_section_for_line(sections, line_number)
        
        if section:
            results.append({
                'file': file_path,
                'line': line_number,
                'section': section['title'],
                'section_path': section['path'],
                'parent_sections': section['parent_sections'],
                'changes': hunk['changes']
            })
    
    return results

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python pr_section_analyzer.py <pr_number>")
        return
    
    pr_number = sys.argv[1]
    results = analyze_pr(pr_number)
    
    if results:
        print(f"\nAnalysis of PR #{pr_number}:")
        for result in results:
            print(f"\nFile: {result['file']}")
            print(f"Section: {result['section_path']}")
            print("Changes:")
            for change in result['changes']:
                print(f"  {change}")
    else:
        print(f"No markdown sections found in PR #{pr_number}")

if __name__ == "__main__":
    main()
