import pytest
import sys
from unittest.mock import patch
from river_sdk.fingerprint import get_fp, pickle_by_reference_modules
from . import test_module_for_fingerprint


class TestFingerprint:

    def _assert_valid_fingerprint(self, obj):
        """Helper to validate fingerprint format"""
        fp = get_fp(obj)
        assert isinstance(fp, str)
        assert len(fp) == 40  # SHA1 hex digest length
        return fp
    
    def test_fingerprint_consistency(self):
        """Test fingerprint consistency and uniqueness"""
        obj = lambda x: x + 1
        
        # Same object should produce same fingerprint
        fp1 = get_fp(obj)
        fp2 = get_fp(obj)
        assert fp1 == fp2
        
        # Different objects should produce different fingerprints
        different_obj = lambda x: x + 2
        fp3 = get_fp(different_obj)
        assert fp1 != fp3

    @pytest.mark.parametrize("obj", [
        test_module_for_fingerprint,  # module
        test_module_for_fingerprint.sample_function,  # function
        test_module_for_fingerprint.SampleClass,  # class
        test_module_for_fingerprint.sample_global_var,  # global variable
        lambda x: x * 2,  # lambda function
    ])
    def test_various_object_types(self, obj):
        """Test fingerprinting various object types"""
        self._assert_valid_fingerprint(obj)
    
    def test_dynamic_objects(self):
        """Test fingerprinting dynamically created objects"""
        # Dynamic function
        namespace = {}
        exec("def dynamic_func(x): return x ** 2", namespace)
        self._assert_valid_fingerprint(namespace['dynamic_func'])
        
        # Dynamic class
        DynamicClass = type('DynamicClass', (), {'method': lambda self: 'test'})
        self._assert_valid_fingerprint(DynamicClass)
    
    @pytest.mark.parametrize("func", [
        test_module_for_fingerprint.function_using_import_lib,  # import hashlib
        test_module_for_fingerprint.function_using_from_import,  # from hashlib import sha1
        test_module_for_fingerprint.function_using_cloudpickle,  # cloudpickle
        test_module_for_fingerprint.function_using_fabric,  # fabric
        test_module_for_fingerprint.ClassUsingThirdParty,  # class with third-party usage
    ])
    def test_third_party_libraries(self, func):
        """Test fingerprinting functions that use third-party libraries"""
        self._assert_valid_fingerprint(func)

    @patch('river_sdk.fingerprint.sys_info')
    def test_environment_dependency(self, mock_sys_info):
        """Test that fingerprints depend on system/module environment"""
        obj = lambda x: x
        
        # Different system info should produce different fingerprints
        mock_sys_info.return_value = "3.11.0"
        fp1 = get_fp(obj)
        
        mock_sys_info.return_value = "3.12.0"
        fp2 = get_fp(obj)
        
        assert fp1 != fp2

    @patch('river_sdk.fingerprint.metadata.version')
    def test_module_version_dependency(self, mock_version):
        """Test that fingerprints depend on module versions"""
        mock_version.side_effect = ["1.0.0", "2.0.0"]
        test_func = test_module_for_fingerprint.sample_function
        
        fp1 = get_fp(test_func)
        fp2 = get_fp(test_func)
        
        assert fp1 != fp2

    def test_internal_state_management(self):
        """Test that internal state is properly managed"""
        from river_sdk.fingerprint import deterministic_tracker_id
        import cloudpickle.cloudpickle as cp
        from river_sdk.fingerprint import _origin_get_or_create_tracker_id, _origin_should_pickle_by_reference
        
        # Test deterministic tracker ID
        assert deterministic_tracker_id(object()) == "The wind, the horse and the cow."
        
        # Test state reset
        assert pickle_by_reference_modules == {}
        get_fp(lambda x: x)
        assert pickle_by_reference_modules == {}
        
        # Test function restoration
        original_tracker = cp._get_or_create_tracker_id
        get_fp(lambda x: x)
        assert cp._get_or_create_tracker_id == original_tracker
