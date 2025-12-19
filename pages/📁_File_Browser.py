import streamlit as st
from pathlib import Path
import os
import time

# Page configuration
st.set_page_config(page_title="File Browser", page_icon="📁", layout="wide")

def main():
    st.title("📁 File Browser")
    
    # Get parameters from URL query params
    mode = st.query_params.get("mode", "folder")
    start_path = st.query_params.get("start_path", "/data" if os.path.exists("/data") else ".")
    title = st.query_params.get("title", f"Select {'Folder' if mode == 'folder' else 'File'}")
    return_key = st.query_params.get("return_key", "file_browser_result")
    
    st.markdown(f"### {title}")
    st.markdown("---")
    
    # Instructions
    if mode == "folder":
        st.info("🎯 **Instructions**: Navigate to your desired folder and click '✅ Select This Folder' to choose it.")
    else:
        st.info("🎯 **Instructions**: Navigate to your desired file and click 'Select' next to the file name.")
    
    # Initialize session state for navigation
    if "current_path" not in st.session_state:
        st.session_state.current_path = Path(start_path)
    
    current_path = st.session_state.current_path
    
    # Current path display with breadcrumb navigation
    st.markdown(f"### 📁 Current Location")
    st.code(str(current_path))
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # Up button (if not at root)
        if current_path != Path(start_path):
            if st.button("⬆️ Go Up", use_container_width=True):
                st.session_state.current_path = current_path.parent
                st.rerun()
    
    with col2:
        # Home button to go back to start path
        if current_path != Path(start_path):
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_path = Path(start_path)
                st.rerun()
    
    # For folder mode, add "Select This Folder" button
    if mode == "folder":
        st.markdown("---")
        col_select, col_cancel = st.columns([1, 1])
        with col_select:
            if st.button("✅ Select This Folder", type="primary", use_container_width=True):
                # Store the result in session state with the specified key
                st.session_state[return_key] = str(current_path)
                st.success(f"✅ **Selected**: `{current_path}`")
                st.info("🔄 **Success!** You can now close this tab and return to the main application.")
                st.balloons()
                return
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state[return_key] = None
                st.info("❌ Selection cancelled. You can close this tab and return to the main application.")
                return
    
    st.markdown("---")
    
    # File and folder listing
    try:
        items = []
        for item in os.listdir(current_path):
            if item.startswith("."):
                continue  # Skip hidden files
            item_path = current_path / item
            items.append((item, item_path))
        
        # Sort: directories first, then files, alphabetically
        items.sort(key=lambda x: (x[1].is_file(), x[0].lower()))
        
    except (FileNotFoundError, PermissionError) as e:
        st.error(f"Cannot access directory: {e}")
        return
    
    if not items:
        st.info("📂 This directory is empty")
        return
    
    st.markdown("### 📋 Contents")
    
    # Display items in a more organized way
    for item_name, item_path in items:
        if item_path.is_dir():
            # Directory button
            col_icon, col_name = st.columns([1, 8])
            with col_icon:
                st.write("📁")
            with col_name:
                if st.button(item_name, use_container_width=True, key=f"dir_{item_name}"):
                    st.session_state.current_path = item_path
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
                    if st.button("Select", key=f"file_{item_name}"):
                        # Store the result in session state with the specified key
                        st.session_state[return_key] = str(item_path)
                        st.success(f"✅ **Selected**: `{item_path}`")
                        st.info("🔄 **Success!** You can now close this tab and return to the main application.")
                        st.balloons()
                        return
            else:
                # Just show file name in folder mode
                col_icon, col_name = st.columns([1, 8])
                with col_icon:
                    st.write("📄")
                with col_name:
                    st.write(item_name)
    
    # Instructions for returning to main app
    st.markdown("---")
    st.markdown("### 🔙 Return to Main App")
    st.info("Close this browser tab to return to the main SIP LIMS Workflow Manager application.")

if __name__ == "__main__":
    main()