"""
Unit tests for authentication functionality including JWT, traditional login, and OAuth.
Tests are self-contained with mocked external dependencies.
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile
import yaml
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestJWTAuthentication(unittest.TestCase):
    """Test JWT token creation, verification, and expiration."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock configuration
        self.test_config = {
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'secret_key': 'test-secret-key-for-jwt-testing'
            },
            'security': {
                'require_auth': True,
                'traditional_login_enabled': True,
                'default_username': 'admin',
                'default_password': 'testpass',
                'max_login_attempts': 5,
                'lockout_duration': 300
            }
        }

        # Create temp config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        # Patch config loading
        with patch('app.Path') as mock_path:
            mock_path.return_value.parent = Path(self.temp_dir)
            # Import after patching
            import app
            app.config = self.test_config
            app.JWT_SECRET_KEY = 'test-secret-key-for-jwt-testing'
            self.app = app

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_access_token(self):
        """Test JWT token creation with proper claims."""
        test_data = {
            "sub": "test@example.com",
            "name": "Test User",
            "provider": "test"
        }

        token = self.app.create_access_token(test_data)

        # Verify token is a string
        self.assertIsInstance(token, str)
        # Verify token has three parts (header.payload.signature)
        self.assertEqual(len(token.split('.')), 3)

    def test_create_access_token_with_expiration(self):
        """Test JWT token creation with custom expiration."""
        test_data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)

        token = self.app.create_access_token(test_data, expires_delta=expires_delta)
        payload = self.app.verify_token(token)

        self.assertIsNotNone(payload)
        self.assertIn('exp', payload)
        self.assertIn('iat', payload)

    def test_verify_valid_token(self):
        """Test verification of a valid JWT token."""
        test_data = {
            "sub": "test@example.com",
            "name": "Test User",
            "provider": "traditional"
        }

        token = self.app.create_access_token(test_data)
        payload = self.app.verify_token(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload.get('sub'), 'test@example.com')
        self.assertEqual(payload.get('name'), 'Test User')
        self.assertEqual(payload.get('provider'), 'traditional')

    def test_verify_invalid_token(self):
        """Test verification fails for invalid tokens."""
        invalid_tokens = [
            "invalid.token.here",
            "not-even-a-jwt",
            "",
            None
        ]

        for invalid_token in invalid_tokens:
            if invalid_token is not None:
                payload = self.app.verify_token(invalid_token)
                self.assertIsNone(payload, f"Token '{invalid_token}' should be invalid")

    def test_verify_expired_token(self):
        """Test verification fails for expired tokens."""
        test_data = {"sub": "test@example.com"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)

        token = self.app.create_access_token(test_data, expires_delta=expires_delta)
        payload = self.app.verify_token(token)

        # Should return None for expired token
        self.assertIsNone(payload)

    def test_verify_token_with_wrong_secret(self):
        """Test verification fails when using wrong secret key."""
        test_data = {"sub": "test@example.com"}
        token = self.app.create_access_token(test_data)

        # Temporarily change the secret key
        original_secret = self.app.JWT_SECRET_KEY
        self.app.JWT_SECRET_KEY = "wrong-secret-key"

        payload = self.app.verify_token(token)

        # Restore original secret
        self.app.JWT_SECRET_KEY = original_secret

        self.assertIsNone(payload)


