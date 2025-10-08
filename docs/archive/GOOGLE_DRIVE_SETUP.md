# Google Drive Setup for SIP LIMS Workflow Manager Updates

## Simple Distribution Strategy

**Goal**: Users get the latest version easily, GitHub handles version history automatically.

## Google Drive Folder Structure

Create this **simple structure** in your shared Google Drive:

```
SIP_LIMS_Releases/
├── latest.json                        # Small text file with version info
├── sip_lims_workflow_manager.zip      # The app folder, zipped (always latest)
└── README.md                          # Instructions for users
```

That's it! Just **3 files** in one folder.

## Setup Steps

### 1. Create the Google Drive Folder
1. In your shared Google Drive, create a folder called `SIP_LIMS_Releases`
2. Right-click → "Share" → Set to "Anyone with the link can view"
3. Copy the folder link to share with your lab

### 2. Create the Files

**File 1: latest.json**
```json
{
  "latest_version": "1.0.0",
  "release_date": "2024-09-24",
  "release_notes": "Initial release of SIP LIMS Workflow Manager",
  "download_url": "https://drive.google.com/uc?id=YOUR_ZIP_FILE_ID&export=download",
  "filename": "sip_lims_workflow_manager.zip"
}
```

**File 2: sip_lims_workflow_manager.zip**
- ZIP up your entire application folder
- Upload to Google Drive
- Get the shareable link

**File 3: README.md**
```markdown
# SIP LIMS Workflow Manager Downloads

## How to Install:
1. Download `sip_lims_workflow_manager.zip`
2. Extract it to your Desktop or Documents folder
3. Run `setup.command` (macOS) or `setup.bat` (Windows)
4. Use `run.command` (macOS) or `run.bat` (Windows) to start

## Updates:
The application will automatically check for updates and notify you when new versions are available.
```

### 3. Get Direct Download Links

For the ZIP file:
1. Right-click → "Get link" → "Anyone with the link can view"
2. Copy the link (looks like: `https://drive.google.com/file/d/FILE_ID/view?usp=sharing`)
3. Convert to direct download: `https://drive.google.com/uc?id=FILE_ID&export=download`
4. Put this URL in the `latest.json` file

For the `latest.json` file:
1. Same process - get the direct download link
2. This URL goes into your application code for automatic checking

## How Updates Work

### For Users:
1. App shows notification: "Update available: v1.1.0"
2. User clicks "Download Update"
3. Browser opens to download the new ZIP file
4. User extracts it to replace their old folder

### For You (Releasing Updates):
1. Make your changes and commit to Git
2. Create Git tag: `git tag v1.1.0`
3. ZIP up the updated application folder
4. Replace the ZIP file in Google Drive (same filename)
5. Update `latest.json` with new version number and release notes

## Benefits of This Approach:

✅ **Simple for Users**: One folder, one ZIP file to download
✅ **Easy for You**: Just replace one file when updating
✅ **Version Control**: Git handles all the history automatically
✅ **Reliable**: Google Drive provides stable hosting
✅ **No Confusion**: Always clear which is the latest version

## Next Steps:

1. Set up the Google Drive folder
2. Upload your first release
3. Test the download links
4. Implement the update checking code in the application