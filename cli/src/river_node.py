from typing import Optional, Dict
from rich.tree import Tree
from animated_label import AnimatedLabel
from river_common import Status

TREE_GUIDE_STYLE = "dim white"

class RiverNode:
    """Represents a node in the River execution tree, combining data, display, and tree structure."""
    
    def __init__(self, item: dict, parent: Optional['RiverNode'] = None, tree_node: Optional[Tree] = None):
        self.item = item
        self.parent = parent
        self.children: Dict[str, 'RiverNode'] = {}
        
        # Calculate indent level based on parent chain
        indent_level = self._calculate_indent_level()
        
        # Create animated label for display
        self.animated_label = AnimatedLabel(
            item_type=item['type'],
            name=item['name'],
            status=Status(item['status']),
            indent_level=indent_level
        )
        
        # Use provided tree_node or create new one
        if tree_node is not None:
            # Root node - use provided tree
            self.tree_node = tree_node
            self.tree_node.label = self.animated_label
        else:
            # Child node - create new tree node
            self.tree_node = Tree(self.animated_label, guide_style=TREE_GUIDE_STYLE)
        
        if parent is not None:
            # Child node - attach to parent
            parent.tree_node.add(self.tree_node)
            # Add to parent's children
            parent.children[item['id']] = self
    
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
    
    def update_item(self, item: dict):
        """Update the item data"""
        self.item = item
        self.animated_label.status = Status(item['status'])
    
    @property
    def item_id(self) -> str:
        """Get the item ID"""
        return self.item['id']
    
    def __str__(self) -> str:
        return f"RiverNode({self.item['name']}, {self.item['status']})"