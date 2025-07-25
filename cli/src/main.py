import subprocess
import sys 
import json
from rich.live import Live
from rich.tree import Tree
from rich.console import Console
from river_common import Status

def get_status_color(status: Status) -> str:
    """Get color for status display"""
    color_map = {
        Status.PENDING: "yellow",
        Status.RUNNING: "blue", 
        Status.SUCCESS: "green",
        Status.FAILED: "red",
        Status.SKIPPED: "dim"
    }
    return color_map.get(status, "white")

def create_tree_from_data():
    """Run data.py and parse output to create tree structure"""
    try:
        # Run data.py as subprocess and capture output
        result = subprocess.run(["uv", "run", "python", "src/data.py"], 
                              capture_output=True, text=True, cwd=".")
        
        if result.returncode != 0:
            return Tree("❌ Error running data.py")
        
        # Parse JSON output lines
        lines = result.stdout.strip().split('\n')
        items = []
        
        for line in lines:
            if line.strip():
                try:
                    item = json.loads(line)
                    items.append(item)
                except json.JSONDecodeError:
                    continue
        
        # Build tree structure
        tree = Tree("🌊 River Status")
        nodes = {}
        
        # First pass: create all nodes
        for item in items:
            status = Status(item['status'])
            color = get_status_color(status)
            
            if item['type'] == 'river':
                label = f"[{color}]{item['name']} ({status.value})[/{color}]"
                tree.label = f"🌊 {label}"
                nodes[item['id']] = tree
            else:
                if item['type'] == 'job':
                    icon = "⚙️"
                else:  # task
                    icon = "📋"
                
                label = f"[{color}]{icon} {item['name']} ({status.value})[/{color}]"
                node = Tree(label)
                nodes[item['id']] = node
        
        # Second pass: build hierarchy  
        for item in items:
            if item['type'] != 'river' and item['parent_id'] in nodes:
                parent = nodes[item['parent_id']]
                child = nodes[item['id']]
                parent.add(child)
        
        return tree
        
    except Exception as e:
        return Tree(f"❌ Error: {str(e)}")

def main():
    """Main live display function"""
    console = Console()
    
    with Live(create_tree_from_data(), refresh_per_second=2, console=console) as live:
        try:
            while True:
                live.update(create_tree_from_data())
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()