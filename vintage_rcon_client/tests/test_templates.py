"""
Unit tests for Jinja2 template rendering and validation.
Tests ensure templates are constructed with expected context and logic results.
"""
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import tempfile
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTemplateRendering(unittest.TestCase):
    """Test Jinja2 template rendering with various contexts."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient
        from jinja2 import Environment, FileSystemLoader

        self.test_config = {
            'server': {'secret_key': 'test-secret'},
            'security': {
                'require_auth': True,
                'traditional_login_enabled': True,
                'oauth': {
                    'enabled': True,
                    'google': {'enabled': True},
                    'facebook': {'enabled': False}
                }
            },
            'rcon': {
                'default_host': 'localhost',
                'default_port': 42425,
                'locked_address': False
            }
        }

        # Create temp config
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'config.yaml'
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        with patch('app.Path') as mock_path:
            # Point to actual templates directory
            templates_dir = Path(__file__).parent.parent / 'templates'
            mock_path.return_value.parent = Path(self.temp_dir)

            import app
            app.config = self.test_config
            app.JWT_SECRET_KEY = 'test-secret'
            self.app_module = app

            # Create Jinja2 environment for testing
            self.jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))

            self.client = TestClient(app.app)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_index_template_renders(self):
        """Test index.html template renders without errors."""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Vintage Story RCon Web Client', response.text)

    def test_index_template_contains_login_form(self):
        """Test index template contains login form elements."""
        response = self.client.get('/')

        self.assertIn('login-form', response.text)
        self.assertIn('id="username"', response.text)
        self.assertIn('id="password"', response.text)
        self.assertIn('type="submit"', response.text)

    def test_index_template_contains_oauth_section(self):
        """Test index template contains OAuth login section."""
        response = self.client.get('/')

        self.assertIn('oauth-buttons', response.text)
        self.assertIn('google-login-btn', response.text)
        self.assertIn('facebook-login-btn', response.text)
        self.assertIn('github-login-btn', response.text)
        self.assertIn('apple-login-btn', response.text)

    def test_index_template_contains_rcon_connection_panel(self):
        """Test index template contains RCON connection panel."""
        response = self.client.get('/')

        self.assertIn('connection-panel', response.text)
        self.assertIn('id="rcon-host"', response.text)
        self.assertIn('id="rcon-port"', response.text)
        self.assertIn('id="rcon-password"', response.text)
        self.assertIn('id="connect-btn"', response.text)

    def test_index_template_contains_console_panel(self):
        """Test index template contains console panel."""
        response = self.client.get('/')

        self.assertIn('console-panel', response.text)
        self.assertIn('id="console-output"', response.text)
        self.assertIn('id="command-input"', response.text)
        self.assertIn('id="send-btn"', response.text)

    def test_index_template_contains_logout_button(self):
        """Test index template contains logout button."""
        response = self.client.get('/')

        self.assertIn('id="logout-btn"', response.text)
        self.assertIn('Logout', response.text)

    def test_index_template_structure(self):
        """Test index template has proper HTML structure."""
        response = self.client.get('/')

        # Check for proper HTML structure
        self.assertIn('<!DOCTYPE html>', response.text)
        self.assertIn('<html', response.text)
        self.assertIn('<head>', response.text)
        self.assertIn('<body>', response.text)
        self.assertIn('</body>', response.text)
        self.assertIn('</html>', response.text)

    def test_index_template_includes_css(self):
        """Test index template includes CSS stylesheet."""
        response = self.client.get('/')

        self.assertIn('/static/css/style.css', response.text)
        self.assertIn('rel="stylesheet"', response.text)

    def test_index_template_includes_javascript(self):
        """Test index template includes JavaScript file."""
        # Read the template file directly
        templates_dir = Path(__file__).parent.parent / 'templates'
        index_path = templates_dir / 'index.html'

        with open(index_path) as f:
            content = f.read()

        # Check for script tag (could be inline or external)
        self.assertTrue(
            '<script' in content,
            "Template should include script tags"
        )

    def test_test_config_template_renders(self):
        """Test test_config.html template renders without errors."""
        response = self.client.get('/test-config')

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers['content-type'])


class TestTemplateContextVariables(unittest.TestCase):
    """Test that templates receive and use correct context variables."""

    def setUp(self):
        """Set up test fixtures."""
        from jinja2 import Environment, DictLoader

        # Create simple test templates
        self.test_templates = {
            'test_request.html': '{{ request.url }}',
            'test_conditional.html': '{% if show_content %}Content{% else %}Hidden{% endif %}',
            'test_loop.html': '{% for item in items %}{{ item }}{% endfor %}',
            'test_variable.html': '{{ title }}'
        }

        self.jinja_env = Environment(loader=DictLoader(self.test_templates))

    def test_template_receives_request_context(self):
        """Test template receives request context variable."""
        from fastapi import Request

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url = "http://testserver/"

        template = self.jinja_env.get_template('test_request.html')
        result = template.render(request=mock_request)

        self.assertEqual(result, "http://testserver/")

    def test_template_conditional_logic_true(self):
        """Test template conditional logic with true condition."""
        template = self.jinja_env.get_template('test_conditional.html')
        result = template.render(show_content=True)

        self.assertEqual(result, 'Content')

    def test_template_conditional_logic_false(self):
        """Test template conditional logic with false condition."""
        template = self.jinja_env.get_template('test_conditional.html')
        result = template.render(show_content=False)

        self.assertEqual(result, 'Hidden')

    def test_template_loop_logic(self):
        """Test template loop logic with list of items."""
        template = self.jinja_env.get_template('test_loop.html')
        result = template.render(items=['A', 'B', 'C'])

        self.assertEqual(result, 'ABC')

    def test_template_loop_logic_empty(self):
        """Test template loop logic with empty list."""
        template = self.jinja_env.get_template('test_loop.html')
        result = template.render(items=[])

        self.assertEqual(result, '')

    def test_template_variable_substitution(self):
        """Test template variable substitution."""
        template = self.jinja_env.get_template('test_variable.html')
        result = template.render(title='Test Title')

        self.assertEqual(result, 'Test Title')

    def test_template_missing_variable(self):
        """Test template handles missing variables gracefully."""
        template = self.jinja_env.get_template('test_variable.html')
        result = template.render()

        # Jinja2 renders undefined as empty string by default
        self.assertEqual(result, '')


class TestTemplateStaticAssets(unittest.TestCase):
    """Test template references to static assets."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient

        self.test_config = {
            'server': {'secret_key': 'test-secret'}
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

    def test_index_references_css(self):
        """Test index template references CSS files correctly."""
        response = self.client.get('/')

        # Check for CSS reference
        self.assertIn('/static/css/', response.text)

    def test_css_paths_are_absolute(self):
        """Test CSS paths in templates are absolute."""
        response = self.client.get('/')

        # CSS paths should start with /static/
        import re
        css_refs = re.findall(r'href="([^"]*\.css)"', response.text)

        for css_ref in css_refs:
            self.assertTrue(
                css_ref.startswith('/static/') or css_ref.startswith('http'),
                f"CSS path {css_ref} should be absolute"
            )


class TestTemplateFormElements(unittest.TestCase):
    """Test form elements in templates have proper attributes."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient

        self.test_config = {
            'server': {'secret_key': 'test-secret'}
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

    def test_login_form_has_proper_inputs(self):
        """Test login form has properly configured inputs."""
        response = self.client.get('/')

        # Username input
        self.assertIn('type="text"', response.text)
        self.assertIn('name="username"', response.text)

        # Password input
        self.assertIn('type="password"', response.text)
        self.assertIn('name="password"', response.text)

        # Submit button
        self.assertIn('type="submit"', response.text)

    def test_login_form_has_autocomplete(self):
        """Test login form inputs have autocomplete attributes."""
        response = self.client.get('/')

        self.assertIn('autocomplete="username"', response.text)
        self.assertIn('autocomplete="current-password"', response.text)

    def test_rcon_connection_form_has_proper_inputs(self):
        """Test RCON connection form has properly configured inputs."""
        response = self.client.get('/')

        # Host input
        self.assertIn('id="rcon-host"', response.text)
        self.assertIn('name="host"', response.text)

        # Port input
        self.assertIn('id="rcon-port"', response.text)
        self.assertIn('name="port"', response.text)
        self.assertIn('type="number"', response.text)

        # Password input
        self.assertIn('id="rcon-password"', response.text)
        self.assertIn('name="password"', response.text)

    def test_command_form_has_proper_input(self):
        """Test command form has properly configured input."""
        response = self.client.get('/')

        self.assertIn('id="command-input"', response.text)
        self.assertIn('autocomplete="off"', response.text)

    def test_oauth_buttons_have_proper_hrefs(self):
        """Test OAuth buttons have correct href attributes."""
        response = self.client.get('/')

        import re
        oauth_hrefs = re.findall(r'href="/login/oauth/(\w+)"', response.text)

        # Should have OAuth provider links
        self.assertIn('google', oauth_hrefs)
        self.assertIn('facebook', oauth_hrefs)
        self.assertIn('github', oauth_hrefs)
        self.assertIn('apple', oauth_hrefs)


class TestTemplateAccessibility(unittest.TestCase):
    """Test templates follow accessibility best practices."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient

        self.test_config = {
            'server': {'secret_key': 'test-secret'}
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

    def test_template_has_lang_attribute(self):
        """Test HTML tag has lang attribute."""
        response = self.client.get('/')

        self.assertIn('lang=', response.text)

    def test_template_has_meta_charset(self):
        """Test template has meta charset declaration."""
        response = self.client.get('/')

        self.assertIn('<meta charset=', response.text)

    def test_template_has_meta_viewport(self):
        """Test template has meta viewport for responsive design."""
        response = self.client.get('/')

        self.assertIn('name="viewport"', response.text)

    def test_template_has_title(self):
        """Test template has title tag."""
        response = self.client.get('/')

        self.assertIn('<title>', response.text)
        self.assertIn('</title>', response.text)

    def test_form_inputs_have_labels(self):
        """Test form inputs have associated labels."""
        response = self.client.get('/')

        import re
        # Find all input IDs
        input_ids = re.findall(r'<input[^>]*id="([^"]+)"', response.text)

        # Find all label for attributes
        label_fors = re.findall(r'<label[^>]*for="([^"]+)"', response.text)

        # At least some inputs should have labels
        common_ids = set(input_ids) & set(label_fors)
        self.assertGreater(len(common_ids), 0, "Some form inputs should have labels")

    def test_buttons_have_descriptive_text(self):
        """Test buttons have descriptive text content."""
        response = self.client.get('/')

        import re
        buttons = re.findall(r'<button[^>]*>([^<]+)</button>', response.text)

        # All buttons should have non-empty text
        for button_text in buttons:
            self.assertGreater(len(button_text.strip()), 0, "Buttons should have text content")


if __name__ == '__main__':
    unittest.main()

