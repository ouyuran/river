# Module for fingerprint testing
import sys
import hashlib
import cloudpickle
from fabric import Connection
from hashlib import sha1, md5

sample_global_var = "sample_value"

def sample_function():
    return "sample"

class SampleClass:
    def method(self):
        return "sample_method"

def factory_function():
    def inner_function():
        return "inner"
    return inner_function

# Functions that use third-party libraries
def function_using_import_lib():
    """Function that uses hashlib.sha1"""
    return hashlib.sha1(b"test").hexdigest()

def function_using_from_import():
    """Function that uses sha1 directly imported from hashlib"""
    return sha1(b"test").hexdigest()

def function_using_cloudpickle():
    """Function that uses cloudpickle"""
    data = {"key": "value"}
    return cloudpickle.dumps(data)

def function_using_fabric():
    """Function that references fabric Connection class"""
    return Connection.__name__

# Class that uses third-party libraries  
class ClassUsingThirdParty:
    def use_hashlib(self):
        return hashlib.md5(b"test").hexdigest()
    
    def use_from_import(self):
        return md5(b"test").hexdigest()

