#!/usr/bin/env spack-python
"""
**Experimental** script to analyze variants in Spack packages and suggest
optimizations to minimize the overall number of packages in an environment.
Runs inside active, concretized environment.

This script evaluates binary variants in Spack packages to determine if
flipping a variant value will reduce the dependency tree size.
"""

import argparse
import multiprocessing
import sys

import spack.environment
import spack.spec
import spack.concretize
import spack.repo

def format_results(results, format_type):
    """
    Format results according to the specified output format.
    
    Args:
        results: List of (spec_name, variant_name, suggested_value) tuples
        format_type: Output format ('human', 'command', or 'yaml')
        
    Returns:
        Formatted output as a string
    """
    if not results:
        return "No recommended variant changes found."
        
    # Group results by package
    packages = {}
    for pkg_name, var_name, var_value in results:
        if pkg_name not in packages:
            packages[pkg_name] = []
        packages[pkg_name].append((var_name, var_value))
    
    output = []
    
    if format_type == 'human':
        output.append("Recommended variant changes:")
        for pkg_name, variants in packages.items():
            for var_name, var_value in variants:
                variant_str = f"{'+' if var_value else '~'}{var_name}"
                output.append(f"  {pkg_name}: Use {variant_str} instead!")
                
    elif format_type == 'command':
        for pkg_name, variants in packages.items():
            variant_strs = [f"{'+' if var_value else '~'}{var_name}" for var_name, var_value in variants]
            variants_combined = " ".join(variant_strs)
            output.append(f"spack config add 'packages:{pkg_name}:variants:{variants_combined}'")
            
    elif format_type == 'yaml':
        output.append("packages:")
        for pkg_name, variants in packages.items():
            output.append(f"  {pkg_name}:")
            variant_strs = [f"{'+' if var_value else '~'}{var_name}" for var_name, var_value in variants]
            variants_combined = " ".join(variant_strs)
            output.append(f"    variants: {variants_combined}")
    
    return "\n".join(output)


def evaluate_variant(task):
    """
    Evaluate whether flipping a package variant reduces the dependency graph.
    
    Args:
        task: A tuple containing (spec_name, variant_name)
        
    Returns:
        A tuple containing (spec_name, variant_name, suggested_value) if flipping 
        the variant reduces dependencies, None otherwise.
    """
    spec_name, variant_name = task
    
    # Load environment in the subprocess
    env = spack.environment.active_environment()
    
    # Find the specified package in the environment
    spec = next(
        (s for s in env.all_specs() 
         if s.name == spec_name 
         and not s.external 
         and not spack.repo.PATH.is_virtual(s.name)),
        None
    )
    
    if spec is None:
        return None
        
    variants = dict(spec.variants)
    
    # Check if variant exists and is boolean
    if variant_name not in variants or variants[variant_name].value not in (True, False):
        return None
        
    # Count original dependencies
    n_original = len(list(spec.traverse()))
    
    # Try the opposite variant value
    opposite_value = not variants[variant_name].value
    variant_str = f"{'+' if opposite_value else '~'}{variant_name}"
    new_spec_str = f"{spec.name} {variant_str}"
    
    try:
        # Create and concretize spec with flipped variant
        new_spec = spack.spec.Spec(new_spec_str)
        new_conc = spack.concretize.concretize_one(new_spec)
        
        # Count new dependencies
        n_updated = len(list(new_conc.traverse()))
        
        # If fewer dependencies, suggest the change
        if n_updated < n_original:
            human_result = f"{spec.name}: Use {variant_str} instead!"
            return (spec_name, variant_name, opposite_value)
            
    except Exception as e:
        print(f"Error processing {new_spec_str}: {e}")
        
    return None


def get_variant_tasks():
    """
    Get all binary variant evaluation tasks from the active environment.
    
    Returns:
        List of (spec_name, variant_name) tuples to evaluate.
    """
    env = spack.environment.active_environment()
    
    # Get all non-external, non-virtual specs
    all_specs = [
        spec for spec in env.all_specs() 
        if not spec.external and not spack.repo.PATH.is_virtual(spec.name)
    ]
    
    tasks = []
    for spec in all_specs:
        for variant_name, variant in spec.variants.items():
            if variant.value in (True, False):  # Only binary variants
                tasks.append((spec.name, variant_name))
                
    return tasks


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze Spack package variants to reduce dependencies'
    )
    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=multiprocessing.cpu_count(),
        help='Number of parallel processes to use (default: number of CPU cores)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['human', 'command', 'yaml'],
        default='human',
        help='Output format: human-readable (human), spack commands (command), or packages.yaml format (yaml)'
    )
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    # Get the tasks to evaluate
    tasks = get_variant_tasks()
    
    # Process tasks in parallel
    with multiprocessing.Pool(processes=args.jobs) as pool:
        results = pool.map(evaluate_variant, tasks)
    
    # Filter out None results
    valid_results = [r for r in results if r is not None]
    
    # Format and print results
    formatted_output = format_results(valid_results, args.format)
    print(f"{formatted_output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
