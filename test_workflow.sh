#!/bin/bash
# Test script to simulate user input for debugging

# Simulate selecting SPS-CE workflow (choice 2) and production mode (choice 1)
echo "Testing workflow with SPS-CE + Production mode..."
echo -e "2\n1\n" | timeout 30 ./run.mac.command || echo "Script terminated (expected due to timeout or missing project folder)"