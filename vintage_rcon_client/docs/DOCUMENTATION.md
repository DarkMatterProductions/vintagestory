# Vintage Story RCon Web Client - Technical Documentation

## Overview

This RCon Web Client is a Python 3.10-based web application designed to provide a modern, user-friendly interface for managing Vintage Story servers through the Source RCON protocol. It seamlessly integrates with the VintageRCon mod.

## Architecture

### Backend (Python/Flask)

- **Flask**: Web framework providing HTTP server and routing
- **Flask-SocketIO**: WebSocket support for real-time bidirectional communication
- **eventlet**: Async I/O for handling concurrent connections
- **PyYAML**: Configuration file parsing

### Frontend

- **HTML5**: Semantic markup for the user interface
- **CSS3**: Modern styling with CSS variables, flexbox, and grid layouts
- **JavaScript (ES6+)**: Client-side application logic
- **Socket.IO Client**: WebSocket client for real-time communication

## Source RCON Protocol Implementation

The client implements the Valve Source RCON protocol as specified in the [Valve Developer Wiki](https://developer.valvesoftware.com/wiki/Source_RCON_Protocol).

### Packet Structure

```
Size (4 bytes, little-endian int)
ID (4 bytes, little-endian int)
Type (4 bytes, little-endian int)
Body (variable length, null-terminated string)
Empty String (1 byte, 0x00)
Padding (1 byte, 0x00)
```

### Packet Types

- `SERVERDATA_AUTH (3)`: Authentication request
- `SERVERDATA_AUTH_RESPONSE (2)`: Authentication response
- `SERVERDATA_EXECCOMMAND (2)`: Execute a command
- `SERVERDATA_RESPONSE_VALUE (0)`: Response from server

### Connection Flow

1. **Connect**: Establish TCP socket connection to RCon server
2. **Authenticate**: Send SERVERDATA_AUTH packet with password
3. **Receive Auth Response**: Check for success (ID matches) or failure (ID = -1)
4. **Execute Commands**: Send SERVERDATA_EXECCOMMAND packets
5. **Receive Responses**: Collect SERVERDATA_RESPONSE_VALUE packets until end marker
6. **Disconnect**: Close socket connection

## Features Implemented

### Core Features (from rcon-web-admin)

1. **Web-based Console Interface**
   - Real-time command execution
   - Immediate response display
   - Command history navigation

2. **Authentication System**
   - Secure login with username/password
   - Session management
   - Login attempt limiting
   - IP-based lockout protection

3. **Server Connection Management**
   - Connect/disconnect functionality
   - Connection status monitoring
   - Configurable timeouts

4. **Configuration System**
   - YAML-based configuration
   - Hot-reloadable settings
   - Template configuration for easy setup

5. **Logging**
   - Command execution logging
   - User activity tracking
   - Configurable log levels

### Additional Features

1. **Locked Address Mode**
   - Restrict connections to a specific server
   - Prevent unauthorized server access
   - Useful for dedicated hosting environments

2. **Responsive Design**
   - Mobile-friendly interface
   - Adaptive layout
   - Touch-friendly controls

3. **Real-time Communication**
   - WebSocket-based communication
   - No page refreshes needed
   - Instant feedback

## Integration with VintageRCon Mod

The client is specifically designed to work with the VintageRCon mod for Vintage Story:

### Compatibility

- **Protocol**: Source RCON (fully compliant)
- **Default Port**: 42425 (VintageRCon default)
- **Authentication**: Password-based (as per VintageRCon config)
- **Commands**: All server commands supported by Vintage Story

### Configuration Alignment

The client's default settings align with VintageRCon defaults:

```yaml
rcon:
  default_host: 'localhost'
  default_port: 42425  # Matches VintageRCon default
  timeout: 10
```

### VintageRCon Configuration

To use this client with VintageRCon, ensure your VintageRCon config has:

```json
{
    "Port": 42425,
    "IP": null,
    "Password": "your-secure-password",
    "Timeout": 20,
    "MaxConnections": 10
}
```

## Security Features

### Authentication

- Username/password authentication
- Session-based authorization
- Configurable authentication requirement

### Rate Limiting

- Maximum login attempts tracking
- IP-based lockout system
- Configurable lockout duration

### Session Management

- Secure session cookies
- Configurable secret key
- Automatic session cleanup

### Address Locking

When `locked_address: true`:
- Users cannot change server address
- Connections restricted to configured server
- Prevents arbitrary server access

## API Reference

### WebSocket Events

#### Client → Server

- `login`: Authenticate user
  ```json
  { "username": "admin", "password": "password" }
  ```

- `logout`: End user session

- `rcon_connect`: Connect to RCon server
  ```json
  { "host": "localhost", "port": 42425, "password": "rcon-password" }
  ```

- `rcon_disconnect`: Disconnect from RCon server

- `rcon_command`: Execute RCon command
  ```json
  { "command": "/help" }
  ```

- `rcon_status`: Request connection status

#### Server → Client

- `login_response`: Login result
  ```json
  { "success": true, "message": "Login successful", "username": "admin" }
  ```

- `logout_response`: Logout confirmation
  ```json
  { "success": true, "message": "Logged out successfully" }
  ```

- `rcon_response`: RCon connection result
  ```json
  { "success": true, "message": "Connected", "host": "localhost", "port": 42425 }
  ```

- `command_response`: Command execution result
  ```json
  { "success": true, "message": "Command output", "command": "/help", "timestamp": "2026-02-07T12:00:00" }
  ```

- `status_response`: Connection status
  ```json
  { "connected": true, "host": "localhost", "port": 42425 }
  ```

## Configuration Reference

### Server Configuration

```yaml
server:
  host: '0.0.0.0'           # Bind address
  port: 5000                # Web interface port
  secret_key: 'key'         # Session encryption key
```

### RCon Configuration

```yaml
rcon:
  default_host: 'localhost' # Default RCon server
  default_port: 42425       # Default RCon port
  locked_address: false     # Lock to default address
  timeout: 10               # Connection timeout (seconds)
  max_message_size: 4096    # Max packet size (bytes)
```

### Security Configuration

```yaml
security:
  require_auth: true              # Enable authentication
  default_username: 'admin'       # Default user
  default_password: 'changeme'    # Default password
  max_login_attempts: 5           # Max failed attempts
  lockout_duration: 300           # Lockout time (seconds)
```

### Logging Configuration

```yaml
logging:
  log_commands: true         # Log all commands
  log_file: 'logs/rcon.log' # Log file path
  log_level: 'INFO'          # Python logging level
```

## Usage Examples

### Basic Usage

1. Start the client: `python app.py`
2. Open browser: `http://localhost:5000`
3. Login with credentials
4. Connect to RCon server
5. Execute commands

### Locked Address Mode

Set in `config.yaml`:
```yaml
rcon:
  default_host: 'your-server.com'
  default_port: 42425
  locked_address: true
```

Users will only be able to connect to `your-server.com:42425`.

### Without Authentication

Set in `config.yaml`:
```yaml
security:
  require_auth: false
```

Users can access console without login (not recommended for production).

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to RCon server

**Solutions**:
- Verify VintageRCon mod is installed and configured
- Check firewall allows connections to RCon port
- Verify RCon password matches
- Check server IP/port are correct

### Authentication Issues

**Problem**: Cannot login to web client

**Solutions**:
- Verify credentials in `config.yaml`
- Check for IP lockout (wait or restart client)
- Clear browser cookies/cache

### Command Not Responding

**Problem**: Commands don't produce output

**Solutions**:
- Some commands may not generate output
- Check VintageRCon mod logs
- Verify command syntax is correct
- Try a simple command like `/help`

## Development

### File Structure

```
vintage_rcon_client/
├── app.py                  # Main Flask application
├── rcon_client.py         # RCON protocol implementation
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # HTML template
├── static/
│   ├── css/
│   │   └── style.css    # Styles
│   └── js/
│       └── app.js       # Client-side code
└── logs/
    └── rcon.log         # Command logs
```

### Adding Features

1. **Backend**: Add SocketIO event handlers in `app.py`
2. **Frontend**: Add event handlers in `static/js/app.js`
3. **Styling**: Update `static/css/style.css`

### Testing

```bash
# Test RCon connection
python -c "from rcon_client import RConClient; c = RConClient('localhost', 42425, 'password'); print(c.connect()); print(c.authenticate())"

# Test web server
python app.py
# Open http://localhost:5000 in browser
```

## Differences from rcon-web-admin

### Simplified Feature Set

This client focuses on core console functionality, omitting:
- Widget system
- Multi-server management
- Multi-user management
- Advanced automation features

### Technology Stack

- **Python** instead of Node.js
- **Flask** instead of Express
- **Socket.IO** for WebSockets (similar)
- **YAML** instead of JavaScript for config

### Vintage Story Specific

- Defaults aligned with VintageRCon
- Locked address mode for dedicated hosting
- Simplified for Vintage Story use case

## Future Enhancements

Potential features for future versions:
- Multi-server support
- User management system
- Command scheduling
- Server statistics dashboard
- Player management tools
- Backup management
- Plugin system

## License

See LICENSE file for details.

