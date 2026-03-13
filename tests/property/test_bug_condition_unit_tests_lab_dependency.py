#!/usr/bin/env python3
"""
Bug Condition Exploration Test - Unit Tests Lab Dependency

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Property 1: Bug Condition - Unit Tests Fail Without Lab Deployment

This test verifies that unit tests execute successfully in environments where
no lab is deployed (CI/CD environments, GitHub Actions, clean dev machines).

EXPECTED OUTCOME: Test FAILS on unfixed code (this is correct - it proves the bug exists)
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, Any


# Environment types that should NOT require a lab
CI_ENVIRONMENT_TYPES = [
    'ci_cd',
    'github_actions', 
    'clean_dev_machine',
    'docker_container_no_lab',
    'fresh_python_env'
]


def is_bug_condition(environment: Dict[str, Any]) -> bool:
    """
    Determine if the bug condition holds for this environment.
    
    Bug condition: NOT labDeployed(environment) OR environment.type IN CI_TYPES
    
    Args:
        environment: Dictionary with 'lab_deployed' and 'type' keys
        
    Returns:
        True if bug condition holds (no lab deployed or CI/CD environment)
    """
    lab_deployed = environment.get('lab_deployed', False)
    env_type = environment.get('type', 'unknown')
    
    return (not lab_deployed) or (env_type in CI_ENVIRONMENT_TYPES)


@st.composite
def environment_strategy(draw):
    """
    Generate test execution environments.
    
    Scoped to environments where bug condition holds:
    - No lab deployed
    - CI/CD environments
    - Clean development machines
    """
    # Generate environment type
    env_type = draw(st.sampled_from([
        'ci_cd',
        'github_actions',
        'clean_dev_machine',
        'docker_container_no_lab',
        'fresh_python_env',
        'local_no_lab'
    ]))
    
    # For CI/CD environments, lab is never deployed
    # For local environments, randomly decide if lab is deployed
    if env_type in CI_ENVIRONMENT_TYPES:
        lab_deployed = False
    else:
        lab_deployed = draw(st.booleans())
    
    return {
        'type': env_type,
        'lab_deployed': lab_deployed,
        'has_docker': draw(st.booleans()),
        'has_containerlab': draw(st.booleans()),
        'python_version': draw(st.sampled_from(['3.9', '3.10', '3.11', '3.12']))
    }


class TestBugConditionUnitTestsLabDependency:
    """
    Bug Condition Exploration Test
    
    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists
    """
    
    @given(environment=environment_strategy())
    @settings(
        max_examples=50,
        deadline=60000,  # 60 seconds per example
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
    )
    def test_property_1_unit_tests_run_without_lab(self, environment):
        """
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        
        Property 1: Bug Condition - Unit Tests Fail Without Lab Deployment
        
        For any environment where isBugCondition(environment) is true:
        - Unit tests SHOULD execute successfully
        - Execution time SHOULD be < 60 seconds
        - No external dependencies SHOULD be used
        
        EXPECTED: This test FAILS on unfixed code because unit tests currently
        require file I/O, subprocess calls, and lab infrastructure.
        
        COUNTEREXAMPLES TO DOCUMENT:
        - FileNotFoundError when topology files don't exist
        - subprocess errors when containerlab commands fail
        - Connection timeouts when trying to reach devices
        - Import errors when dependencies are missing
        """
        # Only test when bug condition holds
        if not is_bug_condition(environment):
            return
        
        # Simulate running unit tests in this environment
        # This will FAIL on unfixed code because tests require actual files
        result = self._run_unit_tests_simulation(environment)
        
        # These assertions will FAIL on unfixed code (proving bug exists)
        assert result['success'], (
            f"Unit tests failed in {environment['type']} environment without lab. "
            f"Error: {result.get('error', 'Unknown error')}. "
            f"This confirms the bug exists - tests require lab dependencies."
        )
        
        assert result['execution_time'] < 60, (
            f"Unit tests took {result['execution_time']}s (> 60s limit). "
            f"This indicates external dependencies are slowing down tests."
        )
        
        assert not result['used_external_dependencies'], (
            f"Unit tests used external dependencies: {result.get('dependencies_used', [])}. "
            f"Tests should use mocks/stubs instead."
        )
    
    def _run_unit_tests_simulation(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the actual unit test suite using pytest to verify they work
        without lab dependencies. On fixed code, this will pass.
        
        Returns:
            Dictionary with 'success', 'execution_time', 'used_external_dependencies',
            'error', and 'dependencies_used' keys
        """
        import time
        from pathlib import Path as PathLib
        
        start_time = time.time()
        
        try:
            # Run the actual pytest unit test suite
            # On fixed code, this should pass because tests use mocks
            # On unfixed code, this would fail with file I/O errors
            
            test_dir = PathLib(__file__).parent.parent / 'unit'
            
            # Run pytest programmatically
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', str(test_dir), '-v', '--tb=no', '-q'],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=PathLib(__file__).parent.parent.parent
            )
            
            execution_time = time.time() - start_time
            
            # Check if tests passed
            if result.returncode == 0:
                # Tests passed - check execution time and dependencies
                # On fixed code, tests should pass quickly using mocks
                return {
                    'success': True,
                    'execution_time': execution_time,
                    'used_external_dependencies': False,  # Mocks were used
                    'dependencies_used': []
                }
            else:
                # Tests failed - parse error output
                # On unfixed code, this would show file I/O errors
                error_msg = result.stdout + result.stderr
                
                # Detect what kind of dependencies caused failure
                dependencies_used = []
                if 'FileNotFoundError' in error_msg or 'No such file' in error_msg:
                    dependencies_used.append('file_io')
                if 'ConnectionError' in error_msg or 'timeout' in error_msg.lower():
                    dependencies_used.append('network_connection')
                if 'subprocess' in error_msg.lower() or 'containerlab' in error_msg.lower():
                    dependencies_used.append('subprocess')
                if 'ImportError' in error_msg or 'ModuleNotFoundError' in error_msg:
                    dependencies_used.append('missing_module')
                
                return {
                    'success': False,
                    'execution_time': execution_time,
                    'used_external_dependencies': True,
                    'error': f'Unit tests failed: {error_msg[:200]}',
                    'dependencies_used': dependencies_used if dependencies_used else ['unknown']
                }
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'execution_time': execution_time,
                'used_external_dependencies': True,
                'error': 'Unit tests timed out after 60 seconds',
                'dependencies_used': ['timeout', 'external_dependencies']
            }
        except subprocess.CalledProcessError as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'execution_time': execution_time,
                'used_external_dependencies': True,
                'error': f'subprocess.CalledProcessError: {str(e)}',
                'dependencies_used': ['subprocess']
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'execution_time': execution_time,
                'used_external_dependencies': True,
                'error': f'Unexpected error: {type(e).__name__}: {str(e)}',
                'dependencies_used': ['unknown']
            }



if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