class TestTraditionalLogin(unittest.TestCase):
    """Test traditional username/password authentication."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'server': {
                'secret_key': 'test-secret-key'
            },
            'security': {
                'require_auth': True,
                'traditional_login_enabled': True,
                'default_username': 'admin',
                'default_password': 'testpass',
                'max_login_attempts': 3,
                'lockout_duration': 300
            }
        }

        # Create temp config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        with patch('app.Path') as mock_path:
            mock_path.return_value.parent = Path(self.temp_dir)
            import app
            app.config = self.test_config
            app.JWT_SECRET_KEY = 'test-secret-key'
            app.login_attempts = {}
            app.lockouts = {}
            self.app = app

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_check_lockout_not_locked(self):
        """Test lockout check when IP is not locked."""
        ip_address = "192.168.1.100"
        is_locked = self.app.check_lockout(ip_address)
        self.assertFalse(is_locked)

    def test_check_lockout_active(self):
        """Test lockout check when IP is actively locked."""
        ip_address = "192.168.1.100"
        # Set lockout in the future
        self.app.lockouts[ip_address] = datetime.now() + timedelta(seconds=300)

        is_locked = self.app.check_lockout(ip_address)
        self.assertTrue(is_locked)

    def test_check_lockout_expired(self):
        """Test lockout check when lockout has expired."""
        ip_address = "192.168.1.100"
        # Set lockout in the past
        self.app.lockouts[ip_address] = datetime.now() - timedelta(seconds=1)

        is_locked = self.app.check_lockout(ip_address)
        self.assertFalse(is_locked)
        # Verify lockout was removed
        self.assertNotIn(ip_address, self.app.lockouts)

    def test_record_login_attempt_success(self):
        """Test recording successful login clears attempts."""
        ip_address = "192.168.1.100"
        # Set some failed attempts
        self.app.login_attempts[ip_address] = 2

        self.app.record_login_attempt(ip_address, success=True)

        self.assertNotIn(ip_address, self.app.login_attempts)

    def test_record_login_attempt_failure(self):
        """Test recording failed login increments attempts."""
        ip_address = "192.168.1.100"

        self.app.record_login_attempt(ip_address, success=False)
        self.assertEqual(self.app.login_attempts[ip_address], 1)

        self.app.record_login_attempt(ip_address, success=False)
        self.assertEqual(self.app.login_attempts[ip_address], 2)

    def test_record_login_attempt_triggers_lockout(self):
        """Test lockout is triggered after max failed attempts."""
        ip_address = "192.168.1.100"
        max_attempts = self.app.config['security']['max_login_attempts']

        # Record max failed attempts
        for _ in range(max_attempts):
            self.app.record_login_attempt(ip_address, success=False)

        # Verify lockout was set
        self.assertIn(ip_address, self.app.lockouts)
        self.assertIsInstance(self.app.lockouts[ip_address], datetime)
        self.assertGreater(self.app.lockouts[ip_address], datetime.now())


class TestPasswordHashing(unittest.TestCase):
    """Test password hashing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        import app
        self.app = app

    def test_hash_password_creates_hash(self):
        """Test password hashing creates a hash."""
        password = "testpassword123"
        hashed = self.app.hash_password(password)

        self.assertIsInstance(hashed, str)
        self.assertNotEqual(hashed, password)
        self.assertEqual(len(hashed), 64)  # SHA-256 produces 64 hex characters

    def test_hash_password_consistent(self):
        """Test same password produces same hash."""
        password = "testpassword123"
        hash1 = self.app.hash_password(password)
        hash2 = self.app.hash_password(password)

        self.assertEqual(hash1, hash2)

    def test_hash_password_different_for_different_passwords(self):
        """Test different passwords produce different hashes."""
        password1 = "testpassword123"
        password2 = "differentpassword456"

        hash1 = self.app.hash_password(password1)
        hash2 = self.app.hash_password(password2)

        self.assertNotEqual(hash1, hash2)


