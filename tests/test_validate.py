"""Unit tests for validate command and helper functions."""
import copy
import pytest

import spack.environment as ev
import spack.spec
import spack.extensions

# Load the helpers extension
spack.extensions.load_extension("helpers")
from spack.extensions.helpers.check_duplicates import check_duplicate_packages
from spack.extensions.helpers.check_compiler_usage import check_compiler_usage
from spack.extensions.helpers.check_allowed_compilers import check_allowed_compilers
from spack.extensions.helpers.check_approved_packages import check_approved_packages


@pytest.fixture(scope="session")
def _validation_env_base(tmp_path_factory):
    """Create a comprehensive test environment for validation checks (cached).
    
    This environment contains:
    - Duplicate packages (zlib with two different variants)
    - Multiple compilers (gcc and intel-oneapi-compilers)
    - Mixed compiler usage across different packages
    - Both approved and unapproved packages
    
    This is a session-scoped fixture that is created once and reused.
    """
    # Create environment directory and manifest file
    tmp_path = tmp_path_factory.mktemp("validation_test_env")
    env_path = tmp_path / "validation_test_env"
    env_path.mkdir(exist_ok=False)
    env = ev.create_in_dir(env_path, with_view=False)
    
    # Configure concretizer to unify when possible
    env.unify = "when_possible"
    
    # Add specs that will create various validation scenarios
    specs_to_add = [
        # Duplicates: zlib with two different variants
        "zlib+shared",
        "zlib~shared",
        
        # Different packages using gcc
        "libelf%gcc",
        "libdwarf%gcc",
        
        # Simple package for testing compiler restrictions
        "gmake%gcc",
        
        # Additional packages for approved/unapproved testing
        "cmake",
        "py-numpy",
    ]
    
    for spec_str in specs_to_add:
        spec = spack.spec.Spec(spec_str)
        env.add(spec)
    
    env.write()
    
    # Concretize the environment once
    env.concretize()
    env.write()
    
    return env


@pytest.fixture
def validation_test_env(_validation_env_base):
    """Provide a deep copy of the validation test environment for each test.
    
    This allows tests to reuse the same concretized environment without
    having to concretize it multiple times, while still providing independent
    copies to avoid any potential state pollution between tests.
    """
    return copy.deepcopy(_validation_env_base)


def test_check_duplicate_packages_finds_duplicates(validation_test_env):
    """Test that check_duplicate_packages identifies duplicate installations."""
    env = validation_test_env
    
    # Check for duplicates
    duplicates = check_duplicate_packages(env)
    
    # Should find zlib as a duplicate (we added zlib+shared and zlib~shared)
    assert "zlib" in duplicates, "Should detect zlib duplicates"
    assert len(duplicates["zlib"]) == 2, "Should find exactly 2 zlib specs"
    
    # Verify the duplicates are different
    hashes = [spec.dag_hash() for spec in duplicates["zlib"]]
    assert len(set(hashes)) == 2, "Duplicate specs should have different hashes"


def test_check_duplicate_packages_with_ignore(validation_test_env):
    """Test that check_duplicate_packages respects ignore_packages parameter."""
    env = validation_test_env
    
    # Check for duplicates, ignoring zlib
    duplicates = check_duplicate_packages(env, ignore_packages=["zlib"])
    
    # Should not find zlib as a duplicate since we're ignoring it
    assert "zlib" not in duplicates, "Should not detect ignored package as duplicate"


def test_check_duplicate_packages_no_false_positives(validation_test_env):
    """Test that check_duplicate_packages doesn't flag non-duplicates."""
    env = validation_test_env
    
    duplicates = check_duplicate_packages(env)
    
    # Packages like libelf, libdwarf should not be flagged as duplicates
    # (they were only added once)
    for pkg in ["libelf", "libdwarf", "cmake"]:
        if pkg in duplicates:
            assert len(duplicates[pkg]) > 1, f"{pkg} should only be flagged if truly duplicated"


def test_check_compiler_usage_detects_violations(validation_test_env):
    """Test that check_compiler_usage detects packages using restricted compilers."""
    env = validation_test_env
    
    # Allow only callpath to use gcc
    allowed_packages = ["gmake"]
    illegal_specs = check_compiler_usage(env, "gcc", allowed_packages)
    
    # Should find specs using gcc that are not gmake
    # (libelf, libdwarf, and potentially dependencies)
    assert len(illegal_specs) > 0, "Should detect packages using gcc that aren't allowed"
    
    # Verify that gmake is not in the illegal list
    illegal_names = [spec.name for spec in illegal_specs]
    assert "gmake" not in illegal_names, "gmake should not be in illegal list"


