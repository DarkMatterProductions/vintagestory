import argparse
import logging
import os
from argparse import Namespace
from pathlib import Path
from traceback import format_exc

import yaml

from output import step_header_string, color_action, color_action_var, \
    section_header_string, color_error, color_success, step_footer_string, section_footer_string, strip_ansi_color_codes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def env_override(args: Namespace, key_path, default_value):
    """Get config value from the environment variable or use default"""
    # if full_key_name:
    #     env_key = key_path.upper()
    # else:
    env_key = f"VS_RCON_CLIENT_CFG_{key_path.upper()}"
    if logger.getEffectiveLevel() == logging.DEBUG:
        msg = color_action(f"Checking environment variable: {color_action_var(env_key)} for config key: {color_action_var(key_path)} with default value: {color_action_var(default_value)}")
        print(strip_ansi_color_codes(msg) if args.monochrome else msg)
    else:
        msg = color_error(f"Environment variable {color_action_var(env_key)} not set, using default value: {color_action_var(default_value)}")
        print(strip_ansi_color_codes(msg) if args.monochrome else msg)
    env_value = os.environ.get(env_key)
    if env_value is not None:
        # Convert string to appropriate type
        if isinstance(default_value, bool):
            return env_value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default_value, int):
            return int(env_value)
        elif isinstance(default_value, list):
            return [item.strip() for item in env_value.split(',')]
        return env_value
    return default_value

def apply_env_overrides(args: Namespace, cfg, prefix="", indent=0):
    """Recursively iterate over config and apply env_override for each leaf item."""
    for key, value in cfg.items():
        key_path = f"{prefix}_{key}" if prefix else key
        msg = color_action(f"{' ' * indent * 2}Processing config key: {color_action_var(key_path)}")
        print(strip_ansi_color_codes(msg) if args.monochrome else msg)
        if isinstance(value, dict):
            msg = color_action(f"{' ' * indent * 2}Recursing into nested config for key: {color_action_var(key_path)}")
            print(strip_ansi_color_codes(msg) if args.monochrome else msg)
            apply_env_overrides(args, value, key_path, indent=indent + 1)
        else:
            if logger.getEffectiveLevel() == logging.DEBUG:
                msg = color_action(f"{' ' * indent * 2}Applying env override for key: {color_action_var(key_path)} with the value: {color_action_var(value)}")
                print(strip_ansi_color_codes(msg) if args.monochrome else msg)
            else:
                msg = color_action(f"{' ' * indent * 2}Applying env override for key: {color_action_var(key_path)}")
                print(strip_ansi_color_codes(msg) if args.monochrome else msg)
            cfg[key] = env_override(args, key_path, value)


def generate_new_config(args: Namespace, config_path: Path):
    msg = color_action(f"No existing configuration file found at: {color_action_var(str(config_path))}")
    print(strip_ansi_color_codes(msg) if args.monochrome else msg)
    msg = color_action("Generating new configuration with default values...")
    print(strip_ansi_color_codes(msg) if args.monochrome else msg, end="")
    config = {
        "server": {
            "host": env_override(args, "server_host", "0.0.0.0"),
            "port": env_override(args, "server_port", 5000),
            "secret_key": env_override(args, "server_secret_key", "vintage-story-rcon-client-secret-key-change-me")
        },
        "rcon": {
            "default_host": env_override(args, "rcon_default_host", "localhost"),
            "default_port": env_override(args, "rcon_default_port", 42425),
            "password": env_override(args, "rcon_password", "changeme"),
            "locked_address": env_override(args, "rcon_locked_address", False),
            "timeout": env_override(args, "rcon_timeout", 10),
            "max_message_size": env_override(args, "rcon_max_message_size", 4096)
        },
        "security": {
            "require_auth": env_override(args, "security_require_auth", True),
            "traditional_login_enabled": env_override(args, "security_traditional_login_enabled", True),
            "default_username": env_override(args, "security_default_username", "admin"),
            "default_password": env_override(args, "security_default_password", "changeme"),
            "max_login_attempts": env_override(args, "security_max_login_attempts", 5),
            "lockout_duration": env_override(args, "security_lockout_duration", 300),
            "oauth": {
                "enabled": env_override(args, "security_oauth_enabled", False),
                "authorized_emails": env_override(args, "security_oauth_authorized_emails", [
                    "admin@example.com",
                    "user@example.com"
                ]),
                "google": {
                    "enabled": env_override(args, "security_oauth_google_enabled", True),
                    "client_id": env_override(args, "security_oauth_google_client_id", "your-google-client-id.apps.googleusercontent.com"),
                    "client_secret": env_override(args, "security_oauth_google_client_secret", "your-google-client-secret")
                },
                "facebook": {
                    "enabled": env_override(args, "security_oauth_facebook_enabled", False),
                    "client_id": env_override(args, "security_oauth_facebook_client_id", "your-facebook-app-id"),
                    "client_secret": env_override(args, "security_oauth_facebook_client_secret", "your-facebook-app-secret")
                },
                "github": {
                    "enabled": env_override(args, "security_oauth_github_enabled", False),
                    "client_id": env_override(args, "security_oauth_github_client_id", "your-github-client-id"),
                    "client_secret": env_override(args, "security_oauth_github_client_secret", "your-github-client-secret")
                },
                "apple": {
                    "enabled": env_override(args, "security_oauth_apple_enabled", False),
                    "client_id": env_override(args, "security_oauth_apple_client_id", "your-apple-service-id"),
                    "client_secret": env_override(args, "security_oauth_apple_client_secret", "your-apple-client-secret"),
                    "team_id": env_override(args, "security_oauth_apple_team_id", "your-apple-team-id"),
                    "key_id": env_override(args, "security_oauth_apple_key_id", "your-apple-key-id")
                }
            }
        },
        "logging": {
            "log_commands": env_override(args, "logging_log_commands", True),
            "log_file": env_override(args, "logging_log_file", "logs/rcon.log"),
            "log_level": env_override(args, "logging_log_level", "INFO")
        }
    }
    msg = color_success(" Done.")
    print(strip_ansi_color_codes(msg) if args.monochrome else msg)
    return config

