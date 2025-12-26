#!/usr/bin/env python3
"""
Comprehensive test runner for the RAG system
Runs all tests and generates a detailed report
"""

import unittest
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock dependencies before importing test modules
# Mock the openai module
with open("tests/mocks/mock_openai.py", "r") as f:
    mock_code = f.read()
openai = type(sys)('openai')
sys.modules['openai'] = openai
exec(mock_code, openai.__dict__)

# Mock the vector_store module
with open("tests/mocks/mock_vector_store_module.py", "r") as f:
    vector_store_code = f.read()
vector_store = type(sys)('vector_store')
sys.modules['vector_store'] = vector_store
exec(vector_store_code, vector_store.__dict__)

# Mock the document_processor module
with open("tests/mocks/mock_document_processor.py", "r") as f:
    mock_doc_code = f.read()
document_processor = type(sys)('document_processor')
sys.modules['document_processor'] = document_processor
exec(mock_doc_code, document_processor.__dict__)

# Now import all test modules
from tests.test_course_search_tool import TestCourseSearchTool
from tests.test_ai_generator import TestAIGenerator
from tests.test_rag_system import TestRAGSystem
from tests.unit.test_edge_cases import TestEdgeCases
from tests.integration.test_session_management import TestSessionManagement
from tests.integration.test_document_processing import TestDocumentProcessing
from tests.integration.test_real_api_integration import TestRealAPIIntegration
from tests.integration.test_chroma_integration import TestChromaIntegration
from tests.integration.test_end_to_end import TestEndToEnd

def run_all_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCourseSearchTool))
    suite.addTests(loader.loadTestsFromTestCase(TestAIGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestRealAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestChromaIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))

    # Create test runner with verbose output
    runner = unittest.TextTestRunner(verbosity=2)

    # Run tests and capture results
    results = runner.run(suite)

    return results

def generate_test_report(results):
    """Generate a detailed test report"""
    print("\n" + "="*80)
    print("RAG SYSTEM TEST REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test statistics
    print("TEST STATISTICS:")
    print(f"  Tests Run: {results.testsRun}")
    print(f"  Failures: {len(results.failures)}")
    print(f"  Errors: {len(results.errors)}")
    print(f"  Skipped: {len(results.skipped)}")
    print(f"  Success Rate: {((results.testsRun - len(results.failures) - len(results.errors)) / results.testsRun * 100):.1f}%")
    print()

    # Detailed results
    if results.failures:
        print("FAILURES:")
        for i, (test, traceback) in enumerate(results.failures, 1):
            print(f"  {i}. {test}")
            print(f"     {traceback}")
            print()

    if results.errors:
        print("ERRORS:")
        for i, (test, traceback) in enumerate(results.errors, 1):
            print(f"  {i}. {test}")
            print(f"     {traceback}")
            print()

    if results.skipped:
        print("SKIPPED:")
        for i, (test, reason) in enumerate(results.skipped, 1):
            print(f"  {i}. {test} - {reason}")
        print()

    # Summary
    print("SUMMARY:")
    if len(results.failures) == 0 and len(results.errors) == 0:
        print("  ✅ ALL TESTS PASSED - System is working correctly!")
    else:
        print("  ❌ SOME TESTS FAILED - Issues need to be addressed")
        print()
        print("RECOMMENDED ACTIONS:")
        if len(results.failures) > 0:
            print("  • Review and fix test failures")
        if len(results.errors) > 0:
            print("  • Investigate and resolve test errors")
        print("  • Re-run tests after making fixes")
        print("  • Check system logs for detailed error information")

    print("="*80)

def main():
    """Main function to run all tests"""
    print("Starting RAG System Comprehensive Tests...")
    print("This may take a few minutes...")
    print()

    # Run all tests
    results = run_all_tests()

    # Generate report
    generate_test_report(results)

    # Return appropriate exit code
    if len(results.failures) > 0 or len(results.errors) > 0:
        sys.exit(1)  # Non-zero exit code for failures
    else:
        sys.exit(0)  # Zero exit code for success

if __name__ == '__main__':
    main()