# MainWindow.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging
from core.managers.persistence_manager import PersistenceManager, MonitoringTask
from core.product_monitor import ProductMonitorWorker

class MainWindow(QMainWindow):
    def __init__(self, driver_path, table_widget):
        super().__init__()
        self.driver_path = driver_path
        self.table_widget = table_widget
        self.persistence_manager = PersistenceManager()
        self.active_monitors = {}  # Dictionary to store active monitoring workers
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.restore_active_monitors()

    def setup_ui(self):
        self.setWindowTitle("TikTok Shop Monitor")
        self.setMinimumSize(800, 600)

        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QLabel {
                font-size: 14px;
                color: #ECEFF4;
            }
            QLineEdit, QSpinBox, QTextEdit {
                background-color: #3B4252;
                border: 1px solid #4C566A;
                color: #ECEFF4;
                padding: 4px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:disabled {
                background-color: #4C566A;
                color: #D8DEE9;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Input section
        input_section = QVBoxLayout()
        
        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Product URL:")
        url_label.setMinimumWidth(120)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter TikTok Shop product URL")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        input_section.addLayout(url_layout)

        # WhatsApp input
        phone_layout = QHBoxLayout()
        phone_label = QLabel("WhatsApp Number:")
        phone_label.setMinimumWidth(120)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter number with country code (e.g., +1234567890)")
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(self.phone_input)
        input_section.addLayout(phone_layout)

        # Interval input
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Check Interval (seconds):")
        interval_label.setMinimumWidth(120)
        self.interval_input = QSpinBox()
        self.interval_input.setRange(5, 3600)
        self.interval_input.setValue(30)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_input)
        input_section.addLayout(interval_layout)

        layout.addLayout(input_section)

        # Button section
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Monitoring")
        self.stop_button = QPushButton("Stop All")
        self.clear_completed_button = QPushButton("Clear Completed")
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_completed_button)
        layout.addLayout(button_layout)

        # Add table widget
        layout.addWidget(self.table_widget)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #2E3440;
                color: #D8DEE9;
                border: 1px solid #4C566A;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_display)

        # Connect signals
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_all_monitoring)
        self.clear_completed_button.clicked.connect(self.clear_completed_tasks)

    def restore_active_monitors(self):
        """Restore previously active monitoring tasks"""
        try:
            active_tasks = self.persistence_manager.load_active_tasks()
            for task in active_tasks:
                if task.last_status == "Active":
                    self.start_monitoring_task(task)
                    self.log_display.append(f"Restored monitoring for: {task.url}")
        except Exception as e:
            self.logger.error(f"Error restoring monitors: {e}")
            self.log_display.append("Error restoring previous monitoring tasks")

    def start_monitoring_task(self, task=None):
        """Start a new monitoring task"""
        try:
            if task is None:
                # New monitoring task
                url = self.url_input.text().strip()
                phone_number = self.phone_input.text().strip()
                interval = self.interval_input.value()

                if not url or not phone_number:
                    self.log_display.append("Please provide both product URL and WhatsApp number.")
                    return None
            else:
                # Restored task
                url = task.url
                phone_number = task.phone_number
                interval = task.interval

            monitor = ProductMonitorWorker(
                driver_path=self.driver_path,
                table_widget=self.table_widget,
                persistence_manager=self.persistence_manager,
                url=url,
                phone_number=phone_number,
                check_interval=interval
            )
            
            monitor_id = monitor.task_id
            self.active_monitors[monitor_id] = monitor
            monitor.start()
            
            # Add new row to the table
            self.table_widget.add_or_update_row(
                url, monitor_id, "Loading", "Active", "Searching", "Pending"
            )
            
            self.log_display.append(f"Started monitoring: {url}")
            self.stop_button.setEnabled(True)
            return monitor_id
            
        except Exception as e:
            self.logger.error(f"Error starting monitor: {e}")
            self.log_display.append(f"Error starting monitoring: {str(e)}")
            return None

    def start_monitoring(self):
        """Start button handler"""
        monitor_id = self.start_monitoring_task()
        if monitor_id:
            self.start_button.setEnabled(True)  # Allow multiple monitoring tasks
            self.stop_button.setEnabled(True)

    def stop_all_monitoring(self):
        """Stop all monitoring tasks"""
        try:
            for monitor in list(self.active_monitors.values()):
                monitor.stop()
                monitor.wait()
            self.active_monitors.clear()
            self.log_display.append("Stopped all monitoring tasks")
            self.stop_button.setEnabled(False)
            self.start_button.setEnabled(True)
        except Exception as e:
            self.logger.error(f"Error stopping monitors: {e}")
            self.log_display.append("Error stopping monitoring tasks")

    def clear_completed_tasks(self):
        """Clear completed monitoring tasks from table"""
        self.table_widget.clear_completed()
        self.log_display.append("Cleared completed tasks")

    def closeEvent(self, event):
        """Handle application closure"""
        try:
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'Are you sure you want to exit? Active monitoring tasks will be stopped.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.stop_all_monitoring()
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            event.accept()