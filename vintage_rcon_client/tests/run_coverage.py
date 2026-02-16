"""
Coverage-enabled test runner.
Generates code coverage reports for the test suite.
"""
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_tests_with_coverage():
    """Run tests with coverage tracking."""
    try:
        import coverage
    except ImportError:
        print("ERROR: coverage package not installed")
        print("Install with: pip install coverage")
        return 1

    # Start coverage
    cov = coverage.Coverage(
        source=['app'],
        omit=[
            '*/tests/*',
            '*/test_*.py',
            '*/__pycache__/*',
            '*/venv/*',
            '*/virtualenv/*'
        ]
    )
    cov.start()

    # Get the tests directory
    tests_dir = Path(__file__).parent

    # Create test loader and discover tests
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(tests_dir),
        pattern='test_*.py',
        top_level_dir=None
    )

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Stop coverage
    cov.stop()
    cov.save()

    # Print coverage report
    print("\n" + "=" * 70)
    print("COVERAGE REPORT")
    print("=" * 70)
    cov.report()

    # Generate HTML coverage report
    html_dir = tests_dir / 'coverage_html'
    cov.html_report(directory=str(html_dir))
    print(f"\nHTML coverage report generated: {html_dir / 'index.html'}")

    # Generate XML coverage report for CI/CD
    xml_file = tests_dir / 'coverage.xml'
    cov.xml_report(outfile=str(xml_file))
    print(f"XML coverage report generated: {xml_file}")

    # Print test summary
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


if __name__ == '__main__':
    exit_code = run_tests_with_coverage()
    sys.exit(exit_code)


