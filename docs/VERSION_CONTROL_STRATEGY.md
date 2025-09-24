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

**Result:** GitHub shows your tags, but you need to manually create "Releases" for better visibility.

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
- Tags alone show just version numbers - no descriptions
- GitHub "Releases" provide better visibility with descriptions

### Benefits:
- **Users**: Simple - just one ZIP file to download from Google Drive
- **You**: Git automatically tracks all changes and versions
- **History**: GitHub keeps everything, Google Drive stays clean
- **Rollback**: If needed, you can always get any old version from GitHub

### The Release Process:
1. **Develop**: Make changes, commit to Git
2. **Tag**: `git tag v1.1` when ready to release
3. **Push**: `git push && git push --tags`
4. **Create GitHub Release** (optional but recommended):
   - Go to GitHub → Releases → Create new release
   - Select your tag (v1.1)
   - Add title: "Version 1.1 - Feature Description"
   - Add description of what changed
5. **Build**: Create ZIP file of the application
6. **Upload**: Replace ZIP file in Google Drive
7. **Update**: Change version number in `latest.json`

This way:
- GitHub = Developer tool (version control, history)
- Google Drive = User tool (simple download)

## GitHub Tags vs Releases

### Tags Only (Current Approach):
- **Pros**: Simple, automatic version tracking
- **Cons**: No visible descriptions of what changed
- **Best for**: Personal projects, simple version tracking

### Tags + Releases (Recommended):
- **Pros**: Clear descriptions, professional appearance, better documentation
- **Cons**: Extra step to create releases
- **Best for**: Projects others might use, better long-term documentation

### How to Create a GitHub Release:

**From Existing Tag:**
1. Go to your GitHub repository
2. Click "Releases" (right side of main page)
3. Click "Create a new release"
4. Choose existing tag (e.g., v1.0.1)
5. Add release title: "Version 1.0.1 - Automatic Update System"
6. Add description:
   ```
   ## What's New in v1.0.1
   - Added automatic update checking from Google Drive
   - Users now get prompted when new versions are available
   - Improved workflow version management
   
   ## Download
   Get the latest version from our Google Drive distribution.
   ```
7. Click "Publish release"

**For Future Releases:**
1. Make changes and commit: `git commit -m "Add new feature"`
2. Create tag: `git tag v1.0.2`
3. Push: `git push && git push --tags`
4. Go to GitHub → Releases → Create new release
5. Select the new tag and add description

This approach gives you the best of both worlds: simple Git workflow + clear documentation.