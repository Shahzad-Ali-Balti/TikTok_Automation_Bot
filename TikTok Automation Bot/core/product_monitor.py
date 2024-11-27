from selenium.webdriver.common.by import By
import logging
import time
from twilio.rest import Client
from PyQt6.QtCore import QThread
from urllib.parse import unquote
import json
from datetime import datetime
from core.managers.persistence_manager import MonitoringTask
from core.managers.web_monitor import WebMonitor

class ProductMonitorWorker(QThread):
    def __init__(self, driver_path, table_widget, persistence_manager, url, phone_number, check_interval=30):
        super().__init__()
        # Initialize basic parameters
        self.driver_path = driver_path
        self.table_widget = table_widget
        self.persistence_manager = persistence_manager
        self.url = url
        self.phone_number = phone_number
        self.check_interval = check_interval
        self.keep_running = True
        self.task_id = str(id(self))
        self.web_monitor = None
        self.table_widget.stop_monitoring.connect(self.stop)
        # Twilio credentials
        self.twilio_account_sid = "AC8f4ee6c4b49b8dcdceedb4a4190dfcdd"
        self.twilio_auth_token = "c04bd4c51fe1ee007beb3927fb4c4d75"
        self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        self.twilio_whatsapp_number = "whatsapp:+14155238886"

        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize task state
        self.save_task_state("Active")
        self.table_widget.update_product_name(self.task_id, "Loading")
        self.table_widget.update_monitoring_status(self.task_id, "Active")
        self.table_widget.update_product_status(self.task_id, "Searching")
        self.table_widget.update_notification_status(self.task_id, "Pending")

    def save_task_state(self, status):
        """Save current task state to persistence"""
        task = MonitoringTask(
            url=self.url,
            phone_number=self.phone_number,
            interval=self.check_interval,
            last_status=status,
            last_check=datetime.now().isoformat(),
            task_id=self.task_id
        )
        self.persistence_manager.add_task(task)

    def initialize_browser_and_load_url(self):
        """Function 1: Initialize browser and load URL"""
        try:
            self.web_monitor = WebMonitor(self.driver_path)
            success = self.web_monitor.open_url(self.url)
            if not success:
                raise Exception("Failed to initialize browser or load URL")
            self.logger.info("Browser initialized and URL loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False

    def reload_page(self):
        """Function 2: Reload the current page"""
        try:
            if self.web_monitor:
                success = self.web_monitor.reload_page()
                if success:
                    self.logger.info("Page reloaded successfully")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to reload page: {e}")
            return False

    def close_browser(self):
        """Function 3: Close the browser"""
        try:
            if self.web_monitor:
                self.web_monitor.cleanup()
                self.web_monitor = None
                self.logger.info("Browser closed successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to close browser: {e}")
            return False

    def send_notification(self, product_title, product_url, availability_strings):
        """Function 4: Send notification through Twilio"""
        try:
            # Prepare message content
            formatted_availability = '\n'.join(availability_strings)
            message_body = (
                f"🔔 Product Alert!\n\n"
                f"Product Name:\n{product_title}\n\n"
                f"Status: Available Now\n\n"
                f"Link: {product_url}\n\n"
                f"Click the link to buy the product."
            )
            
            # Format phone number
            clean_number = ''.join(filter(str.isdigit, self.phone_number))
            formatted_number = f"whatsapp:+{clean_number}"

            # Send message
            self.logger.info("Sending WhatsApp message via Twilio...")
            message = self.twilio_client.messages.create(
                from_=self.twilio_whatsapp_number,
                body=message_body,
                to=formatted_number
            )
            
            self.logger.info(f"Message sent successfully. SID: {message.sid}")
            self.table_widget.update_notification_status(self.task_id, "Sent")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send WhatsApp message: {e}")
            self.table_widget.update_notification_status(self.task_id, "Failed")
            return False

    def get_render_data(self):
        """Function 5: Get product availability from page"""
        try:
            # Find and extract RENDER_DATA script
            script = self.web_monitor.find_element_safe(By.XPATH, "//*[@id='RENDER_DATA']")
            if not script:
                self.logger.error("Render data script not found")
                return None

            # Parse script content
            raw_data = script.get_attribute('innerHTML')
            decoded_data = unquote(raw_data)
            json_data = json.loads(decoded_data)
            
            # Get page info
            product_title = self.web_monitor.driver.title
            product_url = self.web_monitor.get_current_url()

            # Extract product info
            product_info = json_data['2']['initialData']['productInfo']
            skus = product_info.get('skus', [])
            if not isinstance(skus, list):
                skus = [skus]

            # Check availability
            availability_strings = []
            availability = False

            for sku in skus:
                prop_values = '-'.join(prop['prop_value'] for prop in sku.get('sku_sale_props', []))
                stock_status = "Available" if sku.get('stock', 0) > 0 else "Unavailable"
                availability_strings.append(f"{prop_values} : {stock_status}")
                if sku.get('stock', 0) > 0:
                    availability = True

            return {
                "status": "success",
                "availability": availability,
                "product_title": product_title,
                "product_url": product_url,
                "availability_strings": availability_strings
            }

        except Exception as e:
            self.logger.error(f"Failed to get render data: {e}")
            return None

    def run(self):
        """Main monitoring loop"""
        try:
            self.logger.info('1st Main Loop : Browser Initialization')
            # Function 1: Initialize browser and load URL
            if not self.initialize_browser_and_load_url():
                raise Exception("Failed to initialize browser")
            self.logger.info('1st Main Loop : Browser Initialized')

            # Start monitoring loop
            while self.keep_running:
                self.logger.info('1st Main Loop : 1st loop Getting Render Data')
                # Function 5: Get render data
                result = self.get_render_data()

                
                if result and result['status'] == 'success':
                    self.table_widget.update_product_name(self.task_id, result['product_title'])
                    
                    if result['availability']:
                        self.logger.info('1st Main Loop : Product Available')

                        # Product is available
                        self.table_widget.update_product_status(self.task_id, "Available")
                        self.table_widget.update_monitoring_status(self.task_id, "Active")
                        
                        # Function 4: Send notification
                        if self.send_notification(
                            result['product_title'],
                            result['product_url'],
                            result['availability_strings']
                        ):
                            self.persistence_manager.remove_task(self.task_id)
                            self.logger.info('1st Main Loop : Notification Sent')
                            # Function 3: Close browser
                            self.close_browser()
                            self.logger.info('1st Main Loop : Browser Closed')
                            self.keep_running = False
                            self.logger.info('1st Main Loop : Loop ended')

                        self.table_widget.update_monitoring_status(self.task_id, "Completed")

                        break
                    else:
                        # Product unavailable
                        self.table_widget.update_product_status(self.task_id, "Unavailable")
                        self.logger.info('1st Main Loop : Product Unavailable')

                        # Function 2: Reload page
                        time.sleep(30)

                        self.reload_page()
                        self.logger.info('1st Main Loop : Page Reloaded')

                # Wait for next check
                time.sleep(self.check_interval)
                self.logger.info(f'1st Main Loop : Waited for Interval {self.check_interval}')


        except Exception as e:
            self.logger.error(f"Error in monitoring: {e}")
            self.table_widget.update_monitoring_status(self.task_id, "Error")
            self.table_widget.update_product_status(self.task_id, "Error")
            self.table_widget.update_notification_status(self.task_id, "Failed")
            self.stop()
        finally:
            if self.web_monitor:
                self.close_browser()
            # if self.keep_running:
            #     self.stop(emit_signals=True)

    def stop(self, task_id):
        """Handle manual stopping"""
        self.table_widget.update_product_name(self.task_id, 'Unknown')
        # self.table_widget.update_product_status(self.task_id, "Unknown")
        # self.table_widget.update_monitoring_status(task_id, "Stopped")
        # self.table_widget.update_notification_status(task_id, "Cancelled")
        self.keep_running = False
        self.persistence_manager.remove_task(task_id)
        self.close_browser()