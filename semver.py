#!/usr/bin/env python3
"""
Semantic Versioning Script for Git Repositories
Supports conventional commits: feat:, fix:, and BREAKING CHANGE
"""
import subprocess
import os
import re
from pathlib import Path
from zipfile import ZipFile
from typing import Tuple, List, Optional


def get_last_version() -> str:
    """Get the last semantic version tag, or return 0.0.0 if none exist."""
    try:
        result = subprocess.run(
            ['git', 'tag', '-l'],
            capture_output=True,
            text=True,
            check=True
        )
        tags = result.stdout.strip().split('\n')
        # Filter to only semantic version tags (e.g., 1.0.0)
        version_tags = [tag for tag in tags if tag and re.match(r'^\d+\.\d+\.\d+$', tag)]

        if not version_tags:
            return '0.0.0'

        # Sort by version number and return the highest
        version_tags.sort(key=lambda v: tuple(map(int, v.split('.'))))
        return version_tags[-1]
    except Exception as e:
        print(f"Error getting last version: {e}")
        return '0.0.0'


def get_commits_since_tag(tag: str) -> List[str]:
    """Get commit hashes since the given tag."""
    try:
        if tag == '0.0.0':
            # Get all commits if no tags exist
            result = subprocess.run(
                ['git', 'rev-list', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # Get commits since the tag
            result = subprocess.run(
                ['git', 'rev-list', f'{tag}..HEAD'],
                capture_output=True,
                text=True,
                check=True
            )

        commits = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
        return commits
    except Exception as e:
        print(f"Error getting commits: {e}")
        return []


def get_commit_message(commit_hash: str) -> Tuple[str, str]:
    """Get commit subject and body."""
    try:
        result = subprocess.run(
            ['git', 'show', '-s', '--format=%s%n%b', commit_hash],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.split('\n', 1)
        subject = lines[0] if lines else ''
        body = lines[1] if len(lines) > 1 else ''
        return subject, body
    except Exception as e:
        print(f"Error getting commit message for {commit_hash}: {e}")
        return '', ''


def determine_bump(commits: List[str]) -> str:
    """
    Determine the semantic version bump based on commits.
    Returns 'major', 'minor', or 'patch'
    """
    has_major = False
    has_minor = False

    for commit_hash in commits:
        subject, body = get_commit_message(commit_hash)

        # Check for BREAKING CHANGE in subject or body
        if 'BREAKING CHANGE:' in subject or 'BREAKING CHANGE:' in body:
            has_major = True
            break

        # Check for feat! or fix! (exclamation indicates breaking change)
        if re.match(r'^(feat|fix)!:', subject):
            has_major = True
            break

        # Check for feat: (feature bump)
        if re.match(r'^feat:', subject):
            has_minor = True

        # fix: defaults to patch, so we don't need to explicitly check

    if has_major:
        return 'major'
    elif has_minor:
        return 'minor'
    else:
        # Default to patch if there are commits (even without conventional prefix)
        return 'patch'


def increment_version(version: str, bump: str) -> str:
    """Increment the version based on bump type."""
    major, minor, patch = map(int, version.split('.'))

    if bump == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f'{major}.{minor}.{patch}'


def determine_new_version(current_version: str, commits: List[str]) -> Optional[str]:
    """Determine the new version based on current version and commits."""
    if not commits:
        print("No new commits since last version")
        return None

    if current_version == '0.0.0':
        # First version should be 0.0.1
        print("No previous version found. Setting first version to 0.0.1")
        return '0.0.1'

    # Analyze commits and determine bump
    bump = determine_bump(commits)
    new_version = increment_version(current_version, bump)
    print(f"Determined bump type: {bump}")
    return new_version


def create_zip(repo_name: str, version: str) -> str:
    """
    Create a zip file excluding .git and .github directories.
    Returns the filename of the created zip.
    """
    zip_filename = f'{repo_name}-{version}.zip'

    with ZipFile(zip_filename, 'w') as zf:
        for root, dirs, files in os.walk('.'):
            # Remove .git and .github from dirs to prevent traversal
            dirs[:] = [d for d in dirs if d not in ['.git', '.github']]

            for file in files:
                file_path = Path(root) / file

                # Calculate the archive name with the wrapper directory
                relative_path = file_path.relative_to('.')
                archive_name = f'{repo_name}-{version}/{relative_path}'

                zf.write(file_path, arcname=archive_name)

    print(f"Created zip file: {zip_filename}")
    return zip_filename


def create_git_tag(version: str):
    """Create and push a git tag for the new version."""
    try:
        subprocess.run(['git', 'tag', version], check=True)
        subprocess.run(['git', 'push', 'origin', version], check=True)
        print(f"Created and pushed git tag: {version}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating git tag: {e}")
        raise


def create_github_release(version: str, zip_filename: str):
    """Create a GitHub release with the zip file as an artifact."""
    try:
        subprocess.run([
            'gh', 'release', 'create', version,
            zip_filename,
            '--title', f'Release {version}',
            '--notes', f'Automated release for version {version}'
        ], check=True)
        print(f"Created GitHub release for {version}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating GitHub release: {e}")
        raise


def main():
    """Main versioning workflow."""
    print("=== Semantic Versioning Script ===\n")

    # Get repository name from environment
    repo_full_name = os.getenv('GITHUB_REPOSITORY', 'unknown/repo')
    repo_name = repo_full_name.split('/')[-1]
    print(f"Repository: {repo_name}\n")

    # Step 1: Get current version
    current_version = get_last_version()
    print(f"Current version: {current_version}")

    # Step 2: Get commits since last version
    commits = get_commits_since_tag(current_version)
    print(f"Found {len(commits)} new commits\n")

    # Step 3: Determine new version
    new_version = determine_new_version(current_version, commits)
    if not new_version:
        print("No action needed.")
        return

    print(f"New version: {new_version}\n")

    # Step 4: Create git tag
    print("Creating git tag...")
    create_git_tag(new_version)

    # Step 5: Create zip file
    print("\nCreating release artifact...")
    zip_filename = create_zip(repo_name, new_version)

    # Step 6: Create GitHub release
    print("\nCreating GitHub release...")
    create_github_release(new_version, zip_filename)

    print("\n=== Versioning Complete ===")


if __name__ == '__main__':
    main()