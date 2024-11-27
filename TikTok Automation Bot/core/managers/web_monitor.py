from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
import time

class WebMonitor:
    def __init__(self, driver_path):
        self.logger = logging.getLogger(__name__)
        self.driver_path = driver_path
        self.driver = None
        self.url = None
        self.initialize_driver()

    def initialize_driver(self):
        """Initialize a new WebDriver instance"""
        try:
            chromedriver_path = os.path.join(self.driver_path, 'chromedriver.exe')
            chrome_service = Service(chromedriver_path)
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-extensions")
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Additional options for better stability
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-infobars")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            self.driver = webdriver.Chrome(service=chrome_service, options=options)
            self.driver.set_window_size(1920, 1080)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("WebDriver initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize driver: {e}")
            return False

    def open_url(self, url):
        """Opens the specified URL in the browser."""
        try:
            if not self.driver:
                if not self.initialize_driver():
                    return False

            self.url = url
            self.logger.info(f'Opening URL: {url}')
            self.driver.get(url)
            self.wait_for_page_load()
            time.sleep(2)
            self._log_page_info()
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening URL: {e}")
            return False

    def wait_for_page_load(self, timeout=30):
        """Waits for the page to load completely."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            self.logger.info("Page fully loaded")
            return True
        except Exception as e:
            self.logger.error(f"Page load timeout: {e}")
            return False

    def reload_page(self):
        """Reloads the current page."""
        try:
            if not self.driver:
                self.logger.error("Driver not initialized")
                return False

            self.logger.info("Reloading page...")
            current_url = self.get_current_url()
            self.driver.refresh()
            reload_success = self.wait_for_page_load()
            time.sleep(2)
            
            if reload_success and current_url == self.get_current_url():
                self.logger.info("Page successfully reloaded")
                return True
            return False
                
        except Exception as e:
            self.logger.error(f"Error during page reload: {e}")
            return False

    def find_element_safe(self, by, value, timeout=10):
        """Safely finds an element by its locator."""
        try:
            if not self.driver:
                return None
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            self.logger.error(f"Element not found: {str(e)}")
            return None

    def _log_page_info(self):
        """Logs the current page title and URL."""
        try:
            self.logger.info(f"Page Title: {self.driver.title}")
            self.logger.info(f"Current URL: {self.driver.current_url}")
        except Exception as e:
            self.logger.error(f"Error logging page info: {e}")

    def get_current_url(self):
        """Returns the current URL."""
        try:
            if self.driver:
                return self.driver.current_url
            return None
        except Exception as e:
            self.logger.error(f"Error getting current URL: {e}")
            return None

    def cleanup(self):
        """Closes the browser and cleans up resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")