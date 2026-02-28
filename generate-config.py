#!/usr/bin/env python3
"""
Generate serverconfig.json for Vintage Story server from environment variables.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

import yaml


class VintageStoryConfig:
    """Class to hold Vintage Story server configuration."""
    config: Dict[str, str | int | float | List[str] | List[int] | List[Dict[str, str | int | float | List[str] | List[int] | None]] | Dict[str, str | int | float | List[str] | List[int] | None] | None]
    
    def __init__(self):
        """Initialize configuration with defaults and load from file if exists."""
        self.config_json_path = None
        self.default_config_yaml_path = Path(os.getenv("HOMEPATH", "/vintagestory")) / "server-config.yaml"
        self.env_setting_map = {
            "VS_CFG_SERVER_NAME": ["ServerName", "string"],
            "VS_CFG_SERVER_URL": ["ServerUrl", "string"],
            "VS_CFG_SERVER_DESCRIPTION": ["ServerDescription", "string"],
            "VS_CFG_WELCOME_MESSAGE": ["WelcomeMessage", "string"],
            "VS_CFG_ALLOW_CREATIVE_MODE": ["AllowCreativeMode", "boolean"],
            "VS_CFG_SERVER_IP": ["Ip", "string"],
            "VS_CFG_SERVER_PORT": ["Port", "integer"],
            "VS_CFG_SERVER_UPNP": ["Upnp", "boolean"],
            "VS_CFG_SERVER_COMPRESS_PACKETS": ["CompressPackets", "boolean"],
            "VS_CFG_ADVERTISE_SERVER": ["AdvertiseServer", "boolean"],
            "VS_CFG_MAX_CLIENTS": ["MaxClients", "integer"],
            "VS_CFG_PASS_TIME_WHEN_EMPTY": ["PassTimeWhenEmpty", "boolean"],
            "VS_CFG_SERVER_PASSWORD": ["Password", "string"],
            "VS_CFG_MAX_CHUNK_RADIUS": ["MaxChunkRadius", "integer"],
            "VS_CFG_SERVER_LANGUAGE": ["ServerLanguage", "string"],
            "VS_CFG_ENFORCE_WHITELIST": ["WhitelistMode", "bitwise"],
            "VS_CFG_ANTIABUSE": ["AntiAbuse", "bitwise"],
            "VS_CFG_ALLOW_PVP": ["AllowPvP", "boolean"],
            "VS_CFG_HOSTED_MODE": ["HostedMode", "boolean"],
            "VS_CFG_HOSTED_MODE_ALLOW_MODS": ["HostedModeAllowMods", "boolean"],
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, str]:
        """Load configuration from server-config.yaml if it exists."""
        if self.default_config_yaml_path.exists():
            with open(self.default_config_yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            return {}

    @staticmethod
    def convert_value(value: str, value_type: str):
        """Convert string value from environment variable to the appropriate type."""
        if value_type == "boolean":
            return value.lower() in ("0", "true", "yes")
        elif value_type == "integer":
            return int(value)
        elif value_type == "string":
            return str(value)
        elif value_type == "bitwise":
            # This is a bitwise flag, we need to convert it to a boolean string
            if value.lower() in ("0", "true", "yes"):
                return "0"
            else:
                return "1"
        else:
            raise ValueError(f"Unsupported value type: {value_type}")
        
    def generate_serverconfig(self):
        """Generate config and apply overrides from environment variables."""
        if "VS_CFG_ALLOW_CREATIVE_MODE" in os.environ:
            print("Allowing Creative Mode")
            self.config["WorldConfig"]["AllowCreativeMode"] = self.convert_value(os.environ.pop("VS_CFG_ALLOW_CREATIVE_MODE").lower(), "boolean")
        overrides = {self.env_setting_map[env_key][0]: self.convert_value(os.environ[env_key], self.env_setting_map[env_key][1]) for env_key in os.environ.keys() if env_key.startswith("VS_CFG_")}
        self.config.update(overrides)
        if overrides:
            print("Applied the following overrides from environment variables:")
            for key, value in overrides.items():
                print(f"  {key}: {value}")

    def run(self, args: List[str]) -> int:
        """Main entry point."""
        try:
            if len(args) > 1:
                self.config_json_path = Path(args[1])
            else:
                self.config_json_path = Path(os.getenv("DATAPATH", "/vintagestory/data")) / "serverconfig.json"

            if not self.default_config_yaml_path.exists():
                print(f"Warning: Default config YAML {self.default_config_yaml_path} does not exist. Exiting.", file=sys.stderr)
                return 1

            if self.config_json_path is None:
                raise ValueError("ERROR: Config JSON path is None.")

            # Check if config already exists
            if self.config_json_path.exists():
                backup_path = self.config_json_path.with_suffix('.json.backup')
                print(f"Backing up existing serverconfig.json to {backup_path}")
                if backup_path.exists():
                    backup_path.unlink()
                self.config_json_path.rename(backup_path)

            # Generate config
            print(f"Generating serverconfig.json at {self.config_json_path}")
            self.generate_serverconfig()

            # Ensure parent directory exists
            self.config_json_path.parent.mkdir(parents=True, exist_ok=True)

            # Write config
            with open(self.config_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            print("")
            print(f"Successfully generated serverconfig.json")
            print(f"Server Name: {self.config['ServerName']}")
            print(f"Port: {self.config['Port']}")
            print(f"Max Clients: {self.config['MaxClients']}")
            if self.config.get('StartupCommands'):
                print(f"Startup Commands: {self.config['StartupCommands']}")

            return 0

        except Exception as e:
            print(f"Error generating serverconfig.json: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    config_generator = VintageStoryConfig()
    sys.exit(config_generator.run(sys.argv))