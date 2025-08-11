import time
from datetime import datetime, timezone
from rich.text import Text
from river_common import Status
from river_common.status import StatusBase

# Configuration for animations
ANIMATION_CYCLE_DURATION = 2.0  # seconds for full sweep
BRIGHT_DOT = '\u2022'  # •
DIM_DOT = '\u00B7'     # ·
STATIC_DOT = '.'       # Static dots for non-running states

# Visual configuration
ICONS = {
    'river': '>',  # Greater than symbol
    'job': '+',    # Plus sign
    'task': '-'    # Minus sign
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
    
    def __init__(self, item: StatusBase, indent_level: int = 0):
        self.item_type = item.type
        self.name = item.name
        self._status = item.status
        self.running_start: datetime | None = None
        self.running_end: datetime | None = None
        self.indent_level = indent_level
        self._animation_start_time = None  # Will be set on first render
        
        if self._status == Status.RUNNING:
            self.running_start = item.updated_at
        
        # Calculate dots needed based on available width
        self.dots_needed = self._calculate_dots_needed()
    
    def _calculate_dots_needed(self) -> int:
        """Calculate how many dots are needed based on available terminal width"""
        base_width = 90  # Assume 80 char terminal
        tree_indent_width = self.indent_level * 4  # Approximate tree indentation
        available_width = base_width - tree_indent_width
        
        name_part = f"{self.icon} {self.name}"
        
        # Use fixed width for status to ensure consistent alignment
        max_status_length = max(len(s.value) for s in Status)
        max_time_display_length = len("xxh xxm xxs")
        status_padded = f"{self._status.value:<{max_status_length}}"
        time_display_padded = f"{self._status.value:<{max_time_display_length}}"
        status_time_part = f"({status_padded}) {time_display_padded}"
        
        dots_needed = available_width - len(name_part) - len(status_time_part)
        
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
    def icon(self) -> str:
        """Get the icon based on item type"""
        return self.get_icon(self.item_type.value)
    
    @property
    def color(self) -> str:
        """Get the color based on current status"""
        return self.get_status_color(self._status)
    
    @property
    def time_display(self) -> str:
        """Get the running time string"""
        if self.running_start is None:
            return ""
        
        if self.running_end is None:
            # Still running - show time since start
            elapsed = datetime.now(timezone.utc) - self.running_start
        else:
            # Finished - show total runtime
            elapsed = self.running_end - self.running_start
        
        # Convert to seconds and format as xxh xxm xxs
        total_seconds = int(elapsed.total_seconds())
        
        # Use divmod for cleaner time calculation
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Build format string, skipping zero sections
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:  # Always show seconds if nothing else
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    
    @property
    def status_time_part(self) -> str:
        """Get formatted status and time part"""
        max_status_length = max(len(s.value) for s in Status)
        status_padded = f"{self._status.value:<{max_status_length}}"
        return f"{status_padded} {self.time_display}"
    
    def update_from_item(self, item: StatusBase):
        """Update from StatusBase object"""
        if item.status == Status.RUNNING:
            self.running_start = item.updated_at
        elif self._status == Status.RUNNING:
            self.running_end = item.updated_at

        self._status = item.status
    
    def _create_animated_dots(self) -> str:
        """Create animated dots that sweep from left to right."""
        if self._status != Status.RUNNING or self.dots_needed <= 1:
            return STATIC_DOT * self.dots_needed
        
        # Initialize animation start time on first render
        current_time = time.time()
        if self._animation_start_time is None:
            self._animation_start_time = current_time
        
        # Animation calculation
        elapsed = current_time - self._animation_start_time
        
        # Calculate animation cycle position (0 to 1)
        cycle_position = (elapsed % ANIMATION_CYCLE_DURATION) / ANIMATION_CYCLE_DURATION
        
        # Calculate the bright section
        bright_width = min(6, max(1, self.dots_needed // 3))
        # Allow bright section to completely sweep across (from 0 to beyond dots_needed)
        total_sweep_distance = self.dots_needed + bright_width
        bright_start = int(cycle_position * total_sweep_distance) - bright_width // 2
        
        # Build the animated dot string
        dots = []
        for i in range(self.dots_needed):
            if bright_start <= i < bright_start + bright_width:
                dots.append(BRIGHT_DOT)
            else:
                dots.append(DIM_DOT)
        
        return ''.join(dots)
    
    def __rich__(self) -> Text:
        """Rich protocol method - called automatically when Rich needs to render this object."""
        text = Text()
        
        # Add icon and name
        name_part = f"{self.icon} {self.name}"
        text.append(name_part)
        
        # Add animated or static dots
        dots = self._create_animated_dots()
        text.append(dots)
        
        # Add status and time with consistent padding
        max_status_length = max(len(s.value) for s in Status)
        status_padded = f"{self._status.value:<{max_status_length}}"
        status_part = f"({status_padded}) {self.time_display}"
        text.append(status_part)
        
        # Apply color to the entire text
        text.stylize(self.color)
        
        return text
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"AnimatedLabel({self.name}, {self._status.value})"