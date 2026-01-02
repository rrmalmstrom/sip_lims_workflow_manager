"""
Docker Environment Validation Utility

This module provides validation functions for Docker environment setup,
ensuring that required volumes are properly mounted and accessible.

Implementation Guidelines from ESP Docker Plan:
- Validate Docker environment and volume mounts
- Check required paths /data and /workflow-scripts
- Provide clear error messages for volume mount failures
- Test write permissions on mounted volumes
"""

import streamlit as st
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging - use INFO level to reduce debug noise
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_docker_environment() -> bool:
    """
    Check if we're running in a Docker container.
    
    Returns:
        bool: True if running in Docker, False otherwise
    """
    is_docker = os.path.exists("/.dockerenv")
    logger.debug(f"DOCKER_CHECK: Is Docker environment: {is_docker}")
    return is_docker

def validate_docker_environment() -> bool:
    """
    Validate Docker environment and volume mounts.
    
    This function checks that required Docker volumes are properly mounted
    and accessible. Should be called during application startup.
    Uses session state caching to prevent infinite validation loops.
    Only shows UI messages on first run or if validation fails.
    
    Returns:
        bool: True if environment is valid, False otherwise
    """
    # Use session state to cache validation results and prevent infinite loops
    if 'docker_validation_completed' not in st.session_state:
        st.session_state.docker_validation_completed = False
        st.session_state.docker_validation_result = False
        st.session_state.docker_validation_first_run = True
    
    # If validation already completed, return cached result silently
    if st.session_state.docker_validation_completed:
        return st.session_state.docker_validation_result
    
    logger.info("DOCKER_VALIDATION: Starting Docker environment validation")
    
    # Create a placeholder for validation messages that can be cleared
    validation_placeholder = st.empty()
    
    try:
        if not is_docker_environment():
            logger.info("DOCKER_VALIDATION: Not in Docker environment, validation passed")
            st.session_state.docker_validation_completed = True
            st.session_state.docker_validation_result = True
            return True
        
        # Show initial validation message
        with validation_placeholder.container():
            st.info("🐳 **Docker Mode**: Validating environment...")
        
        # Check required Docker volume paths
        required_paths = ["/data"]
        optional_paths = ["/workflow-scripts"]
        
        validation_passed = True
        validation_messages = []
        
        # Validate required paths
        for path in required_paths:
            if not os.path.exists(path):
                logger.error(f"DOCKER_VALIDATION: Required Docker volume not mounted: {path}")
                validation_messages.append(("error", f"❌ Required Docker volume not mounted: {path}"))
                validation_messages.append(("info", "💡 **Solution**: Please ensure you're using proper volume mounts"))
                validation_messages.append(("code", f"docker-compose up  # or ensure PROJECT_PATH is set correctly"))
                validation_passed = False
            else:
                logger.debug(f"DOCKER_VALIDATION: Required path exists: {path}")
        
        # Check optional paths (warn but don't fail)
        for path in optional_paths:
            if not os.path.exists(path):
                logger.warning(f"DOCKER_VALIDATION: Optional Docker volume not mounted: {path}")
                validation_messages.append(("warning", f"⚠️ Optional Docker volume not mounted: {path}"))
                validation_messages.append(("info", "💡 This may affect script functionality"))
            else:
                logger.debug(f"DOCKER_VALIDATION: Optional path exists: {path}")
        
        # Test write permissions on /data (without UI messages to prevent loops)
        if os.path.exists("/data"):
            write_test_passed = _check_write_permissions_silent("/data")
            if not write_test_passed:
                validation_passed = False
                validation_messages.append(("error", "❌ Write permissions test failed for /data"))
        
        # Test read permissions on /workflow-scripts if it exists (without UI messages)
        if os.path.exists("/workflow-scripts"):
            read_test_passed = _check_read_permissions_silent("/workflow-scripts")
            if not read_test_passed:
                validation_messages.append(("warning", "⚠️ Read permissions test failed for /workflow-scripts"))
        
        # Display results
        if validation_passed:
            logger.info("DOCKER_VALIDATION: Docker environment validation passed")
            # Show brief success message that will be cleared
            with validation_placeholder.container():
                st.success("✅ **Docker Environment**: Validation completed successfully")
            
            # Clear the success message after 5 seconds by replacing with empty content
            import time
            time.sleep(5)
            validation_placeholder.empty()
            
        else:
            logger.error("DOCKER_VALIDATION: Docker environment validation failed")
            # Show persistent error messages for failed validation
            with validation_placeholder.container():
                for msg_type, msg_content in validation_messages:
                    if msg_type == "error":
                        st.error(msg_content)
                    elif msg_type == "warning":
                        st.warning(msg_content)
                    elif msg_type == "info":
                        st.info(msg_content)
                    elif msg_type == "code":
                        st.code(msg_content)
                
                st.info("🔧 **Troubleshooting Steps:**")
                st.info("1. Ensure Docker Desktop is running")
                st.info("2. Check that PROJECT_PATH environment variable is set")
                st.info("3. Verify volume mounts in docker-compose.yml")
                st.info("4. Try restarting the container: `docker-compose down && docker-compose up`")
        
        # Cache the result to prevent re-validation
        st.session_state.docker_validation_completed = True
        st.session_state.docker_validation_result = validation_passed
        st.session_state.docker_validation_first_run = False
        
        return validation_passed
        
    except Exception as e:
        logger.error(f"DOCKER_VALIDATION: Error during Docker validation: {e}")
        with validation_placeholder.container():
            st.error(f"❌ Docker validation error: {e}")
        st.session_state.docker_validation_completed = True
        st.session_state.docker_validation_result = False
        return False

