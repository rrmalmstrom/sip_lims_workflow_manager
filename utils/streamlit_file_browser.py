import streamlit as st
from pathlib import Path
import os

def st_file_browser(path, show_hidden=False, key=None):
    """
    A simple file browser component for Streamlit.
    """
    if f"file_browser_current_path_{key}" not in st.session_state:
        st.session_state[f"file_browser_current_path_{key}"] = Path(path)

    current_path = st.session_state[f"file_browser_current_path_{key}"]

    st.write(f"Current path: `{current_path}`")

    # Navigation
    if current_path != Path(path):
        if st.button("⬆️ Up", key=f"{key}_up"):
            st.session_state[f"file_browser_current_path_{key}"] = current_path.parent
            st.rerun()

    # File and folder listing
    try:
        items = sorted(os.listdir(current_path), key=lambda x: (os.path.isfile(os.path.join(current_path, x)), x))
    except FileNotFoundError:
        st.error("Path not found.")
        return None

    selected_file = None
    for item in items:
        if not show_hidden and item.startswith("."):
            continue

        item_path = current_path / item
        if item_path.is_dir():
            if st.button(f"📁 {item}", key=f"{key}_{item}"):
                st.session_state[f"file_browser_current_path_{key}"] = item_path
                st.rerun()
        else:
            if st.button(f"📄 {item}", key=f"{key}_{item}"):
                selected_file = item_path

    return selected_file