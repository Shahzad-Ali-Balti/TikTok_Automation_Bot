import sys
import logging
import os
from PyQt6.QtWidgets import QApplication
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from ui.main_window import MainWindow
from ui.components.table_widget import TableWidget

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def initialize_driver_path():
    """Get the ChromeDriver path."""
    driver_path = r"C:\Users\msbal\.wdm\drivers\chromedriver\win64\131.0.6778.86\chromedriver-win32"
    if not os.path.isdir(driver_path):
        logging.error(f"ChromeDriver directory not found at {driver_path}")
        raise FileNotFoundError(f"ChromeDriver directory not found at {driver_path}")
    return driver_path

def main():
    logger = setup_logging()
    app = QApplication(sys.argv)

    try:
        # Get driver path
        driver_path = initialize_driver_path()
        logger.info(f"ChromeDriver path: {driver_path}")

        # Initialize components
        table_widget = TableWidget()
        
        # Create main window with driver path
        main_window = MainWindow(driver_path=driver_path, table_widget=table_widget)
        main_window.show()
        
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()