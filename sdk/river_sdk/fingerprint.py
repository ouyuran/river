import cloudpickle
import sys
import cloudpickle.cloudpickle as cp
from typing import Any
import hashlib
from importlib import metadata
import os
import io
import pickletools

def _setup_deterministic_pickle():
    def deterministic_tracker_id(class_def):
        return "River doesn't care"
    
    cp._get_or_create_tracker_id = deterministic_tracker_id

_setup_deterministic_pickle()

def get_module_version(module_name: str) -> str:
    return metadata.version(module_name)

def is_third_party_module(module) -> bool:
    if not hasattr(module, '__file__') or module.__file__ is None:
        return False
    
    file_path = os.path.abspath(module.__file__)
    
    indicators = [
        'site-packages',
        'dist-packages', 
        '.local/lib',
        'conda',
        'anaconda'
    ]
    
    return any(indicator in file_path for indicator in indicators)

class DependencyTracker:
    def __init__(self):
        self.third_party_deps: dict[str, str] = {}
        self.tracked_modules: set[str] = set()
    
    def track_module(self, module_name: str):
        if module_name in self.tracked_modules:
            return
        
        self.tracked_modules.add(module_name)
        
        if module_name not in sys.modules:
            return
        
        module = sys.modules[module_name]
        
        if is_third_party_module(module):
            version = get_module_version(module_name)
            if version:
                self.third_party_deps[module_name] = version

    def get_dependency_info(self) -> dict[str, Any]:
        return self.third_party_deps
    
class CloudPicklerWithDependencyTracker(cloudpickle.CloudPickler):
    def __init__(self, file, protocol=None, buffer_callback=None, track_dependencies=True):
        super().__init__(file, protocol=protocol, buffer_callback=buffer_callback)
        self.track_dependencies = track_dependencies
        self.dependency_tracker = DependencyTracker()
    
    def save_global(self, obj, name=None):
        if self.track_dependencies and hasattr(obj, '__module__'):
            module_name = obj.__module__
            if module_name:
                self.dependency_tracker.track_module(module_name)
        
        return super().save_global(obj, name=name)
    
    def save_function(self, obj, name=None):
        if self.track_dependencies:
            # Track function's module
            if hasattr(obj, '__module__') and obj.__module__:
                self.dependency_tracker.track_module(obj.__module__)
            
            # Track modules referenced in function globals
            if hasattr(obj, '__globals__'):
                for global_name, global_value in obj.__globals__.items():
                    # Check for module objects
                    if hasattr(global_value, '__name__') and hasattr(global_value, '__file__'):
                        self.dependency_tracker.track_module(global_value.__name__)
                    # Check module attribute of other objects
                    elif hasattr(global_value, '__module__') and global_value.__module__:
                        self.dependency_tracker.track_module(global_value.__module__)
        
        return super().save_function(obj, name=name)

def dumps_with_deps(obj, protocol=None, track_dependencies=True) -> tuple[bytes, dict]:
    with io.BytesIO() as buffer:
        pickler = CloudPicklerWithDependencyTracker(
            buffer, 
            protocol=protocol, 
            track_dependencies=track_dependencies
        )
        pickler.dump(obj)
        
        pickled_data = buffer.getvalue()
        deps_info = pickler.dependency_tracker.get_dependency_info()
        
        return pickled_data, deps_info

def sys_info() -> str:
    return sys.version

def fingerprint(obj: Any) -> str:
    obj_bytes, deps_info = dumps_with_deps(obj)
    bytes = b''.join([
        obj_bytes,
        str(deps_info).encode(),
        sys_info().encode()
    ])
    print(hashlib.sha1(obj_bytes).hexdigest())
    # print(pickletools.dis(obj_bytes))
    print(deps_info)
    return hashlib.sha1(bytes).hexdigest()
