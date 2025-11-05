"""
acpctl Artifact File Management

Handles reading and writing workflow artifacts (specs, plans, code, etc.).
Manages the specs/ directory structure and artifact files.

Artifact Structure:
    specs/NNN-feature/
    ├── spec.md              # Feature specification
    ├── plan.md              # Implementation plan
    ├── data-model.md        # Data models
    ├── research.md          # Research findings
    ├── quickstart.md        # Quick start guide
    └── contracts/           # API contracts
        └── api.yaml

Architecture:
- UTF-8 encoding for all text files
- Automatic directory creation
- Path validation and sanitization
- Type-safe artifact operations

Reference: plan.md (Project Structure section)
"""

from pathlib import Path
from typing import Dict, List, Optional

# ============================================================
# ARTIFACT TYPES
# ============================================================

# Supported artifact types and their default filenames
ARTIFACT_TYPES = {
    "spec": "spec.md",
    "plan": "plan.md",
    "data_model": "data-model.md",
    "research": "research.md",
    "quickstart": "quickstart.md",
}


# ============================================================
# ARTIFACT OPERATIONS
# ============================================================


def create_feature_directory(feature_id: str, base_dir: str = "specs") -> Path:
    """
    Create feature directory structure.

    Args:
        feature_id: Feature identifier (e.g., "001-oauth2-authentication")
        base_dir: Base directory for specs (default: "specs")

    Returns:
        Path to created feature directory

    Raises:
        IOError: If directory creation fails

    Example:
        >>> feature_dir = create_feature_directory("001-oauth2-authentication")
        >>> print(feature_dir)
        specs/001-oauth2-authentication
    """
    feature_path = Path(base_dir) / feature_id

    try:
        feature_path.mkdir(parents=True, exist_ok=True)

        # Create contracts subdirectory
        contracts_path = feature_path / "contracts"
        contracts_path.mkdir(exist_ok=True)

        return feature_path
    except OSError as e:
        raise IOError(f"Failed to create feature directory: {e}")


def write_artifact(
    feature_id: str,
    artifact_type: str,
    content: str,
    base_dir: str = "specs",
    custom_filename: Optional[str] = None,
) -> Path:
    """
    Write artifact content to file.

    Args:
        feature_id: Feature identifier (e.g., "001-oauth2-authentication")
        artifact_type: Type of artifact ("spec", "plan", "data_model", etc.)
        content: Artifact content to write
        base_dir: Base directory for specs (default: "specs")
        custom_filename: Custom filename (overrides default for artifact_type)

    Returns:
        Path to written artifact file

    Raises:
        ValueError: If artifact_type is unknown and no custom_filename provided
        IOError: If file write fails

    Example:
        >>> path = write_artifact(
        ...     "001-oauth2-authentication",
        ...     "spec",
        ...     "# Feature Specification\\n\\nOAuth2 authentication..."
        ... )
        >>> print(path)
        specs/001-oauth2-authentication/spec.md
    """
    # Determine filename
    if custom_filename:
        filename = custom_filename
    elif artifact_type in ARTIFACT_TYPES:
        filename = ARTIFACT_TYPES[artifact_type]
    else:
        raise ValueError(
            f"Unknown artifact type '{artifact_type}'. "
            f"Provide custom_filename or use one of: {list(ARTIFACT_TYPES.keys())}"
        )

    # Ensure feature directory exists
    feature_path = Path(base_dir) / feature_id
    feature_path.mkdir(parents=True, exist_ok=True)

    # Write artifact file
    artifact_path = feature_path / filename

    try:
        artifact_path.write_text(content, encoding="utf-8")
        return artifact_path
    except IOError as e:
        raise IOError(f"Failed to write artifact: {e}")


def read_artifact(
    feature_id: str,
    artifact_type: str,
    base_dir: str = "specs",
    custom_filename: Optional[str] = None,
) -> str:
    """
    Read artifact content from file.

    Args:
        feature_id: Feature identifier (e.g., "001-oauth2-authentication")
        artifact_type: Type of artifact ("spec", "plan", "data_model", etc.)
        base_dir: Base directory for specs (default: "specs")
        custom_filename: Custom filename (overrides default for artifact_type)

    Returns:
        Artifact content as string

    Raises:
        ValueError: If artifact_type is unknown and no custom_filename provided
        FileNotFoundError: If artifact file doesn't exist
        IOError: If file read fails

    Example:
        >>> content = read_artifact("001-oauth2-authentication", "spec")
        >>> print(content[:50])
        # Feature Specification

        OAuth2 authentication...
    """
    # Determine filename
    if custom_filename:
        filename = custom_filename
    elif artifact_type in ARTIFACT_TYPES:
        filename = ARTIFACT_TYPES[artifact_type]
    else:
        raise ValueError(
            f"Unknown artifact type '{artifact_type}'. "
            f"Provide custom_filename or use one of: {list(ARTIFACT_TYPES.keys())}"
        )

    # Read artifact file
    artifact_path = Path(base_dir) / feature_id / filename

    try:
        return artifact_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    except IOError as e:
        raise IOError(f"Failed to read artifact: {e}")


