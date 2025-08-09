import subprocess
import json
import threading
import queue
from typing import Dict, Optional
from rich.live import Live
from rich.tree import Tree
from rich.console import Console
from river_common import Status
from animated_label import AnimatedLabel
from river_node import RiverNode

TARGET_FPS = 60  # Target frames per second for animations

class StreamingTreeRenderer:
    def __init__(self):
        self.console = Console()
        self.nodes: Dict[str, RiverNode] = {}
        self.data_queue = queue.Queue()
        self.running = True
    
    def update_or_create_node(self, item):
        """Update existing node or create new one"""
        item_id = item['id']
        
        if item_id in self.nodes:
            # Update existing RiverNode
            existing_node = self.nodes[item_id]
            existing_node.update_item(item)
            return existing_node
        
        # Create new RiverNode
        parent_id = item.get('parent_id')
        parent_node = self.nodes.get(parent_id) if parent_id else None
        
        river_node = RiverNode(item=item, parent=parent_node)
        self.nodes[item_id] = river_node
        
        return river_node
    
    def process_item(self, item):
        """Process a single item from the queue"""
        river_node = self.update_or_create_node(item)
        self.data_queue.task_done()
        return river_node
    
    def wait_and_process_first_item(self):
        """Wait for and process the first item from queue"""
        item = self.data_queue.get(timeout=0.1)
        return self.process_item(item)
    
    def process_rest_items(self):
        """Process all remaining items in queue"""
        try:
            while True:
                item = self.data_queue.get_nowait()
                self.process_item(item)
        except queue.Empty:
            pass
    
    def is_process_finished(self, proc):
        """Check if the subprocess has finished"""
        return proc.poll() is not None
    
    def render_error_summary(self):
        """Render summary of all failed items with error details"""
        failed_nodes = [node for node in self.nodes.values() if node.item.get('status') == 'failed']
        
        if not failed_nodes:
            return
            
        self.console.print("\n" + "="*60)
        self.console.print("[bold red]❌ Error Summary[/bold red]")
        self.console.print("="*60)
        
        for node in failed_nodes:
            item = node.item
            self.console.print(f"[bold red]• {item['name']}[/bold red] (ID: {item['id']})")
            
            error_msg = item.get('error')
            error_type = item.get('error_type')
            
            if error_msg:
                self.console.print(f"  [red]Error:[/red] {error_msg}")
                if error_type:
                    self.console.print(f"  [red]Type:[/red] {error_type}")
            else:
                self.console.print(f"  [red]Error:[/red] Failed without details")
            
            self.console.print()  # Empty line between errors
    
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
    
    def _get_root_node(self, proc) -> Optional[RiverNode]:
        root_node = None
        while not root_node and self.running:
            try:
                root_node = self.wait_and_process_first_item()
            except queue.Empty:
                if self.is_process_finished(proc):
                    self.console.print("❌ Process finished without data")
                    return None
                continue
        return root_node

    def run(self):
        """Main rendering loop"""
        proc, thread = self.start_data_process()
        
        if not proc:
            self.console.print("❌ Failed to start data process")
            return
        
        # Wait for first item to get the root tree node
        root_node = self._get_root_node(proc)
        if not root_node:
            return
            
        with Live(root_node.tree_node, refresh_per_second=TARGET_FPS, console=self.console) as live:
            try:
                while self.running:
                    try:
                        self.wait_and_process_first_item()
                        self.process_rest_items()
                    except queue.Empty:
                        if self.is_process_finished(proc):
                            self.process_rest_items()
                            break
                        
            except KeyboardInterrupt:
                self.running = False
                if proc:
                    proc.terminate()
        
        # Show error summary after processing is complete
        self.render_error_summary()
        self.console.print("\n👋 Goodbye!")

def main():
    """Main entry point"""
    renderer = StreamingTreeRenderer()
    renderer.run()

if __name__ == "__main__":
    main()