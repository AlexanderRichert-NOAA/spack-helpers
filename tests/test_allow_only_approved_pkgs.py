"""Unit tests for allow-only-approved-pkgs command."""
import pytest

import spack.environment as ev
import spack.spec
import spack.extensions

# Load the helpers extension
spack.extensions.load_extension("helpers")


@pytest.fixture
def test_env(tmp_path):
    """Create a test environment for allow-only-approved-pkgs command."""
    env_path = tmp_path / "test_env"
    env_path.mkdir(exist_ok=True)
    
    env = ev.create_in_dir(env_path, with_view=False)
    env.write()
    
    return env


def test_allow_only_approved_pkgs_basic(test_env):
    """Test basic functionality of allowing approved packages."""
    # Import the command module
    from spack.extensions.helpers.cmd import allow_only_approved_pkgs
    
    # Create mock args
    class Args:
        packages = ['gcc', 'openmpi', 'hdf5']
        pkgs_from_file = None
    
    args = Args()
    
    # Activate environment and run the command
    with test_env:
        result = allow_only_approved_pkgs.allow_only_approved_pkgs(None, args)
    
    # Check return code
    assert result == 0
    
    # Verify configuration was written
    packages = test_env.manifest.configuration.get('packages', {})
    
    # Check that approved packages are buildable
    assert packages['gcc']['buildable'] is True
    assert packages['openmpi']['buildable'] is True
    assert packages['hdf5']['buildable'] is True
    
    # Check that 'all' is non-buildable
    assert packages['all']['buildable'] is False


def test_allow_only_approved_pkgs_preserves_existing_false(test_env):
    """Test that packages already marked buildable:false are not changed."""
    # Pre-configure a package as buildable:false
    test_env.manifest.configuration['packages'] = {
        'cmake': {'buildable': False}
    }
    test_env.write()
    
    from spack.extensions.helpers.cmd import allow_only_approved_pkgs
    
    class Args:
        packages = ['gcc', 'cmake', 'openmpi']
        pkgs_from_file = None
    
    args = Args()
    
    # Activate environment and run the command
    with test_env:
        result = allow_only_approved_pkgs.allow_only_approved_pkgs(None, args)
    
    assert result == 0
    
    packages = test_env.manifest.configuration.get('packages', {})
    
    # cmake should still be False (unchanged)
    assert packages['cmake']['buildable'] is False
    
    # Other packages should be True
    assert packages['gcc']['buildable'] is True
    assert packages['openmpi']['buildable'] is True
    
    # 'all' should be False
    assert packages['all']['buildable'] is False


def test_allow_only_approved_pkgs_from_file(test_env, tmp_path):
    """Test reading approved packages from a file."""
    # Create a package list file
    pkg_file = tmp_path / "packages.txt"
    pkg_file.write_text("gcc\nopenmpi\n# comment line\nhdf5\n\n")
    
    from spack.extensions.helpers.cmd import allow_only_approved_pkgs
    
    class Args:
        packages = []
        pkgs_from_file = str(pkg_file)
    
    args = Args()
    
    # Activate environment and run the command
    with test_env:
        result = allow_only_approved_pkgs.allow_only_approved_pkgs(None, args)
    
    assert result == 0
    
    packages = test_env.manifest.configuration.get('packages', {})
    
    # Check that packages from file are buildable
    assert packages['gcc']['buildable'] is True
    assert packages['openmpi']['buildable'] is True
    assert packages['hdf5']['buildable'] is True
    
    # 'all' should be False
    assert packages['all']['buildable'] is False


def test_allow_only_approved_pkgs_preserves_other_config(test_env):
    """Test that other package configuration is preserved."""
    # Pre-configure packages with various settings
    test_env.manifest.configuration['packages'] = {
        'gcc': {
            'variants': '+binutils',
            'externals': [{'spec': 'gcc@11.2.0', 'prefix': '/usr'}]
        },
        'openmpi': {
            'version': ['4.1.0'],
            'buildable': False
        }
    }
    test_env.write()
    
    from spack.extensions.helpers.cmd import allow_only_approved_pkgs
    
    class Args:
        packages = ['gcc', 'openmpi']
        pkgs_from_file = None
    
    args = Args()
    
    # Activate environment and run the command
    with test_env:
        result = allow_only_approved_pkgs.allow_only_approved_pkgs(None, args)
    
    assert result == 0
    
    packages = test_env.manifest.configuration.get('packages', {})
    
    # Check that gcc's other config is preserved
    assert packages['gcc']['variants'] == '+binutils'
    assert packages['gcc']['externals'][0]['spec'] == 'gcc@11.2.0'
    assert packages['gcc']['buildable'] is True
    
    # Check that openmpi's buildable:false is preserved
    assert packages['openmpi']['version'] == ['4.1.0']
    assert packages['openmpi']['buildable'] is False

