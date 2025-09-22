#!/usr/bin/env python3
"""
Test script with a proposed fix for the Enter key issue.
This implements a more reliable approach.
"""

import streamlit as st
import streamlit.components.v1 as components

st.title("🧪 Enter Key Fix Test")

# Initialize session state
if 'test_output' not in st.session_state:
    st.session_state.test_output = ""
if 'terminal_input_box' not in st.session_state:
    st.session_state.terminal_input_box = ""

def send_test_input():
    """Send input from session state."""
    user_input = st.session_state.terminal_input_box
    if user_input.strip():
        st.session_state.test_output += f"Sent: {user_input}\n"
        st.session_state.terminal_input_box = ""

def handle_input_change():
    """Handle input changes - check for Enter key simulation."""
    # This will be called whenever the input changes
    pass

# Proposed fix implementation
st.header("Proposed Fix")

col1, col2 = st.columns([4, 1])
with col1:
    # Use on_change callback instead of relying on JavaScript
    user_input = st.text_input(
        "Input:", 
        key="terminal_input_box",
        help="Type your input and press Enter or click 'Send Input'",
        on_change=handle_input_change
    )
with col2:
    send_button = st.button(
        "Send Input",
        key="send_terminal_input",
        on_click=send_test_input
    )

# Always add JavaScript (not conditional on input)
components.html("""
<script>
(function() {
    let setupComplete = false;
    
    function setupEnterHandler() {
        if (setupComplete) return;
        
        // Find all text inputs
        const inputs = window.parent.document.querySelectorAll('input[data-testid="stTextInput"]');
        
        inputs.forEach(input => {
            // Check if this input has the help text we're looking for
            const container = input.closest('[data-testid="stTextInput"]');
            if (container) {
                const helpText = container.querySelector('[data-testid="stTooltipHoverTarget"]');
                if (helpText && helpText.getAttribute('title') && 
                    helpText.getAttribute('title').includes('Type your input and press Enter')) {
                    
                    // This is our terminal input
                    if (!input.hasAttribute('data-enter-setup')) {
                        input.setAttribute('data-enter-setup', 'true');
                        
                        input.addEventListener('keypress', function(event) {
                            if (event.key === 'Enter' && this.value.trim() !== '') {
                                event.preventDefault();
                                
                                // Find and click the Send Input button
                                const buttons = window.parent.document.querySelectorAll('button');
                                buttons.forEach(button => {
                                    if (button.textContent.includes('Send Input')) {
                                        button.click();
                                    }
                                });
                            }
                        });
                        
                        setupComplete = true;
                        console.log('Enter key handler attached to terminal input');
                    }
                }
            }
        });
    }
    
    // Try to setup immediately
    setupEnterHandler();
    
    // Also try after delays to catch dynamically created elements
    setTimeout(setupEnterHandler, 100);
    setTimeout(setupEnterHandler, 500);
    setTimeout(setupEnterHandler, 1000);
    
    // Watch for DOM changes
    const observer = new MutationObserver(function(mutations) {
        setupEnterHandler();
    });
    
    observer.observe(window.parent.document.body, {
        childList: true,
        subtree: true
    });
})();
</script>
""", height=0)

# Show test output
st.text_area("Test Output:", value=st.session_state.test_output, height=200, disabled=True)

st.markdown("---")
st.markdown("**Fix Improvements:**")
st.markdown("1. ✅ JavaScript loads immediately (not conditional)")
st.markdown("2. ✅ Uses help text to identify the correct input (more reliable)")
st.markdown("3. ✅ Multiple setup attempts with delays")
st.markdown("4. ✅ MutationObserver watches for DOM changes")
st.markdown("5. ✅ Uses 'keypress' instead of 'keydown' for better compatibility")

st.markdown("**Test Instructions:**")
st.markdown("1. Type some text in the input box above")
st.markdown("2. Press Enter - it should now work!")
st.markdown("3. Check the browser console for 'Enter key handler attached' message")
st.markdown("4. Report back whether Enter key works")