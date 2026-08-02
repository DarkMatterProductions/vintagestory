"""Semantic versioning core logic for git repositories.

Supports conventional commits: feat:, fix:, and BREAKING CHANGE.
Ported from the standalone semver.py script; output now goes through
ScriptOutput instead of bare print().
"""
import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from zipfile import ZipFile

import requests

from vs_repo_tooling import git_ops, github_release
from vs_repo_tooling.toolslib.script_handler import ScriptOutput

_default_out = ScriptOutput()


def _resolve_out(out: Optional[ScriptOutput]) -> ScriptOutput:
    return out if out is not None else _default_out


class ApiQueryException(Exception):
    pass


def get_distance_from_main(out: Optional[ScriptOutput] = None) -> int:
    """Get the number of commits the current branch is ahead of main."""
    out = _resolve_out(out)
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "main..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return int(result.stdout.strip())
    except Exception as e:
        out.error(f"Error getting distance from main: {e}")
        return 0


def get_current_git_hash(is_dev: bool = False, out: Optional[ScriptOutput] = None) -> str:
    """Get the shortened git hash of the current HEAD."""
    out = _resolve_out(out)
    get_hash_cmd = ["git", "write-tree"] if is_dev else ["git", "rev-parse", "--short", "HEAD"]
    try:
        result = subprocess.run(get_hash_cmd, capture_output=True, text=True, check=True)
        result_hash = result.stdout.strip()
        return result_hash[:7] if len(result_hash) > 7 else result_hash
    except Exception as e:
        out.error(f"Error getting git hash: {e}")
        return "unknown"


def get_prerelease_tags(base_version: str, prerelease_type: str, out: Optional[ScriptOutput] = None) -> List[str]:
    """Get all prerelease tags for a given base version and type."""
    out = _resolve_out(out)
    try:
        result = subprocess.run(
            ["git", "tag", "--list", f"{base_version}-{prerelease_type}.*"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [tag.strip() for tag in result.stdout.strip().split("\n") if tag.strip()]
    except Exception as e:
        out.error(f"Error getting prerelease tags: {e}")
        return []


def get_last_version(out: Optional[ScriptOutput] = None) -> str:
    """Get the last semantic version tag, or return 0.0.0 if none exist."""
    out = _resolve_out(out)
    try:
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True, check=True,
        )
        current_branch = branch_result.stdout.strip()

        result = subprocess.run(
            ["git", "tag", "--merged", current_branch], capture_output=True, text=True, check=True,
        )
        tags = result.stdout.strip().split("\n")
        pattern = re.compile(r"^((?P<vs_version>\d+\.\d+\.\d+)-)*(?P<version>\d+\.\d+\.\d+)$")
        version_tags = [
            pattern.match(tag).groupdict()["version"]
            for tag in tags if pattern.match(tag) is not None
        ]

        if not version_tags:
            return "0.0.0"

        version_tags.sort(key=lambda v: tuple(map(int, v.split("."))))
        return version_tags[-1]
    except Exception as e:
        out.error(f"Error getting last version: {e}")
        return "0.0.0"


def get_commits_since_tag(tag: str, out: Optional[ScriptOutput] = None) -> List[str]:
    """Get commit hashes since the given tag."""
    out = _resolve_out(out)
    try:
        if tag == "0.0.0":
            result = subprocess.run(["git", "rev-list", "HEAD"], capture_output=True, text=True, check=True)
        else:
            result = subprocess.run(["git", "rev-list", f"{tag}..HEAD"], capture_output=True, text=True, check=True)
        return [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]
    except Exception as e:
        out.error(f"Error getting commits: {e}")
        return []


def get_commit_message(commit_hash: str, out: Optional[ScriptOutput] = None) -> Tuple[str, str]:
    """Get commit subject and body."""
    out = _resolve_out(out)
    try:
        result = subprocess.run(
            ["git", "show", "-s", "--format=%s%n%b", commit_hash], capture_output=True, text=True, check=True,
        )
        lines = result.stdout.split("\n", 1)
        subject = lines[0] if lines else ""
        body = lines[1] if len(lines) > 1 else ""
        return subject, body
    except Exception as e:
        out.error(f"Error getting commit message for {commit_hash}: {e}")
        return "", ""


def determine_bump(commits: List[str]) -> str:
    """Determine the semantic version bump based on commits: 'major', 'minor', or 'patch'."""
    has_major = False
    has_minor = False

    for commit_hash in commits:
        subject, body = get_commit_message(commit_hash)

        if "BREAKING CHANGE:" in subject or "BREAKING CHANGE:" in body:
            has_major = True
            break

        if re.match(r"^(feat|fix)!:", subject):
            has_major = True
            break

        if re.match(r"^feat:", subject):
            has_minor = True

    if has_major:
        return "major"
    elif has_minor:
        return "minor"
    return "patch"


def increment_version(version: str, bump: str) -> str:
    """Increment the version based on bump type."""
    major, minor, patch = map(int, version.split("."))
    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def determine_new_version(current_version: str, commits: List[str], out: Optional[ScriptOutput] = None) -> Optional[str]:
    """Determine the new version based on current version and commits."""
    out = _resolve_out(out)
    if not commits:
        out.info("No new commits since last version")
        out.info(f"Keeping current version: {current_version}")
        return current_version

    if current_version == "0.0.0":
        out.info("No previous version found. Setting first version to 0.0.1")
        return "0.0.1"

    bump = determine_bump(commits)
    new_version = increment_version(current_version, bump)
    out.info(f"Determined bump type: {bump}")
    return new_version


def determine_prerelease_version(base_version: str, prerelease_type: str, out: Optional[ScriptOutput] = None) -> str:
    """Determine the prerelease version with proper increment.

    If prerelease tags exist for the base version, increment the counter.
    Otherwise, start at .1
    """
    out = _resolve_out(out)
    prerelease_tags = get_prerelease_tags(base_version, prerelease_type, out=out)

    if not prerelease_tags:
        return f"{base_version}-{prerelease_type}.1"

    increments = []
    pattern = re.compile(rf"^{re.escape(base_version)}-{re.escape(prerelease_type)}\.(\d+)$")
    for tag in prerelease_tags:
        match = pattern.match(tag)
        if match:
            increments.append(int(match.group(1)))

    if not increments:
        return f"{base_version}-{prerelease_type}.1"

    return f"{base_version}-{prerelease_type}.{max(increments) + 1}"


def create_zip(repo_name: str, vs_version: str, version: str, out: Optional[ScriptOutput] = None) -> Path:
    """Create a zip file excluding .git, .github, and build directories. Returns the created path."""
    out = _resolve_out(out)
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)
    zip_filename = build_dir / f"{repo_name}-{vs_version}-{version}.zip"

    with ZipFile(zip_filename, "w") as zf:
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in [".git", ".github", "build"]]
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(".")
                archive_name = f"{repo_name}-{version}/{relative_path}"
                zf.write(file_path, arcname=archive_name)

    out.action(f"Created zip file: {zip_filename}")
    return zip_filename