def check_write_permissions(path: str, required: bool = True) -> bool:
    """
    Test write permissions on a mounted volume.
    
    Args:
        path: Path to test write permissions on
        required: Whether write permissions are required (affects error handling)
        
    Returns:
        bool: True if write permissions are available, False otherwise
    """
    logger.debug(f"PERMISSION_TEST: Testing write permissions on: {path}")
    
    test_file = os.path.join(path, ".permission_test")
    try:
        # Test file creation
        with open(test_file, 'w') as f:
            f.write("Docker permission test")
        
        # Test file reading
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up test file
        os.remove(test_file)
        
        logger.debug(f"PERMISSION_TEST: Write permissions test passed for {path}")
        return True
        
    except PermissionError as e:
        error_msg = f"Container user lacks write permissions to {path}"
        logger.error(f"PERMISSION_TEST: {error_msg}: {e}")
        
        if required:
            st.error(f"❌ {error_msg}")
            st.info("💡 **Solution**: Check user ID mapping in docker-compose.yml")
            st.code("""
# Ensure these environment variables are set:
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
docker-compose up
            """)
        else:
            st.warning(f"⚠️ Limited write permissions: {path}")
        
        return False
        
    except Exception as e:
        error_msg = f"Error testing permissions on {path}: {e}"
        logger.error(f"PERMISSION_TEST: {error_msg}")
        
        if required:
            st.error(f"❌ {error_msg}")
        else:
            st.warning(f"⚠️ {error_msg}")
        
        return False

def _check_write_permissions_silent(path: str) -> bool:
    """
    Test write permissions on a mounted volume without UI messages.
    Used during validation to prevent infinite loops.
    
    Args:
        path: Path to test write permissions on
        
    Returns:
        bool: True if write permissions are available, False otherwise
    """
    logger.debug(f"PERMISSION_TEST: Testing write permissions on: {path}")
    
    test_file = os.path.join(path, ".permission_test")
    try:
        # Test file creation
        with open(test_file, 'w') as f:
            f.write("Docker permission test")
        
        # Test file reading
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up test file
        os.remove(test_file)
        
        logger.debug(f"PERMISSION_TEST: Write permissions test passed for {path}")
        return True
        
    except Exception as e:
        logger.error(f"PERMISSION_TEST: Write permissions test failed for {path}: {e}")
        return False

def check_read_permissions(path: str) -> bool:
    """
    Test read permissions on a mounted volume (for read-only volumes like workflow scripts).
    
    Args:
        path: Path to test read permissions on
        
    Returns:
        bool: True if read permissions are available, False otherwise
    """
    logger.debug(f"READ_PERMISSION_TEST: Testing read permissions on: {path}")
    
    try:
        # Test directory listing
        contents = os.listdir(path)
        
        # Test reading a file if any exist
        for item in contents:
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                try:
                    with open(item_path, 'r') as f:
                        # Just read first few bytes to test access
                        f.read(100)
                    break
                except (UnicodeDecodeError, PermissionError):
                    # Skip files we can't read (binary files, permission issues)
                    continue
        
        logger.debug(f"READ_PERMISSION_TEST: Read permissions test passed for {path}")
        return True
        
    except PermissionError as e:
        error_msg = f"Container user lacks read permissions to {path}"
        logger.error(f"READ_PERMISSION_TEST: {error_msg}: {e}")
        st.warning(f"⚠️ {error_msg}")
        return False
        
    except Exception as e:
        error_msg = f"Error testing read permissions on {path}: {e}"
        logger.error(f"READ_PERMISSION_TEST: {error_msg}")
        st.warning(f"⚠️ {error_msg}")
        return False

