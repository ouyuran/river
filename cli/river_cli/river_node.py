from typing import Optional, Dict
from rich.tree import Tree
from .animated_label import AnimatedLabel
from river_common.status import StatusBase

TREE_GUIDE_STYLE = "dim white"

class RiverNode:
    """Represents a node in the River execution tree, combining data, display, and tree structure."""
    
    def __init__(self, item: StatusBase, parent: Optional['RiverNode'] = None):
        self.item = item
        self.parent = parent
        self.children: Dict[str, 'RiverNode'] = {}
        
        # Calculate indent level based on parent chain
        indent_level = self._calculate_indent_level()
        
        # Create animated label for display
        self.animated_label = AnimatedLabel(item, indent_level)
        self.tree_node = Tree(self.animated_label, guide_style=TREE_GUIDE_STYLE)
        
        if parent is not None:
            # Child node - attach to parent
            parent.tree_node.add(self.tree_node)
            # Add to parent's children
            parent.children[item.id] = self
    
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
    
    def update_item(self, item: StatusBase):
        """Update the item data"""
        self.item = item
        self.animated_label.update_from_item(item)
    
    @property
    def item_id(self) -> str:
        """Get the item ID"""
        return self.item.id
    
    def __str__(self) -> str:
        return f"RiverNode({self.item.name}, {self.item.status})"