import argparse
import logging
import os
from pathlib import Path
from traceback import format_exc

import yaml

from output import step_header_string, color_action, color_action_var, \
    section_header_string, color_error, color_success, step_footer_string, section_footer_string

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def env_override(key_path, default_value, full_key_name=False):
    """Get config value from environment variable or use default"""
    if full_key_name:
        env_key = key_path.upper()
    else:
        env_key = f"VS_RCON_CLIENT_CFG_{key_path.upper()}"
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

def apply_env_overrides(cfg, prefix="", indent=0):
    """Recursively iterate over config and apply env_override for each leaf item."""
    for key, value in cfg.items():
        key_path = f"{prefix}_{key}" if prefix else key
        print(color_action(f"{' ' * indent * 2}Processing config key: {color_action_var(key_path)}"))
        if isinstance(value, dict):
            print(color_action(f"{' ' * indent * 2}Recursing into nested config for key: {color_action_var(key_path)}"))
            apply_env_overrides(value, key_path, indent=indent + 1)
        else:
            if logger.getEffectiveLevel() == logging.DEBUG:
                print(color_action(f"{' ' * indent * 2}Applying env override for key: {color_action_var(key_path)} with the value: {color_action_var(value)}"))
            else:
                print(color_action(f"{' ' * indent * 2}Applying env override for key: {color_action_var(key_path)}"))
            cfg[key] = env_override(key_path, value, full_key_name=True if prefix else False)


def load_config(config_path: Path):
    config = {}
    print(color_action(f"Checking on existing configuration file at: {color_action_var(str(config_path))}"))
    if config_path.exists():
        print(color_action("Existing configuration file found, loading..."), end="")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(color_action(" Done."))
        except Exception as e:
            print(color_error("Failed to load existing configuration file."))
            print(color_error(format_exc()))
            logger.error(f"Error loading configuration: {e}")
            raise

    print(step_header_string("Applying environment variable overrides"))
    apply_env_overrides(config)
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
        '--loglevel',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL','debug', 'info', 'warning', 'error', 'critical'],
        help='Change log level'
    )

    args = parser.parse_args()

    if args.loglevel:
        logger.setLevel(getattr(logging, args.loglevel.upper(), logging.INFO))

    print(section_header_string(f"Vintage Story RCon Client Configuration"))

    config_path = Path(args.file)
    config = load_config(config_path)

    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    print(color_success(f"Configuration saved to {config_path}"))
    print(step_footer_string())
    print(section_footer_string())

if __name__ == "__main__":
    main()