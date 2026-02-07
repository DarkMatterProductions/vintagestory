"""
Comprehensive test suite summary and quick verification.
Runs a subset of tests from each category to verify everything works.
"""
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_quick_verification():
    """Run a quick verification test from each test suite."""
    print("=" * 70)
    print("RUNNING QUICK VERIFICATION TESTS")
    print("=" * 70)
    print("\nThis runs a subset of tests to verify all test suites work correctly.\n")

    # Test classes to verify
    test_classes = [
        'tests.test_authentication.TestPasswordHashing',
        'tests.test_socketio_handlers.TestSocketIOConnection',
        'tests.test_http_routes.TestFastAPIRoutes',
        'tests.test_templates.TestTemplateRendering',
        'tests.test_oauth_complete.TestOAuthEmailValidation'
    ]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_class in test_classes:
        try:
            tests = loader.loadTestsFromName(test_class)
            suite.addTests(tests)
            print(f"[OK] Loaded {test_class.split('.')[-1]}")
        except Exception as e:
            print(f"[FAIL] Failed to load {test_class}: {e}")
            return 1

    print(f"\nRunning {suite.countTestCases()} verification tests...\n")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n[OK] All verification tests passed!")
        print("\nYou can now run the full test suite:")
        print("  python tests/run_tests.py           # All tests")
        print("  python tests/run_tests.py auth      # Authentication tests")
        print("  python tests/run_tests.py socketio  # Socket.IO tests")
        print("  python tests/run_tests.py http      # HTTP route tests")
        print("  python tests/run_tests.py templates # Template tests")
        print("  python tests/run_tests.py oauth     # OAuth tests")
        print("\nOr run with coverage:")
        print("  python tests/run_coverage.py")
    else:
        print("\n[FAIL] Some verification tests failed")
        print("Please check the errors above")

    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_quick_verification()
    sys.exit(exit_code)



