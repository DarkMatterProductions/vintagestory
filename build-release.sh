#!/usr/bin/env bash

# Color Code information from: https://misc.flogisoft.com/bash/tip_colors_and_formatting
RED='\e[38;5;124m'
LIGHTRED='\e[38;5;1m'
GREEN='\e[38;5;34m'
LIGHTGREEN='\e[38;5;82m'
BROWN='\e[38;5;94m'
LIGHTBROWN='\e[38;5;137m'
YELLOW='\e[38;5;226m'
LIGHTYELLOW='\e[38;5;228m'
BLUE='\e[38;5;20m'
LIGHTBLUE='\e[38;5;27m'
CYAN='\e[38;5;74m'
LIGHTCYAN='\e[38;5;87m'
LAVENDER='\e[38;5;171m'
PURPLE='\e[38;5;54m'
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
  COLORIZE_STRING CYAN "$(COLORIZE_PADDING "${PADDING:0:6}" 17 21) ${OUTPUT_TEXT} $(COLORIZE_PADDING "${PADDING:$(( ${#TEXT_COUNT} )):$(( 80 - (${#TEXT_COUNT}) ))}" 21 17)\n"
}

step_footer_string() {
  PADDING="================================================================================"
  local TEXT_COUNT=$(echo -e "${PADDING}" | sed $'s/\e\\[[0-9;]*m//g').
  COLORIZE_STRING NC "$(COLORIZE_PADDING "${PADDING:0:${#TEXT_COUNT}/2}" 17 21)$(COLORIZE_PADDING "${PADDING:$(( ${#TEXT_COUNT} /2 )):$(( 80 - (${#TEXT_COUNT} / 2) ))}" 21 17)"
}

action_string() {
  COLORIZE_STRING LIGHTBLUE "$*"
}

error_string() {
  COLORIZE_STRING LIGHTRED "$*"
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

ARG_1=$1
ARG_2=$2
RAW_VS_VERSION=$ARG_1

if [[ "${ARG_1}" == "stable" ]]; then
  RAW_VS_VERSION=$(curl -s https://api.vintagestory.at/lateststable.txt)
  VS_VERSION_STATE="stable"
elif [[ "${ARG_1}" == "unstable" ]]; then
  RAW_VS_VERSION=$(curl -s https://api.vintagestory.at/latestunstable.txt)
  VS_VERSION_STATE="unstable"
fi

if [[ "${ARG_2}" == "stable" ]]; then
  VS_VERSION_STATE="stable"
elif [[ "${ARG_2}" == "unstable" ]]; then
  VS_VERSION_STATE="unstable"
fi

if [ ! -z "${RAW_VS_VERSION+x}" ] && [[ $RAW_VS_VERSION =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(.*)$ ]]; then
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
  [1.21.6]="8.0"
  [1.22.0]="10.0"
)

VS_VERSION="${VS_VERSION_ARRAY[MAJOR]}.${VS_VERSION_ARRAY[MINOR]}.${VS_VERSION_ARRAY[BUILD]}${VS_VERSION_ARRAY[DEVHASH]}"
DOTNET_VERSION=${VS_STATE_DOTNET_VERSION[${VS_VERSION_ARRAY[MAJOR]}.${VS_VERSION_ARRAY[MINOR]}.${VS_VERSION_ARRAY[BUILD]}]}

section_header_string "Docker Build"
step_header_string "Initializing Build Environment"
if [ ! "$MSYSTEM" = "MINGW64" ]; then
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
eval "$(pyenv virtualenv-init -)"
fi

execute "Selecting Python ${LAVENDER}${PYTHON_VERSION}${NC}." pyenv local "${PYTHON_VERSION}"
execute "Installing System Dependencies: ${LAVENDER}pipenv & requests${NC}." "python${PYTHON_SHORT_VERSION} -m pip install pipenv requests"
execute "Installing Python Dependencies into Virtual Environment." "python -m pipenv install --python ${PYTHON_SHORT_VERSION} -r ./vintage_rcon_client/requirements.txt"
execute "Purging Local Git Tags." "git tag -d $(git tag -l)"
execute "Pulling Git Tags." "git fetch origin --tags"
action_string "Pulled (${LAVENDER}$(git --no-pager tag | wc -l)${NC}) tags from Repository."
action_string "Generating Semver Arguments."
SEMVER_ARGS="--name vintagestory --env-file --vs-version ${VS_VERSION}"

execute "Generating Version with arguments: ${LAVENDER}${SEMVER_ARGS}${NC}" python ./semver.py "${SEMVER_ARGS}"
action_string "Loading Build Environment Variables"
source build.env

step_header_string "Vintage Story Docker Image Build"
action_string "Image Version: ${LAVENDER}${VERSION}${NC} State: ${LAVENDER}${VS_VERSION_STATE}${NC} Version: ${LAVENDER}${VS_VERSION}${NC}"
action_string ".Net Version: ${LAVENDER}${DOTNET_VERSION}${NC} Dev Image Tag: ${LAVENDER}registry.dmpsys.in/vintagestory:${VS_VERSION}-${DOCKER_VERSION_NEW}"
echo execute "Building Docker image" docker build --build-arg VS_VERSION_STATE="${VS_VERSION_STATE}" --build-arg VS_VERSION="${VS_VERSION}" --build-arg DOTNET_VERSION="${DOTNET_VERSION}" -t registry.dmpsys.in/vintagestory:"${VS_VERSION}-${DOCKER_VERSION_NEW}" .
echo execute "Pushing (${LAVENDER}registry.dmpsys.in/vintagestory:${VS_VERSION}-${DOCKER_VERSION_NEW}${NC}) to Registry" docker push registry.dmpsys.in/vintagestory:"${VS_VERSION}-${DOCKER_VERSION_NEW}"
step_header_string "Publishing Images"
action_string "Publishing Tag Matrix"
declare REPOSITORIES=(
  ralnoc/vintagestory
  ghcr.io/darkmatterproductions/vintagestory
)
declare TAG_MATRIX=(
  ${VS_VERSION}-${DOCKER_VERSION_NEW}-python3-trixie-slim
  ${VS_VERSION}-${DOCKER_VERSION_NEW}
  ${DOCKER_VERSION_NEW}-python3-trixie-slim
  ${DOCKER_VERSION_NEW}
  ${VS_VERSION}
  ${VS_VERSION_STATE}
  latest
)
execute "Logging into GHCR" "echo ${GHCR_TOKEN} | docker login ghcr.io -u ghcr_user --password-stdin"
execute "Logging into Docker Hub" "echo ${DOCKERHUB_TOKEN} | docker login -u ${DOCKERHUB_USERNAME} --password-stdin"

for tag in "${TAG_MATRIX[@]}";do
  action_string "Processing Image Tag: ${LAVENDER}${tag}${NC}"
  for repo in "${REPOSITORIES[@]}"; do
    execute "Tagging Image" docker tag registry.dmpsys.in/vintagestory:"${VS_VERSION}-${DOCKER_VERSION_NEW}" "${repo}:${tag}"
    execute "Pushing Image" docker push "${repo}:${tag}"
  done
done

step_header_string "Build Cleanup"
execute "Pruning unused images" docker image prune -f
execute "Removing ${LAVENDER}build.env${NC} File" rm build.env
execute "Removing ${LAVENDER}pipenv${NC} environment" python -m pipenv --rm
step_footer_string
section_footer_string


