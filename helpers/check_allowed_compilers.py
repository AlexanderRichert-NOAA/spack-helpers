"""Check that only specified compilers appear in a Spack environment.

This module provides functionality to validate that only whitelisted compilers
are used in a concretized Spack environment.
"""

from typing import List

import spack.spec


def check_allowed_compilers(env, allowed_compilers):
    """Check for specs using compilers not in the allowed list.
    
    Iterates over all concretized specs in the environment and identifies
    specs that use compilers (c, c++, fortran) not in the allowed list.
    
    Args:
        env: A Spack Environment object to check
        allowed_compilers: List of allowed compiler specs (e.g., 'gcc@11.2.0', 'clang@14.0.0')
        
    Returns:
        List[Spec]: List of Spec objects that use disallowed compilers.
    """
    import spack.spec
    
    illegal_specs = []
    
    # Parse allowed compiler specs
    allowed_compiler_specs = [spack.spec.Spec(spec_str) for spec_str in allowed_compilers]
    
    # Iterate over all concretized specs in the environment
    for user_spec, concrete_spec in env.concretized_specs():
        # Check c, c++, and fortran compilers
        for lang in ("c", "cxx", "fortran"):
            if lang in concrete_spec:
                compiler_spec = concrete_spec[lang]
                
                # Check if this compiler satisfies any of the allowed compiler specs
                is_allowed = any(
                    compiler_spec.satisfies(allowed_spec)
                    for allowed_spec in allowed_compiler_specs
                )
                
                # If this compiler is not allowed, mark as problematic
                if not is_allowed:
                    illegal_specs.append(concrete_spec)
                    break  # Only add each spec once
    
    return illegal_specs
