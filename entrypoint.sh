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
echo "=========================================="

# Ensure data directory structure exists and has proper ownership
echo "Setting up data directory..."
mkdir -p "${DATAPATH}/Logs" "${DATAPATH}/Saves" "${DATAPATH}/Backups" "${DATAPATH}/Playerdata"

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
wait -n