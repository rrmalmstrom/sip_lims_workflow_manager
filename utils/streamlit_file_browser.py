import streamlit as st
from pathlib import Path
import os

def st_file_browser(path, show_hidden=False, key=None, mode="file"):
    """
    A simple file browser component for Streamlit.
    """
    if key is None:
        key = "default"
    
    # Initialize session state
    current_path_key = f"file_browser_current_path_{key}"
    if current_path_key not in st.session_state:
        st.session_state[current_path_key] = Path(path)
    
    current_path = st.session_state[current_path_key]
    
    # Current path display with breadcrumb navigation
    st.markdown(f"### 📁 Current Location")
    st.code(str(current_path))
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # Up button (if not at root)
        if current_path != Path(path):
            if st.button("⬆️ Go Up", key=f"{key}_up", use_container_width=True):
                st.session_state[current_path_key] = current_path.parent
                st.rerun()
    
    with col2:
        # Home button to go back to start path
        if current_path != Path(path):
            if st.button("🏠 Home", key=f"{key}_home", use_container_width=True):
                st.session_state[current_path_key] = Path(path)
                st.rerun()
    
    # For folder mode, add "Select This Folder" button
    if mode == "folder":
        st.markdown("---")
        col_select, col_cancel = st.columns([1, 1])
        with col_select:
            if st.button("✅ Select This Folder", key=f"{key}_select_folder", type="primary", use_container_width=True):
                return str(current_path)
        with col_cancel:
            if st.button("❌ Cancel", key=f"{key}_cancel", use_container_width=True):
                return "CANCELLED"
    
    st.markdown("---")
    
    # File and folder listing
    try:
        items = []
        for item in os.listdir(current_path):
            if not show_hidden and item.startswith("."):
                continue
            item_path = current_path / item
            items.append((item, item_path))
        
        # Sort: directories first, then files, alphabetically
        items.sort(key=lambda x: (x[1].is_file(), x[0].lower()))
        
    except (FileNotFoundError, PermissionError) as e:
        st.error(f"Cannot access directory: {e}")
        return None
    
    if not items:
        st.info("📂 This directory is empty")
        return None
    
    st.markdown("### 📋 Contents")
    
    # Display items in a more organized way
    for item_name, item_path in items:
        if item_path.is_dir():
            # Directory button
            col_icon, col_name = st.columns([1, 8])
            with col_icon:
                st.write("📁")
            with col_name:
                if st.button(item_name, key=f"{key}_dir_{item_name}", use_container_width=True):
                    st.session_state[current_path_key] = item_path
                    st.rerun()
        else:
            # File display (only for file mode)
            if mode == "file":
                col_icon, col_name, col_select = st.columns([1, 6, 2])
                with col_icon:
                    st.write("📄")
                with col_name:
                    st.write(item_name)
                with col_select:
                    if st.button("Select", key=f"{key}_file_{item_name}"):
                        return str(item_path)
            else:
                # Just show file name in folder mode
                col_icon, col_name = st.columns([1, 8])
                with col_icon:
                    st.write("📄")
                with col_name:
                    st.write(item_name)
    
    return None

def show_file_browser_page(start_path="/data", mode="folder", title="Select Folder"):
    """
    Show a dedicated file browser page that replaces the main content.
    This is the proper solution for Docker environments.
    """
    st.title(f"📁 {title}")
    st.markdown("---")
    
    # Instructions
    if mode == "folder":
        st.info("🎯 **Instructions**: Navigate to your desired folder and click '✅ Select This Folder' to choose it.")
    else:
        st.info("🎯 **Instructions**: Navigate to your desired file and click 'Select' next to the file name.")
    
    # File browser
    selected = st_file_browser(start_path, key="main_browser", mode=mode)
    
    if selected:
        if selected == "CANCELLED":
            # User cancelled - return to main app
            st.session_state.file_browser_active = False
            st.session_state.file_browser_result = None
            st.rerun()
        else:
            # User made a selection
            st.session_state.file_browser_active = False
            st.session_state.file_browser_result = selected
            st.success(f"✅ Selected: `{selected}`")
            st.info("🔄 Returning to main application...")
            time.sleep(1)
            st.rerun()
    
    # Cancel button at bottom
    st.markdown("---")
    if st.button("❌ Cancel and Return to Main App", type="secondary", use_container_width=True):
        st.session_state.file_browser_active = False
        st.session_state.file_browser_result = None
        st.rerun()

def activate_file_browser(start_path="/data", mode="folder", title="Select Folder"):
    """
    Activate the file browser by setting session state flags.
    This replaces the popup approach with a dedicated page.
    """
    st.session_state.file_browser_active = True
    st.session_state.file_browser_mode = mode
    st.session_state.file_browser_start_path = start_path
    st.session_state.file_browser_title = title
    st.session_state.file_browser_result = None

def get_file_browser_result():
    """
    Get the result from the file browser if available.
    Returns the selected path or None if no selection made.
    """
    return st.session_state.get('file_browser_result', None)

def is_file_browser_active():
    """
    Check if the file browser is currently active.
    """
    return st.session_state.get('file_browser_active', False)

# Legacy compatibility functions (for existing code)
def show_file_browser_popup(start_path="/data", mode="folder", key="browser"):
    """
    Legacy compatibility function that now uses the new page-based approach.
    """
    # Instead of showing a popup, activate the dedicated file browser page
    title = f"Select {'Folder' if mode == 'folder' else 'File'}"
    activate_file_browser(start_path, mode, title)
    return None  # Return None immediately, result will be available after page navigation