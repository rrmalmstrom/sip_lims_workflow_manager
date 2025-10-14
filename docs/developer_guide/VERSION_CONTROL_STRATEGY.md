# Git Branching Strategy: Promoting sip_mac_solution_no_docker to main

This document outlines the steps to make the `sip_mac_solution_no_docker` branch the new `main` branch, while preserving the history of the old `main` branch.

## Strategy

The strategy involves three main steps:

1.  **Preserve the old `main` branch**: Rename the current `main` branch to `main_docker_legacy`.
2.  **Promote the feature branch**: Rename the `sip_mac_solution_no_docker` branch to `main`.
3.  **Push the changes**: Push the new `main` and `main_docker_legacy` branches to the remote repository.

## Commands

Execute the following commands in your terminal:

```bash
# Step 1: Preserve the old main branch
# Switch to the main branch
git checkout main

# Rename it
git branch -m main_docker_legacy

# Step 2: Promote the feature branch to main
# Switch to your feature branch
git checkout sip_mac_solution_no_docker

# Rename it to main
git branch -m main

# Step 3: Push changes to the remote repository
# Push the new main branch to the remote
git push origin main

# Push the legacy branch to the remote
git push origin main_docker_legacy

# Update the remote's default branch to point to the new main branch
git remote set-head origin main
```
