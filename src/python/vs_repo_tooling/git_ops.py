"""Git plumbing helpers: tag refresh, commit-log parsing, and remote parsing.

No Python-native git library is used here per project direction — these stay
as targeted subprocess calls, consistent with how the versioning core handles git.
"""
import re
import subprocess
from typing import List, Optional, Tuple

from vs_repo_tooling.toolslib.script_handler import ScriptOutput


def list_local_tags(out: ScriptOutput) -> List[str]:
    """List all local git tags."""
    result = out.run_cmd(["git", "tag", "-l"], check=True)
    return [t for t in result.stdout.strip().split("\n") if t]


def refresh_tags(out: ScriptOutput) -> int:
    """Purge local git tags and re-fetch them from origin. Returns the new tag count."""
    local_tags = list_local_tags(out)
    out.action("Purging Local Git Tags")
    if local_tags:
        out.run_cmd(["git", "tag", "-d", *local_tags])
    out.error_handling_execute("Pulling Git Tags", ["git", "fetch", "origin", "--tags"])
    count = len(list_local_tags(out))
    out.action(f"Pulled ({out.LAVENDER}{count}{out.NC}) tags from Repository.")
    return count


def commits_since(tag: str) -> List[Tuple[str, str]]:
    """Return (short_hash, first_nonempty_message_line) for each commit since tag."""
    result = subprocess.run(
        ["git", "--no-pager", "log", f"{tag}..HEAD", "--format=%x1f%h%x1e%B"],
        capture_output=True,
        text=True,
        check=True,
    )
    entries = []
    for record in result.stdout.split("\x1f"):
        if not record:
            continue
        commit_hash, _, message = record.partition("\x1e")
        for line in message.split("\n"):
            if line.strip():
                entries.append((commit_hash, line.strip()))
                break
    return entries


def generate_release_notes(
    vs_version: str,
    docker_tag: str,
    vs_version_state: str,
    version_old: str,
    tag_matrix: List[str],
    repositories: List[str],
) -> str:
    """Build the release-notes.md Markdown body, matching build-release.sh's template."""
    commit_lines = "\n".join(f"- {message} ({commit_hash})" for commit_hash, message in commits_since(version_old))
    tag_lines = "\n".join(f"- `{tag}`" for tag in tag_matrix)
    if vs_version_state == "stable":
        tag_lines = f"{tag_lines}\n- `latest`" if tag_lines else "- `latest`"
    repo_lines = "\n".join(f"- `{repo}`" for repo in repositories)
    return f"""## Vintage Story Docker Image Release

**Vintage Story Version:** `{vs_version}`
**Docker Image Version:** `{docker_tag}`
**Release State:** `{vs_version_state}`

### Included Commits
{commit_lines}

### Docker Image Tags
{tag_lines}

### Available Repositories
{repo_lines}
"""


def origin_repo_slug() -> Optional[str]:
    """Parse `owner/repo` out of the origin remote URL (SSH or HTTPS form)."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True,
    )
    url = result.stdout.strip()
    match = re.search(r"[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", url)
    if not match:
        return None
    return f"{match.group('owner')}/{match.group('repo')}"
