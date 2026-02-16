#!/usr/bin/env python3
"""
Semantic Versioning Script for Git Repositories
Supports conventional commits: feat:, fix:, and BREAKING CHANGE
"""
import subprocess
import os
import re
import requests
import argparse
import sys
from pathlib import Path
from zipfile import ZipFile
from typing import Tuple, List, Optional


def get_distance_from_main() -> int:
    """Get the number of commits the current branch is ahead of main."""
    try:
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'main..HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.strip())
    except Exception as e:
        print(f"Error getting distance from main: {e}")
        return 0


def get_current_git_hash() -> str:
    """Get the shortened git hash of the current HEAD."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting git hash: {e}")
        return 'unknown'


def get_prerelease_tags(base_version: str, prerelease_type: str) -> List[str]:
    """
    Get all prerelease tags for a given base version and type.
    For example: get_prerelease_tags("1.0.0", "alpha") returns ["1.0.0-alpha.1", "1.0.0-alpha.2"]
    """
    try:
        result = subprocess.run(
            ['git', 'tag', '--list', f'{base_version}-{prerelease_type}.*'],
            capture_output=True,
            text=True,
            check=True
        )
        tags = [tag.strip() for tag in result.stdout.strip().split('\n') if tag.strip()]
        return tags
    except Exception as e:
        print(f"Error getting prerelease tags: {e}")
        return []


def get_last_version() -> str:
    """Get the last semantic version tag, or return 0.0.0 if none exist."""
    try:
        # Get current branch name
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = branch_result.stdout.strip()

        # Get tags merged into current branch
        result = subprocess.run(
            ['git', 'tag', '--merged', current_branch],
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
        print("Keeping current version:", current_version)
        return current_version

    if current_version == '0.0.0':
        # First version should be 0.0.1
        print("No previous version found. Setting first version to 0.0.1")
        return '0.0.1'

    # Analyze commits and determine bump
    bump = determine_bump(commits)
    new_version = increment_version(current_version, bump)
    print(f"Determined bump type: {bump}")
    return new_version


def determine_prerelease_version(base_version: str, prerelease_type: str) -> str:
    """
    Determine the prerelease version with proper increment.
    If prerelease tags exist for the base version, increment the counter.
    Otherwise, start at .1
    """
    prerelease_tags = get_prerelease_tags(base_version, prerelease_type)

    if not prerelease_tags:
        # No existing prerelease tags, start at .1
        return f"{base_version}-{prerelease_type}.1"

    # Extract the increment numbers from existing tags
    increments = []
    pattern = re.compile(rf'^{re.escape(base_version)}-{re.escape(prerelease_type)}\.(\d+)$')

    for tag in prerelease_tags:
        match = pattern.match(tag)
        if match:
            increments.append(int(match.group(1)))

    if not increments:
        return f"{base_version}-{prerelease_type}.1"

    # Get the highest increment and add 1
    max_increment = max(increments)
    return f"{base_version}-{prerelease_type}.{max_increment + 1}"


def create_zip(repo_name: str, vs_version: str, version: str) -> Path:
    """
    Create a zip file excluding .git and .github directories.
    Returns the filename of the created zip.
    """
    build_dir = Path('build')
    build_dir.mkdir(exist_ok=True)
    zip_filename = build_dir / f'{repo_name}-{vs_version}-{version}.zip'

    with ZipFile(zip_filename, 'w') as zf:
        for root, dirs, files in os.walk('.'):
            # Remove .git, .github, and build from dirs to prevent traversal
            dirs[:] = [d for d in dirs if d not in ['.git', '.github', 'build']]

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


def create_github_release(version: str, vs_version: str, zip_filename: Path):
    """Create a GitHub release with the zip file as an artifact."""
    try:
        subprocess.run([
            'gh', 'release', 'create', version,
            zip_filename,
            '--title', f'{version}',
            '--notes', f'Automated release for VSVanillaPlus Release version {version}'
        ], check=True)
        print(f"Created GitHub release for {version} built on Vintage Story version {vs_version}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating GitHub release: {e}")
        raise


class ApiQueryException(Exception):
    pass


def get_api_version(stable):
    """Get the Vintage Story version from the Official HTTP API."""
    url = "https://api.vintagestory.at/lateststable.txt"
    if not stable:
        url = "https://api.vintagestory.at/latestunstable.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Error fetching Vintage Story version from API: {e}")
        raise ApiQueryException(f"Failed to fetch Vintage Story version from API: {e}")


def main():
    """Main versioning workflow."""
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description='Semantic Versioning Script for Git Repositories'
    )
    parser.add_argument('--name', type=str,
                       help='Name of the repository (default: derived from GITHUB_REPOSITORY)')
    parser.add_argument('--build', action='store_true',
                        help='Build artifact and GitHub release')
    parser.add_argument('--dry-run', action='store_true',
                        help='Perform a dry run without creating tags or releases')
    vs_version_group = parser.add_mutually_exclusive_group(required=True)
    vs_version_group.add_argument('--vs-version', type=str, default=None,
                        help='Vintage Story version to build for (Default: 1.21.6)')
    vs_version_group.add_argument('--api-stable-vs-version', action='store_true',
                        help='Use Vintage Story version from the latest stable API release')
    vs_version_group.add_argument('--api-unstable-vs-version', action='store_true',
                        help='Use Vintage Story version from the latest unstable API release')
    exclusive_group = parser.add_mutually_exclusive_group(required=False)
    exclusive_group.add_argument('--dev', action='store_true',
                       help='Create a development version (X.Y.Z.devN+hash)')
    exclusive_group.add_argument('--alpha', action='store_true',
                       help='Create an alpha prerelease version (X.Y.Z-alpha.N)')
    exclusive_group.add_argument('--beta', action='store_true',
                       help='Create a beta prerelease version (X.Y.Z-beta.N)')
    exclusive_group.add_argument('--rc', action='store_true',
                       help='Create a release candidate version (X.Y.Z-rc.N)')
    exclusive_group.add_argument('--create-git-tag', action='store_true',
                       help='Create and push a git tag for the new version')

    args = parser.parse_args()

    print("=== Semantic Versioning Script ===\n")

    # Check if dry-run mode is active
    if args.dry_run:
        print("🔍 DRY-RUN MODE ACTIVE - No tags, releases, or artifacts will be created\n")

    # Get repository name
    if args.name:
        repo_name = args.name
    else:
        repo_full_name = os.getenv('GITHUB_REPOSITORY', 'unknown/repo')
        repo_name = repo_full_name.split('/')[-1]
    print(f"Repository: {repo_name}\n")

    # Get Vintage Story version
    if not args.vs_version:
        vs_version = get_api_version(stable=args.api_stable_vs_version)
    else:
        vs_version = args.vs_version
    print(f"Vintage Story version: {vs_version}\n")

    # Step 1: Get current version
    current_version = get_last_version()
    print(f"Current version: {current_version}")

    # Step 2: Get commits since last version
    commits = get_commits_since_tag(current_version)
    print(f"Found {len(commits)} new commits\n")

    # Step 3: Determine new version
    base_version = determine_new_version(current_version, commits)
    if base_version is None:
        print("Cannot determine new version")
        sys.exit(1)

    # Step 4: Format version based on argument
    new_version = base_version  # Initialize with base version
    if args.dev:
        # Dev version: {new_version}.dev{distance_from_main_HEAD}+{GIT_HASH}
        distance = get_distance_from_main()
        git_hash = get_current_git_hash()
        new_version = f"{base_version}.dev{distance}+{git_hash}"
        print(f"Dev version format: {new_version}")
        print(f"Distance from main: {distance}")
        print(f"Git hash: {git_hash}")
    elif args.alpha:
        # Alpha version: {new_version}-alpha.{current_increment_of_alpha}
        new_version = determine_prerelease_version(base_version, 'alpha')
        print(f"Alpha version: {new_version}")
    elif args.beta:
        # Beta version: {new_version}-beta.{current_increment_of_beta}
        new_version = determine_prerelease_version(base_version, 'beta')
        print(f"Beta version: {new_version}")
    elif args.rc:
        # RC version: {new_version}-rc.{current_increment_of_rc}
        new_version = determine_prerelease_version(base_version, 'rc')
        print(f"RC version: {new_version}")
    else:
        # No argument: use standard version format {new_version}
        new_version = base_version
        print(f"Standard version: {new_version}")

    # Step 5: Output version for TeamCity and GitHub Actions
    # Output version for TeamCity
    print(f"##teamcity[setParameter name='build.docker.version.new' value='{new_version.replace('+', '-')}']")
    print(f"##teamcity[setParameter name='build.docker.tag' value='{vs_version}-{new_version.replace('+', '-')}']")
    print(f"##teamcity[setParameter name='build.version.new' value='{new_version}']")
    print(f"##teamcity[setParameter name='build.version.old' value='{current_version}']")
    print(f"##teamcity[setParameter name='build.gameversion' value='{vs_version}']")

    if args.build:
        # Step 6: Create git tag (only for non-dev versions)
        if args.create_git_tag:
            if args.dry_run:
                print("[DRY-RUN] Would create git tag:", new_version)
            else:
                print("Creating git tag...")
                create_git_tag(new_version)

        # Output version for GitHub Actions
        github_output = os.environ.get('GITHUB_OUTPUT', None)
        if github_output:
            with open(os.environ.get('GITHUB_OUTPUT', ''), 'a') as f:
                f.write(f'version={new_version}\n')

            # Step 7: Create zip file (only for non-dev versions)
            if not args.dev:
                if args.dry_run:
                    print("\n[DRY-RUN] Would create release artifact:", f'{repo_name}-{vs_version}-{new_version}.zip')
                    print("[DRY-RUN] Would create GitHub release for version:", new_version)
                else:
                    print("\nCreating release artifact...")
                    zip_filename = create_zip(repo_name, vs_version, new_version)

                    # Step 8: Create GitHub release
                    print("\nCreating GitHub release...")
                    create_github_release(new_version, vs_version, zip_filename)

    print("\n=== Versioning Complete ===")


if __name__ == '__main__':
    main()