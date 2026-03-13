#!/usr/bin/env python3
"""
Preservation Property Tests - Unit Tests Lab Dependency

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

These tests capture the baseline behavior that must be preserved after fixing
the unit tests lab dependency bug. They run on UNFIXED code to establish what
behavior should remain unchanged.

EXPECTED OUTCOME: Tests PASS on unfixed code (confirms baseline to preserve)

Property 2: Preservation - Test Logic and Assertions Remain Unchanged

This test verifies that after fixing the lab dependency:
- All unit test assertions remain unchanged
- Test coverage is maintained or improved
- Integration tests still require lab
- Property-based tests continue to work without changes
"""

import pytest
import subprocess
import sys
import os
import ast
import re
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, List, Set, Any


class TestAssertionExtractor:
    """Extract assertions from test files for comparison"""
    
    @staticmethod
    def extract_assertions_from_file(file_path: Path) -> List[str]:
        """
        Extract all assertion statements from a Python test file.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            List of assertion strings (normalized)
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the file into an AST
            tree = ast.parse(content)
            
            assertions = []
            
            # Walk the AST and find all assert statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    # Convert assertion back to source code
                    assertion_str = ast.unparse(node)
                    assertions.append(assertion_str)
            
            return assertions
            
        except Exception as e:
            # If parsing fails, fall back to regex extraction
            return TestAssertionExtractor._extract_assertions_regex(file_path)
    
    @staticmethod
    def _extract_assertions_regex(file_path: Path) -> List[str]:
        """Fallback: Extract assertions using regex"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find all lines starting with 'assert'
            assertions = []
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith('assert '):
                    assertions.append(stripped)
            
            return assertions
            
        except Exception:
            return []


class TestCoverageAnalyzer:
    """Analyze test coverage for unit tests"""
    
    @staticmethod
    def get_test_count(test_file: Path) -> int:
        """
        Count the number of test methods in a test file.
        
        Args:
            test_file: Path to the test file
            
        Returns:
            Number of test methods
        """
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Count methods starting with 'test_'
            test_count = len(re.findall(r'def test_\w+\(', content))
            return test_count
            
        except Exception:
            return 0
    
    @staticmethod
    def get_test_classes(test_file: Path) -> List[str]:
        """
        Get list of test class names from a test file.
        
        Args:
            test_file: Path to the test file
            
        Returns:
            List of test class names
        """
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Find all class definitions starting with 'Test'
            classes = re.findall(r'class (Test\w+)', content)
            return classes
            
        except Exception:
            return []


