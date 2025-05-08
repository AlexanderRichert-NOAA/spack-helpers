# spack-helpers

This repository contains scripts intended to help with various aspects of package management with Spack.

## Utilities

### fetch_cargo_deps.py
This utility prefetches Rust package dependencies for 'rust' dependents and/or user-specified
packages in an activated, concretized environment. It uses `cargo fetch` to
download dependencies (defined in Cargo.toml) to `$CARGO_HOME` (which must be
set both at fetch time and install time). No arguments are taken.

### fetch_go_deps.py
This utility prefetches Rust package dependencies for GoPackage-type packages
in an activated, concretized environment. It uses `go mod download` to download
dependencies (defined in go.mod) to `$GOMODCACHE` (which must be set both at
fetch time and install time). No arguments are taken.

### filter_spack_compilers.py
This utility filters compilers (compilers.yaml or spack.yaml:compilers) to
selectively keep or delete compilers. This approach is recommended as a way of
ensuring that unwanted compilers do not slip into Spack's concretization.
Notice that this utility will not be useful following
https://github.com/spack/spack/commit/5b3942a48935ee4aeef724b4a28c9666a75821c4
(compilers-as-nodes updates), which deprecates compilers.yaml.
See `./filter_spack_compilers.py` for usage documentation.

### parallel_install.sh
This utility runs parallel instances of `spack install`:
```console
./parallel_install.sh 2 4
```
runs two instances of `spack install -j4`. It is intended to be compatible with
the `--fail-fast` flag. The script may be sourced or run as an executable.

To run in PBS Pro in blocking mode:
```console
qsub \
  -N spack-install \
  -j oe \
  -l "select=4:ncpus=6:mem=20GB,walltime=03:00:00"
  -V \
  -Wblock=true \
  -- $PWD/parallel_install.sh 4 6 --show-log-on-error
```

In SLURM:
```console
sbatch \
  --job-name=spack-install \
  --nodes=1 \
  --ntasks=4 \
  --cpus-per-task=6 \
  --mem=20G \
  --time=03:00:00 \
  --export=ALL \
  --wait \
  --wrap="$PWD/parallel_install.sh 4 6 --show-log-on-error"
```

### show_duplicate_packages.py
This utility parses spack.lock and shows instances of multiple hashes for the
same package name in the concrete specs. Packages can be ignored with the `-i`
flag.

## Links

The following may be of some use as reference for Spack enthusiasts:

- https://github.com/NOAA-EMC/ci-common-build-cache : A GitHub repository with an Actions workflow for deploying Spack-compiled packages to GitHub Packages.
- https://github.com/NOAA-EMC/ci-test-spack-package : A custom GitHub action for building and running install-time tests for a Spack recipe.
- https://github.com/JCSDA/spack-stack/tree/develop/util : Directory under spack-stack with various helpful utilities, including scripts for running scheduled building, testing, and binary caching through cron, Jenkins, GH Actions, etc.
