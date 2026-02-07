#!/usr/bin/env bash
set -e

HOMEPATH=${HOMEPATH:-/vintagestory}
VSPATH=${VSPATH:-/vintagestory/server}
DATAPATH=${DATAPATH:-/vintagestory/data}
USERNAME=${USERNAME:-vintagestory}
SERVICE=${SERVICE}
OPTIONS=$*
UID_NUMBER=${UID_NUMBER:-1100}
GID_NUMBER=${GID_NUMBER:-1100}
ENABLE_DEBUG_LOGGING=${ENABLE_DEBUG_LOGGING:-"false"}
ENABLE_CHAT_LOGGING=${ENABLE_CHAT_LOGGING:-"false"}
VS_MODS=${VS_MODS:-""} # Comma-separated list of mod urls
VS_RCON_MOD_VERSION=${VS_RCON_MOD_VERSION:-"2.0.0"}
FORCE_REGENERATE_CONFIG=${FORCE_REGENERATE_CONFIG:-"false"}

echo "=========================================="
echo "Starting Vintagestory Server..."
echo "=========================================="
echo "Vintagestory Server path: $VSPATH"
echo "Vintagestory Data path: $DATAPATH"
echo "Debug logging: $ENABLE_DEBUG_LOGGING"
echo "Chat logging: $ENABLE_CHAT_LOGGING"
echo "Running initial setup as: $(whoami)"
echo "Service User: $USERNAME (${UID_NUMBER}:${GID_NUMBER})"
echo "Options: $OPTIONS"
echo "Service: $SERVICE"
echo ""
echo "Environment Variables (VS_ prefixed):"
echo "----------------------------------------"
echo "Mod Management:"
echo "  VS_MODS: ${VS_MODS:-<not set>}"
echo "  VS_RCON_ENABLED: ${VS_RCON_ENABLED:-<not set>}"
echo "  VS_RCON_MOD_VERSION: ${VS_RCON_MOD_VERSION}"
echo ""
echo "Server Configuration (VS_CFG_*):"
echo "  VS_CFG_SERVER_NAME: ${VS_CFG_SERVER_NAME:-<not set>}"
echo "  VS_CFG_SERVER_URL: ${VS_CFG_SERVER_URL:-<not set>}"
echo "  VS_CFG_SERVER_DESCRIPTION: ${VS_CFG_SERVER_DESCRIPTION:-<not set>}"
echo "  VS_CFG_WELCOME_MESSAGE: ${VS_CFG_WELCOME_MESSAGE:-<not set>}"
echo "  VS_CFG_ALLOW_CREATIVE_MODE: ${VS_CFG_ALLOW_CREATIVE_MODE:-<not set>}"
echo "  VS_CFG_SERVER_IP: ${VS_CFG_SERVER_IP:-<not set>}"
echo "  VS_CFG_SERVER_PORT: ${VS_CFG_SERVER_PORT:-<not set>}"
echo "  VS_CFG_SERVER_UPNP: ${VS_CFG_SERVER_UPNP:-<not set>}"
echo "  VS_CFG_SERVER_COMPRESS_PACKETS: ${VS_CFG_SERVER_COMPRESS_PACKETS:-<not set>}"
echo "  VS_CFG_ADVERTISE_SERVER: ${VS_CFG_ADVERTISE_SERVER:-<not set>}"
echo "  VS_CFG_MAX_CLIENTS: ${VS_CFG_MAX_CLIENTS:-<not set>}"
echo "  VS_CFG_PASS_TIME_WHEN_EMPTY: ${VS_CFG_PASS_TIME_WHEN_EMPTY:-<not set>}"
echo "  VS_CFG_SERVER_PASSWORD: ${VS_CFG_SERVER_PASSWORD:+***set***}"
echo "  VS_CFG_MAX_CHUNK_RADIUS: ${VS_CFG_MAX_CHUNK_RADIUS:-<not set>}"
echo "  VS_CFG_SERVER_LANGUAGE: ${VS_CFG_SERVER_LANGUAGE:-<not set>}"
echo "  VS_CFG_ENFORCE_WHITELIST: ${VS_CFG_ENFORCE_WHITELIST:-<not set>}"
echo "  VS_CFG_ANTIABUSE: ${VS_CFG_ANTIABUSE:-<not set>}"
echo "  VS_CFG_ALLOW_PVP: ${VS_CFG_ALLOW_PVP:-<not set>}"
echo "  VS_CFG_HOSTED_MODE: ${VS_CFG_HOSTED_MODE:-<not set>}"
echo "  VS_CFG_HOSTED_MODE_ALLOW_MODS: ${VS_CFG_HOSTED_MODE_ALLOW_MODS:-<not set>}"
echo ""
echo "RCON Server Configuration (VS_RCON_SERVER_CFG_*):"
echo "  VS_RCON_SERVER_CFG_PORT: ${VS_RCON_SERVER_CFG_PORT:-<not set>}"
echo "  VS_RCON_SERVER_CFG_IP: ${VS_RCON_SERVER_CFG_IP:-<not set>}"
echo "  VS_RCON_SERVER_CFG_PASSWORD: ${VS_RCON_SERVER_CFG_PASSWORD:+***set***}"
echo "  VS_RCON_SERVER_CFG_TIMEOUT: ${VS_RCON_SERVER_CFG_TIMEOUT:-<not set>}"
echo "  VS_RCON_SERVER_CFG_MAXCONNECTIONS: ${VS_RCON_SERVER_CFG_MAXCONNECTIONS:-<not set>}"
echo ""
echo "RCON Client Configuration (VS_RCON_CLIENT_CFG_*):"
echo "  VS_RCON_CLIENT_CFG_SERVER_HOST: ${VS_RCON_CLIENT_CFG_SERVER_HOST:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SERVER_PORT: ${VS_RCON_CLIENT_CFG_SERVER_PORT:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SERVER_SECRET_KEY: ${VS_RCON_CLIENT_CFG_SERVER_SECRET_KEY:+***set***}"
echo "  VS_RCON_CLIENT_CFG_RCON_DEFAULT_HOST: ${VS_RCON_CLIENT_CFG_RCON_DEFAULT_HOST:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_RCON_DEFAULT_PORT: ${VS_RCON_CLIENT_CFG_RCON_DEFAULT_PORT:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_RCON_PASSWORD: ${VS_RCON_CLIENT_CFG_RCON_PASSWORD:+***set***}"
echo "  VS_RCON_CLIENT_CFG_RCON_LOCKED_ADDRESS: ${VS_RCON_CLIENT_CFG_RCON_LOCKED_ADDRESS:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_RCON_TIMEOUT: ${VS_RCON_CLIENT_CFG_RCON_TIMEOUT:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_RCON_MAX_MESSAGE_SIZE: ${VS_RCON_CLIENT_CFG_RCON_MAX_MESSAGE_SIZE:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_REQUIRE_AUTH: ${VS_RCON_CLIENT_CFG_SECURITY_REQUIRE_AUTH:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_TRADITIONAL_LOGIN_ENABLED: ${VS_RCON_CLIENT_CFG_SECURITY_TRADITIONAL_LOGIN_ENABLED:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_USERNAME: ${VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_USERNAME:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_PASSWORD: ${VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_PASSWORD:+***set***}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_MAX_LOGIN_ATTEMPTS: ${VS_RCON_CLIENT_CFG_SECURITY_MAX_LOGIN_ATTEMPTS:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_LOCKOUT_DURATION: ${VS_RCON_CLIENT_CFG_SECURITY_LOCKOUT_DURATION:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_ENABLED: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_ENABLED:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_AUTHORIZED_EMAILS: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_AUTHORIZED_EMAILS:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_ENABLED: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_ENABLED:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_ID: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_ID:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_SECRET: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_SECRET:+***set***}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_ENABLED: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_ENABLED:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_CLIENT_ID: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_CLIENT_ID:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_CLIENT_SECRET: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_CLIENT_SECRET:+***set***}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_ENABLED: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_ENABLED:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_CLIENT_ID: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_CLIENT_ID:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_CLIENT_SECRET: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_CLIENT_SECRET:+***set***}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_ENABLED: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_ENABLED:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_CLIENT_ID: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_CLIENT_ID:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_CLIENT_SECRET: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_CLIENT_SECRET:+***set***}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_TEAM_ID: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_TEAM_ID:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_KEY_ID: ${VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_KEY_ID:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_LOGGING_LOG_COMMANDS: ${VS_RCON_CLIENT_CFG_LOGGING_LOG_COMMANDS:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_LOGGING_LOG_FILE: ${VS_RCON_CLIENT_CFG_LOGGING_LOG_FILE:-<not set>}"
echo "  VS_RCON_CLIENT_CFG_LOGGING_LOG_LEVEL: ${VS_RCON_CLIENT_CFG_LOGGING_LOG_LEVEL:-<not set>}"