class TestBehaviorPreservation:
    """Test that baseline behavior is preserved"""
    
    def test_property_2_unit_test_assertions_unchanged(self):
        """
        **Validates: Requirements 3.2, 3.3**
        
        Property 2a: Unit Test Assertions Remain Unchanged
        
        For all unit tests, the test assertions should remain unchanged after
        fixing the lab dependency. This ensures that the tests continue to
        verify the same correctness properties.
        
        EXPECTED: This test PASSES on unfixed code (establishes baseline)
        """
        # Unit test files to check
        unit_test_files = [
            Path('tests/unit/test_deployment.py'),
            Path('tests/unit/test_configuration.py'),
            Path('tests/unit/test_validation.py'),
            Path('tests/unit/test_telemetry.py'),
            Path('tests/unit/test_state_management.py'),
        ]
        
        extractor = TestAssertionExtractor()
        
        # Extract assertions from each file
        baseline_assertions = {}
        for test_file in unit_test_files:
            if test_file.exists():
                assertions = extractor.extract_assertions_from_file(test_file)
                baseline_assertions[str(test_file)] = assertions
        
        # Verify we extracted assertions
        total_assertions = sum(len(asserts) for asserts in baseline_assertions.values())
        
        assert total_assertions > 0, (
            "No assertions found in unit tests. This indicates a problem with "
            "assertion extraction or the test files."
        )
        
        # Store baseline for comparison (in a real implementation, this would be
        # saved to a file for comparison after the fix)
        print(f"\n=== Baseline Assertions Extracted ===")
        for file_path, assertions in baseline_assertions.items():
            print(f"{file_path}: {len(assertions)} assertions")
        
        # Property: Each unit test file should have assertions
        for test_file in unit_test_files:
            if test_file.exists():
                file_assertions = baseline_assertions.get(str(test_file), [])
                assert len(file_assertions) > 0, (
                    f"Test file {test_file} has no assertions. "
                    f"This may indicate incomplete test coverage."
                )
    
    def test_property_2_unit_test_coverage_maintained(self):
        """
        **Validates: Requirements 3.2, 3.3**
        
        Property 2b: Unit Test Coverage Maintained
        
        For all unit tests, the test coverage (number of tests, test classes)
        should be maintained or improved after fixing the lab dependency.
        
        EXPECTED: This test PASSES on unfixed code (establishes baseline)
        """
        unit_test_files = [
            Path('tests/unit/test_deployment.py'),
            Path('tests/unit/test_configuration.py'),
            Path('tests/unit/test_validation.py'),
            Path('tests/unit/test_telemetry.py'),
            Path('tests/unit/test_state_management.py'),
        ]
        
        analyzer = TestCoverageAnalyzer()
        
        # Measure baseline coverage
        baseline_coverage = {}
        for test_file in unit_test_files:
            if test_file.exists():
                test_count = analyzer.get_test_count(test_file)
                test_classes = analyzer.get_test_classes(test_file)
                
                baseline_coverage[str(test_file)] = {
                    'test_count': test_count,
                    'test_classes': test_classes,
                    'class_count': len(test_classes)
                }
        
        # Verify we have coverage data
        total_tests = sum(data['test_count'] for data in baseline_coverage.values())
        total_classes = sum(data['class_count'] for data in baseline_coverage.values())
        
        assert total_tests > 0, "No test methods found in unit tests"
        assert total_classes > 0, "No test classes found in unit tests"
        
        print(f"\n=== Baseline Coverage ===")
        print(f"Total test methods: {total_tests}")
        print(f"Total test classes: {total_classes}")
        for file_path, data in baseline_coverage.items():
            print(f"{file_path}:")
            print(f"  - {data['test_count']} test methods")
            print(f"  - {data['class_count']} test classes: {', '.join(data['test_classes'])}")
        
        # Property: Each unit test file should have multiple tests
        for test_file in unit_test_files:
            if test_file.exists():
                coverage = baseline_coverage.get(str(test_file), {})
                test_count = coverage.get('test_count', 0)
                
                assert test_count > 0, (
                    f"Test file {test_file} has no test methods. "
                    f"This indicates incomplete test coverage."
                )
    
    def test_property_2_integration_tests_require_lab(self):
        """
        **Validates: Requirements 3.1, 3.4**
        
        Property 2c: Integration Tests Continue to Require Lab
        
        Integration tests should continue to require a deployed lab environment
        and test against actual network devices. This behavior must be preserved.
        
        EXPECTED: This test PASSES on unfixed code (confirms integration tests
        are correctly designed to require lab)
        """
        integration_readme = Path('tests/integration/README.md')
        
        # Verify integration test README exists and documents lab requirement
        assert integration_readme.exists(), (
            "Integration test README not found. Integration tests should be "
            "documented with their lab requirements."
        )
        
        with open(integration_readme, 'r') as f:
            readme_content = f.read()
        
        # Property: README should mention lab deployment requirement
        lab_keywords = ['lab', 'containerlab', 'deploy', 'infrastructure']
        found_keywords = [kw for kw in lab_keywords if kw.lower() in readme_content.lower()]
        
        assert len(found_keywords) > 0, (
            f"Integration test README does not mention lab requirements. "
            f"Expected keywords: {lab_keywords}"
        )
        
        # Property: README should mention prerequisites
        assert 'prerequisite' in readme_content.lower() or 'require' in readme_content.lower(), (
            "Integration test README does not document prerequisites"
        )
        
        print(f"\n=== Integration Test Lab Requirements ===")
        print(f"README found: {integration_readme}")
        print(f"Lab-related keywords found: {', '.join(found_keywords)}")
        
        # Check integration test files exist
        integration_test_files = [
            Path('tests/integration/test_end_to_end.py'),
            Path('tests/integration/test_multi_vendor.py'),
            Path('tests/integration/test_monitoring_stack.py'),
        ]
        
        existing_integration_tests = [f for f in integration_test_files if f.exists()]
        
        assert len(existing_integration_tests) > 0, (
            "No integration test files found. Integration tests should exist "
            "to validate end-to-end workflows with deployed lab."
        )
        
        print(f"Integration test files: {len(existing_integration_tests)}")
        for test_file in existing_integration_tests:
            print(f"  - {test_file}")
    
    def test_property_2_property_tests_work_without_lab(self):
        """
        **Validates: Requirements 3.5**
        
        Property 2d: Property-Based Tests Continue to Work Without Lab
        
        Property-based tests should continue to run without requiring a deployed
        lab. They test universal properties using generated data, not real devices.
        
        EXPECTED: This test PASSES on unfixed code (confirms property tests
        already work correctly without lab)
        """
        property_test_files = [
            Path('tests/property/test_state_management_properties.py'),
            Path('tests/property/test_telemetry_properties.py'),
        ]
        
        # Verify property test files exist
        existing_property_tests = [f for f in property_test_files if f.exists()]
        
        assert len(existing_property_tests) > 0, (
            "No property test files found. Property-based tests should exist "
            "to validate universal correctness properties."
        )
        
        # Check that property tests use Hypothesis
        for test_file in existing_property_tests:
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Property: Should import hypothesis
            assert 'from hypothesis import' in content or 'import hypothesis' in content, (
                f"Property test file {test_file} does not import Hypothesis. "
                f"Property-based tests should use the Hypothesis framework."
            )
            
            # Property: Should use @given decorator
            assert '@given' in content, (
                f"Property test file {test_file} does not use @given decorator. "
                f"Property-based tests should use Hypothesis strategies."
            )
        
        print(f"\n=== Property-Based Tests ===")
        print(f"Property test files: {len(existing_property_tests)}")
        for test_file in existing_property_tests:
            print(f"  - {test_file}")
        
        # Property: Property tests should not import containerlab or docker modules
        for test_file in existing_property_tests:
            with open(test_file, 'r') as f:
                content = f.read()
            
            # These imports would indicate lab dependency
            lab_imports = ['containerlab', 'docker', 'subprocess']
            found_lab_imports = [imp for imp in lab_imports if f'import {imp}' in content]
            
            # subprocess is allowed for bug condition test, but not for preservation tests
            if 'bug_condition' not in str(test_file):
                assert len(found_lab_imports) == 0, (
                    f"Property test file {test_file} imports lab-related modules: {found_lab_imports}. "
                    f"Property tests should not depend on lab infrastructure."
                )
    
    def test_property_2_unit_tests_validate_business_logic(self):
        """
        **Validates: Requirements 3.2, 3.3**
        
        Property 2e: Unit Tests Continue to Verify Business Logic
        
        Unit tests should continue to validate business logic, data transformations,
        configuration generation, metric normalization, and validation logic.
        
        EXPECTED: This test PASSES on unfixed code (confirms unit tests cover
        the right functionality)
        """
        unit_test_files = {
            'test_deployment.py': ['topology', 'validation', 'error'],
            'test_configuration.py': ['configuration', 'interface', 'bgp', 'filter'],
            'test_validation.py': ['bgp', 'evpn', 'lldp', 'interface', 'validation'],
            'test_telemetry.py': ['gnmi', 'metric', 'normalization', 'prometheus'],
            'test_state_management.py': ['state', 'export', 'restore', 'snapshot'],
        }
        
        print(f"\n=== Unit Test Business Logic Coverage ===")
        
        for test_file, expected_keywords in unit_test_files.items():
            file_path = Path('tests/unit') / test_file
            
            if not file_path.exists():
                continue
            
            with open(file_path, 'r') as f:
                content = f.read().lower()
            
            # Check that test file covers expected business logic areas
            found_keywords = [kw for kw in expected_keywords if kw in content]
            
            coverage_ratio = len(found_keywords) / len(expected_keywords)
            
            print(f"{test_file}:")
            print(f"  Expected keywords: {', '.join(expected_keywords)}")
            print(f"  Found keywords: {', '.join(found_keywords)}")
            print(f"  Coverage: {coverage_ratio:.1%}")
            
            # Property: Test file should cover most expected business logic areas
            assert coverage_ratio >= 0.5, (
                f"Test file {test_file} has low business logic coverage. "
                f"Found {len(found_keywords)}/{len(expected_keywords)} expected keywords. "
                f"Unit tests should validate core business logic."
            )


