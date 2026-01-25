"""
Test suite for src/update_detector.py refactoring to remove Docker dependencies.
This test ensures that update_detector.py is properly refactored to work with Git-only updates
while removing all Docker image detection functionality.

Following TDD methodology:
1. Write tests first (RED)
2. Refactor update_detector.py (GREEN) 
3. Validate and optimize (REFACTOR)
"""

import os
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestUpdateDetectorDockerRemoval:
    """Test that Docker functionality is removed from update_detector.py."""
    
    def test_no_docker_methods(self):
        """Test that Docker image detection methods are removed."""
        from src.update_detector import UpdateDetector
        detector = UpdateDetector()
        
        # These Docker methods should not exist
        docker_methods = [
            'get_local_docker_image_commit_sha',
            'get_remote_docker_image_digest',
            'get_local_docker_image_digest',
            'get_remote_docker_image_commit_sha',
            'check_docker_update',
            'check_docker_image_update',
            'get_docker_image_commit_sha'
        ]
        
        for method in docker_methods:
            assert not hasattr(detector, method), f"Docker method {method} should be removed"
    
    def test_no_docker_references_in_file(self):
        """Test that Docker references are removed from the file."""
        update_detector_path = Path("src/update_detector.py")
        if update_detector_path.exists():
            with open(update_detector_path, 'r') as f:
                content = f.read()
                
            # Check that Docker-specific terms are removed
            docker_terms = [
                'docker',
                'container',
                'image',
                'ghcr.io',
                'buildx',
                'manifest',
                'digest'
            ]
            
            for term in docker_terms:
                # Allow some terms in comments but not in active code
                lines = content.split('\n')
                active_lines = [line for line in lines if not line.strip().startswith('#')]
                active_content = '\n'.join(active_lines)
                
                assert term.lower() not in active_content.lower(), f"Docker term '{term}' should be removed from active code"
    
    def test_no_docker_imports(self):
        """Test that Docker-related imports are removed."""
        update_detector_path = Path("src/update_detector.py")
        if update_detector_path.exists():
            with open(update_detector_path, 'r') as f:
                content = f.read()
                
            # Should not import Docker-related modules
            docker_imports = [
                'docker',
                'container'
            ]
            
            for docker_import in docker_imports:
                assert f"import {docker_import}" not in content, f"Docker import '{docker_import}' should be removed"


class TestUpdateDetectorGitFunctionality:
    """Test that Git functionality is preserved in update_detector.py."""
    
    def test_git_methods_preserved(self):
        """Test that Git-based methods are preserved."""
        from src.update_detector import UpdateDetector
        detector = UpdateDetector()
        
        # These Git methods should still exist
        git_methods = [
            'get_local_commit_sha',
            'get_remote_commit_sha',
            'get_commit_timestamp',
            'is_commit_ancestor',
            'get_current_commit_sha'
        ]
        
        for method in git_methods:
            assert hasattr(detector, method), f"Git method {method} should be preserved"
    
    def test_repository_update_check_exists(self):
        """Test that repository update check functionality exists."""
        from src.update_detector import UpdateDetector
        detector = UpdateDetector()
        
        # Should have method to check repository updates
        assert hasattr(detector, 'check_repository_update') or hasattr(detector, 'get_update_summary'), \
            "Repository update check method should exist"
    
    def test_git_functionality_works(self):
        """Test that Git functionality actually works."""
        from src.update_detector import UpdateDetector
        detector = UpdateDetector()
        
        # Test local commit SHA detection
        local_sha = detector.get_local_commit_sha()
        assert local_sha is None or isinstance(local_sha, str), "get_local_commit_sha should return string or None"
        
        # Test current commit SHA (should be same as local)
        current_sha = detector.get_current_commit_sha()
        assert current_sha is None or isinstance(current_sha, str), "get_current_commit_sha should return string or None"


