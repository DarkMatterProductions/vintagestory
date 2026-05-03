#!/usr/bin/env bash

# Color Code information from: https://misc.flogisoft.com/bash/tip_colors_and_formatting
RED='\e[38;5;124m'
LIGHTRED='\e[38;5;1m'
GREEN='\e[38;5;34m'
LIGHTGREEN='\e[38;5;82m'
LEAFGREEN='\e[38;5;112m'
BROWN='\e[38;5;94m'
LIGHTBROWN='\e[38;5;137m'
YELLOW='\e[38;5;226m'
LIGHTYELLOW='\e[38;5;228m'
DARKBLUE='\e[38;5;20m'
BLUE='\e[38;5;27m'
LIGHTBLUE='\e[38;5;33m'
CYAN='\e[38;5;74m'
LIGHTCYAN='\e[38;5;87m'
LAVENDER='\e[38;5;171m'
PURPLE='\e[38;5;54m'
BLUEPURPLE='\e[38;5;63m'
LIGHTPURPLE='\e[38;5;93m'
DARKGRAY='\e[38;5;238m'
LIGHTGRAY='\e[38;5;248m'
WHITE='\e[38;5;15m'
NC='\e[0m'

COLORIZE_STRING() {
  local STRING_COLOR=$1
  shift 1
  local TEXT="$*"
  local COLOR="${!STRING_COLOR}"
  local RESET
  local OUTERCOLORRESET
  RESET=$(printf '%b' "${NC}")
  OUTERCOLORRESET=$(printf '%b%b' "${NC}" "${COLOR}")

  # First, expand the text to resolve color variables
  local EXPANDED_TEXT
  EXPANDED_TEXT=$(printf '%b' "${TEXT}")

  # Replace ANSI reset codes with reset + action color
  EXPANDED_TEXT="${EXPANDED_TEXT//${RESET}/${OUTERCOLORRESET}}"

  printf "${OUTERCOLORRESET}%s${RESET}\n" "${EXPANDED_TEXT}"
}

