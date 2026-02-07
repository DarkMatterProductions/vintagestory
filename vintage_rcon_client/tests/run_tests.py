"""
Test runner script for all unit tests.
Executes all test suites and generates coverage report.
"""
import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """Discover and run all unit tests."""
    # Get the tests directory
    tests_dir = Path(__file__).parent

    # Create test loader
    loader = unittest.TestLoader()

    # Discover all tests - use parent directory as start to avoid import issues
    suite = loader.discover(
        start_dir=str(tests_dir),
        pattern='test_*.py',
        top_level_dir=None
    )

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


def run_specific_test_suite(suite_name):
    """Run a specific test suite."""
    tests_dir = Path(__file__).parent

    # Map suite names to test files
    test_files = {
        'auth': 'test_authentication.py',
        'socketio': 'test_socketio_handlers.py',
        'http': 'test_http_routes.py',
        'templates': 'test_templates.py',
        'oauth': 'test_oauth_complete.py'
    }

    if suite_name not in test_files:
        print(f"Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(test_files.keys())}")
        return 1

    # Load the specific test module
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(tests_dir),
        pattern=test_files[suite_name],
        top_level_dir=None
    )

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    # Check for command line arguments
    if len(sys.argv) > 1:
        suite_name = sys.argv[1]
        exit_code = run_specific_test_suite(suite_name)
    else:
        exit_code = run_all_tests()

    sys.exit(exit_code)



