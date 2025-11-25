"""Check for duplicate package installations in a Spack environment.

This module provides functionality to detect when multiple hashes exist
for the same package name in a concretized Spack environment.
"""

from collections import defaultdict
from typing import Dict, List

import spack.spec


def check_duplicate_packages(env, ignore_packages=None):
    """Check for duplicate package installations in a Spack environment.
    
    Iterates over all concretized specs in the environment and identifies
    packages that have multiple hashes (i.e., multiple installations).
    
    Args:
        env: A Spack Environment object to check
        ignore_packages: List of package names to exclude from duplicate checking
        
    Returns:
        Dict[str, List[Spec]]: Dictionary with package names as keys and lists
                               of duplicate Spec objects as values. Only includes
                               packages with duplicates (length > 1).
    """
    if ignore_packages is None:
        ignore_packages = []
    
    # Track specs by package name
    packages_by_name = defaultdict(list)
    
    # Iterate over all concretized specs in the environment
    for user_spec, concrete_spec in env.concretized_specs():
        pkg_name = concrete_spec.name
        
        # Skip ignored packages
        if pkg_name in ignore_packages:
            continue
        
        # Check if we already have a different hash for this package
        existing_hashes = [s.dag_hash() for s in packages_by_name[pkg_name]]
        if concrete_spec.dag_hash() not in existing_hashes:
            packages_by_name[pkg_name].append(concrete_spec)
    
    # Filter to only return packages with duplicates
    duplicates = {
        pkg_name: specs 
        for pkg_name, specs in packages_by_name.items() 
        if len(specs) > 1
    }
    
    return duplicates