COLORIZE_PADDING() {
  local STRING="$1"
  local START="${2:-21}"
  local END="${3:-16}"

  if [[ -z "$STRING" ]]; then
    echo "COLORIZE_PADDING: string may not be empty" >&2
    exit 1
  fi

  local N=${#STRING}
  local i
  local COLOR
  local CHAR

  for (( i = 0; i < N; i++ )); do
    CHAR="${STRING:i:1}"
    if (( N == 1 )); then
      COLOR="$START"
    else
      COLOR=$(( START * (N - 1) + (END - START) * i ))
      COLOR=$(( COLOR / (N - 1) ))
    fi
    printf '\e[38;5;%sm%s\e[0m' "$COLOR" "$CHAR"
  done
  echo
}

COLORIZE_PADDING_SERIES() {
  local STRING="$1"
  local SERIES="${2:-}"

  if [[ -z "$STRING" ]]; then
    echo "COLORIZE_PADDING_SERIES: string may not be empty" >&2
    exit 1
  fi
  if [[ -z "$SERIES" ]]; then
    echo "COLORIZE_PADDING_SERIES: series may not be empty (e.g. '54 91 129 171')" >&2
    exit 1
  fi

  local N=${#STRING}
  local -a S_ARR
  read -ra S_ARR <<< "$SERIES"
  local K=${#S_ARR[@]}

  if (( K == 0 )); then
    echo "COLORIZE_PADDING_SERIES: series may not be empty" >&2
    exit 1
  fi

  local i
  local INDEX
  local B
  local R
  local COLOR
  local CHAR

  for (( i = 0; i < N; i++ )); do
    CHAR="${STRING:i:1}"
    if (( N == 1 )); then
      INDEX=0
    else
      B=$(( N / K ))
      R=$(( N % K ))
      if (( i < R * (B + 1) )); then
        INDEX=$(( i / (B + 1) ))
      else
        INDEX=$(( R + (i - R * (B + 1)) / B ))
      fi
    fi
    COLOR="${S_ARR[INDEX]}"
    printf '\e[38;5;%sm%s\e[0m' "$COLOR" "$CHAR"
  done
  echo
}

section_header_string() {
  PADDING="================================================================================"
  OUTPUT_TEXT="$*"
  # Strip ANSI color codes for length calculation
  local TEXT_COUNT=$(echo -e "${OUTPUT_TEXT}" | sed $'s/\e\\[[0-9;]*m//g').
  COLORIZE_STRING LIGHTBROWN "$(COLORIZE_PADDING_SERIES "${PADDING:0:6}" "54 91 129 171") ${OUTPUT_TEXT} $(COLORIZE_PADDING_SERIES "${PADDING:$(( ${#TEXT_COUNT} + 6 )):$(( 80 - (${#TEXT_COUNT} + 6) ))}" "171 129 91 54")\n"
}

section_footer_string() {
  PADDING="================================================================================"
  local TEXT_COUNT=$(echo -e "${PADDING}" | sed $'s/\e\\[[0-9;]*m//g').
  COLORIZE_STRING NC "$(COLORIZE_PADDING_SERIES "${PADDING:0:$(( ${#TEXT_COUNT} /2 ))}" "54 91 129 171")$(COLORIZE_PADDING_SERIES "${PADDING:$(( ${#TEXT_COUNT} /2 )):$(( 80 - (${#TEXT_COUNT} / 2) ))}" "171 129 91 54")"
}

step_header_string() {
  PADDING="================================================================================"
  OUTPUT_TEXT="$*"
  # Strip ANSI color codes for length calculation
  local TEXT_COUNT=$(echo -e "${OUTPUT_TEXT}" | sed $'s/\e\\[[0-9;]*m//g').
  COLORIZE_STRING LIGHTBLUE "$(COLORIZE_PADDING "${PADDING:0:6}" 17 21) ${OUTPUT_TEXT} $(COLORIZE_PADDING "${PADDING:$(( ${#TEXT_COUNT} + 6 )):$(( 80 - (${#TEXT_COUNT}) ))}" 21 17)\n"
}

sub_step_header_string() {
  PADDING="================================================================================"
  OUTPUT_TEXT="$*"
  # Strip ANSI color codes for length calculation
  local TEXT_COUNT=$(echo -e "${OUTPUT_TEXT}" | sed $'s/\e\\[[0-9;]*m//g').
  COLORIZE_STRING BLUEPURPLE "${OUTPUT_TEXT} $(COLORIZE_PADDING "${PADDING:$(( ${#TEXT_COUNT} + 5 )):$(( 80 - (${#TEXT_COUNT}) ))}" 21 17)\n"
}

step_footer_string() {
  PADDING="================================================================================"
  local TEXT_COUNT=$(echo -e "${PADDING}" | sed $'s/\e\\[[0-9;]*m//g').
  COLORIZE_STRING NC "$(COLORIZE_PADDING "${PADDING:0:${#TEXT_COUNT}/2}" 17 21)$(COLORIZE_PADDING "${PADDING:$(( ${#TEXT_COUNT} /2 )):$(( 80 - (${#TEXT_COUNT} / 2) ))}" 21 17)"
}

action_string() {
  COLORIZE_STRING CYAN "$*"
}

info_string() {
  COLORIZE_STRING LIGHTBLUE "$*"
}

list_header() {
  COLORIZE_STRING LIGHTBLUE "$*:\n"
}

list_item() {
  COLORIZE_STRING LIGHTBLUE "   -- $*\n"
}

error_string() {
  COLORIZE_STRING LIGHTRED "$*"
}
warning_string() {
  COLORIZE_STRING YELLOW "$*"
}

run_cmd(){
  local COMMAND="$*"
  local OUTPUT
  OUTPUT=$(${COMMAND} 2>&1)
  local RC=$?
  if [ "$RC" -ne 0 ]; then
    error_string "Error executing command ${MAGENTA}${COMMAND}${NC}"
    error_string "$OUTPUT"
    exit "$RC"
  else
    return "$RC"
  fi
}

execute() {
  local TASK_STEP_OUTPUT="$1"
  shift 1
  local COMMAND="$*"
  action_string ${TASK_STEP_OUTPUT}
  run_cmd ${COMMAND}
}

check_vars() {
  var_names=("$@")
  for var_name in "${var_names[@]}"; do
    [ -z "${!var_name}" ] && error_string "${var_name} is not set." && var_unset=true
  done
  [ -n "$var_unset" ] && exit 1
  return 0
}

## Script Code Starts Here

VS_VERSION_ARG=$1
ARG_2=$2

if [[ -z "${VS_VERSION_ARG}" ]]; then
  INDENT=$(printf -- ' %.0s' {1..27})
  error_string "${RED}Argument required. Syntax: $(basename $0) [stable|unstable]\n${INDENT}$(basename $0) <VS-version> <state-metadata[stable|unstable]>${NC}"
  exit 1
fi

if [[ "${VS_VERSION_ARG}" == "stable" ]]; then
  IDENTIFIED_VS_VERSION=$(curl -s https://api.vintagestory.at/lateststable.txt)
  VS_VERSION_STATE="stable"
elif [[ "${VS_VERSION_ARG}" == "unstable" ]]; then
  IDENTIFIED_VS_VERSION=$(curl -s https://api.vintagestory.at/latestunstable.txt)
  VS_VERSION_STATE="unstable"
fi

if [[ "${ARG_2}" == "stable" ]]; then
  VS_VERSION_STATE="stable"
elif [[ "${ARG_2}" == "unstable" ]]; then
  VS_VERSION_STATE="unstable"
fi

if [ ! -z "${IDENTIFIED_VS_VERSION+x}" ] && [[ $IDENTIFIED_VS_VERSION =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(.*)$ ]]; then
  declare -A VS_VERSION_ARRAY=(
    [MAJOR]=${BASH_REMATCH[1]}
    [MINOR]=${BASH_REMATCH[2]}
    [BUILD]=${BASH_REMATCH[3]}
    [DEVHASH]=${BASH_REMATCH[4]}
  )
fi


PYTHON_VERSION="3.11.9"
PYTHON_SHORT_VERSION="$(echo "${PYTHON_VERSION}" | awk -F'.' '{ print $1"."$2 }')"

declare -A VS_STATE_DOTNET_VERSION=(
  [1.21]="8.0"
  [1.22]="10.0"
)

VS_VERSION="${VS_VERSION_ARRAY[MAJOR]}.${VS_VERSION_ARRAY[MINOR]}.${VS_VERSION_ARRAY[BUILD]}${VS_VERSION_ARRAY[DEVHASH]}"
DOTNET_VERSION=${VS_STATE_DOTNET_VERSION[${VS_VERSION_ARRAY[MAJOR]}.${VS_VERSION_ARRAY[MINOR]}]}

section_header_string "Container Build"
step_header_string "Environment Initialization"
# Installing GitHub CLI if not present (required for GitHub Release Creation)
sub_step_header_string "Install Github CLI"
if ! command -v gh &>/dev/null; then
  warning_string "GitHub CLI (${LAVENDER}gh${NC}) not found."
  action_string "Installing Github CLI via direct binary download"
  GH_INSTALL_DIR="${HOME}/bin"
  mkdir -p "${GH_INSTALL_DIR}"
  action_string "Fetching latest release information from GitHub API"
  GH_LATEST_VERSION=$(curl -fsSL "https://api.github.com/repos/cli/cli/releases/latest" | grep '"tag_name"' | sed -E 's/.*"v([^"]+)".*/\1/')
  GH_DOWNLOAD_URL="https://github.com/cli/cli/releases/download/v${GH_LATEST_VERSION}/gh_${GH_LATEST_VERSION}_windows_amd64.zip"
  GH_ZIP_PATH="${TEMP:-/tmp}/gh_${GH_LATEST_VERSION}_windows_amd64.zip"
  action_string "Downloading GitHub CLI ${LAVENDER}v${GH_LATEST_VERSION}${NC} from ${LAVENDER}${GH_DOWNLOAD_URL}${NC}"
  run_cmd curl -fsSL -o "${GH_ZIP_PATH}" "${GH_DOWNLOAD_URL}"
  run_cmd unzip -jo "${GH_ZIP_PATH}" "bin/gh.exe" -d "${GH_INSTALL_DIR}"
  rm -f "${GH_ZIP_PATH}"
  export PATH="${GH_INSTALL_DIR}:${PATH}"
  success_string "GitHub CLI (${LAVENDER}$(gh --version | head -1)${NC}) installed successfully to ${LAVENDER}${GH_INSTALL_DIR}${NC}."
else
  action_string "GitHub CLI (${LAVENDER}$(gh --version | head -1)${NC}) already installed."
fi
section_header_string "Docker Build"
step_header_string "Environment Initialization"
if [ ! "$MSYSTEM" = "MINGW64" ]; then
  export PYENV_ROOT="$HOME/.pyenv"
  [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init - bash)"
  eval "$(pyenv virtualenv-init -)"
fi
sub_step_header_string "Initializing Python Environment"
execute "Selecting Python ${LAVENDER}${PYTHON_VERSION}${NC}." pyenv local "${PYTHON_VERSION}"
execute "Installing System Dependencies: ${LAVENDER}pipenv & requests${NC}." "python${PYTHON_SHORT_VERSION} -m pip install pipenv requests"
execute "Installing Python Dependencies into Virtual Environment" "python -m pipenv install --python ${PYTHON_SHORT_VERSION} -r ./vintage_rcon_client/requirements.txt"

sub_step_header_string "Cleaning Git Tags for Semver"
execute "Purging Local Git Tags" "git tag -d $(git tag -l)"
execute "Pulling Git Tags" "git fetch origin --tags"
action_string "Pulled (${LAVENDER}$(git --no-pager tag | wc -l)${NC}) tags from Repository."

sub_step_header_string "Generating Semver Arguments"
SEMVER_ARGS="--name vintagestory --env-file --vs-version ${VS_VERSION}"

execute "Generating Version with arguments: ${LAVENDER}${SEMVER_ARGS}${NC}" python ./semver.py "${SEMVER_ARGS}"
action_string "Loading Build Environment Variables"
source build.env

declare TAG_MATRIX=(
  "${DOCKER_VERSION_NEW}-python3-trixie-slim"
  "${DOCKER_VERSION_NEW}"
  "${DOCKER_TAG}-python3-trixie-slim"
  "${DOCKER_TAG}"
  "${VS_VERSION}"
)

declare REPOSITORIES=(
  ghcr.io/darkmatterproductions/vintagestory
  ralnoc/vintagestory
)

step_header_string "Vintage Story Docker Image Build"
info_string "Image Version: ${LAVENDER}${VERSION}${NC} Vintage Story Version: ${LAVENDER}${VS_VERSION}${NC}"
info_string "State: ${LAVENDER}${VS_VERSION_STATE}${NC} .Net Version: ${LAVENDER}${DOTNET_VERSION}${NC}"
list_header "Docker Image Tags"
for tag in "${TAG_MATRIX[@]}"; do list_item "${LAVENDER}${tag}${NC}"; done

list_header "Target Repositories"
for repo in "${REPOSITORIES[@]}"; do list_item "${LAVENDER}${repo}${NC}"; done
execute "Building Container image: registry.dmpsys.in/vintagestory:${VS_VERSION}-${DOCKER_VERSION_NEW}" docker build --build-arg VERSION="${VERSION}" --build-arg VS_VERSION_STATE="${VS_VERSION_STATE}" --build-arg VS_VERSION="${VS_VERSION}" --build-arg DOTNET_VERSION="${DOTNET_VERSION}" -t registry.dmpsys.in/vintagestory:"${VS_VERSION}-${DOCKER_VERSION_NEW}" .
execute "Pushing Image to (${LAVENDER}registry.dmpsys.in/vintagestory${NC}) Registry" docker push registry.dmpsys.in/vintagestory:"${VS_VERSION}-${DOCKER_VERSION_NEW}"

step_header_string "Publishing Images"
execute "Logging into GHCR" bash -c "echo ${GHCR_TOKEN} | docker --context remote-engine login ghcr.io -u ${GHCR_USERNAME} --password-stdin"
for repo in "${REPOSITORIES[@]}"; do
  action_string "Processing Image for Repository: ${LAVENDER}${repo}${NC}"
  for tag in "${TAG_MATRIX[@]}";do
    action_string "Processing Image Tag: ${LAVENDER}${tag}${NC}"
    execute "  Tagging Image: ${LAVENDER}${repo}:${tag}${NC}" "docker --context remote-engine tag registry.dmpsys.in/vintagestory:${VS_VERSION}-${DOCKER_VERSION_NEW} ${repo}:${tag}"
    execute "  Pushing Image to Repository: ${LAVENDER}${repo}${NC}" "docker --context remote-engine push ${repo}:${tag}"
  done
  if [[ "${VS_VERSION_STATE}" == "stable" ]]; then
    action_string "Processing (${LAVENDER}${VS_VERSION_STATE}${NC}) Image Tag: ${LAVENDER}latest${NC}"
    execute "  Tagging Image: ${LAVENDER}${repo}:${tag}${NC}" "docker --context remote-engine tag ${repo}:${VS_VERSION}-${DOCKER_VERSION_NEW} ${repo}:latest"
    execute "  Pushing Image to Repository: ${LAVENDER}${repo}${NC}" "docker --context remote-engine push ${repo}:latest"
  fi
done

step_header_string "GitHub Release"
action_string "Creating GitHub Release for tag: ${LAVENDER}${DOCKER_TAG}${NC}"
RELEASE_NOTES="## Vintage Story Docker Image Release

**Vintage Story Version:** \`${VS_VERSION}\`
**Docker Image Version:** \`${DOCKER_TAG}\`
**Release State:** \`${VS_VERSION_STATE}\`

### Included Commits
$(git --no-pager log "${VERSION_OLD}"..HEAD --format="%x1f%h%x1e%B" | awk '
  BEGIN { RS="\x1f" }
  NR>1 {
    split($0, parts, "\x1e")
    hash = parts[1]
    n = split(parts[2], lines, "\n")
    for (i=1; i<=n; i++) {
      if (lines[i] != "") { print "- " lines[i] " (" hash ")"; break }
    }
  }
')

### Docker Image Tags
$(for tag in "${TAG_MATRIX[@]}"; do echo "- \`${tag}\`"; done)
$(if [[ "${VS_VERSION_STATE}" == "stable" ]]; then echo "- \`latest\`"; fi)

### Available Repositories
$(for repo in "${REPOSITORIES[@]}"; do echo "- \`${repo}\`"; done)"
cat > ./release-notes.md <<EOF
${RELEASE_NOTES}
EOF
echo "${RELEASE_NOTES}"
exit 1
action_string "Creating GitHub Release: ${LAVENDER}${DOCKER_TAG}${NC}"
GH_TOKEN="${GHCR_TOKEN}" gh release create "${DOCKER_TAG}" \
  --title "Vintage Story ${VS_VERSION} (Docker ${DOCKER_VERSION_NEW})" \
  -F ./release-notes.md \
  "$(if [[ "${VS_VERSION_STATE}" == "unstable" ]]; then echo "--prerelease"; fi)" > ./gh-release-publish.log 2>&1

step_header_string "Build Cleanup"
execute "Pruning unused images" docker image prune -f
execute "Removing ${LAVENDER}build.env${NC} File" rm build.env
execute "Removing ${LAVENDER}pipenv${NC} environment" python -m pipenv --rm
step_footer_string
section_footer_string