def _check_read_permissions_silent(path: str) -> bool:
    """
    Test read permissions on a mounted volume without UI messages.
    Used during validation to prevent infinite loops.
    
    Args:
        path: Path to test read permissions on
        
    Returns:
        bool: True if read permissions are available, False otherwise
    """
    logger.debug(f"READ_PERMISSION_TEST: Testing read permissions on: {path}")
    
    try:
        # Test directory listing
        contents = os.listdir(path)
        
        # Test reading a file if any exist
        for item in contents:
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                try:
                    with open(item_path, 'r') as f:
                        # Just read first few bytes to test access
                        f.read(100)
                    break
                except (UnicodeDecodeError, PermissionError):
                    # Skip files we can't read (binary files, permission issues)
                    continue
        
        logger.debug(f"READ_PERMISSION_TEST: Read permissions test passed for {path}")
        return True
        
    except Exception as e:
        logger.error(f"READ_PERMISSION_TEST: Read permissions test failed for {path}: {e}")
        return False

def validate_volume_mounts() -> Dict[str, bool]:
    """
    Validate all expected volume mounts and return detailed status.
    
    Returns:
        Dict[str, bool]: Dictionary mapping volume paths to their validation status
    """
    logger.info("VOLUME_VALIDATION: Starting volume mount validation")
    
    volume_status = {}
    
    # Expected volume mounts
    expected_volumes = {
        "/data": {"required": True, "description": "Project data volume"},
        "/workflow-scripts": {"required": False, "description": "Workflow scripts volume"}
    }
    
    for volume_path, config in expected_volumes.items():
        exists = os.path.exists(volume_path)
        volume_status[volume_path] = exists
        
        if exists:
            logger.debug(f"VOLUME_VALIDATION: Volume exists: {volume_path}")
            st.success(f"✅ {config['description']}: {volume_path}")
            
            # Test if it's actually a mount point (not just an empty directory)
            if is_mount_point(volume_path):
                st.info(f"📁 Volume properly mounted: {volume_path}")
            else:
                st.warning(f"⚠️ Directory exists but may not be mounted: {volume_path}")
                
        else:
            logger.warning(f"VOLUME_VALIDATION: Volume missing: {volume_path}")
            if config["required"]:
                st.error(f"❌ Required {config['description']} not found: {volume_path}")
            else:
                st.warning(f"⚠️ Optional {config['description']} not found: {volume_path}")
    
    return volume_status

def is_mount_point(path: str) -> bool:
    """
    Check if a path is a mount point.
    
    Args:
        path: Path to check
        
    Returns:
        bool: True if path is a mount point, False otherwise
    """
    try:
        # In Docker, mounted volumes typically have different device IDs
        # than the root filesystem
        path_stat = os.stat(path)
        parent_stat = os.stat(os.path.dirname(path))
        
        # If device IDs differ, it's likely a mount point
        is_mount = path_stat.st_dev != parent_stat.st_dev
        logger.debug(f"MOUNT_CHECK: {path} is mount point: {is_mount}")
        return is_mount
        
    except Exception as e:
        logger.debug(f"MOUNT_CHECK: Error checking mount point {path}: {e}")
        return False

def get_docker_environment_info() -> Dict[str, any]:
    """
    Get comprehensive information about the Docker environment.
    
    Returns:
        Dict[str, any]: Environment information including paths, permissions, etc.
    """
    info = {
        "is_docker": is_docker_environment(),
        "working_directory": os.getcwd(),
        "user_id": os.getuid() if hasattr(os, 'getuid') else "N/A",
        "group_id": os.getgid() if hasattr(os, 'getgid') else "N/A",
        "environment_variables": {
            "USER": os.environ.get("USER", "N/A"),
            "HOME": os.environ.get("HOME", "N/A"),
            "PWD": os.environ.get("PWD", "N/A"),
            "APP_ENV": os.environ.get("APP_ENV", "N/A")
        }
    }
    
    if is_docker_environment():
        info.update({
            "data_path_exists": os.path.exists("/data"),
            "scripts_path_exists": os.path.exists("/workflow-scripts"),
            "data_writable": check_write_permissions("/data") if os.path.exists("/data") else False,
            "scripts_readable": check_read_permissions("/workflow-scripts") if os.path.exists("/workflow-scripts") else False
        })
    
    logger.debug(f"ENVIRONMENT_INFO: {info}")
    return info

def display_environment_status():
    """
    Display a comprehensive status of the Docker environment in Streamlit.
    """
    st.subheader("🐳 Docker Environment Status")
    
    env_info = get_docker_environment_info()
    
    if env_info["is_docker"]:
        st.success("✅ Running in Docker container")
        
        # Display volume status
        volume_status = validate_volume_mounts()
        
        # Display user information
        st.info(f"👤 Container User ID: {env_info['user_id']}")
        st.info(f"👥 Container Group ID: {env_info['group_id']}")
        
        # Display environment variables
        with st.expander("🔧 Environment Variables"):
            for key, value in env_info["environment_variables"].items():
                st.text(f"{key}: {value}")
                
    else:
        st.info("ℹ️ Running in native environment (not Docker)")
        st.text(f"Working Directory: {env_info['working_directory']}")