"""Google Earth Engine authentication utility."""
import ee
from logger import get_logger

logger = get_logger(__name__)


def initialize_gee():
    """
    Initialize Google Earth Engine, authenticating if necessary.
    
    Raises:
        Exception: If authentication or initialization fails.
    """
    logger.info("Checking GEE authentication...")
    try:
        ee.Initialize()
        logger.info("GEE is already authenticated and initialized!")
    except Exception as e:
        logger.warning("GEE not authenticated. Authentication required.")
        logger.info("Please follow the instructions in the browser...")
        try:
            ee.Authenticate()
            ee.Initialize()
            logger.info("GEE authentication successful!")
        except Exception as auth_error:
            logger.error(f"GEE authentication failed: {auth_error}")
            raise


if __name__ == "__main__":
    try:
        initialize_gee()
    except Exception as e:
        logger.error(f"Failed to initialize GEE: {e}", exc_info=True)
        raise
