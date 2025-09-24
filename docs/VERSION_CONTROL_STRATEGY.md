# Version Control Strategy for SIP LIMS Workflow Manager

## Git Version Management (Simple Approach)

You **keep the same repository** - no need for separate repos per version! Git handles this automatically with **tags**.

### How Git Versions Work:

**One Repository Timeline:**
```
main branch: v1.0 → v1.1 → v1.2 → v1.3 → ...
             ↑      ↑      ↑      ↑
           tag:   tag:   tag:   tag:
           v1.0   v1.1   v1.2   v1.3
```

### Simple Git Workflow:

**When you release v1.0:**
1. Commit your changes: `git commit -m "Release v1.0"`
2. Create a tag: `git tag v1.0`
3. Push everything: `git push && git push --tags`

**When you release v1.1:**
1. Make your changes and commit them
2. Create a new tag: `git tag v1.1`
3. Push: `git push && git push --tags`

**Result:** GitHub automatically creates a "Releases" page showing all your versions!

## Recommended Distribution Strategy

### Simple Google Drive + GitHub Approach:

**Google Drive (User Access):**
```
SIP_LIMS_Releases/
├── latest.json                        # Version info
└── sip_lims_workflow_manager.zip      # Always the newest version
```

**GitHub (Version History):**
- All code changes tracked automatically
- Tags mark each release (v1.0, v1.1, etc.)
- GitHub "Releases" page shows version history
- You can attach ZIP files to releases if needed

### Benefits:
- **Users**: Simple - just one ZIP file to download from Google Drive
- **You**: Git automatically tracks all changes and versions
- **History**: GitHub keeps everything, Google Drive stays clean
- **Rollback**: If needed, you can always get any old version from GitHub

### The Release Process:
1. **Develop**: Make changes, commit to Git
2. **Tag**: `git tag v1.1` when ready to release
3. **Build**: Create ZIP file of the application
4. **Upload**: Replace ZIP file in Google Drive
5. **Update**: Change version number in `latest.json`

This way:
- GitHub = Developer tool (version control, history)
- Google Drive = User tool (simple download)

Does this approach make sense for your workflow?