def artifact_exists(
    feature_id: str,
    artifact_type: str,
    base_dir: str = "specs",
    custom_filename: Optional[str] = None,
) -> bool:
    """
    Check if artifact file exists.

    Args:
        feature_id: Feature identifier
        artifact_type: Type of artifact
        base_dir: Base directory for specs (default: "specs")
        custom_filename: Custom filename (overrides default for artifact_type)

    Returns:
        True if artifact exists, False otherwise

    Example:
        >>> if artifact_exists("001-oauth2-authentication", "spec"):
        ...     content = read_artifact("001-oauth2-authentication", "spec")
    """
    # Determine filename
    if custom_filename:
        filename = custom_filename
    elif artifact_type in ARTIFACT_TYPES:
        filename = ARTIFACT_TYPES[artifact_type]
    else:
        return False

    artifact_path = Path(base_dir) / feature_id / filename
    return artifact_path.exists() and artifact_path.is_file()


def list_artifacts(feature_id: str, base_dir: str = "specs") -> List[str]:
    """
    List all artifacts for a feature.

    Args:
        feature_id: Feature identifier
        base_dir: Base directory for specs (default: "specs")

    Returns:
        List of artifact filenames

    Example:
        >>> artifacts = list_artifacts("001-oauth2-authentication")
        >>> print(artifacts)
        ['spec.md', 'plan.md', 'data-model.md']
    """
    feature_path = Path(base_dir) / feature_id

    if not feature_path.exists():
        return []

    artifacts = []
    for file_path in feature_path.rglob("*"):
        if file_path.is_file():
            # Get relative path from feature directory
            relative_path = file_path.relative_to(feature_path)
            artifacts.append(str(relative_path))

    return sorted(artifacts)


def write_contract(
    feature_id: str,
    contract_name: str,
    content: str,
    base_dir: str = "specs",
) -> Path:
    """
    Write API contract file to contracts/ directory.

    Args:
        feature_id: Feature identifier
        contract_name: Contract filename (e.g., "api.yaml", "events.yaml")
        content: Contract content
        base_dir: Base directory for specs (default: "specs")

    Returns:
        Path to written contract file

    Raises:
        IOError: If file write fails

    Example:
        >>> path = write_contract(
        ...     "001-oauth2-authentication",
        ...     "api.yaml",
        ...     "openapi: 3.0.0\\n..."
        ... )
        >>> print(path)
        specs/001-oauth2-authentication/contracts/api.yaml
    """
    # Ensure contracts directory exists
    contracts_path = Path(base_dir) / feature_id / "contracts"
    contracts_path.mkdir(parents=True, exist_ok=True)

    # Write contract file
    contract_path = contracts_path / contract_name

    try:
        contract_path.write_text(content, encoding="utf-8")
        return contract_path
    except IOError as e:
        raise IOError(f"Failed to write contract: {e}")


def read_contract(
    feature_id: str,
    contract_name: str,
    base_dir: str = "specs",
) -> str:
    """
    Read API contract file from contracts/ directory.

    Args:
        feature_id: Feature identifier
        contract_name: Contract filename (e.g., "api.yaml")
        base_dir: Base directory for specs (default: "specs")

    Returns:
        Contract content as string

    Raises:
        FileNotFoundError: If contract file doesn't exist
        IOError: If file read fails

    Example:
        >>> content = read_contract("001-oauth2-authentication", "api.yaml")
    """
    contract_path = Path(base_dir) / feature_id / "contracts" / contract_name

    try:
        return contract_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Contract not found: {contract_path}")
    except IOError as e:
        raise IOError(f"Failed to read contract: {e}")


def list_contracts(feature_id: str, base_dir: str = "specs") -> List[str]:
    """
    List all contract files for a feature.

    Args:
        feature_id: Feature identifier
        base_dir: Base directory for specs (default: "specs")

    Returns:
        List of contract filenames

    Example:
        >>> contracts = list_contracts("001-oauth2-authentication")
        >>> print(contracts)
        ['api.yaml', 'events.yaml']
    """
    contracts_path = Path(base_dir) / feature_id / "contracts"

    if not contracts_path.exists():
        return []

    contracts = []
    for file_path in contracts_path.iterdir():
        if file_path.is_file():
            contracts.append(file_path.name)

    return sorted(contracts)


def get_feature_path(feature_id: str, base_dir: str = "specs") -> Path:
    """
    Get path to feature directory.

    Args:
        feature_id: Feature identifier
        base_dir: Base directory for specs (default: "specs")

    Returns:
        Path to feature directory

    Example:
        >>> path = get_feature_path("001-oauth2-authentication")
        >>> print(path)
        specs/001-oauth2-authentication
    """
    return Path(base_dir) / feature_id


def feature_exists(feature_id: str, base_dir: str = "specs") -> bool:
    """
    Check if feature directory exists.

    Args:
        feature_id: Feature identifier
        base_dir: Base directory for specs (default: "specs")

    Returns:
        True if feature directory exists, False otherwise

    Example:
        >>> if feature_exists("001-oauth2-authentication"):
        ...     artifacts = list_artifacts("001-oauth2-authentication")
    """
    feature_path = Path(base_dir) / feature_id
    return feature_path.exists() and feature_path.is_dir()


def list_features(base_dir: str = "specs") -> List[Dict[str, str]]:
    """
    List all features in the specs directory.

    Args:
        base_dir: Base directory for specs (default: "specs")

    Returns:
        List of feature info dictionaries with 'id' and 'path' keys

    Example:
        >>> features = list_features()
        >>> for feature in features:
        ...     print(f"{feature['id']}: {len(list_artifacts(feature['id']))} artifacts")
    """
    specs_path = Path(base_dir)

    if not specs_path.exists():
        return []

    features = []
    for feature_dir in specs_path.iterdir():
        if feature_dir.is_dir() and not feature_dir.name.startswith("."):
            features.append({"id": feature_dir.name, "path": str(feature_dir)})

    return sorted(features, key=lambda x: x["id"])