echo "=========================================="

# Ensure data directory structure exists and has proper ownership
echo "Setting up data directory..."
mkdir -p "${DATAPATH}/Logs" "${DATAPATH}/Saves" "${DATAPATH}/Backups" "${DATAPATH}/Playerdata" "${DATAPATH}/Mods"

# Generate serverconfig.json from environment variables if it doesn't exist
# or if FORCE_REGENERATE_CONFIG is set
if [ ! -f "${DATAPATH}/serverconfig.json" ] || [ "${FORCE_REGENERATE_CONFIG}" == "true" ]; then
  echo "Generating serverconfig.json from environment variables..."
  python3 "${HOMEPATH}/generate-config.py" "${DATAPATH}/serverconfig.json"
  if [ $? -ne 0 ]; then
    echo "ERROR: Failed to generate serverconfig.json"
    exit 1
  fi
else
  echo "Using existing serverconfig.json"
fi

if [[ "${VS_RCON_ENABLED}" == true ]]; then
  rcon_mod_url="https://mods.vintagestory.at/download/67715/VintageRCon-${VS_RCON_MOD_VERSION}.zip"
  echo "Downloading mod_url: $rcon_mod_url"
  if [[ -f "${DATAPATH}/Mods/$(basename ${rcon_mod_url})" ]]; then
    echo "Mod already exists: ${DATAPATH}/Mods/$(basename ${rcon_mod_url}), skipping download."
  else
    curl -sL "${rcon_mod_url}" -o "${DATAPATH}/Mods/$(basename ${rcon_mod_url})"
    mkdir -p /vintagestory/data/ModConfig
  fi
  python /vintage_rcon_client/generate_vsrcon_config.py -f /vintagestory/data/ModConfig/vsrcon.json