def load_config(args: Namespace, config_path: Path):
    config = {}
    msg = color_action(f"Checking on existing configuration file at: {color_action_var(str(config_path))}")
    print(strip_ansi_color_codes(msg) if args.monochrome else msg)
    if config_path.exists():
        msg = color_action("Existing configuration file found, loading...")
        print(strip_ansi_color_codes(msg) if args.monochrome else msg, end="")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            msg = color_success(" Done.")
            print(strip_ansi_color_codes(msg) if args.monochrome else msg)
        except Exception as e:
            msg = color_error("Failed to load existing configuration file.")
            print(strip_ansi_color_codes(msg) if args.monochrome else msg)
            msg = color_error(format_exc())
            print(strip_ansi_color_codes(msg) if args.monochrome else msg)
            logger.error(f"Error loading configuration: {e}")
            raise
    else:
        msg = color_action("No existing configuration file found, generating new one...")
        print(strip_ansi_color_codes(msg) if args.monochrome else msg, end="")
        config = generate_new_config(args, config_path)
        msg = color_success(" Done.")
        print(strip_ansi_color_codes(msg) if args.monochrome else msg)

    msg = step_header_string("Applying environment variable overrides")
    print(strip_ansi_color_codes(msg) if args.monochrome else msg)
    apply_env_overrides(args, config)
    return config

def main():
    parser = argparse.ArgumentParser(
        description='Generate vsrcon.json configuration file from environment variables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with defaults
  python generate_vsrconclient_config.py -f /path/to/vsrcon.json
  
  # Generate with environment variables
  export VS_RCON_CLIENT_CFG_SERVER_SECRET_KEY="rcon-secret"
  python generate_vsrconclient_config.py -f ./vsrcon.json
"""
    )

    parser.add_argument(
        '-f', '--file',
        required=True,
        type=str,
        help='Path to output vsrcon.json file'
    )

    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON with indentation (default: compact)'
    )

    parser.add_argument(
        '--show-env',
        action='store_true',
        help='Show environment variables being used'
    )

    parser.add_argument(
        '--monochrome',
        action='store_true',
        help='Disable colored output (useful for CI logs or terminals that do not support ANSI colors)'
    )

    parser.add_argument(
        '--loglevel',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL','debug', 'info', 'warning', 'error', 'critical'],
        help='Change log level'
    )

    args = parser.parse_args()

    if args.loglevel:
        logger.setLevel(getattr(logging, args.loglevel.upper(), logging.INFO))

    msg = section_header_string(f"Vintage Story RCon Client Configuration")
    print(strip_ansi_color_codes(msg) if args.monochrome else msg)

    config_path = Path(args.file)
    config = load_config(args, config_path)

    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    msg = color_success(f"Configuration saved to {config_path}")
    print(strip_ansi_color_codes(msg) if args.monochrome else msg)
    if not args.monochrome:
        print(step_footer_string())
    print(strip_ansi_color_codes(section_footer_string()) if args.monochrome else section_footer_string())

if __name__ == "__main__":
    main()