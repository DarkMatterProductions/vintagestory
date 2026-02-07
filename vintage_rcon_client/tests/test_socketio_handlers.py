"""
Unit tests for Socket.IO event handlers.
Tests cover connection, disconnection, authentication, and RCON command execution.
All external dependencies are mocked.
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock, call
from datetime import datetime
from pathlib import Path
import sys
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSocketIOConnection(unittest.TestCase):
    """Test Socket.IO connection and disconnection handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'server': {'secret_key': 'test-secret'},
            'security': {'require_auth': True}
        }

        import app
        app.config = self.test_config
        app.JWT_SECRET_KEY = 'test-secret'
        self.app = app

        # Mock Socket.IO server with async emit
        self.mock_sio = MagicMock()
        self.mock_sio.emit = AsyncMock()
        self.app.sio = self.mock_sio

    def test_connect_without_token(self):
        """Test connection without authentication token."""
        sid = "test-session-id"
        environ = {'QUERY_STRING': ''}

        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.connect(sid, environ)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify connected event was emitted
        self.mock_sio.emit.assert_called_once()
        call_args = self.mock_sio.emit.call_args
        self.assertEqual(call_args[0][0], 'connected')

    def test_connect_with_valid_token(self):
        """Test connection with valid authentication token."""
        # Create a valid token
        test_data = {
            "sub": "test@example.com",
            "name": "Test User",
            "provider": "test"
        }
        token = self.app.create_access_token(test_data)

        sid = "test-session-id"
        environ = {
            'QUERY_STRING': f'token={token}'
        }

        # Mock session context manager
        mock_session = {}
        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.connect(sid, environ)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify session was updated with user info
        self.assertEqual(mock_session.get('authenticated'), True)
        self.assertEqual(mock_session.get('username'), 'test@example.com')
        self.assertEqual(mock_session.get('display_name'), 'Test User')

    def test_connect_with_invalid_token(self):
        """Test connection with invalid authentication token."""
        sid = "test-session-id"
        environ = {
            'QUERY_STRING': 'token=invalid.token.here'
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.connect(sid, environ)

        loop.run_until_complete(run_test())
        loop.close()

        # Connection should succeed but not be authenticated
        self.mock_sio.emit.assert_called_once()

    def test_disconnect(self):
        """Test disconnection handler logs properly."""
        sid = "test-session-id"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            with patch('app.logger') as mock_logger:
                await self.app.disconnect(sid)
                mock_logger.info.assert_called()

        loop.run_until_complete(run_test())
        loop.close()


class TestSocketIOLogin(unittest.TestCase):
    """Test Socket.IO login handler for traditional authentication."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'server': {'secret_key': 'test-secret'},
            'security': {
                'require_auth': True,
                'default_username': 'admin',
                'default_password': 'testpass',
                'max_login_attempts': 3,
                'lockout_duration': 300
            }
        }

        import app
        app.config = self.test_config
        app.JWT_SECRET_KEY = 'test-secret'
        app.login_attempts = {}
        app.lockouts = {}
        self.app = app

        self.mock_sio = MagicMock()
        self.mock_sio.emit = AsyncMock()
        self.app.sio = self.mock_sio

    def test_login_success(self):
        """Test successful login with correct credentials."""
        sid = "test-session-id"
        data = {
            'username': 'admin',
            'password': 'testpass'
        }

        # Mock session
        mock_session = {}
        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_login(sid, data)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify success response was emitted
        emit_call = self.mock_sio.emit.call_args
        self.assertEqual(emit_call[0][0], 'login_response')
        response_data = emit_call[0][1]
        self.assertTrue(response_data['success'])
        self.assertIn('token', response_data)

        # Verify session was updated
        self.assertTrue(mock_session.get('authenticated'))
        self.assertEqual(mock_session.get('username'), 'admin')

    def test_login_failure(self):
        """Test login failure with incorrect credentials."""
        sid = "test-session-id"
        data = {
            'username': 'admin',
            'password': 'wrongpassword'
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_login(sid, data)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify failure response was emitted
        emit_call = self.mock_sio.emit.call_args
        self.assertEqual(emit_call[0][0], 'login_response')
        response_data = emit_call[0][1]
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid username or password', response_data['message'])

    def test_login_locked_out(self):
        """Test login when IP is locked out."""
        sid = "test-session-id"
        data = {
            'username': 'admin',
            'password': 'testpass'
        }

        # Set active lockout
        self.app.lockouts['unknown'] = datetime.now() + self.app.timedelta(seconds=300)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_login(sid, data)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify lockout response was emitted
        emit_call = self.mock_sio.emit.call_args
        response_data = emit_call[0][1]
        self.assertFalse(response_data['success'])
        self.assertIn('Too many failed login attempts', response_data['message'])


class TestSocketIOAuthCheck(unittest.TestCase):
    """Test Socket.IO authentication status check handler."""

    def setUp(self):
        """Set up test fixtures."""
        import app
        self.app = app

        self.mock_sio = MagicMock()
        self.mock_sio.emit = AsyncMock()
        self.app.sio = self.mock_sio

    def test_check_auth_authenticated(self):
        """Test auth check for authenticated session."""
        sid = "test-session-id"
        mock_session = {
            'authenticated': True,
            'username': 'test@example.com',
            'display_name': 'Test User',
            'oauth_provider': 'google'
        }

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_check_auth(sid)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify auth_status was emitted with user data
        emit_call = self.mock_sio.emit.call_args
        self.assertEqual(emit_call[0][0], 'auth_status')
        response_data = emit_call[0][1]
        self.assertTrue(response_data['authenticated'])
        self.assertEqual(response_data['username'], 'test@example.com')
        self.assertEqual(response_data['display_name'], 'Test User')
        self.assertEqual(response_data['oauth_provider'], 'google')

    def test_check_auth_not_authenticated(self):
        """Test auth check for non-authenticated session."""
        sid = "test-session-id"
        mock_session = {}

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_check_auth(sid)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify auth_status was emitted with not authenticated
        emit_call = self.mock_sio.emit.call_args
        response_data = emit_call[0][1]
        self.assertFalse(response_data['authenticated'])


class TestSocketIOLogout(unittest.TestCase):
    """Test Socket.IO logout handler."""

    def setUp(self):
        """Set up test fixtures."""
        import app
        self.app = app

        self.mock_sio = MagicMock()
        self.mock_sio.emit = AsyncMock()
        self.app.sio = self.mock_sio

    def test_logout(self):
        """Test logout handler sends proper response."""
        sid = "test-session-id"
        mock_session = {
            'username': 'test@example.com',
            'oauth_provider': 'google'
        }

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_logout(sid)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify logout_response was emitted
        emit_call = self.mock_sio.emit.call_args
        self.assertEqual(emit_call[0][0], 'logout_response')
        response_data = emit_call[0][1]
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['redirect'], '/logout')


class TestSocketIORconCommands(unittest.TestCase):
    """Test Socket.IO RCON connection and command handlers."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'security': {'require_auth': True},
            'rcon': {
                'default_host': 'localhost',
                'default_port': 42425,
                'password': 'testpass',
                'locked_address': False
            },
            'logging': {
                'log_commands': True,
                'log_file': None
            }
        }

        import app
        app.config = self.test_config
        self.app = app

        self.mock_sio = MagicMock()
        self.mock_sio.emit = AsyncMock()
        self.app.sio = self.mock_sio

    @patch('app.rcon')
    def test_rcon_connect_success(self, mock_rcon):
        """Test successful RCON connection."""
        mock_rcon.return_value = AsyncMock(return_value="Server status OK")

        sid = "test-session-id"
        data = {
            'host': 'localhost',
            'port': 42425,
            'password': 'testpass'
        }

        mock_session = {
            'authenticated': True,
            'username': 'test@example.com'
        }

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_rcon_connect(sid, data)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify success response
        emit_call = self.mock_sio.emit.call_args
        self.assertEqual(emit_call[0][0], 'rcon_response')
        response_data = emit_call[0][1]
        self.assertTrue(response_data['success'])

        # Verify session was updated
        self.assertTrue(mock_session.get('rcon_connected'))
        self.assertEqual(mock_session.get('rcon_host'), 'localhost')

    def test_rcon_connect_requires_auth(self):
        """Test RCON connection requires authentication."""
        sid = "test-session-id"
        data = {
            'host': 'localhost',
            'port': 42425,
            'password': 'testpass'
        }

        mock_session = {}  # Not authenticated

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_rcon_connect(sid, data)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify auth required response
        emit_call = self.mock_sio.emit.call_args
        response_data = emit_call[0][1]
        self.assertFalse(response_data['success'])
        self.assertIn('Authentication required', response_data['message'])

    @patch('app.rcon', new_callable=AsyncMock)
    def test_rcon_command_execution(self, mock_rcon):
        """Test successful RCON command execution."""
        mock_rcon.return_value = "Command executed successfully"

        sid = "test-session-id"
        data = {'command': 'status'}

        mock_session = {
            'authenticated': True,
            'username': 'test@example.com',
            'rcon_connected': True,
            'rcon_host': 'localhost',
            'rcon_port': 42425,
            'rcon_password': 'testpass'
        }

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_rcon_command(sid, data)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify command response
        emit_call = self.mock_sio.emit.call_args
        self.assertEqual(emit_call[0][0], 'command_response')
        response_data = emit_call[0][1]
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['command'], 'status')

    def test_rcon_command_requires_connection(self):
        """Test RCON command requires active connection."""
        sid = "test-session-id"
        data = {'command': 'status'}

        mock_session = {
            'authenticated': True,
            'rcon_connected': False  # Not connected
        }

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_rcon_command(sid, data)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify connection required response
        emit_call = self.mock_sio.emit.call_args
        response_data = emit_call[0][1]
        self.assertFalse(response_data['success'])
        self.assertIn('Not connected', response_data['message'])

    def test_rcon_disconnect(self):
        """Test RCON disconnection clears session data."""
        sid = "test-session-id"

        mock_session = {
            'rcon_connected': True,
            'rcon_host': 'localhost',
            'rcon_port': 42425,
            'rcon_password': 'testpass'
        }

        mock_session_context = MagicMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)
        self.mock_sio.session.return_value = mock_session_context

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_test():
            await self.app.handle_rcon_disconnect(sid)

        loop.run_until_complete(run_test())
        loop.close()

        # Verify session data was cleared
        self.assertNotIn('rcon_host', mock_session)
        self.assertNotIn('rcon_port', mock_session)
        self.assertNotIn('rcon_password', mock_session)
        self.assertNotIn('rcon_connected', mock_session)


if __name__ == '__main__':
    unittest.main()