class TestOAuthAuthorization(unittest.TestCase):
    """Test OAuth email authorization functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'security': {
                'oauth': {
                    'enabled': True,
                    'authorized_emails': [
                        'admin@example.com',
                        'user@example.com',
                        'Test@Example.COM'  # Test case insensitivity
                    ]
                }
            }
        }

        import app
        app.config = self.test_config
        self.app = app

    def test_is_email_authorized_valid(self):
        """Test authorized email is accepted."""
        self.assertTrue(self.app.is_email_authorized('admin@example.com'))
        self.assertTrue(self.app.is_email_authorized('user@example.com'))

    def test_is_email_authorized_case_insensitive(self):
        """Test email authorization is case insensitive."""
        self.assertTrue(self.app.is_email_authorized('ADMIN@EXAMPLE.COM'))
        self.assertTrue(self.app.is_email_authorized('User@Example.Com'))
        self.assertTrue(self.app.is_email_authorized('test@example.com'))

    def test_is_email_authorized_invalid(self):
        """Test unauthorized email is rejected."""
        self.assertFalse(self.app.is_email_authorized('hacker@evil.com'))
        self.assertFalse(self.app.is_email_authorized('unauthorized@example.com'))

    def test_is_email_authorized_empty_list(self):
        """Test empty authorized list allows all emails."""
        self.app.config['security']['oauth']['authorized_emails'] = []

        self.assertTrue(self.app.is_email_authorized('anyone@anywhere.com'))
        self.assertTrue(self.app.is_email_authorized('test@test.com'))


class TestTokenExtraction(unittest.TestCase):
    """Test JWT token extraction from various sources."""

    def setUp(self):
        """Set up test fixtures."""
        import app
        self.app = app

    def test_get_token_from_socketio_environ_query_string(self):
        """Test token extraction from Socket.IO query string."""
        environ = {
            'QUERY_STRING': 'token=test.jwt.token&other=param'
        }

        token = self.app.get_token_from_socketio_environ(environ)
        self.assertEqual(token, 'test.jwt.token')

    def test_get_token_from_socketio_environ_cookie_asgi(self):
        """Test token extraction from Socket.IO ASGI cookie."""
        environ = {
            'asgi.scope': {
                'headers': [
                    (b'cookie', b'access_token=test.jwt.token; other=value')
                ]
            }
        }

        token = self.app.get_token_from_socketio_environ(environ)
        self.assertEqual(token, 'test.jwt.token')

    def test_get_token_from_socketio_environ_cookie_legacy(self):
        """Test token extraction from Socket.IO legacy cookie format."""
        environ = {
            'headers': [
                (b'cookie', b'access_token=test.jwt.token')
            ]
        }

        token = self.app.get_token_from_socketio_environ(environ)
        self.assertEqual(token, 'test.jwt.token')

    def test_get_token_from_socketio_environ_no_token(self):
        """Test token extraction returns None when no token present."""
        environ = {
            'QUERY_STRING': 'other=param'
        }

        token = self.app.get_token_from_socketio_environ(environ)
        self.assertIsNone(token)

    def test_get_token_from_socketio_environ_error_handling(self):
        """Test token extraction handles errors gracefully."""
        # Invalid environ structure
        environ = None
        token = self.app.get_token_from_socketio_environ(environ)
        self.assertIsNone(token)


class TestOAuthProviderInitialization(unittest.TestCase):
    """Test OAuth provider initialization and configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'security': {
                'oauth': {
                    'enabled': True,
                    'google': {
                        'enabled': True,
                        'client_id': 'test-google-client-id',
                        'client_secret': 'test-google-client-secret'
                    },
                    'facebook': {
                        'enabled': True,
                        'client_id': 'test-facebook-app-id',
                        'client_secret': 'test-facebook-app-secret'
                    },
                    'github': {
                        'enabled': True,
                        'client_id': 'test-github-client-id',
                        'client_secret': 'test-github-client-secret'
                    },
                    'apple': {
                        'enabled': True,
                        'client_id': 'test-apple-service-id',
                        'client_secret': 'test-apple-client-secret',
                        'team_id': 'test-team-id',
                        'key_id': 'test-key-id'
                    }
                }
            }
        }

        # Create temp config
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('app.oauth')
    def test_initialize_oauth_providers_google(self, mock_oauth):
        """Test Google OAuth provider initialization."""
        import app
        app.config = self.test_config

        app.initialize_oauth_providers()

        # Verify Google was registered
        mock_oauth.register.assert_any_call(
            name='google',
            client_id='test-google-client-id',
            client_secret='test-google-client-secret',
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )

    @patch('app.oauth')
    def test_initialize_oauth_providers_facebook(self, mock_oauth):
        """Test Facebook OAuth provider initialization."""
        import app
        app.config = self.test_config

        app.initialize_oauth_providers()

        # Verify Facebook was registered
        mock_oauth.register.assert_any_call(
            name='facebook',
            client_id='test-facebook-app-id',
            client_secret='test-facebook-app-secret',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            access_token_params=None,
            authorize_url='https://www.facebook.com/dialog/oauth',
            authorize_params=None,
            api_base_url='https://graph.facebook.com/',
            client_kwargs={'scope': 'email'}
        )

    @patch('app.oauth')
    def test_initialize_oauth_providers_github(self, mock_oauth):
        """Test GitHub OAuth provider initialization."""
        import app
        app.config = self.test_config

        app.initialize_oauth_providers()

        # Verify GitHub was registered
        mock_oauth.register.assert_any_call(
            name='github',
            client_id='test-github-client-id',
            client_secret='test-github-client-secret',
            access_token_url='https://github.com/login/oauth/access_token',
            access_token_params=None,
            authorize_url='https://github.com/login/oauth/authorize',
            authorize_params=None,
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'}
        )

    @patch('app.oauth')
    def test_initialize_oauth_providers_disabled(self, mock_oauth):
        """Test OAuth providers not initialized when disabled."""
        import app
        app.config = {
            'security': {
                'oauth': {
                    'enabled': True,
                    'google': {'enabled': False},
                    'facebook': {'enabled': False},
                    'github': {'enabled': False},
                    'apple': {'enabled': False}
                }
            }
        }

        app.initialize_oauth_providers()

        # Verify no providers were registered
        mock_oauth.register.assert_not_called()


if __name__ == '__main__':
    unittest.main()

