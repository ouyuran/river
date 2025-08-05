import time
from const import TREE_GUIDE_STYLE
from rich.text import Text
from river_common import Status

# Configuration for animations
ANIMATION_CYCLE_DURATION = 2.0  # seconds for full sweep
BRIGHT_DOT = '\u2022'  # •
DIM_DOT = '\u00B7'     # ·
STATIC_DOT = '.'       # Static dots for non-running states

INDENT_LENGTH = 4

# Visual configuration
ICONS = {
    'river': '◎',  # Greater than symbol
    'job': '+',    # Plus sign
    'task': '>'    # Minus sign
}

COLORS = {
    Status.PENDING: "bright_black",     # Pulumi-style neutral grey
    Status.RUNNING: "dark_cyan",        # Pulumi's signature blue
    Status.SUCCESS: "dark_cyan",        # Clean success green
    Status.FAILED: "red",               # Clear failure red
    Status.SKIPPED: "bright_black"      # Muted grey for skipped
}

class AnimatedLabel:
    """A Rich-compatible animated label that sweeps dots from left to right for running status."""
    
    def __init__(self, item_type: str, name: str, status: Status, indent_level: int = 0):
        self.item_type = item_type
        self.name = name
        self.status = status
        self.running_start: int | None = None
        self.running_end: int | None = None
        self.indent_level = indent_level
        self._animation_start_time = None  # Will be set on first render
        
        # Calculate dots needed based on available width
        self.dots_needed = self._calculate_dots_needed()
    
    def _calculate_dots_needed(self, tree_prefix: str = "") -> int:
        """Calculate how many dots are needed based on available terminal width"""
        # Use a fixed target width for all items to ensure alignment
        target_width = 80  # Fixed width for consistent alignment
        
        # Calculate the length of all non-dot elements
        prefix_length = len(tree_prefix)
        name_part = f"{self.icon} {self.name} "  # Include the space after name
        
        # Use fixed maximum length for status and time part to ensure consistent alignment
        max_status_length = max(len(s.value) for s in Status)
        max_time_length = 8  # Reserve space for "1h 30m 5s" format
        status_time_part = f" {' ' * max_status_length} {' ' * max_time_length}"  # Fixed width
        
        # Calculate dots needed to reach target width
        used_width = prefix_length + len(name_part) + len(status_time_part) + self.indent_level * INDENT_LENGTH
        dots_needed = target_width - used_width
        
        return max(1, dots_needed)  # Ensure at least 1 dot
    
    @staticmethod
    def get_status_color(status: Status) -> str:
        """Get color for status display"""
        return COLORS.get(status, "white")
    
    @staticmethod
    def get_icon(item_type: str) -> str:
        """Get symbol for item type"""
        return ICONS.get(item_type, '?')
    
    @property
    def time_display(self) -> str:
        """Get the running time string"""
        if self.running_start is None:
            return ""
        
        current_time = int(time.time() * 1000)
        
        if self.running_end is None:
            # Still running - show time since start
            elapsed_ms = current_time - self.running_start
        else:
            # Finished - show total runtime
            elapsed_ms = self.running_end - self.running_start
        
        # Convert to seconds and format as xxh xxm xxs
        total_seconds = int(elapsed_ms / 1000)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        # Build format string, skipping zero sections
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:  # Always show seconds if nothing else
            parts.append(f"{seconds}s")
        
        time_str = " ".join(parts)
        
        # Pad to consistent width (8 characters should handle most cases)
        return time_str
    
    @property
    def icon(self) -> str:
        """Get the icon based on item type"""
        return self.get_icon(self.item_type)
    
    @property
    def color(self) -> str:
        """Get the color based on current status"""
        return self.get_status_color(self.status)
    
    @property
    def status_time_part(self) -> str:
        """Get formatted status and time part"""
        max_status_length = max(len(s.value) for s in Status)
        status_padded = f"{self.status.value:<{max_status_length}}"
        return f"{status_padded} {self.time_display}"
    
    def update_status(self, status: Status):
        """Update the status"""
        current_time = int(time.time() * 1000)
        if status == Status.RUNNING:
            self.running_start = current_time
        elif self.status == Status.RUNNING:
            self.running_end = current_time
        self.status = status
    
    def _create_animated_dots(self, dots_count: int | None = None) -> str:
        """Create animated dots that sweep from left to right."""
        if dots_count is None:
            dots_count = self.dots_needed
            
        if self.status != Status.RUNNING or dots_count <= 1:
            return STATIC_DOT * dots_count
        
        # Initialize animation start time on first render
        current_time = time.time()
        if self._animation_start_time is None:
            self._animation_start_time = current_time
        
        # Animation calculation
        elapsed = current_time - self._animation_start_time
        
        # Calculate animation cycle position (0 to 1)
        cycle_position = (elapsed % ANIMATION_CYCLE_DURATION) / ANIMATION_CYCLE_DURATION
        
        # Calculate the bright section
        bright_width = min(6, max(1, dots_count // 3))
        # Allow bright section to completely sweep across (from 0 to beyond dots_count)
        total_sweep_distance = dots_count + bright_width
        bright_start = int(cycle_position * total_sweep_distance) - bright_width // 2
        
        # Build the animated dot string
        dots = []
        for i in range(dots_count):
            if bright_start <= i < bright_start + bright_width:
                dots.append(BRIGHT_DOT)
            else:
                dots.append(DIM_DOT)
        
        return ''.join(dots)
    
    def get_text(self, tree_prefix: str = "") -> Text:
        """Get the formatted text for this label."""
        text = Text()
        
        if tree_prefix:
            text.append(tree_prefix, style=TREE_GUIDE_STYLE)
        
        # Create the label content with color styling
        label_content = Text()
        
        # Add icon and name
        name_part = f"{self.icon} {self.name} "
        label_content.append(name_part)
        
        # Recalculate dots needed with tree prefix
        dots_needed = self._calculate_dots_needed(tree_prefix)
        
        # Add animated or static dots with updated count
        dots = self._create_animated_dots(dots_needed)
        label_content.append(dots)
        
        # Add status and time with consistent padding
        status_part = f" {self.status_time_part}"
        label_content.append(status_part)
        
        # Apply color only to the label content, not the tree prefix
        label_content.stylize(self.color)
        
        # Append the styled label content to the main text
        text.append(label_content)
        
        return text
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"AnimatedLabel({self.name}, {self.status.value})"