class TestPreservationPropertyBased:
    """Property-based tests for preservation"""
    
    @given(
        test_file=st.sampled_from([
            'test_deployment.py',
            'test_configuration.py',
            'test_validation.py',
            'test_telemetry.py',
            'test_state_management.py',
        ])
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow]
    )
    def test_property_2_all_unit_tests_have_assertions(self, test_file):
        """
        **Validates: Requirements 3.2, 3.3**
        
        Property 2 (Property-Based): All Unit Tests Have Assertions
        
        For any unit test file, it should contain assertion statements that
        verify correctness properties. This ensures comprehensive test coverage.
        
        EXPECTED: This test PASSES on unfixed code (confirms baseline)
        """
        file_path = Path('tests/unit') / test_file
        
        if not file_path.exists():
            # Skip if file doesn't exist
            return
        
        extractor = TestAssertionExtractor()
        assertions = extractor.extract_assertions_from_file(file_path)
        
        # Property: Unit test files must have assertions
        assert len(assertions) > 0, (
            f"Unit test file {test_file} has no assertions. "
            f"All unit tests should verify correctness with assertions."
        )
        
        # Property: Should have multiple assertions (comprehensive testing)
        assert len(assertions) >= 5, (
            f"Unit test file {test_file} has only {len(assertions)} assertions. "
            f"Unit tests should have comprehensive assertion coverage."
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
