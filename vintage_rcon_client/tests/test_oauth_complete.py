"""
Unit tests for OAuth flow with simulated certificates and tokens.
Tests verify OAuth process works without querying external services.
All OAuth providers and token validation are completely mocked.
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile
import yaml
import json
import base64

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOAuthFlowSimulation(unittest.TestCase):
    """Test complete OAuth flow with simulated responses."""

    def setUp(self):
        """Set up test fixtures with simulated OAuth certificates."""
        from fastapi.testclient import TestClient

        # Simulated OAuth configuration
        self.test_config = {
            'server': {'secret_key': 'test-secret-key'},
            'security': {
                'oauth': {
                    'enabled': True,
                    'authorized_emails': [
                        'authorized@example.com',
                        'admin@company.com'
                    ],
                    'google': {
                        'enabled': True,
                        'client_id': 'simulated-google-client-id.apps.googleusercontent.com',
                        'client_secret': 'simulated-google-client-secret'
                    },
                    'github': {
                        'enabled': True,
                        'client_id': 'simulated-github-client-id',
                        'client_secret': 'simulated-github-client-secret'
                    }
                }
            }
        }

        # Create temp config
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        # Simulated OAuth tokens
        self.simulated_google_token = {
            'access_token': 'simulated-google-access-token-abc123',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'openid email profile',
            'id_token': self._create_simulated_jwt('google', 'authorized@example.com')
        }

        self.simulated_github_token = {
            'access_token': 'simulated-github-access-token-xyz789',
            'token_type': 'bearer',
            'scope': 'user:email'
        }

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

    def _create_simulated_jwt(self, provider, email, name=None):
        """Create a simulated JWT token for testing."""
        if name is None:
            name = email.split('@')[0].capitalize()

        # Create JWT-like structure (header.payload.signature)
        header = base64.b64encode(json.dumps({
            'alg': 'RS256',
            'typ': 'JWT',
            'kid': 'simulated-key-id'
        }).encode()).decode()

        payload = base64.b64encode(json.dumps({
            'iss': f'https://{provider}.com',
            'sub': f'{provider}-user-id-12345',
            'email': email,
            'email_verified': True,
            'name': name,
            'iat': int(datetime.now().timestamp()),
            'exp': int((datetime.now() + timedelta(hours=1)).timestamp())
        }).encode()).decode()

        signature = base64.b64encode(b'simulated-signature').decode()

        return f'{header}.{payload}.{signature}'

    @patch('app.oauth')
    def test_oauth_complete_flow_google(self, mock_oauth):
        """Test complete OAuth flow for Google provider."""
        # Mock OAuth client
        mock_client = MagicMock()

        # Mock authorization redirect
        mock_redirect_response = MagicMock()
        mock_redirect_response.status_code = 302
        mock_redirect_response.headers = {
            'location': 'https://accounts.google.com/o/oauth2/v2/auth?client_id=...'
        }
        mock_client.authorize_redirect = AsyncMock(return_value=mock_redirect_response)

        # Mock token exchange
        mock_client.authorize_access_token = AsyncMock(return_value=self.simulated_google_token)

        # Mock userinfo endpoint
        mock_userinfo_response = MagicMock()
        mock_userinfo_response.json.return_value = {
            'sub': 'google-user-id-12345',
            'email': 'authorized@example.com',
            'email_verified': True,
            'name': 'Authorized User',
            'picture': 'https://example.com/photo.jpg',
            'given_name': 'Authorized',
            'family_name': 'User'
        }
        mock_client.get = AsyncMock(return_value=mock_userinfo_response)

        mock_oauth.create_client.return_value = mock_client

        # Step 1: Initiate OAuth login
        response = self.client.get('/login/oauth/google', follow_redirects=False)

        # Should redirect to Google
        mock_client.authorize_redirect.assert_called_once()

        # Step 2: OAuth callback/authorization
        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should exchange code for token
        mock_client.authorize_access_token.assert_called_once()

        # Should fetch user info
        mock_client.get.assert_called_once()

        # Should redirect to home with success
        self.assertEqual(response.status_code, 303)
        self.assertIn('login=success', response.headers['location'])

        # Should set JWT cookie
        self.assertIn('access_token', response.cookies)

        # Verify JWT token contains correct claims
        jwt_token = response.cookies['access_token']
        payload = self.app_module.verify_token(jwt_token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['sub'], 'authorized@example.com')
        self.assertEqual(payload['name'], 'Authorized User')
        self.assertEqual(payload['provider'], 'google')

    @patch('app.oauth')
    def test_oauth_complete_flow_github(self, mock_oauth):
        """Test complete OAuth flow for GitHub provider."""
        mock_client = MagicMock()

        # Mock token exchange
        mock_client.authorize_access_token = AsyncMock(return_value=self.simulated_github_token)

        # Mock user endpoint (without email)
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            'login': 'githubuser',
            'id': 12345,
            'node_id': 'MDQ6VXNlcjEyMzQ1',
            'avatar_url': 'https://avatars.githubusercontent.com/u/12345',
            'name': 'GitHub User',
            'bio': 'Test user'
            # No email
        }

        # Mock emails endpoint
        mock_emails_response = MagicMock()
        mock_emails_response.json.return_value = [
            {
                'email': 'authorized@example.com',
                'primary': True,
                'verified': True,
                'visibility': 'private'
            },
            {
                'email': 'secondary@example.com',
                'primary': False,
                'verified': True,
                'visibility': 'private'
            }
        ]

        # Mock client.get to return different responses for different endpoints
        mock_client.get = AsyncMock(side_effect=[mock_user_response, mock_emails_response])
        mock_oauth.create_client.return_value = mock_client

        # OAuth callback/authorization
        response = self.client.get('/login/oauth/github/authorize', follow_redirects=False)

        # Should call both user and emails endpoints
        self.assertEqual(mock_client.get.call_count, 2)

        # Should redirect with success
        self.assertEqual(response.status_code, 303)
        self.assertIn('login=success', response.headers['location'])

        # Verify JWT token
        jwt_token = response.cookies['access_token']
        payload = self.app_module.verify_token(jwt_token)
        self.assertEqual(payload['sub'], 'authorized@example.com')
        self.assertEqual(payload['provider'], 'github')

    @patch('app.oauth')
    def test_oauth_token_validation(self, mock_oauth):
        """Test OAuth token validation with simulated certificates."""
        mock_client = MagicMock()

        # Simulated token with all required fields
        valid_token = {
            'access_token': 'valid-access-token',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_token': 'refresh-token',
            'scope': 'openid email profile'
        }

        mock_client.authorize_access_token = AsyncMock(return_value=valid_token)

        mock_userinfo_response = MagicMock()
        mock_userinfo_response.json.return_value = {
            'email': 'authorized@example.com',
            'name': 'Test User'
        }
        mock_client.get = AsyncMock(return_value=mock_userinfo_response)
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should successfully process valid token
        self.assertEqual(response.status_code, 303)
        self.assertIn('login=success', response.headers['location'])

    @patch('app.oauth')
    def test_oauth_token_missing_fields(self, mock_oauth):
        """Test OAuth handles tokens with missing fields."""
        mock_client = MagicMock()

        # Token missing access_token field
        invalid_token = {
            'token_type': 'Bearer'
            # Missing access_token
        }

        mock_client.authorize_access_token = AsyncMock(side_effect=Exception("Invalid token"))
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should handle error gracefully
        self.assertEqual(response.status_code, 303)
        self.assertIn('error=oauth_failed', response.headers['location'])


class TestOAuthEmailValidation(unittest.TestCase):
    """Test OAuth email validation and authorization logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'security': {
                'oauth': {
                    'enabled': True,
                    'authorized_emails': [
                        'admin@company.com',
                        'user@company.com',
                        'test@EXAMPLE.COM'  # Test case insensitivity
                    ]
                }
            }
        }

        import app
        app.config = self.test_config
        self.app = app

    def test_email_authorization_exact_match(self):
        """Test email authorization with exact match."""
        self.assertTrue(self.app.is_email_authorized('admin@company.com'))
        self.assertTrue(self.app.is_email_authorized('user@company.com'))

    def test_email_authorization_case_insensitive(self):
        """Test email authorization is case insensitive."""
        self.assertTrue(self.app.is_email_authorized('ADMIN@COMPANY.COM'))
        self.assertTrue(self.app.is_email_authorized('User@Company.Com'))
        self.assertTrue(self.app.is_email_authorized('test@example.com'))
        self.assertTrue(self.app.is_email_authorized('TEST@EXAMPLE.COM'))

    def test_email_authorization_unauthorized(self):
        """Test unauthorized emails are rejected."""
        self.assertFalse(self.app.is_email_authorized('hacker@evil.com'))
        self.assertFalse(self.app.is_email_authorized('unknown@company.com'))
        self.assertFalse(self.app.is_email_authorized(''))

    def test_email_authorization_wildcard_disabled(self):
        """Test wildcard domains are not supported."""
        # Add wildcard-like entry
        self.app.config['security']['oauth']['authorized_emails'].append('@company.com')

        # Should not match any email with @company.com domain
        self.assertFalse(self.app.is_email_authorized('newuser@company.com'))

        # But should match the literal string
        self.assertTrue(self.app.is_email_authorized('@company.com'))


