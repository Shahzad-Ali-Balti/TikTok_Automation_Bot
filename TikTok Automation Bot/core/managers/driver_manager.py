import platform
import os
import logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def setup_logging():
    """Sets up logging for driver manager."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def clear_incompatible_driver(driver_path):
    """Clear the existing ChromeDriver if incompatible."""
    if os.path.exists(driver_path):
        logger.warning(f"Removing existing incompatible ChromeDriver at {driver_path}")
        os.remove(driver_path)  # Clear the cached driver file

def is_driver_compatible(driver_path):
    """Check if the existing ChromeDriver is compatible."""
    try:
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service)
        driver.quit()  # If it works, the driver is compatible
        logger.info("ChromeDriver is compatible.")
        return True
    except Exception as e:
        logger.error(f"Existing ChromeDriver is incompatible: {e}")
        return False

def detect_system_architecture():
    """Detects the system's architecture (64-bit or 32-bit)."""
    system_arch = platform.architecture()[0]
    logger.info(f"Detected system architecture: {system_arch}")
    return system_arch

def download_appropriate_driver():
    """Download the appropriate ChromeDriver based on the system architecture."""
    system_arch = detect_system_architecture()

    # ChromeDriverManager automatically downloads the right version based on the system architecture
    logger.info("Ensuring ChromeDriver compatibility...")
    driver_path = ChromeDriverManager().install()  # Automatically handles system architecture
    logger.info(f"Installed ChromeDriver at: {driver_path}")

    return driver_path

def detect_system_and_download_driver():
    """Detects the system and ensures a compatible ChromeDriver is installed."""
    logger.info("Checking system architecture...")

    try:
        # Download and install the appropriate driver
        driver_path = download_appropriate_driver()

        # Verify compatibility of the downloaded/installed driver
        if is_driver_compatible(driver_path):
            return driver_path
        else:
            logger.warning("ChromeDriver is incompatible. Redownloading...")
            clear_incompatible_driver(driver_path)
            return download_appropriate_driver()

    except Exception as e:
        logger.error(f"Failed to install or verify ChromeDriver: {e}")
        raise

# Test the driver manager
# if __name__ == "__main__":
#     try:
#         driver_path = detect_system_and_download_driver()
#         logger.info(f"Driver path: {driver_path}")
#     except Exception as e:
#         logger.error(f"Error in driver setup: {e}")
