"""Command-line entrypoint for the semantic versioning workflow."""
import argparse
import os
import sys
from typing import Optional, Sequence

from vs_repo_tooling.toolslib.script_handler import ScriptOutput
from vs_repo_tooling.versioning import core


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Semantic Versioning Script for Git Repositories")
    parser.add_argument("--name", type=str,
                         help="Name of the repository (default: derived from GITHUB_REPOSITORY)")
    parser.add_argument("--build", action="store_true", help="Build artifact and GitHub release")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without creating tags or releases")
    parser.add_argument("--no-create-git-tag", action="store_false", dest="create_git_tag",
                         help="Disable create and push for git tags of the new version")

    vs_version_group = parser.add_mutually_exclusive_group(required=True)
    vs_version_group.add_argument("--vs-version", type=str, default=None,
                                   help="Vintage Story version to build for (Default: 1.21.6)")
    vs_version_group.add_argument("--api-stable-vs-version", action="store_true",
                                   help="Use Vintage Story version from the latest stable API release")
    vs_version_group.add_argument("--api-unstable-vs-version", action="store_true",
                                   help="Use Vintage Story version from the latest unstable API release")

    exclusive_output_group = parser.add_mutually_exclusive_group(required=False)
    exclusive_output_group.add_argument("--teamcity", action="store_true",
                                         help="Output metadata to be consumed by TeamCity")
    exclusive_output_group.add_argument("--github", action="store_true",
                                         help="Output metadata to be consumed by GitHub Actions")
    exclusive_output_group.add_argument("--env-file", action="store_true",
                                         help="Output metadata to environment variable file")

    exclusive_group = parser.add_mutually_exclusive_group(required=False)
    exclusive_group.add_argument("--dev", action="store_true",
                                  help="Create a development version (X.Y.Z.devN+hash)")
    exclusive_group.add_argument("--alpha", action="store_true",
                                  help="Create an alpha prerelease version (X.Y.Z-alpha.N)")
    exclusive_group.add_argument("--beta", action="store_true",
                                  help="Create a beta prerelease version (X.Y.Z-beta.N)")
    exclusive_group.add_argument("--rc", action="store_true",
                                  help="Create a release candidate version (X.Y.Z-rc.N)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Main versioning workflow."""
    out = ScriptOutput()
    args = build_parser().parse_args(argv)

    out.section_header("Semantic Versioning Script")

    if args.dry_run:
        out.warning("[DRY-RUN MODE ACTIVE] No tags, releases, or artifacts will be created")

    if args.name:
        repo_name = args.name
    else:
        repo_full_name = os.getenv("GITHUB_REPOSITORY", "unknown/repo")
        repo_name = repo_full_name.split("/")[-1]
    out.info(f"Repository: {repo_name}")

    if not args.vs_version:
        vs_version = core.get_api_version(stable=args.api_stable_vs_version, out=out)
    else:
        vs_version = args.vs_version
    out.info(f"Vintage Story version: {vs_version}")

    current_version = core.get_last_version(out=out)
    out.info(f"Current version: {current_version}")

    commits = core.get_commits_since_tag(current_version, out=out)
    out.info(f"Found {len(commits)} new commits")

    base_version = core.determine_new_version(current_version, commits, out=out)
    if base_version is None:
        out.error("Cannot determine new version")
        sys.exit(1)

    if args.dev:
        distance = core.get_distance_from_main(out=out)
        git_hash = core.get_current_git_hash(args.dev, out=out)
        new_version = f"{base_version}.dev{distance}+{git_hash}"
        out.info(f"Dev version format: {new_version}")
        out.info(f"Distance from main: {distance}")
        out.info(f"Git hash: {git_hash}")
    elif args.alpha:
        new_version = core.determine_prerelease_version(base_version, "alpha", out=out)
        out.info(f"Alpha version: {new_version}")
    elif args.beta:
        new_version = core.determine_prerelease_version(base_version, "beta", out=out)
        out.info(f"Beta version: {new_version}")
    elif args.rc:
        new_version = core.determine_prerelease_version(base_version, "rc", out=out)
        out.info(f"RC version: {new_version}")
    else:
        new_version = base_version
        out.info(f"Standard version: {new_version}")

    if new_version == current_version:
        out.info(f"No version bump detected, keeping version at {new_version}. No git tag will be created.")
    elif args.create_git_tag is True:
        if args.dry_run:
            out.warning(f"[DRY-RUN MODE ACTIVE] Would have created and pushed git tag: {new_version}")
        else:
            core.create_git_tag(new_version, out=out)
    else:
        out.info("No valid Git Tag implementation detected. Git tag creation disabled.")

    if args.teamcity:
        print(f"##teamcity[setParameter name='build.docker.version.new' value='{new_version.replace('+', '-')}']")
        print(f"##teamcity[setParameter name='build.docker.tag' value='{vs_version}-{new_version.replace('+', '-')}']")
        print(f"##teamcity[setParameter name='build.version.new' value='{new_version}']")
        print(f"##teamcity[setParameter name='build.version.old' value='{current_version}']")
        print(f"##teamcity[setParameter name='build.gameversion' value='{vs_version}']")
    elif args.env_file:
        env_var_output = (
            f"VERSION={new_version}\n"
            f"DOCKER_VERSION_NEW={new_version.replace('+', '-')}\n"
            f"DOCKER_TAG={vs_version}-{new_version.replace('+', '-')}\n"
            f"GAMEVERSION={vs_version}\n"
            f"VERSION_OLD={current_version}\n"
        )
        if not args.dry_run:
            with open("build.env", "w") as f:
                f.write(env_var_output)
        else:
            indented_output = "\n   ".join(env_var_output.split("\n"))
            out.warning(f"[DRY-RUN MODE ACTIVE] Would have written the following to 'build.env':\n   {indented_output}")
    else:
        raise ValueError("No output format specified, you must select one of --teamcity, --github, or --env-file")

    out.section_footer()


if __name__ == "__main__":
    main()
