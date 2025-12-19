# ESP Docker Implementation - Executive Summary

## Simple Implementation Plan (1-2 Days Total)

### What I'm Going to Do

**Step 1: Copy the Working Stuff (4 hours)**
- Check out the `main_docker_legacy` branch 
- Copy these specific files to current branch:
  - `Dockerfile` 
  - `docker-compose.yml`
  - `utils/streamlit_file_browser.py` (the file browser that works in Docker)
  - The run scripts (`run.command`, `run.bat`)

**Step 2: Fix the One Critical Problem (6 hours)**
- Add user ID mapping to the Dockerfile so files aren't created as root
- This fixes the shared network drive problem for lab collaboration

**Step 3: Add Safety Check (2 hours)**
- Add a simple check when the app starts to make sure Docker volumes are mounted
- Prevents users from seeing empty file browsers

**Step 4: Test It Works (4 hours)**
- Build the Docker container
- Test file selection works
- Test on a shared network drive
- Make sure files have correct ownership

### Why This Approach?

**The legacy Docker implementation already works** - it's been running in labs for 4+ years. Instead of building from scratch (2-3 weeks), I'm just copying the working solution and fixing the one thing that's broken (file permissions).

### What I'm NOT Doing

- Building Docker from scratch
- Rewriting the file browser
- Changing the core application
- Complex new features

### The Result

You'll have a working Docker container that:
- Uses the same file browser that's proven to work
- Creates files with proper ownership for shared drives
- Starts up with proper error checking
- Works exactly like the current app, just in Docker

**Total time: 1-2 days instead of 2-3 weeks**

## Implementation Strategy: "Copy and Fix"

Rather than building from scratch, I'm doing a "copy and fix" approach:

1. **Copy** the proven legacy Docker files
2. **Fix** the one critical gap (user permissions)
3. **Test** that everything works
4. **Done**

This leverages 4+ years of production-tested Docker implementation instead of reinventing the wheel.

## Critical Update Strategy Clarification

### How Updates Work in the Legacy System

**Scripts Updates (Git-based)**:
- Scripts are stored in a host directory: `~/.sip_lims_workflow_manager/scripts`
- This directory is mounted into the container as `/workflow-scripts`
- The existing `git_update_manager.py` pulls script updates into this mounted directory
- **Key Point**: Scripts update via Git operations that happen INSIDE the running container

**Application Updates (Docker Image-based)**:
- Application code is baked into the Docker image during build
- To update the application, you need a new Docker image
- Users would run `docker-compose pull` to get new image, then restart

### What This Means for Implementation

**I need to preserve the hybrid update system**:
1. **Scripts**: Keep the existing Git update mechanism - it works in containers
2. **Application**: New Docker images for app updates (standard Docker practice)

**The legacy system already handles this correctly** - the Git update manager works inside containers because:
- Git is installed in the container
- The scripts directory is mounted and writable
- Git operations happen inside the container, updating the mounted host directory

This is actually a sophisticated and working solution that I should copy exactly, not modify.

## Key Insight: Updates Are Already Solved

You were right to question this! The legacy implementation already has a working hybrid update strategy:

- **Scripts update via Git** (inside container, to mounted volume)
- **App updates via Docker images** (standard Docker practice)

I don't need to build a new update system - I just need to copy the working one.

## Critical File Browsing Strategy Clarification

After reviewing the current [`app.py`](app.py:1), I can see there are **two distinct file selection scenarios**:

### 1. **Project Directory Selection** (Lines 352-357)
**Current Implementation**: Uses tkinter via [`select_folder_via_subprocess()`](app.py:214)
```python
if st.button("Browse for Project Folder", key="browse_button"):
    folder = select_folder_via_subprocess()  # Uses tkinter
    if folder:
        st.session_state.project_path = Path(folder)
```

**Docker Problem**: tkinter won't work in containers

### 2. **Workflow Input File Selection** (Lines 1079-1083)
**Current Implementation**: Uses tkinter via [`select_file_via_subprocess()`](app.py:208)
```python
if st.button("Browse", key=f"browse_{input_key}"):
    selected_file = select_file_via_subprocess()  # Uses tkinter
    if selected_file:
        st.session_state.user_inputs[step_id][input_key] = selected_file
```

**Docker Problem**: tkinter won't work in containers

### My Implementation Strategy

**For Docker**: Replace BOTH tkinter calls with Streamlit file browser
- **Project selection**: Use Streamlit file browser starting from `/data` mount point
- **Workflow inputs**: Use Streamlit file browser for individual file selection

**Key Insight**: The legacy Docker implementation already has the [`st_file_browser`](utils/streamlit_file_browser.py:5) component that works in containers. I just need to:

1. **Replace project folder selection** with Streamlit browser
2. **Replace workflow input file selection** with Streamlit browser (already planned)
3. **Use the two-volume strategy** where `/data` is the project directory

This means users will select their project directory OUTSIDE Docker (when mounting volumes), and then use Streamlit file browser INSIDE Docker for all file operations.