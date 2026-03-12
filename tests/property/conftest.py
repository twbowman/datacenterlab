"""
Property-based testing configuration for production network testing lab

This module configures hypothesis settings for property-based tests.
"""

from hypothesis import settings, Verbosity

# Configure hypothesis to run 100+ examples per test as per design requirements
settings.register_profile("default", max_examples=100, deadline=None)
settings.register_profile("ci", max_examples=200, deadline=None)
settings.register_profile("dev", max_examples=50, deadline=None, verbosity=Verbosity.verbose)

# Load the default profile
settings.load_profile("default")
