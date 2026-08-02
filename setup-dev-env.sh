#!/usr/bin/env bash
# Bootstraps the pyenv/pipenv environment previously set up inline by
# build-dev.sh/build-release.sh. Run this once per dev environment before
# using `python -m vs_repo_tooling.entrypoints.*` -- it is not part of the
# Python build pipeline's runtime flow.
set -euo pipefail

PYTHON_VERSION="3.11.9"
PYTHON_SHORT_VERSION="$(echo "${PYTHON_VERSION}" | awk -F'.' '{ print $1"."$2 }')"

echo "Initializing pyenv environment..."
if [ ! "${MSYSTEM:-}" = "MINGW64" ]; then
  export PYENV_ROOT="$HOME/.pyenv"
  [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init - bash)"
  eval "$(pyenv virtualenv-init -)"
fi

echo "Selecting Python ${PYTHON_VERSION}."
pyenv local "${PYTHON_VERSION}"

echo "Installing system dependencies: pipenv & requests."
"python${PYTHON_SHORT_VERSION}" -m pip install pipenv requests

echo "Installing Python dependencies into virtual environment."
"python${PYTHON_SHORT_VERSION}" -m pipenv install --python "${PYTHON_SHORT_VERSION}"

echo "Dev environment ready. Use 'pipenv shell' or 'pipenv run' to enter it."
