# Vintage Story Server Docker Image for Debian 13 (Trixie)
# Based on the official Vintage Story server installation instructions, and extracted from server.sh
# for better Docker compatibility.
# Official guide: https://wiki.vintagestory.at/Guide:Dedicated_Server#Dedicated_server_on_Linux
FROM python:3.10-slim-trixie

EXPOSE 42420

# Variables from the server.sh
ARG USERNAME=vintagestory
ARG HOMEPATH=/vintagestory
ARG VSPATH=${HOMEPATH}/server
ARG DATAPATH=${HOMEPATH}/data
ENV SERVICE="${VSPATH}/VintagestoryServer.dll"
ENV USERNAME=${USERNAME}
ENV HOMEPATH=${HOMEPATH}
ENV VSPATH=${VSPATH}
ENV DATAPATH=${DATAPATH}

ARG VS_VERSION=1.21.6
ARG DOTNET_VERSION=8.0
ENV VS_VERSION=${VS_VERSION}
ENV DOTNET_VERSION=${DOTNET_VERSION}

LABEL org.opencontainers.image.source=https://github.com/DarkMatterProductions/vintagestory
LABEL org.opencontainers.image.description="Vintage Story Dedicated Server on Ubuntu 24.04"
LABEL org.opencontainers.image.licenses=MIT
LABEL in.dmpsys.maintainer="DarkMatter Productions"
LABEL in.dmpsys.project="Vintage Story Dedicated Server"
LABEL in.dmpsys.website="https://github.com/DarkMatterProductions/vintagestory"
LABEL in.dmpsys.vsversion="${VS_VERSION}"


# Server configuration defaults (can be overridden with -e flags at runtime)
ENV SERVER_NAME="Vintage Story Server"
ENV SERVER_DESCRIPTION=""
ENV SERVER_URL=""
ENV WELCOME_MESSAGE="Welcome {0}, may you survive well and prosper"
ENV SERVER_IP=""
ENV SERVER_PORT=42420
ENV SERVER_PASSWORD=""
ENV SERVER_UPNP=false
ENV SERVER_COMPRESS_PACKETS=true
ENV ADVERTISE_SERVER=false
ENV MAX_CLIENTS=16
ENV PASS_TIME_WHEN_EMPTY=false
ENV MAX_CHUNK_RADIUS=12
ENV SERVER_LANGUAGE="en"
ENV DEFAULT_ROLE_CODE="suplayer"
ENV ONLY_WHITELISTED=false
ENV ANTI_ABUSE="Off"
ENV ALLOW_PVP=true
ENV ALLOW_FIRE_SPREAD=true
ENV ALLOW_FALLING_BLOCKS=true

# Startup commands (e.g., "/op username" or "/op player1; /op player2")
ENV ADMIN_USERNAME=""
ENV STARTUP_COMMANDS=""

# World configuration defaults
ENV WORLD_SEED=""
ENV WORLD_NAME="Vintage Story World"
ENV SAVE_FILE_LOCATION="${DATAPATH}/Saves/default.vcdbs"
ENV ALLOW_CREATIVE_MODE=true
ENV PLAY_STYLE="surviveandbuild"
ENV WORLDCONFIG_TEMPORAL_STORMS="sometimes"
ENV WORLDCONFIG_TEMPORAL_RIFTS="visible"
ENV WORLDCONFIG_WORLD_CLIMATE="realistic"
ENV WORLDCONFIG_GAME_MODE="survival"
ENV WORLDCONFIG_DEATH_PUNISHMENT="drop"
ENV WORLDCONFIG_CREATURE_HOSTILITY="aggressive"
ENV WORLDCONFIG_PLAYER_HEALTH="15"
ENV WORLDCONFIG_HUNGER_SPEED="1"
ENV WORLDCONFIG_MOVE_SPEED="1.5"
ENV WORLDCONFIG_FOOD_SPOIL="1"
ENV WORLDCONFIG_SAPLING_GROWTH="1"
ENV WORLDCONFIG_TOOL_DURABILITY="1"
ENV WORLDCONFIG_ALLOW_COORDINATES=true
ENV WORLDCONFIG_ALLOW_MAP=true

# Install dependencies
RUN apt update && \
    apt install -yf wget curl vim gosu

# Install PyYAML
RUN pip3 install --break-system-packages pyyaml

# Install Mono
RUN apt install -y ca-certificates gnupg && \
    gpg --homedir /tmp --no-default-keyring --keyring gnupg-ring:/usr/share/keyrings/mono-official-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF && \
    chmod +r /usr/share/keyrings/mono-official-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/mono-official-archive-keyring.gpg] https://download.mono-project.com/repo/ubuntu stable-focal main" | tee /etc/apt/sources.list.d/mono-official-stable.list && \
    apt update && \
    apt install -y mono-complete

# Install required .Net runtime
RUN wget https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt update && \
    apt install -y aspnetcore-runtime-${DOTNET_VERSION}

# Add user
ENV UID_NUMBER=1100
ENV GID_NUMBER=1100
RUN groupadd -g ${GID_NUMBER} ${USERNAME}
RUN useradd -u ${UID_NUMBER} -g ${GID_NUMBER} -d ${HOMEPATH} -ms /bin/bash ${USERNAME}

WORKDIR ${HOMEPATH}

# Install Vintage Story server
RUN wget -P ${VSPATH} https://cdn.vintagestory.at/gamefiles/stable/vs_server_linux-x64_${VS_VERSION}.tar.gz && \
    tar -C ${VSPATH} -xvzf ${VSPATH}/vs_server_linux-x64_${VS_VERSION}.tar.gz && \
    rm ${VSPATH}/vs_server_linux-x64_${VS_VERSION}.tar.gz && \
    chown -R ${USERNAME}: ${HOMEPATH}

# Copy entrypoint and config generator
COPY entrypoint.sh ${HOMEPATH}/entrypoint.sh
COPY generate-config.py ${HOMEPATH}/generate-config.py
COPY server-config.yaml ${HOMEPATH}/server-config.yaml
# Set permissions, change ownership
RUN chmod 755 ${HOMEPATH}/entrypoint.sh && \
    chown ${USERNAME}: ${HOMEPATH}/*

ENTRYPOINT ["./entrypoint.sh"]
