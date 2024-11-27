import json
import os
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class MonitoringTask:
    url: str
    phone_number: str
    interval: int
    last_status: str
    last_check: str  # ISO format datetime
    task_id: Optional[str] = None

class PersistenceManager:
    def __init__(self, file_path="monitoring_state.json"):
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)

    def save_active_tasks(self, tasks: List[MonitoringTask]):
        """Save active monitoring tasks to file"""
        try:
            data = [{
                'url': task.url,
                'phone_number': task.phone_number,
                'interval': task.interval,
                'last_status': task.last_status,
                'last_check': task.last_check,
                'task_id': task.task_id
            } for task in tasks]
            
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved {len(tasks)} active tasks")
            return True
        except Exception as e:
            self.logger.error(f"Error saving tasks: {e}")
            return False

    def load_active_tasks(self) -> List[MonitoringTask]:
        """Load active monitoring tasks from file"""
        try:
            if not os.path.exists(self.file_path):
                return []
                
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            
            tasks = [MonitoringTask(
                url=item['url'],
                phone_number=item['phone_number'],
                interval=item['interval'],
                last_status=item['last_status'],
                last_check=item['last_check'],
                task_id=item.get('task_id')
            ) for item in data]
            
            self.logger.info(f"Loaded {len(tasks)} tasks")
            return tasks
        except Exception as e:
            self.logger.error(f"Error loading tasks: {e}")
            return []

    def update_task_status(self, task_id: str, status: str):
        """Update status of a specific task"""
        try:
            tasks = self.load_active_tasks()
            updated = False
            for task in tasks:
                if task.task_id == task_id:
                    task.last_status = status
                    task.last_check = datetime.now().isoformat()
                    updated = True
                    break
            
            if updated:
                self.save_active_tasks(tasks)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating task status: {e}")
            return False

    def remove_task(self, task_id: str):
        """Remove a task from persistence"""
        try:
            tasks = self.load_active_tasks()
            tasks = [task for task in tasks if task.task_id != task_id]
            return self.save_active_tasks(tasks)
        except Exception as e:
            self.logger.error(f"Error removing task: {e}")
            return False

    def add_task(self, task: MonitoringTask):
        """Add a new task to persistence"""
        try:
            tasks = self.load_active_tasks()
            tasks.append(task)
            return self.save_active_tasks(tasks)
        except Exception as e:
            self.logger.error(f"Error adding task: {e}")
            return False