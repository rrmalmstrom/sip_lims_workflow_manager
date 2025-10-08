# SSH Key Management

This document provides a developer's guide to the SSH key management system in the SIP LIMS Workflow Manager. The system is designed for secure, flexible, and reliable access to the application and script repositories on GitHub.

## Architecture

The application uses a dedicated SSH key for each repository to ensure a clear separation of concerns and enhance security. This resolves the "key already in use" error that can occur when a single deploy key is used for multiple repositories.

-   **Application Repository Key**: `app_deploy_key` is used for all interactions with the `sip_lims_workflow_manager` repository.
-   **Scripts Repository Key**: `scripts_deploy_key` is used for all interactions with the `sip_scripts_workflow_gui` repository.

These keys are stored in the `.ssh/` directory in the root of the application.

### `SSHKeyManager` Class

The `src/ssh_key_manager.py` module contains the `SSHKeyManager` class, which is responsible for all SSH key operations.

-   **Dynamic Key Loading**: The class is initialized with a `key_name` (`app_deploy_key` or `scripts_deploy_key`), and it dynamically loads the correct key paths.
-   **Security Validation**: The `validate_key_security()` method automatically checks for common security issues, including:
    -   **File Permissions**: Ensures that the private key permissions are set to `600` (read/write for owner only).
    -   **Key Type and Strength**: Recommends the use of modern, secure `Ed25519` keys and warns about weaker `RSA` keys.
-   **Access Testing**: The `test_key_access()` method provides a simple way to test if a key has the necessary permissions to access its corresponding repository.

### `GitUpdateManager` Integration

The `src/git_update_manager.py` module's `GitUpdateManager` class seamlessly integrates with the `SSHKeyManager`.

-   **Automatic Key Selection**: When a `GitUpdateManager` instance is created for either the "application" or "scripts" repository, it automatically initializes an `SSHKeyManager` with the correct key name.
-   **Secure Git Environment**: All Git commands are executed in a secure environment created by the `create_git_env()` method, which sets the `GIT_SSH_COMMAND` environment variable to use the correct SSH key.

## Security Best Practices

-   **File Permissions**: The setup scripts (`setup.command` and `setup.bat`) automatically set the correct file permissions (`600`) for the private keys. It is crucial that these permissions are maintained.
-   **Key Type**: The application is designed to work best with `Ed25519` SSH keys, which offer excellent security and performance. While `RSA` keys are supported, `Ed25519` is strongly recommended.
-   **Read-Only Access**: The deploy keys should be configured with read-only access to the GitHub repositories to minimize potential security risks.

## Troubleshooting

The `docs/user_guide/TROUBLESHOOTING.md` file contains a comprehensive guide for resolving common SSH key issues, including "permission denied" and "repository not found" errors. Developers can use the `test_key_access()` method in the `SSHKeyManager` for more advanced debugging.