"""
Get the external IP address of the GCP ORS instance.
This script queries Google Cloud Platform to find the current IP of the ORS instance.
"""
import subprocess
import json
import sys
from pathlib import Path
from config import get_config
from logger import get_logger

logger = get_logger(__name__)

# Default instance name from deploy script
DEFAULT_INSTANCE_NAME = "ors-kenya-server"
DEFAULT_ZONE = "us-central1-a"


def get_gcp_instance_ip(instance_name: str = None, zone: str = None) -> str:
    """
    Get the external IP address of a GCP Compute Engine instance.
    
    Args:
        instance_name: Name of the GCP instance (default from deploy script)
        zone: Zone of the instance (default from deploy script)
    
    Returns:
        External IP address as string, or None if not found
    
    Raises:
        subprocess.CalledProcessError: If gcloud command fails
        FileNotFoundError: If gcloud is not installed
    """
    if instance_name is None:
        instance_name = DEFAULT_INSTANCE_NAME
    if zone is None:
        zone = DEFAULT_ZONE
    
    logger.info(f"Querying GCP for instance '{instance_name}' in zone '{zone}'...")
    
    try:
        # Get instance details in JSON format
        cmd = [
            'gcloud', 'compute', 'instances', 'describe',
            instance_name,
            '--zone', zone,
            '--format', 'json'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        instance_data = json.loads(result.stdout)
        
        # Extract external IP
        network_interfaces = instance_data.get('networkInterfaces', [])
        if network_interfaces:
            access_configs = network_interfaces[0].get('accessConfigs', [])
            if access_configs:
                external_ip = access_configs[0].get('natIP')
                if external_ip:
                    logger.info(f"Found external IP: {external_ip}")
                    return external_ip
        
        logger.warning("No external IP found for instance")
        return None
        
    except FileNotFoundError:
        logger.error("gcloud CLI not found. Please install Google Cloud SDK.")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to query GCP: {e.stderr}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse GCP response: {e}")
        raise


def list_gcp_instances():
    """
    List all GCP Compute Engine instances to help find the ORS instance.
    
    Returns:
        List of instance names
    """
    logger.info("Listing GCP Compute Engine instances...")
    
    try:
        cmd = [
            'gcloud', 'compute', 'instances', 'list',
            '--format', 'json'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        instances = json.loads(result.stdout)
        
        if not instances:
            logger.info("No instances found")
            return []
        
        logger.info(f"Found {len(instances)} instance(s):")
        for instance in instances:
            name = instance.get('name', 'unknown')
            zone = instance.get('zone', '').split('/')[-1]
            status = instance.get('status', 'unknown')
            
            # Get external IP
            network_interfaces = instance.get('networkInterfaces', [])
            external_ip = None
            if network_interfaces:
                access_configs = network_interfaces[0].get('accessConfigs', [])
                if access_configs:
                    external_ip = access_configs[0].get('natIP', 'None')
            
            logger.info(f"  - {name} (zone: {zone}, status: {status}, IP: {external_ip})")
        
        return instances
        
    except FileNotFoundError:
        logger.error("gcloud CLI not found. Please install Google Cloud SDK.")
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list instances: {e.stderr}")
        return []


def update_config_with_ip(ip_address: str, config_path: Path = None):
    """
    Update config.yaml with the new IP address.
    
    Args:
        ip_address: New IP address to set
        config_path: Path to config.yaml (default: project root)
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return False
    
    try:
        import yaml
        
        # Read current config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update IP
        old_ip = config.get('ors', {}).get('base_url', '').split('//')[1].split(':')[0] if '//' in config.get('ors', {}).get('base_url', '') else None
        
        base_url = f"http://{ip_address}:8080/ors"
        health_url = f"http://{ip_address}:8080/ors/v2/health"
        
        config['ors']['base_url'] = base_url
        config['ors']['health_url'] = health_url
        
        # Write back
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Updated config.yaml:")
        if old_ip:
            logger.info(f"  Old IP: {old_ip}")
        logger.info(f"  New IP: {ip_address}")
        logger.info(f"  Base URL: {base_url}")
        logger.info(f"  Health URL: {health_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update config.yaml: {e}", exc_info=True)
        return False


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Get external IP address of GCP ORS instance'
    )
    parser.add_argument(
        '--instance-name',
        default=DEFAULT_INSTANCE_NAME,
        help=f'GCP instance name (default: {DEFAULT_INSTANCE_NAME})'
    )
    parser.add_argument(
        '--zone',
        default=DEFAULT_ZONE,
        help=f'GCP zone (default: {DEFAULT_ZONE})'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all GCP instances to find the ORS instance'
    )
    parser.add_argument(
        '--update-config',
        action='store_true',
        help='Automatically update config.yaml with the found IP'
    )
    
    args = parser.parse_args()
    
    try:
        if args.list:
            list_gcp_instances()
            return
        
        # Get IP
        ip_address = get_gcp_instance_ip(args.instance_name, args.zone)
        
        if ip_address:
            print(f"\n✓ Found external IP: {ip_address}")
            print(f"  ORS URL: http://{ip_address}:8080/ors")
            
            if args.update_config:
                if update_config_with_ip(ip_address):
                    print(f"\n✓ Config.yaml updated successfully")
                    print(f"  You can now test the connection with: python check_ors.py")
                else:
                    print(f"\n✗ Failed to update config.yaml")
            else:
                print(f"\nTo update config.yaml, run:")
                print(f"  python get_gcp_ors_ip.py --update-config")
                print(f"\nOr manually update config.yaml:")
                print(f"  ors:")
                print(f"    base_url: \"http://{ip_address}:8080/ors\"")
                print(f"    health_url: \"http://{ip_address}:8080/ors/v2/health\"")
        else:
            print(f"\n✗ Could not find external IP for instance '{args.instance_name}'")
            print(f"  Try listing instances: python get_gcp_ors_ip.py --list")
            sys.exit(1)
            
    except FileNotFoundError:
        print("\n✗ Error: gcloud CLI not found")
        print("  Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error querying GCP: {e.stderr}")
        print("  Make sure you're authenticated: gcloud auth login")
        print("  And have the correct project set: gcloud config set project YOUR_PROJECT")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