def create_git_tag(version: str, out: Optional[ScriptOutput] = None) -> None:
    """Create and push a git tag for the new version."""
    out = _resolve_out(out)
    try:
        subprocess.run(["git", "tag", version], check=True)
        subprocess.run(["git", "push", "origin", version], check=True)
        out.action(f"Created and pushed git tag: {version}")
    except subprocess.CalledProcessError as e:
        out.error(f"Error creating git tag: {e}")
        raise


def create_github_release(version: str, vs_version: str, zip_filename: Path, out: Optional[ScriptOutput] = None) -> None:
    """Create a GitHub release with the zip file as an artifact, via PyGithub."""
    out = _resolve_out(out)
    try:
        token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GH_TOKEN or GITHUB_TOKEN must be set to create a GitHub release")
        repo_slug = git_ops.origin_repo_slug()
        if not repo_slug:
            raise RuntimeError("Could not determine owner/repo from the origin remote")
        github_release.create_release(
            token=token,
            repo_slug=repo_slug,
            tag=version,
            notes=f"Automated release for VSVanillaPlus Release version {version}",
            assets=[zip_filename],
        )
        out.action(f"Created GitHub release for {version} built on Vintage Story version {vs_version}")
    except Exception as e:
        out.error(f"Error creating GitHub release: {e}")
        raise


def get_api_version(stable: bool, out: Optional[ScriptOutput] = None) -> str:
    """Get the Vintage Story version from the Official HTTP API."""
    out = _resolve_out(out)
    url = "https://api.vintagestory.at/lateststable.txt" if stable else "https://api.vintagestory.at/latestunstable.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        out.error(f"Error fetching Vintage Story version from API: {e}")
        raise ApiQueryException(f"Failed to fetch Vintage Story version from API: {e}")
