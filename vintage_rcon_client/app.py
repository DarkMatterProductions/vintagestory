"""
Vintage Story RCon Web Client
Async Application with FastAPI and python-socketio
JWT-based authentication for unified session management
"""
import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
import socketio
import hashlib
import traceback
from pathlib import Path
from rcon.source import rcon
import re
from authlib.integrations.starlette_client import OAuth
import uvicorn
from jose import JWTError, jwt
from passlib.context import CryptContext

# Initialize SocketIO server with asyncio support
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)

# Initialize FastAPI app
app = FastAPI(title="Vintage Story RCon Web Client")

# Mount static files
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

# Initialize OAuth
oauth = OAuth()

# Setup templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Create combined ASGI application
socket_app = socketio.ASGIApp(sio, app)


# Global configuration
config: Dict[str, Any] = {}
login_attempts: Dict[str, int] = {}
lockouts: Dict[str, datetime] = {}
_middleware_added: bool = False  # Track if SessionMiddleware has been added

# JWT Configuration
JWT_SECRET_KEY: str = ""  # Will be set from config
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    global config, JWT_SECRET_KEY, _middleware_added

    config_path = Path(__file__).parent / 'config.yaml'

    if not config_path.exists():
        logger.warning(f"{config_path} not found, using default configuration")
        with open(config_path, 'w') as f:
            # Default configuration with environment variable overrides
            # Each config item can be overridden with VS_RCON_CLIENT_CFG_* environment variables
            # Example: VS_RCON_CLIENT_CFG_SERVER_HOST=0.0.0.0
            import os

            def env_override(key_path, default_value):
                """Get config value from environment variable or use default"""
                env_key = f"VS_RCON_CLIENT_CFG_{key_path.upper()}"
                env_value = os.environ.get(env_key)
                if env_value is not None:
                    # Convert string to appropriate type
                    if isinstance(default_value, bool):
                        return env_value.lower() in ('true', '1', 'yes', 'on')
                    elif isinstance(default_value, int):
                        return int(env_value)
                    elif isinstance(default_value, list):
                        return [item.strip() for item in env_value.split(',')]
                    return env_value
                return default_value

            config = {
                "server": {
                    "host": env_override("server_host", "0.0.0.0"),
                    "port": env_override("server_port", 5000),
                    "secret_key": env_override("server_secret_key", "vintage-story-rcon-client-secret-key-change-me")
                },
                "rcon": {
                    "default_host": env_override("rcon_default_host", "localhost"),
                    "default_port": env_override("rcon_default_port", 42425),
                    "password": env_override("rcon_password", "changeme"),
                    "locked_address": env_override("rcon_locked_address", False),
                    "timeout": env_override("rcon_timeout", 10),
                    "max_message_size": env_override("rcon_max_message_size", 4096)
                },
                "security": {
                    "require_auth": env_override("security_require_auth", True),
                    "traditional_login_enabled": env_override("security_traditional_login_enabled", True),
                    "default_username": env_override("security_default_username", "admin"),
                    "default_password": env_override("security_default_password", "changeme"),
                    "max_login_attempts": env_override("security_max_login_attempts", 5),
                    "lockout_duration": env_override("security_lockout_duration", 300),
                    "oauth": {
                        "enabled": env_override("security_oauth_enabled", True),
                        "authorized_emails": env_override("security_oauth_authorized_emails", [
                            "admin@example.com",
                            "user@example.com"
                        ]),
                        "google": {
                            "enabled": env_override("security_oauth_google_enabled", True),
                            "client_id": env_override("security_oauth_google_client_id", "your-google-client-id.apps.googleusercontent.com"),
                            "client_secret": env_override("security_oauth_google_client_secret", "your-google-client-secret")
                        },
                        "facebook": {
                            "enabled": env_override("security_oauth_facebook_enabled", False),
                            "client_id": env_override("security_oauth_facebook_client_id", "your-facebook-app-id"),
                            "client_secret": env_override("security_oauth_facebook_client_secret", "your-facebook-app-secret")
                        },
                        "github": {
                            "enabled": env_override("security_oauth_github_enabled", False),
                            "client_id": env_override("security_oauth_github_client_id", "your-github-client-id"),
                            "client_secret": env_override("security_oauth_github_client_secret", "your-github-client-secret")
                        },
                        "apple": {
                            "enabled": env_override("security_oauth_apple_enabled", False),
                            "client_id": env_override("security_oauth_apple_client_id", "your-apple-service-id"),
                            "client_secret": env_override("security_oauth_apple_client_secret", "your-apple-client-secret"),
                            "team_id": env_override("security_oauth_apple_team_id", "your-apple-team-id"),
                            "key_id": env_override("security_oauth_apple_key_id", "your-apple-key-id")
                        }
                    }
                },
                "logging": {
                    "log_commands": env_override("logging_log_commands", True),
                    "log_file": env_override("logging_log_file", "logs/rcon.log"),
                    "log_level": env_override("logging_log_level", "INFO")
                }
            }

            yaml.dump(config, f)
            logger.info(f"Default configuration created at {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Setup JWT secret key
        JWT_SECRET_KEY = config.get('server', {}).get('secret_key', 'change-this-secret-key')

        # Add SessionMiddleware for OAuth flow (required by authlib)
        # Note: We use JWT for user authentication, but OAuth needs sessions for the redirect flow
        # Only add middleware once to avoid RuntimeError when load_config is called multiple times
        if not _middleware_added:
            secret_key = config.get('server', {}).get('secret_key', 'change-this-secret-key')
            app.add_middleware(SessionMiddleware, secret_key=secret_key)
            _middleware_added = True

        # Setup logging
        log_level = config.get('logging', {}).get('log_level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level))

        # Create logs directory if needed
        log_file = config.get('logging', {}).get('log_file')
        if log_file:
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Configuration loaded successfully")


        # Initialize OAuth providers if enabled
        if config.get('security', {}).get('oauth', {}).get('enabled', False):
            initialize_oauth_providers()

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def initialize_oauth_providers():
    """Initialize OAuth providers based on configuration"""
    oauth_config = config.get('security', {}).get('oauth', {})

    # Google OAuth
    if oauth_config.get('google', {}).get('enabled', False):
        google_config = oauth_config['google']
        oauth.register(
            name='google',
            client_id=google_config.get('client_id'),
            client_secret=google_config.get('client_secret'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        logger.info("Google OAuth provider registered")

    # Facebook OAuth
    if oauth_config.get('facebook', {}).get('enabled', False):
        facebook_config = oauth_config['facebook']
        oauth.register(
            name='facebook',
            client_id=facebook_config.get('client_id'),
            client_secret=facebook_config.get('client_secret'),
            access_token_url='https://graph.facebook.com/oauth/access_token',
            access_token_params=None,
            authorize_url='https://www.facebook.com/dialog/oauth',
            authorize_params=None,
            api_base_url='https://graph.facebook.com/',
            client_kwargs={'scope': 'email'}
        )
        logger.info("Facebook OAuth provider registered")

    # GitHub OAuth
    if oauth_config.get('github', {}).get('enabled', False):
        github_config = oauth_config['github']
        oauth.register(
            name='github',
            client_id=github_config.get('client_id'),
            client_secret=github_config.get('client_secret'),
            access_token_url='https://github.com/login/oauth/access_token',
            access_token_params=None,
            authorize_url='https://github.com/login/oauth/authorize',
            authorize_params=None,
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'}
        )
        logger.info("GitHub OAuth provider registered")

    # Apple OAuth
    if oauth_config.get('apple', {}).get('enabled', False):
        apple_config = oauth_config['apple']
        oauth.register(
            name='apple',
            client_id=apple_config.get('client_id'),
            client_secret=apple_config.get('client_secret'),
            server_metadata_url='https://appleid.apple.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'email name'
            }
        )
        logger.info("Apple OAuth provider registered")


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def is_email_authorized(email: str) -> bool:
    """Check if an email is authorized to log in via OAuth"""
    oauth_config = config.get('security', {}).get('oauth', {})
    authorized_emails = oauth_config.get('authorized_emails', [])

    # If no authorized emails are configured, allow all
    if not authorized_emails:
        return True

    # Check if email is in authorized list
    return email.lower() in [e.lower() for e in authorized_emails]


def check_lockout(ip_address: str) -> bool:
    """Check if an IP address is locked out"""
    if ip_address in lockouts:
        if datetime.now() < lockouts[ip_address]:
            return True
        else:
            # Lockout expired
            del lockouts[ip_address]
            if ip_address in login_attempts:
                del login_attempts[ip_address]
    return False


def record_login_attempt(ip_address: str, success: bool):
    """Record a login attempt"""
    if success:
        if ip_address in login_attempts:
            del login_attempts[ip_address]
        if ip_address in lockouts:
            del lockouts[ip_address]
    else:
        login_attempts[ip_address] = login_attempts.get(ip_address, 0) + 1
        max_attempts = config.get('security', {}).get('max_login_attempts', 5)

        if login_attempts[ip_address] >= max_attempts:
            lockout_duration = config.get('security', {}).get('lockout_duration', 300)
            lockouts[ip_address] = datetime.now() + timedelta(seconds=lockout_duration)
            logger.warning(f"IP {ip_address} locked out due to too many failed login attempts")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.debug(f"Token verification failed: {e}")
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token (for HTTP routes)"""
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        return None

    return {
        'username': payload.get('sub'),
        'display_name': payload.get('name'),
        'oauth_provider': payload.get('provider'),
        'authenticated': True
    }


def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract JWT token from cookie"""
    return request.cookies.get('access_token')


def get_token_from_socketio_environ(environ) -> Optional[str]:
    """Extract JWT token from Socket.IO connection environ"""
    try:
        # Try to get from query parameters (Socket.IO client can pass it here)
        query_string = environ.get('QUERY_STRING', '')
        if 'token=' in query_string:
            for param in query_string.split('&'):
                if param.startswith('token='):
                    return param.split('=', 1)[1]

        # Try to get from cookies
        http_headers = None
        if 'asgi.scope' in environ:
            http_headers = environ['asgi.scope'].get('headers', [])
        elif 'headers' in environ:
            http_headers = environ['headers']

        if http_headers:
            for header_name, header_value in http_headers:
                header_name_str = header_name.decode('utf-8') if isinstance(header_name, bytes) else header_name
                if header_name_str.lower() == 'cookie':
                    cookie_header = header_value.decode('utf-8') if isinstance(header_value, bytes) else header_value
                    # Simple parse for access_token
                    for cookie in cookie_header.split(';'):
                        cookie = cookie.strip()
                        if cookie.startswith('access_token='):
                            return cookie.split('=', 1)[1]

        return None
    except Exception as e:
        logger.debug(f"Error extracting token from environ: {e}")
        return None


def sanitize_html_response(text: str) -> str:
    """
    Remove anchor tags from HTML content while preserving other HTML.
    This removes <a href="...">...</a> tags but keeps the text content.
    """
    if not text:
        return text

    # Remove <a> tags but keep the text content inside them
    # Pattern matches: <a href="..." ...>text</a> or <a ...>text</a>
    text = re.sub(r'<a\s+[^>]*href[^>]*>(.*?)</a>', r'\1', text, flags=re.IGNORECASE | re.DOTALL)

    return text


def log_command(host: str, port: int, command: str, result: str, success: bool, username: str = 'unknown'):
    """Log an RCON command"""
    if not config.get('logging', {}).get('log_commands', True):
        return

    log_file = config.get('logging', {}).get('log_file')
    if not log_file:
        return

    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = 'SUCCESS' if success else 'FAILED'

        log_entry = f"[{timestamp}] [{status}] User: {username}, Server: {host}:{port}, Command: {command}\n"
        if not success:
            log_entry += f"  Error: {result}\n"

        with open(log_file, 'a') as f:
            f.write(log_entry)

    except Exception as e:
        logger.error(f"Error logging command: {e}")


# FastAPI Routes
@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse(request, 'index.html')


@app.get('/test-config', response_class=HTMLResponse)
async def test_config_page(request: Request):
    """Serve the config test page"""
    return templates.TemplateResponse(request, 'test_config.html')


@app.get('/favicon.ico')
async def favicon():
    """Return empty response for favicon to prevent 404 errors"""
    from fastapi.responses import Response
    return Response(status_code=204)  # No Content


@app.get('/logout')
async def logout(request: Request):
    """Handle logout and clear JWT token"""
    # Try to get user info from token for logging
    token = get_token_from_cookie(request)
    username = 'unknown'
    oauth_provider = None

    if token:
        payload = verify_token(token)
        if payload:
            username = payload.get('sub', 'unknown')
            oauth_provider = payload.get('provider')

    provider_info = f" (via {oauth_provider})" if oauth_provider else ""
    logger.info(f"User {username} logged out{provider_info}")

    # Create response with redirect
    response = RedirectResponse(url='/', status_code=303)

    # Clear JWT token cookie
    response.delete_cookie(key="access_token")

    return response


@app.get('/config')
async def get_config_endpoint():
    """Get client configuration"""
    oauth_config = config.get('security', {}).get('oauth', {})
    oauth_enabled = oauth_config.get('enabled', False)

    # Build list of enabled OAuth providers
    oauth_providers = []
    if oauth_enabled:
        if oauth_config.get('google', {}).get('enabled', False):
            oauth_providers.append('google')
        if oauth_config.get('facebook', {}).get('enabled', False):
            oauth_providers.append('facebook')
        if oauth_config.get('github', {}).get('enabled', False):
            oauth_providers.append('github')
        if oauth_config.get('apple', {}).get('enabled', False):
            oauth_providers.append('apple')

    return JSONResponse({
        'rcon': {
            'default_host': config.get('rcon', {}).get('default_host', 'localhost'),
            'default_port': config.get('rcon', {}).get('default_port', 42425),
            'locked_address': config.get('rcon', {}).get('locked_address', False)
        },
        'security': {
            'require_auth': config.get('security', {}).get('require_auth', True),
            'traditional_login_enabled': config.get('security', {}).get('traditional_login_enabled', True),
            'oauth_enabled': oauth_enabled,
            'oauth_providers': oauth_providers
        }
    })


# OAuth Routes
@app.get('/login/oauth/{provider}')
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login for a specific provider"""
    if provider not in ['google', 'facebook', 'github', 'apple']:
        return JSONResponse({'error': 'Invalid OAuth provider'}, status_code=400)

    oauth_config = config.get('security', {}).get('oauth', {})
    if not oauth_config.get('enabled', False):
        return JSONResponse({'error': 'OAuth is not enabled'}, status_code=400)

    if not oauth_config.get(provider, {}).get('enabled', False):
        return JSONResponse({'error': f'{provider} OAuth is not enabled'}, status_code=400)


    # Generate redirect URI
    redirect_uri = str(request.url_for('oauth_authorize', provider=provider))

    # Initiate OAuth flow
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)


@app.get('/login/oauth/{provider}/authorize')
async def oauth_authorize(provider: str, request: Request):
    """OAuth callback/authorization endpoint"""
    if provider not in ['google', 'facebook', 'github', 'apple']:
        return JSONResponse({'error': 'Invalid OAuth provider'}, status_code=400)

    try:
        # Get OAuth token
        token = await oauth.create_client(provider).authorize_access_token(request)

        # Get user info based on provider
        if provider == 'google':
            resp = await oauth.create_client(provider).get('https://www.googleapis.com/oauth2/v1/userinfo', token=token)
            user_info = resp.json()
            email = user_info.get('email')
            name = user_info.get('name', email)

        elif provider == 'facebook':
            resp = await oauth.create_client(provider).get('me?fields=id,name,email', token=token)
            user_info = resp.json()
            email = user_info.get('email')
            name = user_info.get('name', email)

        elif provider == 'github':
            # Get user info
            resp = await oauth.create_client(provider).get('user', token=token)
            user_info = resp.json()
            name = user_info.get('name') or user_info.get('login')

            # GitHub might not provide email in user endpoint, need to fetch separately
            email = user_info.get('email')
            if not email:
                # Fetch primary email
                email_resp = await oauth.create_client(provider).get('user/emails', token=token)
                emails = email_resp.json()
                # Find primary email
                for email_data in emails:
                    if email_data.get('primary'):
                        email = email_data.get('email')
                        break
                # If no primary, use first email
                if not email and emails:
                    email = emails[0].get('email')

        elif provider == 'apple':
            user_info = token.get('userinfo', {})
            email = user_info.get('email')
            name = user_info.get('name', email)

        else:
            return RedirectResponse(url='/?error=invalid_provider', status_code=303)

        # Check if email is provided
        if not email:
            logger.warning(f"OAuth login attempt without email from {provider}")
            return RedirectResponse(url='/?error=no_email', status_code=303)

        # Check if email is authorized
        if not is_email_authorized(email):
            logger.warning(f"Unauthorized OAuth login attempt from {email} via {provider}")
            return RedirectResponse(url='/?error=unauthorized', status_code=303)

        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": email,
                "name": name,
                "provider": provider
            }
        )

        # Record successful login
        record_login_attempt(request.client.host, True)

        logger.info(f"User {email} logged in via {provider} OAuth")

        # Create response with redirect
        response = RedirectResponse(url='/?login=success', status_code=303)

        # Set JWT token in httponly cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite='lax'
        )

        return response

    except Exception as e:
        logger.error(f"OAuth authorization error for {provider}: {e}")
        logger.error(traceback.format_exc())
        return RedirectResponse(url='/?error=oauth_failed', status_code=303)


# SocketIO event handlers - JWT-based authentication
@sio.event
async def connect(sid, environ):
    """Handle client connection and verify JWT token"""
    logger.info(f"Client connected: {sid}")

    # Extract JWT token from connection
    try:
        token = get_token_from_socketio_environ(environ)

        if token:
            payload = verify_token(token)

            if payload:
                username = payload.get('sub')
                display_name = payload.get('name', username)
                oauth_provider = payload.get('provider')

                logger.info(f"Authenticated connection for {sid}: username={username}, provider={oauth_provider}")

                # Store user info in Socket.IO session for convenience
                async with sio.session(sid) as socket_session:
                    socket_session['authenticated'] = True
                    socket_session['username'] = username
                    socket_session['display_name'] = display_name
                    socket_session['oauth_provider'] = oauth_provider
                    socket_session['token'] = token  # Store token for future verification
            else:
                logger.info(f"Invalid or expired token for {sid}")
        else:
            logger.info(f"No token found for {sid}")
    except Exception as e:
        logger.error(f"Error verifying token for {sid}: {e}")
        logger.error(traceback.format_exc())

    await sio.emit('connected', {'message': 'Connected to RCon Web Client'}, to=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {sid}")


@sio.on('login')
async def handle_login(sid, data):
    """Handle traditional login request and return JWT token"""
    # Get IP from environ - for now use placeholder
    ip_address = 'unknown'

    # Check lockout
    if check_lockout(ip_address):
        await sio.emit('login_response', {
            'success': False,
            'message': 'Too many failed login attempts. Please try again later.'
        }, to=sid)
        return

    logger.debug(f"Login attempt from {ip_address} with data: {data}")
    username = data.get('username', '')
    password = data.get('password', '')

    # Simple authentication (in production, use a proper user database)
    default_username = config.get('security', {}).get('default_username', 'admin')
    default_password = config.get('security', {}).get('default_password', 'changeme')

    if username == default_username and password == default_password:
        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": username,
                "name": username,
                "provider": "traditional"
            }
        )

        # Store user info in Socket.IO session
        async with sio.session(sid) as session:
            session['authenticated'] = True
            session['username'] = username
            session['display_name'] = username
            session['oauth_provider'] = None
            session['token'] = access_token

        await sio.emit('login_response', {
            'success': True,
            'message': 'Login successful',
            'token': access_token,  # Send token to client
            'username': username,
            'display_name': username
        }, to=sid)

        # Record successful login
        record_login_attempt(ip_address, True)
        logger.info(f"User {username} logged in via traditional login")
    else:
        # Record failed login
        record_login_attempt(ip_address, False)

        await sio.emit('login_response', {
            'success': False,
            'message': 'Invalid username or password'
        }, to=sid)
        logger.warning(f"Failed login attempt for user {username} from {ip_address}")


@sio.on('check_auth')
async def handle_check_auth(sid):
    """Check if user is already authenticated (e.g., via OAuth)"""
    async with sio.session(sid) as session:
        if session.get('authenticated', False):
            await sio.emit('auth_status', {
                'authenticated': True,
                'username': session.get('username', 'unknown'),
                'display_name': session.get('display_name', session.get('username', 'unknown')),
                'oauth_provider': session.get('oauth_provider')
            }, to=sid)
        else:
            await sio.emit('auth_status', {
                'authenticated': False
            }, to=sid)


@sio.on('logout')
async def handle_logout(sid):
    """Handle logout request - instructs client to redirect to logout route"""
    async with sio.session(sid) as session:
        username = session.get('username', 'unknown')
        oauth_provider = session.get('oauth_provider')

        provider_info = f" (via {oauth_provider})" if oauth_provider else ""
        logger.info(f"User {username} requested logout{provider_info}")

        # Tell client to redirect to logout route which will clear session properly
        await sio.emit('logout_response', {
            'success': True,
            'message': 'Logging out...',
            'redirect': '/logout'
        }, to=sid)


@sio.on('rcon_connect')
async def handle_rcon_connect(sid, data):
    """Handle RCon connection request"""
    logger.info(f"RCon connect request received: {data}")

    async with sio.session(sid) as session:
        logger.info(f"Session data: {dict(session)}")

        if config.get('security', {}).get('require_auth', True):
            if 'authenticated' not in session or not session['authenticated']:
                await sio.emit('rcon_response', {'success': False, 'message': 'Authentication required'}, to=sid)
                return

        # Get connection details
        locked_address = config.get('rcon', {}).get('locked_address', False)

        if locked_address:
            host = config.get('rcon', {}).get('default_host', 'localhost')
            port = config.get('rcon', {}).get('default_port', 42425)
            password = config.get('rcon', {}).get('password', '')
        else:
            host = data.get('host', config.get('rcon', {}).get('default_host', 'localhost'))
            port = int(data.get('port', config.get('rcon', {}).get('default_port', 42425)))
            password = data.get('password', config.get('rcon', {}).get('password', ''))

        # Test connection by sending a simple command
        try:
            logger.info(f"Testing connection to RCon server at {host}:{port}")

            # Store connection parameters in session
            session['rcon_host'] = host
            session['rcon_port'] = port
            session['rcon_password'] = password
            session['rcon_connected'] = True

            await sio.emit('rcon_response', {
                'success': True,
                'message': 'Connected to RCon server',
                'host': host,
                'port': port
            }, to=sid)
            logger.info(f"User {session.get('username', 'unknown')} connected to RCon server {host}:{port}")
        except ConnectionRefusedError:
            await sio.emit('rcon_response', {
                'success': False,
                'message': 'Connection refused. Check the server address and port.'
            }, to=sid)
            logger.error(f"Connection refused to RCon server {host}:{port}")
        except TimeoutError:
            await sio.emit('rcon_response', {
                'success': False,
                'message': 'Connection timeout. Server not responding.'
            }, to=sid)
            logger.error(f"Connection timeout to RCon server {host}:{port}")
        except Exception as e:
            await sio.emit('rcon_response', {
                'success': False,
                'message': f'Connection error: {str(e)}'
            }, to=sid)
            logger.error(f"RCon connection error: {e}")
            logger.error(traceback.format_exc())


@sio.on('rcon_disconnect')
async def handle_rcon_disconnect(sid):
    """Handle RCon disconnection request"""
    logger.info(f"RCon disconnect request received")

    async with sio.session(sid) as session:
        logger.info(f"Session data: {dict(session)}")

        # Clear connection parameters from session
        session.pop('rcon_host', None)
        session.pop('rcon_port', None)
        session.pop('rcon_password', None)
        session.pop('rcon_connected', None)

        await sio.emit('rcon_response', {'success': True, 'message': 'Disconnected from RCon server'}, to=sid)
    logger.info(f"User {session.get('username', 'unknown')} disconnected from RCon server")


@sio.on('rcon_command')
async def handle_rcon_command(sid, data):
    """Handle RCon command execution"""
    logger.info(f"RCon command request received: {data}")

    async with sio.session(sid) as session:
        logger.info(f"Session data: {dict(session)}")

        if config.get('security', {}).get('require_auth', True):
            if 'authenticated' not in session or not session['authenticated']:
                await sio.emit('command_response', {'success': False, 'message': 'Authentication required'}, to=sid)
                return

        if not session.get('rcon_connected', False):
            await sio.emit('command_response', {'success': False, 'message': 'Not connected to RCon server'}, to=sid)
            return

        command = data.get('command', '').strip()
        if not command:
            await sio.emit('command_response', {'success': False, 'message': 'Empty command'}, to=sid)
            return

        # Get connection parameters from session
        host = session.get('rcon_host')
        port = session.get('rcon_port')
        password = session.get('rcon_password')
        username = session.get('username', 'unknown')

        if not host or not port or not password:
            await sio.emit('command_response', {'success': False, 'message': 'Connection parameters missing'}, to=sid)
            return

        try:
            logger.info(f"Executing command: {command}")

            # Execute command using async rcon function
            result = await rcon(command, host=host, port=port, passwd=password)

            logger.info(f"Command execution complete")

            # Sanitize HTML response - remove anchor tags but preserve other HTML
            sanitized_result = sanitize_html_response(result)

            # Log command
            log_command(host, port, command, sanitized_result, True, username)

            await sio.emit('command_response', {
                'success': True,
                'message': sanitized_result if sanitized_result else "Command executed (no output)",
                'command': command,
                'timestamp': datetime.now().isoformat(),
                'is_html': True  # Flag to indicate the response contains HTML
            }, to=sid)

        except Exception as e:
            error_msg = f'Command execution error: {str(e)}'
            log_command(host, port, command, error_msg, False, username)

            await sio.emit('command_response', {
                'success': False,
                'message': error_msg,
                'command': command
            }, to=sid)
            logger.error(f"Command execution error: {e}")
            logger.error(traceback.format_exc())


@sio.on('rcon_status')
async def handle_rcon_status(sid):
    """Handle RCon status request"""
    async with sio.session(sid) as session:
        await sio.emit('status_response', {
            'connected': session.get('rcon_connected', False),
            'host': session.get('rcon_host'),
            'port': session.get('rcon_port')
        }, to=sid)


def run():
    """Run the FastAPI application with uvicorn"""
    load_config()

    host = config.get('server', {}).get('host', '0.0.0.0')
    port = config.get('server', {}).get('port', 5000)

    logger.info(f"Starting Vintage Story RCon Web Client on {host}:{port}")

    # Run the combined ASGI app (FastAPI + SocketIO)
    uvicorn.run(socket_app, host=host, port=port, log_level="info")


if __name__ == '__main__':
    run()

