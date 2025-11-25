"""Check that only approved packages appear in a Spack environment.

This module provides functionality to validate that only whitelisted packages
are present in a concretized Spack environment.
"""

from typing import List

import spack.spec
from spack.llnl.util import tty


def check_approved_packages(env, approved_packages):
    """Check for specs with package names not in the approved list.
    
    Iterates over all concretized specs in the environment and identifies
    specs whose package names are not in the approved list.
    
    Args:
        env: A Spack Environment object to check
        approved_packages: List of approved package names (e.g., ['gcc', 'openmpi', 'hdf5'])
        
    Returns:
        List[Spec]: List of Spec objects for unauthorized packages.
    """
    unauthorized_specs = []
    
    # Convert approved_packages to a set for faster lookup
    approved_set = set(approved_packages)
    
    # Iterate over all concretized specs in the environment
    for user_spec, concrete_spec in env.concretized_specs():
        pkg_name = concrete_spec.name
        
        # If this package is not approved, mark as unauthorized
        if pkg_name not in approved_set:
            unauthorized_specs.append(concrete_spec)
            tty.debug(f"Illegal package: pkg_name")
        else:
            tty.debug(f"Legal package validated: pkg_name")
    
    return unauthorized_specs
