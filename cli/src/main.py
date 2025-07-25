import subprocess
import json
import threading
import queue
import time
from rich.live import Live
from rich.tree import Tree
from rich.console import Console
from river_common import Status

# Configuration for visual elements
ICONS = {
    'river': '>',  # Greater than symbol
    'job': '+',    # Plus sign
    'task': '-'    # Minus sign
}

COLORS = {
    Status.PENDING: "bright_black",     # Pulumi-style neutral grey
    Status.RUNNING: "dark_cyan",             # Pulumi's signature blue
    Status.SUCCESS: "dark_cyan",            # Clean success green
    Status.FAILED: "red",               # Clear failure red
    Status.SKIPPED: "bright_black"      # Muted grey for skipped
}

TREE_GUIDE_STYLE = "dim white"  # Tree connection lines color

class StreamingTreeRenderer:
    def __init__(self):
        self.console = Console()
        self.tree = Tree(f"{ICONS['river']} River Status", guide_style=TREE_GUIDE_STYLE)
        self.nodes = {}
        self.node_data = {}  # Store original item data for each node
        self.data_queue = queue.Queue()
        self.running = True
        self.start_time = time.time()
        
    def get_status_color(self, status: Status) -> str:
        """Get color for status display"""
        return COLORS.get(status, "white")
    
    def get_icon(self, item_type: str) -> str:
        """Get symbol for item type"""
        return ICONS.get(item_type, '?')
    
    def create_animated_dots(self, dots_needed, is_running=False):
        """Create animated dots that sweep from left to right when running"""
        if not is_running or dots_needed <= 1:
            return '.' * dots_needed
        
        # Animation parameters
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Animation cycle: 2 seconds for a full sweep
        cycle_duration = 2.0
        cycle_position = (elapsed % cycle_duration) / cycle_duration
        
        # Calculate the position of the "bright" section
        bright_width = min(6, dots_needed // 3)  # Width of bright section
        if bright_width < 1:
            bright_width = 1
            
        # Position of the bright section (0 to dots_needed)
        bright_start = int(cycle_position * (dots_needed + bright_width)) - bright_width
        
        # Build the animated dot string
        dots = []
        for i in range(dots_needed):
            if bright_start <= i < bright_start + bright_width:
                dots.append('\u2022')  # Bright dot •
            else:
                dots.append('\u00B7')  # Dim dot ·
        
        return ''.join(dots)
    
    def create_label(self, item, status, color, icon, indent_level=0):
        """Create label with right-aligned status and time, accounting for tree indentation"""
        name_part = f"{icon} {item['name']}"
        status_part = f"({status.value})"
        time_part = "10s"  # Placeholder for now
        
        is_running = status == Status.RUNNING
        
        # Calculate available width considering tree indentation
        # Tree indentation: root=0, job=4 chars ("├── "), task=8 chars ("│   ├── ")
        base_width = 80  # Assume 80 char terminal
        tree_indent_width = indent_level * 4  # Approximate tree indentation
        available_width = base_width - tree_indent_width
        
        right_part = f"{status_part} {time_part}"
        left_width = available_width - len(right_part)
        
        if len(name_part) > left_width:
            name_part = name_part[:left_width-3] + "..."
        
        # Use animated dots for running status
        dots_needed = left_width - len(name_part)
        if dots_needed > 1:
            dots = self.create_animated_dots(dots_needed, is_running)
            label = f"{name_part}{dots}{right_part}"
        else:
            label = f"{name_part} {right_part}"
        
        return f"[{color}]{label}[/{color}]"
    
    def update_or_create_node(self, item):
        """Update existing node or create new one"""
        item_id = item['id']
        status = Status(item['status'])
        color = self.get_status_color(status)
        icon = self.get_icon(item['type'])
        
        # Store item data for spinner refresh
        self.node_data[item_id] = item
        
        if item['type'] == 'river':
            # River node - no indentation
            label = self.create_label(item, status, color, icon, indent_level=0)
            self.tree.label = f"{ICONS['river']} {label}"
            self.nodes[item_id] = self.tree
        else:
            # Determine indent level based on type
            indent_level = 1 if item['type'] == 'job' else 2  # job=1, task=2
            label = self.create_label(item, status, color, icon, indent_level)
            
            if item_id in self.nodes:
                # Update existing node
                self.nodes[item_id].label = label
            else:
                # Create new node with same guide style
                node = Tree(label, guide_style=TREE_GUIDE_STYLE)
                self.nodes[item_id] = node
                
                # Add to parent if parent exists
                parent_id = item['parent_id']
                if parent_id in self.nodes:
                    self.nodes[parent_id].add(node)
    
    def refresh_running_nodes(self):
        """Refresh spinner animations for all running nodes"""
        for node_id, item_data in self.node_data.items():
            if item_data['status'] == 'running':
                status = Status.RUNNING
                color = self.get_status_color(status)
                icon = self.get_icon(item_data['type'])
                
                if item_data['type'] == 'river':
                    # River node - no indentation
                    label = self.create_label(item_data, status, color, icon, indent_level=0)
                    self.tree.label = f"{ICONS['river']} {label}"
                else:
                    # Determine indent level based on type
                    indent_level = 1 if item_data['type'] == 'job' else 2  # job=1, task=2
                    label = self.create_label(item_data, status, color, icon, indent_level)
                    if node_id in self.nodes:
                        self.nodes[node_id].label = label
    
    def process_stream_data(self, proc):
        """Process streaming data from subprocess"""
        try:
            for line in iter(proc.stdout.readline, ''):
                if not line or not self.running:
                    break
                    
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        self.data_queue.put(item)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.data_queue.put({'error': str(e)})
        finally:
            proc.stdout.close()
    
    def start_data_process(self):
        """Start the data.py subprocess"""
        try:
            proc = subprocess.Popen(
                ["uv", "run", "python", "src/data.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Start thread to read from subprocess
            thread = threading.Thread(target=self.process_stream_data, args=(proc,))
            thread.daemon = True
            thread.start()
            
            return proc, thread
        except Exception as e:
            self.data_queue.put({'error': f'Failed to start data process: {str(e)}'})
            return None, None
    
    def run(self):
        """Main rendering loop"""
        proc, thread = self.start_data_process()
        
        if not proc:
            self.console.print("❌ Failed to start data process")
            return
            
        with Live(self.tree, refresh_per_second=10, console=self.console) as live:
            try:
                while self.running:
                    try:
                        # Get data with timeout to allow for spinner updates
                        item = self.data_queue.get(timeout=0.1)
                        
                        if 'error' in item:
                            self.tree.label = f"❌ Error: {item['error']}"
                        else:
                            self.update_or_create_node(item)
                        
                        self.data_queue.task_done()
                        
                    except queue.Empty:
                        # No new data, but refresh spinners for running nodes
                        self.refresh_running_nodes()
                        
                        # Check if process is still running
                        if proc.poll() is not None:
                            # Process finished, wait a bit for remaining data
                            try:
                                while True:
                                    item = self.data_queue.get_nowait()
                                    if 'error' in item:
                                        self.tree.label = f"❌ Error: {item['error']}"
                                    else:
                                        self.update_or_create_node(item)
                                    self.data_queue.task_done()
                            except queue.Empty:
                                pass
                            break
                        continue
                    
                    # Always update the display
                    live.update(self.tree)
                        
            except KeyboardInterrupt:
                self.running = False
                if proc:
                    proc.terminate()
                self.console.print("\n👋 Goodbye!")

def main():
    """Main entry point"""
    renderer = StreamingTreeRenderer()
    renderer.run()

if __name__ == "__main__":
    main()