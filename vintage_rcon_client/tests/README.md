# Unit Test Suite

Comprehensive unit test suite for the Vintage Story RCon Web Client application.

## Overview

This test suite provides complete code coverage for the application, including:

- **Authentication** - JWT tokens, traditional login, password hashing
- **Socket.IO Handlers** - Connection, login, logout, RCON commands
- **HTTP Routes** - FastAPI endpoints, OAuth flows, configuration
- **Template Rendering** - Jinja2 templates, context variables, HTML structure
- **OAuth Integration** - Complete OAuth flow with simulated providers

## Test Organization

Tests are organized into focused test classes using `unittest.TestCase`:

### `test_authentication.py`
- `TestJWTAuthentication` - JWT token creation and verification
- `TestTraditionalLogin` - Username/password authentication
- `TestPasswordHashing` - Password hashing utilities
- `TestOAuthAuthorization` - Email authorization logic
- `TestTokenExtraction` - Token extraction from requests
- `TestOAuthProviderInitialization` - OAuth provider setup

### `test_socketio_handlers.py`
- `TestSocketIOConnection` - Socket.IO connection/disconnection
- `TestSocketIOLogin` - Traditional login via Socket.IO
- `TestSocketIOAuthCheck` - Authentication status checks
- `TestSocketIOLogout` - Logout functionality
- `TestSocketIORconCommands` - RCON command execution

### `test_http_routes.py`
- `TestFastAPIRoutes` - Basic HTTP routes
- `TestOAuthRoutes` - OAuth login and authorization
- `TestConfigLoading` - Configuration loading
- `TestUtilityFunctions` - HTML sanitization, logging

### `test_templates.py`
- `TestTemplateRendering` - Jinja2 template rendering
- `TestTemplateContextVariables` - Template context and logic
- `TestTemplateStaticAssets` - Static asset references
- `TestTemplateFormElements` - Form element validation
- `TestTemplateAccessibility` - Accessibility standards

### `test_oauth_complete.py`
- `TestOAuthFlowSimulation` - Complete OAuth flow
- `TestOAuthEmailValidation` - Email authorization
- `TestOAuthProviderSpecificBehavior` - Provider-specific logic
- `TestOAuthStateManagement` - CSRF protection
- `TestOAuthErrorHandling` - Error handling

## Running Tests

### Run All Tests

```bash
python tests/run_tests.py
```

### Run Specific Test Suite

```bash
python tests/run_tests.py auth        # Authentication tests
python tests/run_tests.py socketio    # Socket.IO tests
python tests/run_tests.py http        # HTTP route tests
python tests/run_tests.py templates   # Template tests
python tests/run_tests.py oauth       # OAuth tests
```

### Run with Coverage

```bash
python tests/run_coverage.py
```

This generates:
- Console coverage report
- HTML coverage report in `tests/coverage_html/`
- XML coverage report in `tests/coverage.xml`

### Run Individual Test File

```bash
python -m unittest tests/test_authentication.py
```

### Run Specific Test Class

```bash
python -m unittest tests.test_authentication.TestJWTAuthentication
```

### Run Specific Test Method

```bash
python -m unittest tests.test_authentication.TestJWTAuthentication.test_create_access_token
```

## Test Dependencies

Install test dependencies:

```bash
pip install -r tests/test_requirements.txt
```

Required packages:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage plugin
- `coverage` - Coverage tracking
- `httpx` - FastAPI test client

## Test Design Principles

### Self-Contained Tests

All tests are completely self-contained:
- No external API calls
- No database connections
- No file system dependencies (except temporary files)
- All external services mocked with `unittest.mock`

### Mocked Dependencies

External dependencies are mocked:
- OAuth providers (Google, Facebook, GitHub, Apple)
- RCON server connections
- Network requests
- File system operations

### Simulated OAuth Certificates

OAuth tests use simulated certificates and tokens:
- Simulated JWT tokens with proper structure
- Simulated OAuth responses from providers
- Simulated user info and email data
- No actual OAuth provider connections

### Template Validation

Template tests validate:
- Templates render without errors
- Expected HTML elements are present
- Context variables are properly used
- Template logic produces expected results
- Forms have proper attributes
- Accessibility standards are followed

## Coverage Goals

The test suite aims for:
- **>90% code coverage** - All critical paths tested
- **100% authentication coverage** - All auth flows verified
- **100% OAuth flow coverage** - Complete OAuth process tested
- **All HTTP routes tested** - Every endpoint verified
- **All Socket.IO handlers tested** - Every event covered
- **Template rendering validated** - All templates checked

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install -r tests/test_requirements.txt

- name: Run tests with coverage
  run: python tests/run_coverage.py

- name: Upload coverage report
  uses: codecov/codecov-action@v3
  with:
    file: ./tests/coverage.xml
```

## Writing New Tests

When adding new tests:

1. **Use `unittest.TestCase`** - Organize tests into classes
2. **Mock external dependencies** - Use `@patch` decorator
3. **Test both success and failure** - Cover error paths
4. **Use descriptive names** - Clear test method names
5. **Add docstrings** - Explain what is being tested
6. **Keep tests isolated** - No shared state between tests
7. **Use setUp/tearDown** - Clean up after tests

Example test structure:

```python
class TestNewFeature(unittest.TestCase):
    """Test description."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize test data
        pass
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up resources
        pass
    
    def test_success_case(self):
        """Test successful execution."""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_failure_case(self):
        """Test failure handling."""
        # Arrange
        # Act
        # Assert
        pass
```

## Troubleshooting

### Import Errors

If you encounter import errors:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/vintage_rcon_client"
```

### Async Test Warnings

For async tests, ensure `pytest-asyncio` is installed:

```bash
pip install pytest-asyncio
```

### Coverage Not Tracking

Ensure coverage is measuring the correct source:

```python
cov = coverage.Coverage(source=['app'])
```

## Test Maintenance

Regular maintenance tasks:

1. **Update tests for new features** - Add tests for new code
2. **Remove obsolete tests** - Clean up tests for removed code
3. **Refactor duplicate code** - Use test fixtures and helpers
4. **Monitor coverage** - Maintain high coverage levels
5. **Review failing tests** - Fix or update as needed

## Support

For issues with tests:

1. Check test output for specific errors
2. Review test documentation
3. Run individual tests to isolate issues
4. Check mock configurations
5. Verify test dependencies are installed

