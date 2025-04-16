#!/usr/bin/env python3
#
# Run "./filter_spack_compilers.py --help" for documentation. NOTE: This script
# will be of no use after
# https://github.com/spack/spack/commit/5b3942a48935ee4aeef724b4a28c9666a75821c4
# and the deprecation of compilers.yaml. Use with
# https://github.com/spack/spack/commit/a9c879d53e758f67cdbf4cec919425cb2a3a1082
# or prior commits.
#

import argparse
import os
import re
import sys


def parse_arguments():
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser(
        prog='filter_spack_compilers.py',
        description='Inclusively or exclusively delete compilers from compilers.yaml or spack.yaml.',
        epilog='Written by Alex Richert, March 2025',
    )
    parser.add_argument('yamlfile', help='Input YAML file (compilers.yaml or spack.yaml)')
    parser.add_argument('compilerspecs', nargs='+', help='Compiler specs to keep/remove')
    
    inc_or_exc_group = parser.add_mutually_exclusive_group(required=True)
    inc_or_exc_group.add_argument('--remove', action='store_true', 
                                  help='Remove specified compiler specs')
    inc_or_exc_group.add_argument('--keep-only', action='store_true', 
                                  help='Remove all compiler specs except those specified')
    inc_or_exc_group.add_argument('--keep-only-this-version', action='store_true', 
                                  help='Remove all compiler specs of the same name(s) specified (i.e., have only one version of intel)')
    
    parser.add_argument('--use-ruamel', action='store_true',
                       help='Use ruamel.yaml (preserves comments) instead of standard yaml module')
    
    return parser.parse_args()


def load_yaml_file(filename, use_ruamel=False):
    """Load and return YAML file contents using either standard yaml or ruamel.yaml."""
    if use_ruamel:
        try:
            from ruamel.yaml import YAML
            yaml_parser = YAML(typ='rt')
            yaml_parser.default_flow_style = False
            
            with open(filename, 'r') as file:
                raw_yaml_data = yaml_parser.load(file)
        except ImportError:
            print("Error: ruamel.yaml module not available. Install with,, e.g., 'pip install ruamel.yaml'")
            sys.exit(1)
    else:
        # Use standard yaml module
        import yaml
        
        with open(filename, 'r') as file:
            raw_yaml_data = yaml.safe_load(file)
        yaml_parser = yaml  # For consistency in return values
    
    # Handle both spack.yaml and compilers.yaml formats
    if 'spack' in raw_yaml_data.keys():
        yaml_data = raw_yaml_data['spack']
        is_spack_yaml = True
    else:
        yaml_data = raw_yaml_data
        is_spack_yaml = False
    
    return yaml_parser, raw_yaml_data, yaml_data, is_spack_yaml


def filter_compilers(yaml_data, args):
    """Filter compilers based on command line arguments."""

    # In the future, `spack.spec.Spec("foo@1.2.3").satisfies("foo@1")` may provide
    # a more robust way to match specs.

    # Change "@=" to "@" to make sure we don't miss anything. For matching purposes
    # we'll treat the two as equivalent.
    args.compilerspecs = [x.replace("@=", "@") for x in args.compilerspecs]

    n_compilers = len(yaml_data['compilers'])
    
    for i in range(n_compilers-1, -1, -1):
        compiler_spec = yaml_data['compilers'][i]['compiler']['spec'].replace("@=", "@")
        
        if args.keep_only_this_version:
            names = [re.sub('@.*', '', x) for x in args.compilerspecs]
            compiler_name = re.sub('@.*', '', compiler_spec)
            if (compiler_name in names) and (compiler_spec not in args.compilerspecs):
                del yaml_data['compilers'][i]
            continue
            
        if (compiler_spec in args.compilerspecs) and args.remove:
            del yaml_data['compilers'][i]
            continue
            
        if (compiler_spec not in args.compilerspecs) and args.keep_only:
            del yaml_data['compilers'][i]
    
    return yaml_data


def save_yaml_file(yaml_parser, yaml_data, raw_yaml_data, yamlfile, is_spack_yaml, use_ruamel=False):
    """Save modified YAML data back to file with backup of original."""
    if is_spack_yaml:
        raw_yaml_data['spack'] = yaml_data
        output_data = raw_yaml_data
    else:
        output_data = yaml_data
    
    # Create backup of original file
    bkp_path = yamlfile + '.bkp'
    os.rename(yamlfile, bkp_path)
    
    # Write updated file
    with open(yamlfile, 'w') as outputfile:
        if use_ruamel:
            # ruamel.yaml has its own dump method
            yaml_parser.dump(output_data, outputfile)
        else:
            # Standard yaml module is already imported in yaml_parser
            yaml_parser.dump(output_data, outputfile, sort_keys=False, default_flow_style=False)


def main():
    """Main function to run the script."""
    args = parse_arguments()
    yaml_parser, raw_yaml_data, yaml_data, is_spack_yaml = load_yaml_file(args.yamlfile, args.use_ruamel)
    yaml_data = filter_compilers(yaml_data, args)
    save_yaml_file(yaml_parser, yaml_data, raw_yaml_data, args.yamlfile, is_spack_yaml, args.use_ruamel)


if __name__ == "__main__":
    main()
