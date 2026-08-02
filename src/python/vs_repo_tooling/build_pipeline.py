"""Shared orchestration for the dev and release Docker build pipelines."""
import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from vs_repo_tooling import docker_ops, git_ops, github_release
from vs_repo_tooling.settings import DevBuildSettings
from vs_repo_tooling.toolslib.script_handler import ScriptOutput
from vs_repo_tooling.versioning import core

_VS_VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(.*)$")


@dataclass
class VsVersionInfo:
    vs_version: str
    vs_version_state: str
    dotnet_version: str


@dataclass
class BuildVersion:
    version: str
    version_old: str
    docker_version_new: str
    docker_tag: str


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve the Vintage Story version to build")
    parser.add_argument(
        "--vs-version",
        required=True,
        help="Literal Vintage Story version to build for (e.g. 1.22.5)",
    )
    parser.add_argument(
        "--vs-version-state",
        choices=["stable", "unstable"],
        default=None,
        help="Override the release state (drives the 'latest' tag and GitHub prerelease flag)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enable Dry run mode.",
    )
    return parser


def parse_cli_args(argv: Optional[Sequence[str]]) -> Tuple[str, Optional[str], bool]:
    """Parse --vs-version/--vs-version-state/--dry-run from CLI args."""
    args = build_arg_parser().parse_args(argv)
    return args.vs_version, args.vs_version_state, args.dry_run


def resolve_vs_version(
    settings: DevBuildSettings,
    vs_version_arg: str,
    state_arg: Optional[str],
) -> VsVersionInfo:
    """Resolve the Vintage Story + .NET version from a literal version string."""
    vs_version_state = ""
    if state_arg == "stable":
        vs_version_state = "stable"
    elif state_arg == "unstable":
        vs_version_state = "unstable"

    match = _VS_VERSION_PATTERN.match(vs_version_arg)
    if not match:
        raise ValueError(f"Could not parse Vintage Story version from: {vs_version_arg!r}")
    major, minor, build, devhash = match.groups()
    vs_version = f"{major}.{minor}.{build}{devhash}"

    dotnet_version = settings.dotnet_version_by_vs.get(f"{major}.{minor}")
    if dotnet_version is None:
        raise ValueError(f"No .NET version configured for Vintage Story {major}.{minor}")

    return VsVersionInfo(vs_version=vs_version, vs_version_state=vs_version_state, dotnet_version=dotnet_version)


def _determine_build_version(
    out: ScriptOutput,
    vs_info: VsVersionInfo,
    *,
    dev: bool,
    create_git_tag: bool,
) -> BuildVersion:
    """Equivalent of `semver.py --env-file [--dev] [--no-create-git-tag]`, called in-process."""
    current_version = core.get_last_version(out=out)
    commits = core.get_commits_since_tag(current_version, out=out)
    base_version = core.determine_new_version(current_version, commits, out=out)

    if dev:
        distance = core.get_distance_from_main(out=out)
        git_hash = core.get_current_git_hash(is_dev=True, out=out)
        new_version = f"{base_version}.dev{distance}+{git_hash}"
    else:
        new_version = base_version

    if new_version != current_version and create_git_tag:
        if out.dry_run:
            out.action(f"Creating and pushing git tag: {new_version}")
        else:
            core.create_git_tag(new_version, out=out)

    docker_version_new = new_version.replace("+", "-")
    docker_tag = f"{vs_info.vs_version}-{docker_version_new}"
    return BuildVersion(
        version=new_version,
        version_old=current_version,
        docker_version_new=docker_version_new,
        docker_tag=docker_tag,
    )


def _build_tag_matrix(build_version: BuildVersion, vs_info: VsVersionInfo, *, publish_release: bool) -> List[str]:
    tags = [
        f"{build_version.docker_version_new}-python3-trixie-slim",
        build_version.docker_version_new,
    ]
    if publish_release:
        tags += [
            f"{build_version.docker_tag}-python3-trixie-slim",
            build_version.docker_tag,
            vs_info.vs_version,
        ]
    return tags


