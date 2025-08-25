import cloudpickle
import sys
import cloudpickle.cloudpickle as cp
from typing import Any
from types import FunctionType, ModuleType
import hashlib
from importlib import metadata


_origin_get_or_create_tracker_id = cp._get_or_create_tracker_id
_origin_should_pickle_by_reference = cp._should_pickle_by_reference
pickle_by_reference_modules = {}

def sys_info() -> str:
    return sys.version

def deterministic_tracker_id(class_def) -> str:
    return "The wind, the horse and the cow."
    
def should_pickle_by_reference_with_record(obj, name=None) -> bool:
    result = _origin_should_pickle_by_reference(obj, name=name)
    module = None
    if isinstance(obj, FunctionType) or issubclass(type(obj), type):
        module_and_name = cp._lookup_module_and_qualname(obj, name=name)
        if module_and_name:
            module = module_and_name[0]
    elif isinstance(obj, ModuleType):
        module = obj
    else:
        # Should not goes here, cloudpickle raises error in this case
        ...

    if module:
        module_name = module.__name__
        root_module_name = module_name.split(".")[0]
        try:
            root_module_version = metadata.version(root_module_name)
            pickle_by_reference_modules[root_module_name] = root_module_version
        except metadata.PackageNotFoundError:
            # Skip modules without package metadata (internal modules, stdlib, etc.)
            pass

    return result

def get_fp(obj: Any) -> str:
    global pickle_by_reference_modules
    pickle_by_reference_modules = {}
    
    cp._get_or_create_tracker_id = deterministic_tracker_id
    cp._should_pickle_by_reference = should_pickle_by_reference_with_record

    obj_bytes = cloudpickle.dumps(obj)
    bytes = b''.join([
        obj_bytes,
        str(pickle_by_reference_modules).encode(),
        sys_info().encode()
    ])

    pickle_by_reference_modules = {}
    cp._get_or_create_tracker_id = _origin_get_or_create_tracker_id
    cp._should_pickle_by_reference = _origin_should_pickle_by_reference

    return hashlib.sha1(bytes).hexdigest()

# TODO, TEST
# import moudel
# import function
# import class
# global variable
# dynamic import
# lambda function
# dynamic function
# dynamic class