else
  echo "RCON mod not enabled, skipping download."
fi

for mod_url_path in ${VS_MODS//,/ }; do
  mod_url="https://mods.vintagestory.at/download/${mod_url_path}"
  echo "Downloading mod_url: https://mods.vintagestory.at/download/$mod_url"
  if [[ -f "${DATAPATH}/Mods/$(basename ${mod_url})" ]]; then
    echo "Mod already exists: ${DATAPATH}/Mods/$(basename ${mod_url}), skipping download."
    continue
  fi
  curl -sL "${mod_url}" -o "${DATAPATH}/Mods/$(basename ${mod_url})"
done

# Ensure proper ownership of everything under the data directory
echo "Setting ownership of data directory..."
chown -R "${UID_NUMBER}":"${GID_NUMBER}" "${DATAPATH}" 2>/dev/null || true

# Change to server directory
echo "Changing to server directory: $VSPATH"
cd $VSPATH || sh -c "echo \"ERROR: Failed to change directory to $VSPATH\" && exit 1"

# Drop privileges and run the server as the non-root user
echo "=========================================="
echo "Executing server as user: $USERNAME"
echo "Starting server: dotnet ${SERVICE} --dataPath ${DATAPATH} ${OPTIONS}"
echo "=========================================="

exec gosu ${UID_NUMBER}:${GID_NUMBER} dotnet "${SERVICE}" --dataPath "${DATAPATH}" ${OPTIONS} &

# Tail logs
echo "Initializing log monitoring..."
# Create log files if they don't exist
touch ${DATAPATH}/Logs/server-audit.log
touch ${DATAPATH}/Logs/server-crash.log
touch ${DATAPATH}/Logs/server-main.log
touch ${DATAPATH}/Logs/server-worldgen.log
touch ${DATAPATH}/Logs/server-build.log
touch ${DATAPATH}/Logs/server-debug.log
touch ${DATAPATH}/Logs/server-chat.log
chown ${UID_NUMBER}:${GID_NUMBER} ${DATAPATH}/Logs/*.log

# Always-on logs
echo "Tailing main log files..."
exec tail -f ${DATAPATH}/Logs/server-audit.log &
exec tail -f ${DATAPATH}/Logs/server-crash.log &
exec tail -f ${DATAPATH}/Logs/server-main.log &
exec tail -f ${DATAPATH}/Logs/server-worldgen.log &

# Conditional logs
if [[ "$ENABLE_DEBUG_LOGGING" == "true" ]]; then
  echo "Enabling debug logging..."
  exec tail -f ${DATAPATH}/Logs/server-build.log &
  exec tail -f ${DATAPATH}/Logs/server-debug.log &
fi

if [[ "$ENABLE_CHAT_LOGGING" == "true" ]]; then
  echo "Enabling chat logging..."
  exec tail -f ${DATAPATH}/Logs/server-chat.log &
fi

if [[ "${VS_RCON_ENABLED}" == true ]]; then
  echo "RCON mod enabled, starting RCON web client..."
  screen -dms rcon_web_client bash -c 'cd /vintage_rcon_client && python app.py 2>&1 | tee /var/log/vintage_rcon_client.log '
else
  echo "RCON mod not enabled, skipping RCON web client startup."
fi

wait -n