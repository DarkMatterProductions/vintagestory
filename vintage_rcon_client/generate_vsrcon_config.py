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


def get_env_value(key, default_value):
    """
    Get configuration value from environment variable or use default.

    Args:
        key: Environment variable key (without prefix)
        default_value: Default value if env var not set

    Returns:
        Value from environment or default, converted to appropriate type
    """
    env_key = f"VS_RCON_SERVER_CFG_{key.upper()}"
    env_value = os.environ.get(env_key)

    if env_value is not None:
        # Convert to appropriate type based on default value
        if isinstance(default_value, int):
            try:
                return int(env_value)
            except ValueError:
                print(f"Warning: Invalid integer value for {env_key}='{env_value}', using default: {default_value}",
                      file=sys.stderr)
                return default_value
        elif isinstance(default_value, str):
            return env_value
        else:
            return env_value

    return default_value


def generate_config():
    """
    Generate vsrcon.json configuration from environment variables.

    Returns:
        dict: Configuration dictionary
    """
    config = {
        "Port": get_env_value("port", 42425),
        "IP": get_env_value("ip", "127.0.0.1"),
        "Password": get_env_value("password", "changeme"),
        "Timeout": get_env_value("timeout", 20),
        "MaxConnections": get_env_value("maxconnections", 10)
    }

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

    # Show environment variables if requested
    if args.show_env:
        print("Environment variables:")
        env_vars = [
            {"var_name": "VS_RCON_SERVER_CFG_PORT", "default_value": "42425"},
            {"var_name": "VS_RCON_SERVER_CFG_IP", "default_value": "127.0.0.1"},
            {"var_name": "VS_RCON_SERVER_CFG_PASSWORD", "default_value": "changeme"},
            {"var_name": "VS_RCON_SERVER_CFG_TIMEOUT", "default_value": "20"},
            {"var_name": "VS_RCON_SERVER_CFG_MAXCONNECTIONS", "default_value": "10"}
        ]
        for var in env_vars:
            value = os.environ.get(var["var_name"], var["default_value"])
            # Mask password
            if "PASSWORD" in var["var_name"]:
                value = "***" + value[-3:] if len(value) > 3 else "***"
            print(f"  {var['var_name']} = {value}")
        print()

    # Generate configuration
    config = generate_config()

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

