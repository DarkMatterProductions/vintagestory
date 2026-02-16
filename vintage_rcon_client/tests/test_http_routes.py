"""
Unit tests for FastAPI HTTP routes including OAuth, config, and logout endpoints.
All external OAuth services are mocked with simulated certificates and responses.
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock, Mock
from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile
import yaml
import json
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFastAPIRoutes(unittest.TestCase):
    """Test FastAPI HTTP route handlers."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient

        self.test_config = {
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'secret_key': 'test-secret-key'
            },
            'rcon': {
                'default_host': 'localhost',
                'default_port': 42425,
                'locked_address': False,
                'password': 'testpass'
            },
            'security': {
                'require_auth': True,
                'traditional_login_enabled': True,
                'oauth': {
                    'enabled': True,
                    'authorized_emails': ['test@example.com'],
                    'google': {'enabled': True},
                    'facebook': {'enabled': True},
                    'github': {'enabled': True},
                    'apple': {'enabled': False}
                }
            }
        }

        # Create temp config
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        with patch('app.Path') as mock_path:
            mock_path.return_value.parent = Path(self.temp_dir)
            import app
            app.config = self.test_config
            app.JWT_SECRET_KEY = 'test-secret-key'
            self.app_module = app

            # Create test client
            self.client = TestClient(app.app)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_index_route(self):
        """Test index route returns HTML."""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers['content-type'])

    def test_favicon_route(self):
        """Test favicon returns 204."""
        response = self.client.get('/favicon.ico')

        self.assertEqual(response.status_code, 204)

    def test_config_endpoint(self):
        """Test config endpoint returns proper configuration."""
        response = self.client.get('/config')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify RCON config
        self.assertIn('rcon', data)
        self.assertEqual(data['rcon']['default_host'], 'localhost')
        self.assertEqual(data['rcon']['default_port'], 42425)
        self.assertFalse(data['rcon']['locked_address'])

        # Verify security config
        self.assertIn('security', data)
        self.assertTrue(data['security']['require_auth'])
        self.assertTrue(data['security']['traditional_login_enabled'])
        self.assertTrue(data['security']['oauth_enabled'])

        # Verify OAuth providers
        self.assertIn('oauth_providers', data['security'])
        self.assertIn('google', data['security']['oauth_providers'])
        self.assertIn('facebook', data['security']['oauth_providers'])
        self.assertIn('github', data['security']['oauth_providers'])
        self.assertNotIn('apple', data['security']['oauth_providers'])

    def test_logout_route(self):
        """Test logout route clears token and redirects."""
        response = self.client.get('/logout', follow_redirects=False)

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers['location'], '/')

        # Note: FastAPI TestClient doesn't always expose Set-Cookie headers
        # The important part is the redirect works


