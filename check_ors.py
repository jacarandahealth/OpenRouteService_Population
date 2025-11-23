"""OpenRouteService health check and connectivity test utility."""
import requests
import time
import openrouteservice
from config import get_config
from logger import get_logger

logger = get_logger(__name__)

# Default GCP instance settings (from deploy_ors.ps1)
DEFAULT_INSTANCE_NAME = "ors-kenya-server"
DEFAULT_ZONE = "us-central1-a"


def check_ors_health(health_url: str = None, timeout: int = 5, max_attempts: int = None):
    """
    Check OpenRouteService health status, waiting until ready.
    
    Args:
        health_url: ORS health check URL. If None, uses config value.
        timeout: Request timeout in seconds.
        max_attempts: Maximum number of attempts. If None, waits indefinitely.
    
    Returns:
        bool: True if ORS is ready, False if max_attempts reached.
    """
    config = get_config()
    if health_url is None:
        health_url = config.ors_health_url
    
    logger.info(f"Checking ORS status at {health_url}...")
    
    attempt = 0
    while max_attempts is None or attempt < max_attempts:
        try:
            response = requests.get(health_url, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                if status == 'ready':
                    logger.info("ORS is READY!")
                    return True
                else:
                    logger.info(f"ORS status: {status} - Waiting...")
            else:
                logger.warning(f"ORS returned status code: {response.status_code} - Waiting...")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Connection failed: {e} - Waiting...")
        except Exception as e:
            logger.error(f"Unexpected error checking ORS health: {e}", exc_info=True)
        
        attempt += 1
        time.sleep(10)
    
    logger.error(f"ORS health check failed after {max_attempts} attempts")
    return False


def test_ors_connectivity(base_url: str = None, api_key: str = None):
    """
    Test ORS connectivity by attempting to generate a simple isochrone.
    
    Args:
        base_url: ORS base URL. If None, uses config value.
        api_key: ORS API key. If None, uses config value.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    config = get_config()
    if base_url is None:
        base_url = config.ors_base_url
    if api_key is None:
        api_key = config.ors_api_key
    
    logger.info(f"Testing ORS connectivity at {base_url}...")
    
    try:
        # Create ORS client
        client = openrouteservice.Client(key=api_key, base_url=base_url)
        
        # Test with a simple isochrone request (Nairobi coordinates)
        # Small range (300 seconds = 5 minutes) for quick test
        logger.info("Attempting to generate test isochrone...")
        result = client.isochrones(
            locations=[[36.8219, -1.2921]],  # Nairobi coordinates
            profile='driving-car',
            range=[300],  # 5 minutes
            attributes=['total_pop']
        )
        
        if result and 'features' in result and len(result['features']) > 0:
            logger.info("✓ ORS connectivity test PASSED - Successfully generated isochrone")
            logger.info(f"  Test isochrone contains {len(result['features'])} feature(s)")
            return True, "ORS is working correctly"
        else:
            logger.warning("ORS returned empty result")
            return False, "ORS returned empty isochrone result"
            
    except openrouteservice.exceptions.ApiError as e:
        logger.error(f"✗ ORS API Error: {e}")
        return False, f"ORS API error: {e}"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"✗ Connection Error: Cannot reach ORS server at {base_url}")
        logger.error(f"  Error: {e}")
        return False, f"Cannot connect to ORS server: {e}"
    except requests.exceptions.Timeout as e:
        logger.error(f"✗ Timeout Error: ORS server did not respond in time")
        return False, f"ORS server timeout: {e}"
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}", exc_info=True)
        return False, f"Unexpected error: {e}"


def test_ors_comprehensive():
    """
    Run comprehensive ORS tests: health check and connectivity test.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    config = get_config()
    
    logger.info("=" * 60)
    logger.info("OpenRouteService (ORS) Comprehensive Test")
    logger.info("=" * 60)
    logger.info(f"ORS Base URL: {config.ors_base_url}")
    logger.info(f"ORS Health URL: {config.ors_health_url}")
    logger.info("")
    
    # Test 1: Health Check
    logger.info("Test 1: Health Check")
    logger.info("-" * 60)
    health_ok = check_ors_health(max_attempts=1)  # Just check once, don't wait
    
    if not health_ok:
        logger.warning("Health check failed - ORS may still be initializing")
        logger.info("You can run 'python check_ors.py' to wait for ORS to be ready")
    else:
        logger.info("✓ Health check passed")
    
    logger.info("")
    
    # Test 2: Connectivity Test
    logger.info("Test 2: Connectivity and Isochrone Generation")
    logger.info("-" * 60)
    connectivity_ok, message = test_ors_connectivity()
    
    logger.info("")
    logger.info("=" * 60)
    
    if health_ok and connectivity_ok:
        logger.info("✓ All ORS tests PASSED")
        return True
    elif connectivity_ok:
        logger.info("⚠ ORS is functional but health check failed (may be normal)")
        return True
    else:
        logger.error("✗ ORS tests FAILED")
        logger.error("")
        logger.error("Troubleshooting Steps:")
        logger.error("")
        logger.error("1. Verify GCP Instance Status:")
        logger.error(f"   - Check if instance is running: gcloud compute instances describe {DEFAULT_INSTANCE_NAME} --zone={DEFAULT_ZONE}")
        logger.error(f"   - Get current IP: python get_gcp_ors_ip.py")
        logger.error("")
        logger.error("2. Update Configuration:")
        logger.error("   - If IP changed, update config.yaml:")
        logger.error("     python get_gcp_ors_ip.py --update-config")
        logger.error("   - Or manually edit config.yaml with correct IP")
        logger.error("")
        logger.error("3. Check Instance Logs:")
        logger.error(f"   gcloud compute instances get-serial-port-output {DEFAULT_INSTANCE_NAME} --zone={DEFAULT_ZONE}")
        logger.error("")
        logger.error("4. Verify Firewall Rules:")
        logger.error("   - Check firewall rule exists: gcloud compute firewall-rules list --filter='name:allow-ors-8080'")
        logger.error("   - Ensure port 8080 is open and accessible")
        logger.error("")
        logger.error("5. Test Network Connectivity:")
        logger.error(f"   - Try accessing: http://{config.ors_base_url.split('//')[1].split(':')[0]}:8080/ors/v2/health")
        logger.error("   - Check if instance has external IP assigned")
        return False


if __name__ == "__main__":
    import sys
    
    # Check if user wants just health check or full test
    if len(sys.argv) > 1 and sys.argv[1] == "--health-only":
        try:
            check_ors_health()
        except KeyboardInterrupt:
            logger.info("Health check interrupted by user")
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            sys.exit(1)
    else:
        # Run comprehensive test
        success = test_ors_comprehensive()
        sys.exit(0 if success else 1)
