"""
acpctl Storage Layer

File system operations for artifacts, constitution, and project structure.

Modules:
- artifacts: Spec/plan/code artifact file management
- constitution: Constitutional template creation and loading
"""

from acpctl.storage.artifacts import (
    ARTIFACT_TYPES,
    artifact_exists,
    create_feature_directory,
    feature_exists,
    get_feature_path,
    list_artifacts,
    list_contracts,
    list_features,
    read_artifact,
    read_contract,
    write_artifact,
    write_contract,
)
from acpctl.storage.constitution import (
    constitution_exists,
    create_acp_directory_structure,
    create_constitution_template,
    get_constitution_path,
    load_constitution,
    update_constitution,
    validate_constitution_structure,
)

__all__ = [
    # Artifacts
    "ARTIFACT_TYPES",
    "create_feature_directory",
    "write_artifact",
    "read_artifact",
    "artifact_exists",
    "list_artifacts",
    "write_contract",
    "read_contract",
    "list_contracts",
    "get_feature_path",
    "feature_exists",
    "list_features",
    # Constitution
    "create_constitution_template",
    "load_constitution",
    "constitution_exists",
    "get_constitution_path",
    "update_constitution",
    "create_acp_directory_structure",
    "validate_constitution_structure",
]
