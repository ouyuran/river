from typing import Dict
from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text
from rich.segment import Segment
from animated_label import AnimatedLabel
from river_common import Status

class CompositeLabel:
    """A composite label that shows a job with its tasks integrated using custom rendering."""
    
    def __init__(self, job_item: dict, indent_level: int = 0):
        self.job_item = job_item
        self.indent_level = indent_level
        self.tasks: Dict[str, dict] = {}
        self.task_labels: Dict[str, AnimatedLabel] = {}  # Cache task labels for animation
        self.has_child_jobs = False  # Track if this job has child jobs
        
        # Create animated label for the job
        self.job_label = AnimatedLabel(
            item_type=job_item['type'],
            name=job_item['name'],
            status=Status(job_item['status']),
            indent_level=indent_level
        )
    
    def set_has_child_jobs(self, has_child_jobs: bool):
        """Set whether this job has child jobs (affects task rendering)"""
        self.has_child_jobs = has_child_jobs
    
    def add_task(self, task_item: dict):
        """Add a task to this job's display"""
        self.tasks[task_item['id']] = task_item
        # Create and cache the AnimatedLabel for this task
        self.task_labels[task_item['id']] = AnimatedLabel(
            item_type=task_item['type'],
            name=task_item['name'],
            status=Status(task_item['status']),
            indent_level=self.indent_level,
        )
    
    def update_task(self, task_item: dict):
        """Update an existing task"""
        self.tasks[task_item['id']] = task_item
        # Update the cached AnimatedLabel
        if task_item['id'] in self.task_labels:
            self.task_labels[task_item['id']].update_status(Status(task_item['status']))
    
    def update_job(self, job_item: dict):
        """Update the job information"""
        self.job_item = job_item
        self.job_label.update_status(Status(job_item['status']))
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Custom rich console rendering - controls exactly how content is rendered"""
        
        # First, yield the job text - this is the main connection point for tree
        job_text = self.job_label.get_text()
        yield job_text
        
        # Then yield each task text on separate lines
        for task_id, task_item in self.tasks.items():
            tree_prefix = "│ " if self.has_child_jobs else "  "
            # Use cached AnimatedLabel to preserve animation state
            if task_id in self.task_labels:
                yield self.task_labels[task_id].get_text(tree_prefix)
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"CompositeLabel(job={self.job_item['name']}, tasks={len(self.tasks)})"