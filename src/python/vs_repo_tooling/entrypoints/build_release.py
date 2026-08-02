#!/usr/bin/env python3
"""python -m vs_repo_tooling.entrypoints.build_release -- equivalent of build-release.sh."""
import sys
import traceback

from vs_repo_tooling import build_pipeline
from vs_repo_tooling.settings import ReleaseBuildSettings
from vs_repo_tooling.toolslib.script_handler import ScriptOutput


def main(argv=None) -> None:
    out = ScriptOutput()
    try:
        vs_version_arg, state_arg, dry_run = build_pipeline.parse_cli_args(argv if argv is not None else sys.argv[1:])
        out.dry_run = dry_run
        settings = ReleaseBuildSettings()
        build_pipeline.run(out, settings, vs_version_arg, state_arg, publish_release=True)
    except SystemExit:
        raise
    except BaseException as e:
        out.error(f"{type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
