"""SSH Key Manager for secure deploy key handling."""

import os
import stat
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib


class SSHKeyManager:
    """Manages SSH deploy keys for secure GitHub repository access."""
    
    def __init__(self, ssh_dir: Path = None):
        """Initialize SSH key manager."""
        if ssh_dir is None:
            ssh_dir = Path(__file__).parent.parent / ".ssh"
        
        self.ssh_dir = Path(ssh_dir)
        self.private_key_path = self.ssh_dir / "deploy_key"
        self.public_key_path = self.ssh_dir / "deploy_key.pub"
        
    def validate_key_security(self) -> Dict[str, Any]:
        """Validate SSH key security settings."""
        result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'key_info': {}
        }
        
        # Check if keys exist
        if not self.private_key_path.exists():
            result['valid'] = False
            result['issues'].append("Private key file not found")
            return result
            
        if not self.public_key_path.exists():
            result['valid'] = False
            result['issues'].append("Public key file not found")
            return result
        
        # Check file permissions
        private_stat = self.private_key_path.stat()
        private_perms = stat.filemode(private_stat.st_mode)
        
        if private_stat.st_mode & 0o077:  # Check if group/other have any permissions
            result['issues'].append(f"Private key permissions too open: {private_perms}")
            result['valid'] = False
        
        # Check key type and strength
        try:
            with open(self.public_key_path, 'r') as f:
                public_key_content = f.read().strip()
            
            if public_key_content.startswith('ssh-ed25519'):
                result['key_info']['type'] = 'ed25519'
                result['key_info']['strength'] = 'excellent'
            elif public_key_content.startswith('ssh-rsa'):
                # Check RSA key length
                key_parts = public_key_content.split()
                if len(key_parts) >= 2:
                    # Estimate key length (rough approximation)
                    key_data_len = len(key_parts[1])
                    if key_data_len > 500:  # Roughly 4096-bit
                        result['key_info']['type'] = 'rsa-4096'
                        result['key_info']['strength'] = 'good'
                    elif key_data_len > 350:  # Roughly 2048-bit
                        result['key_info']['type'] = 'rsa-2048'
                        result['key_info']['strength'] = 'acceptable'
                        result['warnings'].append("Consider upgrading to Ed25519 for better security")
                    else:
                        result['key_info']['type'] = 'rsa-weak'
                        result['key_info']['strength'] = 'weak'
                        result['issues'].append("RSA key appears to be less than 2048 bits")
                        result['valid'] = False
            else:
                result['warnings'].append("Unknown key type")
                result['key_info']['type'] = 'unknown'
                result['key_info']['strength'] = 'unknown'
        
        except Exception as e:
            result['issues'].append(f"Error reading public key: {e}")
            result['valid'] = False
        
        # Check if SSH directory is properly secured
        ssh_stat = self.ssh_dir.stat()
        if ssh_stat.st_mode & 0o077:
            result['warnings'].append("SSH directory permissions could be more restrictive")
        
        return result
    
    def fix_permissions(self) -> bool:
        """Fix SSH key file permissions."""
        try:
            # Set proper permissions on SSH directory
            self.ssh_dir.chmod(0o700)
            
            # Set proper permissions on private key
            if self.private_key_path.exists():
                self.private_key_path.chmod(0o600)
            
            # Set proper permissions on public key
            if self.public_key_path.exists():
                self.public_key_path.chmod(0o644)
            
            return True
        except Exception as e:
            print(f"Error fixing permissions: {e}")
            return False
    
    def get_key_fingerprint(self) -> Optional[str]:
        """Get SSH key fingerprint for verification."""
        try:
            result = subprocess.run(
                ['ssh-keygen', '-lf', str(self.public_key_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract fingerprint from output
                output_parts = result.stdout.strip().split()
                if len(output_parts) >= 2:
                    return output_parts[1]  # The fingerprint part
            
            return None
        except Exception:
            return None
    
    def test_key_access(self, repo_url: str, timeout: int = 10) -> Dict[str, Any]:
        """Test if SSH key can access a repository."""
        result = {
            'success': False,
            'error': None,
            'response_time': None
        }
        
        try:
            import time
            start_time = time.time()
            
            # Set up environment for SSH key
            env = os.environ.copy()
            env['GIT_SSH_COMMAND'] = f'ssh -i {self.private_key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no'
            
            # Test with git ls-remote (lightweight operation)
            test_result = subprocess.run(
                ['git', 'ls-remote', repo_url],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            result['response_time'] = time.time() - start_time
            
            if test_result.returncode == 0:
                result['success'] = True
            else:
                result['error'] = test_result.stderr.strip()
        
        except subprocess.TimeoutExpired:
            result['error'] = f"Connection timeout after {timeout} seconds"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def get_ssh_command(self) -> str:
        """Get the SSH command string for Git operations."""
        return f'ssh -i {self.private_key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no'
    
    def create_git_env(self) -> Dict[str, str]:
        """Create environment variables for Git operations with SSH key."""
        env = os.environ.copy()
        env['GIT_SSH_COMMAND'] = self.get_ssh_command()
        return env


# Example usage and testing
if __name__ == "__main__":
    ssh_manager = SSHKeyManager()
    
    print("=== SSH Key Security Validation ===")
    validation = ssh_manager.validate_key_security()
    
    print(f"Valid: {validation['valid']}")
    if validation['key_info']:
        print(f"Key type: {validation['key_info'].get('type', 'unknown')}")
        print(f"Security strength: {validation['key_info'].get('strength', 'unknown')}")
    
    if validation['issues']:
        print("\nIssues found:")
        for issue in validation['issues']:
            print(f"  ❌ {issue}")
    
    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️ {warning}")
    
    # Get fingerprint
    fingerprint = ssh_manager.get_key_fingerprint()
    if fingerprint:
        print(f"\nKey fingerprint: {fingerprint}")
    
    # Test access (example - replace with actual repo URL)
    # test_result = ssh_manager.test_key_access("git@github.com:user/repo.git")
    # print(f"Access test: {'✅ Success' if test_result['success'] else '❌ Failed'}")