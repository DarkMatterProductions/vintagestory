# Changelog

All notable changes to the Vintage Story RCON Web Client will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## \[0.0.30\] - 2026-02-17

### Added
- Initial release of Vintage Story RCON Web Client
- FastAPI-based web server
- Socket.IO real-time communication
- OAuth authentication support (Google, Facebook, GitHub, Apple)
- Traditional username/password authentication
- RCON connection management
- Command execution interface
- Session-based authentication
- JWT token support
- Configurable security settings
- Command logging functionality
- HTML response sanitization
- Responsive web interface

### Security
- Password hashing with bcrypt
- JWT-based authentication tokens
- OAuth 2.0 integration
- Session management with rate limiting
- CSRF protection via OAuth state parameter
- Email-based authorization whitelist

---

## Version History Format

**Before making your first release, please update the dates and version numbers above.**

### Semantic Versioning Guide
- **MAJOR** version: Incompatible API changes
- **MINOR** version: Backwards-compatible functionality additions
- **PATCH** version: Backwards-compatible bug fixes

### Change Categories
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements or vulnerability patches

[Unreleased]: https://github.com/DarkMatterProductions/vintagestory/compare/0.0.30...HEAD
[0.0.30]: https://github.com/DarkMatterProductions/vintagestory/releases/tag/0.0.30
