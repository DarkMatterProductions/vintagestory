# Vintage Story RCon Web Client

A modern Python 3.10-based web client for managing Vintage Story servers via the Source RCON protocol.

## 📚 Documentation Index

Start here based on what you need:

### 🚀 Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Fast installation and setup guide
  - Prerequisites
  - Step-by-step installation
  - First-time configuration
  - Common issues

### 📖 Detailed Documentation
- **[README.md](README.md)** - Complete feature documentation
  - Full feature list
  - Detailed configuration options
  - Usage examples
  - Security considerations
  - Troubleshooting

### 🔧 Technical Details
- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Technical documentation
  - Architecture overview
  - RCON protocol implementation
  - API reference
  - Integration with VintageRCon mod
  - Development guide

### 📋 Project Information
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project overview
  - What was built
  - Technology stack
  - Component breakdown
  - Design decisions

## 🎯 Quick Links

### Installation
```bash
pip install -r requirements.txt
python test_install.py
```

### Configuration
Edit `config.yaml` - change these:
- `secret_key` (for session security)
- `default_password` (admin password)

### Running
```bash
python app.py
```
Then open: http://localhost:5000

### Testing
```bash
python test_install.py
```

## 📂 Project Structure

```
vintage_rcon_client/
├── 📄 Core Files
│   ├── app.py                 - Main Flask application
│   ├── rcon_client.py        - RCON protocol implementation
│   └── config.yaml           - Configuration file
│
├── 📚 Documentation
│   ├── QUICKSTART.md         - Quick start guide
│   ├── README.md             - Main documentation
│   ├── DOCUMENTATION.md      - Technical docs
│   └── PROJECT_SUMMARY.md    - Project overview
│
├── 🌐 Web Interface
│   ├── templates/
│   │   └── index.html        - HTML template
│   └── static/
│       ├── css/style.css     - Styles
│       └── js/app.js         - JavaScript
│
└── 🛠️ Tools
    ├── test_install.py       - Installation test
    ├── start.bat             - Windows startup
    └── start.sh              - Linux/Mac startup
```

## ✨ Key Features

- ✅ Web-based console interface
- ✅ Real-time command execution via WebSocket
- ✅ Source RCON protocol support
- ✅ Secure authentication system
- ✅ Command history navigation
- ✅ Configurable server address locking
- ✅ Command logging
- ✅ Responsive mobile-friendly design
- ✅ Session management
- ✅ Rate limiting and lockout protection

## 🔐 Security

**Important**: Before deploying to production:
1. Change `secret_key` in config.yaml
2. Change `default_password` in config.yaml
3. Use HTTPS (reverse proxy with SSL/TLS)
4. Configure firewall rules
5. Review security settings in config.yaml

## 🎮 Compatible With

- Vintage Story servers
- VintageRCon mod
- Any server supporting Source RCON protocol

## 📦 Requirements

- Python 3.10 or higher
- pip (Python package manager)
- Flask and dependencies (see requirements.txt)

## 🆘 Support

1. Check [QUICKSTART.md](QUICKSTART.md) for common issues
2. Review [README.md](README.md) troubleshooting section
3. Check [DOCUMENTATION.md](DOCUMENTATION.md) for technical details
4. Verify VintageRCon mod configuration

## 📄 License

See LICENSE file for details.

## 🙏 Acknowledgments

- Based on rcon-web-admin project structure
- Implements Valve Source RCON protocol specification
- Built for the Vintage Story community

---

**Ready to start?** → [QUICKSTART.md](QUICKSTART.md)

**Need help?** → [README.md](README.md)

**Technical details?** → [DOCUMENTATION.md](DOCUMENTATION.md)