class TestUpdateDetectorSimplified:
    """Test that update_detector.py is simplified correctly."""
    
    def test_file_size_reduced(self):
        """Test that file size is significantly reduced."""
        update_detector_path = Path("src/update_detector.py")
        if update_detector_path.exists():
            with open(update_detector_path, 'r') as f:
                lines = f.readlines()
            
            # Should be around 200 lines (down from 648 - 69% reduction)
            line_count = len(lines)
            assert line_count < 250, f"File should be simplified to ~200 lines, got {line_count}"
    
    def test_class_structure_simplified(self):
        """Test that UpdateDetector class is simplified."""
        from src.update_detector import UpdateDetector
        detector = UpdateDetector()
        
        # Should have basic initialization
        assert hasattr(detector, 'repo_owner'), "Should have repo_owner attribute"
        assert hasattr(detector, 'repo_name'), "Should have repo_name attribute"
        assert hasattr(detector, 'github_api_base'), "Should have github_api_base attribute"
        
        # Should NOT have Docker-specific attributes
        docker_attributes = [
            'ghcr_image'
        ]
        
        for attr in docker_attributes:
            assert not hasattr(detector, attr), f"Docker attribute {attr} should be removed"
    
    def test_update_summary_git_only(self):
        """Test that update summary only includes Git information."""
        from src.update_detector import UpdateDetector
        detector = UpdateDetector()
        
        # Mock the Git methods to avoid actual Git calls
        with patch.object(detector, 'get_local_commit_sha', return_value='abc123'), \
             patch.object(detector, 'get_remote_commit_sha', return_value='def456'):
            
            summary = detector.get_update_summary()
            
            # Should have timestamp and repository info
            assert 'timestamp' in summary, "Summary should include timestamp"
            assert 'repository' in summary or 'any_updates_available' in summary, "Summary should include repository info"
            
            # Should NOT have Docker info
            docker_keys = ['docker', 'image', 'container']
            for key in docker_keys:
                assert key not in summary, f"Summary should not include Docker key: {key}"


class TestUpdateDetectorErrorHandling:
    """Test that error handling is preserved without Docker dependencies."""
    
    def test_git_error_handling(self):
        """Test that Git error handling works correctly."""
        from src.update_detector import UpdateDetector
        detector = UpdateDetector()
        
        # Test with invalid Git repository (should handle gracefully)
        with patch('subprocess.run', side_effect=Exception("Git error")):
            local_sha = detector.get_local_commit_sha()
            assert local_sha is None, "Should handle Git errors gracefully"
    
    def test_network_error_handling(self):
        """Test that network error handling works correctly."""
        from src.update_detector import UpdateDetector
        detector = UpdateDetector()
        
        # Test with network error (should handle gracefully)
        with patch('urllib.request.urlopen', side_effect=Exception("Network error")):
            remote_sha = detector.get_remote_commit_sha()
            assert remote_sha is None, "Should handle network errors gracefully"


class TestUpdateDetectorPerformance:
    """Test that update_detector.py performance is optimized without Docker overhead."""
    
    def test_no_docker_subprocess_calls(self):
        """Test that Docker subprocess calls are removed."""
        update_detector_path = Path("src/update_detector.py")
        if update_detector_path.exists():
            with open(update_detector_path, 'r') as f:
                content = f.read()
            
            # Should not have Docker subprocess calls
            docker_commands = [
                'docker inspect',
                'docker buildx',
                'docker manifest',
                'docker pull'
            ]
            
            for command in docker_commands:
                assert command not in content, f"Docker command '{command}' should be removed"
    
    def test_simplified_initialization(self):
        """Test that initialization is simplified without Docker setup."""
        from src.update_detector import UpdateDetector
        
        # Should initialize quickly without Docker setup
        detector = UpdateDetector()
        
        # Should have basic attributes only
        required_attrs = ['repo_owner', 'repo_name', 'github_api_base']
        for attr in required_attrs:
            assert hasattr(detector, attr), f"Should have required attribute: {attr}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])