def run(
    out: ScriptOutput,
    settings: DevBuildSettings,
    vs_version_arg: str,
    state_arg: Optional[str] = None,
    *,
    publish_release: bool,
) -> None:
    out.section_header("Container Build")
    out.step_header("Environment Initialization")

    vs_info = resolve_vs_version(settings, vs_version_arg, state_arg)

    out.sub_step_header("Cleaning Git Tags for Semver")
    git_ops.refresh_tags(out)

    out.sub_step_header("Generating Semver Arguments")
    build_version = _determine_build_version(
        out, vs_info, dev=not publish_release, create_git_tag=publish_release,
    )

    tag_matrix = _build_tag_matrix(build_version, vs_info, publish_release=publish_release)

    out.step_header("Vintage Story Docker Image Build")
    out.info(f"Image Version: {out.LAVENDER}{build_version.version}{out.NC} "
              f"Vintage Story Version: {out.LAVENDER}{vs_info.vs_version}{out.NC}")
    out.info(f"State: {out.LAVENDER}{vs_info.vs_version_state}{out.NC} "
              f".Net Version: {out.LAVENDER}{vs_info.dotnet_version}{out.NC}")
    out.list_header("Docker Image Tags")
    for tag in tag_matrix:
        out.list_item(f"{out.LAVENDER}{tag}{out.NC}")
    out.list_header("Target Repositories")
    for repo in settings.repositories:
        out.list_item(f"{out.LAVENDER}{repo}{out.NC}")

    base_repository = f"{settings.registry_host}/{settings.image_name}"
    base_tag = f"{vs_info.vs_version}-{build_version.docker_version_new}"
    build_args = {
        "VERSION": build_version.version,
        "VS_VERSION_STATE": vs_info.vs_version_state,
        "VS_VERSION": vs_info.vs_version,
        "DOTNET_VERSION": vs_info.dotnet_version,
    }

    local_client = docker_ops.get_client()
    out.action(f"Building Container image: {base_repository}:{base_tag}")
    if not out.dry_run:
        docker_ops.build_image(out, local_client, f"{base_repository}:{base_tag}", build_args)
    out.action(f"Pushing Image to ({out.LAVENDER}{base_repository}{out.NC}) Registry")
    if not out.dry_run:
        docker_ops.push_image(out, local_client, base_repository, base_tag)

    out.step_header("Publishing Images")
    remote_client = docker_ops.get_client(settings.docker_context)

    logged_in_registries = set()
    for repo in settings.repositories:
        registry = docker_ops.registry_for_repository(repo)
        if registry not in logged_in_registries:
            username, token = settings.registry_credentials.get(registry, ("", ""))
            if not username or not token:
                raise RuntimeError(f"No credentials configured for registry {registry!r} (required to publish {repo})")
            out.action(f"Logging into {out.LAVENDER}{registry}{out.NC}")
            if not out.dry_run:
                docker_ops.login(remote_client, registry, username, token)
            logged_in_registries.add(registry)

        out.action(f"Processing Image for Repository: {out.LAVENDER}{repo}{out.NC}")
        for tag in tag_matrix:
            out.action(f"Processing Image Tag: {out.LAVENDER}{tag}{out.NC}")
            out.action(f"  Tagging Image: {out.LAVENDER}{repo}:{tag}{out.NC}")
            out.action(f"  Pushing Image to Repository: {out.LAVENDER}{repo}{out.NC}")
            if not out.dry_run:
                docker_ops.tag_image(remote_client, f"{base_repository}:{base_tag}", repo, tag)
                docker_ops.push_image(out, remote_client, repo, tag)
        if publish_release and vs_info.vs_version_state == "stable":
            out.action(f"Processing ({out.LAVENDER}{vs_info.vs_version_state}{out.NC}) Image Tag: {out.LAVENDER}latest{out.NC}")
            out.action(f"  Tagging Image: {out.LAVENDER}{repo}:latest{out.NC}")
            out.action(f"  Pushing Image to Repository: {out.LAVENDER}{repo}{out.NC}")
            if not out.dry_run:
                docker_ops.tag_image(remote_client, f"{repo}:{build_version.docker_tag}", repo, "latest")
                docker_ops.push_image(out, remote_client, repo, "latest")

    if publish_release:
        out.step_header("GitHub Release")
        notes = git_ops.generate_release_notes(
            vs_version=vs_info.vs_version,
            docker_tag=build_version.docker_tag,
            vs_version_state=vs_info.vs_version_state,
            version_old=build_version.version_old,
            tag_matrix=tag_matrix,
            repositories=settings.repositories,
        )
        out.action(f"Writing release notes to release-notes.md")
        if not out.dry_run:
            Path("release-notes.md").write_text(notes)
        token = settings.ghcr_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GHCR_TOKEN (or GH_TOKEN/GITHUB_TOKEN) must be set to create a GitHub release")
        repo_slug = git_ops.origin_repo_slug()
        if not repo_slug:
            raise RuntimeError("Could not determine owner/repo from the origin remote")
        out.action(f"Creating GitHub Release: {out.LAVENDER}{build_version.docker_tag}{out.NC}")
        if not out.dry_run:
            github_release.create_release(
                token=token,
                repo_slug=repo_slug,
                tag=build_version.docker_tag,
                title=build_version.docker_tag,
                notes=notes,
                prerelease=(vs_info.vs_version_state == "unstable"),
            )

    out.step_header("Build Cleanup")
    out.action(f"Pruning unused images")
    if not out.dry_run:
        docker_ops.prune_images(local_client)
    out.step_footer()
    out.section_footer()
