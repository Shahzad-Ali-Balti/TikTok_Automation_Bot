from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import logging

class TableWidget(QTableWidget):
    status_updated = pyqtSignal(str, str, str)
    stop_monitoring = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setup_table()
        self.row_task_map = {}
        self.task_row_map = {}
        self.logger = logging.getLogger(__name__)

    def setup_table(self):
        """Initialize the table structure"""
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "URL",
            "Product Name",
            "Monitoring Status",
            "Product Status",
            "Notification Status",
            "Action"
        ])
        
        # Set column stretching
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # URL
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Product Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Monitoring Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Product Status
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Notification Status
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)    # Action Button
        
        # Set fixed widths for status columns
        self.setColumnWidth(2, 120)  # Monitoring Status
        self.setColumnWidth(3, 100)  # Product Status
        self.setColumnWidth(4, 120)  # Notification Status
        self.setColumnWidth(5, 80)   # Action Button

        # Apply styling
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2E3440;
                color: #D8DEE9;
                border: 1px solid #4C566A;
                gridline-color: #4C566A;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #5E81AC;
            }
            QHeaderView::section {
                background-color: #3B4252;
                color: #ECEFF4;
                padding: 5px;
                border: 1px solid #4C566A;
                font-weight: bold;
            }
        """)

    def create_styled_item(self, text, status_type=None):
        """Create a styled table item based on status"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set colors based on status
        if status_type == "monitoring":
            if text == "Active":
                item.setBackground(QColor("#A3BE8C"))  # Green
                item.setForeground(QColor("#000000"))  # Black text
            elif text == "Completed":
                item.setBackground(QColor("#88C0D0"))  # Blue
                item.setForeground(QColor("#000000"))
            elif text == "Stopped":
                item.setBackground(QColor("#BF616A"))  # Red
                item.setForeground(QColor("#FFFFFF"))  # White text
            elif text == "Error":
                item.setBackground(QColor("#B48EAD"))  # Purple
                item.setForeground(QColor("#FFFFFF"))
                
        elif status_type == "product":
            if text == "Available":
                item.setBackground(QColor("#A3BE8C"))
                item.setForeground(QColor("#000000"))
            elif text == "Unavailable":
                item.setBackground(QColor("#BF616A"))
                item.setForeground(QColor("#FFFFFF"))
            elif text == "Unknown":
                item.setBackground(QColor("#BF616A"))
                item.setForeground(QColor("#FFFFFF"))
            elif text == "Searching":
                item.setBackground(QColor("#EBCB8B"))  # Yellow
                item.setForeground(QColor("#000000"))
                
        elif status_type == "notification":
            if text == "Sent":
                item.setBackground(QColor("#A3BE8C"))
                item.setForeground(QColor("#000000"))
            elif text == "Pending":
                item.setBackground(QColor("#EBCB8B"))
                item.setForeground(QColor("#000000"))
            elif text == "Cancelled":
                item.setBackground(QColor("#BF616A"))
                item.setForeground(QColor("#FFFFFF"))
                
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make item read-only
        return item

    def create_stop_button(self, row, task_id):
        """Create a styled stop button"""
        button = QPushButton("Stop")
        button.setStyleSheet("""
            QPushButton {
                background-color: #BF616A;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                min-width: 60px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d08770;
            }
            QPushButton:disabled {
                background-color: #4C566A;
            }
        """)
        button.clicked.connect(lambda: self.handle_stop_button(task_id))
        return button

    def add_or_update_row(self, url, task_id, product_name, monitoring_status, product_status, notification_status):
        """Add a new row at the top or update existing row in the table"""
        try:
            if task_id in self.task_row_map:
                # Update existing row
                row = self.task_row_map[task_id]
            else:
                # Add new row at the top (position 0)
                self.insertRow(0)
                row = 0
                
                # Update row mappings
                self.row_task_map[row] = task_id
                self.task_row_map[task_id] = row
                
                # Create stop button for new row
                self.setCellWidget(row, 5, self.create_stop_button(row, task_id))

            # Update cells with styling
            url_item = QTableWidgetItem(url)
            url_item.setFlags(url_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 0, url_item)
            
            name_item = QTableWidgetItem(product_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 1, name_item)
            
            self.setItem(row, 2, self.create_styled_item(monitoring_status, "monitoring"))
            self.setItem(row, 3, self.create_styled_item(product_status, "product"))
            self.setItem(row, 4, self.create_styled_item(notification_status, "notification"))

            # Disable stop button if monitoring is completed or stopped
            stop_button = self.cellWidget(row, 5)
            if stop_button and monitoring_status in ["Completed", "Stopped", "Error"]:
                stop_button.setEnabled(False)
            else:
                stop_button.setEnabled(True)

        except Exception as e:
            self.logger.error(f"Error adding/updating row: {e}")

    def update_product_name(self, task_id, value):
        """Update the product name column"""
        if task_id in self.task_row_map:
            row = self.task_row_map[task_id]
            name_item = QTableWidgetItem(value)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, 1, name_item)
            self.status_updated.emit(task_id, "product_name", value)

    def update_monitoring_status(self, task_id, value):
        """Update the monitoring status column"""
        if task_id in self.task_row_map:
            row = self.task_row_map[task_id]
            self.setItem(row, 2, self.create_styled_item(value, "monitoring"))
            self.status_updated.emit(task_id, "monitoring_status", value)
            # Disable stop button if status is Completed or Stopped
            # stop_button = self.cellWidget(row, 5)
            # if stop_button and value in ["Completed", "Stopped"]:
            #     stop_button.setEnabled(False)
            # else:
            #     stop_button.setEnabled(True)

    def update_product_status(self, task_id, value):
        """Update the product status column"""
        if task_id in self.task_row_map:
            row = self.task_row_map[task_id]
            self.setItem(row, 3, self.create_styled_item(value, "product"))
            self.status_updated.emit(task_id, "product_status", value)

    def update_notification_status(self, task_id, value):
        """Update the notification status column"""
        if task_id in self.task_row_map:
            row = self.task_row_map[task_id]
            self.setItem(row, 4, self.create_styled_item(value, "notification"))
            self.status_updated.emit(task_id, "notification_status", value)

    def handle_stop_button(self, task_id):
        """Handle stop button click"""
        try:
            if task_id:
                self.stop_monitoring.emit(task_id)
                row = self.task_row_map[task_id]
                self.setItem(row, 2, self.create_styled_item("Stopped", "monitoring"))
                self.setItem(row, 3, self.create_styled_item('Unknown', "product"))
                self.setItem(row, 4, self.create_styled_item("Cancelled", "notification"))
                # Disable the stop button
                stop_button = self.cellWidget(row, 5)
                if stop_button:
                    stop_button.setEnabled(False)
        except Exception as e:
            self.logger.error(f"Error handling stop button: {e}")

    def remove_row(self, task_id):
        """Remove a row from the table"""
        try:
            if task_id in self.task_row_map:
                row = self.task_row_map[task_id]
                self.removeRow(row)
                
                # Update mappings after removal
                del self.row_task_map[row]
                del self.task_row_map[task_id]
        except Exception as e:
            self.logger.error(f"Error removing row: {e}")

    def clear_completed(self):
        """Clear all completed monitoring tasks"""
        try:
            rows_to_remove = []
            for row in range(self.rowCount()):
                if self.item(row, 2).text() in ["Completed"]:
                    task_id = self.row_task_map.get(row)
                    if task_id:
                        rows_to_remove.append(task_id)
                        
            for task_id in rows_to_remove:
                self.remove_row(task_id)
        except Exception as e:
            self.logger.error(f"Error clearing completed tasks: {e}")