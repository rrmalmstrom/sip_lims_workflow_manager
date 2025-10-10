# Cross-Platform Strategy Comparison: GitHub Actions vs. Hybrid Docker

## 1. Introduction

This document evaluates two strategies to address cross-platform compatibility issues for the SIP LIMS Workflow Manager, primarily stemming from failures on Windows systems. The current setup relies on Conda and shell scripts developed on macOS, which do not translate well to Windows environments.

The two proposed solutions are:
1.  **GitHub Actions for Automated Testing:** Maintain the Conda-based approach but implement a CI/CD pipeline to test the setup and application execution on both Windows and macOS virtual machines.
2.  **Hybrid Docker Strategy:** Package the application environment into a Docker container but mount the user's local `scripts` directory, allowing for dynamic updates via `git pull`.

## 2. Evaluation Criteria

### 2.1. Developer Experience

*   **GitHub Actions:**
    *   **Pros:** The core development workflow remains unchanged. The developer can continue working in their native macOS environment. Failures are caught automatically by the CI pipeline, providing clear feedback without needing a local Windows machine.
    *   **Cons:** Debugging Windows-specific issues can be cumbersome, relying on logs from GitHub Actions. There's a risk of developing platform-specific code that passes on macOS but consistently fails on Windows, leading to a frustrating "debug-by-CI" loop.

*   **Hybrid Docker Strategy:**
    *   **Pros:** Development and testing occur within the same containerized environment that users will have, significantly reducing the "it works on my machine" problem. The developer gets a consistent, reproducible environment.
    *   **Cons:** Requires the developer to have Docker installed and to become familiar with a container-based workflow. This adds a layer of abstraction that might complicate simple tasks.

### 2.2. User Experience

*   **GitHub Actions:**
    *   **Pros:** If the scripts are perfected, the user experience could be simple. The user would still run a `setup` script and a `run` script.
    *   **Cons:** This strategy doesn't fundamentally solve the underlying problem of environment disparity. A user's local machine configuration (e.g., PATH variables, existing Python installations, shell differences) can still cause the scripts to fail, even if they pass in the clean environment of GitHub Actions. This is the core issue at hand.

*   **Hybrid Docker Strategy:**
    *   **Pros:** The initial setup is more complex, as it requires installing Docker Desktop. However, once Docker is running, the application environment is guaranteed to be identical for all users on all platforms. This eliminates an entire class of environment-related bugs and support requests. Daily execution is simplified to a single `docker-compose up` command.
    *   **Cons:** Docker can be an intimidating tool for non-technical users. The initial installation and setup represent a significant hurdle.

### 2.3. Maintenance Burden

*   **GitHub Actions:**
    *   **Pros:** The maintenance is focused on the GitHub Actions workflow file, which is relatively simple.
    *   **Cons:** The primary maintenance burden is in the setup scripts themselves. As dependencies change or Conda evolves, the scripts may require ongoing tweaks to maintain compatibility with both macOS and Windows. This is a reactive approach.

*   **Hybrid Docker Strategy:**
    *   **Pros:** The `Dockerfile` and `docker-compose.yml` files are the single source of truth for the environment. Updating a dependency is a matter of changing a line in the `Dockerfile` and rebuilding the image. This is a proactive and centralized approach to dependency management.
    *   **Cons:** The Docker image will need to be periodically rebuilt and pushed to a registry (like Docker Hub) to distribute updates to the core application environment.

### 2.4. Reliability & Robustness

*   **GitHub Actions:**
    *   **Pros:** Provides a safety net to catch cross-platform bugs before they reach users.
    *   **Cons:** Does not guarantee that the application will run on a user's machine. It only guarantees that it runs on a clean GitHub Actions runner. The reliability for the end-user is not directly addressed.

*   **Hybrid Docker Strategy:**
    *   **Pros:** High reliability. The container encapsulates the entire environment, ensuring that if it runs on the developer's machine, it will run on the user's machine, regardless of the host OS.
    *   **Cons:** The application's reliability is dependent on Docker itself running correctly on the user's system.

### 2.5. Update Mechanism

*   **GitHub Actions:**
    *   **Pros:** Fully supports the existing `git pull` mechanism for updating scripts without any changes.
    *   **Cons:** No significant cons for this criterion.

*   **Hybrid Docker Strategy:**
    *   **Pros:** The hybrid approach (mounting the local `scripts` folder) is designed specifically to support the `git pull` update mechanism. The container provides the stable environment, while the local files can be updated dynamically as required.
    *   **Cons:** Requires careful configuration of the volume mount to ensure permissions and paths are correct.

## 3. Recommendation

The **Hybrid Docker Strategy** is the recommended approach.

While it introduces a higher initial setup cost for the user (installing Docker), it provides a far more robust and reliable long-term solution. It directly solves the core problem of environment inconsistency, which the GitHub Actions strategy only papers over. By containerizing the application, we guarantee that all users are running the exact same environment, drastically reducing the maintenance burden of debugging platform-specific issues.

The hybrid model elegantly preserves the dynamic script update feature, which is a critical project requirement. The trade-off of a more involved one-time setup is well worth the benefit of a stable, predictable, and cross-platform application environment. This strategy is a proactive investment in reliability and maintainability.