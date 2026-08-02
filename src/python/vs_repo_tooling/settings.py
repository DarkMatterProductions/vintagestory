"""Pydantic-settings models for the Vintage Story Docker build pipeline."""
from typing import Dict, List, Tuple

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DOTNET_VERSION_BY_VS: Dict[str, str] = {
    "1.21": "8.0",
    "1.22": "10.0",
}


class DevBuildSettings(BaseSettings):
    """Configuration for the dev build pipeline (build-dev.sh equivalent)."""
    image_name: str = "vintagestory"
    python_version: str = "3.11.9"
    docker_context: str = "remote-engine"
    dotnet_version_by_vs: Dict[str, str] = dict(DOTNET_VERSION_BY_VS)
    repositories: List[str] = ["dcr.dmpsys.in/vintagestory", "ghcr.io/darkmatterproductions/vintagestory", "ralnoc/vintagestory"]
    # Unprefixed: these mirror the GHCR_TOKEN/GHCR_USERNAME/DOCKERHUB_TOKEN/
    # DOCKERHUB_USERNAME env vars the bash scripts already relied on, set
    # externally by CI (not VS_BUILD_-namespaced).
    ghcr_token: str = Field(default="", validation_alias="GHCR_TOKEN")
    ghcr_username: str = Field(default="", validation_alias="GHCR_USERNAME")
    dockerhub_token: str = Field(default="", validation_alias="DOCKERHUB_TOKEN")
    dockerhub_username: str = Field(default="", validation_alias="DOCKERHUB_USERNAME")

    model_config = SettingsConfigDict(env_prefix="VS_BUILD_")

    @property
    def registry_credentials(self) -> Dict[str, Dict[str, Tuple[str, str] | bool]]:
        """Maps a registry host to its (username, token) login credentials."""
        return {
            "ghcr.io": {"credentials": (self.ghcr_username, self.ghcr_token), "authenticated": True},
            "docker.io": {"credentials": (self.dockerhub_username, self.dockerhub_token), "authenticated": True},
            "dcr.dmpsys.in": {"credentials": ("XX", "XX"), "authenticated": False},
        }


class ReleaseBuildSettings(DevBuildSettings):
    """Configuration for the release build pipeline (build-release.sh equivalent)."""

    repositories: List[str] = [
        "ghcr.io/darkmatterproductions/vintagestory",
        "ralnoc/vintagestory",
    ]
