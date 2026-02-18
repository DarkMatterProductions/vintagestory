![Official game logo for Vinstage Story as published by the developer Anego Studios](./images/vintage-story.png "Vintage Story Logo")

[![GitHub Release](https://img.shields.io/github/v/release/DarkmatterProductions/vintagestory?display_name=release&style=flat&label=Latest%20Stable%20Release&color=blue)](https://github.com/DarkMatterProductions/vintagestory/pkgs/container/vintagestory/?tag=latest)
[![GitHub contributors](https://img.shields.io/github/contributors/DarkmatterProductions/vintagestory?style=flat&label=Contributors&color=%234B86EB)](https://github.com/DarkMatterProductions/vintagestory/graphs/contributors)

![Vintage Story Stable Version](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fapi.vintagestory.at%2Flateststable.txt&search=(%5Cd%2B).(%5Cd%2B).(%5Cd%2B)(.*)&style=flat&label=Vintage%20Story%20Stable%20Version&color=%23029600)
![Vintage Story Unstable Version](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fapi.vintagestory.at%2Flatestunstable.txt&search=(%5Cd%2B).(%5Cd%2B).(%5Cd%2B)(.*)&style=flat&label=Vintage%20Story%20Unstable%20Version&color=FCF765)
![Vintage Story Preview Release Version](https://img.shields.io/badge/Vintage_Story_Preview_Release_Version-1.22.0--pre.2-E32424?style=flat)


[![Docker Stars](https://img.shields.io/docker/stars/ralnoc/vintagestory?style=flat&label=Docker%20Stars&color=purple)](https://hub.docker.com/r/ralnoc/vintagestory)
[![Docker Pulls](https://img.shields.io/docker/pulls/ralnoc/vintagestory?style=flat&label=Docker%20Pulls&color=%23621747)](https://hub.docker.com/r/ralnoc/vintagestory)

## Table of Contents
- [Docker Image References](#docker-image-references)
- [Support](#Support)
- [Quick Start](#quick-start)
- [Container Commands](#container-commands)
- [Environment Variables Reference](#environment-variables-reference)
   - [General Logging Configuration](#general-logging-configuration)
   - [Server Configuration Variables](#server-configuration-variables)
   - [Mod Management Variables](#mod-management-variables)
   - [RCON Server Configuration](#rcon-server-configuration)
   - [RCON Web Client Configuration](#rcon-web-client-configuration)
- [Configuration Options](#configuration-options)
- [Docker Compose Examples](#docker-compose-examples)
- [Building the Image](#building-the-image)

---


## About Vintage Story

Vintage Story is an uncompromising wilderness survival sandbox that takes everything you know from block-based games 
and adds authentic complexity. Progress through five metallurgical eras—from knapping flint tools to building steel 
production chains—using hands-on crafting systems where you actually chip stone, hammer metal on anvils, and sculpt 
clay voxel by voxel. The world generates with focus on realistic geology, implementing 22 rock types in proper strata,
climate-driven seasons that transform gameplay, and a unique temporal horror dimension: your stability meter drains 
underground, spawning increasingly dangerous Drifters as it drops, while periodic temporal storms force you into 
fortified bunkers. Late-game mechanical power systems let you automate grinding, pulverizing, and forging with 
windmill-driven factories.

Choose from six character classes each with unique traits, explore a procedurally generated world spanning 
climate zones from tundra to desert, and tackle an optional 8-chapter story featuring dungeons, NPCs, and boss 
encounters. The game supports both hardcore survivalists (permadeath, harsh winters, cave-ins) and peaceful builders 
(creative mode, reduced combat) through extensive world customization. Multiplayer includes land claiming, while a 
robust C# modding API allows the ability to extend the experience infinitely. Built for survival veterans seeking 
genuine depth beyond the Minecraft formula.

## Dedicated Server Docker Image
Vintage Story Dedicated Server Docker Image, built on Ubuntu 24.04 is based on the official Vintage Story server 
installation instructions, and extracted from server.sh for better Docker compatibility.

Official dedicated server guide: https://wiki.vintagestory.at/Guide:Dedicated_Server

## Docker Image References

### Container Registries
* **Docker Hub**: `ralnoc/vintagestory`
* **GitHub Container Registry**: `ghcr.io/darkmatterproductions/vintagestory`

---

## Support

For issues, questions, or contributions:
- **GitHub Issues**: [https://github.com/DarkMatterProductions/vintagestory/issues](https://github.com/DarkMatterProductions/vintagestory/issues)
- **Official Wiki**: [https://wiki.vintagestory.at/](https://wiki.vintagestory.at/)

---

## Quick Start

### Basic Server
**⚠️ Important Note:** This will use default settings and is not suitable for production use. 
Ensure you use environment variables or a custom configuration file for a production server.

Run a basic Vintage Story server with default settings:

```bash
docker run -d \
  --name vintagestory-server \
  -p 42420:42420/tcp \
  -p 42420:42420/udp \
  -v /path/to/your/vs/data:/vintagestory/data \
  --restart unless-stopped \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

### Server with Configuration
Run with custom server name and settings:

```bash
docker run -d \
  --name vintagestory-server \
  -p 42420:42420/tcp \
  -p 42420:42420/udp \
  -v /path/to/your/vs/data:/vintagestory/data \
  -e VS_CFG_SERVER_NAME="My Vintage Story Server" \
  -e VS_CFG_MAX_CLIENTS=20 \
  -e VS_CFG_SERVER_PASSWORD="secret123" \
  -e ENABLE_DEBUG_LOGGING=true \
  --restart unless-stopped \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

**Important**: Replace `/path/to/your/vs/data` with the actual path on your host machine where you want to persist server data. This ensures your world data, configurations, and mods are not lost when the container is removed or upgraded.

---

## Container Commands

### Running the Container

#### Basic Run
```bash
docker run -d \
  --name vintagestory-server \
  -p 42420:42420/tcp \
  -p 42420:42420/udp \
  -v /path/to/your/vs/data:/vintagestory/data \
  --restart unless-stopped \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

#### Run with RCON Web Client
```bash
docker run -d \
  --name vintagestory-server \
  -p 42420:42420/tcp \
  -p 42420:42420/udp \
  -p 5000:5000/tcp \
  -v /path/to/your/vs/data:/vintagestory/data \
  -e VS_RCON_ENABLED=true \
  --restart unless-stopped \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

#### Run with RCON Server
```bash
docker run -d \
  --name vintagestory-server \
  -p 42420:42420/tcp \
  -p 42420:42420/udp \
  -p 42425:42425/tcp \
  -v /path/to/your/vs/data:/vintagestory/data \
  -e VS_RCON_ENABLED=true \
  --restart unless-stopped \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

### Managing the Container

#### Start the Container
```bash
docker start vintagestory-server
```

#### Stop the Container
```bash
docker stop vintagestory-server
```

#### Restart the Container
```bash
docker restart vintagestory-server
```

#### Remove the Container
```bash
docker stop vintagestory-server
docker rm vintagestory-server
```

### Viewing Logs

#### View All Logs
```bash
docker logs vintagestory-server
```

#### Follow Logs in Real-Time
```bash
docker logs -f vintagestory-server
```

#### View Last 100 Lines
```bash
docker logs --tail 100 vintagestory-server
```

#### View Logs with Timestamps
```bash
docker logs -t vintagestory-server
```

#### View Container Statistics
```bash
docker stats vintagestory-server
```

#### Inspect Container Configuration
```bash
docker inspect vintagestory-server
```

---

## Environment Variables Reference

### General Logging Configuration

Control logging behavior for the Vintage Story server.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_DEBUG_LOGGING` | Boolean | `false` | Enables debug level logging for troubleshooting |
| `ENABLE_CHAT_LOGGING` | Boolean | `false` | Enables chat message logging to server logs |
| `FORCE_REGENERATE_CONFIG` | Boolean | `false` | Forces regeneration of serverconfig.json on startup |

**Example:**
```bash
docker run -d \
  -e ENABLE_DEBUG_LOGGING=true \
  -e ENABLE_CHAT_LOGGING=true \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

---

### Server Configuration Variables

These variables configure the Vintage Story game server and map to settings in `serverconfig.json`. All variables with the `VS_CFG_` prefix override corresponding server settings.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_CFG_SERVER_NAME` | String | _(from server-config.yaml)_ | The name of your server as displayed in the server list |
| `VS_CFG_SERVER_URL` | String | _(from server-config.yaml)_ | URL to your server's website or information page |
| `VS_CFG_SERVER_DESCRIPTION` | String | _(from server-config.yaml)_ | Server description shown in the server list |
| `VS_CFG_WELCOME_MESSAGE` | String | _(from server-config.yaml)_ | Message displayed to players when they join |
| `VS_CFG_ALLOW_CREATIVE_MODE` | Boolean | _(from server-config.yaml)_ | Whether creative mode is allowed (true/false/1/0/yes) |
| `VS_CFG_SERVER_IP` | String | _(from server-config.yaml)_ | IP address the server binds to (0.0.0.0 for all interfaces) |
| `VS_CFG_SERVER_PORT` | Integer | _(from server-config.yaml)_ | Port number the game server listens on (default: 42420) |
| `VS_CFG_SERVER_UPNP` | Boolean | _(from server-config.yaml)_ | Enable UPnP port forwarding (true/false/1/0/yes) |
| `VS_CFG_SERVER_COMPRESS_PACKETS` | Boolean | _(from server-config.yaml)_ | Enable packet compression to reduce bandwidth |
| `VS_CFG_ADVERTISE_SERVER` | Boolean | _(from server-config.yaml)_ | Advertise server in the public server list |
| `VS_CFG_MAX_CLIENTS` | Integer | _(from server-config.yaml)_ | Maximum number of concurrent players allowed |
| `VS_CFG_PASS_TIME_WHEN_EMPTY` | Boolean | _(from server-config.yaml)_ | Whether time passes when no players are online |
| `VS_CFG_SERVER_PASSWORD` | String | _(from server-config.yaml)_ | Password required to join the server (empty for no password) |
| `VS_CFG_MAX_CHUNK_RADIUS` | Integer | _(from server-config.yaml)_ | Maximum chunk view distance allowed for clients |
| `VS_CFG_SERVER_LANGUAGE` | String | _(from server-config.yaml)_ | Server language code (e.g., "en", "de", "fr") |
| `VS_CFG_ENFORCE_WHITELIST` | Integer | _(from server-config.yaml)_ | Whitelist enforcement mode (0=disabled, 1=enabled) |
| `VS_CFG_ANTIABUSE` | Integer | _(from server-config.yaml)_ | Anti-abuse protection level (0=disabled, 1=enabled) |
| `VS_CFG_ALLOW_PVP` | Boolean | _(from server-config.yaml)_ | Allow player-vs-player combat |
| `VS_CFG_HOSTED_MODE` | Boolean | _(from server-config.yaml)_ | Enable hosted mode restrictions |
| `VS_CFG_HOSTED_MODE_ALLOW_MODS` | Boolean | _(from server-config.yaml)_ | Allow mods in hosted mode |

**Example:**
```bash
docker run -d \
  -e VS_CFG_SERVER_NAME="My Awesome Server" \
  -e VS_CFG_SERVER_DESCRIPTION="A friendly survival server" \
  -e VS_CFG_MAX_CLIENTS=16 \
  -e VS_CFG_SERVER_PASSWORD="mypassword" \
  -e VS_CFG_ALLOW_PVP=false \
  -e VS_CFG_ADVERTISE_SERVER=true \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

**Note**: Values marked as "_(from server-config.yaml)_" come from the `server-config.yaml` file and are only overridden if the environment variable is explicitly set.

---

### Mod Management Variables

Control which mods are downloaded and installed on the server.

| Variable | Type | Default      | Description |
|----------|------|--------------|-------------|
| `VS_MODS` | String | `""` | Comma-separated list of mod download paths from mods.vintagestory.at<br>Format: `modid/filename.zip,modid2/filename2.zip` |
| `VS_RCON_ENABLED` | Boolean | `true` | Set to `true` to enable RCON functionality and download the RCON mod |
| `VS_RCON_MOD_VERSION` | String | `2.0.0` | Version of the VintageRCon mod to download when RCON is enabled |

**Example:**
```bash
docker run -d \
  -e VS_MODS="72291/vsvanillaplus_0.1.5.zip,75006/BetterRuinsv0.5.7.zip,73792/configlib_1.10.14.zip" \
  -e VS_RCON_ENABLED=true \
  -e VS_RCON_MOD_VERSION="2.0.0" \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

---

### RCON Server Configuration

Configure the RCON server connection settings. These control how the RCON web client connects to the Vintage Story server's RCON interface.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_SERVER_CFG_PORT` | Integer | `42425` | Port number the Vintage Story RCON server listens on |
| `VS_RCON_SERVER_CFG_IP` | String | `127.0.0.1` | IP address of the Vintage Story RCON server |
| `VS_RCON_SERVER_CFG_PASSWORD` | String | `changeme` | Password for authenticating to the RCON server<br>**⚠️ CHANGE IN PRODUCTION** |
| `VS_RCON_SERVER_CFG_TIMEOUT` | Integer | `20` | Connection timeout in seconds |
| `VS_RCON_SERVER_CFG_MAXCONNECTIONS` | Integer | `10` | Maximum number of concurrent RCON connections allowed |

**Example:**
```bash
docker run -d \
  -p 42425:42425/tcp \
  -e VS_RCON_ENABLED=true \
  -e VS_RCON_SERVER_CFG_PORT=42425 \
  -e VS_RCON_SERVER_CFG_PASSWORD="secure-rcon-password" \
  -e VS_RCON_SERVER_CFG_TIMEOUT=30 \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

---

### RCON Web Client Configuration

Configure the RCON web client application that provides a browser-based interface for server administration.  
_Note: Web Client leverages the Async mode for the python library [rcon](https://pypi.org/project/rcon/) to communicate
with the server's RCON interface, so the RCON server must be enabled and properly configured for the web client to function._

#### Server Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_CLIENT_CFG_SERVER_HOST` | String | `0.0.0.0` | Host address the web client listens on (0.0.0.0 for all interfaces) |
| `VS_RCON_CLIENT_CFG_SERVER_PORT` | Integer | `5000` | Port number the web client listens on |
| `VS_RCON_CLIENT_CFG_SERVER_SECRET_KEY` | String | `vintage-story-rcon-...` | Secret key for session encryption<br>**⚠️ CHANGE IN PRODUCTION** |

#### RCON Connection Settings

| Variable | Type | Default | Description                                                                                                              |
|----------|------|---------|--------------------------------------------------------------------------------------------------------------------------|
| `VS_RCON_CLIENT_CFG_RCON_DEFAULT_HOST` | String | `localhost` | Default RCON host to connect to                                                                                          |
| `VS_RCON_CLIENT_CFG_RCON_DEFAULT_PORT` | Integer | `42425` | Default RCON port to connect to                                                                                          |
| `VS_RCON_CLIENT_CFG_RCON_PASSWORD` | String | `changeme` | RCON password for authentication<br>**⚠️ CHANGE IN PRODUCTION**<br><i>Value must match `VS_RCON_SERVER_CFG_PASSWORD`</i> |
| `VS_RCON_CLIENT_CFG_RCON_LOCKED_ADDRESS` | Boolean | `false` | Lock RCON connection to default host/port (true/false)                                                                   |
| `VS_RCON_CLIENT_CFG_RCON_TIMEOUT` | Integer | `10` | RCON connection timeout in seconds                                                                                       |
| `VS_RCON_CLIENT_CFG_RCON_MAX_MESSAGE_SIZE` | Integer | `4096` | Maximum RCON message size in bytes                                                                                       |

#### Security Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_CLIENT_CFG_SECURITY_REQUIRE_AUTH` | Boolean | `true` | Require authentication to access the web client |
| `VS_RCON_CLIENT_CFG_SECURITY_TRADITIONAL_LOGIN_ENABLED` | Boolean | `true` | Enable traditional username/password login |
| `VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_USERNAME` | String | `admin` | Default username for traditional login<br>**⚠️ CHANGE IN PRODUCTION** |
| `VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_PASSWORD` | String | `changeme` | Default password for traditional login<br>**⚠️ CHANGE IN PRODUCTION** |
| `VS_RCON_CLIENT_CFG_SECURITY_MAX_LOGIN_ATTEMPTS` | Integer | `5` | Maximum login attempts before lockout |
| `VS_RCON_CLIENT_CFG_SECURITY_LOCKOUT_DURATION` | Integer | `300` | Account lockout duration in seconds after max attempts |

#### OAuth Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_ENABLED` | Boolean | `true` | Enable OAuth authentication providers |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_AUTHORIZED_EMAILS` | String | `admin@example.com,...` | Comma-separated list of authorized email addresses for OAuth login |

**⚠️ Important Note:** If you do not have access to a reverse proxy (such as NGINX or HAProxy) that can handle SSL/TLS
certificates and port mapping, you should **disable OAuth** and use traditional username/password authentication
instead. Most OAuth providers require HTTPS for security, which is not provided directly by the Docker container.

##### Provider Redirect URIs
All provider redirect URIs must be configured in the provider's app settings to point to your application. Below are
the URIs for each provider. Replace `yourdomain.com` with your actual domain.
_**IMPORTANT NOTE**: Be aware most providers require HTTPS for the URL._

###### URI Examples
- Google:   `https://yourdomain.com/login/oauth/google/authorize`
- Facebook: `https://yourdomain.com/login/oauth/facebook/authorize`
- GitHub:   `https://yourdomain.com/login/oauth/github/authorize`
- Apple:    `https://yourdomain.com/login/oauth/apple/authorize`

###### Provider Registration Links

| Provider | Registration URL |
|----------|-----------------|
| Google   | https://console.cloud.google.com/ |
| Facebook | https://developers.facebook.com/ |
| GitHub   | https://github.com/settings/developers |
| Apple    | https://developer.apple.com/account/ |

##### Google OAuth

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_ENABLED` | Boolean | `true` | Enable Google OAuth login |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_ID` | String | `your-google-client-id...` | Google OAuth client ID |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_SECRET` | String | `your-google-client-secret` | Google OAuth client secret |

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Choose "Web application" as the application type
6. Add authorized redirect URIs:
- `https://yourdomain.com/login/oauth/google/authorize`
7. Copy the Client ID and Client Secret

##### Facebook OAuth

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_ENABLED` | Boolean | `false` | Enable Facebook OAuth login |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_CLIENT_ID` | String | `your-facebook-app-id` | Facebook OAuth app ID |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_FACEBOOK_CLIENT_SECRET` | String | `your-facebook-app-secret` | Facebook OAuth app secret |

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or select an existing one
3. Add the "Facebook Login" product
4. In "Facebook Login" settings, add Valid OAuth Redirect URIs:
- `https://yourdomain.com/login/oauth/facebook/authorize` (for production)
5. Copy the App ID and App Secret from Settings > Basic

##### GitHub OAuth

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_ENABLED` | Boolean | `false` | Enable GitHub OAuth login |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_CLIENT_ID` | String | `your-github-client-id` | GitHub OAuth client ID |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GITHUB_CLIENT_SECRET` | String | `your-github-client-secret` | GitHub OAuth client secret |

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in the application details:
- Authorization callback URL: `https://yourdomain.com/login/oauth/github/authorize`
4. Copy the Client ID and generate a Client Secret

##### Apple OAuth

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_ENABLED` | Boolean | `false` | Enable Apple OAuth login |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_CLIENT_ID` | String | `your-apple-service-id` | Apple OAuth service ID |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_CLIENT_SECRET` | String | `your-apple-client-secret` | Apple OAuth client secret |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_TEAM_ID` | String | `your-apple-team-id` | Apple Developer Team ID |
| `VS_RCON_CLIENT_CFG_SECURITY_OAUTH_APPLE_KEY_ID` | String | `your-apple-key-id` | Apple OAuth key ID |

#### Logging Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VS_RCON_CLIENT_CFG_LOGGING_LOG_COMMANDS` | Boolean | `true` | Log RCON commands to file |
| `VS_RCON_CLIENT_CFG_LOGGING_LOG_FILE` | String | `logs/rcon.log` | Path to RCON client log file |
| `VS_RCON_CLIENT_CFG_LOGGING_LOG_LEVEL` | String | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

**Example (RCON with OAuth):**
```bash
docker run -d \
  -p 42420:42420/tcp \
  -p 42420:42420/udp \
  -p 42425:42425/tcp \
  -p 5000:5000/tcp \
  -v /path/to/your/vs/data:/vintagestory/data \
  -e VS_RCON_ENABLED=true \
  -e VS_RCON_SERVER_CFG_PASSWORD="my-secure-rcon-password" \
  -e VS_RCON_CLIENT_CFG_SERVER_SECRET_KEY="my-unique-secret-key-change-me" \
  -e VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_PASSWORD="web-admin-password" \
  -e VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_ENABLED=true \
  -e VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_ID="your-google-id.apps.googleusercontent.com" \
  -e VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_SECRET="your-google-secret" \
  -e VS_RCON_CLIENT_CFG_SECURITY_OAUTH_AUTHORIZED_EMAILS="admin@example.com,player@example.com" \
  --restart unless-stopped \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

---

## Configuration Options

There are four options for handling configuration of the Vintage Story server:

### 1. Default Configuration
Use the default configuration as defined within the Docker image.

**Not recommended for production use.**

### 2. Pre-created serverconfig.json
Pre-create the `serverconfig.json` configuration file in your mapped data directory. This file will be used by the server on the first run.

```bash
# Create your serverconfig.json in the data directory before starting
docker run -d \
  -v /path/to/your/vs/data:/vintagestory/data \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

### 3. Custom server-config.yaml
Create an updated `server-config.yaml` and mount it into the container at `/vintagestory/server-config.yaml`. This will cause the server to generate a `serverconfig.json` file based on the provided YAML configuration.

```bash
docker run -d \
  -v /path/to/your/vs/data:/vintagestory/data \
  -v /path/to/your/server-config.yaml:/vintagestory/server-config.yaml \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

### 4. Environment Variables
Use environment variables to override specific configuration options. See the [Environment Variables Reference](#environment-variables-reference) section above.

```bash
docker run -d \
  -v /path/to/your/vs/data:/vintagestory/data \
  -e VS_CFG_SERVER_NAME="My Server" \
  -e VS_CFG_MAX_CLIENTS=20 \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

**Priority Order**: Environment variables override values in `server-config.yaml`, which override default values.

---

## Docker Compose Examples

### Basic Server

```yaml
version: '3.8'

services:
  vintagestory-server:
    image: ghcr.io/darkmatterproductions/vintagestory:latest
    container_name: vintagestory-server
    ports:
      - "42420:42420/tcp"
      - "42420:42420/udp"
    volumes:
      - /path/to/your/vs/data:/vintagestory/data
    environment:
      - ENABLE_DEBUG_LOGGING=false
      - ENABLE_CHAT_LOGGING=true
      - VS_CFG_SERVER_NAME=My Vintage Story Server
      - VS_CFG_MAX_CLIENTS=16
    restart: unless-stopped
```

**Start the server:**
```bash
docker-compose up -d
```

### Server with RCON and OAuth

```yaml
version: '3.8'

services:
  vintagestory-server:
    image: ghcr.io/darkmatterproductions/vintagestory:latest
    container_name: vintagestory-server
    ports:
      - "42420:42420/tcp"
      - "42420:42420/udp"
      - "42425:42425/tcp"
      - "5000:5000/tcp"
    volumes:
      - /path/to/your/vs/data:/vintagestory/data
    environment:
      # Server Configuration
      - VS_CFG_SERVER_NAME=My Modded Server
      - VS_CFG_MAX_CLIENTS=20
      - VS_CFG_SERVER_PASSWORD=mypassword
      
      # RCON Mod
      - VS_RCON_ENABLED=true
      - VS_RCON_MOD_VERSION=2.0.0
      
      # RCON Server
      - VS_RCON_SERVER_CFG_PORT=42425
      - VS_RCON_SERVER_CFG_PASSWORD=rcon-password
      
      # RCON Web Client
      - VS_RCON_CLIENT_CFG_SERVER_PORT=5000
      - VS_RCON_CLIENT_CFG_SERVER_SECRET_KEY=my-secret-key-change-me
      - VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_PASSWORD=admin-password
      
      # OAuth
      - VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_ENABLED=true
      - VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
      - VS_RCON_CLIENT_CFG_SECURITY_OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
      - VS_RCON_CLIENT_CFG_SECURITY_OAUTH_AUTHORIZED_EMAILS=admin@example.com,user@example.com
      
      # Mods
      - VS_MODS=12345/mod1.zip,67890/mod2.zip
    restart: unless-stopped
```

### Docker Compose with Build

Build the image from source with specific version:

```yaml
version: '3.8'

services:
  vintagestory-server:
    build:
      context: .
      args:
        VS_VERSION: 1.21.6
        DOTNET_VERSION: 8.0
    image: vintagestory:1.21.6
    container_name: vintagestory-server
    ports:
      - "42420:42420/tcp"
      - "42420:42420/udp"
    volumes:
      - /path/to/your/vs/data:/vintagestory/data
    environment:
      - ENABLE_DEBUG_LOGGING=true
      - VS_CFG_SERVER_NAME=My Custom Build Server
    restart: unless-stopped
```

**Build and start:**
```bash
docker-compose up -d --build
```

---

## Building the Image

### Build with Specific Version

```bash
docker build \
  -t vintagestory:1.21.6 \
  --build-arg VS_VERSION=1.21.6 \
  --build-arg DOTNET_VERSION=8.0 \
  .
```

### Build with Environment Variables

```bash
export VS_VERSION=1.21.6
export DOTNET_VERSION=8.0

docker build \
  -t vintagestory:$VS_VERSION \
  --build-arg VS_VERSION=$VS_VERSION \
  --build-arg DOTNET_VERSION=$DOTNET_VERSION \
  .
```

### Build Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `VS_VERSION` | Version of Vintage Story to install | _(required)_ |
| `DOTNET_VERSION` | Version of .NET SDK to use | `8.0` |

---

## Notes

### Boolean Values
Boolean environment variables accept the following values (case-insensitive):
- **True**: `true`, `1`, `yes`, `on`
- **False**: `false`, `0`, `no`, `off`

### Security Best Practices
- **Always change default passwords** in production environments
- Change `VS_RCON_SERVER_CFG_PASSWORD`
- Change `VS_RCON_CLIENT_CFG_SERVER_SECRET_KEY`
- Change `VS_RCON_CLIENT_CFG_SECURITY_DEFAULT_PASSWORD`
- Use strong, unique passwords for each setting

### Data Persistence
Always mount the `/vintagestory/data` volume to a persistent location on your host. This ensures:
- World data is preserved across container updates
- Server configurations persist
- Mods are retained
- Player data is not lost

### Upgrading
When using `ghcr.io/darkmatterproductions/vintagestory:latest` or `ralnoc/vintagestory:latest`, the image always installs the latest version of Vintage Story. To upgrade:

```bash
# Stop and remove old container
docker stop vintagestory-server
docker rm vintagestory-server # Ensure you have your data backed up or mounted to a volume before removing the container

# Pull latest image
docker pull ghcr.io/darkmatterproductions/vintagestory:latest

# Start new container with same volumes
docker run -d \
  --name vintagestory-server \
  -p 42420:42420/tcp \
  -p 42420:42420/udp \
  -v /path/to/your/vs/data:/vintagestory/data \
  --restart unless-stopped \
  ghcr.io/darkmatterproductions/vintagestory:latest
```

Or with Docker Compose:
```bash
docker-compose pull
docker-compose up -d
```