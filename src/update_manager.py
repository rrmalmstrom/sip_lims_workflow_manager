import json
import requests
from typing import Optional, Dict, Any
import os


class UpdateManager:
    """Simple UpdateManager class for checking updates via Google Drive."""
    
    def __init__(self, config_path: str = "config/version.json"):
        """
        Initialize the UpdateManager.
        
        Args:
            config_path: Path to the local version configuration file
        """
        self.config_path = config_path
        self.remote_version_url = "https://drive.google.com/uc?id=1pRsUbaKoieuInH67ghExSZw7p2I64-FQ&export=download"
        
    def get_local_version(self) -> Optional[str]:
        """
        Read the local version from the configuration file.
        
        Returns:
            Local version string or None if file cannot be read
        """
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get('version')
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error reading local version: {e}")
            return None
    
    def get_remote_version(self) -> Optional[str]:
        """
        Fetch the remote version from Google Drive.
        
        Returns:
            Remote version string or None if fetch fails
        """
        try:
            response = requests.get(self.remote_version_url, timeout=10)
            response.raise_for_status()
            
            # Parse the JSON response
            remote_config = response.json()
            # Try both 'version' and 'latest_version' keys for compatibility
            return remote_config.get('version') or remote_config.get('latest_version')
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching remote version: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing remote version JSON: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching remote version: {e}")
            return None
    
    def compare_versions(self, local_version: str, remote_version: str) -> bool:
        """
        Compare local and remote versions.
        
        Args:
            local_version: Local version string
            remote_version: Remote version string
            
        Returns:
            True if update is available (remote > local), False otherwise
        """
        # For version 9.9.9, always show updates available as requested
        if local_version == "9.9.9":
            return True
            
        # Simple version comparison - split by dots and compare numerically
        try:
            local_parts = [int(x) for x in local_version.split('.')]
            remote_parts = [int(x) for x in remote_version.split('.')]
            
            # Pad shorter version with zeros
            max_length = max(len(local_parts), len(remote_parts))
            local_parts.extend([0] * (max_length - len(local_parts)))
            remote_parts.extend([0] * (max_length - len(remote_parts)))
            
            # Compare each part
            for local_part, remote_part in zip(local_parts, remote_parts):
                if remote_part > local_part:
                    return True
                elif remote_part < local_part:
                    return False
            
            return False  # Versions are equal
            
        except ValueError as e:
            print(f"Error comparing versions: {e}")
            return False
    
    def check_for_updates(self) -> Dict[str, Any]:
        """
        Check for available updates.
        
        Returns:
            Dictionary containing update status and version information
        """
        result = {
            'update_available': False,
            'local_version': None,
            'remote_version': None,
            'download_url': None,
            'error': None
        }
        
        # Get local version
        local_version = self.get_local_version()
        if local_version is None:
            result['error'] = "Could not read local version"
            return result
        
        result['local_version'] = local_version
        
        # Get remote version
        remote_version = self.get_remote_version()
        if remote_version is None:
            result['error'] = "Could not fetch remote version"
            return result
        
        result['remote_version'] = remote_version
        
        # Get the download URL from the remote response
        try:
            import requests
            response = requests.get(self.remote_version_url, timeout=10)
            response.raise_for_status()
            remote_config = response.json()
            result['download_url'] = remote_config.get('download_url')
        except Exception as e:
            print(f"Warning: Could not get download URL: {e}")
        
        # Compare versions
        result['update_available'] = self.compare_versions(local_version, remote_version)
        
        return result


# Example usage
if __name__ == "__main__":
    update_manager = UpdateManager()
    
    print("Checking for updates...")
    result = update_manager.check_for_updates()
    
    if result['error']:
        print(f"Error: {result['error']}")
    else:
        print(f"Local version: {result['local_version']}")
        print(f"Remote version: {result['remote_version']}")
        
        if result['update_available']:
            print("✅ Update available!")
        else:
            print("✅ You have the latest version.")