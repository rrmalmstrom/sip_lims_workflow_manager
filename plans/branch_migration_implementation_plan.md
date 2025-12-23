# Branch Migration Implementation Plan

## Current State Analysis
- **Current Branch**: `analysis/esp-docker-adaptation` (development branch with new features)
- **Target**: Replace `main` branch with current development branch
- **Main Branch**: Currently at commit `24b4a65` (v2.2.2)
- **Development Branch**: Currently at commit `5261c30` with significant Docker and branch-aware enhancements
- **Issue Detected**: Untracked files in plans directory on main branch

## Objective
Replace the main branch with the `analysis/esp-docker-adaptation` branch while preserving the current main branch as a legacy archive, ensuring proper remote synchronization.

## Implementation Plan

### Phase 0: Pre-Migration Sync and Cleanup
1. **Fetch latest remote changes**
   ```bash
   git fetch --all --prune
   ```

2. **Handle untracked files on main branch**
   ```bash
   git add plans/
   git commit -m "Add migration plan before branch replacement"
   git push origin main
   ```

3. **Switch to development branch and ensure it's up to date**
   ```bash
   git checkout analysis/esp-docker-adaptation
   git pull origin analysis/esp-docker-adaptation
   ```

### Phase 1: Create Legacy Archive Branch
1. **Checkout main branch**
   ```bash
   git checkout main
   ```

2. **Create legacy archive branch**
   ```bash
   git checkout -b legacy-main-esp-condensed-lims
   ```

3. **Push legacy branch to remote**
   ```bash
   git push origin legacy-main-esp-condensed-lims
   ```

4. **Verify legacy branch exists on remote**
   ```bash
   git ls-remote --heads origin legacy-main-esp-condensed-lims
   ```

### Phase 2: Replace Main Branch Content
1. **Return to main branch**
   ```bash
   git checkout main
   ```

2. **Reset main to match development branch**
   ```bash
   git reset --hard analysis/esp-docker-adaptation
   ```

3. **Force push the updated main branch**
   ```bash
   git push origin main --force-with-lease
   ```

4. **Verify main branch updated on remote**
   ```bash
   git log --oneline -5
   git ls-remote --heads origin main
   ```

### Phase 3: Clean Up Development Branch
1. **Delete local development branch**
   ```bash
   git branch -d analysis/esp-docker-adaptation
   ```

2. **Delete remote development branch**
   ```bash
   git push origin --delete analysis/esp-docker-adaptation
   ```

3. **Update local tracking and verify cleanup**
   ```bash
   git fetch --prune
   git branch -a
   ```

### Phase 4: Final Remote Synchronization Verification
1. **Verify all remote branches are as expected**
   ```bash
   git ls-remote --heads origin
   ```

2. **Confirm main branch content matches expected development branch content**
   ```bash
   git log --oneline --graph --decorate -10
   ```

3. **Verify legacy branch preserves original main content**
   ```bash
   git log --oneline legacy-main-esp-condensed-lims -5
   ```

## Safety Considerations

### Pre-execution Checks
- ✅ Working tree is clean (confirmed)
- ✅ All changes are committed and pushed
- ✅ Development branch is up to date with remote

### Backup Strategy
- The current main branch will be preserved as `legacy-main-esp-condensed-lims`
- All commit history will be maintained
- Remote branches provide additional backup

### Risk Mitigation
- Using `--force-with-lease` instead of `--force` to prevent overwriting unexpected changes
- Creating archive branch before any destructive operations
- Maintaining all commit history in the legacy branch

## Expected Outcome
- **Main branch**: Will contain all the Docker and branch-aware enhancements from `analysis/esp-docker-adaptation`
- **Legacy branch**: `legacy-main-esp-condensed-lims` will preserve the original main branch state
- **Clean repository**: No orphaned development branches
- **Preserved history**: All commit history maintained in appropriate branches

## Rollback Plan (if needed)
If something goes wrong, the main branch can be restored using:
```bash
git checkout main
git reset --hard legacy-main-esp-condensed-lims
git push origin main --force-with-lease
```

## Post-Migration Verification
1. Verify main branch contains expected commits from development branch
2. Verify legacy branch contains original main branch content
3. Confirm all team members can access the new main branch
4. Update any CI/CD pipelines that reference the old development branch

---

**Note**: This plan assumes you have appropriate permissions to force-push to the main branch. If your repository has branch protection rules, they may need to be temporarily disabled or you may need administrator approval.