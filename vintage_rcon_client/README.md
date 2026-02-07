# Vintage Story RCon Web Client

A Python 3.10-based web client for managing Vintage Story servers via the Source RCON protocol. Built with Flask, Socket.IO, HTML5, CSS3, and JavaScript.

## Features

- **Source RCON Protocol Support**: Fully compliant with the Valve Source RCON specification
- **Real-time Communication**: Uses WebSocket (Socket.IO) for real-time command execution and responses
- **Web-based Console**: Interactive console interface for executing server commands
- **Authentication**: Secure login system with configurable credentials
- **OAuth Support**: Login with Google, Facebook, GitHub, or Apple accounts (see OAUTH_SETUP.md)
- **Email Authorization**: Control access by configuring authorized email addresses
- **Locked Server Mode**: Option to lock the RCon server address for controlled access
- **Command History**: Navigate through previous commands using arrow keys
- **Responsive Design**: Modern, responsive UI that works on desktop and mobile devices
- **Command Logging**: Optional logging of all executed commands
- **Session Management**: Secure session handling with automatic timeout

## Requirements

- Python 3.10 or higher
- pip (Python package manager)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Create a configuration file:
```bash
cp config.template.yaml config.yaml
```

3. Edit `config.yaml` with your settings:
   - Update the `secret_key` for session security
   - Configure default RCon server settings
   - Set authentication credentials (change default username/password!)
   - Enable/disable address locking
   - (Optional) Configure OAuth providers - see [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed instructions

## Configuration

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
  -p 42420:42420/tcp \
  -p 42420:42420/udp \
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

## Usage

### Starting the Server

Run the application:
```bash
python app.py
```

Or use the startup script:
```bash
python -m vintage_rcon_client.app
```

The web interface will be available at `http://localhost:5000` (or the configured host/port).

### Web Interface

1. **Login**: Enter your credentials (default: admin/changeme)
2. **Connect**: Enter RCon server details and password
3. **Execute Commands**: Use the console to execute server commands

### Command History

- Use **Up Arrow** to navigate to previous commands
- Use **Down Arrow** to navigate to next commands

## Security Considerations

1. **Change Default Credentials**: Always change the default username and password in production
2. **Use Strong Secret Key**: Generate a strong random secret key for session management
3. **Enable HTTPS**: Use a reverse proxy (nginx, Apache) with SSL/TLS for production
4. **Firewall**: Restrict access to the web interface using firewall rules
5. **Locked Address Mode**: Enable `locked_address` to prevent users from connecting to arbitrary RCon servers

## Locked Address Mode

When `locked_address` is set to `true` in the configuration:
- Users cannot modify the RCon server host and port
- The connection is restricted to the default server specified in the config
- This is useful for dedicated server management where admins should only access a specific server

## Compatibility

This client is designed to work with the Vintage RCon mod which implements the Source RCON protocol. It should also work with any server that supports the standard Source RCON protocol.

### Tested With
- Vintage Story with VintageRCon mod

## File Structure

```
vintage_rcon_client/
├── app.py                      # Main Flask application
├── rcon_client.py              # Source RCON protocol implementation
├── config.template.yaml        # Configuration template
├── config.yaml                 # Your configuration (create from template)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/
│   └── index.html             # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css          # Application styles
│   └── js/
│       └── app.js             # Client-side JavaScript
└── logs/
    └── rcon.log               # Command log (auto-created)
```

## Troubleshooting

### Connection Issues

- Verify the RCon server is running and accessible
- Check firewall rules allow connections to the RCon port
- Verify the RCon password is correct
- Check the RCon mod is properly installed on the server

### Authentication Issues

- Verify credentials match those in `config.yaml`
- Check for IP lockouts (wait for lockout duration to expire)
- Clear browser cookies/session storage

### Command Execution Issues

- Some commands may not produce output
- Check the server logs for error messages
- Verify you have permission to execute the command

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python app.py
```

### Testing

Connect to a local Vintage Story server with VintageRCon mod installed.

## License

See LICENSE file for details.

## Acknowledgments

- Based on the rcon-web-admin project structure
- Implements the Valve Source RCON protocol specification
- Built for the Vintage Story community