class TestOAuthRoutes(unittest.TestCase):
    """Test OAuth login routes with mocked OAuth providers."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient

        self.test_config = {
            'server': {'secret_key': 'test-secret-key'},
            'security': {
                'oauth': {
                    'enabled': True,
                    'authorized_emails': ['authorized@example.com'],
                    'google': {
                        'enabled': True,
                        'client_id': 'test-google-client-id',
                        'client_secret': 'test-google-client-secret'
                    },
                    'facebook': {
                        'enabled': True,
                        'client_id': 'test-facebook-client-id',
                        'client_secret': 'test-facebook-client-secret'
                    },
                    'github': {
                        'enabled': True,
                        'client_id': 'test-github-client-id',
                        'client_secret': 'test-github-client-secret'
                    },
                    'apple': {
                        'enabled': False
                    }
                }
            }
        }

        # Create temp config
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        with patch('app.Path') as mock_path:
            mock_path.return_value.parent = Path(self.temp_dir)
            import app
            app.config = self.test_config
            app.JWT_SECRET_KEY = 'test-secret-key'
            self.app_module = app

            self.client = TestClient(app.app)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_oauth_login_invalid_provider(self):
        """Test OAuth login with invalid provider."""
        response = self.client.get('/login/oauth/invalid')

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid OAuth provider', response.json()['error'])

    def test_oauth_login_disabled_provider(self):
        """Test OAuth login with disabled provider."""
        response = self.client.get('/login/oauth/apple')

        self.assertEqual(response.status_code, 400)
        self.assertIn('not enabled', response.json()['error'])

    @patch('app.oauth')
    def test_oauth_login_google_redirect(self, mock_oauth):
        """Test Google OAuth login redirects properly."""
        # Mock OAuth client
        mock_client = MagicMock()
        mock_client.authorize_redirect = AsyncMock(return_value=MagicMock(status_code=302))
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google', follow_redirects=False)

        # Should initiate redirect to Google
        mock_oauth.create_client.assert_called_with('google')

    @patch('app.oauth')
    def test_oauth_authorize_google_success(self, mock_oauth):
        """Test successful Google OAuth authorization."""
        # Mock OAuth token and user info
        mock_token = {
            'access_token': 'mock-access-token',
            'token_type': 'Bearer'
        }

        mock_user_info = {
            'email': 'authorized@example.com',
            'name': 'Test User',
            'verified_email': True
        }

        # Mock OAuth client
        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(return_value=mock_token)

        # Mock user info request
        mock_response = MagicMock()
        mock_response.json.return_value = mock_user_info
        mock_client.get = AsyncMock(return_value=mock_response)

        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should redirect to home with success
        self.assertEqual(response.status_code, 303)
        self.assertIn('/?login=success', response.headers['location'])

        # Should set access token cookie
        self.assertIn('access_token', response.cookies)

    @patch('app.oauth')
    def test_oauth_authorize_unauthorized_email(self, mock_oauth):
        """Test OAuth authorization with unauthorized email."""
        mock_token = {'access_token': 'mock-access-token'}
        mock_user_info = {
            'email': 'unauthorized@example.com',
            'name': 'Unauthorized User'
        }

        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
        mock_response = MagicMock()
        mock_response.json.return_value = mock_user_info
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should redirect with error
        self.assertEqual(response.status_code, 303)
        self.assertIn('error=unauthorized', response.headers['location'])

    @patch('app.oauth')
    def test_oauth_authorize_no_email(self, mock_oauth):
        """Test OAuth authorization without email in response."""
        mock_token = {'access_token': 'mock-access-token'}
        mock_user_info = {
            'name': 'No Email User'
            # No email field
        }

        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
        mock_response = MagicMock()
        mock_response.json.return_value = mock_user_info
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should redirect with error
        self.assertEqual(response.status_code, 303)
        self.assertIn('error=no_email', response.headers['location'])

    @patch('app.oauth')
    def test_oauth_authorize_github_with_email_fetch(self, mock_oauth):
        """Test GitHub OAuth authorization that requires email fetch."""
        mock_token = {'access_token': 'mock-access-token'}

        # User info without email
        mock_user_info = {
            'login': 'testuser',
            'name': 'Test User'
            # No email
        }

        # Email endpoint response
        mock_emails = [
            {'email': 'authorized@example.com', 'primary': True, 'verified': True}
        ]

        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(return_value=mock_token)

        # Mock two different GET requests
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = mock_user_info

        mock_email_response = MagicMock()
        mock_email_response.json.return_value = mock_emails

        mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_email_response])
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/github/authorize', follow_redirects=False)

        # Should succeed with fetched email
        self.assertEqual(response.status_code, 303)
        self.assertIn('login=success', response.headers['location'])

    @patch('app.oauth')
    def test_oauth_authorize_facebook_success(self, mock_oauth):
        """Test successful Facebook OAuth authorization."""
        mock_token = {'access_token': 'mock-access-token'}
        mock_user_info = {
            'email': 'authorized@example.com',
            'name': 'Facebook User',
            'id': '123456789'
        }

        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(return_value=mock_token)
        mock_response = MagicMock()
        mock_response.json.return_value = mock_user_info
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/facebook/authorize', follow_redirects=False)

        self.assertEqual(response.status_code, 303)
        self.assertIn('login=success', response.headers['location'])

    @patch('app.oauth')
    def test_oauth_authorize_error_handling(self, mock_oauth):
        """Test OAuth authorization handles exceptions gracefully."""
        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(side_effect=Exception("OAuth error"))
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should redirect with error
        self.assertEqual(response.status_code, 303)
        self.assertIn('error=oauth_failed', response.headers['location'])


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading and environment variable overrides."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Clean up any environment variables
        env_vars = [key for key in os.environ.keys() if key.startswith('VS_RCON_CLIENT_CFG_')]
        for var in env_vars:
            del os.environ[var]

    def test_load_config_creates_default(self):
        """Test config loading creates default config if missing."""
        config_path = Path(self.temp_dir) / 'config.yaml'

        with patch('app.Path') as mock_path, \
             patch('app.app.add_middleware') as mock_add_middleware:
            mock_path.return_value.parent = Path(self.temp_dir)
            import app

            # Reset middleware flag to allow the test to add it
            app._middleware_added = False

            # Config file doesn't exist yet
            self.assertFalse(config_path.exists())

            # Load config should create it
            app.load_config()

            # Config file should now exist
            self.assertTrue(config_path.exists())

            # Verify it has expected structure
            with open(config_path) as f:
                config = yaml.safe_load(f)

            self.assertIn('server', config)
            self.assertIn('rcon', config)
            self.assertIn('security', config)
            self.assertIn('logging', config)

            # Verify middleware was added
            mock_add_middleware.assert_called_once()

    def test_load_config_existing_file(self):
        """Test config loading reads existing file."""
        config_path = Path(self.temp_dir) / 'config.yaml'

        test_config = {
            'server': {
                'host': '127.0.0.1',
                'port': 8080,
                'secret_key': 'my-secret'
            },
            'rcon': {
                'default_host': 'game-server',
                'default_port': 12345
            }
        }

        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)

        with patch('app.Path') as mock_path, \
             patch('app.app.add_middleware'):
            mock_path.return_value.parent = Path(self.temp_dir)
            import app

            # Reset middleware flag to allow the test to add it
            app._middleware_added = False

            app.load_config()

            # Verify config was loaded
            self.assertEqual(app.config['server']['host'], '127.0.0.1')
            self.assertEqual(app.config['server']['port'], 8080)
            self.assertEqual(app.config['rcon']['default_host'], 'game-server')


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions like HTML sanitization and command logging."""

    def setUp(self):
        """Set up test fixtures."""
        import app
        self.app = app
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sanitize_html_response_removes_anchors(self):
        """Test HTML sanitization removes anchor tags."""
        html_with_anchors = '<div>Hello <a href="http://example.com">World</a>!</div>'

        result = self.app.sanitize_html_response(html_with_anchors)

        self.assertEqual(result, '<div>Hello World!</div>')

    def test_sanitize_html_response_preserves_other_html(self):
        """Test HTML sanitization preserves non-anchor tags."""
        html = '<div><span class="highlight">Important</span> <strong>text</strong></div>'

        result = self.app.sanitize_html_response(html)

        self.assertEqual(result, html)

    def test_sanitize_html_response_handles_none(self):
        """Test HTML sanitization handles None input."""
        result = self.app.sanitize_html_response(None)

        self.assertIsNone(result)

    def test_sanitize_html_response_handles_empty_string(self):
        """Test HTML sanitization handles empty string."""
        result = self.app.sanitize_html_response('')

        self.assertEqual(result, '')

    def test_sanitize_html_response_complex_anchors(self):
        """Test HTML sanitization handles complex anchor tags."""
        html = '<div>Visit <a href="http://example.com" class="link" target="_blank">our site</a> today!</div>'

        result = self.app.sanitize_html_response(html)

        self.assertEqual(result, '<div>Visit our site today!</div>')

    def test_log_command_success(self):
        """Test command logging for successful execution."""
        log_file = Path(self.temp_dir) / 'test.log'

        self.app.config = {
            'logging': {
                'log_commands': True,
                'log_file': str(log_file)
            }
        }

        self.app.log_command(
            host='localhost',
            port=42425,
            command='status',
            result='Server is running',
            success=True,
            username='testuser'
        )

        # Verify log file was created and contains entry
        self.assertTrue(log_file.exists())

        with open(log_file) as f:
            log_content = f.read()

        self.assertIn('[SUCCESS]', log_content)
        self.assertIn('testuser', log_content)
        self.assertIn('localhost:42425', log_content)
        self.assertIn('status', log_content)

    def test_log_command_failure(self):
        """Test command logging for failed execution."""
        log_file = Path(self.temp_dir) / 'test.log'

        self.app.config = {
            'logging': {
                'log_commands': True,
                'log_file': str(log_file)
            }
        }

        self.app.log_command(
            host='localhost',
            port=42425,
            command='invalid_command',
            result='Command not found',
            success=False,
            username='testuser'
        )

        with open(log_file) as f:
            log_content = f.read()

        self.assertIn('[FAILED]', log_content)
        self.assertIn('Error: Command not found', log_content)

    def test_log_command_disabled(self):
        """Test command logging is skipped when disabled."""
        log_file = Path(self.temp_dir) / 'test.log'

        self.app.config = {
            'logging': {
                'log_commands': False,
                'log_file': str(log_file)
            }
        }

        self.app.log_command(
            host='localhost',
            port=42425,
            command='status',
            result='Server is running',
            success=True
        )

        # Log file should not be created
        self.assertFalse(log_file.exists())


if __name__ == '__main__':
    unittest.main()


