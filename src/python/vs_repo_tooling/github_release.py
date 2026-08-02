"""GitHub release creation via PyGithub, replacing the `gh` CLI."""
from pathlib import Path
from typing import List, Optional

from github import Auth, Github
from github.GitRelease import GitRelease


def create_release(
    token: str,
    repo_slug: str,
    tag: str,
    notes: str,
    *,
    title: Optional[str] = None,
    prerelease: bool = False,
    assets: Optional[List[Path]] = None,
) -> GitRelease:
    """Create a GitHub release (and optionally upload assets), mirroring `gh release create`."""
    client = Github(auth=Auth.Token(token))
    repo = client.get_repo(repo_slug)
    release = repo.create_git_release(
        tag=tag,
        name=title or tag,
        message=notes,
        prerelease=prerelease,
    )
    for asset in assets or []:
        release.upload_asset(str(asset))
    return release
