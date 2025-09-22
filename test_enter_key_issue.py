#!/usr/bin/env python3
"""
Test script to reproduce the Enter key issue in terminal input.
This creates a minimal reproduction of the problem.
"""

import streamlit as st
import streamlit.components.v1 as components

st.title("🧪 Enter Key Test")

# Simulate the current terminal input implementation
st.header("Current Implementation (Broken)")

if 'test_output' not in st.session_state:
    st.session_state.test_output = ""

def send_test_input(user_input):
    """Simulate sending input to terminal."""
    if user_input.strip():
        st.session_state.test_output += f"Sent: {user_input}\n"
        st.session_state.terminal_input_box = ""

# Current implementation from app.py
col1, col2 = st.columns([4, 1])
with col1:
    user_input = st.text_input(
        "Input:", 
        key="terminal_input_box",
        help="Type your input and press Enter or click 'Send Input'"
    )
with col2:
    send_button = st.button(
        "Send Input",
        key="send_terminal_input",
        on_click=send_test_input,
        args=(user_input,)
    )

# Add the current JavaScript implementation
if user_input:  # Only add the script when there's input
    components.html(f"""
    <script>
    (function() {{
        // Find the terminal input box
        const inputs = window.parent.document.querySelectorAll('input[data-testid="stTextInput"]');
        let terminalInput = null;
        
        // Find the input that has "Input:" as its label (our terminal input)
        inputs.forEach(input => {{
            const label = input.closest('div').querySelector('label');
            if (label && label.textContent.includes('Input:')) {{
                terminalInput = input;
            }}
        }});
        
        if (terminalInput && !terminalInput.hasAttribute('data-enter-handler')) {{
            terminalInput.setAttribute('data-enter-handler', 'true');
            
            terminalInput.addEventListener('keydown', function(event) {{
                if (event.key === 'Enter' && this.value.trim() !== '') {{
                    event.preventDefault();
                    
                    // Find and click the Send Input button
                    const buttons = window.parent.document.querySelectorAll('button');
                    buttons.forEach(button => {{
                        if (button.textContent.includes('Send Input')) {{
                            button.click();
                        }}
                    }});
                }}
            }});
        }}
    }})();
    </script>
    """, height=0)

# Show test output
st.text_area("Test Output:", value=st.session_state.test_output, height=200, disabled=True)

st.markdown("---")
st.markdown("**Test Instructions:**")
st.markdown("1. Type some text in the input box above")
st.markdown("2. Try pressing Enter - it should send the input but likely won't work")
st.markdown("3. Click 'Send Input' button - this should work")
st.markdown("4. Report back whether Enter key works or not")