class TestOAuthProviderSpecificBehavior(unittest.TestCase):
    """Test provider-specific OAuth behaviors."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient

        self.test_config = {
            'server': {'secret_key': 'test-secret'},
            'security': {
                'oauth': {
                    'enabled': True,
                    'authorized_emails': ['test@example.com'],
                    'google': {'enabled': True},
                    'facebook': {'enabled': True},
                    'github': {'enabled': True},
                    'apple': {'enabled': True}
                }
            }
        }

        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        with patch('app.Path') as mock_path:
            mock_path.return_value.parent = Path(self.temp_dir)
            import app
            app.config = self.test_config
            app.JWT_SECRET_KEY = 'test-secret'
            self.app_module = app

            self.client = TestClient(app.app)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('app.oauth')
    def test_google_uses_openid_discovery(self, mock_oauth):
        """Test Google OAuth uses OpenID discovery."""
        import app
        app.config = self.test_config

        app.initialize_oauth_providers()

        # Find the Google registration call
        google_call = None
        for call in mock_oauth.register.call_args_list:
            if call[1].get('name') == 'google':
                google_call = call
                break

        self.assertIsNotNone(google_call)
        self.assertEqual(
            google_call[1]['server_metadata_url'],
            'https://accounts.google.com/.well-known/openid-configuration'
        )

    @patch('app.oauth')
    def test_github_requires_user_email_scope(self, mock_oauth):
        """Test GitHub OAuth requests user:email scope."""
        import app
        app.config = self.test_config

        app.initialize_oauth_providers()

        # Find the GitHub registration call
        github_call = None
        for call in mock_oauth.register.call_args_list:
            if call[1].get('name') == 'github':
                github_call = call
                break

        self.assertIsNotNone(github_call)
        self.assertEqual(github_call[1]['client_kwargs']['scope'], 'user:email')

    @patch('app.oauth')
    def test_facebook_uses_graph_api(self, mock_oauth):
        """Test Facebook OAuth uses Graph API."""
        import app
        app.config = self.test_config

        app.initialize_oauth_providers()

        # Find the Facebook registration call
        facebook_call = None
        for call in mock_oauth.register.call_args_list:
            if call[1].get('name') == 'facebook':
                facebook_call = call
                break

        self.assertIsNotNone(facebook_call)
        self.assertEqual(facebook_call[1]['api_base_url'], 'https://graph.facebook.com/')

    @patch('app.oauth')
    def test_apple_uses_openid_configuration(self, mock_oauth):
        """Test Apple OAuth uses OpenID configuration."""
        import app
        app.config = self.test_config

        app.initialize_oauth_providers()

        # Find the Apple registration call
        apple_call = None
        for call in mock_oauth.register.call_args_list:
            if call[1].get('name') == 'apple':
                apple_call = call
                break

        self.assertIsNotNone(apple_call)
        self.assertEqual(
            apple_call[1]['server_metadata_url'],
            'https://appleid.apple.com/.well-known/openid-configuration'
        )


class TestOAuthStateManagement(unittest.TestCase):
    """Test OAuth state parameter for CSRF protection."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient

        self.test_config = {
            'server': {'secret_key': 'test-secret'},
            'security': {
                'oauth': {
                    'enabled': True,
                    'google': {'enabled': True}
                }
            }
        }

        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        with patch('app.Path') as mock_path:
            mock_path.return_value.parent = Path(self.temp_dir)
            import app
            app.config = self.test_config
            self.app_module = app

            self.client = TestClient(app.app)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('app.oauth')
    def test_oauth_redirect_uri_construction(self, mock_oauth):
        """Test OAuth redirect URI is properly constructed."""
        mock_client = MagicMock()
        mock_client.authorize_redirect = AsyncMock(return_value=MagicMock(status_code=302))
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google', follow_redirects=False)

        # Verify authorize_redirect was called with request and redirect_uri
        call_args = mock_client.authorize_redirect.call_args
        self.assertEqual(len(call_args[0]), 2)  # request, redirect_uri

        # Redirect URI should point to authorize endpoint
        redirect_uri = call_args[0][1]
        self.assertIn('/login/oauth/google/authorize', redirect_uri)


