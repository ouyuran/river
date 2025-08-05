from typing import Optional, Dict
from rich.tree import Tree
from composite_label import CompositeLabel
from river_common import Status
from const import TREE_GUIDE_STYLE


class RiverNode:
    """Represents a node in the River execution tree, combining data, display, and tree structure."""
    
    def __init__(self, item: dict, parent: Optional['RiverNode'] = None, tree_node: Optional[Tree] = None):
        self.item = item
        self.parent = parent
        self.task_children: Dict[str, 'RiverNode'] = {}
        self.job_children: Dict[str, 'RiverNode'] = {}
        
        # Calculate indent level based on parent chain
        indent_level = self._calculate_indent_level()
        
        # Only jobs and river create labels and tree nodes
        # Tasks are managed entirely by their parent job's CompositeLabel
        if item['type'] in ['job', 'river']:
            # Jobs and river use composite labels that can contain tasks
            self.composite_label = CompositeLabel(item, indent_level)
            self.animated_label = None
            
            if tree_node is not None:
                # Root node - use provided tree
                self.tree_node = tree_node
                self.tree_node.label = self.composite_label
            else:
                # Child node - create new tree node
                self.tree_node = Tree(self.composite_label, guide_style=TREE_GUIDE_STYLE)
        else:
            # Tasks don't create their own labels or tree nodes
            # They are managed by their parent job's CompositeLabel
            self.composite_label = None
            self.animated_label = None
            self.tree_node = None
        
        if parent is not None:
            # Child node - attach to parent with proper ordering
            self._attach_to_parent(parent, item)
    
    def _calculate_indent_level(self) -> int:
        """Calculate indent level based on parent chain"""
        if self.parent is None:
            return 0
        
        # Count parent chain depth
        level = 1
        current_parent = self.parent
        while current_parent and current_parent.parent:
            current_parent = current_parent.parent
            level += 1
        
        return level
    
    def _attach_to_parent(self, parent: 'RiverNode', item: dict):
        """Attach this node to parent with proper ordering"""
        item_type = item['type']
        item_id = item['id']
        
        if item_type == 'task':
            # Tasks get added to parent's composite label, not as tree nodes
            parent.task_children[item_id] = self
            if parent.composite_label:
                parent.composite_label.add_task(item)
        elif item_type == 'job':
            # Jobs get added as tree nodes
            parent.job_children[item_id] = self
            # Update parent's composite label to show it has child jobs
            if parent.composite_label:
                parent.composite_label.set_has_child_jobs(True)
            # Only rebuild tree for job children
            self._rebuild_parent_tree(parent)
    
    def _rebuild_parent_tree(self, parent: 'RiverNode'):
        """Rebuild parent's tree structure with only job children"""
        if not parent.tree_node:
            return
            
        # Clear existing children from tree
        parent.tree_node.children.clear()
        
        # Add only job children (tasks are now part of composite labels)
        for job_node in parent.job_children.values():
            if job_node.tree_node:
                parent.tree_node.add(job_node.tree_node)
    
    def update_item(self, item: dict):
        """Update the item data"""
        self.item = item
        
        if self.composite_label:
            # Update composite label for jobs/river
            self.composite_label.update_job(item)
        elif item['type'] == 'task':
            # Tasks don't have their own labels, update in parent's composite label
            if self.parent and self.parent.composite_label:
                self.parent.composite_label.update_task(item)
    
    @property
    def item_id(self) -> str:
        """Get the item ID"""
        return self.item['id']
    
    @property
    def all_children(self) -> Dict[str, 'RiverNode']:
        """Get all children (tasks and jobs combined)"""
        combined = {}
        combined.update(self.task_children)
        combined.update(self.job_children)
        return combined
    
    def __str__(self) -> str:
        return f"RiverNode({self.item['name']}, {self.item['status']})"