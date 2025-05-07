#!/usr/bin/env spack-python
#
# Run this script in an active, concretized Spack environment to fetch Rust
# dependencies and store them in $CARGO_HOME. You must either run it with
# 'spack-python' or have 'spack-python' in your $PATH. Ensure $CARGO_PATH has
# the same value when 'spack install' is run.
#
# For each spec that depends on 'rust' and/or is specified by the user, it will
# attempt to use that spec's 'rust' dependency to execute 'cargo fetch', but
# will fall back to searching for 'cargo' $PATH if that dependency has not
# already been installed.
#
# Alex Richert, Apr 2025
#

import os
import argparse

from spack.environment import active_environment
from spack.error import SpackError
from spack.installer import PackageInstaller
from spack.spec import Spec
from spack.util.executable import Executable, which
from llnl.util.filesystem import working_dir

parser = argparse.ArgumentParser(
    description="Fetch Rust dependencies for packages in a Spack environment"
)
parser.add_argument(
    "--spec", "-s", 
    nargs="+", 
    default=[],
    help="Additional specs for which to fetch cargo dependencies",
)
parser.add_argument(
    "--install-rust", 
    action="store_true", 
    help="Install rust dependency if not already installed",
)
parser.add_argument(
    "--only-listed", "-o",
    action="store_true",
    help="Only fetch user-provided specs (no auto-detection of rust dependents)",
)

args = parser.parse_args()

# Load the current environment
env = active_environment()
if not env:
    raise SpackError("No active Spack environment")

cargo_home = os.getenv("CARGO_HOME")
if not cargo_home:
    raise SpackError("CARGO_HOME must be set")

user_specs = []
for spec_str in args.spec:
    try:
        user_specs.append(Spec(spec_str))
    except Exception as e:
        print(f"Warning: Invalid spec '{spec_str}': {e}")

# Find each spec that depends on 'rust' or is in the user-specified package list
for spec in env.all_specs():
    if not spec.concrete:
        continue
        
    # Check if the package depends on rust or is user specified
    is_user_specified = False
    for user_spec in user_specs:
        if spec.satisfies(user_spec):
            is_user_specified = True
            break
    if is_user_specified:
        fetch_it = True
    elif not args.only_listed:
        fetch_it = any(dep.name == 'rust' for dep in spec.dependencies())
    else:
        fetch_it = False
    
    if fetch_it:
        print(f"Processing: {spec.name}@{spec.version}/{spec.dag_hash()}")
        
        # Check if package actually has a rust dependency
        if 'rust' not in spec:
            print(f"  Warning: {spec.name} does not have a 'rust' dependency, skipping")
            continue
            
        pkg = spec.package
        pkg.do_stage()
        
        # Install rust dependency if requested and not already installed
        rust_dep = spec["rust"]
        dep_cargo_path = os.path.join(rust_dep.prefix.bin, "cargo").replace("/bin/bin/", "/bin/")
        
        if not which(dep_cargo_path) and args.install_rust:
            print(f"  Installing rust dependency: {rust_dep}")
            installer = PackageInstaller([rust_dep.package])
            installer.install()
        
        # Now try to use the rust dependency's cargo executable
        if which(dep_cargo_path):
            cargo_exe = Executable(dep_cargo_path)
        elif which("cargo"):
            cargo_exe = Executable("cargo")
        else:
            raise SpackError("Could not find 'cargo' executable")

        # Execute cargo fetch
        with working_dir(pkg.stage.source_path):
            if os.path.isfile("Cargo.toml"):
                cargo_exe("fetch")
                print(f"  Successfully fetched dependencies for {spec.name}")
            else:
                print(f"  No Cargo.toml for {spec.name}")