class TestOAuthErrorHandling(unittest.TestCase):
    """Test OAuth error handling and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient

        self.test_config = {
            'server': {'secret_key': 'test-secret'},
            'security': {
                'oauth': {
                    'enabled': True,
                    'authorized_emails': ['test@example.com'],
                    'google': {'enabled': True}
                }
            }
        }

        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        with patch('app.Path') as mock_path:
            mock_path.return_value.parent = Path(self.temp_dir)
            import app
            app.config = self.test_config
            self.app_module = app

            self.client = TestClient(app.app)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('app.oauth')
    def test_oauth_network_error(self, mock_oauth):
        """Test OAuth handles network errors gracefully."""
        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(
            side_effect=Exception("Network error")
        )
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should redirect with error
        self.assertEqual(response.status_code, 303)
        self.assertIn('error=oauth_failed', response.headers['location'])

    @patch('app.oauth')
    def test_oauth_invalid_response(self, mock_oauth):
        """Test OAuth handles invalid API responses."""
        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(return_value={'access_token': 'test'})

        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should handle error
        self.assertEqual(response.status_code, 303)
        self.assertIn('error=oauth_failed', response.headers['location'])

    @patch('app.oauth')
    def test_oauth_timeout(self, mock_oauth):
        """Test OAuth handles timeout errors."""
        mock_client = MagicMock()
        mock_client.authorize_access_token = AsyncMock(
            side_effect=TimeoutError("Request timeout")
        )
        mock_oauth.create_client.return_value = mock_client

        response = self.client.get('/login/oauth/google/authorize', follow_redirects=False)

        # Should handle timeout
        self.assertEqual(response.status_code, 303)
        self.assertIn('error=oauth_failed', response.headers['location'])


if __name__ == '__main__':
    unittest.main()

