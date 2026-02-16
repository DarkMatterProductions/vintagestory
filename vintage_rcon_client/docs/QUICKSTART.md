# Vintage Story RCon Web Client - Quick Start Guide

This guide will help you get the RCon Web Client up and running quickly.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- A Vintage Story server with the VintageRCon mod installed

## Step-by-Step Installation

### 1. Verify Python Installation

Open a terminal/command prompt and run:

```bash
python --version
```

You should see Python 3.10.x or higher.

### 2. Navigate to the Client Directory

```bash
cd vintage_rcon_client
```

### 3. Install Dependencies

**Option A: Direct installation**
```bash
pip install -r requirements.txt
```

**Option B: Using a virtual environment (recommended)**

Windows:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Verify Installation

Run the test script:
```bash
python test_install.py
```

You should see all tests pass.

### 5. Configure the Client

Edit `config.yaml`:

```yaml
server:
  host: '0.0.0.0'      # Bind to all interfaces
  port: 5000           # Web interface port
  secret_key: 'your-secret-key-here'  # CHANGE THIS!

rcon:
  default_host: 'localhost'  # Your server address
  default_port: 42425        # RCon port
  locked_address: false      # Set to true to lock address

security:
  require_auth: true
  default_username: 'admin'
  default_password: 'changeme'  # CHANGE THIS!
```

**Important**: Change the `secret_key` and `default_password`!

### 6. Start the Server

**Windows:**
```bash
python app.py
```

Or use the startup script:
```bash
start.bat
```

**Linux/Mac:**
```bash
python app.py
```

Or use the startup script:
```bash
chmod +x start.sh
./start.sh
```

### 7. Access the Web Interface

Open your web browser and navigate to:
```
http://localhost:5000
```

### 8. Login

Use the credentials from your `config.yaml`:
- Username: `admin` (or what you configured)
- Password: `changeme` (or what you configured)

### 9. Connect to RCon Server

1. Enter your server details:
   - Host: `localhost` (or your server IP)
   - Port: `42425` (or your RCon port)
   - Password: Your RCon password from VintageRCon config

2. Click "Connect"

### 10. Execute Commands

Once connected, you can execute server commands in the console:
- Type a command (e.g., `/help`)
- Press Enter or click "Send"
- View the response in the console

## Common Issues

### Port Already in Use

If port 5000 is already in use, change it in `config.yaml`:
```yaml
server:
  port: 5001  # Or any other available port
```

### Cannot Connect to RCon

1. Verify VintageRCon mod is installed on the server
2. Check the RCon port in your server's VintageRCon config
3. Ensure the firewall allows connections to the RCon port
4. Verify the RCon password is correct

### Authentication Failed

1. Check username/password in `config.yaml`
2. Clear browser cookies/cache
3. Wait 5 minutes if locked out due to failed attempts

## Security Checklist

- [ ] Changed `secret_key` in config.yaml
- [ ] Changed `default_password` in config.yaml
- [ ] Set strong RCon password on server
- [ ] Configured firewall rules
- [ ] Using HTTPS (in production)
- [ ] Restricted access to web interface

## Next Steps

- Read the full [README.md](README.md) for detailed information
- Check [DOCUMENTATION.md](DOCUMENTATION.md) for technical details
- Configure advanced settings in `config.yaml`
- Set up SSL/TLS for production use

## Quick Reference

### Useful Commands

Start server:
```bash
python app.py
```

Test installation:
```bash
python test_install.py
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Default Ports

- Web Interface: 5000
- RCon Server: 42425

### Configuration File

Location: `config.yaml`

### Log Files

Location: `logs/rcon.log`

## Support

For issues or questions:
1. Check the troubleshooting section in README.md
2. Review DOCUMENTATION.md for technical details
3. Check VintageRCon mod documentation
4. Verify server logs

## Production Deployment

For production use:

1. **Use a reverse proxy** (nginx, Apache) with SSL/TLS
2. **Change all default credentials**
3. **Set `locked_address: true`** if managing a single server
4. **Configure firewall rules** to restrict access
5. **Enable command logging** for audit trail
6. **Regular backups** of configuration and logs
7. **Monitor server resources**

Example nginx configuration:

```nginx
server {
    listen 443 ssl;
    server_name rcon.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## License

See LICENSE file for details.