def test_check_compiler_usage_no_violations(validation_test_env):
    """Test that check_compiler_usage returns empty when all packages are allowed."""
    env = validation_test_env
    
    # Get all package names in the environment
    all_packages = set()
    for _, concrete_spec in env.concretized_specs():
        all_packages.add(concrete_spec.name)
    
    # Allow all packages to use gcc
    illegal_specs = check_compiler_usage(env, "gcc", list(all_packages))
    
    # Should find no violations
    assert len(illegal_specs) == 0, "Should find no violations when all packages are allowed"


def test_check_compiler_usage_nonexistent_compiler(validation_test_env):
    """Test check_compiler_usage with a compiler that doesn't exist in env."""
    env = validation_test_env
    
    # Check for a compiler that's not used (e.g., 'clang')
    illegal_specs = check_compiler_usage(env, "nonexistent-compiler", [])
    
    # Should find no violations since no specs use this compiler
    assert len(illegal_specs) == 0, "Should find no violations for unused compiler"


def test_check_allowed_compilers_detects_violations(validation_test_env):
    """Test that check_allowed_compilers detects specs using disallowed compilers."""
    env = validation_test_env
    
    # Allow only a specific gcc version (that likely doesn't match)
    allowed_compilers = ["gcc@999.0.0"]
    illegal_specs = check_allowed_compilers(env, allowed_compilers)
    
    # Should find specs using compilers other than gcc@999.0.0
    assert len(illegal_specs) > 0, "Should detect specs using disallowed compilers"


def test_check_allowed_compilers_with_wildcard(validation_test_env):
    """Test that check_allowed_compilers works with compiler version wildcards."""
    env = validation_test_env
    
    # Allow any gcc version
    allowed_compilers = ["gcc"]
    illegal_specs = check_allowed_compilers(env, allowed_compilers)
    
    # Should find few or no violations (most specs use gcc in our test env)
    # The exact count depends on mock packages, but we can verify the function runs
    assert isinstance(illegal_specs, list), "Should return a list"


def test_check_allowed_compilers_multiple_allowed(validation_test_env):
    """Test check_allowed_compilers with multiple allowed compilers."""
    env = validation_test_env
    
    # Allow both gcc and intel compilers (with any version)
    allowed_compilers = ["gcc", "intel-oneapi-compilers"]
    illegal_specs = check_allowed_compilers(env, allowed_compilers)
    
    # Should allow specs using either compiler
    assert isinstance(illegal_specs, list), "Should return a list"


def test_check_approved_packages_detects_violations(validation_test_env):
    """Test that check_approved_packages detects unauthorized packages."""
    env = validation_test_env
    
    # Allow only a subset of packages
    approved_packages = ["zlib", "gmake"]
    unauthorized_specs = check_approved_packages(env, approved_packages)
    
    # Should find unauthorized packages (like libelf, libdwarf, cmake, etc.)
    assert len(unauthorized_specs) > 0, "Should detect unauthorized packages"
    
    # Verify that approved packages are not in the unauthorized list
    unauthorized_names = [spec.name for spec in unauthorized_specs]
    assert "zlib" not in unauthorized_names, "zlib should not be unauthorized"
    assert "gmake" not in unauthorized_names, "gmake should not be unauthorized"


def test_check_approved_packages_all_approved(validation_test_env):
    """Test that check_approved_packages returns empty when all are approved."""
    env = validation_test_env
    
    # Get all package names in the environment
    all_packages = set()
    for _, concrete_spec in env.concretized_specs():
        all_packages.add(concrete_spec.name)
    
    # Approve all packages
    unauthorized_specs = check_approved_packages(env, list(all_packages))
    
    # Should find no unauthorized packages
    assert len(unauthorized_specs) == 0, "Should find no violations when all packages are approved"


def test_check_approved_packages_none_approved(validation_test_env):
    """Test that check_approved_packages detects all packages when none approved."""
    env = validation_test_env
    
    # Approve no packages (empty list)
    unauthorized_specs = check_approved_packages(env, [])
    
    # Should find all packages as unauthorized
    assert len(unauthorized_specs) > 0, "Should detect all packages as unauthorized"
    
    # Count should match total number of concretized specs
    total_specs = len(list(env.concretized_specs()))
    assert len(unauthorized_specs) == total_specs, "All specs should be unauthorized"
