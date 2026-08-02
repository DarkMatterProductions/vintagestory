"""Docker SDK wrapper: client/context resolution, build, tag, push, login, prune."""
import subprocess
from typing import Dict, Optional

import docker

from vs_repo_tooling.toolslib.script_handler import ScriptOutput


def get_client(context: Optional[str] = None) -> docker.DockerClient:
    """Return a Docker client. `docker` contexts aren't addressable through the
    SDK directly, so a named context is resolved to its endpoint via the CLI."""
    if not context:
        return docker.from_env()
    result = subprocess.run(
        ["docker", "context", "inspect", context, "--format", '{{(index .Endpoints "docker").Host}}'],
        capture_output=True,
        text=True,
        check=True,
    )
    base_url = result.stdout.strip()
    return docker.DockerClient(base_url=base_url)


def build_image(
    out: ScriptOutput,
    client: docker.DockerClient,
    tag: str,
    build_args: Optional[Dict[str, str]] = None,
    path: str = ".",
) -> None:
    """Build an image, streaming build log lines through `out`."""
    for chunk in client.api.build(path=path, tag=tag, buildargs=build_args or {}, rm=True, decode=True):
        if "stream" in chunk:
            for line in chunk["stream"].splitlines():
                if line.strip():
                    out.action(line.strip())
        elif "errorDetail" in chunk or "error" in chunk:
            raise RuntimeError(chunk.get("error") or chunk["errorDetail"].get("message"))


def push_image(out: ScriptOutput, client: docker.DockerClient, repository: str, tag: str) -> None:
    """Push an image, streaming progress through `out`."""
    for chunk in client.api.push(repository, tag=tag, decode=True):
        if "error" in chunk or "errorDetail" in chunk:
            raise RuntimeError(chunk.get("error") or chunk["errorDetail"].get("message"))
        if "status" in chunk:
            progress = chunk.get("progress", "")
            out.action(f"{chunk['status']} {progress}".strip())


def tag_image(client: docker.DockerClient, source_tag: str, repository: str, tag: str) -> None:
    """Tag an existing local image under a new repository/tag."""
    client.images.get(source_tag).tag(repository, tag)


def login(client: docker.DockerClient, registry: str, username: str, password: str) -> dict:
    """Authenticate against a registry."""
    return client.login(username=username, password=password, registry=registry)


def registry_for_repository(repository: str) -> str:
    """Resolve the registry host a repository lives on, mirroring Docker's own
    resolution rules: the leading path segment is an explicit registry host if
    it contains a '.' or ':' or is 'localhost'; otherwise it's Docker Hub."""
    first_segment = repository.split("/", 1)[0]
    if "." in first_segment or ":" in first_segment or first_segment == "localhost":
        return first_segment
    return "docker.io"


def prune_images(client: docker.DockerClient) -> dict:
    """Remove unused (dangling) images."""
    return client.images.prune()
