#!/usr/bin/env python3
"""
Validation script for acpctl setup phase (T001-T005).

Run this script to verify that the package structure is correctly set up.
"""

import sys
from pathlib import Path


def validate_structure():
    """Validate directory and file structure."""
    print("Validating package structure...")

    root = Path(__file__).parent

    # Check directories
    required_dirs = [
        "acpctl",
        "acpctl/cli",
        "acpctl/cli/commands",
        "acpctl/cli/ui",
        "acpctl/core",
        "acpctl/agents",
        "acpctl/storage",
        "acpctl/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/integration/fixtures",
        "tests/unit",
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.is_dir():
            missing_dirs.append(dir_path)
        else:
            print(f"  ✓ {dir_path}/")

    if missing_dirs:
        print(f"\n❌ Missing directories: {', '.join(missing_dirs)}")
        return False

    # Check __init__.py files
    required_init_files = [
        "acpctl/__init__.py",
        "acpctl/cli/__init__.py",
        "acpctl/cli/commands/__init__.py",
        "acpctl/cli/ui/__init__.py",
        "acpctl/core/__init__.py",
        "acpctl/agents/__init__.py",
        "acpctl/storage/__init__.py",
        "acpctl/utils/__init__.py",
        "tests/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
        "tests/integration/fixtures/__init__.py",
        "tests/unit/__init__.py",
    ]

    missing_files = []
    for file_path in required_init_files:
        full_path = root / file_path
        if not full_path.is_file():
            missing_files.append(file_path)
        else:
            print(f"  ✓ {file_path}")

    if missing_files:
        print(f"\n❌ Missing __init__.py files: {', '.join(missing_files)}")
        return False

    # Check configuration files
    config_files = ["pyproject.toml", "setup.py", "tests/conftest.py"]
    for file_path in config_files:
        full_path = root / file_path
        if not full_path.is_file():
            print(f"  ❌ Missing configuration file: {file_path}")
            return False
        else:
            print(f"  ✓ {file_path}")

    print("\n✅ All required directories and files present!")
    return True


def validate_imports():
    """Validate that packages can be imported."""
    print("\nValidating package imports...")

    try:
        import acpctl
        print(f"  ✓ acpctl (version {acpctl.__version__})")

        from acpctl import cli
        print("  ✓ acpctl.cli")

        from acpctl import core
        print("  ✓ acpctl.core")

        from acpctl import agents
        print("  ✓ acpctl.agents")

        from acpctl import storage
        print("  ✓ acpctl.storage")

        from acpctl import utils
        print("  ✓ acpctl.utils")

        print("\n✅ All package imports successful!")
        return True

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False


def validate_configuration():
    """Validate configuration in pyproject.toml."""
    print("\nValidating configuration...")

    try:
        import tomli
    except ImportError:
        # tomli is not available in Python 3.11+ (uses tomllib)
        try:
            import tomllib as tomli
        except ImportError:
            print("  ⚠️  Cannot validate TOML (tomli/tomllib not available)")
            return True

    root = Path(__file__).parent
    pyproject_path = root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)

    # Check key sections
    sections = ["build-system", "project", "tool.pytest.ini_options", "tool.black", "tool.isort", "tool.mypy"]
    for section in sections:
        keys = section.split(".")
        data = config
        found = True
        for key in keys:
            if key in data:
                data = data[key]
            else:
                found = False
                break

        if found:
            print(f"  ✓ [{section}] configured")
        else:
            print(f"  ❌ Missing configuration section: [{section}]")
            return False

    # Check dependencies
    deps = config["project"]["dependencies"]
    required_deps = ["langgraph", "langchain", "typer", "rich", "pydantic"]
    for dep in required_deps:
        if any(dep in d for d in deps):
            print(f"  ✓ Dependency: {dep}")
        else:
            print(f"  ❌ Missing dependency: {dep}")
            return False

    print("\n✅ Configuration valid!")
    return True


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("acpctl Setup Validation (T001-T005)")
    print("=" * 60)

    checks = [
        ("Directory Structure", validate_structure),
        ("Package Imports", validate_imports),
        ("Configuration", validate_configuration),
    ]

    results = []
    for check_name, check_func in checks:
        print()
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ {check_name} check failed with exception: {e}")
            results.append((check_name, False))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All validation checks passed!")
        print("\nSetup phase (T001-T005) is complete.")
        print("Ready to proceed to Phase 2 (Foundational).")
        return 0
    else:
        print("❌ Some validation checks failed!")
        print("\nPlease review and fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
