#!/usr/bin/env python3
"""
Script to analyze PRs in the policy repository and extract the specific sections 
of the manifest that are being modified. This script can identify which PRs modify
the same sections of the manifest.
"""

import json
import os
import re
import subprocess
import sys
import argparse
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

def get_pr_details(pr_number):
    """Get detailed information about a PR."""
    command = f"gh pr view {pr_number} --json number,title,headRefName,state,url,body"
    output = run_command(command)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(f"Error parsing JSON from PR details: {output}")
        return {}

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
    command = f"git fetch origin pull/{pr_number}/head:pr-{pr_number}-temp && git diff main..pr-{pr_number}-temp"
    diff = run_command(command)
    if not diff:
        print(f"DEBUG: Failed to get diff using git fetch/diff, trying alternative method")
        command = f"git fetch && git diff origin/main...origin/pr-{pr_number}-head"
        diff = run_command(command)
    return diff

def extract_markdown_sections(file_path):
    """Extract the markdown sections from a file with improved Japanese section handling."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    headings = []
    section_content = {}
    current_section_start = None
    
    for i, line in enumerate(content.split('\n')):
        heading_match = re.match(r'^(#+)\s+(.+)$', line)
        
        jp_section_match = None
        if not heading_match:
            jp_section_match = re.match(r'^([０-９]+）|\d+）)\s*(.+)$', line)
        
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            headings.append((i+1, level, title))
            
            if current_section_start is not None:
                section_content[current_section_start] = (current_section_start, i)
            current_section_start = i+1
            
        elif jp_section_match:
            level = 3
            title = jp_section_match.group(0).strip()
            headings.append((i+1, level, title))
            
            if current_section_start is not None:
                section_content[current_section_start] = (current_section_start, i)
            current_section_start = i+1
    
    if current_section_start is not None and len(content.split('\n')) > 0:
        section_content[current_section_start] = (current_section_start, len(content.split('\n')))
    
    sections = {}
    for i, (line_num, level, title) in enumerate(headings):
        parent_sections = []
        for prev_line, prev_level, prev_title in reversed(headings[:i]):
            if prev_level < level:
                parent_sections.insert(0, prev_title)
                if prev_level == 1:  # Stop at top level
                    break
        
        section_path = " > ".join(parent_sections + [title])
        
        content_range = section_content.get(line_num, (line_num, line_num))
        
        sections[line_num] = {
            "level": level,
            "title": title,
            "path": section_path,
            "parent_sections": parent_sections,
            "start_line": content_range[0],
            "end_line": content_range[1]
        }
    
    return sections

def find_section_for_line(sections, line_number):
    """Find the section that contains a specific line."""
    for section_line, section_info in sections.items():
        if section_info["start_line"] <= line_number <= section_info["end_line"]:
            return section_info
    
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
    """Parse the diff hunks to extract line numbers and changes with improved accuracy."""
    hunks = []
    current_file = None
    in_file_header = False
    
    lines = diff_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('diff --git'):
            in_file_header = True
            match = re.search(r'b/(.+?)("?)$', line)
            if match:
                current_file = match.group(1)
                if current_file.endswith('"'):
                    current_file = current_file[:-1]
                current_file = current_file.replace('\\', '')
                print(f"DEBUG: Extracted file path: {current_file}")
        elif line.startswith('+++'):
            in_file_header = False
            match = re.search(r'\+\+\+ b/(.+?)("?)$', line)
            if match:
                new_file = match.group(1)
                if new_file.endswith('"'):
                    new_file = new_file[:-1]
                new_file = new_file.replace('\\', '')
                print(f"DEBUG: Updated file path from +++ line: {new_file}")
                current_file = new_file
        elif line.startswith('@@') and not in_file_header:
            match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
            if match and current_file:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                
                hunk = {
                    'file': current_file,
                    'old_start': old_start,
                    'old_count': old_count,
                    'new_start': new_start,
                    'new_count': new_count,
                    'changes': [],
                    'context_before': [],
                    'context_after': []
                }
                
                j = i + 1
                while j < len(lines) and j < i + 4 and not lines[j].startswith(('+', '-', '@@')):
                    hunk['context_before'].append(lines[j])
                    j += 1
                
                current_old_line = old_start
                current_new_line = new_start
                
                j = i + 1
                while j < len(lines) and not lines[j].startswith('@@'):
                    if lines[j].startswith('+'):
                        hunk['changes'].append({
                            'type': 'add',
                            'line_num': current_new_line,
                            'content': lines[j][1:]
                        })
                        current_new_line += 1
                    elif lines[j].startswith('-'):
                        hunk['changes'].append({
                            'type': 'remove',
                            'line_num': current_old_line,
                            'content': lines[j][1:]
                        })
                        current_old_line += 1
                    else:
                        current_old_line += 1
                        current_new_line += 1
                    j += 1
                
                hunks.append(hunk)
        
        i += 1
    
    return hunks

def analyze_pr(pr_number):
    """Analyze a PR and extract the sections being modified."""
    pr_details = get_pr_details(pr_number)
    diff_text = get_pr_diff(pr_number)
    
    print(f"DEBUG: Analyzing PR #{pr_number}")
    
    if not diff_text:
        print("DEBUG: No diff text found")
        return None
    
    print(f"DEBUG: Diff text length: {len(diff_text)} characters")
    print(f"DEBUG: First 100 chars of diff: {diff_text[:100]}")
    
    hunks = parse_diff_hunks(diff_text)
    print(f"DEBUG: Found {len(hunks)} hunks in diff")
    
    results = []
    for i, hunk in enumerate(hunks):
        file_path = hunk['file']
        print(f"DEBUG: Hunk {i+1} - File: {file_path}")
        
        is_markdown = False
        if file_path.endswith('.md'):
            is_markdown = True
        elif file_path.lower().endswith('.md"'):
            is_markdown = True
            file_path = file_path[:-1]  # Remove trailing quote
        elif '.' in file_path and file_path.split('.')[-1].lower() == 'md':
            is_markdown = True
        
        if not is_markdown:
            print(f"DEBUG: Skipping non-markdown file: {file_path}")
            continue
        
        full_path = os.path.join(os.getcwd(), file_path)
        print(f"DEBUG: Full path: {full_path}")
        
        if not os.path.exists(full_path):
            print(f"Warning: File {full_path} does not exist, skipping")
            continue
        
        sections = extract_markdown_sections(full_path)
        print(f"DEBUG: Found {len(sections)} sections in {file_path}")
        if len(sections) > 0:
            print(f"DEBUG: Section titles: {[s['title'] for s in sections.values()][:5]}")
        
        affected_sections = set()
        for j, change in enumerate(hunk['changes']):
            line_number = change['line_num']
            print(f"DEBUG: Change {j+1} - Line: {line_number}, Content: {change['content'][:30]}...")
            
            section = find_section_for_line(sections, line_number)
            
            if section:
                print(f"DEBUG: Found section: {section['title']}")
                affected_sections.add((section['title'], section['path']))
            else:
                print(f"DEBUG: No section found for line {line_number}")
        
        for section_title, section_path in affected_sections:
            results.append({
                'pr_number': pr_number,
                'pr_title': pr_details.get('title', ''),
                'pr_url': pr_details.get('url', ''),
                'file': file_path,
                'section': section_title,
                'section_path': section_path,
                'changes': [c['content'] for c in hunk['changes']]
            })
    
    print(f"DEBUG: Found {len(results)} affected sections")
    return results

def analyze_all_prs(limit=100):
    """Analyze all PRs and group them by the sections they modify."""
    prs = get_pr_list(limit)
    
    all_results = []
    section_to_prs = defaultdict(list)
    
    for pr in prs:
        pr_number = pr['number']
        print(f"Analyzing PR #{pr_number}: {pr['title']}")
        
        results = analyze_pr(pr_number)
        if results:
            all_results.extend(results)
            
            for result in results:
                section_key = f"{result['file']}:{result['section_path']}"
                section_to_prs[section_key].append({
                    'pr_number': pr_number,
                    'pr_title': pr['title'],
                    'pr_url': pr['url']
                })
    
    return all_results, section_to_prs

def generate_report(all_results, section_to_prs):
    """Generate a report of the analysis results."""
    report = []
    
    report.append("# PRs Grouped by Section\n")
    
    for section_key, prs in sorted(section_to_prs.items()):
        if len(prs) > 1:  # Only show sections with multiple PRs
            file_path, section_path = section_key.split(':', 1)
            report.append(f"## {file_path}\n")
            report.append(f"### {section_path}\n")
            report.append("PRs modifying this section:\n")
            
            for pr in prs:
                report.append(f"- PR #{pr['pr_number']}: {pr['pr_title']} ({pr['pr_url']})\n")
            
            report.append("\n")
    
    report.append("# Sections Modified by Each PR\n")
    
    pr_to_sections = defaultdict(list)
    for result in all_results:
        pr_key = f"{result['pr_number']}:{result['pr_title']}"
        section_info = {
            'file': result['file'],
            'section_path': result['section_path']
        }
        pr_to_sections[pr_key].append(section_info)
    
    for pr_key, sections in sorted(pr_to_sections.items()):
        pr_number, pr_title = pr_key.split(':', 1)
        report.append(f"## PR #{pr_number}: {pr_title}\n")
        
        for section in sections:
            report.append(f"- {section['file']}: {section['section_path']}\n")
        
        report.append("\n")
    
    return "".join(report)

def main():
    """Main function with improved command-line interface."""
    parser = argparse.ArgumentParser(description='Analyze PRs in the policy repository and extract modified sections.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pr', type=str, help='PR number to analyze')
    group.add_argument('--all', action='store_true', help='Analyze all PRs')
    parser.add_argument('--limit', type=int, default=100, help='Limit the number of PRs to analyze (default: 100)')
    parser.add_argument('--output', type=str, help='Output file for the report (default: stdout)')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format (default: text)')
    
    args = parser.parse_args()
    
    if args.pr:
        results = analyze_pr(args.pr)
        
        if results:
            if args.format == 'json':
                output = json.dumps(results, indent=2, ensure_ascii=False)
            else:
                output = f"\nAnalysis of PR #{args.pr}:\n"
                for result in results:
                    output += f"\nFile: {result['file']}\n"
                    output += f"Section: {result['section_path']}\n"
                    output += "Changes:\n"
                    for change in result['changes']:
                        output += f"  {change}\n"
        else:
            output = f"No markdown sections found in PR #{args.pr}"
    else:  # --all
        all_results, section_to_prs = analyze_all_prs(args.limit)
        
        if args.format == 'json':
            output = json.dumps({
                'results': all_results,
                'section_to_prs': {k: v for k, v in section_to_prs.items()}
            }, indent=2, ensure_ascii=False)
        else:
            output = generate_report(all_results, section_to_prs)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
