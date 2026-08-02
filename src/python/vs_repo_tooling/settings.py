"""Pydantic-settings models for the Vintage Story Docker build pipeline."""
from typing import Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DOTNET_VERSION_BY_VS: Dict[str, str] = {
    "1.21": "8.0",
    "1.22": "10.0",
}


class DevBuildSettings(BaseSettings):
    """Configuration for the dev build pipeline (build-dev.sh equivalent)."""

    model_config = SettingsConfigDict(env_prefix="VS_BUILD_")

    registry_host: str = "dcr.dmpsys.in"
    image_name: str = "vintagestory"
    python_version: str = "3.11.9"
    docker_context: str = "remote-engine"
    dotnet_version_by_vs: Dict[str, str] = dict(DOTNET_VERSION_BY_VS)
    repositories: List[str] = []
    # Unprefixed: these mirror the GHCR_TOKEN/GHCR_USERNAME env vars the bash
    # scripts already relied on, set externally by CI (not VS_BUILD_-namespaced).
    ghcr_token: str = Field(default="", validation_alias="GHCR_TOKEN")
    ghcr_username: str = Field(default="", validation_alias="GHCR_USERNAME")


class ReleaseBuildSettings(DevBuildSettings):
    """Configuration for the release build pipeline (build-release.sh equivalent)."""

    repositories: List[str] = [
        "ghcr.io/darkmatterproductions/vintagestory",
        "ralnoc/vintagestory",
    ]
