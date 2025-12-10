"""Allow only approved packages in Spack environment.

This command configures a Spack environment so that only approved packages
are buildable while all other packages are marked as non-buildable.
"""

import spack.llnl.util.tty as tty

import spack.cmd
import spack.environment as ev
from spack.error import SpackError

description = "configure environment to set only approved packages as buildable"
section = "environments"
level = "long"


def setup_parser(subparser):
    """Setup argument parser for allow-only-approved-pkgs command."""
    
    # Make packages and --pkgs-from-file mutually exclusive
    pkg_group = subparser.add_mutually_exclusive_group(required=True)
    pkg_group.add_argument(
        '--packages',
        nargs='+',
        help='approved package names'
    )
    pkg_group.add_argument(
        '--pkgs-from-file',
        type=str,
        help='read approved package names from a newline-delimited text file'
    )


def allow_only_approved_pkgs(parser, args):
    """Handle allow-only-approved-pkgs command.
    
    Args:
        parser: Arg parser
        args: Parsed command-line arguments    
    Returns:
        Exit code: 0 for success, 1 for errors
    """
    
    env = ev.active_environment()
    if not env:
        raise SpackError("No active Spack environment.")
    
    # Get approved packages from command line or file
    if args.pkgs_from_file:
        try:
            with open(args.pkgs_from_file, 'r') as f:
                approved_packages = [
                    line.strip() for line in f 
                    if line.strip() and not line.strip().startswith('#')
                ]
        except IOError as e:
            raise SpackError(f"Could not read package list from {args.pkgs_from_file}: {e}")
    else:
        approved_packages = args.packages if args.packages else []
    
    if not approved_packages:
        raise SpackError("No packages specified. Provide package names or use --pkgs-from-file.")
    
    # Get packages config from environment
    if 'packages' not in env.manifest.configuration:
        env.manifest.configuration['packages'] = {}
    
    packages = env.manifest.configuration['packages']
    
    # Process approved packages
    for pkg_name in approved_packages:
        if pkg_name not in packages:
            packages[pkg_name] = {}
        
        # Check if already marked as buildable: false
        if packages[pkg_name].get('buildable') is False:
            tty.msg(f"Package '{pkg_name}' is already buildable:false, skipping.")
        else:
            packages[pkg_name]['buildable'] = True
            tty.debug(f"Set '{pkg_name}' buildable:true")
    
    # Set packages:all:buildable:false
    if 'all' not in packages:
        packages['all'] = {}
    packages['all']['buildable'] = False
    
    # Mark as changed and write
    env.manifest.changed = True
    env.write()
    
    tty.msg(f"Configured {len(approved_packages)} approved package(s) as buildable.")
    tty.msg("Set 'all' packages as non-buildable (buildable:false).")
    
    # Check if environment has concrete specs and remind user to re-concretize
    if env.concretized_specs():
        tty.warn("Environment has concretized specs. Run 'spack concretize -f' to re-concretize with the new buildabillity settings.")
    
    return 0
