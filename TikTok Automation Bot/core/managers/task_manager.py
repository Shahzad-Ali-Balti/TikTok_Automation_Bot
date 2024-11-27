from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime

class TaskStatus(Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    STOPPED = "Stopped"
    COMPLETED = "Completed"
    FAILED = "Failed"

class NotificationStatus(Enum):
    PENDING = "Pending"
    SENDING = "Sending"
    SENT = "Sent"
    FAILED = "Failed"

class TaskManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.tasks: Dict[str, dict] = {}
        self.url_to_task: Dict[str, str] = {}

    def create_task(self, url: str, phone_number: str, check_interval: int) -> dict:
        task = {
            'url': url,
            'phone_number': phone_number,
            'check_interval': check_interval,
            'product_name': "Loading...",
            'monitoring_status': TaskStatus.PENDING.value,
            'product_status': "Unknown",
            'notification_status': NotificationStatus.PENDING.value,
            'created_at': datetime.utcnow(),
            'last_checked': None,
            'notification_sent': False
        }
        self.tasks[url] = task
        self.url_to_task[url] = url
        return task

    def get_task(self, url: str) -> Optional[dict]:
        return self.tasks.get(url)

    def update_task_status(self, url: str, status: TaskStatus, 
                          product_status: Optional[str] = None,
                          notification_status: Optional[NotificationStatus] = None):
        """Update task status"""
        task = self.get_task(url)
        if task:
            task['monitoring_status'] = status.value
            task['last_checked'] = datetime.utcnow()
            if product_status is not None:
                task['product_status'] = product_status
            if notification_status is not None:
                task['notification_status'] = notification_status.value

    def update_product_name(self, url: str, product_name: str):
        """Update product name for a task"""
        task = self.get_task(url)
        if task:
            task['product_name'] = product_name

    def mark_notification_sent(self, url: str):
        """Mark notification as sent for a task"""
        task = self.get_task(url)
        if task:
            task['notification_sent'] = True
            task['notification_status'] = NotificationStatus.SENT.value

    def remove_task(self, url: str):
        """Remove a task"""
        if url in self.url_to_task:
            del self.tasks[url]
            del self.url_to_task[url]

    def get_active_tasks(self) -> List[dict]:
        """Get all active tasks"""
        return [task for task in self.tasks.values() if task['monitoring_status'] == TaskStatus.ACTIVE.value]

    def get_all_tasks(self) -> List[dict]:
        """Get all tasks"""
        return list(self.tasks.values())

    def clear_all_tasks(self):
        """Clear all tasks from memory"""
        self.tasks.clear()
        self.url_to_task.clear()

    def is_url_monitored(self, url: str) -> bool:
        """Check if URL is already being monitored"""
        task = self.get_task(url)
        return task and task['monitoring_status'] == TaskStatus.ACTIVE.value