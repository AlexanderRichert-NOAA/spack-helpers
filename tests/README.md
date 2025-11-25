# Running Unit Tests for spack-helpers Extension

This directory contains unit tests for the spack-helpers extension.

## Prerequisites

1. Spack must be available in your environment
2. 'go' and 'cargo' must be installed and available in your PATH (for integration tests)
3. Source the setup script to enable the extension.

## Running the Tests

The extension name is derived from the directory name. Since the directory is `/n/spack-helpers`, the extension name is `helpers`.

### Run all tests for the helpers extension

```bash
spack unit-test --extension=helpers
```

### Run a specific test file

```bash
spack unit-test --extension=helpers tests/test_fetch_go.py
```

### Run a specific test function

```bash
spack unit-test --extension=helpers tests/test_fetch_go.py::test_fetch_go_dependencies_empty_list
```

### Run without integration tests

```bash
spack unit-test --extension=helpers -m "not integration"
```

### List available tests

```bash
spack unit-test --extension=helpers --list-names
```
