#!/usr/bin/env python3
"""
Generate vsrcon.json configuration file from environment variables

Environment variables (with VS_RCON_SERVER_CFG_ prefix):
  VS_RCON_SERVER_CFG_PORT          - RCON server port (default: 42425)
  VS_RCON_SERVER_CFG_IP            - RCON server IP (default: 127.0.0.1)
  VS_RCON_SERVER_CFG_PASSWORD      - RCON password (default: changeme)
  VS_RCON_SERVER_CFG_TIMEOUT       - Connection timeout in seconds (default: 20)
  VS_RCON_SERVER_CFG_MAXCONNECTIONS - Maximum connections (default: 10)

Usage:
  python generate_vsrcon_config.py -f /path/to/vsrcon.json
  python generate_vsrcon_config.py --file ./config/vsrcon.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict


def get_env_value(key, default_value):
    """
    Get configuration value from environment variable or use default.

    Args:
        key: Environment variable key (without prefix)
        default_value: Default value if env var not set

    Returns:
        Value from environment or default, converted to appropriate type
    """
    # env_key = f"VS_RCON_SERVER_CFG_{key.upper()}"
    env_value = os.environ.get(key.upper())

    if env_value is not None:
        # Convert to appropriate type based on default value
        if isinstance(default_value, int):
            try:
                return int(env_value)
            except ValueError:
                print(f"Warning: Invalid integer value for {key}='{env_value}', using default: {default_value}",
                      file=sys.stderr)
                return default_value
        elif isinstance(default_value, str):
            return env_value
        else:
            return env_value

    return default_value


def generate_config(arguments):
    """
    Generate vsrcon.json configuration from environment variables.

    Returns:
        dict: Configuration dictionary
    """
    env_vars = [
        {"var_name": "VS_RCON_SERVER_CFG_PORT", "default_value": "42425", "config_key": "Port"},
        {"var_name": "VS_RCON_SERVER_CFG_IP", "default_value": "127.0.0.1", "config_key": "IP"},
        {"var_name": "VS_RCON_SERVER_CFG_PASSWORD", "default_value": "changeme", "config_key": "Password"},
        {"var_name": "VS_RCON_SERVER_CFG_TIMEOUT", "default_value": "20", "config_key": "Timeout"},
        {"var_name": "VS_RCON_SERVER_CFG_MAXCONNECTIONS", "default_value": "10", "config_key": "MaxConnections"},
    ]
    config = {}
    for cidx in range(len(env_vars)):
        config[env_vars[cidx]["config_key"]] = get_env_value(env_vars[cidx]["var_name"], env_vars[cidx]["default_value"])
        if arguments.show_env:
            # Show environment variables if requested
            print("Environment variables:")
            # Mask password
            value = '***' if 'password' in env_vars[cidx]['var_name'] else config[env_vars[cidx]['config_key']]
            print(f"  {env_vars[cidx]['var_name']} = {value}")
            print()

    return config


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate vsrcon.json configuration file from environment variables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  VS_RCON_SERVER_CFG_PORT            RCON server port (default: 42425)
  VS_RCON_SERVER_CFG_IP              RCON server IP (default: 127.0.0.1)
  VS_RCON_SERVER_CFG_PASSWORD        RCON password (default: changeme)
  VS_RCON_SERVER_CFG_TIMEOUT         Connection timeout (default: 20)
  VS_RCON_SERVER_CFG_MAXCONNECTIONS  Max connections (default: 10)

Examples:
  # Generate with defaults
  python generate_vsrcon_config.py -f /path/to/vsrcon.json
  
  # Generate with environment variables
  export VS_RCON_SERVER_CFG_PORT=25575
  export VS_RCON_SERVER_CFG_PASSWORD=mysecret
  python generate_vsrcon_config.py -f ./vsrcon.json
  
  # One-liner with inline env vars
  VS_RCON_SERVER_CFG_PORT=25575 python generate_vsrcon_config.py -f vsrcon.json
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

    args = parser.parse_args()

    # Generate configuration
    config = generate_config(args)

    # Create output directory if it doesn't exist
    output_path = Path(args.file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write configuration file
    try:
        with open(output_path, 'w') as f:
            if args.pretty:
                json.dump(config, f, indent=2)
            else:
                json.dump(config, f)

        print(f"✓ Configuration written to: {output_path}")
        return 0

    except PermissionError:
        print(f"Error: Permission denied writing to {output_path}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: Failed to write configuration: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

